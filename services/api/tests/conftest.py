import os, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = (
    "sqlite:///" + tempfile.mkdtemp(prefix="leadpilot-tests-") + "/test.db"
)
import pytest
from fastapi.testclient import TestClient
from app.db import Base, engine, SessionLocal
from app.seed import seed
from app.main import app, attempts


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db, count=120, reset=True)
    attempts.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/auth/login",
            json={"email": "owner@margalla.example", "password": "Demo@2026!"},
        )
        assert r.status_code == 200
        c.headers["X-CSRF-Token"] = r.json()["csrf"]
        yield c


@pytest.fixture
def make():
    def f(c, **extra):
        d = {
            "name": "API Ayesha Test",
            "contact": "SYN-API-NEW",
            "source": "Website",
            "city": "Islamabad",
            "interest": "Data Science",
            "inquiry": "Please share the course details. I would like to enroll today.",
            "budget": 65000,
            "urgency": "today",
            "consent": "granted",
            **extra,
        }
        r = c.post("/api/v1/leads", json=d)
        assert r.status_code == 200, r.text
        return r.json()["lead"]

    return f
