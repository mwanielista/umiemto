# ADR-0006: Browser sessions and credential authority options

## Status
Proposed — 2026-10-03. Blocks authentication implementation; no identity provider or credential mechanism is selected.

## Context
Parent and child educational accounts, privileged MFA, safe recovery and guardian authority are required. No backend/authentication exists. Account creation/recovery, child login and provider/data-processing choices remain undefined.

## Problem
Choose who verifies credentials and how the browser obtains a restricted authenticated session without inventing child identity rules.

## Constraints
SR-01,08,14; privileged MFA, guardian-owned purchase, resource authorization, minimal child data, no long-lived browser-storage secrets, single-server pilot topology.

## Considered options
External OIDC credential authority with backend-managed session reduces credential/MFA implementation but introduces provider cost/processing dependence and child-account constraints. Application-managed Spring Security credentials/MFA/session avoids a provider but increases recovery/security responsibility. Direct browser bearer-token storage adds theft/refresh complexity and is not the recommended baseline.

## Decision
Recommend same-origin server-managed Secure/HttpOnly/SameSite session with CSRF protection, rotation, expiry/revocation and PostgreSQL session persistence if needed. Retain both credential-authority options until product/security resolve parent verification, child login, recovery, MFA and provider suitability. Never implement both in anticipation. Authorization from ADR-0004 remains required whichever option wins.

## Rationale
Session boundary separates browser handling from credential verification and avoids requiring Redis. Leaving credential authority Proposed makes unresolved operational and child-account assumptions visible.

## Consequences
Resolve and accept/supersede this ADR before authentication bootstrap. External credentials still map to locally owned grants/guardian relations. Child context must not retain parent purchase authority.

## Risks
Recovery/MFA bypass, child email requirements from unsuitable providers, identity outage, weak parental verification, session CSRF/fixation/revocation defects.

## Rejected alternatives
Do not select a credential provider by familiarity, presume child-owned email, treat OIDC claims as unlimited local roles, or allow parent-session UI switching without server authority restriction. Direct browser token storage is not recommended.

## Validation / fitness functions
Before acceptance, validate threat model and account/recovery flows with product/security. Future tests cover session/CSRF/cookie boundaries, login/logout/revocation, child/parent context isolation, required MFA and provider issuer/audience/assurance validation if external. No authentication checks can run now.
