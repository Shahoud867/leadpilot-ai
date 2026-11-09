import re, csv, io
from sqlalchemy import select, or_
from fastapi import HTTPException
from .db import *
from .domain import *
from .agents import *


def capture(db, tid, data, actor, auto_assign=True):
    contact = data["contact"].strip().upper()
    match = [Lead.contact == contact]
    if data.get("email"):
        match.append(Lead.email == data["email"])
    if data.get("external_id"):
        match.append(Lead.external_id == data["external_id"])
    existing = db.scalar(select(Lead).where(Lead.tenant_id == tid, or_(*match)))
    if existing:
        audit(
            db,
            tid,
            actor,
            "duplicate_detected",
            existing.id,
            "Merge review required; canonical record unchanged",
            after={"contact": contact},
        )
        return {
            "lead": serialize(existing),
            "duplicate": True,
            "message": "Duplicate linked for manager review; no fields overwritten.",
        }
    clock = now(db, tid)
    campaign = data.get("campaign_id")
    if campaign and not db.scalar(
        select(Campaign).where(Campaign.id == campaign, Campaign.tenant_id == tid)
    ):
        raise HTTPException(422, "Campaign does not belong to this business")
    l = Lead(
        id=uid(),
        tenant_id=tid,
        external_id=data.get("external_id") or uid(),
        name=data["name"],
        contact=contact,
        email=data.get("email", ""),
        source=data["source"],
        campaign_id=campaign,
        city=data["city"],
        interest=data["interest"],
        inquiry=data["inquiry"],
        budget=data.get("budget"),
        urgency=data.get("urgency", "this_week"),
        stage="new",
        consent=data.get("consent", "unknown"),
        consent_source="manual_simulation",
        consent_at=clock if data.get("consent") == "granted" else None,
        created_at=clock,
        updated_at=clock,
    )
    db.add(l)
    db.flush()
    emit(db, l, "captured", {"source": l.source, "synthetic": True}, actor)
    trace(
        db,
        l,
        "Capture",
        "Validate and deduplicate",
        {"contact": contact, "source": l.source},
        {"valid": True, "duplicate": False, "is_synthetic": True},
    )
    qualify(db, l)
    schedule(db, l)
    if auto_assign:
        commit_allocation(db, tid, allocation_preview(db, tid, [l]), actor)
    audit(
        db, tid, actor, "lead_created", l.id, after={"name": l.name, "stage": l.stage}
    )
    db.flush()
    return {"lead": serialize(l), "duplicate": False}


def reassign(db, user, l, rep_id, reason):
    if not reason.strip():
        raise HTTPException(422, "Override reason is required")
    r = db.scalar(select(Rep).where(Rep.id == rep_id, Rep.tenant_id == l.tenant_id))
    if not r:
        raise HTTPException(404, "Representative not found")
    reps, loads, clock = load_snapshot(db, l.tenant_id)
    if (
        not r.active
        or not r.shift_start <= clock.hour < r.shift_end
        or loads[r.id] >= r.capacity
    ):
        raise HTTPException(422, "Representative unavailable, off shift or at capacity")
    previous = l.owner_id
    for a in db.scalars(
        select(Assignment).where(
            Assignment.tenant_id == l.tenant_id,
            Assignment.lead_id == l.id,
            Assignment.status == "active",
        )
    ):
        a.status = "overridden"
    l.owner_id = r.id
    if l.stage in ("new", "reopened"):
        transition(db, l, "assigned", user["id"])
    db.add(
        Assignment(
            tenant_id=l.tenant_id,
            lead_id=l.id,
            rep_id=r.id,
            utility=0,
            approved_by=user["id"],
            created_at=now(db, l.tenant_id),
        )
    )
    for t in db.scalars(
        select(Task).where(
            Task.tenant_id == l.tenant_id,
            Task.lead_id == l.id,
            Task.status == "pending",
        )
    ):
        t.assigned_to = r.id
    for rec in db.scalars(
        select(Recommendation).where(
            Recommendation.tenant_id == l.tenant_id,
            Recommendation.lead_id == l.id,
            Recommendation.agent == "Recovery",
            Recommendation.status == "recommended",
        )
    ):
        rec.status = "approved"
    emit(
        db,
        l,
        "agent_override",
        {"before": previous, "after": r.id, "reason": reason},
        user["id"],
    )
    audit(
        db,
        l.tenant_id,
        user["id"],
        "agent_override",
        l.id,
        reason,
        {"owner_id": previous},
        {"owner_id": r.id},
    )
    trace(
        db,
        l,
        "Allocation",
        "Manager override",
        {"previous_owner": previous},
        {"chosen_owner": r.id, "reason": reason},
        status="overridden",
    )


