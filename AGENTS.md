# Agent Instructions for eSzkola

## Purpose of This File

`AGENTS.md` defines the repository-wide context, constraints, and working rules for coding agents such as Codex.

Before modifying this repository, all agents must follow the rules described here, including:

- product scope,
- business constraints,
- technology stack,
- architectural principles,
- architecture workflow,
- security requirements,
- testing and verification rules,
- documentation requirements.

This file does not start or configure the application itself. Its purpose is to preserve consistency across work performed by multiple agents over time.

These instructions apply to the entire repository.

More specific `AGENTS.md` files placed in subdirectories may add or refine instructions for those areas, but they must not contradict repository-level architectural decisions unless explicitly authorized.

The user's current explicit instruction has priority over assumptions derived from documentation.

---

# 1. Sources of Truth

The following files contain the current product and business context.

## Business and product requirements

`biznesplan-platforma-kursy-dla-dzieci.md`

Contains the product concept, business processes, roles, expected architecture, MVP priorities, and major business assumptions.

Read the relevant sections before implementing or designing functionality related to them.

## Educational program model

`szablon-programu-edukacyjnego-modul-4-zajecia.md`

Defines the expected structure of:

- educational programs,
- learning outcomes,
- assessments,
- retakes,
- progress reporting.

The included mathematics example is an example configuration only.

It must not be treated as a universal business rule for all courses.

## Existing application

`landing/`

Contains the current static marketing landing page for the product.

It is served through Nginx.

## Current deployment

`docker-compose.yml`

Currently starts only the landing page on port `8080`.

Spring Boot backend and Angular frontend do not yet exist.

Therefore, architecture described below represents the intended target direction rather than the current implemented system.

Do not claim that backend, frontend, tests, APIs, or build commands already exist until they are actually created.

---

# 2. Product Goal

eSzkola is an educational platform targeting the Polish market.

A parent purchases access for a child to an educational module containing four online lessons with a teacher.

The intended learning flow is:

```text
diagnosis
    ↓
lessons
    ↓
homework and practice
    ↓
exam
    ↓
feedback
    ↓
next module
```

The initial pilot focuses on mathematics for one age group, currently expected to be grades 5–6, with small groups of approximately 4–6 students.

The domain model must allow future support for:

- English,
- German,
- additional school subjects,
- additional age groups,

without requiring redesign of the core learning and commerce processes.

---

# 3. MVP Scope

The initial MVP includes:

- parent accounts,
- child profiles,
- parental consents,
- educational module catalog,
- scheduled groups,
- enrollment,
- orders,
- payments,
- lesson schedules,
- links to external video lessons,
- educational materials,
- attendance,
- homework,
- student submissions,
- practice exercises,
- exams,
- retakes,
- teacher panel,
- parent progress reports,
- educational content administration,
- email notifications,
- limited asynchronous consultations,
- audit trail for privileged and important actions.

Do not extend the MVP without an explicit task.

The following are specifically out of scope unless explicitly requested:

- proprietary video conferencing,
- AI tutor,
- teacher marketplace,
- native mobile applications,
- open social chat,
- unnecessary microservices,
- complex distributed infrastructure.

---

# 4. Target Technology Stack

## Backend

- Java
- Spring Boot
- modular monolith
- HTTP/JSON API
- PostgreSQL
- versioned database migrations

The repository should use:

```text
backend/
```

for backend application code.

Select mutually compatible and currently supported Java and Spring Boot versions when the backend is created.

Record the selected versions in project configuration and documentation.

## Frontend

- Angular
- TypeScript
- responsive web application
- Polish product interface

The repository should use:

```text
frontend/
```

for the Angular application.

Select mutually compatible and supported Angular, Node.js, and related tooling versions.

Record the selected versions in project configuration and documentation.

## Persistence

Use PostgreSQL as the primary relational database.

Schema changes must be managed through versioned migrations.

Do not manually rely on production schema changes outside the migration mechanism.

## File storage

Educational materials and attachments must use S3-compatible object storage.

For production environments, prefer storage hosted in the EU/EEA when feasible.

## Deployment

Initial deployment should use:

- Docker images,
- Docker Compose,
- a single server.

Do not introduce Kubernetes unless a concrete operational requirement justifies it.

Do not introduce Redis, dedicated message brokers, or additional distributed infrastructure unless a measurable requirement justifies them.

## External systems

Use external providers for:

- video conferencing,
- payment processing.

