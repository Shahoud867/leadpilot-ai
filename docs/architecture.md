# Domain architecture and operating boundaries

HTTP requests resolve membership on the server. All tenant entities carry a tenant ID; service queries include that ID, and foreign IDs return opaque 404s. Operators read and mutate only their owned leads. Managers allocate, configure adviser availability and run simulations; owners additionally change policies/roles, redact contacts and reset their tenant. Viewers read and export. Every new production endpoint must use the same scoped boundary.

SQLite uses foreign keys and WAL. Mutations run through one process-wide lock and one transaction. The idempotency result and domain events commit together; an exception rolls back both. Session cookies hold a high-entropy opaque value, only its SHA256 digest is persisted, Argon2 verifies passwords, CSRF tokens protect mutations and sessions expire after eight wall-clock hours. The virtual business clock never affects session expiry.

The orchestrated path is capture → qualification → allocation → scheduled task → explicit outbound approval → queued simulated delivery → customer response → guarded pipeline → analytics. `lead_events` are the domain event journal; `recommendations` preserve input snapshots, policy version, factors and alternatives. `audit_events` record manager overrides, settings, duplicate attempts, stage changes, clock/reset and redaction. Contact redaction intentionally clears contact payloads and appends a redaction audit. Demo reset is an explicit owner exception to historical preservation.

## Deterministic agents

| Agent | Inputs | Outputs and guardrails |
|---|---|---|
| Capture | validated synthetic inquiry and tenant contact/email | canonical lead or linked duplicate review; never overwrites an existing contact |
| Qualification | interest, budget evidence, urgency, context, city | contributions totaling 0–100, unknown fields and rule-based confidence; no probability claim |
| Allocation | lead batch, rep skills, capacity, shift, active status, current-day assignments | MILP plan and greedy baseline on same batch; alternatives; fairness enforcement or logged relaxation |
| Follow-up | consent and SLA setting | persistent task; explicit send approval creates persistent job; consent rechecked at delivery |
| Recovery | pending task, deadline and virtual clock | deduplicated missed-SLA recommendation; manager chooses reassignment or dismissal |
| Analytics | event progression, persisted lead outcomes and captured date cohort | reconciled funnel, conversion denominators, staff-response SLA and source/team metrics |

Fairness uses all on-duty active reps, not only the selected specialist. Capacity is daily active assignments in PKT, not total open historical leads. Optimization first maximizes the number of feasible assignments, then published policy utility. Unavailable/off-shift reps have zero remaining capacity. The fairness gap constraint may reduce utility relative to greedy; a negative comparison is reported honestly. This is constrained cooperative allocation, not a Nash equilibrium claim. Managers retain contextual vetoes; no compensation or staff sanction mechanism exists.

## Queue and simulation adapters

Manual, CSV and scenario inputs share capture/deduplication. Simulation outputs go only to the communications table. Jobs record tenant, lead, task, correlation, creation/due time, lease, status, retry count, last error and payload. Worker ticks are explicit, not wall-clock background threads. A two-minute lease and retry backoff demonstrate durability; repeated process ticks do not redeliver completed jobs. Injected timeout creates a retry event, then succeeds on the next eligible tick. Terminal leads, redacted contacts and absent/withdrawn consent suppress delivery.

Customer reply time and first staff response are separate fields. Only a delivered simulated adviser message sets `first_response_at`. A customer reply leaves the adviser response task pending; a delivered staff message completes remaining first-response obligations. Customer replies provide evidence for contacted/qualified/appointment progression. Won requires an explicit verified outcome and positive monetary value. Booking an appointment does not itself create a won deal.

## Data contract

LP-1 defaults to 3,000 leads over 180 days in two fictional tenants. Each tenant has its own seeded RNG, stable UUIDv5 namespace, contacts with SYN IDs, .example email domains and seeded histories. There are 100 deliberate duplicate attempt audit records. Totals are computed from generated rows; independent marketing totals are not invented. `scripts/validate_seed.py` checks foreign keys, tenant membership, non-dialable identities, timestamp bounds, verified wins and stage partitions. `checksum` hashes stable business rows and excludes password salts/sessions. Per-tenant reset recreates the same cohort regardless of the other tenant's state.

## Explicit limitations

The database snapshots and event journal are reconciled for implemented transitions; this is not a general event-sourcing replay framework. Historical fixture assignments carry synthetic policy utility; newly executed allocations contain full computed comparisons. No synthetic-trained ML model is presented as validated. The retention setting is a documented policy and explicit redaction control, not a scheduled production deletion service. There is no live webhook, payment, email, calendar, WhatsApp or CRM provider. These require separately consented official adapters. Single-process local operation is the verified deployment target.
