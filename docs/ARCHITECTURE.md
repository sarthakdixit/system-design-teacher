# Architecture

This document is the short, narrative companion to `docs/diagrams/architecture.png`. For implementation depth, read [DESIGN.md](./DESIGN.md) and the [ADRs](./adr/).

![System architecture](./diagrams/architecture.png)

## In one paragraph

A React single-page app served from Azure Static Web Apps talks to a FastAPI backend running on Azure Container Apps. The backend uses Microsoft Entra ID for sign-in, Cosmos DB (Mongo API) for storage, Azure Key Vault for secrets (accessed via Managed Identity), and the OpenAI API for AI feedback. Application Insights collects telemetry. The whole thing is provisioned by Bicep and deployed via GitHub Actions on every push to `main`.

## The four layers

### 1. Client (browser)

A React 18 SPA built with Vite. State is split four ways: TanStack Query for server state, Zustand for global client state (auth session), URL parameters for routing state, and `useState` for local UI. MSAL.js handles the Microsoft Entra OAuth flow. Axios with interceptors attaches JWTs to every API call. React Flow powers the design canvas.

### 2. Backend (FastAPI on Container Apps)

Hexagonal architecture with seven ports (`AuthProvider`, `Database`, `LLMProvider`, `Cache`, `RateLimiter`, `Telemetry`, `SecretsProvider`). Local development uses local adapters (mock auth, Mongo, Redis, console logging); production uses Azure adapters (Entra, Cosmos, App Insights, Key Vault). Adapters are selected at runtime by the dependency-injection container based on the `ENVIRONMENT` env var.

The container scales to zero when idle and up to two replicas under load. HTTP-based scaling triggers at ~10 concurrent requests per replica.

### 3. Data + secrets

**Cosmos DB (Mongo API)** holds five collections: users, questions, attempts, feedback_cache, rate_limit_counters. Free tier covers 1000 RU/s and 25 GB storage — enough for portfolio-scale traffic.

**Key Vault** holds five secrets: `OPENAI-API-KEY`, `JWT-SECRET`, `MONGO-URI`, `MICROSOFT-CLIENT-ID`, `MICROSOFT-TENANT-ID`. The Container App's system-assigned Managed Identity has the "Key Vault Secrets User" role and pulls secrets via Container Apps' platform-level secret references — not via in-process Python code.

### 4. External services

**OpenAI API** is called from the backend via `httpx`. Two models are used: `gpt-4o-mini` for cheap tasks (situation question generation, never on user requests after seed time) and `gpt-4o` for the design feedback loop. Every call is rate-limited and cache-keyed by a normalized hash of the diagram structure.

**Microsoft Entra ID** issues ID tokens validated against the published JWKS. The backend never sees user passwords. The session JWT issued by the backend is HS256-signed, stored in memory only, and expires after 24 hours.

## Request flow: design submission

This is the headline feature, end-to-end:

1. User drags components on the React Flow canvas, types optional notes, clicks Submit.
2. Frontend serializes the diagram (nodes + edges, with optional edge labels), strips UI-only fields (positions, selection state), and POSTs to `/api/v1/attempts/design`.
3. Backend's auth middleware validates the JWT and resolves the user.
4. The rate-limit service checks per-user (2/day) and global (100/day) caps. On limit hit, returns 429 with reset time.
5. The diagram-hash service normalizes node order and edge order, hashes with SHA-256.
6. The design-feedback service queries the cache by hash. **Cache hit** → return immediately at $0 cost.
7. **Cache miss** → call OpenAI gpt-4o with the diagram + system prompt. Validate response against the `DesignFeedback` Pydantic schema. Retry once on schema failure with stricter instructions.
8. Persist the attempt and the feedback to Cosmos. Telemetry records latency, token count, cache hit/miss.
9. Return severity-grouped feedback to the client.

## Request flow: sign-in

1. User clicks "Sign in with Microsoft".
2. MSAL.js opens a Microsoft popup. User authenticates.
3. Microsoft returns an ID token to the frontend.
4. Frontend POSTs the ID token to `/api/v1/auth/microsoft/callback`.
5. Backend fetches Microsoft's JWKS (cached 1 hour), verifies the token's signature and claims (audience, issuer, expiry).
6. Backend upserts the user in Cosmos by Microsoft Object ID.
7. Backend signs its own JWT (HS256, 24-hour expiry) using the secret from Key Vault.
8. Frontend stores the backend JWT in memory (Zustand, never localStorage) and uses it for every subsequent request.

## What the architecture does NOT do

- **No multi-region failover.** Single region (`eastus2`). An eastus2 outage takes the site down. Acceptable for portfolio scope.
- **No private endpoints / VNet integration.** Cosmos and Key Vault accept traffic from public IPs but require auth. For an MVP that's fine; production with sensitive data would add private endpoints.
- **No queue or worker tier.** All work is synchronous in the request path. The longest call (OpenAI design feedback) takes ~10–30 seconds and the user waits. A worker queue would unblock the API but add complexity.
- **No CDN beyond Static Web Apps' built-in edge.** The free SWA tier handles all edge caching for static assets.
- **No A/B testing or feature flags.** Single revision serves all traffic. Container Apps supports multi-revision routing if we ever need it.

## Why hexagonal architecture was worth it

Going hexagonal cost extra time in Batch 1 — defining Protocol classes for every external system seemed over-engineered when only one local implementation existed. It paid for itself in Batch 5: switching from local to Azure was a single config change. Not one line of business logic moved. The five Azure adapters added in Batch 5 dropped into pre-existing port slots without touching the services that use them.

If the project grew (added a real-time collab feature, switched to Azure OpenAI, moved to a different vector store), the same pattern would handle each migration without touching domain logic.

## Trade-offs we accepted

| What                         | Trade-off                                                             |
| ---------------------------- | --------------------------------------------------------------------- |
| Single-region                | No HA; one region down = whole site down                              |
| Container Apps scale-to-zero | First request after idle has 5–10s cold start                         |
| Free Cosmos tier             | Capped at 1000 RU/s; throttled if traffic spikes                      |
| In-process rate limiter      | Two replicas can't share counters perfectly; acceptable for portfolio |
| Synchronous LLM call         | User waits 10–30s for design feedback; no queue                       |
| MSAL popup-based auth        | Not the smoothest mobile UX; redirect mode would be better            |

Each is documented in the ADR for the relevant decision (`docs/adr/`).

## Reading further

- Component-level details: [DESIGN.md](./DESIGN.md)
- Why each technology was chosen: [docs/adr/](./adr/)
- How to deploy: [DEPLOYMENT.md](./DEPLOYMENT.md)
- How to run locally: top-level [README.md](../README.md) §Quickstart
- For AI assistants and contributors working on the code: [AGENT.md](../AGENT.md)
