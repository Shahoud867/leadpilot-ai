"""Six deterministic agents. Allocation uses an explicit fairness-constrained MILP."""

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from sqlalchemy import select
from .db import *
from .domain import *


def qualify(db, l):
    factors = {
        "known_interest": 30 if l.interest != "Unknown" else 0,
        "budget_evidence": 20 if l.budget and l.budget >= 15000 else 0,
        "urgency": (
            30 if l.urgency == "today" else 18 if l.urgency == "this_week" else 8
        ),
        "inquiry_context": 10 if len(l.inquiry) >= 20 else 0,
        "local_service_fit": 10 if l.city in ("Islamabad", "Rawalpindi") else 5,
    }
    l.score = sum(factors.values())
    emit(db, l, "qualified_by_rules", {"score": l.score, "factors": factors})
    return trace(
        db,
        l,
        "Qualification",
        "Score inquiry",
        {"budget": l.budget, "urgency": l.urgency, "interest": l.interest},
        {
            "score": l.score,
            "contributions": factors,
            "confidence": "rule_based",
            "unknowns": ["budget"] if l.budget is None else [],
            "priority": l.score,
            "note": "Priority score is not a conversion probability.",
        },
    )


def load_snapshot(db, tid):
    clock = dt(now(db, tid)).astimezone(PKT)
    reps = sorted(rows(db, Rep, tid), key=lambda r: r.id)
    loads = {r.id: 0 for r in reps}
    for a in rows(db, Assignment, tid):
        if dt(a.created_at).astimezone(PKT).date() == clock.date():
            l = db.get(Lead, a.lead_id)
            if a.status == "active" and l.stage not in TERMINAL and not l.deleted:
                loads[a.rep_id] += 1
    return reps, loads, clock


def allocation_preview(db, tid, leads):
    reps, loads, clock = load_snapshot(db, tid)
    n, m = len(leads), len(reps)
    if not n or not m:
        return {
            "assignments": [],
            "baseline": [],
            "optimized_utility": 0,
            "baseline_utility": 0,
            "fairness_relaxed": False,
            "explanation": "No unassigned leads or representatives.",
        }
    cap = np.array(
        [
            (
                max(0, r.capacity - loads[r.id])
                if r.active and r.shift_start <= clock.hour < r.shift_end
                else 0
            )
            for r in reps
        ]
    )
    utilities = np.array(
        [
            [
                0.40 * (1 if l.interest in r.skills else 0.35)
                + 0.25
                * (
                    {"today": 1, "this_week": 0.6, "this_month": 0.25}.get(
                        l.urgency, 0.5
                    )
                )
                + 0.20 * r.response
                - 0.15 * (loads[r.id] / max(r.capacity, 1))
                for r in reps
            ]
            for l in leads
        ]
    )
    # Reward assignment cardinality first, then exact published utility. Deterministic ID tie break.
    c = -(10 + utilities).ravel() + np.arange(n * m) * 1e-6
    constraints = []
    for i in range(n):
        arr = np.zeros((n, m))
        arr[i, :] = 1
        constraints.append((arr.ravel(), 0, 1))
    for j in range(m):
        arr = np.zeros((n, m))
        arr[:, j] = 1
        constraints.append((arr.ravel(), 0, cap[j]))
    eligible = [
        j
        for j, r in enumerate(reps)
        if r.active and r.shift_start <= clock.hour < r.shift_end
    ]
    fair = []
    for j in eligible:
        for k in eligible:
            if j >= k:
                continue
            arr = np.zeros((n, m))
            arr[:, j] = 1 / reps[j].capacity
            arr[:, k] = -1 / reps[k].capacity
            offset = (
                loads[reps[j].id] / reps[j].capacity
                - loads[reps[k].id] / reps[k].capacity
            )
            fair.append((arr.ravel(), -0.25 - offset, 0.25 - offset))

    def solve(cs):
        return milp(
            c,
            integrality=np.ones(n * m),
            bounds=Bounds(0, 1),
            constraints=LinearConstraint(
                np.array([x[0] for x in cs]),
                np.array([x[1] for x in cs]),
                np.array([x[2] for x in cs]),
            ),
            options={"time_limit": 5},
        )

    result = solve(constraints + fair)
    relaxed = not result.success
    if relaxed:
        result = solve(constraints)
    x = np.rint(result.x).reshape(n, m) if result.success else np.zeros((n, m))
    baseline = []
    base_load = loads.copy()
    for i, l in enumerate(leads):
        opts = [j for j in eligible if base_load[reps[j].id] < reps[j].capacity]
        if opts:
            j = min(opts, key=lambda j: (base_load[reps[j].id], reps[j].id))
            base_load[reps[j].id] += 1
            baseline.append(
                {
                    "lead_id": l.id,
                    "rep_id": reps[j].id,
                    "utility": round(float(utilities[i, j]), 5),
                }
            )
    assignments = []
    unassigned_details = []
    for i, l in enumerate(leads):
        alternatives = [
            {
                "rep_id": r.id,
                "name": r.name,
                "utility": round(float(utilities[i, j]), 5),
                "fit": 1 if l.interest in r.skills else 0.35,
                "response": r.response,
                "load": loads[r.id],
                "capacity": r.capacity,
                "feasible": bool(cap[j] > 0),
                "reason": (
                    "off shift, unavailable or at capacity"
                    if cap[j] == 0
                    else "eligible; global utility and fairness compared"
                ),
            }
            for j, r in enumerate(reps)
        ]
        if not any(x[i, j] > 0.5 for j in range(m)):
            unassigned_details.append({"lead_id": l.id, "alternatives": alternatives})
        for j in range(m):
            if x[i, j] > 0.5:
                assignments.append(
                    {
                        "lead_id": l.id,
                        "lead_name": l.name,
                        "rep_id": reps[j].id,
                        "rep_name": reps[j].name,
                        "utility": round(float(utilities[i, j]), 5),
                        "alternatives": alternatives,
                    }
                )
    final = loads.copy()
    for a in assignments:
        final[a["rep_id"]] += 1
    ratios = [final[reps[j].id] / reps[j].capacity for j in eligible]
    return {
        "assignments": assignments,
        "unassigned": n - len(assignments),
        "unassigned_details": unassigned_details,
        "baseline": baseline,
        "optimized_utility": round(sum(a["utility"] for a in assignments), 4),
        "baseline_utility": round(sum(a["utility"] for a in baseline), 4),
        "fairness_relaxed": relaxed,
        "fairness_gap": round(max(ratios) - min(ratios), 3) if ratios else 0,
        "explanation": (
            "Fairness gap ≤0.25 enforced."
            if not relaxed
            else "Fairness infeasible under existing loads/capacity; relaxed and logged."
        ),
        "formula": "0.40 fit + 0.25 urgency + 0.20 expected SLA − 0.15 load",
        "is_simulated": True,
    }


