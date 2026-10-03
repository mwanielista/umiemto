# Baseline design principles

[AGENTS.md](../../AGENTS.md) defines repository-wide principles. This page records their application to the baseline rather than duplicating that policy.

1. Capabilities own rules and data. `workflows` composes cross-capability use cases; it does not become a second commerce or assessment domain. Public DTOs and IDs cross boundaries, never repositories or persistence entities.
2. Purchase, payment, enrollment and participation are distinct states. Paid access can await prerequisites. Final assessment decisions drive progression; reports only present them.
3. Published educational content is historical evidence. Edit by new version; pin delivery and attempts to exact versions. Program policies vary by subject and age band.
4. Use one process/database to obtain local atomicity where needed; do not make network calls inside business transactions. Durable PostgreSQL delivery handles provider latency/retry without a broker.
5. Resource owners authorize operations using verified identity plus current guardian/group/assignment relations. Privileged roles do not imply unrestricted access to children.
6. Choose exact supported framework versions at bootstrap. Baseline architecture does not install frameworks, choose providers, or infer legal/tax defaults.
7. Automate what can be proven today (model/ownership/document consistency); add compiled dependency, security, migration and contract checks with implementation.
