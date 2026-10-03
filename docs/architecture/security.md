# Security and privacy boundaries

Target-only; no security implementation exists. [ADR-0004](decisions/0004-resource-authorization.md) fixes authorization requirements; [ADR-0006](decisions/0006-authentication-options.md) leaves authentication selection Proposed.

## Authentication and session boundary

Backend verifies the credential authority's identity and assurance and creates a trusted actor context. External identity subjects are mapped to local accounts; identity provider roles cannot silently grant local educational/admin authority. Recommended browser boundary is a server-managed session with Secure/HttpOnly/SameSite cookie, rotation, expiration/revocation and CSRF validation. Tokens/secrets never go to browser localStorage or logs. If selected, persist sessions in PostgreSQL to avoid an extra service. Exact credential/password/MFA/recovery implementation awaits ADR-0006 resolution; do not implement both options speculatively.

MFA is a requirement for teachers, methodologists, admins and other privileged actors. A privileged operation checks session assurance and current grants; a lower-assurance login cannot exercise these privileges. Identity/account recovery must not bypass MFA or let a child obtain guardian authority. Parent consent/profile authorization is separate from authentication. Parent-child switching must produce a restricted learner context, never retain purchasing power in the child UI/session context.

## Resource authorization matrix

| Actor | Allowed scope | Explicit boundary |
| --- | --- | --- |
| Parent/guardian | Currently authorized children, their schedules/reports/consultations, own purchases | No access to other guardians' children/orders; managing linked profile requires current grant and required consents |
| Child | Own educational resources and active eligible participation | No purchases, other children, teacher private notes, admin functions or pre-review exam keys |
| Teacher | Assigned groups, relevant learners/submissions/attempts and scoped consultations | No unrelated groups, broad commerce data or guardian administrative authority |
| Methodologist | Program authoring/publishing, assessment oversight and scoped educational exception/correction | Educational permission does not imply payment or identity administration; child-data scope explicit |
| Support | Assigned operational case and minimum relevant contact/order/group data | No implicit answer-key, grade-change or complete child transcript access |
| Business administrator | Granted group/payment/content operations | Grade/permission changes need separate grants; sensitive changes audited |
| Technical operator/auditor | Infrastructure/health or restricted audit purpose | No default unrestricted application impersonation or child-content browsing |

Resource owners authorize on every query and command, including lists, nested IDs, exports, attachments and archived data. Pagination/counts must not leak unauthorized resources. Recheck guardian/teacher revocation and enrollment state rather than assuming old browser grants are current. Negative integration tests cover identifier swapping, role elevation, stale assignments and nested resources. Admin roles are not a universal bypass. Any exceptional operational access needs purpose, scope, expiry and audit according to an approved workflow.

## Files and free text

Upload uses an owner-authorized intent bound to resource and actor. Server limits size/type/count, generates object keys, validates MIME/content and quarantines until malware scanning passes. Expired, oversized, spoofed or failed/unavailable scans stay inaccessible. Storage operations are private; short-lived URLs are issued only after owner authorization and clean scan, with careful content disposition and no predictable bucket/key enumeration. File access logs redact URL secrets. Scanner choice and limits are open implementation inputs; do not make a file downloadable before the pipeline exists.

Render submitted text/math with output escaping and restricted markup; mathematical evaluation uses bounded grammar/resources, never arbitrary execution. Rate-limit authentication, uploads, checkout, submissions and consultation sends; exact quotas require capacity/product choices. Exam delivery uses a learner DTO without keys or private rubrics. Teacher/private notes need explicit visibility, not generic report serialization.

## Audit, privacy and lifecycle

Privileged mutation plus audit append share a transaction; failure to record required audit fails the mutation. Grade changes, progression overrides, permission changes, refunds, sensitive exports/admin actions and consultation moderation have actor/reason/time/resource/revision evidence. Runtime logs are not the audit trail. Restrict audit reads; application credentials must not support arbitrary mutation/deletion of audit history. Retention processing is a separate privileged operation with evidence, not perpetual retention by default.

Collect only justified child/profile data; do not presume full birth date, address or medical details are needed. Keep passwords/tokens/card data/child message bodies out of logs, metric labels and email subject lines. Prefer email linking to an authenticated report over sending full child results. Encrypt transmission, protect stored sensitive data and backups, and keep secrets outside Git. Legal basis, retention schedules, guardian verification and processing agreements require review by the appropriate owners; this architecture does not certify legal compliance.

Consultation scope/quota/window is enforced on the server, archived access is authorized, and edits/moderation cannot erase history without audit. Do not direct children to personal teacher contact accounts. Recording lessons is not required by baseline; any later recording workflow needs purpose, access, retention and approved basis before integration.

External providers are untrusted until verified; only trusted proxy addresses may supply forwarded identity/IP headers. Payment exceptions from CSRF protection apply only to the exact verified webhook route. Health/metrics endpoints and database ports remain private. Logs centralize on the initial server with rotation and off-host recovery evidence, without requiring a new observability service.