def commit_allocation(db, tid, preview, actor="system"):
    for item in preview.get("unassigned_details", []):
        l = db.get(Lead, item["lead_id"])
        if l.owner_id:
            continue
        trace(
            db,
            l,
            "Allocation",
            "Unassigned: manager attention",
            {"score": l.score, "interest": l.interest},
            {
                "reason": "No remaining feasible slot under shift, capacity and allocation constraints.",
                "fairness_relaxed": preview["fairness_relaxed"],
            },
            item["alternatives"],
            status="recommended",
        )
        emit(db, l, "assignment_escalated", {"reason": "No feasible capacity"}, actor)
        audit(
            db,
            tid,
            actor,
            "assignment_unassigned",
            l.id,
            "Manager attention required: no feasible capacity",
        )
    for a in preview["assignments"]:
        l = db.get(Lead, a["lead_id"])
        if l.owner_id:
            continue
        l.owner_id = a["rep_id"]
        if l.stage in ("new", "reopened"):
            transition(db, l, "assigned", actor)
        db.add(
            Assignment(
                tenant_id=tid,
                lead_id=l.id,
                rep_id=l.owner_id,
                utility=a["utility"],
                approved_by=actor,
                created_at=now(db, tid),
            )
        )
        for t in db.scalars(
            select(Task).where(
                Task.tenant_id == tid, Task.lead_id == l.id, Task.status == "pending"
            )
        ):
            t.assigned_to = l.owner_id
        trace(
            db,
            l,
            "Allocation",
            f"Assign to {a['rep_name']}",
            {"score": l.score, "interest": l.interest},
            {
                "utility": a["utility"],
                "formula": preview["formula"],
                "fairness_relaxed": preview["fairness_relaxed"],
                "reason": preview["explanation"],
                "baseline_utility": preview["baseline_utility"],
                "optimized_utility": preview["optimized_utility"],
            },
            a["alternatives"],
        )
        emit(db, l, "assigned", {"rep_id": l.owner_id, "utility": a["utility"]}, actor)
    db.flush()


def schedule(db, l, due_at=None, kind="first_response"):
    task = Task(
        tenant_id=l.tenant_id,
        lead_id=l.id,
        assigned_to=l.owner_id,
        kind=kind,
        due_at=due_at
        or plus(
            now(db, l.tenant_id), db.get(Tenant, l.tenant_id).settings["sla_minutes"]
        ),
        created_at=now(db, l.tenant_id),
    )
    db.add(task)
    db.flush()
    trace(
        db,
        l,
        "Follow-up",
        "Schedule next action",
        {"consent": l.consent},
        {
            "due_at": task.due_at,
            "task_id": task.id,
            "human_approval_required": True,
            "simulated": True,
        },
    )
    emit(db, l, "task_scheduled", {"task_id": task.id, "due_at": task.due_at})
    return task


def recovery(db, tid):
    found = []
    existing = {
        (r.lead_id, r.inputs.get("task_id"), r.inputs.get("deadline"))
        for r in rows(db, Recommendation, tid)
        if r.agent == "Recovery"
    }
    for t in rows(db, Task, tid):
        l = db.get(Lead, t.lead_id)
        if (
            t.status == "pending"
            and t.due_at < now(db, tid)
            and l.stage not in TERMINAL
            and not l.deleted
            and (l.id, t.id, t.due_at) not in existing
        ):
            r = trace(
                db,
                l,
                "Recovery",
                "Manager review: missed SLA",
                {"task_id": t.id, "owner_id": l.owner_id, "deadline": t.due_at},
                {
                    "reason": "Response deadline exceeded",
                    "minutes_overdue": round(
                        (dt(now(db, tid)) - dt(t.due_at)).total_seconds() / 60
                    ),
                    "next_action": "Review workload and approve reassignment; leave-aware human review required.",
                },
                status="recommended",
            )
            emit(db, l, "sla_breached", {"task_id": t.id, "recommendation_id": r.id})
            found.append(r.id)
    return found


def analytics_trace(db, l):
    return trace(
        db,
        l,
        "Analytics",
        "Recompute persisted outcomes",
        {"stage": l.stage, "verified": l.outcome_verified},
        {
            "deal_value_pkr": l.deal_value,
            "is_simulated": True,
            "note": "Observed within simulation; no causal uplift claim.",
        },
    )
