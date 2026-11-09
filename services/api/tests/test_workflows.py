import json, hashlib
import pytest
from sqlalchemy import select, func
from app.db import *
from app.seed import seed, checksum, stable
from app.agents import allocation_preview, commit_allocation, load_snapshot
from app.domain import plus, now
from app.main import app
from fastapi.testclient import TestClient

P = "/api/v1"


def test_auth_and_secure_session(client):
    assert client.get(P + "/auth/me").json()["role"] == "owner"
    r = client.post(
        P + "/auth/login",
        json={"email": "owner@margalla.example", "password": "Demo@2026!"},
    )
    assert (
        "HttpOnly" in r.headers["set-cookie"]
        and "SameSite=strict" in r.headers["set-cookie"]
    )
    assert client.get(P + "/health").headers["X-Content-Type-Options"] == "nosniff"


def test_denies_anonymous_and_csrf():
    with TestClient(app) as c:
        assert c.get(P + "/leads").status_code == 401
        c.post(
            P + "/auth/login",
            json={"email": "owner@margalla.example", "password": "Demo@2026!"},
        )
        assert (
            c.post(P + "/demo/clock/advance", json={"minutes": 31}).status_code == 403
        )


def test_login_rate_limit():
    with TestClient(app) as c:
        for _ in range(15):
            assert (
                c.post(
                    P + "/auth/login", json={"email": "absent", "password": "bad"}
                ).status_code
                == 401
            )
        assert (
            c.post(
                P + "/auth/login", json={"email": "absent", "password": "bad"}
            ).status_code
            == 429
        )


def test_tenant_boundary(client):
    foreign = stable("lead", 1000000)
    assert client.get(P + "/leads/" + foreign).status_code == 404
    assert (
        client.patch(
            P + "/leads/" + foreign, json={"name": "Bad", "reason": "test"}
        ).status_code
        == 404
    )
    assert client.post(P + "/leads/" + foreign + "/qualify", json={}).status_code == 404
    assert (
        client.post(
            P + "/leads/" + foreign + "/override",
            json={"rep_id": stable("rep", 4), "reason": "test"},
        ).status_code
        == 404
    )


