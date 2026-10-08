# Security and privacy boundaries

Target-only; no product authentication/security implementation exists. Preserve [ADR-0004](decisions/0004-resource-authorization.md). [ADR-0006](decisions/0006-authentication-options.md) remains Proposed for credential authority/session implementation. Approved FR-001/FR-014/FR-015/FR-019/FR-020 and NFR-001/NFR-007/NFR-008 define the current business/security behavior.

## Authentication, guardians and recovery

Backend creates verified actor/assurance context and maps external subjects, if selected, to local accounts/grants. Provider claims never grant unlimited local authority. ADR-0006 recommends same-origin Secure/HttpOnly/SameSite session cookies with CSRF protection, rotation, expiry/revocation and PostgreSQL persistence if needed; no credential mechanism/provider is selected here. Do not implement both options or store secrets/tokens in browser localStorage.

Child has independent educational login without mandatory email/phone, created/reset by an authorized guardian. Verified administration can recover it with audit. Child context cannot purchase, manage guardian relations/adult consents, change billing or acquire guardian authority through recovery/switching.

Main guardian is established by verified assignment; only main guardian invites a named additional guardian, who accepts through their own account. Additional guardians cannot delegate. Removal blocks subsequent child-resource access and preserves history. Main replacement needs current main consent or verified audited administrator decision; disputes/loss of all access require controlled manual administration, never automatic family-law adjudication. Serialize changes per child and recheck authoritative relation versions during mutations.

MFA is mandatory for teachers, methodologists, support, administrators and product Business Owner accounts. It is optional for guardians in MVP and not mandatory for children. A privileged operation checks current grants, scope and assurance. Recovery uses a previously generated code or additional identity verification by authorized administration; administrators cannot approve their own MFA recovery. Reset invalidates old configuration, requires new setup and appends audit; session invalidation is supported. Recovery must not provide a lower-assurance privileged bypass.

## Resource matrix

| Actor | Allowed authority | Denied implicit authority |
| --- | --- | --- |
| Guardian | Active related child schedules/materials/results/reports/consultations, authorized purchases/consents and child recovery | Other children; automatic visibility into another purchaser's unrelated financial data; additional-guardian delegation |
| Child | Own authorized educational resources | Purchase/billing, adult consents, guardian management, other children or pre-review exam keys |
| Teacher | Assigned/explicitly shared programs/groups, relevant learners, grading, consultations and authoring | Unrelated child/group data, unnecessary billing data; authorship is not required for assigned-teacher progression exception |
| Methodologist | Scoped content/criteria and quality evidence | Role alone cannot grant progression exception, refunds, purchases, guardian management or full child access |
| Support | Minimum case data and preparation of operations | No dispute-based guardian grant, final grade change or progression override without a distinct authorized grant |
| Administrator | Explicit granted participation/commerce/guardian/incident/moderation actions | No global bypass, automatic grade authority or self-approved MFA recovery |
| Business Owner | Explicit business authority including audited progression exception and terms qualification | BA/SA approval is external governance, not a product endpoint |
| Technical operator/auditor | Private operational health or restricted audit purpose | Unrestricted child-content browsing or impersonation |

Owners check every list/detail/query/command/export, nested ID, file and archive. Revoked relations/assignments must fail subsequent operations; UI state and stale cached grants are insufficient. Counts/pagination must not enumerate inaccessible children. Named internal workflow authority carries original actor/event and grants only its operation.

## File and content boundary

Owner-authorized upload intent binds actor/resource and generated opaque object key. Allowed attachments: PDF, JPG/JPEG, PNG, WEBP, DOCX; at most 20 MB per file and five files per submission/message. Owner checks batch count and files checks extension, declared MIME, actual type/magic bytes, bytes/size and malware. DOCX is an explicitly allowed document format; that does not admit generic ZIP/archive uploads or arbitrary embedded active content.

Quarantine/scan-pending/rejected states are not downloadable by other users. Scanner failure fails closed. Private buckets and least-privilege server access remain mandatory. Short-lived URLs or proxied bytes require owner authorization, clean scan and content disposition; URL tokens are redacted. Recheck resource scope before issuing each operation. Safe retention determines archive lifetime.

Free text uses output escaping/restricted markup. Mathematical answers use bounded safe server parsing/evaluation, never arbitrary execution. Learner DTOs omit answer keys/private rubrics until authorized review. Rate-limit login, recovery, uploads, checkout, submission and consultation sends; unspecified operational thresholds must be set during concrete design, not invented as business policy.

## Audit and lifecycle

Required audit and privileged mutation share one transaction. Include grades/reviews/corrections, progression exceptions, permissions/guardian changes, recovery, refund/manual decisions, sensitive administration, moderation and appropriate exports. Retain actor, resource, time, decision, prior revision and required reason without secrets or full child-message bodies. Restrict reads and mutation/deletion capabilities; approved retention processing itself is privileged/audited.

Default diagnostic retention is 30 days under NFR-008 unless an approved policy changes it. Business/security audit has separate retention and is not automatically purged after 30 days. Exclude passwords, secrets, tokens, card data and sensitive child content from logs, metrics and email subjects. Prefer authenticated links over emailing full child results.

No public child profiles, open contact or private teacher accounts. Consultations are archived with active authorized-guardian visibility. No default recording; recording needs separately approved purpose, basis, access and retention. Teacher readiness records approved checks/training with minimal restricted evidence. Consent/declaration versions retain person/time; lawful bases, retention, rights procedures, contracts, safeguards and final teacher checks remain SA-Q-010 production gates.

Trust only configured proxy sources for forwarded headers. Exact verified payment webhook route has provider authentication; other mutations must not inherit its CSRF exception. Database, health and metrics remain private. Independent security/architecture review and actor/resource negative tests are required after implementation.
