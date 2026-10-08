# ADR-0008: Approved requirement impact on owned contracts

## Status

Proposed — 2026-10-07. No architecture approval is issued by this proposal. On acceptance, explicitly partially supersedes ADR-0003's enrollment/retake-entitlement fulfillment decision for retakes only. Enrollment, payment inbox/outbox, local atomicity, notification deduplication and recovery remain unchanged. Original Accepted ADR files are not edited.

## Context

Approved BA revision 6 and SA revision 3 require configurable educational completion/progression, all-free retakes, guardian lifecycle, consultation quota, purchased-term changes/refunds, pilot KPI and concrete NFR objectives. Exact consumed content identities and external approvals are in [implementation-handoff.md](../implementation-handoff.md).

ADRs 0001–0005 and 0007 are present and retain their exact Accepted text at HEAD f94029b1486721893a4258ae07e6885272d06357. ADR-0006 remains Proposed and unchanged. Baseline principles and the unchanged validator are also present and match HEAD. Both existing architecture checks pass against the checkout as verified on 2026-10-08; exact identities and verification limits are recorded in the implementation handoff. ADR-0003 explicitly includes retake-entitlement fulfillment, while the historical model puts RetakeEntitlement in commerce.

## Problem

Remove obsolete financial gating of assessment attempts and cover approved owner/consumer/data gaps while preserving the monolith, existing boundaries and durable payment guarantees.

## Constraints

No application implementation or Accepted ADR rewrite. No invented business rules, payment-provider choice or authentication mechanism. Exactly one data owner, acyclic public-contract imports, no foreign persistence access. Approved business rules cannot be overridden by a historical example. New decisions remain Proposed pending architecture adoption.

## Considered options

1. Retain a zero-price commerce entitlement for every retake. This would impose a commerce/order dependency on a purely educational process and preserve withdrawn pricing semantics.
2. Let assessments own free attempt eligibility, using program policy and practice evidence; retain workflows only for cross-capability composition. This removes financial gating without reversing dependency direction.
3. Introduce a separate administration/analytics service or allow reporting direct SQL joins. Neither is justified by the approved scope; both expand coupling or operations.

For KPI, a narrow reporting-to-commerce public read dependency fits the existing DAG better than moving commercial evidence into reporting or making workflows a persistent analytics owner.

## Decision

Recommend option 2. Remove RetakeEntitlement from the candidate commerce model and contract. Attempts require scoped enrollment, pinned educational policy, required evidence and serialized/idempotent creation, never purchase or payment for a retake.

Preserve module IDs and all existing public import edges; add reporting → commerce for FR-024 financial/continuation evidence. Add single-owner logical records for guardian invitations/readiness, organizational cases, lesson-change decisions, weekly consultation usage, immutable offer/settlement terms and refund/change evidence, and derived KPI qualifications/surveys. The complete candidate registry is [model.json](../model.json).

Catalog remains educational-rule owner; groups capacity/participation owner; assessments completion/attempt owner; commerce purchased-term/financial owner; reporting derived-metric owner. Workflows owns no tables. Refund requests reserve remaining paid value transactionally; provider calls happen outside locks, with stable idempotency keys and reconciliation of uncertain results.

## Rationale

This satisfies FR-001, FR-004, FR-005, FR-009–FR-011, FR-013, FR-017–FR-021, FR-024 and NFR-001/NFR-002/NFR-009/NFR-010 without a new deployment boundary. Existing PostgreSQL transactions and durable delivery can enforce the required concurrency constraints.

## Consequences

Dependent contracts/model documentation become a Proposed delta. Acceptance of this ADR establishes the narrow supersession; the ADR register must retain the historical ADR-0003 and record the superseding reference. Unchanged decisions in ADRs 0001–0005 and 0007 remain binding. ADR-0006 remains separately unresolved.

There is no implemented retake data to migrate. Downstream features must provide actual DTO/schema, migration and tests for their scope. Approved requirements do not authorize full-MVP implementation.

## Risks

Historical documents can still imply paid retakes or unconditional progression; handoff traceability identifies those conflicts without rewriting requirements. Refund reservation/reconciliation must handle uncertain provider outcomes. Derived KPI can drift without source revisions/cohort definitions. Structural validation cannot establish semantic compliance or replace independent review of the complete proposed package. Single-server NFR compliance requires measurement, not inference.

## Rejected alternatives

Paid retakes; client-selected free/paid flags; universal prerequisite/lesson/threshold defaults; shared mutable owner tables; unrestricted reporting joins; a new broker/cache/service without evidence; silently changing Accepted ADR-0003; treating BA/SA approval as architecture approval.

## Validation / fitness functions

Use the existing model validator for unique ownership, DAG and no workflow persistence. Future compiled checks enforce the public import allowlist including reporting → commerce. Focused PostgreSQL/contract tests must cover free attempts without commerce, optional completion/gating, last-seat/late-payment races, pending/successful refund budget, shared weekly quota, guardian revocation and KPI/survey deduplication. Security tests cover independent child access, privileged MFA/recovery and audit atomicity. NFR evidence follows [nfr.md](../nfr.md). No application check exists or is claimed to pass in this stage.
