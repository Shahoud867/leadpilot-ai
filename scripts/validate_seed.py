import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api"))
from sqlalchemy import select, func, text
from app.db import *
from app.seed import checksum
from app.domain import STAGES

with SessionLocal() as db:
    assert not db.execute(text("PRAGMA foreign_key_check")).all()
    totals = {
        model.__tablename__: db.scalar(select(func.count()).select_from(model))
        for model in [
            Tenant,
            User,
            Rep,
            Campaign,
            Lead,
            Event,
            Task,
            Communication,
            Assignment,
            Recommendation,
            Audit,
        ]
    }
    for l in db.scalars(select(Lead)):
        assert (
            l.stage in STAGES
            and l.contact.startswith("SYN-")
            and (not l.email or l.email.endswith(".example"))
        )
        assert (
            l.is_synthetic
            and l.created_at <= l.updated_at <= db.get(Tenant, l.tenant_id).clock
        )
        assert not l.owner_id or db.get(Rep, l.owner_id).tenant_id == l.tenant_id
        assert l.stage != "won" or l.outcome_verified and l.deal_value > 0
    for e in db.scalars(select(Event)):
        l = db.get(Lead, e.lead_id)
        assert (
            l.tenant_id == e.tenant_id
            and l.created_at <= e.created_at <= db.get(Tenant, l.tenant_id).clock
        )
    for t in db.scalars(select(Tenant)):
        ls = db.scalars(select(Lead).where(Lead.tenant_id == t.id)).all()
        assert sum(sum(l.stage == s for l in ls) for s in STAGES) == len(ls)
    print(
        json.dumps(
            {"valid": True, "counts": totals, "checksum": checksum(db)}, indent=2
        )
    )
