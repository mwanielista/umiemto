# C4 level 1 — system context

AS-IS: visitor → static Nginx landing → demo waitlist in that browser's localStorage. Browser also loads Google Fonts. There is no server signup, educational account or running platform integration.

## Target actors and systems

```mermaid
flowchart LR
    guardian["Main / additional guardian"]
    child["Child learner: independent educational login"]
    teacher["Assigned teacher"]
    methodologist["Methodologist: scoped quality"]
    support["Support: scoped case"]
    admin["Authorized administrator"]
    owner["Business Owner: product grants"]
    operator["Technical operator / auditor"]
    platform["eSzkola: web UI + modular monolith"]
    payments["External payment processor"]
    video["External video provider"]
    email["Transactional email provider"]
    objects["Private S3-compatible objects"]
    credentials["Conditional external credential authority"]
    guardian -->|"Purchases, consent, related-child access"| platform
    child -->|"Own learning and consultations"| platform
    teacher -->|"Programs, assigned learning, grading"| platform
    methodologist -->|"Content and quality evidence"| platform
    support -->|"Minimum authorized case data"| platform
    admin -->|"Scoped administration and recovery"| platform
    owner -->|"Audited business exceptions / terms decisions"| platform
    operator -->|"Private operations / restricted audit"| platform
    guardian -->|"Hosted checkout"| payments
    platform -->|"Verified payments / refunds"| payments
    platform -->|"Authorized meeting information"| video
    child -->|"Lesson media"| video
    teacher -->|"Lesson media"| video
    platform -->|"Minimal transactional message"| email
    platform -->|"Private material / attachment operations"| objects
    platform -.->|"ADR-0006 pending"| credentials
```

External credentials are conditional, not a selected service. Main/additional guardians have different relationship-management authority; child has no purchasing authority. Product Business Owner grants include approved business exceptions, but BA/SA approval occurs solely in repository governance and is not a product feature.

Video media bypasses eSzkola; links may be entered by authorized staff without a mandatory provider API. No default recording, private teacher contact, public child profiles or open social chat is proposed. Providers receive purpose-minimal data. Existing topology decisions remain unchanged; the actor/authority refinement follows FR-001/FR-005/FR-014/FR-019.

Browsers are untrusted. HTTPS/API authenticates, validates and checks resource access. Provider callbacks require verified server authority; browser returns cannot confirm payment/refund. PostgreSQL and S3 buckets remain private; authorized short-lived object access is a controlled exception to backend-proxied bytes. See [security](security.md), [integrations](integrations.md) and [containers](containers.md).
