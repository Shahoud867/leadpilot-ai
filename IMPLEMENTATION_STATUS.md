# LeadPilot AI implementation

## Dependency ordered checklist
- [x] 1. Migrations, SQLite, sessions, memberships and tenant boundaries.
- [x] 2. Reproducible historical seed, intake, deduplication, import and guarded pipeline.
- [x] 3. Six deterministic agents, constrained matching, trace, persisted jobs and recovery.
- [x] 4. Fourteen responsive SaaS workspaces with operational controls.
- [x] 5. Eight demo scenarios, virtual clock, replies, baseline comparisons and reset.
- [x] 6. API, frontend and browser checks; security and integrity validation.
- [x] 7. Local startup, demo guide, source archive and final verification.

## Decisions made before implementation
- Local demonstration is the deployment target: a Python/SQLite API cannot be hosted in the Sites Worker runtime. No paid or external communication service is used.
- The blueprint's embedded master prompt is document content; the actual pasted request authorizes implementation and defines scope.
- Historical dataset totals are derived, not forced to arbitrary independent communication/event counts. Target: 3,000 leads, two fictional businesses, twelve users, eight reps; reproducible relational histories.
- Rule-based qualification is the default. Optional synthetic-trained prediction is excluded from decision making because it provides no validated signal.
- Daily workload means active assignments created on the simulated PKT calendar day. Working hours and availability constrain allocation; historical open cases remain visible separately.
- Fairness is an explicit MILP constraint; when infeasible, relax it with an explanation. Conventional baseline: deterministic lowest-current-load greedy assignment.
- Jobs run on explicit simulated worker ticks (advance clock or process queue), with leases, bounded retries and backoff. They do not run on real wall-clock time.
- Operator access is limited to owned leads; managers and owners control assignments. Viewer reads/exports only. The second tenant uses separate demo accounts.
- Amounts are PKR; dates are persisted UTC and rendered Asia/Karachi.


## Implemented application

Thirteen navigable workspaces plus the lead-detail workspace cover every requested MVP screen. Intake, CSV preview/import, canonical duplicate detection, searchable/paginated lists, priority ordering, rescoring, edits, consent, task scheduling/snoozing/completion, simulated approval/send/reply, pipeline moves, future appointments, verified positive-value wins, owner contact redaction, assignment preview/confirmation, manager overrides, team capacity/shifts/skills, policy changes, membership roles, reports and audit inspection persist in SQLite.

The six agents use real rule/optimization logic with versioned snapshots and alternatives. Staff first response and customer reply are separate. Allocation records infeasible/unassigned outcomes for manager attention instead of silently dropping them. Recovery is deduplicated per task deadline even after a manager decision. The capacity scenario explicitly reassigns a lead under a changed adviser capacity and audits both changes.

Ten executable scenarios cover all eight required demonstrations plus consent refusal and retryable connector failure. Before/after metrics derive from persisted states. Time advancement runs recovery and approved jobs. Tenant reset is owner-only with explicit typed confirmation; each tenant has an independent seeded RNG.

Security controls: Argon2 hashes, random opaque HTTP-only SameSite cookies, eight-hour real-time expiry, CSRF validation, per-role/per-lead tenant checks, opaque foreign-tenant 404s, login throttling, one-MiB body limits, Pydantic input validation, bounded imports, CSV formula neutralization, composite uniqueness, foreign keys and request IDs. Domain mutations and idempotency results share one transaction. No audit-edit/delete API exists; explicit contact redaction scrubs identifying payloads with a redaction audit.

## Intentional limits and specification resolutions

- Verified target is a single-process local demo. Multi-worker hosting, actual providers, commercial guarantees and live customer operation are outside this MVP.
- LP-1 generates 3,000 leads, 14,714 events, 3,750 tasks, 4,768 simulated communications, 100 deliberate duplicate-attempt audits, two fictional tenants, twelve users and eight reps. Exact generated totals replace independent illustrative blueprint counts. Histories are reconciled and fixtures are deterministic.
- Historical assignments carry synthetic utility values; newly executed assignments have computed utility and alternatives. Scoring is rule-based. No synthetic-trained ML efficacy claim is made.
- Daily load counts active assignments made on the current PKT calendar day. Historical open cases are reported separately. Simulated shifts apply every day, including the presentation's Sunday date; no holiday calendar is assumed.
- A simulation worker tick is explicit, leased, persistent and idempotent. There is no hidden real-time background sender. Only the simulation connector is operational; CSV/scenarios feed the same capture logic. Official inbound webhooks are future integrations.
- Retention is configurable policy metadata with explicit owner redaction. Automated scheduled deletion is deferred to preserve demo evidence. Audit history is preserved except explicit synthetic reset and contact redaction.
- Event history and snapshots reconcile for implemented transitions; arbitrary historical event-stream replay and configurable workflow authoring are future work. Reset reproduces the fixture; it is not arbitrary event-sourcing replay.
- No staff pay changes, sanctions, broadcast messages, scraped contacts, live integrations or paid AI dependencies exist. Optimization utility is not strategic equilibrium or observed conversion lift.
- Initial migration is frozen DDL; the second migration separately introduces staff-response timing. Upgrade/downgrade/re-upgrade is tested on an empty SQLite database.
- The frontend ships as one approximately 638 kB minified JS bundle (about 185 kB gzip). Vite reports a size advisory; local load and functional browser tests pass. Further code splitting is a production optimization.

## Verification

43 API tests, 7 frontend tests, 7 browser journeys and 21 zero-violation automated accessibility scans pass. Both dependency audits report zero known vulnerabilities. See TEST_REPORT.md and docs/verification for executed results, dependency audit snapshots, seed reconciliation, performance measurement, browser checks and screenshots. No tested critical journey remains broken. No real-world conversion effectiveness, production availability or privacy-law compliance is claimed.
