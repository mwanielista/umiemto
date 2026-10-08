# eSzkola intended architecture

Architecture impact analysis verified: 2026-10-08. This proposal consumes approved BA revision 6 and SA revision 3; exact identities and approval evidence are in [implementation handoff](implementation-handoff.md). The requirement-impact delta is Proposed under [ADR-0008](decisions/0008-approved-requirement-impact.md). It is not application implementation or architecture approval.

## AS-IS

The verified application is the static Polish landing in `landing/`. Its waitlist stores demo entries in browser localStorage and does not create accounts or consents. Google Fonts is an external browser dependency. Nginx `1.27-alpine` serves static assets with 404 fallback; there is no API proxy, Angular routing, configured TLS or health check. Landing Compose exposes 8080 and uses restart `unless-stopped`; the repository-root project directory is required for its build context.

There is no `backend/`, `frontend/`, root Compose file, product database, migration, product API or application build/test wrapper. Python orchestration and its tests are repository governance tooling, not the product runtime.

The working tree contains all six Accepted ADRs (0001–0005 and 0007), Proposed ADR-0006, baseline principles and the unchanged architecture validator. Their bytes match HEAD `f94029b1486721893a4258ae07e6885272d06357`. Both existing validator variants pass against the actual checkout, including all six negative model cases. The earlier absence, exit-2 and missing-link statements describe an older checkout and are superseded by this verification.

Historical ARCH-001 is recorded in the existing handoff and [coordinator recovery decisions](architecture_decisions.md). The current controller context supplies no new `review_findings` object. Recovery presence, exact identities and configured checks are now verified; this Architect stage does not close a reviewer finding or approve architecture. See the [current recovery evidence](implementation-handoff.md#arch-001-recovery-handoff).

The supplied reservation excludes validation code and existing Accepted ADRs. This proposal refreshes affected architecture documentation only. The recovery document's proposed factual update preserves the coordinator's technical selections and records the same current evidence; its earlier incomplete-recovery statements are historical. Controller promotion must compare initial output/upstream identities, retain a complete architecture snapshot and baseline-relative diff including dirty/untracked bytes, then obtain independent read-only review and validation of the resulting package.

## TO-BE and impact

Preserve one Java/Spring Boot modular monolith, Angular/TypeScript web application, HTTP/JSON API, PostgreSQL with versioned migrations, private S3-compatible storage, external payment/video/email adapters and single-server Docker Compose. Keep the landing. Same-origin `/api/v1`, owner-prefixed persistence, immutable educational history, scoped authorization and PostgreSQL durable delivery remain valid.

The affected design now covers configurable completion and progression, free retakes without commerce entitlements, guardian lifecycle and privileged recovery, bounded consultations, purchased-term changes/refunds, lesson disruption, teacher-readiness evidence and pilot KPI. Reporting gains an explicit read dependency on commerce for financial KPI; no additional deployable or broad shared-data layer is proposed.

Approved BA/SA take precedence over conflicting historical business examples. Legacy SR-03, SR-04 and SR-05 are preserved as historical identifiers, with an explicit impact mapping in the handoff. Fixed four-lesson flow, unconditional prerequisite gating and paid retakes are not current business rules. Historical educational-template prices and thresholds are examples/superseded assumptions.

## Views and contracts

| Artifact | Purpose |
| --- | --- |
| [System context](system-context.md), [containers](containers.md) | C4 actors, trust and runtime boundaries |
| [Components](components.md), [model](model.json) | Responsibilities, import allowlist and single data ownership |
| [Data model](data-model.md), [contracts](contracts.md) | Consistency, historical evidence and public contract boundaries |
| [Security](security.md), [integrations](integrations.md) | Resource access, files, provider verification and recovery |
| [NFRs](nfr.md), [deployment](deployment.md) | Approved measurable objectives and release evidence |
| [Constraints](constraints.md), [principles](principles.md) | Fitness functions and retained baseline principles |
| [Implementation handoff](implementation-handoff.md) | Exact input gate, traceability, owners, verification and remaining gates |

## Decision register

| ADR | Historical status | Current treatment |
| --- | --- | --- |
| [0001](decisions/0001-modular-monolith-boundaries.md) | Accepted | Preserve capability modules, public contracts and acyclic imports; ownership/import additions are proposed in 0008 |
| [0002](decisions/0002-owned-persistence-and-history.md) | Accepted | Preserve owned persistence, immutable versions and local consistency |
| [0003](decisions/0003-durable-effects-and-payments.md) | Accepted | Preserve durable delivery/payment deduplication; 0008 proposes explicit partial supersession of retake-entitlement fulfillment only |
| [0004](decisions/0004-resource-authorization.md) | Accepted | Preserve role plus resource checks, MFA and transactional audit |
| [0005](decisions/0005-runtime-and-api-boundary.md) | Accepted | Preserve same-origin API, Compose topology and provider boundaries |
| [0006](decisions/0006-authentication-options.md) | Proposed | Credential authority remains unresolved; business login/recovery rules are now specified by SA |
| [0007](decisions/0007-deterministic-analysis-orchestration.md) | Accepted | Preserve controller-owned writes and exact external approval evidence |
| [0008](decisions/0008-approved-requirement-impact.md) | Proposed | Requirement-impact delta and narrowly scoped replacement of paid-retake design |

No Accepted ADR is rewritten, marked accepted or silently reinterpreted by this stage. Authentication implementation requires resolution of ADR-0006; new architecture choices require adoption of ADR-0008. BA/SA approval is not approval of these architecture decisions.

## Checks available now

The repository BA/SA structural and external-approval gates pass for the exact consumed inputs. All 24 FRs and 10 NFRs trace to the 26 input BRs, both artifacts have zero unresolved BLOCKER questions, and SA consumes the approved BA revision/content.

Both unchanged architecture checker variants configured in `config/pipeline.yaml` were executed directly with the existing virtual-environment interpreter and bytecode writes disabled: PASS, exit 0. They verify 13 target modules, unique ownership, acyclic imports, ADR structure/status, ownership-table alignment and existing local Markdown destinations. The self-test rejects six invalid models. Landing Compose configuration also passes; no service was started.

These results cover the current checkout. Proposed file contents require validation after controller promotion and independent review of the complete resulting package. Proposed ADR adoption remains separate from requirements approval and executable validation.

Compiled rules, migrations, provider tests, load/accessibility tests and recovery exercises remain downstream responsibilities. No application implementation or operational objective is verified by this stage.
