# Future official integrations

The MVP has no live providers and never sends external messages. Existing capture, consent checks, event history, queues, retry fields and correlation IDs form an adapter boundary for a later controlled pilot.

| Integration | Implementation path | Cost boundary |
|---|---|---|
| WhatsApp Cloud API | Verified Meta business/app, approved number, opt-in provenance, templates, official webhooks with signature verification, deduplication by provider event ID, approved outbound jobs and delivery callbacks | Meta's current regional/category message pricing, possible BSP fees and number/hosting costs. Verify official prices at implementation time; not guaranteed free |
| Email | Client-approved SMTP or transactional provider, sender/domain authentication, unsubscribe handling and verified delivery events | Provider allowance may be free at small volume; paid delivery, domain, support and hosting may apply |
| CRM import/sync | Client-approved OAuth/API access, field mapping, sanitized CSV first, dry-run reconciliation, ID mapping and conflict resolution | CRM plan/API limits and integration maintenance may require payment |
| Calendar | Official Google/Microsoft OAuth with least scopes, explicit appointment approval, time zones, cancel/reschedule and webhook reconciliation | Provider account/license requirements and hosting vary |
| Forms/webhooks | Authenticated endpoint, signed payloads, replay protection, stable idempotency, validation and consent source | Small-volume hosting may have free allowances; availability is not guaranteed |

Start with a customer-assisted CSV pilot and manually execute real outreach in existing tools. Connect only official providers after consent, platform permissions, credentials and pricing are confirmed. No scraping, unofficial WhatsApp automation, bulk outreach or browser impersonation.

Never request secrets in chat. Configure server-side credential storage, environment variables or a secret manager. Test webhook authenticity, duplicate callbacks, timeouts, revocation, opt-outs, retention, provider failure and reconciliation before enabling live sends. Retain human approval for real outbound work until pilot evidence supports a scoped change.

No claim is made that synthetic scores, simulated conversions or assumed ROI establish real effectiveness. Compare a consented baseline or randomized/matched cohorts, including labor, software, acquisition, setup, messaging and support costs.
