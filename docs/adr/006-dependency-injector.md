# ADR-006: Use `dependency-injector` Library for DI Wiring

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Project owner
- **Related:** ADR-001 (ports & adapters), DESIGN.md §3, AGENT.md "Dependency injection"

---

## Context

ADR-001 commits us to ports & adapters: business logic depends on abstract Protocols, concrete adapters are injected at runtime. We need a mechanism to:

1. **Select adapters per environment** (`local` vs `azure`) without `if/else` ladders in the codebase.
2. **Manage lifetimes** — singletons for stateful resources (Mongo client, Redis pool), factories for per-request services.
3. **Inject dependencies into FastAPI routes** cleanly.
4. **Swap adapters in tests** without monkey-patching globals.
5. **Stay readable** — wiring should look like a configuration file, not a magic spell.

Python has several options ranging from "no library" to heavyweight frameworks. We need to pick one and commit, because the DI container is the single most-touched seam in the codebase.

---

## Decision

Use the **[`dependency-injector`](https://python-dependency-injector.ets-labs.org/)** library, with all wiring centralized in `app/config/container.py`.

### Why this library

- **Declarative** — adapters are wired in a `Container` class with `providers.Singleton`, `providers.Factory`, `providers.Selector`. Reads top-down like a config file.
- **Environment-driven selection** — `providers.Selector(config.environment, local=..., azure=...)` is purpose-built for our use case.
- **FastAPI integration** — `@inject` + `Provide[Container.x]` works cleanly with `Depends`.
- **Testable** — `container.database.override(FakeDatabase())` swaps implementations in tests without touching imports.
- **Mature** — actively maintained, used in production by sizable Python shops, well-documented.
- **Type-friendly** — works with Protocol-based ports.

### How we'll use it

```python
# app/config/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Port: Database — selected by ENVIRONMENT
    database = providers.Selector(
        config.environment,
        local=providers.Singleton(MongoDBDatabase, uri=config.mongo.uri),
        azure=providers.Singleton(CosmosDatabase, endpoint=config.cosmos.endpoint),
    )

    # Service depending on the port — never on a concrete adapter
    health_service = providers.Factory(HealthService, db=database, ...)
```

Routes inject via `Depends(Provide[Container.health_service])`. Tests use `container.database.override(...)`.

---

## Consequences

### Positive

- **Single source of wiring truth.** New contributors find every adapter binding in one file.
- **Trivial environment swaps.** `ENVIRONMENT=azure` flips every adapter in one place.
- **Test isolation without `unittest.mock.patch`.** This aligns with the AGENT.md rule that `core/` tests must not patch — they `.override()`.
- **Clear lifetime control.** `Singleton` for connection pools, `Factory` for stateless services, `Resource` for things needing setup/teardown.

### Negative

- **One more dependency** in `pyproject.toml` (~150 KB, no native code, pure Python).
- **Magic feel.** `Provide[...]` markers in route signatures look unusual to developers unfamiliar with the library. Mitigated by documentation in AGENT.md and consistent usage.
- **`@inject` decorator must be applied carefully.** Forgetting it means `Provide[...]` is treated as a literal default value — confusing failure mode. Mitigated by the convention that _every route uses `@inject`_, no exceptions.
- **`container.wire(modules=[...])`** must be called at startup so `@inject` works. One more thing to remember in `main.py`.

### Neutral

- The library is the standard pick in this design space; few alternatives are seriously competitive.

---

## Alternatives considered

### 1. Manual DI (no library, hand-write a container)

- ✅ Zero dependencies, total control.
- ✅ Simple for ~5 components.
- ❌ Reinventing `Selector`, `Singleton`, lifetime management. Predictable code rot as the project grows.
- ❌ FastAPI integration requires writing helpers anyway.
- ❌ No portfolio signal (anyone can write a dict).
- **Rejected** — saves no real time, removes a recognizable architecture pattern.

### 2. FastAPI's built-in `Depends()` only

- ✅ Native, no extra library.
- ✅ Familiar to FastAPI developers.
- ❌ Couples DI to the web framework. Background jobs, CLI scripts, and standalone tests all need a separate path.
- ❌ Environment-based selection requires writing factory functions with `if/else` — exactly what we want to avoid.
- ❌ No clean override story for tests beyond `app.dependency_overrides`, which is FastAPI-specific.
- **Rejected** — couples too tightly to one entrypoint.

### 3. `punq`

- ✅ Lightweight, minimal API.
- ✅ Decent type support.
- ❌ Smaller community, less FastAPI-specific guidance, no built-in environment selector.
- ❌ Lifetime management less expressive.
- **Rejected** as the weaker version of `dependency-injector`.

### 4. `injector` (Python port of Guice)

- ✅ Familiar to Java/Guice users.
- ❌ Decorator-heavy, less declarative than `dependency-injector`.
- ❌ Environment-based binding is awkward — typically requires multiple Module classes.
- **Rejected** for being less fit-for-purpose.

### 5. Django-style global app registry / service locator

- ❌ Anti-pattern in modern Python. Hidden dependencies, untestable, action at a distance.
- **Rejected** outright.

---

## Open questions

- Do we use `Resource` providers for anything in Batch 1? _(Probably not — Mongo/Redis pools are happy as Singletons. Resource providers are useful when teardown matters, e.g., closing connection pools cleanly. Revisit in Batch 5 for Azure adapters.)_
- Wire modules at import time or via FastAPI lifespan? _(Leaning: lifespan, so test apps can wire their own container.)_

---

## References

- [dependency-injector documentation](https://python-dependency-injector.ets-labs.org/)
- [FastAPI integration guide](https://python-dependency-injector.ets-labs.org/examples/fastapi.html)
- ADR-001 (this repo)
- AGENT.md "Dependency injection" (this repo)