def test_cross_tenant_rep_and_campaign(client, make):
    l = make(client)
    assert (
        client.post(
            P + f"/leads/{l['id']}/override",
            json={"rep_id": stable("rep", 4), "reason": "test"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            P + "/leads",
            json={
                "name": "Bad Test",
                "contact": "SYN-BAD",
                "source": "Website",
                "city": "Islamabad",
                "interest": "IELTS",
                "inquiry": "Test inquiry",
                "campaign_id": stable("campaign", 4),
            },
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "email,role",
    [("viewer@estates.example", "viewer"), ("ayesha@margalla.example", "operator")],
)
def test_roles(email, role):
    with TestClient(app) as c:
        r = c.post(P + "/auth/login", json={"email": email, "password": "Demo@2026!"})
        c.headers["X-CSRF-Token"] = r.json()["csrf"]
        assert c.get(P + "/auth/me").json()["role"] == role
        assert (
            c.post(
                P + "/demo/reset", json={"confirmation": "RESET SYNTHETIC DATA"}
            ).status_code
            == 403
        )
        assert (
            c.patch(
                P + "/settings", json={"sla_minutes": 10, "retention_days": 30}
            ).status_code
            == 403
        )
        assert (
            c.post(
                P + "/leads",
                json={
                    "name": "New",
                    "contact": "SYN-RBAC",
                    "source": "Website",
                    "city": "Islamabad",
                    "interest": "IELTS",
                    "inquiry": "Testing role permissions",
                },
            ).status_code
            == 403
        )
        for l in c.get(P + "/leads").json()["items"]:
            if role == "operator":
                assert l["owner_id"] == c.get(P + "/auth/me").json()["rep_id"]


def test_intake_and_duplicate(client, make):
    before = client.get(P + "/leads").json()["total"]
    l = make(client)
    assert l["stage"] in ("assigned", "new") and l["score"] == 100
    detail = client.get(P + "/leads/" + l["id"]).json()
    assert len(detail["tasks"]) == 1
    assert {"Capture", "Qualification", "Allocation", "Follow-up"} <= {
        r["agent"] for r in detail["recommendations"]
    }
    make(client, name="Must not overwrite")
    assert client.get(P + "/leads").json()["total"] == before + 1
    assert (
        client.get(P + "/leads/" + l["id"]).json()["lead"]["name"] == "API Ayesha Test"
    )
    assert any(
        a["action"] == "duplicate_detected" for a in client.get(P + "/audit").json()
    )


def test_missing_budget_unknown(client, make):
    l = make(client, budget=None)
    d = client.get(P + "/leads/" + l["id"]).json()
    r = next(r for r in d["recommendations"] if r["agent"] == "Qualification")
    assert (
        "budget" in r["explanation"]["unknowns"]
        and r["explanation"]["confidence"] == "rule_based"
    )


def test_idempotency_and_conflict(client):
    d = {"minutes": 31}
    h = {"Idempotency-Key": "repeat"}
    a = client.post(P + "/demo/clock/advance", json=d, headers=h)
    b = client.post(P + "/demo/clock/advance", json=d, headers=h)
    assert a.json() == b.json() and b.headers.get("X-Idempotent-Replay") == "true"
    assert (
        client.post(
            P + "/demo/clock/advance", json={"minutes": 60}, headers=h
        ).status_code
        == 409
    )


def test_csv_atomic_validation_and_dedup(client):
    text = "name,contact,source,city,interest,inquiry\nAyesha Test,SYN-CSV,Website,Islamabad,IELTS,Please share details\nAyesha Other,SYN-CSV,Website,Islamabad,IELTS,Please share details"
    before = client.get(P + "/leads").json()["total"]
    d = client.post(
        P + "/leads/import", json={"csv_text": text, "dry_run": True}
    ).json()
    assert d["created"] == 1 and d["duplicates"] == 1
    assert client.get(P + "/leads").json()["total"] == before
    d = client.post(
        P + "/leads/import", json={"csv_text": text, "dry_run": False}
    ).json()
    assert d["created"] == 1 and d["duplicates"] == 1
    bad = client.post(
        P + "/leads/import",
        json={"csv_text": text.replace("SYN-CSV", "03001234567"), "dry_run": False},
    ).json()
    assert not bad["valid"] and bad["created"] == 0
    assert client.get(P + "/leads").json()["total"] == before + 1


def test_csv_formula_sanitization(client, make):
    make(client, name="=1+2")
    make(client, name=" =1+2", contact="SYN-CSV-SPACE")
    r = client.get(P + "/leads/export")
    assert "'=1+2" in r.text and "' =1+2" in r.text and "SIMULATED DATA" in r.text


def test_guarded_pipeline_and_verified_outcome(client, make):
    l = make(client)
    url = P + "/leads/" + l["id"]
    assert (
        client.post(
            url + "/transition", json={"stage": "won", "verified": True, "value": 1}
        ).status_code
        == 422
    )
    assert (
        client.post(url + "/transition", json={"stage": "contacted"}).status_code == 422
    )
    assert (
        client.post(
            url + "/reply", json={"body": "Simulated: Please book a consultation."}
        ).status_code
        == 200
    )
    assert (
        client.post(url + "/transition", json={"stage": "qualified"}).status_code == 200
    )
    clock = client.get(P + "/settings").json()["clock"]
    assert (
        client.post(
            url + "/transition",
            json={"stage": "appointment", "appointment_at": plus(clock, 1440)},
        ).status_code
        == 200
    )
    assert (
        client.post(
            url + "/transition", json={"stage": "won", "value": 65000}
        ).status_code
        == 422
    )
    assert (
        client.post(
            url + "/transition", json={"stage": "won", "value": 65000, "verified": True}
        ).status_code
        == 200
    )
    assert client.get(url).json()["lead"]["outcome_verified"]


@pytest.mark.parametrize("consent", ["unknown", "opted_out"])
def test_consent_suppression(client, make, consent):
    l = make(client, consent=consent)
    t = client.get(P + "/leads/" + l["id"]).json()["tasks"][0]
    assert (
        client.post(
            P + "/tasks/" + t["id"] + "/action", json={"action": "send"}
        ).status_code
        == 200
    )
    client.post(P + "/jobs/process", json={})
    d = client.get(P + "/leads/" + l["id"]).json()
    assert all(m["status"] == "suppressed" for m in d["messages"])


def test_consent_recheck_after_enqueue(client, make):
    l = make(client)
    t = client.get(P + "/leads/" + l["id"]).json()["tasks"][0]
    client.post(P + "/tasks/" + t["id"] + "/action", json={"action": "send"})
    client.patch(
        P + "/leads/" + l["id"],
        json={"consent": "opted_out", "reason": "Customer refused"},
    )
    client.post(P + "/jobs/process", json={})
    assert client.get(P + "/jobs").json()[0]["status"] == "suppressed"


def test_persistent_retry_and_no_duplicate_delivery(client, make):
    l = make(client)
    t = client.get(P + "/leads/" + l["id"]).json()["tasks"][0]
    url = P + "/tasks/" + t["id"] + "/action"
    assert (
        client.post(url, json={"action": "send", "inject_failure": True}).status_code
        == 200
    )
    assert client.post(url, json={"action": "send"}).status_code == 409
    client.post(P + "/jobs/process", json={})
    assert client.get(P + "/jobs").json()[0]["status"] == "retry"
    client.post(P + "/demo/clock/advance", json={"minutes": 2})
    client.post(P + "/jobs/process", json={})
    d = client.get(P + "/leads/" + l["id"]).json()
    assert len(d["messages"]) == 1 and d["messages"][0]["status"] == "sent_simulated"


def test_sla_and_recovery_dedup(client, make):
    l = make(client)
    client.post(P + "/demo/clock/advance", json={"minutes": 31})
    r = [
        r
        for r in client.get(P + "/recommendations?agent=Recovery").json()
        if r["lead_id"] == l["id"]
    ]
    assert len(r) == 1
    client.post(P + "/recovery/scan", json={})
    assert (
        len(
            [
                r
                for r in client.get(P + "/recommendations?agent=Recovery").json()
                if r["lead_id"] == l["id"]
            ]
        )
        == 1
    )


def test_override_audit(client, make):
    l = make(client)
    team = client.get(P + "/team").json()
    r = next(r for r in team if r["id"] != l["owner_id"] and r["load"] < r["capacity"])
    a = client.post(
        P + "/leads/" + l["id"] + "/override",
        json={"rep_id": r["id"], "reason": "Prior consultation context"},
    )
    assert a.status_code == 200
    ev = next(
        a for a in client.get(P + "/audit").json() if a["action"] == "agent_override"
    )
    assert (
        ev["before"]["owner_id"] == l["owner_id"] and ev["after"]["owner_id"] == r["id"]
    )


def test_optimization_capacity_and_baseline(client):
    r = client.post(P + "/demo/scenarios/burst/run", json={})
    assert r.status_code == 200, r.text
    d = r.json()["comparison"]
    assert d["optimized_utility"] >= 0 and len(d["assignments"]) + d["unassigned"] == 20
    assert all(r["load"] <= r["capacity"] for r in client.get(P + "/team").json())
    for a in d["assignments"]:
        assert len(a["alternatives"]) == 4


def test_all_unavailable(client, make):
    for r in client.get(P + "/team").json():
        client.patch(
            P + "/team/" + r["id"],
            json={
                k: (False if k == "active" else r[k])
                for k in ["capacity", "active", "shift_start", "shift_end", "skills"]
            },
        )
    l = make(client)
    assert l["owner_id"] is None
    p = client.post(P + "/assignments/preview", json={"lead_ids": [l["id"]]}).json()
    assert not p["assignments"] and p["unassigned"] == 1


def test_exact_capacity_reference():
    with SessionLocal() as db:
        tid = stable("tenant", 0)
        for a in db.scalars(select(Assignment).where(Assignment.tenant_id == tid)):
            a.status = "historical"
        reps = db.scalars(
            select(Rep).where(Rep.tenant_id == tid).order_by(Rep.id)
        ).all()
        for i, r in enumerate(reps):
            r.capacity = [4, 3, 3, 1][i]
            r.active = i < 3
        leads = db.scalars(select(Lead).where(Lead.tenant_id == tid).limit(10)).all()
        for l in leads:
            l.owner_id = None
            l.stage = "new"
        db.flush()
        p = allocation_preview(db, tid, leads)
        commit_allocation(db, tid, p)
        db.flush()
        _, loads, _ = load_snapshot(db, tid)
        assert len(p["assignments"]) == 10 and [loads[r.id] for r in reps[:3]] == [
            4,
            3,
            3,
        ]


def test_analytics_reconcile(client):
    m = client.get(P + "/analytics?days=0").json()
    assert sum(m["stages"].values()) == m["total"]
    assert sum(s["leads"] for s in m["sources"]) == m["total"]
    assert sum(r["revenue"] for r in m["team"]) == m["revenue"]
    assert m["funnel"][0]["count"] == m["total"]


@pytest.mark.parametrize(
    "key",
    [
        "inquiry",
        "high_value",
        "sla",
        "capacity",
        "appointment",
        "override",
        "conversion",
        "burst",
        "opt_out",
        "retry",
    ],
)
def test_each_scenario_from_clean_fixture(client, key):
    r = client.post(P + "/demo/scenarios/" + key + "/run", json={})
    assert r.status_code == 200, r.text
    assert (
        r.json()["is_simulated"]
        and r.json()["after"]["total"] > r.json()["before"]["total"]
    )


def test_reset_is_tenant_scoped_and_repeatable(client, make):
    with SessionLocal() as db:
        before = [
            serialize(l)
            for l in db.scalars(
                select(Lead)
                .where(Lead.tenant_id == stable("tenant", 1))
                .order_by(Lead.id)
            )
        ]
    make(client)
    r = client.post(P + "/demo/reset", json={"confirmation": "RESET SYNTHETIC DATA"})
    assert r.status_code == 200, r.text
    assert client.get(P + "/auth/me").status_code == 200
    with SessionLocal() as db:
        after = [
            serialize(l)
            for l in db.scalars(
                select(Lead)
                .where(Lead.tenant_id == stable("tenant", 1))
                .order_by(Lead.id)
            )
        ]
    assert before == after
    assert client.get(P + "/leads").json()["total"] == 1500


def test_seed_checksum_and_event_integrity():
    with SessionLocal() as db:
        a = checksum(db)
        seed(db, count=120, reset=True)
        assert a == checksum(db)
        for e in db.scalars(select(Event)):
            l = db.get(Lead, e.lead_id)
            assert (
                l.tenant_id == e.tenant_id
                and l.created_at <= e.created_at <= db.get(Tenant, l.tenant_id).clock
            )
        assert (
            db.execute(__import__("sqlalchemy").text("PRAGMA foreign_key_check")).all()
            == []
        )


def test_task_schedule_and_snooze(client, make):
    l = make(client)
    clock = client.get(P + "/settings").json()["clock"]
    r = client.post(P + "/tasks", json={"lead_id": l["id"], "due_at": plus(clock, 120)})
    assert r.status_code == 200
    tid = r.json()["id"]
    assert client.post(
        P + "/tasks/" + tid + "/action", json={"action": "snooze", "minutes": 240}
    ).json()["due_at"] == plus(clock, 240)


def test_redaction(client, make):
    l = make(client)
    r = client.post(
        P + "/leads/" + l["id"] + "/delete",
        json={"reason": "Synthetic deletion request"},
    )
    assert r.status_code == 200
    assert client.get(P + "/leads/" + l["id"]).status_code == 404
    assert not any(
        r["lead_id"] == l["id"] for r in client.get(P + "/recommendations").json()
    )
    with SessionLocal() as db:
        lead = db.get(Lead, l["id"])
        assert lead.name == "Redacted synthetic contact" and not lead.email
        for rec in db.scalars(
            select(Recommendation).where(Recommendation.lead_id == l["id"])
        ):
            assert not rec.inputs


def test_staff_sla_is_independent_of_customer_reply(client, make):
    l = make(client)
    url = P + "/leads/" + l["id"]
    task = client.get(url).json()["tasks"][0]
    client.post(url + "/reply", json={"body": "Simulated: I am still waiting."})
    assert client.get(url).json()["lead"]["first_response_at"] is None
    assert client.get(url).json()["tasks"][0]["status"] == "pending"
    # A separate approved follow-up is a staff response, even after customer reply.
    clock = client.get(P + "/settings").json()["clock"]
    t = client.post(
        P + "/tasks", json={"lead_id": l["id"], "due_at": plus(clock, 60)}
    ).json()
    client.post(P + "/tasks/" + t["id"] + "/action", json={"action": "send"})
    client.post(P + "/jobs/process", json={})
    assert client.get(url).json()["lead"]["first_response_at"] == clock
    original = next(x for x in client.get(url).json()["tasks"] if x["id"] == task["id"])
    assert original["status"] == "completed"


def test_recovery_decision_is_not_duplicated_on_rescan(client, make):
    l = make(client)
    client.post(P + "/demo/clock/advance", json={"minutes": 31})
    rec = next(
        r
        for r in client.get(P + "/recommendations?agent=Recovery").json()
        if r["lead_id"] == l["id"]
    )
    client.post(
        P + "/recommendations/" + rec["id"] + "/decision",
        json={"action": "dismiss", "reason": "Reviewed with manager"},
    )
    client.post(P + "/recovery/scan", json={})
    assert (
        len(
            [
                r
                for r in client.get(P + "/recommendations?agent=Recovery").json()
                if r["lead_id"] == l["id"]
            ]
        )
        == 1
    )


def test_import_preview_matches_email_deduplication(client):
    text = "name,contact,email,source,city,interest,inquiry\nFirst Test,SYN-EMAIL-1,test@synthetic.example,Website,Islamabad,IELTS,Please share more details\nSecond Test,SYN-EMAIL-2,test@synthetic.example,Website,Islamabad,IELTS,Please share more details"
    preview = client.post(
        P + "/leads/import", json={"csv_text": text, "dry_run": True}
    ).json()
    result = client.post(
        P + "/leads/import", json={"csv_text": text, "dry_run": False}
    ).json()
    assert (
        preview["created"] == result["created"] == 1
        and preview["duplicates"] == result["duplicates"] == 1
    )


def test_frozen_migrations_on_empty_database(tmp_path):
    import subprocess, sys, os, sqlite3
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + str(tmp_path / "migrated.db")}
    cmd = [sys.executable, "-m", "alembic", "-c", "services/api/alembic.ini"]
    for action in [["upgrade", "head"], ["downgrade", "0001"], ["upgrade", "head"]]:
        r = subprocess.run(
            cmd + action, cwd=root, env=env, capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr
    with sqlite3.connect(tmp_path / "migrated.db") as c:
        assert "first_response_at" in {
            r[1] for r in c.execute("PRAGMA table_info(leads)")
        }
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []


def test_capacity_scenario_reassigns_and_audits(client):
    result = client.post(P + "/demo/scenarios/capacity/run", json={})
    assert result.status_code == 200, result.text
    d = client.get(P + "/leads/" + result.json()["lead_ids"][0]).json()
    assert len(d["assignments"]) == 2
    assert any(
        e["kind"] == "agent_override"
        and "capacity constraint" in e["payload"]["reason"]
        for e in d["events"]
    )
    assert all(r["load"] <= r["capacity"] for r in client.get(P + "/team").json())


def test_unassigned_decision_is_persistently_explained(client, make):
    for r in client.get(P + "/team").json():
        client.patch(
            P + "/team/" + r["id"],
            json={
                k: (False if k == "active" else r[k])
                for k in ["capacity", "active", "shift_start", "shift_end", "skills"]
            },
        )
    lead = make(client)
    d = client.get(P + "/leads/" + lead["id"]).json()
    rec = next(r for r in d["recommendations"] if r["agent"] == "Allocation")
    assert rec["status"] == "recommended" and len(rec["alternatives"]) == 4
    assert any(e["kind"] == "assignment_escalated" for e in d["events"])