Provider-specific logic must be isolated from domain logic.

---

# 5. Repository Structure

The expected high-level structure is:

```text
/
├── AGENTS.md
├── .codex/
│   └── agents/
│
├── docs/
│   ├── requirements/
│   └── architecture/
│       ├── README.md
│       ├── principles.md
│       ├── constraints.md
│       ├── nfr.md
│       ├── system-context.md
│       ├── containers.md
│       ├── components.md
│       ├── data-model.md
│       ├── integrations.md
│       └── decisions/
│
├── backend/
├── frontend/
├── landing/
└── docker-compose.yml
```

Do not remove or replace `landing/` unless the current task explicitly requires it.

---

# 6. Architecture Governance

Architecture is a first-class repository artifact.

Architectural decisions must not exist only in chat responses or implementation code.

Relevant architecture documentation must be stored under:

```text
docs/architecture/
```

Architectural Decision Records must be stored under:

```text
docs/architecture/decisions/
```

Business and system requirements intended for implementation should gradually be normalized under:

```text
docs/requirements/
```

Existing business documents remain valid sources until their relevant requirements are migrated or superseded.

---

# 7. Architect Agent

The repository defines a specialized architecture agent:

```text
architect
```

Expected configuration location:

```text
.codex/agents/architect.toml
```

The architect owns architecture decisions.

Implementation agents do not independently redefine architecture when a change is architecturally significant.

---

# 8. When to Delegate to the Architect

Before implementation, delegate the task to the `architect` agent if the requested change includes any of the following:

- creation of a new domain or major module,
- modification of domain boundaries,
- modification of module dependencies,
- new persistence ownership,
- significant database model changes,
- authentication architecture,
- authorization architecture,
- role or permission model changes,
- external integrations,
- payment integration changes,
- asynchronous processing,
- messaging,
- queues,
- event-driven communication,
- major API changes,
- shared contracts between modules,
- storage architecture,
- deployment topology changes,
- infrastructure architecture,
- introduction of a major dependency,
- scalability-sensitive functionality,
- availability-sensitive functionality,
- reliability-sensitive functionality,
- security-sensitive functionality,
- observability architecture,
- significant performance decisions,
- changes that conflict with an existing ADR.

Implementation should not begin until the relevant architectural questions have been resolved sufficiently.

---

# 9. Architect Responsibilities

The architect is responsible for:

- architectural decomposition,
- bounded contexts,
- domain boundaries,
- module boundaries,
- dependency direction,
- component responsibilities,
- data ownership,
- API boundaries,
- integration patterns,
- event and message contracts,
- persistence strategy,
- authentication architecture,
- authorization architecture,
- cross-cutting concerns,
- security architecture,
- scalability considerations,
- resilience considerations,
- availability considerations,
- observability architecture,
- deployment architecture,
- architectural risks,
- architecture documentation,
- Architectural Decision Records,
- architecture fitness functions,
- detection of architectural drift.

The architect should inspect the repository before proposing changes.

Architecture must be based on:

1. actual business requirements,
2. actual existing code,
3. existing architecture documentation,
4. accepted ADRs,
5. non-functional requirements,
6. explicit technical constraints.

Do not invent business requirements to simplify architectural work.

---

# 10. Architect Boundaries

The architect should normally modify:

- `docs/architecture/**`,
- `docs/requirements/**` when clarifying technical requirements,
- architecture model files,
- ADR files,
- architecture validation rules,
- architecture tests,
- dependency constraints,
- interface definitions,
- API contracts when explicitly part of architecture work.

The architect should not normally implement business features.

In particular, the architect should not become the default agent for:

- CRUD implementation,
- controller implementation,
- UI implementation,
- CSS changes,
- feature-specific business logic,
- routine bug fixes.

The architect defines implementation boundaries and constraints for downstream implementation agents.

---

# 11. Architectural Principles

Prefer:

- simple architecture over clever architecture,
- modular monolith over microservices unless distribution is justified,
- explicit module boundaries,
- high cohesion,
- low coupling,
- domain-oriented decomposition,
- explicit contracts,
- clear data ownership,
- stateless application services where practical,
- infrastructure as code,
- architecture as code,
- automated architectural enforcement,
- evolutionary architecture,
- backward-compatible public contracts where practical.

Avoid:

