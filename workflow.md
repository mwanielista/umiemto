# Requirements-to-implementation workflow

[AGENTS.md](AGENTS.md) is the repository constitution. This workflow uses the current directory structure and defines manual stage gates; it does not register agents or provide an automated pipeline.

```text
Business input
    ↓ Business Analyst
Business requirements (BR) + review and explicit approval
    ↓ System Analyst
System requirements (FR/NFR) + review and explicit approval
    ↓ Architect
ADRs + architecture + contracts + executable constraints where practical
    ↓ Planner (future role)
Implementation DAG, tasks tracing to FR/NFR
    ↓ Developers (backend / frontend / infrastructure)
Implementation + tests
    ↓ QA + independent architecture reviewer (read-only)
Verified behavior + architecture compliance
```

## Stage ownership and gates

| Stage | Owns | Progression gate |
| --- | --- | --- |
| BA | Business goals, actors, processes, BRs, rules, glossary and questions | Complete source-backed artifact, no unresolved blockers, explicit business-owner approval of exact revision |
| SA | FR/NFR, use cases, concepts, data/integration requirements, security and failure scenarios | Approved BA revision, every FR/NFR traces to BR IDs, no unresolved blockers, explicit requirements-owner approval of exact SA revision |
| Architect | Boundaries, ownership, contracts, ADRs and fitness functions | Approved system requirements, relevant uncertainties resolved, architecture and constraints documented |
| Planner (future) | Tasks, dependencies and acceptance checks | Approved requirements and architecture; every task traces to FR/NFR; acyclic task dependencies |
| Developers | Requested features within these boundaries | Relevant tests/checks pass; changes and unverified areas documented |
| QA / architecture reviewer | Behavior / independent architecture compliance | Reviewer reports compliance or required changes; implementer fixes, reviewer reviews again |

BA is not SA; SA is not Architect; Architect is not Developer. BA and SA never generate implementation tasks. Existing technical mandates in AGENTS.md remain binding; analysts cite them without making new technology choices. Planner is a future responsibility, not an agent claimed to exist today.

Missing or contradictory information becomes an open question with an owner and affected scope. Unresolved `BLOCKER` questions set analysis to `BLOCKED` and stop the dependent stage. Non-blocking questions require justification that uncertainty does not prevent progression. Assumptions cannot replace missing business decisions. Approval belongs to a designated human owner; agents must not fabricate it. A changed approved revision requires downstream impact review and renewed approval.

### Architect input gate

For new or changed business functionality, Architect must inspect the exact SA artifact, its `APPROVED` status and actual requirements-owner approval evidence for its revision and reviewed content. It must also verify the currently approved BA and that SA's `business_input.artifact_id`, `revision` and `content_digest` still identify that BA. Both artifacts must satisfy their documented contract and have no unresolved blockers; FR/NFR references must resolve to the consumed BA. Record SA/BA IDs, revisions, content identities and approval evidence in the handoff, and recheck the input snapshots before publishing architecture. Missing, stale, unapproved, blocked or unverifiable input stops dependent feature architecture; return the failed gate to the responsible analyst/owner.

An explicitly requested baseline architecture creation/audit or maintenance of existing architecture, ADRs, governance or validation can inspect existing sources without approved BA/SA outputs. Report that scope and the missing approvals/artifacts. This exception does not authorize new business functionality, fabricated approval or representing the legacy SR baseline as approved SA.

## Branches and worktrees

One independent feature uses one branch, normally `feature/<short-name>`. Focused
fixes and documentation use `fix/<short-name>` and `docs/<short-name>`. `main` is
the integration branch; do not implement features directly on it. BA, SA,
architecture, implementation and tests may progress sequentially on the same
feature branch, retaining the approval and blocker gates above. A branch does
not authorize bypassing a stage or expanding the requested scope.

For concurrent independent tasks, assign a distinct branch and Git worktree to
each task. All agents collaborating on one feature use its assigned worktree
and explicit file ownership; reviewers read that same branch without editing it.
A worktree isolates checked-out files, not shared Git references or final merge
conflicts. Never checkout another branch in a directory used by active agents.

Before edits, inspect `git status --short`, `git branch --show-current` and
`git worktree list`. The coordinator records task scope, base branch/commit,
feature branch, absolute worktree path and assigned writers in the handoff.
Preserve existing dirty changes; do not reset, discard, automatically stash or
move them into a feature without coordinating with their owner. Choose a fresh
branch/worktree when the current checkout belongs to another task.

Example from the repository root, after selecting the intended base and an
available branch/directory (use a writable location permitted by the environment):