def reply(db, l, actor, body="Simulated: Please book a consultation."):
    db.add(
        Communication(
            tenant_id=l.tenant_id,
            lead_id=l.id,
            direction="inbound",
            channel=l.source,
            body=body,
            status="received_simulated",
            consent_snapshot=l.consent,
            created_at=now(db, l.tenant_id),
        )
    )
    l.responded_at = l.responded_at or now(db, l.tenant_id)
    emit(db, l, "customer_reply", {"body": body, "simulated": True}, actor)
    if l.stage in ("assigned", "reopened"):
        transition(db, l, "contacted", actor)
    # A customer reply cannot satisfy the adviser first-response obligation.
    analytics_trace(db, l)


def enqueue(db, l, task, body, inject_failure=False, actor="system"):
    if task and task.status != "pending":
        raise HTTPException(409, "Task is no longer pending")
    if task and db.scalar(
        select(Job).where(
            Job.tenant_id == l.tenant_id,
            Job.task_id == task.id,
            Job.status.in_(["queued", "retry", "processing", "completed"]),
        )
    ):
        raise HTTPException(409, "Task already queued")
    j = Job(
        tenant_id=l.tenant_id,
        lead_id=l.id,
        task_id=task.id if task else None,
        created_at=now(db, l.tenant_id),
        due_at=now(db, l.tenant_id),
        payload={"body": body, "inject_failure": inject_failure},
    )
    db.add(j)
    db.flush()
    emit(db, l, "message_approved", {"job_id": j.id}, actor)
    audit(
        db,
        l.tenant_id,
        actor,
        "message_approved",
        l.id,
        "Explicit approval of simulated message",
        after={"job_id": j.id},
    )
    return j


def process_jobs(db, tid):
    clock = now(db, tid)
    results = []
    for job in db.scalars(
        select(Job)
        .where(
            Job.tenant_id == tid,
            Job.status.in_(["queued", "retry", "processing"]),
            Job.due_at <= clock,
        )
        .order_by(Job.created_at, Job.id)
    ):
        if job.locked_until and job.locked_until > clock:
            continue
        job.status = "processing"
        job.locked_until = plus(clock, 2)
        db.flush()
        l = db.get(Lead, job.lead_id)
        task = db.get(Task, job.task_id) if job.task_id else None
        if l.deleted or l.consent != "granted" or l.stage in TERMINAL:
            job.status = "suppressed"
            if task:
                task.status = "canceled"
            db.add(
                Communication(
                    tenant_id=tid,
                    lead_id=l.id,
                    direction="outbound",
                    channel=l.source,
                    body=job.payload["body"],
                    status="suppressed",
                    consent_snapshot=l.consent,
                    created_at=clock,
                )
            )
            emit(
                db,
                l,
                "outreach_suppressed",
                {"reason": "No active consent or closed record", "job_id": job.id},
            )
        elif job.payload.get("inject_failure") and job.retry_count == 0:
            job.status = "retry"
            job.retry_count += 1
            job.last_error = "Injected connector timeout"
            job.due_at = plus(clock, 2)
            emit(
                db,
                l,
                "connector_retry",
                {"job_id": job.id, "retry_count": job.retry_count},
            )
        else:
            db.add(
                Communication(
                    tenant_id=tid,
                    lead_id=l.id,
                    direction="outbound",
                    channel=l.source,
                    body=job.payload["body"],
                    status="sent_simulated",
                    consent_snapshot=l.consent,
                    created_at=clock,
                )
            )
            job.status = "completed"
            job.last_error = None
            l.first_response_at = l.first_response_at or clock
            if task:
                task.status = "sent_simulated"
                task.completed_at = clock
            for pending in db.scalars(
                select(Task).where(
                    Task.tenant_id == tid,
                    Task.lead_id == l.id,
                    Task.kind == "first_response",
                    Task.status == "pending",
                )
            ):
                pending.status = "completed"
                pending.completed_at = clock
            emit(db, l, "message_sent_simulated", {"job_id": job.id})
        job.locked_until = None
        results.append({"id": job.id, "status": job.status})
    return results


