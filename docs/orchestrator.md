# Analysis and architecture factory

Factory is repository tooling, separate from the eSzkola product runtime. Agents create knowledge; Python controls state, gates, approval, retries and writes. It ends at architecture validation. [ADR-0007](architecture/decisions/0007-deterministic-analysis-orchestration.md) defines its boundaries.

## Installation and use

Use Python 3.11+ and an installed/authenticated Codex CLI. The default macOS Python 3.9 is insufficient.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
source .venv/bin/activate
factory analyze
factory status
factory approve ba
factory resume
factory approve sa
factory resume
factory status
```

PyYAML 6.0.3 and setuptools 80.9.0 are pinned. Run inside the checkout or use `factory --root /absolute/path status`. Config/role definitions remain repository resources. Write stages require a feature branch; main/master and detached checkouts are rejected. Dirty work is permitted and preserved.

`analyze` selects full, incremental or no-op analysis and snapshots configured business sources/Git status. BA inspects applicable sources and returns a full proposal or bounded patch. Each analysis stops for explicit human approval. `resume` starts only the next eligible stage; repeating it cannot skip gates or duplicate completed stages. Use `approve ba --owner NAME` or `approve sa --owner NAME` to declare the designated owner; defaults are BUSINESS_OWNER and REQUIREMENTS_OWNER. This label is not independent identity verification. Confirmation requires an interactive terminal and explicit `y`; no piped approval or `--yes` exists.

## Stages and lifecycle

BUSINESS_ANALYSIS → BA_APPROVAL → SYSTEM_ANALYSIS → SA_APPROVAL → ARCHITECTURE → ARCHITECTURE_REVIEW → ARCH_VALIDATION → DONE. Rejected review goes through ARCH_FIX back to review. Third rejection terminates HUMAN_REQUIRED. BLOCKED/FAILED include reasons. Approval stages persist WAITING_FOR_APPROVAL status and display WAITING_FOR_BA_APPROVAL/WAITING_FOR_SA_APPROVAL.

Artifacts retain the [version 1 contract](requirements/README.md). Analysts propose DRAFT, BLOCKED or READY_FOR_REVIEW, with null approval. DRAFT cannot progress; unresolved blockers stop the run. Structural validation checks fields, types, duplicate keys/IDs, criteria, sources/references, complete BR coverage and blocker/status consistency. It cannot prove source truth or replace semantic human review.

Approval prepares a candidate whose only semantic changes are status APPROVED and embedded approval metadata; YAML formatting may normalize. It displays the complete candidate, owner/time/evidence and SHA-256 over its final exact UTF-8 bytes. Explicit confirmation writes those bytes and an external record in `.orchestrator/approvals/`. External evidence binds type/path/ID/revision/digest and is authoritative. Embedded APPROVED or LLM statements alone never pass. Any byte change invalidates evidence; changed content needs a new revision. Old records are immutable. An interruption leaving APPROVED without matching sidecar fails closed.

SA records exact approved BA in `business_input.{artifact_id, revision, content_digest}`. Approval metadata is included in the consumed digest. SA approval rechecks BA; all architecture/fix/reviewer/validation stages recheck both approvals/lineage. Changed BA makes SA stale, changed SA makes architecture stale. Changed sources/config invalidate the run. Status derives from actual files and records; historical DONE never implies current approval validity.

## Role execution and writes

The adapter loads actual `.codex/agents/*.toml` instructions and validates names. `architect-reviewer` maps to `architecture-reviewer.toml`. Separate `codex exec` invocations use read-only sandbox, no escalation, delegation or user config/rules inheritance; CLI authentication remains. The transport asks full-analysis/Architect agents for complete file proposals, incremental analysts for strict JSON patches, and Reviewers for structured findings instead of writes. This is contract-loaded execution, not custom-agent selector attestation. Official documentation: [non-interactive mode](https://developers.openai.com/codex/noninteractive), [sandbox security](https://developers.openai.com/codex/security).

CLI agent execution prints a heartbeat on stderr about every two seconds: stage label, elapsed time and timeout (default 1800 seconds). Interactive terminals redraw one line; redirected output uses plain lines. This reports waiting for the Codex subprocess, not model reasoning progress or a completion percentage. Raw provider output remains private. A dedicated process group is terminated on timeout or Ctrl+C, with a kill fallback; interruption returns exit code 130 and preserves RUNNING for deliberate recovery.

BA can propose only business-analysis.yaml; SA only system-analysis.yaml. Architect can propose `.md`/`.json` under docs/architecture excluding validation code; existing Accepted ADRs cannot change and new decisions require new ADRs. Empty/deletion proposals and application implementation are rejected. Reviewer returns no files. Agent commands/state/approval decisions are never executed by the controller.

A per-worktree advisory lock prevents concurrent factory control, including approvals/reset. Context records writer/path/worktree reservations. Input/output/unrelated checked-out content snapshots are rechecked before promotion; unexpected edits stop writes. Locks do not coordinate arbitrary editors or discover every independent session; follow [single-writer coordination](../workflow.md#single-writer-coordination). Snapshot checks are not atomic multi-file transactions. Factory never resets Git, stashes, switches branches or discards user changes.

## Baseline, review and validation

Each run captures HEAD/status, actual architecture bytes/digests including dirty/untracked files, Accepted ADRs and exact approved BA/SA identities. Diff is computed against those captured bytes, not HEAD alone. Independent reviewer inspects baseline/current diff, requirements and rules. It returns APPROVED or REJECTED with IDs, severity, requirement/file references, description and expected_action. Missing verification requires rejection. Exact findings are supplied to Architect; attempts are retained, maximum three.

Reviewer approval runs both actual mandatory commands from config/pipeline.yaml:

```bash
python docs/architecture/validation/check_baseline.py
python docs/architecture/validation/check_baseline.py --self-test
```

Python resolves to factory's interpreter. Any failure records argv/code/output and prevents DONE. These checks validate target model/ownership/DAG, ADR structure and local links, not future compiled application security or analysis quality. Reviewed architecture and approved inputs must remain unchanged through validation. Validators are trusted operator-maintained repository code; agent proposals cannot modify them.

## Persistence and recovery

Ignored `.orchestrator/state.json` stores run/stage/status/attempt/timestamps/reason/input identities/config digest. Per-run directories retain run.json, events.jsonl, architecture-baseline.json, architecture-diff.json, numbered architecture-review YAML-compatible JSON files, reviewed-architecture.json and validation-results.json. Events record transitions, identities, duration, findings, gate failure and validator output. No raw provider stream or environment credentials are logged; validators must also avoid secrets.

```bash
factory history
factory reset
```

Reset removes only current state; sources, BA/SA, architecture, ADRs, approvals and history remain. BLOCKED: resolve questions with owners, then reset/reanalyze. FAILED: inspect reason/evidence, fix cause, then reset/reanalyze. HUMAN_REQUIRED: inspect findings/interrupted execution, coordinate resolution, then reset/reanalyze. RUNNING after interruption is ambiguous; resume stops for human recovery instead of replay. Partial approval cannot progress; inspect and regenerate a new revision if an immutable prior evidence file already exists. No automatic rollback overwrites documents.

## Verification and extension

```bash
python -m unittest discover -s tests -v
python -m orchestrator.smoke --timeout 120
```

Unit/end-to-end tests use fake agents and actual baseline validators without LLM calls. Live smoke requires Codex login/network, tests all four role contracts using instruction receipts, and creates no analyses/approvals. It does not verify human-approved live business analysis quality. Receipts are model-reported transport evidence.

v0.1 validates a fixed mandatory graph. Configuration cannot remove gates or execute arbitrary shell. A future stage needs an architecture decision, enum/edge/config validation changes, bounded handler and runner contract, failure/progression tests, input lineage and ownership documentation. New validator commands require reviewed code allowlist changes. Planner, DAG, developers, release and other future stages are not implemented.

## Incremental analysis

[ADR-0008](architecture/decisions/0008-incremental-analysis-patches.md) extends the incremental BA/SA transport. FULL file proposals remain supported for bootstrap and explicit reanalysis; Architect/Reviewer transport stays compatible. See the [closed patch contract](requirements/incremental-analysis.md).

```bash
factory analyze          # automatically FULL, INCREMENTAL or NOOP
factory analyze --full   # force full BA and subsequent SA
```

Absent/invalid BA selects FULL. A valid BA with changed sources, analysis inputs or unresolved blockers selects INCREMENTAL. An unchanged known snapshot and no reanalysis reason selects NOOP without inference, artifact writes or revision increments. Changed role/contract/config bytes count as inputs. Unfinished runs cannot be replaced, including with `--full`; inspect and resume/reset them. DONE and NOOP runs may start another analysis; histories are retained. After NOOP, explicit `factory resume` re-enters BA approval and normal downstream gates. NOOP does not mean approval.

Source deltas report added/changed/removed/unchanged by raw-byte SHA-256. Removal means removing the path from configuration; a configured path missing on disk is an error. Generated BA/SA, runtime and architecture outputs are forbidden business sources, including renamed generated YAML/JSON analysis files. [Owner decisions](business/README.md) are a required, initially empty, owner-maintained source. ACTIVE decisions outrank legacy BA; SUPERSEDED entries cannot independently create blockers. Precedence is an analyst/human semantic responsibility; structural checks do not interpret business text.

Incremental analysts return only the versioned patch object bound to baseline ID/revision/raw-byte digest. The controller gives them a complete compact baseline, changed-source text/diffs, all open questions and precedence policy; it excludes unchanged whole business sources and extra historical artifacts. Operations are bounded and typed by actual BA/SA section schemas. Controller-owned approval, revision and lineage cannot be patched. All operations apply to a deep copy; strict schema, existing validators, deterministic serialization and snapshot/Git rechecks precede the single canonical atomic write. Invalid patches leave canonical bytes unchanged. A changed analysis, including an empty impact-review patch, increments revision and loses approval.

`.orchestrator/provenance/` independently retains content-addressed exact artifact YAML, exact source blobs, immutable manifests and approval evidence copies. Manifests bind sources, input fingerprint, parent identity, consumed BA and retired IDs. Reset keeps all provenance and approval files. Approval archives draft and approved bytes and transfers their verified source snapshot across YAML formatting/status/digest changes. Legacy valid BA is adopted with bytes unchanged and historical snapshot UNKNOWN; its first incremental context may include all current sources as unknown delta with null old hashes. Source citations are not fabricated into historical snapshot hashes.

Previous SA is validated against its exact archived consumed approved BA and external approval evidence. Incremental SA requires currently approved BA, receives its semantic diff and current lineage, and is validated against current BRs/coverage before write. Missing valid historical consumed input causes full SA generation. Every changed SA needs new approval; stale SA cannot pass architecture gates. Unchanged eligible SA may be reused during explicit resume without inference.

Codex process handling drains both output pipes while sending stdin with bounded `communicate` waits. Timeout and Ctrl+C terminate its process group and descendants. Persisted errors use `CODEX_TIMEOUT`, `CODEX_START_FAILED`, `CODEX_EXIT_FAILED`, `CODEX_INVALID_OUTPUT`, `INVALID_PATCH`, `BASE_REVISION_MISMATCH`, `BASE_DIGEST_MISMATCH`, `INVALID_GENERATED_ARTIFACT` or `VALIDATION_FAILED` as applicable. Raw provider stderr/messages are not persisted.

The BA/SA TOML role contracts and adapter explicitly select patch-only incremental transport. Source text and decision context come from verified content-addressed blobs captured for the run. Source changes during capture are rejected. Approval handoff pins the generated candidate (or NOOP baseline) and accepts only its exact bytes or a metadata-only human-approved descendant. Replacing canonical content with another approved analysis cannot redirect the run.

Archives and external approval records publish complete fsynced temporary files atomically without replacing an existing immutable path. An interruption between canonical approval and evidence publication still fails closed. If the evidence path is absent, repeat `factory approve ba`/`sa` and explicitly review/confirm the new candidate; no approval is recovered automatically. An existing invalid evidence record remains immutable and requires a new content revision after deliberate recovery.
