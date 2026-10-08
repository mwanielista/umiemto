# Architecture decisions following rejected reviews

Decision date: 2026-10-07. Execution evidence verified: 2026-10-08.
Branch: `feature/create-ba-bs`.
Scope: decisions for recovery of run `400a2120-ac2e-4355-8b67-f75db4c60e5b`
and selection of the existing architecture proposals.

These decisions select the recovery procedure and technical direction. They do
not record human architecture approval, change an Accepted ADR, or close the
independent review gate. ADR-0006 and ADR-0008 remain Proposed until formal
adoption. The coordinator maintains these selections. The current controller reservation
assigns the Architect docs/architecture/** excluding validation code and existing
Accepted ADRs; this proposal updates factual execution evidence within that scope,
without changing the selections or controller state. Generated BA/SA must not
interpret it as a new owner business decision.

## Verified requirements baseline

The actual ba_gate and sa_gate, using ApprovalStore.validate, passed again during
Architect verification on 2026-10-08. Both approvals bind the current raw bytes,
match the mandatory supplied external evidence, and SA consumes this BA.

| Artifact | Revision | SHA-256 content digest |
| --- | --- | --- |
| eszkola-business-analysis | 6 | `87f40e1eb91b6f9487425fdff2a5351c221ec54b2d6e9055973e5261c496e45c` |
| eszkola-system-analysis | 3 | `14dab97a77b119239d6cbb6ad2c2530ea88249e7895b4e619e25df7dc01250f3` |

Approval evidence: `.orchestrator/approvals/business-analysis-r6.yaml` and
`.orchestrator/approvals/system-analysis-r3.yaml`. Approval must be checked again
before dependent progression; the table itself is not approval evidence.

## AD-001 — Restore the reproducible governance baseline

Decision: recover the following seven files byte-for-byte from commit
`f94029b1486721893a4258ae07e6885272d06357` through a coordinator-owned recovery:

```text
docs/architecture/decisions/0001-modular-monolith-boundaries.md
docs/architecture/decisions/0002-owned-persistence-and-history.md
docs/architecture/decisions/0003-durable-effects-and-payments.md
docs/architecture/decisions/0004-resource-authorization.md
docs/architecture/decisions/0005-runtime-and-api-boundary.md
docs/architecture/decisions/0007-deterministic-analysis-orchestration.md
docs/architecture/validation/check_baseline.py
```

Preserve the six ADRs' Accepted status and historical text. Preserve the already
restored ADR-0006 and `principles.md`, checking their bytes against that commit.
Use the recovery digest manifest in [implementation handoff](implementation-handoff.md).
Check each destination immediately before recovery and stop if it has changed;
preserve all unrelated working-tree changes.

Rationale: the historical review record reports rejection for ARCH-001 and
seven absences. The current attempt supplies no new review_findings object;
current presence and validation must be established from the actual checkout. Removing links, weakening validators or
rewriting historical decisions would hide the problem rather than fix it.
Recovery of `docs/system-decisions.md` is outside this finding.

Execution evidence as of 2026-10-08: all seven paths are present and match the
exact commit above, including the six unchanged Accepted statuses. Proposed
ADR-0006 and principles.md also match that commit. Both unchanged configured
architecture checks pass against the current checkout. The Architect verified
these facts read-only and did not perform recovery or close the review finding.
Exact digests and remaining review/promotion responsibilities are in the handoff.

## AD-002 — Preserve the modular monolith and explicit ownership

Decision: retain existing module identities, single data ownership, public
contracts, acyclic dependencies, PostgreSQL persistence and the single-server
Compose direction. No new service, broker, cache or deployment boundary is
introduced by this requirements impact.

Catalog owns educational policy; groups owns capacity and participation;
assessments owns results and attempt eligibility; commerce owns purchased terms
and financial evidence; reporting owns derived metrics. Workflows composes
public operations and owns no persistent business tables.

Rationale: approved requirements fit the established boundaries. Extra runtime
components would add operational cost without a demonstrated requirement.

## AD-003 — Free retakes belong to assessments

Decision: select option 2 from [ADR-0008](decisions/0008-approved-requirement-impact.md).
Remove commerce `RetakeEntitlement` from the candidate model. A retake requires
authorized participation, pinned educational policy and applicable educational
evidence, with serialized/idempotent attempt creation. It never requires an
order, payment or zero-price commerce entitlement.

Preserve verified settlement, inbox/outbox, enrollment fulfillment, local
atomicity, notification deduplication and uncertain-result reconciliation.
Provider calls stay outside business row locks. Refund requests transactionally
reserve available paid value, including pending refunds.

Rationale: BR-011 / FR-011 require free retakes; pricing is not an educational
eligibility concern. Formal adoption of ADR-0008 must explicitly partially
supersede ADR-0003 for retake entitlement only, preserving its other guarantees.
This selection does not silently amend the historical Accepted ADR.

## AD-004 — Reporting uses owner contracts

Decision: select the narrow `reporting → commerce` public read dependency in
ADR-0008 for FR-024 financial and continuation evidence. Reporting must not join
another module's private tables or become owner of payment records. Retain
source/cohort identities, deduplication and the approved KPI definitions.

Rationale: the existing proposed model preserves the dependency DAG and keeps
financial authority in commerce. Missing denominators must not become fabricated
zero-performance results. Formal adoption follows ADR-0008's review gate.

## AD-005 — Use a server-managed browser session boundary

Decision: select the session direction in
[ADR-0006](decisions/0006-authentication-options.md): same-origin server-managed
sessions with Secure/HttpOnly/SameSite cookies, CSRF protection, rotation,
expiry and revocation. PostgreSQL session persistence may be used when needed.
Child sessions must not acquire guardian purchase authority; resource-level
authorization and privileged MFA/recovery remain mandatory.

Credential authority is still an explicit technical decision: evaluate external
OIDC versus application-managed credentials against approved child/guardian and
recovery flows, threat model and operational responsibility. No provider or
credential mechanism is selected by this document. Resolve and formally adopt
or supersede ADR-0006 before authentication implementation.

Rationale: the session boundary avoids browser-held long-lived secrets without
introducing Redis. Choosing a credential provider without suitability evidence
would leave the known recovery and child-account risks unresolved.

## AD-006 — Close ARCH-001 through actual validation and independent review

Decision: the coordinator must retain complete evidence for recovery and
verification before progression:

1. Verify the AD-001 paths against the exact historical commit and retain their
   Accepted text/status. This presence/identity check passes on the inspected
   2026-10-08 checkout.
2. Refresh README, constraints, implementation handoff and this document's
   execution-status evidence. Architect proposals replace historical absence,
   exit-2 and missing-link counts with actual current results.
3. Capture a complete resulting architecture snapshot and baseline-relative
   diff including Accepted ADRs and dirty/untracked bytes, then recheck BA/SA
   external approvals, exact digests, lineage and blockers.
4. Execute both unchanged check_baseline.py variants configured in
   config/pipeline.yaml against the resulting checkout: the default check and
   its --self-test variant. Both pass on the currently inspected checkout;
   promotion still requires validation of the resulting package.
5. Submit the complete resulting package for independent read-only review.
   Only that review can determine ARCH-001 closure.

Do not reset away evidence, manually mark the pipeline DONE or repeatedly run
paid architecture inference before recovery. Formal adoption of Proposed ADRs
is separate from recovery and BA/SA approval. This document changes neither
controller state nor approval records and does not authorize full MVP implementation.

## Verification and remaining work

Current Architect verification: exact supplied/local BA/SA approvals, contract
and lineage pass; all seven AD-001 files are present and match the baseline
commit; ADR-0006 and principles.md remain unchanged; both existing architecture
validator variants exit 0, with 13 modules, unique ownership, a DAG, valid ADR
structure/status, existing local Markdown destinations and six rejected invalid
model cases. These are checkout evidence, not application or review approval.

The prior incomplete-recovery statements are historical. No independent review
was performed by this stage and no controller lifecycle state is asserted.
Controller owns promotion, final snapshot/diff and renewed gates/validation;
the independent reviewer owns review of that complete resulting package and
any finding closure. ADR-0006 and ADR-0008 remain Proposed, separately from
requirements approval and recovery. No application implementation is authorized
or verified by this document.
