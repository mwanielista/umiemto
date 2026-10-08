# Logical data model and ownership

Target-only logical model; no physical schema or migration exists. Preserve [ADR-0002](decisions/0002-owned-persistence-and-history.md). The requirement-impact changes in [ADR-0008](decisions/0008-approved-requirement-impact.md) are Proposed. [model.json](model.json) records exactly one owner per entity.

## Ownership

| Owner | Logical persistent data |
| --- | --- |
| identity | ActorAccount, ParentProfile, ChildProfile, TeacherProfile, GuardianRelationship, ConsentRecord, RoleGrant, AuthenticationState, GuardianInvitation, TeacherReadinessRecord |
| catalog | Subject, AgeBand, LearningPath, ModuleDefinition, ProgramVersion, LessonPlan, LearningOutcome, AssessmentPolicyVersion, QuestionVersion, GradingCriteriaVersion, ProgramMaterial |
| groups | ScheduledGroup, TeacherAssignment, SeatReservation, Enrollment, AdministrativeCase |
| lessons | LessonOccurrence, MeetingReference, Attendance, LessonMaterial, LessonChangeDecision |
| assignments | Assignment, Submission, PracticeAttempt, HintUsage, AssignmentFeedback |
| assessments | DiagnosticAttempt, ExamAttempt, AttemptQuestionSnapshot, GradingDecision, ModuleCompletion, ProgressionOverride |
| consultations | ConsultationThread, ConsultationMessage, ConsultationPolicyVersion, ConsultationWeekUsage |
| commerce | PriceConfiguration, Order, OrderLineSnapshot, Payment, Refund, ProviderCallback, CommerceDelivery, OfferVersion, SettlementPlanVersion, PurchasedTermsChange, RefundDecision, SalesDocument |
| reporting | ProgressReportSnapshot, ContinuationQualification, SatisfactionSurvey, KpiReportSnapshot |
| files | FileObject, FileScan |
| notifications | NotificationIntent, EmailDelivery |
| audit | AuditEvent |
| workflows | No business persistence. Coordinates through owning contracts. |

## Versioned service and education

Definition, immutable published ProgramVersion, OfferVersion, ScheduledGroup, LessonOccurrence and Enrollment remain distinct. A program carries its configurable structure, required elements, target group, outcomes, optional diagnosis/exam, entry requirements, completion/progression conditions, access periods and free-retake eligibility. OfferVersion supplies commercial/access terms and references the published program. No global four-lesson count, class, group size, 75% threshold or 90-day material period exists.

Groups and enrollments pin the delivered program. Orders snapshot purchased gross/net/tax treatment, PLN, quantity, offer/program/group references, material/consultation periods, reservation and applicable terms. An optional immutable SettlementPlanVersion assigns decimal gross values to service elements; their sum equals the gross purchased service price. Program publication does not retroactively rewrite purchased terms.

Attempts pin exact program, question, rubric/criteria and assessment-rule versions, selected order/randomization, allowed time, deadline and accommodations. Question content/keys remain catalog-owned; answers and grading remain assessments-owned. Referenced versions cannot be edited/deleted. Assignment/practice evidence likewise retains its content references. Corrections append grading decisions and audit, retaining previous result and reason; reports are revised, not treated as authority.

ModuleCompletion represents completion of a versioned program/stage even without an exam. Required-element evidence is checked against the pinned completion policy; completion does not imply mastery of all outcomes. Preliminary or incident-review results cannot satisfy a final-result prerequisite. No prerequisite means no previous-stage gate. Authorized exceptions belong to assessments and retain actor, participant, scope, time and reason; groups records the activation evidence.

RetakeEntitlement is removed from the candidate model. All later attempts remain educational, free of order/payment requirements; assessments owns eligibility and attempt ordinal. Program rules can limit availability/attempt count without charging. Removal is a Proposed partial supersession of ADR-0003, not deletion of an implemented table.

## Identity and guardian history

GuardianRelationship contains child, guardian, main/additional role, activity and versioned grant/revocation/change evidence. Serialize changes per child; enforce at most one active main guardian while allowing the documented loss-of-all-access recovery state. Invitations bind a named account/person and child, require acceptance by that account and cannot be accepted/replayed to grant another person access.

