# Baseline system requirements

Status: normalized architectural subset, 2026-10-03. No capability below is implemented by this document.

This index predates the [BA/SA contracts](README.md) and is not an approved business or system analysis artifact. Preserve `SR-01`–`SR-15` for existing architecture/ADR traceability. Future normalization requires source-backed BR/FR/NFR, explicit owner approval and a reviewed coverage mapping; no approval or BR link is inferred from these SR entries. The questions below remain unresolved inputs and must be assessed against the new stage gates before dependent work.

Sources remain authoritative: [AGENTS.md](../../AGENTS.md), [business plan](../biznesplan-platforma-kursy-dla-dzieci.md) and [educational program template](../szablon-programu-edukacyjnego-modul-4-zajecia.md). This index adds stable references and architectural acceptance criteria; it does not supersede the sources or migrate all business requirements. Where the plan lists alternatives or examples, they remain configuration or open decisions. AGENTS.md resolves the plan's consultation priority ambiguity by including limited asynchronous consultations in MVP.

| ID | Requirement and acceptance boundary | Source | Architecture |
| --- | --- | --- | --- |
| SR-01 | Parent owns purchase and consents; child has a linked educational profile and cannot pay. Guardian relationship must be checked per resource. | Plan §§8–11; AGENTS §§21–23 | identity; [security](../architecture/security.md) |
| SR-02 | Keep module definition, published program version, scheduled group, lesson occurrence and enrollment distinct. Subject and age band are data, allowing later subjects without new commerce processes. | Plan §§5,9; template A §§1–6 | catalog, groups, lessons; [data model](../architecture/data-model.md) |
| SR-03 | Pilot learning flow: diagnosis, four lessons, homework/practice, exam, feedback, next module. Learning outcomes and assessment/retake rules belong to program versions. | Plan §5; template A §§3–10 | catalog, assignments, assessments |
| SR-04 | Purchase can precede prerequisite completion; beginning participation requires final approved completion or an audited authorized educational override. Preliminary results cannot unlock participation. | Plan §5; AGENTS §21 | groups, assessments, workflows; [contracts](../architecture/contracts.md) |
| SR-05 | First retake is free; later retakes use configurable current prices and versioned educational eligibility rules. Never globalize the example threshold, delay, duration, lesson length, prices or VAT. | Plan §§5–6; template A §§9–10; AGENTS §21 | assessments, commerce, workflows |
| SR-06 | Preserve exact published program, question, grading-criterion and assessment-rule versions used for each attempt. Support teacher approval and audited grade corrections without overwriting historical evidence. | Plan §§8–9; template A §9 | catalog, assessments, audit; [ADR-0002](../architecture/decisions/0002-owned-persistence-and-history.md) |
| SR-07 | Parent buys a place in a scheduled group; confirmed payment is verified server-side. Duplicate callbacks or delivery retries cannot duplicate payments, enrollment or entitlements. Amounts are decimal-safe and carry currency; checkout shows full gross price. | Plan §§6,9,18; AGENTS §21 | commerce, groups, workflows; [ADR-0003](../architecture/decisions/0003-durable-effects-and-payments.md) |
| SR-08 | Teachers access assigned groups and relevant data; methodologist, support, business admin and technical/audit permissions are separated. Privileged access uses MFA and audited operations. | Plan §§8–10; AGENTS §§22–23 | [ADR-0004](../architecture/decisions/0004-resource-authorization.md) |
| SR-09 | Materials and attachments use private S3-compatible storage with quotas, type/size validation, malware scanning and resource authorization. | Plan §9; AGENTS §§4,23 | files plus owning capability; [integrations](../architecture/integrations.md) |
| SR-10 | Consultations are limited, asynchronous, time-bounded and archived with authorized parent visibility. No private teacher accounts or open social chat. Scope/quota/window remain configurable product rules. | Plan §§5,10; template A §8; AGENTS §§3,21 | consultations |
| SR-11 | Parent reports combine attendance, homework/practice, diagnosis, final exam and outcome-level feedback without becoming the authority for progression. Transactional email accompanies relevant workflows. | Plan §§8–9,18; template A §13 | reporting, notifications |
| SR-12 | Evaluate mathematical answers on server with bounded safe parsing; render LaTeX-compatible notation accessibly. Do not disclose exam keys before authorized review. | Plan §9; AGENTS §24 | catalog, assignments, assessments, frontend |
| SR-13 | Record unambiguous event instants; schedules display Europe/Warsaw and handle DST. Explicitly validate ambiguous/nonexistent local times. | AGENTS §21 | [data model](../architecture/data-model.md) |
| SR-14 | Minimize child data and retention, support controlled export/deletion, protected audit and recovery. Retention periods/legal basis/provider processing agreements require confirmation rather than invented legal defaults. | Plan §§9–11,22; AGENTS §§20,23 | [security](../architecture/security.md), [NFRs](../architecture/nfr.md) |
| SR-15 | Java/Spring modular monolith, Angular/TypeScript, PostgreSQL/migrations, HTTP/JSON, single-server Docker Compose. External payments/video; no speculative distributed infrastructure. Preserve landing. | AGENTS §§4,11–15,25 | [ADRs](../architecture/README.md#decision-register) |

MVP is the scope in AGENTS.md §3. The plan's premium products, marketplace, native apps, public social features, AI, SMS, coupons and advanced analytics do not become baseline delivery requirements. They may inform extensible identifiers, not implementation work.

## Decisions still needed

| Question | Owner | Must be resolved before |
| --- | --- | --- |
| Exact pilot class, group min/max, lesson duration, absence/cancellation rules, seat reservation expiry and paid-place validity | Product + education | Catalog/group/checkout implementation |
| Published passing/outcome criteria, grading authority, appeal/correction handling and retake eligibility windows | Methodologist + product | Publish a program; assessment implementation |
| Consultation quota, response expectation, archive/access duration and moderation permissions | Product + safeguarding | Consultation implementation |
| Parent verification, child login/recovery and guardian relationship lifecycle | Product + security | Authentication implementation; [ADR-0006](../architecture/decisions/0006-authentication-options.md) |
| Identity/payment/video/email/storage/scanner providers and EU/EEA processing constraints | Product + security + operations | Integrations and authentication |
| Retention/legal holds, export/deletion process, recording policy, VAT and sales documentation, refunds | Product + legal/accounting | Data retention and live sales; no legal/tax determination is made here |
| Capacity envelope, latency/availability targets, RPO/RTO and backup retention | Product + operations | Production readiness |
| Compatible supported Java/Spring and Angular/Node versions, migration/build/math libraries | Implementation + architect for major dependencies | Application bootstrap; verify against then-current official sources |
