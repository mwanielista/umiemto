# ADR-0005: Single-server runtime and same-origin API boundary

## Status
Accepted — 2026-10-03. Target decision; landing alone is implemented.

## Context
SR-09,12,15 and AGENTS.md fix Angular, Spring Boot, PostgreSQL, S3-compatible storage, external payments/video and Docker Compose. Existing landing uses one Nginx container.

## Problem
Define deployable/API/integration boundaries and operational recovery without prematurely implementing infrastructure.

## Constraints
Preserve landing, pin supported versions at bootstrap, HTTPS in production, private database/backend exposure, versioned migrations and recoverable persistent data.

## Considered options
Same-origin Angular + `/api` reverse proxy simplifies browser trust/routing. Separate frontend/API origins are possible but require CORS/cookie policy without a current requirement. Single-server Compose fits pilot constraints; managed/distributed application topology is unjustified today.

## Decision
Serve Angular with production web server, route fallback and same-origin `/api/v1` to one Spring monolith. Use private PostgreSQL/persistent volume, private S3-compatible objects and owner-defined provider adapters. Initial deployment is one Compose server with HTTPS edge and preserved landing. Separate dev/prod config; protect secrets and private management endpoints. Define readiness, ordered migrations, backup/restore and compatible-image rollback in [deployment](../deployment.md).

## Rationale
Small operational footprint and a clear browser/backend boundary. External service choice remains reversible behind domain ports.

## Consequences
Single-server outage affects platform availability; backups and practiced restoration are essential. A volume is not backup. Exact versions/providers/tooling and numeric service targets are future choices, not claims of implemented support.

## Risks
Single failure domain, stale dependencies, proxy header errors, inconsistent DB/object recovery, destructive migration rollback.

## Rejected alternatives
Unpinned latest images, public database/admin ports, production HTTP only, routine volume deletion, speculative Kubernetes/Redis/broker/video infrastructure.

## Validation / fitness functions
Run available landing Compose configuration check. At bootstrap add actual builds, production proxy/SPA/TLS and port/readiness checks, migration upgrade evidence, off-server backup and isolated restore rehearsal, supported version verification and provider-neutral contract tests.
