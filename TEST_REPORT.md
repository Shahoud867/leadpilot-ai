# LeadPilot AI verification report

Executed in the managed Linux environment on 8 November 2026. Python 3.12.14, Node 24.22.1, SQLite, system Chromium, pinned application/build dependencies. All business evidence in these checks is synthetic.

**Final automated test total: 57 passing tests** (43 API + 7 frontend + 7 browser), plus 21 accessibility scans.

## Automated checks

| Check | Executed command | Result |
|---|---|---|
| API/domain/security | `pytest services/api/tests -q` | 43 passed |
| Frontend behavior/transport | `npm test` | 7 passed |
| Production compilation | `npm run build` | TypeScript and Vite build passed |
| Browser journeys | `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run e2e` | 7 passed |
| Automated accessibility | `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run a11y` | Zero WCAG A/AA violations reported across 21 scanned views |
| Fixture reconciliation | `python scripts/validate_seed.py` | Passed; no foreign-key violations, invalid identities, timestamp bounds or stage partition errors |
| Node dependency audit | `npm audit --json` | Zero known vulnerabilities at execution time |
| Python dependency audit | `pip-audit -r services/api/requirements.txt` | No known vulnerabilities at execution time |
| Fresh archive startup | `python scripts/run_demo.py` from a clean extraction | Passed: migration, automatic 3,000-lead seed, HTML/assets, login, intake, atomic replay and staff-response semantics |
| Migration bootstrap | Included API test: empty DB → head → 0001 → head | Passed with final schema and foreign keys |

API coverage includes anonymous denial, cookie attributes, CSRF checks, login throttling, owner/manager/operator/viewer restrictions, operator ownership, opaque cross-tenant reads/writes, cross-tenant representative/campaign rejection, capture orchestration, canonical deduplication, unknown-budget evidence, atomic idempotency/conflict handling, CSV dry-run atomicity, email/contact dedup preview parity, CSV formula neutralization, guarded pipeline and verified win, consent suppression/recheck, persistent retry without duplicate delivery, SLA detection, recovery deduplication even after manager dismissal, before/after override audit, exact [4,3,3] capacity matching, unavailable reps, persisted unassigned explanations, capacity-driven reassignment, analytics reconciliation, ten separate scenarios, tenant-only reset, deterministic seed checksum, event timestamp/FK integrity, scheduling/snoozing and contact redaction without stale recommendation links.

Two affected browser tests were also rerun successfully after making screenshot output paths portable to local project directories.

Browser coverage includes every workspace, manual capture → reply → qualification → appointment → verified won → reload/persistence, CSV preview/import/deduplication, missed SLA evidence, manager override, capacity reassignment, batch optimizer comparison, viewer denial, 390-pixel mobile layout/navigation and keyboard dialog behavior. The browser navigation test records zero JavaScript page errors.

The accessibility scan covers sign-in, all thirteen navigation workspaces, capture dialog, five lead-detail tabs and a populated conversation. It checks WCAG 2 A/AA and WCAG 2.1 AA rules with axe. Keyboard flow is tested separately. Automated scans are not a full assistive-technology certification.

## Reproducible seed

LP-1 seed 20261108: 2 tenants, 12 users, 8 reps, 8 campaigns, 3,000 leads, 14,714 events, 3,750 tasks, 4,768 communications, 3,000 historical assignments, 24 historical qualification recommendations and 124 audit rows including 100 duplicate attempts. Newly executed workflows add computed traces and audits.

Pure-seed business-data SHA256: `579603e9bdd2bad2a21763f01ca16c4f1dffe31e37069166458fff9649ad1432`. Salted password hashes and sessions are intentionally excluded. Tenant reset adds a reset audit; it reproduces the cohort, not the entire audit checksum.

## Performance evidence

An isolated 10,000-lead SQLite dataset seeded in 11.926 seconds. After warmup, ten API queries filtering a 1,001-lead Website cohort and returning 100 rows had median 14.51 ms and maximum 15.26 ms on this executor. This meets the local API filtering target. It is not a 1,000-DOM-row browser rendering benchmark or a remote production latency guarantee. Full measurement is in `docs/verification/benchmark.json`; rerun with `python scripts/benchmark.py`.

## Remaining limitations

No known critical defect remains in the tested workflows. One upstream TestClient deprecation notice recommends httpx2; the pinned httpx test transport passes. Vite reports a bundle-size advisory (approximately 638 kB minified JS / 185 kB gzip); the local browser journeys pass. The app uses a single-process SQLite queue and virtual time, and has no real provider adapters, production account provisioning, automated retention deletion, arbitrary event-stream replay or validated prediction model. Real conversion effectiveness, customer ROI, legal compliance, multi-process production operation and continuous availability were not tested or claimed.

Raw logs, dependency reports, fixture counts, benchmark and accessibility findings are retained under `docs/verification`. The source package excludes local session/database files and installed dependencies.
