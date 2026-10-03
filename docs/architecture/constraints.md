# Architecture constraints and fitness functions

[model.json](model.json) is a target dependency allowlist and logical ownership registry, not evidence of source compliance. [AGENTS.md](../../AGENTS.md) supplies repository rules; the following connects baseline decisions to checks.

| Constraint | Baseline check available | Required implementation fitness function |
| --- | --- | --- |
| Unique module/entity IDs, known edges, acyclic imports, no self-dependency | `validation/check_baseline.py` + negative self-tests | Compile-time/ArchUnit module graph compared with allowlist |
| Exactly one owner per logical persistent entity; workflows owns no business persistence | JSON ownership check | Owner-prefixed migrations; no foreign persistence access; review entity-to-table registry |
| Only `.api` crosses modules; no provider/ORM models in public/domain contracts | Specified in model/package convention only | ArchUnit detects forbidden foreign private/package dependencies; DTO/schema contract checks |
| Domain independent of HTTP/ORM/providers; controllers delegate business coordination | Not provable without source | Compiled layer dependency rules plus focused code review |
| Defined ADR status/sections and local documentation links | Python document consistency check | ADR impact and architecture review for significant changes |
| Role + resource authority, privileged MFA and transactional audit | Documented only | Actor/resource negative integration tests; audit rollback and assurance checks |
| Immutable content/attempt history and final-only progression | Documented only | Version/edit/correction tests and concurrent activation/grade tests |
| Verified, deduplicated payments and durable local effects | Documented only | Real PostgreSQL callback/fulfillment crash/retry/concurrency tests + provider sandbox |
| Migration, money, time and private-file invariants | Documented only | Empty/upgrade database tests; decimal/currency, Warsaw DST and quarantine/access checks |
| Deployable config, compatible tooling, protected exposure and recovery | Existing landing Compose config command | New config/build/readiness/proxy/TLS checks and isolated backup restore rehearsal |

## Checker scope

Run `python3 docs/architecture/validation/check_baseline.py`; use `--self-test` to additionally prove representative invalid models are rejected. The standard-library checker parses the model, validates its specific structure/invariants and checks Markdown file links/ADR headings. It has no application dependencies and starts nothing.

It does not validate physical SQL, inspect Java/TypeScript imports, certify security, compare full source behavior, render Mermaid or replace an independent review. Those gaps are intentional and must be closed during actual implementation. Do not report a target model passing as an implementation test passing.
