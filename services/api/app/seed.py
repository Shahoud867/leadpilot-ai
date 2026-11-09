"""Reproducible LP-1 synthetic histories. No dialable contacts or live identities."""

import random, uuid, hashlib, json
from sqlalchemy import delete, select
from .db import *
from .auth import ph
from .domain import plus

BASE = "2026-11-08T07:00:00+00:00"


def stable(kind, n):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"leadpilot/{kind}/{n}"))


NAMES = [
    "Ayesha",
    "Ahmed",
    "Fatima",
    "Hassan",
    "Zainab",
    "Usman",
    "Maryam",
    "Bilal",
    "Hira",
    "Hamza",
    "Sana",
    "Ali",
    "Iqra",
    "Saad",
    "Noor",
    "Daniyal",
    "Mehwish",
    "Omar",
    "Mahnoor",
    "Talha",
]


def seed(
    db, seed_value=20261108, count=3000, reset=False, tenant_only=None, commit=True
):
    if reset:
        for table in reversed(Base.metadata.sorted_tables):
            if tenant_only:
                if "tenant_id" in table.c:
                    db.execute(delete(table).where(table.c.tenant_id == tenant_only))
            else:
                db.execute(delete(table))
        db.flush()
    rng = random.Random(seed_value)
    password = ph.hash("Demo@2026!")
    for ti in range(2):
        tid = stable("tenant", ti)
        rng = random.Random(seed_value + ti)
        if tenant_only and tid != tenant_only:
            continue
        tenant = db.get(Tenant, tid)
        settings = {
            "sla_minutes": 30,
            "timezone": "Asia/Karachi",
            "currency": "PKR",
            "retention_days": 180,
            "seed": seed_value,
            "seed_version": "LP-1",
            "simulation_rule_version": "LP-1",
        }
        if tenant:
            tenant.clock = BASE
            tenant.settings = settings
        else:
            db.add(
                Tenant(
                    id=tid,
                    name=["Margalla Skills · Demo", "Twin Cities Estates · Demo"][ti],
                    clock=BASE,
                    settings=settings,
                )
            )
        db.flush()
        reps = []
        for j in range(6):
            user_id = stable("user", ti * 6 + j)
            email = (
                ["owner", "manager", "ayesha", "bilal", "hira", "usman"][j]
                if ti == 0
                else ["owner", "viewer", "sara", "hamza", "noor", "saad"][j]
            ) + ("@margalla.example" if ti == 0 else "@estates.example")
            if not db.get(User, user_id):
                db.add(
                    User(
                        id=user_id,
                        email=email,
                        name=(
                            [
                                "Aamir Khan",
                                "Sara Malik",
                                "Ayesha Noor",
                                "Bilal Ahmed",
                                "Hira Saeed",
                                "Usman Ali",
                            ]
                            if ti == 0
                            else [
                                "Zain Malik",
                                "Nida Shah",
                                "Sara Ali",
                                "Hamza Raza",
                                "Noor Khan",
                                "Saad Ahmed",
                            ]
                        )[j],
                        password_hash=password,
                    )
                )
            db.flush()
            db.add(
                Membership(
                    id=stable("member", ti * 6 + j),
                    tenant_id=tid,
                    user_id=user_id,
                    role=[
                        "owner",
                        "manager" if ti == 0 else "viewer",
                        "operator",
                        "operator",
                        "operator",
                        "operator",
                    ][j],
                )
            )
            if j >= 2:
                interests = (
                    ["Data Science", "IELTS", "Web Development", "Digital Marketing"]
                    if ti == 0
                    else [
                        "Bahria Apartment",
                        "DHA Plot",
                        "Commercial Office",
                        "Rental Home",
                    ]
                )
                r = Rep(
                    id=stable("rep", ti * 4 + j - 2),
                    tenant_id=tid,
                    user_id=user_id,
                    name=db.get(User, user_id).name,
                    skills=[interests[(j - 2) % 4], interests[(j - 1) % 4]],
                    capacity=[12, 10, 14, 12][j - 2],
                    response=[0.9, 0.75, 0.85, 0.8][j - 2],
                )
                db.add(r)
                reps.append(r)
        db.flush()
        sources = ["WhatsApp", "Instagram", "Website", "Walk-in"]
        campaigns = []
        for k, s in enumerate(sources):
            c = Campaign(
                id=stable("campaign", ti * 4 + k),
                tenant_id=tid,
                name=(
                    [
                        "November admissions",
                        "Autumn open house",
                        "Scholarship inquiry",
                        "Campus visits",
                    ][k]
                    if ti == 0
                    else [
                        "Bahria launch",
                        "DHA listings",
                        "Commercial spaces",
                        "Office visits",
                    ][k]
                ),
                source=s,
            )
            db.add(c)
            campaigns.append(c)
        db.flush()
        interests = (
            ["Data Science", "IELTS", "Web Development", "Digital Marketing"]
            if ti == 0
            else ["Bahria Apartment", "DHA Plot", "Commercial Office", "Rental Home"]
        )
        for i in range(count // 2):
            ordinal = ti * 1000000 + i
            # Keep recent active cases as well as six months of reconciled histories.
            mins = rng.randint(180, 240) if i < 32 else rng.randint(300, 180 * 1440)
            created = plus(BASE, -mins)
            r = reps[i % 4]
            source = rng.choices(range(4), [45, 25, 20, 10])[0]
            depth = rng.choices([1, 2, 3, 4, 5, 6], [20, 25, 20, 13, 10, 12])[0]
            stages = ["new", "assigned"]
            if depth >= 2:
                stages.append("contacted")
            if depth >= 3:
                stages.append("qualified")
            if depth >= 4:
                stages.append("appointment")
            if depth == 5:
                stages.append("won")
            if depth == 6:
                stages.append("lost")
            consent = (
                "opted_out" if i % 13 == 0 else "unknown" if i % 17 == 0 else "granted"
            )
            l = Lead(
                id=stable("lead", ordinal),
                tenant_id=tid,
                external_id=f"LP-{ti}-{i:06}",
                name=f"{NAMES[i%len(NAMES)]} {i+1:04} · Test",
                contact=f"SYN-PK-{ti}-{i:06}",
                email=f"lead-{ti}-{i}@synthetic.example",
                source=sources[source],
                campaign_id=campaigns[source].id,
                city=rng.choices(["Islamabad", "Rawalpindi", "Taxila"], [45, 40, 15])[
                    0
                ],
                interest=interests[i % 4],
                inquiry=(
                    f"Assalam-o-Alaikum, please share details for {interests[i%4]}. I would like to discuss the next available session."
                    if ti == 0
                    else f"Please share the location and viewing times for {interests[i%4]}."
                ),
                budget=(
                    rng.choice([None, 15000, 35000, 65000, 120000])
                    if ti == 0
                    else rng.choice([None, 1500000, 5000000, 12000000])
                ),
                urgency=rng.choice(["today", "this_week", "this_month"]),
                stage=stages[-1],
                owner_id=r.id,
                score=rng.choice([48, 65, 78, 90, 100]),
                consent=consent,
                consent_source="synthetic_fixture",
                consent_at=created if consent == "granted" else None,
                opt_out_at=created if consent == "opted_out" else None,
                created_at=created,
                updated_at=created,
                responded_at=plus(created, rng.randint(3, 120)) if depth >= 2 else None,
                appointment_at=plus(created, 180) if depth >= 4 else None,
                outcome_verified=depth == 5,
                deal_value=(
                    (
                        rng.choice([25000, 45000, 65000, 95000])
                        if ti == 0
                        else rng.choice([1500000, 2500000, 6000000])
                    )
                    if depth == 5
                    else 0
                ),
            )
            l.score = (
                (30 if l.interest != "Unknown" else 0)
                + (20 if l.budget and l.budget >= 15000 else 0)
                + (
                    30
                    if l.urgency == "today"
                    else 18 if l.urgency == "this_week" else 8
                )
                + 10
                + (10 if l.city in ("Islamabad", "Rawalpindi") else 5)
            )
            l.first_response_at = l.responded_at if consent == "granted" else None
            l.updated_at = l.responded_at or created
            db.add(l)
            db.flush()
            kinds = [
                ("captured", {"synthetic": True, "source": l.source}),
                ("consent_recorded", {"status": consent}),
            ] + [
                ("stage_changed", {"from": stages[k - 1], "to": stages[k]})
                for k in range(1, len(stages))
            ]
            for e, (kind, payload) in enumerate(kinds):
                db.add(
                    Event(
                        id=stable("event", f"{ordinal}-{e}"),
                        tenant_id=tid,
                        lead_id=l.id,
                        kind=kind,
                        payload=payload,
                        created_at=(
                            l.responded_at
                            if kind == "stage_changed"
                            and payload.get("to")
                            in ("contacted", "qualified", "appointment", "won", "lost")
                            else created
                        ),
                        correlation_id=stable("correlation", ordinal),
                        actor="seed",
                    )
                )
            db.add(
                Assignment(
                    id=stable("assignment", ordinal),
                    tenant_id=tid,
                    lead_id=l.id,
                    rep_id=r.id,
                    utility=0.6,
                    approved_by="seed",
                    created_at=created,
                )
            )
            task = Task(
                id=stable("task", ordinal),
                tenant_id=tid,
                lead_id=l.id,
                assigned_to=r.id,
                due_at=plus(created, 30),
                status="completed" if depth >= 2 else "pending",
                completed_at=l.responded_at,
                created_at=created,
            )
            db.add(task)
            if i < 50:
                db.add(
                    Audit(
                        id=stable("duplicate-attempt", ordinal),
                        tenant_id=tid,
                        actor="seed",
                        action="duplicate_detected",
                        target_id=l.id,
                        reason="LP-1 deliberate duplicate attempt; canonical record preserved",
                        before={},
                        after={"canonical_id": l.id, "merge_review_required": True},
                        created_at=created,
                    )
                )

            if i % 4 == 0:
                db.add(
                    Task(
                        id=stable("task-extra", ordinal),
                        tenant_id=tid,
                        lead_id=l.id,
                        assigned_to=r.id,
                        kind="follow_up",
                        due_at=plus(BASE, rng.randint(-90, 180)),
                        status="canceled" if l.stage in ("won", "lost") else "pending",
                        created_at=created,
                    )
                )
            if depth >= 2:
                for d in ["outbound", "inbound"]:
                    db.add(
                        Communication(
                            id=stable("message", f"{ordinal}-{d}"),
                            tenant_id=tid,
                            lead_id=l.id,
                            direction=d,
                            channel=l.source,
                            body=(
                                "Simulated: thank you for your inquiry."
                                if d == "outbound"
                                else "Simulated: I would like more details, please."
                            ),
                            status=(
                                "sent_simulated"
                                if d == "outbound" and consent == "granted"
                                else (
                                    "suppressed"
                                    if d == "outbound"
                                    else "received_simulated"
                                )
                            ),
                            consent_snapshot=consent,
                            created_at=l.responded_at,
                        )
                    )
            if i < 12:
                db.add(
                    Recommendation(
                        id=stable("recommendation", ordinal),
                        tenant_id=tid,
                        lead_id=l.id,
                        agent="Qualification",
                        action="Score inquiry",
                        inputs={"budget": l.budget, "interest": l.interest},
                        alternatives=[],
                        explanation={
                            "score": l.score,
                            "confidence": "rule_based",
                            "note": "Synthetic historical fixture; rerun to inspect current rule contributions.",
                        },
                        status="applied",
                        created_at=created,
                    )
                )
                db.add(
                    Audit(
                        id=stable("audit", ordinal),
                        tenant_id=tid,
                        actor="seed",
                        action="fixture_generated",
                        target_id=l.id,
                        reason="LP-1 synthetic history",
                        before={},
                        after={"stage": l.stage},
                        created_at=created,
                    )
                )
        db.flush()
    if commit:
        db.commit()


def checksum(db):
    payload = []
    for model in [
        Tenant,
        Membership,
        Rep,
        Campaign,
        Lead,
        Event,
        Assignment,
        Task,
        Communication,
        Recommendation,
        Audit,
    ]:
        payload.extend(
            [
                {"table": model.__tablename__, **serialize(x)}
                for x in db.scalars(select(model).order_by(model.id))
            ]
        )
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
