# Deployment and operational target

AS-IS: only `landing/docker-compose.yml` with static Nginx on 8080 exists. Its configuration check was executed successfully using repository-root project directory. No application runtime, production deployment or migration exists. Preserve the landing; no service was started or configuration edited in this stage.

## Retained topology

[ADR-0005](decisions/0005-runtime-and-api-boundary.md) remains binding: single-server Docker Compose, Angular production build/web server with route fallback and same-origin API forwarding, one Spring monolith, private PostgreSQL/persistent volume and private S3-compatible files. HTTPS exposes only required edge ports; backend/database/management stay private. External file storage does not introduce another product deployable.

Select compatible supported pinned toolchains/images at actual bootstrap; no current vendor/version support claim is made here. Separate dev/prod credentials/configuration. Distinguish container health, database readiness, migration completion and backend readiness. Restart policies never substitute for recovery or durable delivery.

Secrets stay outside Git; runtime and recovery access are least privilege. Trust only configured proxy forwarding. Keep diagnostics redacted/restricted with default 30-day retention, separate from audit. Monitoring covers availability, provider failures, permanent data failures, scan backlog and backup integrity. Do not introduce a monitoring platform/broker/cache without a measured need.

## Availability and incident controls

NFR-003 sets 99.5% monthly measured controlled-process availability. Per-process one-minute synthetic checks and app fault evidence follow [nfr.md](nfr.md); partial process outages count. Maintenance exclusion requires ≥24-hour user notice and recorded exclusion evidence. Inform families of lesson disruption without an invented global notification SLA.

NFR-008 requires critical alert at five consecutive unavailable minutes, three consecutive failed critical-integration attempts, permanent data read/write failure and significant authorization/payment/file-error growth. Configure thresholds outside domain code. SA-Q-009 must resolve growth baseline/window and retry timing semantics before operational acceptance. Incident ownership/escalation and monitoring implementation must be documented when selected.

## Migrations, rollout and rollback

One reviewed globally ordered migration stream retains owner-prefixed data and immutable history. Choose the migration library at bootstrap; no product migration command exists. Apply migrations once before starting compatible images; never rely on ORM production auto-update or uncontrolled concurrent migration runners.

Prefer additive expand/contract changes and bounded verified backfill. Rehearse empty-database creation and upgrade with real PostgreSQL. Back up before destructive changes. Restore/forward-fix plans must preserve payments/submissions arriving after a backup. Rollback uses a previous immutable image only if compatible with current schema; an image rollback does not undo persisted state.

These proposals do not migrate a deployed educational database or retake table, because none exists. An intentionally adopted model delta needs future versioned migrations for the implemented slice. Landing localStorage entries are not an account/consent import. Never remove user volumes during routine rollout.

## Backup and measured restore

NFR-004 requires RPO ≤24 hours and RTO ≤4 hours, including 15 continuous healthy minutes. Operations must implement encrypted off-server database backups, verified integrity, recoverable object versions/inventory and secure independent secrets/recovery configuration. A named volume is not a backup. Backup intervals, transfer delays and restore procedure must demonstrate the bounds; a nominal daily schedule alone does not prove RPO.

Backup/audit/object retention remains approved production policy, not an invented duration. Use point-in-time recovery only when needed to meet the agreed objective. Retain provider identifiers, durable callback/delivery/refund/request keys and appropriate session metadata for safe reconciliation.

Isolated restore covers all NFR-004 data classes, matching DB/object versions and complete basic processes. Test historical assessments, guardian authority, enrollment/refund uniqueness, consultation quota and protected audit. Compare durable pre-failure events to restored state for RPO. Measure from earliest detection/confirmation through 15-minute stability for RTO. Reconcile provider outcomes before releasing pending dispatch/replay; uncertain refund requests cannot be sent anew without verification. Document actual scripts only when the chosen infrastructure exists.

## Production gates

Before corresponding production use: TLS/private exposure, supported pinned builds, proxy/SPA routing, migrations/compatible rollback, resource/MFA/recovery controls, sandbox verified payments/refunds, clean private attachments, load evidence, monitoring, off-server backup and measured full restore. SA-Q-010 additionally covers final consent/privacy/retention/rights/processor agreements, VAT/sales documents, consumer procedures and teacher safeguards. Approved BA/SA do not certify those gates.

No operational gate is claimed to pass beyond the existing landing configuration check.
