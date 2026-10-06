# Incremental BA/SA transport contract, version 1

This transport preserves the [artifact contract](README.md). [ADR-0008](../architecture/decisions/0008-incremental-analysis-patches.md) extends ADR-0007 for incremental analysts only. Full BA/SA and Architect return file proposals; Reviewer returns findings. Incremental BA/SA return the patch object itself, without a `files` or `review` wrapper. `AgentResult.patch` is the adapter representation, not a JSON response wrapper.

The executable strict JSON Schema is `patch_schema(kind)` in [orchestrator/patches.py](../../orchestrator/patches.py); `kind` is `business_analysis` or `system_analysis`. Its entry schemas encode every existing BA/SA section, including process/use-case fields, question resolutions and BR coverage. The controller validates the same schema locally; no third-party schema library is required. All objects use `additionalProperties: false`. Contract schemas and role instructions are hashed reanalysis inputs.

```json
{
  "schema_version": 1,
  "artifact_type": "business_analysis",
  "base": {
    "artifact_id": "example-ba",
    "revision": 5,
    "content_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "operations": [
    {"op": "set_scope", "value": "Owner-confirmed scope and exclusions"},
    {"op": "set_status", "value": "READY_FOR_REVIEW"}
  ]
}
```

The example is protocol syntax, not a business decision or executable approval. `base` must match exact supplied baseline ID/revision/raw-byte SHA-256, including approved metadata when present.

| Operation | Exact additional fields | Meaning |
| --- | --- | --- |
| `create` | `section`, `entry` | Add complete correctly typed entry with unused stable ID |
| `update` | `section`, `entry` | Replace complete existing entry, preserving its ID |
| `remove` | `section`, `id` | Retire an existing entry; prohibited for questions |
| `resolve_question` | `id`, `resolution: {answer, evidence}` | Resolve an OPEN question exactly once using current evidence |
| `set_scope` | `value` | Replace the scope string |
| `set_section_note` | `section`, `value` | Set an explanation for a contract section or existing standard report note |
| `set_status` | `value` | DRAFT, READY_FOR_REVIEW or BLOCKED; never APPROVED |

Sections are enumerated per role; no arbitrary paths or pointers. BR coverage uses `br_id` as its key (`remove.id` is that BR ID); retirement uses a separate `coverage:` namespace. Strings are bounded to 20,000 characters, stable IDs to 128 ASCII identifier characters, arrays to 1,000 entries and a patch to 500 operations. Requirement and referenced entry shapes are closed. Question updates preserve status/resolution; lifecycle changes use `resolve_question`. Resolved evidence and all prior questions are retained even in full reanalysis. An old resolution cannot be rewritten; cite a superseding decision in affected requirements/notes while retaining that evidence.

The entire patch is applied to a deep copy and validated before canonical promotion. Unknown entry update/removal, duplicate creation, reuse after retirement, repeat resolution, invalid traceability, missing criteria, wrong base and control-field injection fail without changing canonical bytes. Controller owns revision increment, approval clearing, and current approved BA lineage in SA. Deterministic serialization sorts mapping keys; list order remains meaningful. Changed output requires fresh external approval. DRAFT fails the readiness gate before promotion; BLOCKED remains a valid stored result and halts progression.

Input context supplies the compact complete baseline, exact identity, all OPEN questions, retired IDs, configured source digests and changed source text/diffs. Known deltas classify added/changed/removed/unchanged. Unchanged source text and extra history are excluded. UNKNOWN adoption supplies current sources with null old digests; citations in legacy BA are not treated as a verified historical snapshot. ACTIVE current owner decisions supersede conflicting legacy BA; SUPERSEDED entries cannot independently generate blockers. This is an explicit semantic responsibility of the analyst and reviewing owner, not a claim that Python understands the business meaning.

Incremental SA first passes the current BA approval gate. Its previous artifact is structurally validated against its archived consumed approved BA and that BA's exact external evidence. Context includes semantic BA changes, historical consumed identity/evidence and current approved BA/evidence. Missing verified historical input falls back to full SA; no stale baseline is patched. All SA traceability/coverage validators run against current BA before promotion, then changed SA waits for its own approval. Architecture gates remain unchanged.
