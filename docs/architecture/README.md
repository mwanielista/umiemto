# eSzkola baseline architecture

Baseline date: 2026-10-03. This is the current intended architecture, with explicit implementation gaps. [AGENTS.md](../../AGENTS.md) remains the project constitution. Architecture files and identifiers use English; the future product interface uses Polish.

## AS-IS: verified repository

| Artifact | Verified behavior |
| --- | --- |
| `landing/index.html`, `styles.css`, `script.js`, hero image | Static Polish marketing page branded “Pyk! I umiem to.”; waitlist stores demo entries only in browser `localStorage`. It sends no server signup and is not an account/consent system. Google Fonts is an external browser dependency. |
| `landing/Dockerfile`, `nginx.conf` | Nginx `1.27-alpine` serves static assets with `/` fallback to 404, not Angular routing; no API forwarding, TLS termination or health check is configured. |
| `landing/docker-compose.yml` | One landing service, host port 8080, restart `unless-stopped`. Build context `./landing` requires repository-root project directory. No root Compose file exists. |
| `docs/biznesplan-platforma-kursy-dla-dzieci.md`, `docs/szablon-programu-edukacyjnego-modul-4-zajecia.md` | Business plan and generic educational template with an illustrative mathematics configuration. |
| `.codex/agents/architect.toml`, `.codex/agents/architecture-reviewer.toml` | Architecture and independent read-only review role definitions exist. |

At baseline there is no backend, Angular frontend, database, migration, application build/test wrapper, application API or running integration in the repository. The architecture below is target-only; the landing remains the implemented application.

## TO-BE: accepted baseline

One Spring Boot deployable with domain modules and one PostgreSQL database; an Angular application served behind the same HTTPS origin; private S3-compatible files; external payment, video and email adapters. Initial hosting is a single server with Docker Compose. The existing landing remains a separate static entry point. Module boundaries and data ownership apply even inside one process/database.

Architecture decisions are Accepted when fixed by repository constraints or sufficiently resolved in this baseline. Accepted does not mean implemented. Authentication mechanism remains Proposed pending provider, account and child-login decisions.

| View | Purpose |
| --- | --- |
| [Normalized requirements](../requirements/baseline.md) | Traceable requirements and unresolved business inputs |
| [Analysis contracts](../requirements/README.md), [workflow](../../workflow.md) | Separate BA/SA responsibilities, revision/approval gates and future BR/FR/NFR traceability; existing SR baseline is not approved BA/SA |
| [System context](system-context.md) | Actors, external systems and trust boundaries |
| [Containers](containers.md) | Actual landing and intended runtime/deployment |
| [Components](components.md) | Capabilities, dependency direction and orchestration |
| [Data model](data-model.md) | Logical ownership, versioning, concurrency and consistency |
| [Contracts](contracts.md) | Cross-module contracts, events and HTTP boundary |
| [Security](security.md) | Resource access, MFA, child privacy and file protection |
| [Integrations](integrations.md) | Provider boundaries, failure/retry/reconciliation |
| [Deployment](deployment.md) | Rollout, migration, backup/restore and operations |
| [NFRs](nfr.md) | Quality scenarios and validation evidence |
| [Principles](principles.md), [constraints](constraints.md) | Baseline-specific implementation rules and fitness functions |
| [Implementation handoff](implementation-handoff.md) | Responsibilities, sequence, gates and risks |
| [Machine-readable model](model.json) | Module dependency allowlist and logical persistent-data ownership |

## Decision register

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](decisions/0001-modular-monolith-boundaries.md) | Accepted | Capability modules with explicit public contracts and acyclic dependencies |
| [0002](decisions/0002-owned-persistence-and-history.md) | Accepted | Owned persistence, immutable educational versions and explicit consistency |
| [0003](decisions/0003-durable-effects-and-payments.md) | Accepted | PostgreSQL-backed durable delivery and idempotent payment fulfillment |
| [0004](decisions/0004-resource-authorization.md) | Accepted | Role plus resource authorization, scoped privileged access and audit |
| [0005](decisions/0005-runtime-and-api-boundary.md) | Accepted | Same-origin API, single-server Compose, provider adapters and recovery boundaries |
| [0006](decisions/0006-authentication-options.md) | Proposed | Same-origin server session recommendation; credential authority unresolved |
| [0007](decisions/0007-deterministic-analysis-orchestration.md) | Accepted | Deterministic repository orchestration and controller-owned approval/write boundaries |

The [analysis factory](../orchestrator.md) automates BA/SA contract/approval gates through architecture review and validation. It is repository tooling, separate from the product runtime; installation does not approve requirements.

## Checks available now

Run from repository root:

```bash
python3 docs/architecture/validation/check_baseline.py
python3 docs/architecture/validation/check_baseline.py --self-test
docker compose --project-directory . -f landing/docker-compose.yml config
```

The Python check uses only the standard library. It validates the target model, unique logical data ownership, acyclic dependency allowlist, ADR structure/status and local documentation links. Self-tests exercise rejected graph/ownership cases. It does **not** inspect application bytecode, execute migrations, prove security or render Mermaid. Application fitness functions are specified in [constraints](constraints.md); they must be implemented at bootstrap. No application command is claimed to exist.
