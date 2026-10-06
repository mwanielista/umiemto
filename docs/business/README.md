# Owner-maintained product decisions

[product-decisions.yaml](product-decisions.yaml) is maintained by Michał Wanielista, the sole business/product/requirements owner. It starts empty: tooling installation invents no decisions and approves no BA/SA revision. Analysts and generated BA/SA are not decision authorities and may not edit this registry during inference.

The executable convention is `DECISION_SCHEMA` in [orchestrator/sources.py](../../orchestrator/sources.py); the equivalent [JSON Schema](product-decisions.schema.json) is supplied for editors. Root contains exactly `schema_version: 1`, `owner: Michał Wanielista` and `decisions`. Each decision contains exactly:

| Field | Convention |
| --- | --- |
| `id` | Unique stable identifier, e.g. DEC-001; retain it when superseded |
| `status` | ACTIVE for current binding decisions, SUPERSEDED for retained history |
| `decision` | Explicit owner decision text, not generated inference |
| `rationale` | Why this decision applies |
| `supersedes` | String list of replaced decision IDs or precise legacy source locations; empty for a new decision |
| `source` | `{location, locator}` identifying the actual owner statement/evidence |
| `date` | Quoted ISO date, e.g. `"2026-10-06"`; unquoted YAML date objects are rejected |

When replacing an earlier registry decision, retain it with SUPERSEDED status and add an ACTIVE decision referencing it. ACTIVE decisions outrank conflicting generated BA and legacy sources. SUPERSEDED decisions retain historical evidence; they cannot independently require a blocker or missing-history reconfirmation. A current explicit owner answer may resolve an existing question with real evidence, but it never grants exact-content approval of an artifact.

Precedence: current explicit owner decision > current owner-maintained source > historical source > generated BA. The controller validates schema, unique IDs, dates, configured source byte identity and excludes generated analysis/runtime/architecture artifacts from business inputs. It supplies the precedence policy to both roles. Semantic conflict detection, whether a source is genuinely owner-maintained, evidence truth and correct question severity require analyst and owner review. Python does not prove those properties.

The registry is a required configured source; its absence/malformed structure fails closed. Removing an ordinary source is represented by removing its configured path, with exact previous source bytes retained in provenance for impact review. A path that remains configured but disappears is a missing input error.
