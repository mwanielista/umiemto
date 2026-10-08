# C4 level 2 — containers

## AS-IS

```mermaid
flowchart LR
    visitor["Visitor browser: HTML/CSS/JS + localStorage demo"]
    landing["landing: Nginx :80"]
    fonts["Google Fonts"]
    visitor -->|"HTTP :8080"| landing
    visitor -->|"HTTPS fonts"| fonts
```

Only landing Compose exists; no server account storage, API, authenticated application or configured TLS boundary is implemented.

## Retained target topology

```mermaid
flowchart TB
    browser["Guardian / child / staff: Angular browser"]
    payment["External payment processor"]
    subgraph server["Single server: Docker Compose"]
        edge["HTTPS edge: TLS and routing"]
        landing["Preserved static landing"]
        frontend["Frontend web server: Angular assets, SPA fallback, API proxy"]
        backend["Spring Boot modular monolith: API + scheduled durable work"]
        db[("Private PostgreSQL: owned data, delivery, sessions if selected")]
        edge --> landing
        edge --> frontend
        frontend -->|"/api/v1"| backend
        backend --> db
    end
    browser -->|"HTTPS"| edge
    payment -->|"Verified payment / refund callbacks"| edge
    backend -->|"Owner adapters"| providers["Payments / video / email"]
    backend -->|"Private objects / quarantine"| storage["S3-compatible storage: EU/EEA preferred"]
    db -.->|"Encrypted off-server backup"| backup["Restricted recovery destination"]
    storage -.->|"Recoverable versions / inventory"| backup
```

ADR-0005's topology is preserved. Edge may be integrated with the frontend server or host proxy, retaining same-origin API, landing/TLS and trusted forwarding. No new service is required for KPI, cases, MFA, quota or refund coordination. Provider/credential selection and session persistence remain separate choices.

| Boundary | Responsibility / exposure |
| --- | --- |
| landing | Static marketing/demo; no production child/account persistence |
| frontend | Polish responsive feature flows and typed APIs; no long-lived browser-storage secrets |
| backend | Resource-authorized capability rules, bounded owner adapters and in-process durable workers; private service/management ports |
| PostgreSQL | Owner-prefixed tables, uniqueness, versioned migrations and durable work; persistent volume plus independent backup |
| S3 | Private quarantined/scanned materials/submissions; expiring authorized operations and matching backup inventory |
| Recovery | Off-server database plus object evidence, protected audit and provider references; measured RPO/RTO |

All new containers/routing/migrations/health/TLS remain unimplemented. The diagram adds object recovery alongside database recovery because NFR-004 explicitly includes service files. No current-version compatibility or operational objective is claimed to be verified. See [deployment](deployment.md) and [nfr.md](nfr.md).
