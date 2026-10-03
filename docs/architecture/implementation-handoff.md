# Implementation handoff

## Decision and rationale

Implement the capability-oriented modular monolith defined by [ADRs](README.md#decision-register), [components](components.md), [ownership](data-model.md) and [contracts](contracts.md). One process/database allows atomic educational/commerce effects at pilot cost. Explicit ownership and a small coordination layer prevent hidden coupling and let further subjects reuse the same learning/commerce processes.

## Components affected and responsibilities

| Future owner | Concrete scope |
| --- | --- |
| Backend | Create `backend/` and Maven/Gradle wrapper; verify compatible supported Java/Spring versions; implement module public contracts, owner migrations, authorization and bounded adapters; add ArchUnit rules consuming the model; do not create empty business feature scaffolds without an actual feature task |
| Frontend | Create `frontend/` with supported Angular/Node/TypeScript versions and real npm scripts; feature-owned typed APIs/routing, session UX, responsive Polish interface, safe accessible mathematics; no server-authority rules in UI only |
| Infrastructure | Add requested root Compose dev/prod setup preserving landing; pinned images, production frontend build/proxy/fallback/TLS, PostgreSQL persistence/readiness, secrets, off-server backups/restore and monitoring |
| QA/security | Actor/resource isolation matrix, privileged MFA, historical/version correctness, progression/retake races, duplicate payments/crash recovery, file quarantine, migration upgrade, recovery and responsive/accessibility verification |
| Architect/reviewer | Resolve remaining significant choices before conflicting implementation; inspect compiled/source implementation against ADRs after each significant change |

## Contracts and constraints

[model.json](model.json) is the module import allowlist and logical ownership registry. [contracts](contracts.md) defines owner/consumer, authorization, transaction/idempotency and failure boundaries. It is not a final full-feature endpoint catalog. Every real feature must add concrete DTO/OpenAPI/event schemas and tests before declaring its contracts implemented. Adapters implement owner ports; provider credentials/models do not appear in domain APIs. Cross-module calls cannot import internal repositories or circumvent resource checks.

## Suggested sequence and validation gates

1. Resolve credential authority, parent-child login/recovery, account lifecycle and ADR-0006. Choose actual compatible supported toolchain and major dependencies using official then-current documentation.
2. Bootstrap only when requested: real build wrappers/scripts, migration tool, local/dev topology and architecture checks. Keep target documentation aligned with actual new paths/commands.
3. Implement a scoped end-to-end parent/child/catalog/group workflow with concrete program versions and access rules; prove resource isolation and ownership before adding commerce.
4. Resolve seat/late-settlement/refund policies and implement commerce + fulfillment with sandbox provider checks and duplicate/crash/concurrency evidence.
5. Implement lessons/homework/practice, historical assessments/manual grading/retakes and limited consultations, preserving versioned rules and audited exception paths.
6. Add reports/email and production release gates from [deployment](deployment.md); independently review architecture compliance before declaring readiness.

This sequence is guidance, not authorization to implement business features in this task. Product may reprioritize vertical slices while retaining the architectural gates.

## Migration and rollout

No existing educational production database needs migration in this baseline. Landing remains static and is not a consent/account database to import automatically. Future rollout uses [deployment](deployment.md)'s versioned migration and backup/restore/rollback process. Exact commands are documented only once supported tools actually exist.

## Risks, assumptions and open questions

The pilot is small enough for one server/process; no workload evidence supports a broker/cache/microservices. Single-server failure downtime is accepted as a baseline topology limitation pending agreed recovery goals. The workflow coordinator can become overly broad; keep business rules/data in owners and only compose real use cases.

Authentication, provider selection, commercial exceptions, retentions/recordings, exact program policies and numeric operational targets remain open in [requirements](../requirements/baseline.md). Identity choice must not delay writing owner-independent educational contracts, but does block authentication implementation. Legal/tax and educational example defaults are not established here.

## Verification limits

Baseline validation checks target/document coherence only. Application security, compiled boundaries, provider behavior, migrations, build compatibility, actual deployment, performance, accessible UI and recovery cannot be verified before implementation. [Constraints](constraints.md) distinguishes executed baseline checks from future checks.