- premature microservices,
- cyclic dependencies,
- hidden coupling,
- shared mutable state,
- database tables implicitly owned by multiple modules,
- direct access to another module's persistence layer,
- business logic in HTTP controllers,
- business logic embedded in infrastructure adapters,
- speculative abstractions,
- technology choices without justification,
- architecture introduced only because it is fashionable.

---

# 12. Backend Architecture

The backend should be organized by business capability rather than only by technical layers.

Expected domains include, subject to architectural validation:

- identity and permissions,
- catalog and educational programs,
- groups and enrollment,
- lessons,
- assignments,
- exams and assessments,
- consultations,
- commerce and payments,
- reporting.

Within modules, separate responsibilities clearly.

As a general rule:

- controllers handle HTTP concerns,
- application services coordinate use cases,
- domain logic implements business rules,
- repositories handle persistence,
- adapters handle infrastructure and external integrations.

Do not expose persistence entities directly through HTTP APIs.

Use DTOs and explicit API contracts.

Use input validation.

Use transactions where atomicity is required.

External provider implementations must not leak into domain logic.

---

# 13. Modular Monolith Rules

Until an ADR explicitly changes this decision, treat the backend as a modular monolith.

Modules should communicate through explicit public contracts.

Avoid:

```text
Module A
    ↓
Module B internal repository
```

Prefer:

```text
Module A
    ↓
Module B public application/domain contract
```

A module must not directly depend on another module's internal persistence implementation.

Avoid cyclic module dependencies.

Where practical, architectural constraints should be enforced automatically through tests or dependency rules.

For Java, tools such as ArchUnit may be used to implement architecture fitness functions.

---

# 14. Angular Architecture

Organize the frontend primarily by product features and user workflows.

Prefer structures aligned with business capabilities rather than a single global technical-layer hierarchy.

Maintain:

- typed API models,
- dedicated API communication services,
- clear feature boundaries,
- explicit routing ownership,
- reusable shared components only when genuinely shared.

Critical authorization and business rules must always be enforced by the backend.

Frontend restrictions are user experience mechanisms, not security boundaries.

Do not treat hidden buttons or routes as sufficient authorization.

---

# 15. Architecture Documentation

Use the C4 model where appropriate.

Maintain at least:

- System Context,
- Container view.

Create Component views when they materially improve understanding.

Avoid unnecessary class-level architecture diagrams.

Prefer architecture-as-code formats when practical.

Architecture documentation describes the current intended architecture.

Do not use architecture documentation as a chronological history of every design discussion.

Historical decisions belong in ADRs.

---

# 16. Architectural Decision Records

Create ADRs for architecturally significant decisions.

Do not create ADRs for trivial implementation details.

An ADR should contain at least:

```text
Title
Status
Context
Problem
Constraints
Considered options
Decision
Rationale
Consequences
Risks
Rejected alternatives
Validation / fitness functions
```

Supported statuses:

- Proposed
- Accepted
- Deprecated
- Superseded

Do not silently rewrite the meaning of an accepted ADR.

If an accepted architectural decision changes, create a new ADR that supersedes the old one.

---

# 17. Architecture Workflow

For architecturally significant work, follow this sequence:

```text
business requirement
        ↓
system requirement
        ↓
architecture analysis
        ↓
architecture decision
        ↓
implementation boundaries
        ↓
implementation
        ↓
tests
        ↓
architecture review
```

The architect should:

1. understand the requirement,
2. identify architecturally significant requirements,
3. inspect the current repository,
4. inspect existing architecture documentation,
5. inspect accepted ADRs,
6. identify impacted domains and components,
7. identify constraints,
8. identify relevant NFRs,
9. consider multiple viable approaches when a meaningful trade-off exists,
10. document trade-offs,
11. recommend an architecture,
12. create or update ADRs where appropriate,
13. update architecture documentation,
14. define implementation responsibilities,
15. define machine-checkable architecture constraints where practical.

---

# 18. Architecture Review

After implementation of an architecturally significant change, architecture compliance should be reviewed.

The review should compare:

```text
intended architecture
        ↓
actual implementation
```

Check for:

- module boundary violations,
- unexpected dependencies,
- data ownership violations,
- API contract violations,
- architectural drift,
- new hidden coupling,
- security boundary violations,
- undocumented infrastructure changes,
- ADR violations.

Where practical, this review should eventually be performed by a separate read-only `architecture-reviewer` agent.

---

# 19. Architecture as Code

Architectural decisions should be converted into executable constraints where practical.

Examples include:

