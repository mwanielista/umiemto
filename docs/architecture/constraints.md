# Architecture constraints and fitness functions

[model.json](model.json) is a target public-import allowlist and single-owner registry, not implementation evidence. Retain Accepted boundaries from ADRs 0001–0005 and 0007. [ADR-0008](decisions/0008-approved-requirement-impact.md) identifies Proposed additions and partial retake supersession. Validation code is excluded from this stage's reservation.

| Constraint / trace | Structural evidence now | Required downstream fitness function |
| --- | --- | --- |
| Unique owners/modules, known acyclic edges, no workflow data; ADR-0001/0002 | Both unchanged checkout checks pass; self-test rejects six invalid models | Compiled graph vs allowlist; owner-prefixed migration/entity registry; reject foreign persistence |
| Only public api crosses modules; no ORM/provider/HTTP in domain/DTOs; ADR-0001 | Package convention in model | ArchUnit public/private/layer/import rules and DTO/schema compatibility |
| Reporting reads commerce via public queries, never source SQL/writes; FR-024 | Candidate allows reporting → commerce with no reverse edge | Architecture rule and scoped reporting contract tests with fake owner APIs |
| Free attempts never need commerce/order/payment; FR-011 | Candidate has no RetakeEntitlement and no assessments → commerce edge | Attempt creation with no commerce interaction; every configured retake remains free and eligibility/versioned ordinal is serialized |
| Configurable completion/progression; FR-005/FR-009/FR-010/FR-017 | Owner/contracts documented | No-exam required-element completion, no-prerequisite start, final-only gate, authorized exception and immutable-history tests |
| Role plus active resource, guardian lifecycle, MFA and audit; FR-001/FR-014/FR-015/NFR-001 | Documented authority/owner boundaries | ID substitution/revocation tests, main-guardian/invitation races, child/adult separation, recovery self-approval denial, audit-failure rollback |
| Verified/deduplicated payments, capacity and refunds; FR-004/FR-018/NFR-002 | Stable identity and transaction contracts documented | Real PostgreSQL callback/last-seat/late-payment/parallel-refund tests; crashes, pending balance and uncertain-provider reconciliation |
| Shared weekly quota; FR-013/NFR-009 | ConsultationWeekUsage has one owner | Parallel child/guardian creation accepts one slot, replies/carryover/week/DST/holiday tests |
| Attachment quarantine and safe math; FR-007/FR-023/NFR-007 | Candidate owner/type/count/size contracts | Type spoofing, 20 MB boundary, five-file limit, DOCX vs generic archive, scan outage and unauthorized access; bounded server evaluation/no key leakage |
| Versioned KPI cohorts and dedup; FR-024 | Reporting owns qualification/survey/snapshot; source facts remain with owners | Missing continuation, repeated availability, 60th-day Warsaw boundary, rescheduled attendance, survey/main-change and zero-denominator tests |
| Durable bounded retries and redacted diagnostics; NFR-008/NFR-010 | Owner delivery contracts and stated pending SA-Q-009 | Restart/lease/key/retry exhaustion tests; no unsafe automatic replay; fault-injected alerts and diagnostics/audit retention separation |
| Measurable operations; NFR-003–NFR-006 | Approved targets documented | Process availability report, ≥100-family/10-lesson load, p95/p99/errors, full DB/object restore and manual/automated accessibility review |

## Scope and limits

The exact BA/SA input gate passes with both mandatory controller approval identities and local external evidence. Both unchanged configured architecture checker variants pass against the actual checkout, exit 0. They report 13 modules, unique ownership, a valid DAG, valid ADR structure/status and existing local Markdown destinations; all six negative model cases are rejected.

Accepted ADRs 0001–0005 and 0007 and validation/check_baseline.py are present and byte-for-byte equal to HEAD f94029b1486721893a4258ae07e6885272d06357. Proposed ADR-0006 and principles.md also match HEAD. Earlier absence/exit-2/missing-link descriptions are historical. Exact input, output and protected-file identities are recorded in the [handoff](implementation-handoff.md).

Historical ARCH-001's recovery and executable-check preconditions are now supported by actual checkout evidence. This stage has no newly supplied review_findings object and issues no finding closure or review approval. It returns documentation proposals within the current architect reservation, including a factual execution-status update to architecture_decisions.md that preserves the coordinator's selections. No Accepted ADR or validator proposal is needed.

Controller promotion requires fresh upstream/output comparisons, a complete resulting architecture snapshot and baseline-relative diff including dirty/untracked content, rechecked exact external BA/SA approvals and lineage, independent read-only review and both unchanged checks on the resulting checkout. Passing structural validation is not architecture adoption. ADR-0006/0008 remain Proposed.

The unchanged checker validates model uniqueness/DAG, distinct delivery concepts, ADR structure/status, ownership-table alignment and local Markdown destinations. It does not prove link fragments, physical SQL, compiled Java/TypeScript, provider/API behavior, Mermaid rendering, numeric objectives, source semantics or security. Meaningful implementation checks remain with downstream owners.
