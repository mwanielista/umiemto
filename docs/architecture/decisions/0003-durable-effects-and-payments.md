# ADR-0003: Durable local delivery and idempotent payment fulfillment

## Status
Accepted — 2026-10-03. Target decision; not implemented.

## Context
SR-07,11 require reliable verified payments, enrollment and email. Providers can retry callbacks and processes can crash. AGENTS.md does not authorize a message broker.

## Problem
Prevent duplicate paid effects and lost integration work without coupling local commits to network success.

## Constraints
Verified server-side settlement; no browser-confirmed payments; no duplicate payments/enrollments/entitlements; decimal amount and currency validation.

## Considered options
Synchronous provider calls inside transactions hold locks and cannot guarantee external/local atomicity. Volatile application events lose work on crash. PostgreSQL-owned delivery records with in-process scheduled handlers provide durable retry. A dedicated broker adds operations and does not itself ensure payment idempotency.

## Decision
Use provider adapters and owner-local durable inbox/outbox records. Commerce atomically commits verified callback evidence, payment transition and delivery intent. Workflow fulfillment atomically records each order-line effect, enrollment/retake entitlement, deduplicated notification intent and consumed-delivery marker through public contracts. Workers perform network calls outside business transactions with bounded retries and reconciliation. [Contracts](../contracts.md) and [integrations](../integrations.md) define envelopes and behavior.

## Rationale
Same-database effects can be atomic; external effects need idempotency/reconciliation. Durable work survives restart at pilot complexity.

## Consequences
Unique keys protect both repeated callback IDs and separate events for one payment. Failed delivery/reconciliation is visible and auditable. Exactly-once local business effects do not promise exactly-once email delivery.

## Risks
Incorrect ack ordering loses work; unsafe replay duplicates effects. Expired seats, delayed settlements and refunds require product policy; payment evidence cannot simply be discarded.

## Rejected alternatives
Payment success from return URL, unrestricted webhook transitions, volatile-only notifications, broker introduced without scale requirement, network calls under business row locks.

## Validation / fitness functions
Future provider sandbox/contract and PostgreSQL tests: forged callback, wrong merchant/amount/currency, duplicate/reordered events, parallel settlement, crash before/after fulfillment commit, lost lease, retries, uncertain provider result and reconciliation. Baseline validates only model/document consistency.