- ArchUnit rules,
- dependency rules,
- package visibility constraints,
- Nx or ESLint module-boundary rules,
- API schema validation,
- database migration validation,
- contract tests,
- infrastructure validation,
- architecture model validation.

Prefer:

```text
architecture decision
        ↓
machine-readable constraint
        ↓
CI validation
        ↓
PASS / FAIL
```

over architecture rules that exist only as documentation.

Not every architectural property can or should be automated, but enforceable rules should be automated whenever the cost is reasonable.

---

# 20. Non-Functional Requirements

Architecturally significant changes must consider relevant quality attributes.

Consider, when applicable:

- maintainability,
- security,
- privacy,
- performance,
- scalability,
- reliability,
- availability,
- observability,
- testability,
- operational complexity,
- deployment complexity,
- cost,
- auditability,
- recoverability.

Do not optimize quality attributes that are not relevant to the requirement.

Avoid speculative scalability work without evidence of need.

---

# 21. Domain Rules

The following rules are current business constraints.

## Parent responsibility

The parent is responsible for:

- purchasing,
- required consents,
- managing the child's participation where legally required.

A child must not independently perform payments.

## Educational module model

Separate:

- module definition,
- module/program version,
- scheduled group,
- lesson schedule,
- enrollment.

Do not merge these concepts into a single entity merely for implementation convenience.

## Learning progression

Passing the previous module is required to begin the next module.

Passing the previous module is not necessarily required to purchase the next module.

An exception approved by an authorized educational role must be recorded in the audit trail.

## Retakes

The first retake is currently free.

Additional retakes are charged according to the current pricing configuration.

Do not hard-code example prices.

Do not hard-code one universal VAT rate.

Pricing rules must remain configurable where the business documentation marks them as configurable.

## Assessment rules

Passing thresholds, learning outcome criteria, time limits, and retake rules belong to the educational program version.

Do not globally hard-code a `75%` passing threshold.

## Versioning

Preserve the exact versions of:

- educational program,
- questions,
- answer criteria,
- assessment rules,

that were used for a specific exam attempt.

Later edits must not change historical assessment results.

## Manual grading

Open-ended assignments or exam questions may require teacher review.

Distinguish:

```text
preliminary result
```

from:

```text
final approved result
```

Do not unlock learning progression based on an unapproved preliminary result.

## Consultations

Consultations must be:

- limited in scope,
- limited according to product rules,
- archived,
- available to the authorized parent where appropriate.

Do not direct children to teachers' private communication accounts.

## Money

Represent monetary values using decimal-safe types.

Always associate amounts with a currency.

Never use binary floating-point types for persisted or calculated monetary values.

Show the full gross price before purchase.

## Payments

Payment confirmation must be verified server-side.

Payment webhooks must be idempotent.

Processing the same provider webhook multiple times must not:

- create duplicate enrollments,
- create duplicate payments,
- duplicate business operations.

## Time

Store significant event timestamps with an unambiguous instant, timezone, or offset representation as appropriate.

Display schedules to users using:

```text
Europe/Warsaw
```

and correctly handle daylight saving time transitions.

---

# 22. Authorization

Authorization must validate both:

1. user role,
2. access to the specific resource.

Examples:

A parent may access only authorized children and associated resources.

A teacher may access only assigned groups and relevant educational data.

Permissions for:

- educational methodologists,
- support staff,
- administrators,

must be separated according to responsibilities.

Do not implement security based only on broad roles when resource-level authorization is required.

---

# 23. Security and Privacy

Minimize collection and retention of children's personal data.

Do not write the following into application logs:

- passwords,
- authentication secrets,
- access tokens,
- payment card data,
- sensitive personal data.

Secrets must remain outside the repository.

`.env.example` may contain:

- variable names,
- safe placeholder values.

It must not contain real credentials.

Audit at least:

- grade changes,
- permission changes,
- privileged actions,
- sensitive administrative operations.

Account for MFA for teachers, administrators, and other privileged users.

Attachments must support appropriate:

- size limits,
- file validation,
- malware scanning,
- access control.

---

# 24. UI and Accessibility

The child-facing interface should clearly communicate the next expected action.

Aim for WCAG 2.2 AA.

Consider:

- keyboard navigation,
- form labels,
- sufficient contrast,
- understandable validation,
- readable error messages,
- responsive layouts.

Mathematical formulas should be represented using LaTeX-compatible notation and rendered using a suitable library such as KaTeX or MathJax.

