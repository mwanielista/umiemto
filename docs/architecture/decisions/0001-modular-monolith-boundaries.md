# ADR-0001: Capability-oriented modular monolith

## Status
Accepted — 2026-10-03. Target decision; not implemented.

## Context
SR-01–SR-15 require coupled learning/commerce flows for a small pilot. Only a static landing exists. AGENTS.md fixes Java/Spring Boot and a modular monolith; no previous ADR exists.

## Problem
Establish module ownership and dependency direction without turning a shared database/process into unrestricted coupling.

## Constraints
One deployable, explicit public contracts, no cross-module persistence access or cycles; no extra MVP features.

## Considered options
Capability modules with direct bidirectional coordination would create groups/assessment and groups/commerce cycles. Capability modules with a top-level coordinator preserve owner rules and acyclic imports. A global controller/service/repository hierarchy obscures capability ownership. Microservices conflict with current constraints and have no justified distribution need.

## Decision
Use the modules and allowed imports in [model.json](../model.json). `workflows` composes checkout, paid fulfillment, progression and retake use cases through public contracts. Capabilities own business state/rules; supporting files/audit/notifications are in-process modules. Cross-module imports use `pl.eszkola.<owner>.api` only. [Components](../components.md) defines backend and Angular boundaries.

## Rationale
Keeps coordination explicit while retaining one-process transactions and a small operational footprint. Subject/age configuration does not require rebuilding commerce or learning modules.

## Consequences
Cross-capability use cases need deliberate contracts and coordination; public contract DTOs must remain independent of entities/internal layers. The dependency allowlist is permission, not mandatory coupling.

## Risks
Workflow coordinator becoming a new domain or shared utility bypass; over-fragmenting supporting modules before real needs.

## Rejected alternatives
Unstructured shared services/repositories; speculative microservices; owner-to-consumer dependencies that create cycles.

## Validation / fitness functions
Baseline Python checker verifies allowlist references, acyclicity and unique logical data ownership. Backend bootstrap adds compiled ArchUnit rules for allowed public imports, internal access, layer direction and cycles; frontend bootstrap adds bounded feature imports. No compiled check exists yet.
