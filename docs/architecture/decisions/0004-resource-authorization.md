# ADR-0004: Role plus resource authorization and privileged audit

## Status
Accepted — 2026-10-03. Target decision; not implemented.

## Context
SR-01,08–10,14 require protecting child data, guardian/teacher scope, separated privileged responsibilities and MFA. Authentication mechanism is still open in ADR-0006.

## Problem
Define authority independently of UI visibility and prevent broad roles from exposing unrelated children/resources.

## Constraints
Backend enforcement; guardian resource relation, assigned teacher scope, separated support/education/admin access, MFA, minimal child data, audited important changes.

## Considered options
Role-only authorization is easy but cannot satisfy resource isolation. A standalone authorization service adds a distributed boundary without need. Owner-local policies using shared verified identity and authoritative relation contracts preserve resource ownership inside the monolith.

## Decision
Identity owns account/guardian/consent/grant data; resource owners enforce their policies using verified actor, current grants/assurance and resource relations. All entry points including lists/files/reports/internal workflows enforce scoped authority. Privileged changes and audit append share a transaction. No general admin bypass; MFA required for privileged actors. [Security](../security.md) defines access and trust boundaries.

## Rationale
Owners know resource scope and avoid a central policy module depending cyclically on all domains. Authentication/provider choices can remain separate from authorization contracts.

## Consequences
Every feature must specify an access matrix and negative tests. Restricted internal workflow authority carries original actor/event evidence. Uploads quarantine until scanning and owner authorization succeed.

## Risks
Stale relationship caches, cross-resource enumeration, service authority abused as a bypass, recovery paths lowering MFA assurance.

## Rejected alternatives
Hidden UI buttons as security, broad roles without resource checks, unrestricted staff child access, public buckets, secrets in browser storage/logs.

## Validation / fitness functions
Future integration tests substitute unauthorized child/group/order/file IDs and revoked guardian/teacher assignments; require MFA; ensure audit failure rolls back privileged mutation; verify file scan fail-closed and no answer-key leakage. No implementation security behavior can be tested now.