Only main guardians invite/remove additional guardians; replacing the main guardian requires current main consent or verified audited administrator decision. A dispute flag can suspend changes pending manual resolution. Revocation preserves consent/audit evidence and blocks subsequent child-resource operations. Child login is independent, requires no child email/phone and is created/reset by authorized guardian or verified audited administration. AuthenticationState remains credential-authority-neutral pending ADR-0006.

ConsentRecord binds version, purpose, actor, time and state. TeacherReadinessRecord stores minimal approved verification/training status, restricted evidence references and audit; details depend on the production policy.

## Consistency and concurrency

One PostgreSQL database uses owner-prefixed tables and globally ordered versioned migrations. Owners alone access persistence. Cross-owner references are opaque IDs/public-contract checks; foreign keys can protect immutable references but must not enable cross-owner access or cascading history deletion.

Local transactions cover reservation plus order, payment evidence/state plus delivery intent, enrollment fulfillment plus delivery acknowledgment/notification intent, prerequisite plus participation, final grade/completion plus audit, guardian changes plus audit and consultation quota plus thread creation. External calls never hold business row locks.

Reservations expire no later than 24 hours after creation; shorter configured windows are valid. Groups serializes remaining capacity. Late payment remains bound to the original order: reacquire an available original seat atomically or retain paid/unresolved fulfillment. An alternative needs recorded guardian acceptance; silence does not move the child.

Commerce serializes refunds on payment/order: reserve amounts for pending/uncertain requests in addition to accounting for successful refunds, so parallel calls cannot over-refund. Provider idempotency keys and evidence distinguish requested, pending, uncertain, successful and failed refunds. Only definitive failure releases the pending amount. Actual successful refunds never exceed verified paid value. PurchasedTermsChange records qualification by authorized administration/Business Owner, exact change, guardian acceptance or unresolved status. Missing settlement plan requires an audited manual RefundDecision with amount, currency, basis, actor, time and reason; no invented proportion.

Database uniqueness protects callback provider/merchant/event identity, provider payment identity, order-line fulfillment, notification intent, attempt request/ordinal, guardian invitation acceptance, survey per completed enrollment and continuation qualification. Enrollment-history/reenrollment keys require concrete feature policy; never overwrite history to achieve deduplication. Stable lock ordering and optimistic revision checks accompany implementation.

ConsultationWeekUsage keys enrollment/program consultation scope plus Warsaw-local Monday date, independent of author. Insert/check quota and create thread atomically. One new thread per week is shared by child and all guardians, with no carryover; replies do not consume it. Store opened/replied/closed times and the calendar basis for the two-working-day response objective, excluding Polish statutory holidays.

## Delivery, reporting and time

LessonOccurrence retains a stable service-occurrence lineage across rescheduling, realized/cancelled status and substitutions. Attendance uses that lineage once; organizer-cancelled unrealized lessons are excluded from its denominator. LessonChangeDecision records scope, actor, reason and terms-change reference where applicable. AdministrativeCase records organizational case status and references decisions in their authoritative owners.

Reporting uses authorized owner queries. Source facts carry source revision/time; generated reports/qualifications retain cohort and source identities. A continuation qualification key is purchasing guardian + child + completed enrollment + logical continuation. Its start is the later completion/purchase-availability date; repeated availability does not create a new qualification. A survey pins the main guardian at completion, with one response per completed enrollment despite later guardian changes.

Significant times use unambiguous instants/offsets; schedule authoring retains Europe/Warsaw local intent and resolves DST gaps/overlaps explicitly. Consultation weeks and KPI day boundaries use that zone. File metadata retains resource binding, bytes/type/scan status and approved lifecycle. Business and security audit retention is separate from the default 30-day technical diagnostics.

Configurable, approved retention/export/deletion calls each owner. Profile deletion cannot indiscriminately cascade payments, attempts or audit. Required evidence is minimized/pseudonymized under policy; backup/object versions are included. No unapproved legal basis or retention period is introduced.