Mathematical answers must be evaluated server-side according to the rules of the exercise.

Never execute arbitrary code received from mathematical expressions.

Do not send exam answer keys to the browser before the assessment is complete and authorized for review.

---

# 25. Docker and Initial Deployment

When expanding Docker Compose, add services for:

- backend,
- frontend,
- PostgreSQL.

Build the Angular frontend using a dedicated build stage.

Serve the frontend using Nginx or an equivalent production web server.

Provide:

- Angular route fallback,
- `/api` forwarding to the backend.

Separate local development configuration from production configuration.

Production requires HTTPS.

Pin image versions and dependency versions.

Do not rely on the `latest` tag.

Add appropriate:

- health checks,
- restart policies,
- database readiness handling.

PostgreSQL data must survive container recreation through persistent storage.

A persistent volume is not a backup.

Document:

- migration process,
- backup process,
- restore process,
- rollback strategy.

Routine deployment must never remove user data volumes.

Production exposure should include only ports that are actually required.

---

# 26. Working Rules for All Agents

Before modifying code:

1. inspect Git status,
2. inspect relevant documentation,
3. inspect relevant accepted ADRs,
4. inspect nearby implementation,
5. understand whether the task is architecturally significant.

Preserve unrelated changes made by other users or agents.

Do not perform unrelated refactoring as part of a focused task.

Code, identifiers, API field names, and technical artifacts should be written in English.

Product-facing messages and user-facing explanations should normally be in Polish unless the current task explicitly requires another language.

Document important implementation and operational decisions together with the change.

---

# 27. Implementation Agents

Backend, frontend, and other implementation agents must follow accepted architectural decisions.

Implementation agents must not silently violate an ADR.

If correct implementation appears to require violating an accepted ADR:

1. stop the conflicting implementation,
2. identify the conflict,
3. delegate architectural analysis to the `architect`,
4. resolve the architectural decision before continuing.

Implementation agents may make local implementation decisions when they do not alter architectural boundaries or significant architectural decisions.

---

# 28. Testing and Verification

Verification must match the type of change.

Prioritize tests for:

- user data isolation,
- authorization,
- module completion,
- exam progression,
- retakes,
- payment processing,
- duplicate payment webhooks,
- database migrations.

For frontend changes, verify where relevant:

- modified user flows,
- error states,
- responsive/mobile behavior,
- authorization-dependent views.

Do not claim that a test was executed unless it was actually executed.

Do not treat commands that do not yet exist as valid project commands.

Currently, landing configuration can be checked with:

```bash
docker compose config
```

and started locally using:

```bash
docker compose up --build -d
```

After backend creation, add and commit a Maven or Gradle wrapper.

After frontend creation, define actual npm scripts.

Document real commands for:

- build,
- test,
- run,
- migration,
- local development.

---

# 29. Definition of Done

A feature is not complete until all relevant conditions are satisfied:

- functional requirements are implemented,
- authorization rules are implemented,
- required tests pass,
- architecture constraints pass,
- persistence changes have migrations,
- external contracts are documented,
- architecture documentation is updated if architecture changed,
- relevant ADRs are updated or created,
- user-facing behavior is verified,
- remaining unverified areas are explicitly identified.

---

# 30. Required Final Agent Report

At the end of every task, report:

## Changed

What was changed.

## Verification

What commands, tests, or checks were actually executed.

## Architecture impact

Whether the change affected architecture.

If yes, identify:

- affected ADRs,
- affected architecture documentation,
- architectural constraints introduced or modified.

## Not verified

Anything that remains unverified.

Do not hide incomplete verification.

---

# 31. Updating This File

Update `AGENTS.md` when:

- the actual repository structure changes,
- the agreed technology stack changes,
- architecture governance changes,
- agent responsibilities change,
- repository-wide development rules change.

Do not update this file merely because one feature has a local implementation detail.

Prefer a more specific `AGENTS.md`, ADR, or feature documentation when the rule applies only to one area.

---

# 32. Core Rule

Architecture constrains implementation.

Business requirements constrain architecture.

Implementation agents must not silently redefine either.

The expected workflow is:

```text
Business Requirements
        ↓
System Analysis
        ↓
Architecture
        ↓
Implementation
        ↓
Verification
        ↓
Architecture Compliance Review
```

When a task introduces an architecturally significant change, architecture analysis must happen before implementation.