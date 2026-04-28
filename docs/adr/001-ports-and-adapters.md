# ADR-001: Ports & Adapters (Hexagonal) Architecture

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Project owner
- **Related:** ADR-006 (DI framework), DESIGN.md §2.1, §3

---

## Context

This project will be developed locally first (Docker Compose, MongoDB, Redis, mock auth, console logging) and later deployed to Azure (Cosmos DB, Application Insights, Microsoft Entra ID, Key Vault).

We need an architecture that allows:

1. **Zero changes to business logic** when swapping local infrastructure for Azure equivalents.
2. **Fast unit tests** that don't need Docker, real databases, or LLM API keys.
3. **Clear contracts** between business logic and external systems, so each side can evolve independently.
4. **A portfolio-grade demonstration** of clean architecture, since this project doubles as a job-search artifact.

The naive alternative — calling `pymongo`, `openai`, `redis-py`, etc. directly from FastAPI route handlers — fails all four goals. Tests would require running services, swapping cloud providers would mean rewriting routes, and the architecture would have nothing distinctive to show.

---

## Decision

Adopt **Ports & Adapters (Hexagonal Architecture)** as the structural backbone of the backend.

- **Domain & services (`app/core/`)** depend only on **abstract Protocols** (ports) defined in `app/core/ports/`.
- **Concrete implementations (adapters)** live in `app/adapters/local/` and `app/adapters/azure/`.
- A **DI container** (`app/config/container.py`) wires the right adapter for each port based on the `ENVIRONMENT` setting.
- **`app/core/` may not import from `app/adapters/`** or any cloud SDK. This rule is enforced by convention and (ideally) by `import-linter`.

### Layer dependencies

```
core/domain    ←  stdlib + Pydantic only
core/ports     ←  stdlib + typing + Pydantic types only
core/services  ←  core/domain + core/ports
adapters/*     ←  ports + domain + external SDKs (pymongo, openai, redis, etc.)
api/*          ←  services + domain + schemas + container
config/*       ←  adapters + ports (the wiring layer)
main.py        ←  config + api
```

### Ports we will define

`AuthProvider`, `Database`, `LLMProvider`, `Cache`, `RateLimiter`, `Telemetry`, `SecretsProvider`. See DESIGN.md §3.1 for the architecture diagram.

---

## Consequences

### Positive

- **Cloud portability.** Swapping Mongo → Cosmos, console logs → Application Insights, mock auth → Entra ID requires writing one new adapter and adding a line to the DI container. Business logic never changes.
- **Testability.** Unit tests inject **fake adapters** (in-memory, deterministic) — no Docker, no API keys, no flakiness.
- **Clear contracts.** Each port is a one-page Protocol with typed methods. New contributors learn the surface area in minutes.
- **Optionality.** If Cosmos turns out wrong, swap to Postgres without touching domain code. If OpenAI prices spike, swap to Anthropic Claude or Azure OpenAI by writing one adapter.
- **Portfolio signal.** Hexagonal architecture is recognized by senior engineers and architects as a sign of mature thinking.

### Negative

- **Up-front cost.** Defining 7 Protocols + 7 local adapters + DI container before writing any feature feels heavy. Mitigated by the fact that this is exactly Batch 1 — we do it once and then move fast.
- **Indirection.** Newcomers may find "service depends on a Protocol that's bound to an adapter at runtime" harder to follow than direct imports. Mitigated by `AGENT.md` documentation and consistent naming.
- **Easy to violate accidentally.** A junior dev (or AI assistant) might `from pymongo import ...` inside a service. Mitigated by review, linting, and `AGENT.md` callouts.

### Neutral

- More files than a "flat" architecture, but each file is small and focused. The trade-off favors the long term.

---

## Alternatives considered

### 1. Layered architecture (controllers → services → repositories, with concrete imports)

- ✅ Familiar to most developers.
- ❌ Tightly couples services to specific data stores. Swapping providers means editing every service.
- ❌ Repository pattern alone doesn't solve LLM, cache, telemetry, auth — you'd reinvent ports anyway, just less coherently.
- **Rejected** because the swap-at-deploy requirement is central to this project.

### 2. Direct SDK calls in route handlers (no abstraction)

- ✅ Lowest indirection, fastest to write feature 1.
- ❌ Untestable without infrastructure. No swap path. No portfolio signal.
- **Rejected** outright.

### 3. Clean Architecture (Uncle Bob's full version, with use-case interactors, DTOs at every boundary, etc.)

- ✅ Most rigorous separation.
- ❌ Significant overhead for an MVP. The boundary between request DTO → use case input DTO → entity is overkill at this scale.
- **Rejected** as too heavy. Hexagonal gives 80% of the benefit at 30% of the ceremony.

### 4. Framework-coupled (FastAPI `Depends` everywhere, no separate container)

- ✅ Native to FastAPI, less library footprint.
- ❌ Couples DI to the web framework. Background jobs, CLI tools, and tests all suffer.
- ❌ Harder to express environment-driven adapter selection.
- **Rejected** in favor of `dependency-injector` — see ADR-006.

---

## Open questions

- Will we enforce import rules with `import-linter` or rely on review and docs? _(Leaning: add `import-linter` in Batch 6 polish.)_
- Should adapters ever depend on each other (e.g., RedisCache used inside CosmosDatabase as a fast lookup)? _(Default: no — composition happens in services, not between adapters. Revisit if a clear case appears.)_

---

## References

- Alistair Cockburn, "Hexagonal Architecture" (2005)
- DESIGN.md §2.1, §3 (this repo)
- AGENT.md "Architectural contract" (this repo)
