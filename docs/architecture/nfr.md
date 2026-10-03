# Relevant quality scenarios

Requirements derive from [baseline requirements](../requirements/baseline.md), business-plan §§9–12,15,22 and AGENTS.md §§20–25. This baseline defines testable scenarios; numeric service objectives must be agreed before production, not copied from marketing scenarios or the mathematics example.

| Attribute | Scenario / required behavior | Evidence and owner |
| --- | --- | --- |
| Isolation/security | An actor substitutes another child's/group's/order's/file's ID or uses a revoked assignment | All relevant list/detail/mutation/export routes deny; negative authorization integration tests, backend + QA |
| Privileged access | A teacher/admin attempts sensitive action without required assurance or scope | Server enforces MFA/grants and records successful privileged mutation transactionally, security + QA |
| Historical integrity | Methodologist publishes revised questions/thresholds after an exam | Prior pinned attempt and result reproduce identically; new attempt uses deliberate version, backend + education |
| Progression | Parent purchases early; an exam is pending manual review | Purchase allowed according to product availability; participation blocked until approved completion or audited exception, backend + QA |
| Payment reliability | Provider retries/reorders callback; process crashes during fulfillment | One paid transition and one effect per order line; durable retry/reconciliation, commerce + QA |
| Concurrent capacity | Two checkouts compete for the last group seat | Database-serialized capacity prevents overselling; expired reservation and late settlement have explicit recoverable path, groups + QA |
| Files/privacy | Malicious/oversized/unchecked file or direct key request | Rejected/quarantined, no unauthorized download, limits and scan-failure tests, files + security |
| Recoverability | Host/disk loss | Off-server database/object recovery reconciles paid effects and preserves assessment/audit; measured RPO/RTO within agreed targets, operations |
| Availability | Mail/video/payment provider slow or unavailable | Bounded calls, independent durable retries and safe status; no prolonged business row locks or false payment confirmations, integration owners |
| Accessibility/usability | Child uses keyboard/tablet/mobile and mathematical content | Clear next action, labels/errors/contrast, keyboard and screen-reader math checks; aim WCAG 2.2 AA, frontend + QA |
| Observability | Delivery repeatedly fails or migration/readiness breaks | Redacted correlation-based logs, metrics and actionable alerts; no child content/token leaks, operations |
| Maintainability | A module imports another module's persistence or creates a cycle | Model and compiled architecture checks reject it; explicit public APIs, backend |
| Time correctness | Scheduling crosses Warsaw DST change | Display/resolve exact intended instant; explicit gap/overlap handling, backend/frontend + QA |
| Performance/cost | Enrollment peak and exam submission burst | Measure agreed workload envelope and response targets on pilot topology before larger recruitment; avoid extra infrastructure without evidence, QA + operations |

Open objectives: expected concurrent learners/checkouts/exams, submission/file budgets, p95 latency, uptime/service window, retry response times, RPO/RTO and alert owner/response expectations. The plan's consultation/grading response examples remain product SLAs to agree. Single-server deployment accepts a single-server failure domain and recovery downtime; it does not promise high availability.