def analytics(db, user, days=30, source=""):
    tid = user["tenant_id"]
    clock = now(db, tid)
    cutoff = plus(clock, -days * 1440) if days else ""
    ls = [
        l
        for l in rows(db, Lead, tid)
        if not l.deleted
        and l.created_at >= cutoff
        and (not source or l.source == source)
        and (user["role"] != "operator" or l.owner_id == user["rep_id"])
    ]
    ids = {l.id for l in ls}
    tasks = [t for t in rows(db, Task, tid) if t.lead_id in ids]
    overdue = [t for t in tasks if t.status == "pending" and t.due_at < clock]
    stages = {s: sum(l.stage == s for l in ls) for s in STAGES}
    delays = [
        max(0, (dt(l.first_response_at) - dt(l.created_at)).total_seconds() / 60)
        for l in ls
        if l.first_response_at
    ]
    sla = db.get(Tenant, tid).settings["sla_minutes"]
    responded = [l for l in ls if l.first_response_at]
    eligible = [l for l in ls if l.first_response_at or plus(l.created_at, sla) < clock]
    met = sum(
        l.first_response_at is not None
        and (dt(l.first_response_at) - dt(l.created_at)).total_seconds() <= sla * 60
        for l in eligible
    )
    trend = []
    for d in range(min(days or 30, 30) - 1, -1, -1):
        date = dt(plus(clock, -d * 1440)).astimezone(PKT).date().isoformat()
        cohort = [
            l for l in ls if dt(l.created_at).astimezone(PKT).date().isoformat() == date
        ]
        trend.append(
            {
                "date": date[5:],
                "inquiries": len(cohort),
                "won": sum(l.stage == "won" for l in cohort),
            }
        )
    source_stats = [
        {
            "source": s,
            "leads": sum(l.source == s for l in ls),
            "won": sum(l.source == s and l.stage == "won" for l in ls),
            "value": sum(l.deal_value for l in ls if l.source == s),
        }
        for s in ["WhatsApp", "Instagram", "Website", "Walk-in"]
    ]
    reps, loads, _ = load_snapshot(db, tid)
    team = [
        {
            **serialize(r),
            "load": loads[r.id],
            "open": sum(l.owner_id == r.id and l.stage not in TERMINAL for l in ls),
            "won": sum(l.owner_id == r.id and l.stage == "won" for l in ls),
            "revenue": sum(l.deal_value for l in ls if l.owner_id == r.id),
            "conversion": round(
                100
                * sum(l.owner_id == r.id and l.stage == "won" for l in ls)
                / max(1, sum(l.owner_id == r.id for l in ls)),
                1,
            ),
        }
        for r in reps
    ]
    # Funnel from persisted forward transitions, not current-stage sums.
    events = [
        e
        for e in rows(db, Event, tid)
        if e.lead_id in ids and e.kind == "stage_changed"
    ]
    funnel = [
        {
            "stage": s,
            "count": (
                len(ids)
                if s == "captured"
                else len({e.lead_id for e in events if e.payload.get("to") == s})
            ),
        }
        for s in ["captured", "contacted", "qualified", "appointment", "won"]
    ]
    return {
        "total": len(ls),
        "new": stages["new"] + stages["assigned"],
        "qualified": stages["qualified"],
        "won": stages["won"],
        "overdue": len(overdue),
        "revenue": sum(l.deal_value for l in ls),
        "conversion": round(stages["won"] / max(1, len(ls)) * 100, 1),
        "sla_met": round(met / max(1, len(eligible)) * 100, 1),
        "sla_denominator": len(eligible),
        "mean_response": round(sum(delays) / max(1, len(delays)), 1),
        "responded": len(responded),
        "opt_outs": sum(l.consent == "opted_out" for l in ls),
        "stages": stages,
        "trend": trend,
        "sources": source_stats,
        "team": team,
        "funnel": funnel,
        "is_simulated": True,
        "clock": clock,
        "denominator_note": "Conversion = verified won / captured cohort. SLA = timely first replies / staff-replied or expired-SLA cohort.",
    }
