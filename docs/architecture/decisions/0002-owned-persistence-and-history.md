# ADR-0002: Owned persistence and immutable educational history

## Status
Accepted — 2026-10-03. Target decision; not implemented.

## Context
SR-02,04–06,13 require distinct delivery concepts, configurable educational rules, final grading and reproducible historical attempts. PostgreSQL/migrations are fixed by AGENTS.md.

## Problem
Preserve historical meaning and clear data ownership while coordinating atomic operations in one database.

## Constraints
No shared table owners, foreign repositories or overwritten published rules/results. Money carries currency and decimal precision; time is unambiguous.

## Considered options
One schema with owner-prefixed tables and explicit contract-mediated transactions provides simple migrations. Separate schemas per module offer namespace isolation with more migration/permission work. Independent databases add coordination cost without a requirement. Mutable current content alone cannot reproduce prior assessment meaning.

## Decision
One PostgreSQL database, owner-prefixed tables, globally ordered versioned migrations and one owner per logical entity in [model.json](../model.json). Owners write their own data through public contracts. Freeze published content/policies; pin group and attempts to exact versions and append grade corrections with audit. Use local cross-contract transactions for invariants; provider delivery/reports may be eventual. Define details in [data model](../data-model.md).

## Rationale
Local atomicity handles last-seat capacity, fulfillment and final results without distributed machinery. Version references/snapshots preserve reproducibility across editorial changes.

## Consequences
Separate migration ordering from data ownership. Reporting uses public queries, not unrestricted joins. Deletion/retention must preserve or appropriately minimize historical records under approved policy.

## Risks
Single application database credentials cannot alone enforce module boundaries; code checks and reviews remain necessary. Grade corrections affecting already-started learning need product policy.

## Rejected alternatives
Shared ownership, ORM auto-update in production, rewriting referenced published versions, historical assessment based on current thresholds.

## Validation / fitness functions
Baseline model ownership checks. Future tests cover migration creation/upgrade, immutable version references, final-vs-preliminary progression, decimal money, Warsaw DST, last-seat/grade races and forbidden foreign persistence imports.
