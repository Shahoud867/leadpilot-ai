from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import select
from .db import *

PKT = ZoneInfo("Asia/Karachi")
STAGES = [
    "new",
    "assigned",
    "contacted",
    "qualified",
    "appointment",
    "won",
    "lost",
    "dormant",
    "reopened",
    "archived",
]
TERMINAL = {"won", "lost", "archived"}


def dt(x):
    return datetime.fromisoformat(x)


def plus(x, minutes):
    return (dt(x) + timedelta(minutes=minutes)).isoformat()


def now(db, tid):
    return db.get(Tenant, tid).clock


def rows(db, model, tid):
    return db.scalars(select(model).where(model.tenant_id == tid)).all()


def get_lead(db, user, lid):
    l = db.scalar(
        select(Lead).where(
            Lead.id == lid, Lead.tenant_id == user["tenant_id"], Lead.deleted == False
        )
    )
    if not l or (user["role"] == "operator" and l.owner_id != user["rep_id"]):
        raise HTTPException(404, "Lead not found")
    return l


def audit(db, tid, actor, action, target, reason="", before=None, after=None):
    db.add(
        Audit(
            tenant_id=tid,
            actor=actor,
            action=action,
            target_id=target,
            reason=reason,
            before=before or {},
            after=after or {},
            created_at=now(db, tid),
        )
    )


def emit(db, l, kind, payload=None, actor="system", at=None):
    at = at or now(db, l.tenant_id)
    db.add(
        Event(
            tenant_id=l.tenant_id,
            lead_id=l.id,
            kind=kind,
            payload=payload or {},
            actor=actor,
            created_at=at,
        )
    )
    l.updated_at = at


def trace(
    db, l, agent, action, inputs, explanation, alternatives=None, status="applied"
):
    r = Recommendation(
        tenant_id=l.tenant_id,
        lead_id=l.id,
        agent=agent,
        action=action,
        inputs=inputs,
        explanation=explanation,
        alternatives=alternatives or [],
        status=status,
        created_at=now(db, l.tenant_id),
    )
    db.add(r)
    db.flush()
    return r


def transition(
    db, l, target, actor, reason="", verified=False, appointment_at=None, value=0
):
    allowed = {
        "new": {"assigned", "dormant", "lost", "archived"},
        "assigned": {"contacted", "dormant", "lost", "archived"},
        "contacted": {"qualified", "dormant", "lost", "archived"},
        "qualified": {"appointment", "lost", "archived"},
        "appointment": {"won", "lost", "archived"},
        "dormant": {"reopened", "archived"},
        "reopened": {"assigned", "contacted", "dormant", "lost", "archived"},
        "archived": {"reopened"},
    }
    if target not in allowed.get(l.stage, set()):
        raise HTTPException(422, f"Cannot move {l.stage} to {target}")
    if (
        target in ("contacted", "qualified", "appointment", "won")
        and not l.responded_at
    ):
        raise HTTPException(422, "A simulated or logged customer reply is required")
    if target == "appointment" and not appointment_at:
        raise HTTPException(422, "Appointment time is required")
    if target == "appointment" and dt(appointment_at) <= dt(now(db, l.tenant_id)):
        raise HTTPException(422, "Appointment must be in the future")
    if target == "won" and (not verified or value <= 0):
        raise HTTPException(422, "Verified outcome and positive deal value required")
    if target in ("lost", "dormant", "archived", "reopened") and not reason.strip():
        raise HTTPException(422, "A reason is required")
    before = l.stage
    l.stage = target
    if appointment_at:
        l.appointment_at = appointment_at
    if target == "won":
        l.outcome_verified = True
        l.deal_value = value
    emit(
        db, l, "stage_changed", {"from": before, "to": target, "reason": reason}, actor
    )
    audit(
        db,
        l.tenant_id,
        actor,
        "pipeline_transition",
        l.id,
        reason,
        {"stage": before},
        {"stage": target},
    )
    if target in TERMINAL:
        for task in db.scalars(
            select(Task).where(
                Task.tenant_id == l.tenant_id,
                Task.lead_id == l.id,
                Task.status == "pending",
            )
        ):
            task.status = "canceled"
        for job in db.scalars(
            select(Job).where(
                Job.tenant_id == l.tenant_id,
                Job.lead_id == l.id,
                Job.status.in_(["queued", "retry"]),
            )
        ):
            job.status = "suppressed"
