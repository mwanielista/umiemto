# Deployment and operational baseline

## AS-IS commands

From repository root, configuration validation is:

```bash
docker compose --project-directory . -f landing/docker-compose.yml config
```

Starting the existing landing (not executed by this architecture task):

```bash
docker compose --project-directory . -f landing/docker-compose.yml up --build -d
```

Default project-directory resolution from the Compose file would incorrectly target `landing/landing` for its build. The explicit project directory preserves the existing file. No root Compose file, application build/test command or production deployment exists. This baseline does not change container/image versions or start services.

## TO-BE topology and responsibilities

Follow [ADR-0005](decisions/0005-runtime-and-api-boundary.md). Add backend/frontend/PostgreSQL to a documented root Compose setup when bootstrap is explicitly requested; preserve landing. Separate development from production configuration, environment credentials and data. Select supported compatible pinned runtimes/dependencies/images at that time; this baseline avoids unsupported claims about then-current versions.

Frontend uses a dedicated Angular build stage and a production web server with route fallback and `/api` forwarding. HTTPS edge exposes only needed 443 and, where required, 80 for redirect/certificate validation. Backend/database are private; do not publish database or metrics/admin ports. Separate container health checks, database readiness and migration completion before backend readiness; restart policies do not replace these checks. A database outage must not turn backend readiness green or discard pending work. Private S3 storage can be external without changing the single-server application topology.

Secrets are mounted/provided at deployment, with safe placeholders only in examples. Runtime credentials and backup access are least privilege. Rotate payment/identity/storage secrets using provider procedures; do not log them. Centralize/rotate structured logs initially on the server and alert on readiness, failed callbacks/delivery, backup failure and storage scan backlog. Select an operational monitoring tool only with a concrete requirement; no additional observability platform is part of the baseline.

## Migration and rollout

One globally ordered versioned migration stream, reviewed for owner prefixes and immutable history preservation. Choose a migration library at bootstrap; no command is available yet. Never rely on production ORM schema auto-update. Migration credentials are separate from runtime where practical. Use deployment sequencing that applies migrations once, records success, and starts only compatible backend images; concurrently starting multiple app instances must not race migrations.

Use additive expand/contract changes for persisted/public compatibility: introduce new fields/tables, migrate/backfill with bounded verified jobs, deploy compatible code, remove old structure only after rollback window. Backup before destructive migrations. Do not reverse accepted historical content by rewriting migrations. Rehearse empty-database creation and upgrade from previous schema with real PostgreSQL before release.

Rollback uses the last compatible immutable application image when schema permits. Destructive migrations require a separately tested recovery/forward-fix plan; rolling back an image does not undo database state. User submissions/payments acquired after a backup must be reconciled before accepting a destructive restore. Never routinely delete database/object volumes to redeploy.

## Backup and restore

Database volume survives container recreation but is not a backup. Operations must implement encrypted off-server PostgreSQL backups with retention, access control and integrity checks; periodic database dumps may be enough only if agreed RPO allows their interval, otherwise choose a justified point-in-time recovery method. Set RPO/RTO and retention with product before production rather than promising invented targets.

Object storage needs its own recoverable backup/versioning policy and inventory consistent with database object metadata. Include protected audit/history and any selected database session/delivery state. Provider transaction references must survive restoration for reconciliation. Secrets/recovery configuration need secure independent recovery, not plain-text inclusion in repository/backups.

Restore rehearsal: provision isolated environment; restore database and matching object inventory; apply only compatible migrations; validate sample historical attempts, authorized parent access, payment/fulfillment uniqueness and audit; reconcile provider settlements before replaying pending work; measure recovery time and evidence. Document exact commands/scripts once chosen infrastructure exists. Do not test recovery destructively against production.

## Readiness gates

Before real child data/payments: production TLS, correct API/SPA routing, supported pinned images, migration upgrade/rollback evidence, authorization/MFA checks, sandbox payment lifecycle, private clean attachments, off-server backup + restore rehearsal, retention/provider review, monitoring and incident owner. These are future release responsibilities; no baseline document claims they pass today.
