# Integration boundaries

Providers are unselected and integrations unimplemented. Preserve [ADR-0003](decisions/0003-durable-effects-and-payments.md) durable payment/delivery principles and [ADR-0005](decisions/0005-runtime-and-api-boundary.md) topology. [ADR-0008](decisions/0008-approved-requirement-impact.md) proposes removing retake fulfillment only. Owner ports/public models remain provider-neutral.

| Owner / integration | Purpose and minimum data | Trust and failure boundary |
| --- | --- | --- |
| commerce / payments | Hosted checkout, verified payment/refund status; original order reference, decimal amount, PLN and necessary guardian billing data; no platform card processing | Secret credentials; signed callback/authenticated server verification; validate merchant/order/payment/amount/currency; bounded timeouts, stable operation keys and reconciliation; browser return is status only |
| lessons / video | Authorized meeting information and minimal group/teacher display data | Approved manually entered link can satisfy MVP; no mandatory meeting-creation API/recording. Repair is scoped/audited; failure preventing lesson creates rescheduling coordination |
| notifications / email | Transactional template, approved guardian recipient and minimal variables | Durable intent with preparation/send/failure status; provider verification if callback used; sending does not prove reading and cannot undo payment/enrollment/schedule |
| files / S3 | Private material/attachment bytes and opaque metadata | Least-privilege server credentials, private bucket/encryption, bounded/checksummed operations and matching recoverable inventory; owner access and clean scan before disclosure |
| files / malware scan | Quarantined bytes and scan evidence, no profile data | Restricted execution/service identity; bounded work, fail closed on unavailable/failed scan; scanner choice does not mandate a new distributed service |
| identity / credential authority | Subject, assurance/MFA and necessary metadata | Pending ADR-0006; if external, verify issuer/audience/signature/flow and map local grants; must support independent child login/guardian recovery without mandatory child email/phone |

Provider selection requires security/operations assessment of the specified flows and processing constraints, favoring EU/EEA storage where feasible. This stage chooses neither vendors nor current library/runtime versions.

## Durable outbound operations

Owner-local PostgreSQL records retain intent, aggregate/request identity, claim lease, attempt count, next-attempt time and safe outcome. Producing mutation plus outgoing intent is atomic. Workers claim through public APIs, recover abandoned claims and perform network calls outside business transactions. A lease is not successful delivery; persist local/provider outcome before acknowledgment.

NFR-010 requires an immediate initial attempt, then safe retries after approximately 1, 5 and 15 minutes, ending in visible manual/error handling. Do not choose whether those intervals are cumulative or between attempts: SA-Q-009 assigns precise reference points/tolerances to the requirements owner before operational configuration acceptance. Do not auto-retry an operation without safe idempotency. Manual replay uses the same key, scoped authority, reason and audit; unknown outcomes stay uncertain until checked.

Configure bounded provider timeouts from actual provider limits. NFR-008 requires critical alerts for three consecutive critical-integration failures; final retry exhaustion remains an independently visible error. Remaining alert baseline/window/significant-growth thresholds require SA-Q-009, not guessed defaults.

Local exactly-once effects do not promise exactly-once email delivery. Where an email provider lacks safe idempotency after an uncertain result, hold for reconciliation/manual handling rather than blindly resend.

## Payment and service recovery

Unique provider/merchant/event identity plus payment identity and state prevent duplicate settlement. Fulfillment deduplicates original order-line enrollment effects, commits notification intent and consumed delivery marker atomically. Valid late payment remains attached to its original order; available original capacity may be acquired, otherwise paid fulfillment remains unresolved. Guardian must explicitly accept alternative group/edition or receive the defined full-refund resolution; silence cannot transfer enrollment.

Refund request reserves remaining amount and persists a stable key before dispatch; pending/uncertain requests consume reserved balance. Provider success, not request submission, records a successful refund. Reconcile callbacks/provider queries before replay after crashes or restore; final failure releases reserved amount. Purchased settlement-plan values or an authorized audited manual decision supply amounts. No retake payment/refund integration is introduced.

S3 reconciliation detects incomplete/orphaned objects without granting unchecked files. Scanner/type validation follows NFR-007 formats/20 MB/five-file limit. Storage recovery must align metadata, object versions and assessment/audit evidence. Credential failure fails closed; video-provider failure is distinguished from failure to publish join information in eSzkola.

Future sandbox/contract checks cover forged/wrong-merchant callbacks, wrong amount/currency, duplicates/reordering, parallel refunds, uncertain creation/refund outcomes, retry exhaustion, orphan uploads, scan outage and authorized link repair. No broker, Redis or distributed transaction is proposed.
