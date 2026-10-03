# Requirements-to-implementation workflow

[AGENTS.md](AGENTS.md) is the repository constitution. This workflow uses the current directory structure and defines manual stage gates; it does not register agents or provide an automated pipeline.

```text
Business input
    ↓ Business Analyst
Business requirements (BR) + review and explicit approval
    ↓ System Analyst
System requirements (FR/NFR) + review and explicit approval
    ↓ Architect
ADRs + architecture + contracts + executable constraints where practical
    ↓ Planner (future role)
Implementation DAG, tasks tracing to FR/NFR
    ↓ Developers (backend / frontend / infrastructure)
Implementation + tests
    ↓ QA + independent architecture reviewer (read-only)
Verified behavior + architecture compliance
```

## Stage ownership and gates

| Stage | Owns | Progression gate |
| --- | --- | --- |
| BA | Business goals, actors, processes, BRs, rules, glossary and questions | Complete source-backed artifact, no unresolved blockers, explicit business-owner approval of exact revision |
| SA | FR/NFR, use cases, concepts, data/integration requirements, security and failure scenarios | Approved BA revision, every FR/NFR traces to BR IDs, no unresolved blockers, explicit requirements-owner approval of exact SA revision |
| Architect | Boundaries, ownership, contracts, ADRs and fitness functions | Approved system requirements, relevant uncertainties resolved, architecture and constraints documented |
| Planner (future) | Tasks, dependencies and acceptance checks | Approved requirements and architecture; every task traces to FR/NFR; acyclic task dependencies |
| Developers | Requested features within these boundaries | Relevant tests/checks pass; changes and unverified areas documented |
| QA / architecture reviewer | Behavior / independent architecture compliance | Reviewer reports compliance or required changes; implementer fixes, reviewer reviews again |

BA is not SA; SA is not Architect; Architect is not Developer. BA and SA never generate implementation tasks. Existing technical mandates in AGENTS.md remain binding; analysts cite them without making new technology choices. Planner is a future responsibility, not an agent claimed to exist today.

Missing or contradictory information becomes an open question with an owner and affected scope. Unresolved `BLOCKER` questions set analysis to `BLOCKED` and stop the dependent stage. Non-blocking questions require justification that uncertainty does not prevent progression. Assumptions cannot replace missing business decisions. Approval belongs to a designated human owner; agents must not fabricate it. A changed approved revision requires downstream impact review and renewed approval.

## Run BA then SA manually

Read [requirements contracts](docs/requirements/README.md). Role prompts explicitly load the relevant documents rather than assuming nested instructions activate a role for a task started at repository root.

```text
Read AGENTS.md, workflow.md, docs/requirements/business-analyst.md and
docs/requirements/README.md. Act as Business Analyst on
docs/biznesplan-platforma-kursy-dla-dzieci.md and
docs/szablon-programu-edukacyjnego-modul-4-zajecia.md.
Produce docs/requirements/business-analysis.yaml as a draft or blocked
artifact. Cite sources, distinguish examples from requirements, and raise
questions. Do not approve the artifact, design architecture or tasks.
```

After actual business-owner approval of the exact BA revision:

```text
Read AGENTS.md, workflow.md, docs/requirements/system-analyst.md and
docs/requirements/README.md. Verify the approval and revision of
docs/requirements/business-analysis.yaml. If the gate passes, act as
System Analyst and produce docs/requirements/system-analysis.yaml.
Trace every FR/NFR to BR IDs. Do not change BA, choose technologies,
design final architecture, create tasks or approve your own output.
```

The current [baseline](docs/requirements/baseline.md) is an architectural subset with stable `SR-01`–`SR-15` references, not approved BA/SA output. Preserve its references and Accepted ADRs. Future normalization requires reviewed coverage mapping to BR/FR/NFR, not inferred approvals. The [existing checker](docs/architecture/README.md#checks-available-now) verifies target model/document coherence; BA/SA contract and approval checks remain manual until an executable validator exists.