```bash
git worktree add -b feature/parent-registration ../eszkola-parent-registration main
```

This is a future feature example, not a command executed or a feature authorized
by this documentation change. Check repository instructions in the new worktree
and pass its path explicitly to every delegated agent.

Before integration, synchronize with the current target branch while preserving
others' work, resolve conflicts deliberately, and recheck requirements, approval
identities, ADR consistency and affected tests. Record the exact commit reviewed.
Merge to `main` only after applicable BA/SA approvals, tests, architecture checks
and independent review have passed; disclose any remaining verification gaps.
Further changes invalidate review of their affected scope. If integration changes
reviewed content, verify/review the resulting content before merge. Branches and
worktrees do not provide automated branch protection or CI gates.

After integration, release file reservations. Remove a task worktree or branch
only when no agent uses it and no uncommitted or unmerged work remains; do not
force cleanup of another user's work.

## Single-writer coordination

One coordinator (the initiating agent, or the human directing independent sessions) assigns exactly one active writer to each shared artifact path before editing starts. Record the reservation in the task handoff/session: exact path, writer, output scope and the initial revision/content identity (or absence for a new file). This applies especially to `docs/requirements/business-analysis.yaml` and `docs/requirements/system-analysis.yaml`, and also to shared architecture/docs files. Direct single-agent work holds its own reservation; for multiple independent sessions, the human coordinates ownership. Do not claim to have checked sessions that are not visible.

Do not launch competing BA or SA writers for the fixed output paths. Parallel readers and writers of disjoint assigned paths are permitted. If another writer owns a path, ownership is disputed or a known independent session may be writing the same path without established ownership, stop writes to that path and resolve the reservation with the coordinator. A child agent receives explicit ownership and must preserve other agents' edits. Release the reservation on completion/cancellation; before reassignment, verify that the previous writer has stopped.

After reserving, capture the output's initial content snapshot and the exact upstream inputs. Immediately before each write, compare the current output against the initial snapshot (or the writer's last own write), and upstream inputs against the consumed snapshots. If either changed unexpectedly, stop, report the conflict and obtain a fresh reservation/input review; never overwrite or silently merge another writer's revision. Rerun applicable approval/traceability gates after upstream changes. Sequential BA→SA handoff requires BA to release its output and SA to pin the approved snapshot; reserve upstream BA against concurrent edits while SA consumes it.

These are behavioral coordination rules, not filesystem locks, an atomic compare-and-write mechanism or an automated pipeline. `agents.max_concurrent_threads_per_session` permits concurrency but does not enforce ownership. Independent sessions need shared human coordination; snapshot rechecks reduce stale writes but do not remove all races. Automated locking is not implemented.

Reservations identify both the worktree and relative artifact path. Separate
feature worktrees may contain independent drafts at the same relative BA/SA
paths, but never have competing writers to the same checked-out file. Shared
authoritative requirements and ADR changes still need coordinator review before
integration: do not replace one feature's analysis with another's or concatenate
artifacts blindly. Preserve IDs, provenance and approved scope; reconcile coverage
and repeat affected approval/traceability gates when combined content changes.

## Run BA then SA manually

Read [requirements contracts](docs/requirements/README.md). Role prompts explicitly load the relevant documents rather than assuming nested instructions activate a role for a task started at repository root.

```text
Read AGENTS.md, workflow.md, docs/requirements/business-analyst.md and
docs/requirements/README.md. Act as Business Analyst on
docs/biznesplan-platforma-kursy-dla-dzieci.md and
docs/szablon-programu-edukacyjnego-modul-4-zajecia.md.
Produce docs/requirements/business-analysis.yaml as a draft or blocked
artifact. Cite sources, distinguish examples from requirements, and raise
questions. Do not approve the artifact, design architecture or tasks.
```

After actual business-owner approval of the exact BA revision:

```text
Read AGENTS.md, workflow.md, docs/requirements/system-analyst.md and
docs/requirements/README.md. Verify the approval and revision of
docs/requirements/business-analysis.yaml. If the gate passes, act as
System Analyst and produce docs/requirements/system-analysis.yaml.
Trace every FR/NFR to BR IDs. Do not change BA, choose technologies,
design final architecture, create tasks or approve your own output.
```

The current [baseline](docs/requirements/baseline.md) is an architectural subset with stable `SR-01`–`SR-15` references, not approved BA/SA output. Preserve its references and Accepted ADRs. Future normalization requires reviewed coverage mapping to BR/FR/NFR, not inferred approvals. The [existing checker](docs/architecture/README.md#checks-available-now) verifies target model/document coherence; BA/SA contract and approval checks remain manual until an executable validator exists.
