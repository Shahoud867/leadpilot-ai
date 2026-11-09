# LeadPilot AI

A working, Pakistan-focused local sales demo: React/TypeScript/Vite/Tailwind, FastAPI, SQLAlchemy, SQLite WAL, six deterministic agents, and SciPy optimization. **All data, messages, deals, conversations and reported outcomes are simulated.** No paid services, API keys, external messaging account or LLM is required.

## Quick start (Python 3.12+, Node 22.12+)

Run from this repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
cd apps/web
npm ci
npm run build
cd ../..
python -m alembic -c services/api/alembic.ini upgrade head
python scripts/seed.py --seed 20261108 --reset --scenario all
python scripts/run_demo.py
```

Open **http://127.0.0.1:8000**. The API serves the built frontend on the same origin. SQLite persists in `demo.db`; closing and reopening the server preserves changes. The seed command is destructive to *demo* data; do not run it on a database you wish to keep. First startup seeds an empty migrated database automatically.

Windows: activate with `.venv\Scripts\activate`; the other Python/npm commands are identical. Native SciPy/NumPy wheels require a supported Python/platform combination. No Docker is required.

For development, use two terminals after migration/seed:

```bash
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
# other terminal
cd apps/web
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to port 8000. Use the same browser hostname throughout the demo because cookies are host-scoped.

## Demo accounts

Every seeded account uses **`Demo@2026!`**. The sign-in screen offers the principal accounts.

| Business | Email | Role |
|---|---|---|
| Margalla Skills · Demo | owner@margalla.example | Owner |
| Margalla Skills · Demo | manager@margalla.example | Manager |
| Margalla Skills · Demo | ayesha@margalla.example | Operator, own leads |
| Margalla Skills · Demo | bilal@margalla.example | Operator |
| Margalla Skills · Demo | hira@margalla.example | Operator |
| Margalla Skills · Demo | usman@margalla.example | Operator |
| Twin Cities Estates · Demo | owner@estates.example | Owner |
| Twin Cities Estates · Demo | viewer@estates.example | Viewer |
| Twin Cities Estates · Demo | sara@estates.example | Operator |
| Twin Cities Estates · Demo | hamza@estates.example | Operator |
| Twin Cities Estates · Demo | noor@estates.example | Operator |
| Twin Cities Estates · Demo | saad@estates.example | Operator |

This is a local demonstration, not a production deployment. Default credentials are public demo credentials. Bind to loopback for presentations.

## Workspaces and real interactions

Overview; inbox/capture and validated CSV preview/import; searchable/filterable/paginated directory with detail drawer; priority queue; qualification evidence; assignment optimizer and team configuration; guarded draggable pipeline; follow-ups and durable simulated message queue; lead recovery ledger; source/funnel/SLA/team analytics and hypothetical ROI calculator; six-agent decision journal; ten executable Demo Lab scenarios; team, RBAC, policies and audit settings.

The lead drawer provides edits, explicit consent updates, rescoring, follow-up scheduling, simulated replies, stage changes, manager assignment overrides, contact redaction, history, messages, recommendations and task actions. Every meaningful mutation is persisted. An unassigned lead stays unassigned when capacity or shift constraints prevent allocation.

## Tests and data validation

```bash
pytest services/api/tests -q
python scripts/validate_seed.py
cd apps/web
npm test
npm run build
npx playwright install chromium
# Run API and web development servers first, then:
npm run e2e
# Optional automated WCAG A/AA scan (same running servers):
npm run a11y
```

On Linux with system Chromium, omit browser download and run `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run e2e`. `npm run a11y` scans 21 views, including the sign-in page and lead detail tabs. Browser tests reset the first demo tenant; run them against a disposable demo database. Tests use a separate temporary SQLite database for API cases. See `TEST_REPORT.md` for actual execution evidence.

## Architecture

- `services/api/app/db.py`: typed tables, foreign keys, composite tenant constraints, WAL and sessions.
- `auth.py`: Argon2 verification, random opaque HTTP-only session cookies, hashed server-side session IDs and CSRF checks.
- `domain.py`: guarded pipeline, audit and domain events.
- `agents.py`: qualification, capacity/fairness MILP, follow-up, recovery and analytics traces.
- `service.py`: capture/dedup, overrides, customer simulator, approved job orchestration and aggregate metrics.
- `seed.py`: seeded fictional identities, histories and stable UUIDv5 records.
- `main.py`: Pydantic validation, scoped API routes, RBAC, rate limits, body caps, idempotency, clock and scenarios. OpenAPI: `/docs`.
- `apps/web/src`: responsive React UI, typed API transport and design system.
- `services/api/alembic`: versioned migrations. `scripts`: seed, integrity checks and launcher.

The virtual clock starts at 8 November 2026, noon PKT. Nothing secretly advances with wall-clock time. Approved messages run only when a manager processes the queue or advances time. Consent and terminal state are rechecked at delivery; all output remains inside SQLite. The simulation handles a connector timeout with persisted backoff/retry and correlation IDs.

## Decision policy

Qualification: interest 30, budget evidence 20, urgency up to 30, inquiry context 10 and local service fit up to 10. Missing facts remain explicit unknowns. The score is a priority heuristic, not a calibrated probability.

Allocation maximizes `0.40 fit + 0.25 urgency + 0.20 expected_SLA − 0.15 load`, subject to availability, PKT shifts, daily remaining capacity, one owner per lead and a maximum load-ratio gap of 0.25 when feasible. Infeasible fairness is explicitly relaxed and logged. The baseline uses deterministic lowest-current-load greedy assignment on identical inputs. Objective differences are not real-world conversion lift or proof of strategic equilibrium.

## Other deliverables

- `DEMO_GUIDE.md`: five-minute customer walkthrough.
- `IMPLEMENTATION_STATUS.md`: implementation choices and limits.
- `TEST_REPORT.md`: verified checks and outstanding limits.
- `DEPLOYMENT.md`: native startup, storage and free-hosting tradeoffs.
- `FUTURE_INTEGRATIONS.md`: official integration path and cost boundaries.
- `docs/architecture.md`, `data/schemas.sql`, `data/openapi.json`: architecture and generated contracts.
