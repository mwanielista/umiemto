# Requirements and analysis contracts

Sources remain authoritative: [business plan](../biznesplan-platforma-kursy-dla-dzieci.md), [educational template](../szablon-programu-edukacyjnego-modul-4-zajecia.md) and [AGENTS.md](../../AGENTS.md). The mathematics example is not a universal business rule.

| Document | Purpose |
| --- | --- |
| [Workflow](../../workflow.md) | Stage ownership, gates and run prompts |
| [Business Analyst](business-analyst.md) | Business analysis responsibilities and quality gate |
| [System Analyst](system-analyst.md) | System requirements and BR traceability |
| [Baseline](baseline.md) | Existing architectural subset and unresolved inputs |
| [Architecture](../architecture/README.md) | Current intended architecture and implementation gaps |

Outputs belong directly in `docs/requirements/business-analysis.yaml` and `docs/requirements/system-analysis.yaml`; inputs remain in their current locations. The [factory](../orchestrator.md) implements executable contract/approval gates. Installing tooling does not create approved analysis outputs or new agent registrations.

## Machine-readable artifact contract, version 1

This is a documented YAML/JSON specification, not an executable JSON Schema. Field names use English. Each output is an object with the following required fields; lists are arrays, textual fields are nonempty strings unless explicitly nullable.

| Field | Shape and meaning |
| --- | --- |
| `schema_version` | Integer `1`; contract version independent of content revision |
| `artifact_type` | `business_analysis` or `system_analysis` |
| `artifact_id`, `revision` | Stable artifact string ID and positive integer content revision |
| `status` | `DRAFT`, `READY_FOR_REVIEW`, `APPROVED` or `BLOCKED` |
| `scope` | Explicit analyzed scope and exclusions |
| `sources` | Nonempty array of `{id, location, revision}`; revision identifies actual input content, e.g. commit or digest |
| `approval` | `null` until explicit approval; otherwise `{owner, approved_at, artifact_revision, evidence}` identifying actual human approval and exact approved revision; timestamp includes offset |
| `assumptions`, `constraints` | Arrays of `{id, description, source_refs}`; assumptions are explicitly unconfirmed |
| `open_questions` | Array of `{id, question, severity, owner, affected_refs, status, resolution}`; severity `BLOCKER`/`NON_BLOCKER`, status `OPEN`/`RESOLVED`, resolution null until answered, then `{answer, evidence}` |
| `section_notes` | Object mapping empty section names to explanations; empty lists require a reason, never placeholder entries |

`source_refs` is a nonempty array of `{source_id, locator}` citing an existing source ID and a precise section/location. A requirement has `{id, description, rationale, priority, acceptance_criteria, source_refs}`; priority is `MUST`/`SHOULD`/`COULD`, acceptance criteria are a nonempty string array. IDs are unique within an artifact, stable across revisions and never reused after retirement.

BA adds required arrays: `goals`, `stakeholders`, `actors`, `processes`, `business_requirements`, `business_rules`, `glossary`. `business_requirements` uses `BR-xxx` IDs and the requirement shape above. Other business entries have `{id, description, source_refs}`; process entries also list `actor_refs` and ordered `steps`, glossary entries add `term`. No architecture, technology-selection or implementation-task sections belong in BA.

SA adds `business_input: {artifact_id, revision, content_digest}` identifying the exact approved BA, plus required arrays: `functional_requirements`, `non_functional_requirements`, `system_actors`, `use_cases`, `domain_concepts`, `data_requirements`, `integrations`, `edge_cases`, `error_scenarios`, `security_requirements`, `br_coverage`. FR/NFR use the requirement shape plus nonempty `br_refs`, with `FR-xxx`/`NFR-xxx` IDs. Supporting entries use `{id, description, requirement_refs}` referencing valid FR/NFR IDs; use cases also include `actor_refs`, `preconditions`, ordered `main_flow`, `alternatives` and `postconditions`. Coverage entries use `{br_id, requirement_refs, exclusion_reason}`; every input BR appears, with a reason when no FR/NFR applies. No technology choices, final architecture or implementation-task sections belong in SA.

Unknown business or system details are questions, not invented mandatory values. Unknown owner names are recorded as `unassigned`, with ownership itself treated as a blocker when necessary for approval. Non-blocker severity requires a reason in the question text that the uncertainty permits progression. Validation cannot prove source truth or that an approval is genuine; human review remains necessary.

## Revision, approval and traceability policy

Only an actual designated owner can approve the exact reviewed revision. `READY_FOR_REVIEW` and `APPROVED` require complete content and no open blockers; any open blocker requires `BLOCKED`. Keep resolved questions and their evidence. A changed artifact receives a new content revision, loses approval and invalidates dependent readiness until impact review and renewed approval. SA cannot approve or edit BA to bypass its input gate. Changing contract meaning requires a new schema version and documented compatibility/migration rather than silent reinterpretation.

Architect checks approval and reviewed content identity of the exact SA revision, both BA and SA blockers, and SA's consumed BA ID/revision/digest against the currently approved BA. It records these inputs in its handoff; unknown content identity or stale approval fails progression. See the [Architect input gate](../../workflow.md#architect-input-gate) for the explicit baseline-maintenance exception, which never treats this legacy baseline as approved SA.

All writers follow [single-writer coordination](../../workflow.md#single-writer-coordination): coordinator reservation per output path, no competing fixed-path BA/SA writers, upstream/output snapshots and rechecks before writing. Reservations are behavioral, not filesystem-enforced locks; agents must report conflicts rather than overwriting another writer's work.

The [baseline](baseline.md) predates this contract and is not approved BA/SA. Preserve `SR-01`–`SR-15` and ADR links. Future reviewed normalization must record legacy SR → BR/FR/NFR coverage, including gaps; do not rename SRs or fabricate BR links and approvals. Future Planner tasks trace to approved FR/NFR; this requirement does not authorize task creation during BA/SA.

## Validation expectations

### Factory external approval evidence

The factory preserves version 1 fields and `business_input` lineage. Before human confirmation it prepares a candidate with `APPROVED` status and embedded `{owner, approved_at, artifact_revision, evidence}` referencing an external `.orchestrator/approvals/` record. It displays the complete candidate and final raw-byte SHA-256. Confirmation approves those exact bytes; external evidence binds type/path/artifact ID/revision/digest and is authoritative. Embedded approval or agent-generated statements alone never pass a gate. Content changes require a new revision and approval; external records remain immutable. See [ADR-0007](../architecture/decisions/0007-deterministic-analysis-orchestration.md).

Factory validates required fields/types, nonempty requirement criteria/sources, unique IDs, references, complete BR coverage, approved BA identity, external approval binding and blocker/status consistency. Negative tests cover dangling BRs, duplicate IDs, stale approvals/digests, blockers and missing criteria. Source truth, stable ID meaning across revisions, absence of disguised design/task content and semantic role boundaries still require human review.

The existing `docs/architecture/validation/check_baseline.py` verifies target architecture model/ADRs/local document links only. Factory separately enforces artifact contracts, approval gates and BA/SA traceability; the baseline checker does not replace those checks.
