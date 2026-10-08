# ADR-0007: Deterministic analysis orchestration and approval ownership

## Status
Accepted — 2026-10-04. Repository governance tooling only.

## Context
The user explicitly requests an analysis-to-architecture orchestrator. Existing role contracts and artifact contract version 1 remain authoritative. BA/SA artifacts are absent; the workflow governance/validation maintenance exception permits tooling, not product requirement approval.

## Problem
Keep process control, exact human approvals and bounded retries outside LLM agents while preserving established contracts and dirty working trees.

## Constraints
External approval evidence, raw-byte SHA-256, `business_input` lineage, persistent restart-safe state, single-writer coordination, independent review and executable validation. No implementation stage after architecture.

## Considered options
Writable agents in the authoritative repository can fabricate approval files despite prompts. Isolated writable copies require more promotion machinery. Read-only agents returning complete proposals provide a narrow controller-owned write boundary.

## Decision
Use Python 3.11+ and pinned PyYAML for deterministic state, contracts, gates, evidence and promotion. Configuration supports a fixed validated mandatory graph and allowlisted validator argv, never arbitrary shell. Runtime lives in ignored `.orchestrator/`, with a per-worktree OS advisory lock.

Load existing TOML role instructions in separate read-only Codex executions, disable delegation/user configuration/rules and escalation, and request structured file proposals/reviewer findings. Do not claim custom-agent selector startup. Controller promotes only reserved BA/SA or architecture documentation/model paths after snapshot comparisons; reject runtime/config/code/validator proposals, deletions and changed existing Accepted ADRs.

Human approval prepares a metadata-only candidate with APPROVED and compatible embedded owner/time/evidence metadata. Display complete candidate and final SHA before explicit confirmation. External evidence binds artifact type/path/ID/revision/digest and remains authoritative. Embedded APPROVED alone cannot pass. Records are immutable per revision; changed content needs a new revision. Human owner labels are declarations, not independently authenticated identities.

Capture actual dirty/untracked architecture bytes, HEAD/status, existing Accepted ADRs and exact approved BA/SA inputs. Reviewer receives computed baseline-relative diff. Recheck approvals/lineage before all dependent stages and promotion; recheck reviewed architecture around executable validation. Persist RUNNING until the next transition commits; ambiguous interruption requires human recovery. Three rejected reviews terminate HUMAN_REQUIRED.

## Rationale
Existing agents retain specialist responsibilities; application code owns authority and writes. Version 1 remains compatible without digest circularity. Standard-library persistence/locking avoids distributed infrastructure and a speculative workflow framework.

## Consequences
Interactive approval changes lifecycle metadata before binding final bytes. Partial approval persistence fails closed. Reset removes only current state and retains artifacts, approvals and history. Historical DONE becomes stale if approved/reviewed inputs change. Validators remain trusted operator-maintained code.

## Risks
Advisory locks do not lock editors or discover independent sessions. Snapshot checks reduce races but are not multi-file transactions; human coordination remains necessary. Runtime/OS sandbox enforcement must be verified. Logs must omit secrets; raw provider streams/environment credentials are not persisted, but validators must honor repository logging rules. Alternate runners must preserve proposal isolation.

## Rejected alternatives
LLM-controlled gates, self-approval, arbitrary shell from YAML/proposals, unlimited retries, digest before metadata changes, HEAD-only dirty diff and silently rewritten agent contracts.

## Validation / fitness functions
`python -m unittest discover -s tests -v` covers gates, lineage, modification, state/recovery, scope, locks, retries and fake-agent end-to-end behavior. Pipeline runs both existing baseline checker variants. `python -m orchestrator.smoke` verifies real contract-loaded Codex transport, not analysis quality or human approval. See [factory guide](../../orchestrator.md).
