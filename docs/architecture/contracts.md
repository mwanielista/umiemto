# Baseline contracts

Status: architectural contract shapes and invariants, not implemented endpoints or final OpenAPI. Owners/consumers follow [model.json](model.json). API and integration implementation must add machine-readable OpenAPI/event schemas and compatibility checks for the actual feature scope.

## HTTP boundary

Same-origin `/api/v1` HTTP/JSON; explicit request/response DTOs, server validation, pagination/size limits and uniform error shape (`code`, safe Polish `message`, `correlationId`, optional field errors). Use HTTP status semantics: 400 invalid shape, 401 unauthenticated, 403 forbidden or privacy-preserving 404 for inaccessible resources, 409 conflicting state/idempotency/version, 422 unmet domain policy, 429 throttled, 503 transient unavailable integration. Decide consistent inaccessible-resource behavior before each API is published. Correlation IDs are technical identifiers, not child names/emails.

Use decimal strings plus currency for money, ISO dates/instants, explicit enums distinguishing preliminary/final and purchased/active states. Do not expose entities, provider models, unneeded child data or answer keys. Browser mutations require CSRF protection for cookie sessions if ADR-0006 is accepted. Webhook endpoint is separately authenticated by provider verification, not a browser session. Compatibility is additive within v1; breaking changes require a new version and migration plan. Pagination, field limits and exact DTO schemas are feature decisions before implementation, not vague future conventions.

## Public application contracts

All contracts receive a verified actor/service execution context. A caller-supplied parent/teacher/child ID is not authorization. The resource-owning module checks the actor's grants and current scope; workflow orchestration does not bypass those checks. Internal service authority is restricted to a named operation and carries source actor/event for audit.

| Contract / owner | Consumers | Input and output | Authorization, invariants and failures |
| --- | --- | --- | --- |
| `GuardianAccess` / identity | groups, lessons, assignments, assessments, consultations, commerce, reporting, workflows | Actor ID + child ID + operation → allow/deny with relation/version | Current authorized relationship; deny missing/revoked relation. No general role-only allow. |
| `PublishedProgram` / catalog | groups, lessons, assignments, assessments, commerce, reporting, workflows | ProgramVersion ID → immutable learner manifest or separately authorized server grading manifest | Public catalog excludes private exam pool/keys; grading manifest is trusted-server/educational-authority access only; fail unpublished/unknown. |
| `GroupAccess` / groups | lessons, assignments, assessments, consultations, reporting, workflows | Actor + group/enrollment/resource ID + action → scope and program version | Resolve parent relation, learner enrollment or assigned teacher; active participation required for learning actions; report access can include history under retention rules. |
| `ReserveSeat`, `ConfirmEnrollment` / groups | workflows | Child/group/order-line key and validated reservation → reservation/enrollment IDs + status | Parent authorized; capacity locked; confirm idempotently for same order line; expired/missing reservation needs reconciliation, never oversell. |
| `CreateOrder`, `PaidEntitlement` / commerce | workflows | Quote/program/reservation/parent/child references; or entitlement ID → snapshotted order / verified entitlement | Parent purchase only; server pricing, gross total/currency; bound child/product; distinguish free entitlement from verified paid entitlement. Fail quote mismatch/consumed entitlement. |
| `PrerequisiteDecision` / assessments | workflows | Child + target program version → decision, final completion/override revision IDs and reason code | Uses authoritative approved results and configured prerequisites; pending grading returns not eligible; authorized educational override is audited. Decision is revalidated in the participation transaction. |
| `ActivateParticipation` / groups | workflows | Enrollment + prerequisite decision reference + expected state version → active enrollment | Only scoped progression workflow service authority; cannot activate on payment alone or stale/preliminary decision. Parent/child assignment and group state remain valid. |
| `RetakeReadiness`, `CreateAttempt` / assessments | workflows | Enrollment + program rules + verified entitlement evidence → readiness / attempt pinned to versions | Program-defined practice/window and final prior result checked; first retake free; serialize attempt ordinal/entitlement consumption. No client-supplied free/paid flag can authorize. |
| `PracticeEvidence` / assignments | assessments, reporting, workflows | Child/program/outcome IDs → relevant completed practice and revision | Scoped actor; compare to versioned retake conditions rather than global numeric threshold. |
| `ApproveGrade` / assessments | scoped teacher/methodologist entry point | Attempt + expected revision + decision/reason → final grading revision and completion status | Assigned teacher or approved educational reviewer; audited; revision conflict fails rather than overwrites. |
| `FileOperation` / files | catalog, lessons, assignments, assessments, consultations, workflows | Owning module/resource binding + size/type intent or scanned file ID → object intent/status/short-lived operation | Public user endpoint resides in owner/workflows which first authorizes resource; files validates binding, scan state and limits. No arbitrary key/bucket access. |
| `ParentProgress` / reporting | workflows / scoped reporting entry point | Authorized parent/child/program → summary/report revision | Calls owner queries with original actor; no direct table join; no progression side effects. |
| `EnqueueEmail` / notifications | workflows | Template ID, approved recipient reference, safe template variables, dedup key → intent ID/status | Internal operation only; dedup by source event/recipient/template; no unrestricted user-supplied recipient/body relay. |
| `AppendAudit` / audit | owning modules and workflows | Actor/action/resource/reason/time/correlation + bounded redacted change metadata → audit ID | Same transaction as important mutation; append-only; no secrets/free-form child messages; protected read authority. |

## Durable event envelope

Internal delivery uses a versioned envelope with `eventId`, `eventType`, `schemaVersion`, `occurredAt`, `producer`, `aggregateId`, `aggregateRevision`, `correlationId` and a minimal typed payload. Publisher owns the delivery table and exposes claim/ack/retry through public API; consumers never query its persistence. Handlers are explicitly wired in `workflows`. This is an in-process delivery contract, not a public message broker, event-sourced domain, or automatic dynamic subscriber system.

Initial significant event: `PaymentConfirmed` v1, commerce-owned. Payload references `orderId`, `paymentId`, `orderLineIds` and decimal settled amount/currency. Provider payloads remain inside commerce infrastructure. Workflow resolves snapshots/entitlements through commerce API; it never trusts the envelope alone as paid authority. Event ordering is checked against aggregate revision; duplicates/stale events are harmless and audited appropriately. Add further typed notifications only for real workflows, not speculative events for every entity.

## Payment-to-enrollment transaction

1. Callback adapter verifies authenticity, merchant/payment identity, amount/currency and authoritative provider state; network verification is outside the database transaction.
2. Commerce locks payment/order, persists unique callback evidence, validated monotonic transition and `PaymentConfirmed` delivery atomically. Acknowledge only after this durable commit. Browser return only reads status.
3. A workflow claims the delivery through commerce API. One local database transaction commands groups/retake owner using an order-line effect key, records fulfillment status, enqueues a deduplicated notification intent and acknowledges commerce delivery. Crash before commit rolls back all local effects; retry after commit cannot duplicate them.
4. The notification worker sends the committed intent after fulfillment. Email delivery failure retries independently and cannot undo payment/enrollment. Provider/network calls never hold business row locks.

More than one successful provider event for the same payment still produces one business transition/effect. Valid settled payments with unavailable/expired seats become a recoverable fulfillment issue, with parent-safe status and operator reconciliation; automatic refund/alternate group policy needs product agreement. Refund evidence is commerce-owned and must not silently delete attendance/grades or cancel in-progress learning without a defined workflow.
