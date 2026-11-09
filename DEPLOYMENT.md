# Deployment and operations

## Guaranteed zero-mandatory-spend option

Use an already-owned laptop, Python 3.12+ and Node 22.12+. Follow README setup and run `python scripts/run_demo.py`. The built React UI and FastAPI API share `http://127.0.0.1:8000`; SQLite resides on durable local disk. After dependency installation and building, the demo runs without internet. No hosted fonts, CDNs, LLMs, commercial APIs or message delivery services are used.

Copy `.env.example` to `.env` only when changing defaults. Keep the database URL relative to the repository root, or use an absolute SQLite path. Run migrations before seeding and starting. A process restart preserves DB state. Reset is explicitly destructive to synthetic data and owner-only.

## Backups and recovery

Stop the server before copying `demo.db`, or use SQLite's backup API for a consistent live snapshot. Restore a copied database and run Alembic upgrade before starting. Never copy only `demo.db` during a write while ignoring its WAL. Keep one writer process: the application serializes mutations and the simulation runner is part of that process. Do not use multiple Uvicorn workers with this demo clock/queue implementation.

## Free-hosting options and limits

| Option | What works | Limitation |
|---|---|---|
| Local laptop | Entire app with persistent SQLite, PKR 0 new service fees | Equipment, electricity and time are not economically free |
| Cloudflare Pages | Static frontend | Does not run this Python API; needs a separate API and correct cookie/origin configuration |
| Free Python service tier | Potential short demonstration | Availability/terms change; sleep and ephemeral disks can destroy SQLite. Do not promise durable free hosting |
| Existing VM or server | Entire app behind HTTPS | Requires existing machine/access, backups and administration |

Sites hosting uses Cloudflare Workers and cannot execute this FastAPI/SQLite process directly. A static-only deployment would not satisfy the MVP, so the delivered application remains a local full-stack demo.

Before a real hosted pilot: replace demo credentials; introduce account provisioning; use HTTPS and `COOKIE_SECURE=true`; configure a precise origin allowlist; add host validation and distributed rate limiting; move to PostgreSQL and durable background workers; configure backups, secret management, monitoring, retention enforcement and consented data handling. Scope integrations and legal responsibilities with the client. These are production requirements, not evidence provided by synthetic tests.
