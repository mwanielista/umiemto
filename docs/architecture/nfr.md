# Quality objectives and evidence

Target requirements, not verified application performance. Consumed source: approved SA revision 3, with exact BA/SA approval identities in [handoff](implementation-handoff.md). Existing SR-01–SR-15 are retained historical traceability, not substitutes for approved NFRs.

| Requirement | Target scenario / objective | Evidence and owner |
| --- | --- | --- |
| NFR-001 | Direct foreign/revoked resource requests deny. MFA mandatory for teacher, methodologist, support, admin and product Business Owner; optional guardian, not mandatory child. Recovery cannot self-approve administrator MFA and must invalidate old setup, require new setup and audit | Actor/resource/assurance negative integration tests, recovery and audit-rollback evidence; backend/security/QA |
| NFR-002 | Decimal-safe money with currency, PLN purchase, verified provider authority, one payment/enrollment effect, no over-refund under duplicate/parallel/uncertain requests | Real PostgreSQL concurrency/crash tests and provider sandbox; commerce/groups/QA |
| NFR-003 | 99.5% monthly availability for controlled login, catalog, purchase/enrollment, family and teacher workflows, schedule/join information, materials/submissions, results/reports/progression and consultations | Per-process synthetic checks and monthly numerator/denominator evidence; operations |
| NFR-004 | RPO ≤24 hours; RTO ≤4 hours including 15 continuous healthy minutes; complete database/object/history recovery | Isolated measured restore and post-restore consistency/process checks; operations/QA |
| NFR-005 | ≥100 active families and ≥10 overlapping live occurrences; concurrent login, panels, schedules, materials, work, results and basic administration; typical synchronous backend p95 ≤2s, p99 ≤5s, technical errors <1% | Representative load profile on intended topology, percentile/error evidence; QA/operations/backend |
| NFR-006 | Design objective WCAG 2.2 AA, including mathematical content, keyboard/focus/labels/contrast/errors/resizing/mobile | Manual and automated criterion-based report, not automated certification; frontend/QA |
| NFR-007 | PDF/JPG/JPEG/PNG/WEBP/DOCX, ≤20 MB/file, ≤5 files/submission/message; extension/MIME/magic/size/malware/resource checks; failed/pending scans remain inaccessible; safe server math | Boundary/spoofing/malware/outage/access tests and bounded parser tests; files/security/QA |
| NFR-008 | Redacted restricted diagnostics, default 30-day diagnostic retention, separate approved audit retention; actionable critical alerts | Secret/log leakage, rotation, retention separation and fault-injection evidence; operations/security |
| NFR-009 | Unambiguous event times, Europe/Warsaw schedule/week/KPI boundaries and explicit DST disambiguation | DST gap/overlap/week/day and event-order tests; backend/frontend/QA |
| NFR-010 | Immediate attempt then safe retries approximately 1/5/15 minutes; bounded exhaustion/manual status; unsafe operations not blindly replayed | Durable attempt/lease/restart/uncertain-result tests with provider evidence; integration owners/QA |

## Availability and recovery measurement

A minute is unavailable for a controlled critical process if two consecutive synthetic attempts within that minute fail, or application evidence proves a blocking fault. Partial outage counts when the basic process cannot complete, even if other routes respond. Exclude maintenance only when users received notice ≥24 hours beforehand. Monthly evidence retains covered time, valid exclusions, unavailable time, affected process and source; available share is measured over covered time minus valid exclusions.

External video outage alone is not eSzkola outage; missing eSzkola join information is. Payment/login/storage dependency failure counts when it blocks a covered platform process; do not remove it merely because the provider is external.

RTO starts at the earlier automatic detection or authorized manual confirmation of critical failure, and ends only after restored affected processes pass checks for ≥15 consecutive minutes. All of that interval must fit four hours. RPO compares the last durable pre-failure business state with the newest recoverable state and must fit 24 hours.

Restore covers accounts/relations, programs/versions, offers/groups/schedules, enrollments, orders/payments/refunds, consent/declarations, homework/submissions/attempts/results, consultations, service files and protected audit. Starting containers alone is not successful recovery.

## Workload and operational interpretation

An active family is counted once regardless of children/programs when at least one child has active ongoing or paid enrollment whose service period includes the measured month. Ten simultaneous lessons means ten overlapping live occurrences, not ten attendees; media is external. The load report states actual simultaneous operations, dataset and transaction mix; number of families is not automatically concurrent sessions.

Long-running reports/integrations may exceed two seconds but must acknowledge accepted work unambiguously. Development toward approximately 10,000 families/200 overlapping occurrences is a domain-evolution target, not pilot load acceptance or justification for new distributed services. Single-server architecture is a failure domain; its availability/recovery targets require measured evidence and prepared replacement capacity.

Critical alerts include five consecutive minutes of basic-process outage, three consecutive failed critical integration attempts, permanent business-data read/write failure and significant growth in authorization/payment/file errors. Thresholds are operational configuration. SA-Q-009 still owns the exact significant-growth baseline/window and retry reference/tolerances before operational acceptance.

FR-013's two-working-day response objective uses Monday–Friday excluding Polish statutory holidays, measured from thread creation. This is a teacher/service objective, distinct from backend latency. FR-024 KPI targets are pilot goals (completion ≥70%, continuation ≥60%, attendance ≥80%, satisfaction ≥4.2/5), not guaranteed educational results.

Maintainability additionally requires model/compiled DAG, owner-only persistence, private-layer boundaries and independent architecture review. Historical-version edit, preliminary-result, configured-progression and free-retake checks remain mandatory despite not being numeric NFRs.
