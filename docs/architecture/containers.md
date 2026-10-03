# C4 level 2 — containers

## AS-IS

```mermaid
flowchart LR
    browser["Visitor browser\nHTML/CSS/JS + localStorage demo"] -->|"HTTP :8080"| nginx["landing container\nNginx :80"]
    browser -->|"HTTPS fonts"| fonts["Google Fonts"]
```

Defined by `landing/docker-compose.yml`. No server storage, API, authenticated UI or TLS endpoint is currently configured.

## TO-BE

```mermaid
flowchart TB
    browser["Parent / child / staff browser\nAngular application"]
    external["External payment provider"]
    subgraph server["Single server — Docker Compose"]
        edge["HTTPS edge\nTLS termination and routing"]
        landing["Existing landing\nStatic Nginx service"]
        frontend["frontend\nNginx: Angular assets / route fallback / API proxy"]
        backend["backend\nSpring Boot modular monolith\nHTTP API + in-process scheduled jobs"]
        db[("PostgreSQL\nOwned tables + durable delivery + sessions if selected\nPersistent volume")]
        edge -->|"Marketing host/path"| landing
        edge -->|"Application host"| frontend
        frontend -->|"/api"| backend
        backend -->|"Private database connection"| db
    end
    browser -->|"HTTPS"| edge
    external -->|"Verified /api payment webhook"| edge
    backend -->|"Provider adapters"| providers["Payments / video / email\nExternal services"]
    backend -->|"Private object operations"| storage["S3-compatible object storage\nEU/EEA preferred"]
    db -.->|"Encrypted off-server backup"| backup["Restricted backup destination"]
```

The edge can be integrated into the production frontend web server or provided by a host reverse proxy; no extra distributed service is mandated. The chosen arrangement must preserve application same-origin `/api` access, landing, TLS, correct forwarded headers and webhook routing. It is an implementation topology decision within ADR-0005.

| Container/boundary | Responsibility | Exposure / state |
| --- | --- | --- |
| landing | Marketing and existing demo behavior | Static files; no production child/account data |
| frontend | Angular feature workflows, accessible Polish interface, dedicated typed API clients | Browser assets; no credentials/long-lived tokens in browser storage |
| backend | Domain capabilities, authorization, integration adapters, scheduled durable delivery | Private service port; no exposed admin/metrics endpoint |
| PostgreSQL | Business state, unique constraints, versioned migrations, delivery/session state | Private network; persistent named volume, separately backed up |
| Object storage | Quarantined/scanned private materials and submissions | Private buckets; controlled expiring access after capability authorization |

Backend/frontend containers, PostgreSQL, TLS and production routing are target-only. Exact image/runtime versions, secrets provisioning and hostnames await bootstrap. See [deployment](deployment.md) for migration/readiness/backup responsibilities.
