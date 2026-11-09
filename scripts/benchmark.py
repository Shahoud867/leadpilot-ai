"""Isolated 10k-row API filter benchmark. Does not mutate the presentation DB."""

import os, sys, tempfile, time, json, statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api"))
folder = tempfile.TemporaryDirectory(prefix="leadpilot-benchmark-")
os.environ["DATABASE_URL"] = "sqlite:///" + folder.name + "/benchmark.db"
from app.db import Base, engine, SessionLocal
from app.seed import seed
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(engine)
start = time.perf_counter()
with SessionLocal() as db:
    seed(db, count=10000, reset=True)
seed_seconds = time.perf_counter() - start
with TestClient(app) as client:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@margalla.example", "password": "Demo@2026!"},
    )
    assert r.status_code == 200
    path = "/api/v1/leads?source=Website&page_size=100"
    client.get(path)
    values = []
    for _ in range(10):
        start = time.perf_counter()
        response = client.get(path)
        values.append((time.perf_counter() - start) * 1000)
        assert response.status_code == 200
    print(
        json.dumps(
            {
                "seeded_leads": 10000,
                "seed_seconds": round(seed_seconds, 3),
                "filter_matches": response.json()["total"],
                "returned_page_size": len(response.json()["items"]),
                "warm_requests": 10,
                "median_filter_ms": round(statistics.median(values), 2),
                "maximum_filter_ms": round(max(values), 2),
                "under_one_second": max(values) < 1000,
                "scope": "Local TestClient end-to-end API; excludes browser rendering and remote network",
            },
            indent=2,
        )
    )
engine.dispose()
folder.cleanup()
