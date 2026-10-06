# ADR-0008: Incremental analysis patches and immutable provenance

## Status
Accepted — 2026-10-06, explicitly requested governance tooling maintenance with completed read-only Architect delegation. Extends ADR-0007 and supersedes only its complete BA/SA file-proposal transport for incremental runs. ADR-0007 itself remains unchanged. This decision approves no business analysis or system analysis.

## Context
An existing BA revision 5 must be preserved while adding tooling for source-driven incremental BA/SA updates. Read-only Architect delegation recommends exact-baseline patches, a deterministic Python engine, validation before atomic promotion, archives and no approval carryover. Existing approval, recovery and architecture gates remain mandatory.

## Problem
Avoid repeated full analysis and sending unchanged business sources, while preventing stale patches, lost provenance, fabricated historical hashes, ID reuse and downstream approval reuse.

## Constraints
Python 3.11+, pinned PyYAML, existing version 1 artifacts, raw-byte SHA-256, external immutable human evidence, per-worktree controller lock, read-only specialist executions, no actual SA creation in this maintenance task, and no change to canonical BA revision 5. Architect/reviewer transport and accepted ADR protection remain governed by ADR-0007.

## Considered options
Complete proposals are compatible for bootstrap but expensive for small updates. Arbitrary JSON pointers make lifecycle metadata writable and widen the mutation surface. Textual YAML edits depend on formatting and are difficult to validate atomically. Closed, typed, section-specific operations retain existing artifact shapes with bounded mutation authority.

## Decision
`factory analyze` selects FULL for absent/invalid BA, INCREMENTAL for valid baselines requiring source/input or blocker impact review, and NOOP for an unchanged known snapshot with no reanalysis reason. `--full` forces full BA and subsequent SA analysis. Active unfinished runs require resume/reset; RUNNING recovery never automatically replays inference. A completed/NOOP run may start another analysis. NOOP itself invokes no agent and changes no artifact; explicit resume re-enters the normal approval and downstream gates.

Incremental analysts return only a version 1 JSON patch with exact baseline artifact ID, revision and raw-byte digest. Every object is closed (`additionalProperties: false`). Typed create/update/remove, resolve-question, scope, section-note and status operations have bounded counts and entry shapes matching BA/SA contracts. No arbitrary pointer, approval, revision or lineage operation exists. Stable IDs cannot be created twice or reused after retirement; questions/evidence cannot be deleted, reopened or resolved twice. Full proposals remain supported, with strict generated entry shapes and complete validation before write.

The controller copies the baseline, applies all operations in memory, increments its revision exactly once, clears approval, updates SA lineage, serializes deterministically with `safe_dump`, validates contracts/references/coverage/readiness and rechecks repository/Git/input/output snapshots before one canonical `atomic_write`. BLOCKED is a valid analysis result that persists and stops dependent progression. Architect and reviewer continue their original proposal/findings protocol.

Ignored `.orchestrator/provenance/` retains exact artifact bytes, content-addressed source blobs, immutable per-artifact manifests and approval evidence copies. Approval inherits the analyzed snapshot across metadata/formatting changes and archives both draft and approved bytes. Reset retains this store. A valid legacy artifact is adopted byte-for-byte with UNKNOWN historical inputs, without deriving past hashes from its citations. Its first incremental prompt may include all current configured sources as unknown delta; no forced full migration is required.

SA consumes only currently approved BA. Its previous baseline is validated against the exact archived, externally approved BA it consumed; otherwise SA uses full generation. Incremental SA receives the semantic BA diff and controller-owned current lineage and always requires approval for a changed SA revision. Architecture still requires both exact current approvals.

Owner decision registry is an empty owner-maintained source at `docs/business/product-decisions.yaml`. Current explicit ACTIVE owner decisions outrank current owner-maintained sources, historical sources and generated BA. SUPERSEDED decisions are historical and cannot independently create blockers. Structural schema and source exclusion are executable; Python does not interpret business text or prove semantic precedence compliance. Semantic analyst and human review remain mandatory.

Codex execution uses `communicate` with bounded waits to drain both pipes and send stdin safely. Timeout/Ctrl+C terminate the process group, including descendants. Persisted provider failures use fixed codes and classified hints, never raw stderr or provider messages.

## Rationale
Patch authority is narrow and mechanically enforceable. In-memory application prevents partial updates. Separate provenance avoids losing source identity during approval normalization and reset. Unknown migration states report the actual available evidence rather than inventing history.

## Consequences
Every changed analysis requires a fresh explicit approval; even an empty patch after an impact review creates a new revision. Incremental prompts retain the complete baseline for referential integrity, changed-source text/diffs and all open questions, without extra unchanged source files or historical artifacts. Local provenance is operational data and must be retained with approval records. Config and role/contract inputs are hashed as reanalysis inputs.

## Risks
Advisory locks and snapshot comparisons do not lock independent editors; the existing single-writer policy remains necessary. Canonical promotion is atomic per file, not a multi-file transaction with evidence. Interrupted archive/approval writes fail closed. Local files are trusted controller-owned evidence, not cryptographically authenticated human identity or tamper-proof storage. Semantic precedence, truth and stable ID meaning cannot be proven by the schema. A removed source requires semantic impact review.

## Rejected alternatives
Unbounded JSON Patch/pointers, agent-authored YAML in incremental mode, approval carryover, forced full legacy migration, fabricated source history, silently rewriting ADR-0007, and applying operations directly to canonical files.

## Validation / fitness functions
`python -m unittest discover -s tests -v` covers mode selection, legacy adoption, raw bytes/approval/reset retention, source changes/removal, precedence protocol, patch atomicity/bounds/IDs/questions, stale lineage, fake-agent SA impact, transport failure classification, large pipes and process-group cleanup. Run both `docs/architecture/validation/check_baseline.py` variants. No live business inference is required. See [incremental contract](../../requirements/incremental-analysis.md) and [factory guide](../../orchestrator.md).

Architecture handoff: branch `feature/incremental-analysis`, worktree `/private/tmp/eszkola-incremental-analysis`, base `630773c`. Controller owns `orchestrator/**`, tests, pipeline configuration, BA/SA role transport, requirements contracts and owner registry. Canonical BA revision 5 and absence of actual SA are preserved. Independent read-only review of the final uncommitted diff remains an integration requirement; no merge or commit is authorized by this ADR.
