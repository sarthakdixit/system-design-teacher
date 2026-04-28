# AGENT.md — System Design Teacher (Python Backend)

This file tells AI coding assistants (and new human contributors) how to work effectively in this repo. Read it before making changes.

---

## Project snapshot

- **What:** Web platform for practicing system-design interviews. Two modes: situation-based Q&A, and drag-and-drop architecture design with AI feedback.
- **Why it exists:** Portfolio project showcasing clean architecture, Azure integration, and pragmatic LLM use.
- **Where to find the big picture:** `docs/DESIGN.md` is the source of truth. Read it before proposing any architectural change.

---

## Architectural contract — read this first

This project uses **Ports & Adapters (Hexagonal Architecture)**. It is non-negotiable. New code must respect it.

### The rule

> Code in `app/core/` must never import from `app/adapters/` or from any cloud SDK. It may only import from `app/core/ports/`.

If you find yourself wanting to `from pymongo import ...` inside a use case, stop — you're in the wrong layer. Add or use a port.

### The layers

```
app/
├── core/
│   ├── domain/        # Entities (User, Question, Attempt, Feedback)
│   ├── services/      # Use cases (SubmitDesign, GetSituationQuestion, ...)
│   └── ports/         # Abstract Protocols — interfaces only
├── adapters/
│   ├── local/         # MongoDB, Redis, mock auth, console logging
│   └── azure/         # Cosmos DB, App Insights, Entra ID (added in Batch 5)
├── api/
│   ├── routes/        # FastAPI routers (thin — delegate to services)
│   ├── schemas/       # Pydantic request/response DTOs
│   └── deps.py        # FastAPI dependency helpers (wires DI → routes)
├── config/
│   ├── settings.py    # Pydantic BaseSettings — reads env
│   └── container.py   # dependency-injector Container
└── main.py            # FastAPI app factory
```

### Import rules (enforced by convention, and ideally by `import-linter`)

- `core/domain` ← may import only stdlib + Pydantic
- `core/services` ← may import `core/domain` and `core/ports`
- `core/ports` ← may import only stdlib, `typing`, Pydantic types
- `adapters/*` ← may import ports, domain, and external SDKs
- `api/*` ← may import services, domain, schemas, `config/container`
- `config/container` ← may import adapters and ports; wires them together
- `main.py` ← imports `config/container` and `api`

**If you violate these, you've broken the architecture. Don't.**

---

## Dependency injection — how it works here

We use the **`dependency-injector`** library.

### The container

`app/config/container.py` is where adapters are wired to ports based on the `ENVIRONMENT` setting.

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Port: Database → selected by environment
    database = providers.Selector(
        config.environment,
        local=providers.Singleton(MongoDBDatabase, uri=config.mongo.uri),
        azure=providers.Singleton(CosmosDatabase, endpoint=config.cosmos.endpoint),
    )

    # Services depend on ports — never on concrete adapters
    design_submission_service = providers.Factory(
        DesignSubmissionService,
        db=database,
        llm=llm_provider,
        cache=cache,
        rate_limiter=rate_limiter,
        telemetry=telemetry,
    )
```

### Injecting into FastAPI routes

Use `dependency-injector`'s `@inject` with `Provide[...]` markers:

```python
from dependency_injector.wiring import inject, Provide
from app.config.container import Container

@router.post("/attempts/design")
@inject
async def submit_design(
    payload: DesignSubmissionRequest,
    service: DesignSubmissionService = Depends(Provide[Container.design_submission_service]),
):
    return await service.submit(payload)
```

Never instantiate a service directly in a route. Always inject.

---

## Adding a new capability — the playbook

When you need to add functionality, follow this order:

1. **Does it need an external system?** (DB query, LLM call, cache, logging, file I/O)
   - **Yes:** It belongs behind a port. Go to step 2.
   - **No:** It's pure domain logic. Put it in `core/services/` or `core/domain/`. Done.
2. **Is there already a port for this capability?** (Check `core/ports/`.)
   - **Yes:** Use it. If the existing port needs a new method, add it — update all adapters.
   - **No:** Create a new port.
3. **Creating a new port:**
   - Define a `Protocol` in `core/ports/<capability>.py` with typed methods and docstrings.
   - Implement local adapter in `adapters/local/`.
   - Implement Azure adapter in `adapters/azure/` (or stub it if Batch 5 hasn't arrived).
   - Wire both in `config/container.py` via `providers.Selector`.
4. **Write the use case** in `core/services/`, depending only on ports.
5. **Expose via API** in `api/routes/`.
6. **Tests:** Unit test the service with fake ports. Integration test the adapters.

---

## Code conventions

### Language & version
- Python **3.11+** (use `match`, `Self`, `TypedDict`, PEP 695 syntax where helpful).
- Type hints are **mandatory** on all public functions and methods.
- Use `from __future__ import annotations` at the top of each module.

### Async
- Everything I/O-bound is `async`. No blocking calls in request paths.
- Use `httpx.AsyncClient` for HTTP, `motor` for MongoDB. **Never** `requests` or `pymongo` (sync).

### Naming
- Modules: `snake_case`
- Classes: `PascalCase`
- Functions/vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Ports end in the capability noun: `LLMProvider`, `Cache`, `RateLimiter`, `Database`, `Telemetry`, `AuthProvider`, `SecretsProvider`.
- Adapters are named `<Tech><Port>`: `MongoDBDatabase`, `OpenAILLMProvider`, `RedisCache`, `MockAuthProvider`.

### Pydantic
- Use **Pydantic v2**.
- Domain entities: Pydantic models with `model_config = ConfigDict(frozen=True)` where immutable.
- API DTOs live in `api/schemas/`, separate from domain entities (don't leak internal fields to clients).

### Errors
- Domain errors: custom exceptions in `core/domain/errors.py` (e.g., `RateLimitExceeded`, `QuestionNotFound`).
- API layer translates domain errors → HTTP responses in a central exception handler.
- Never raise raw `Exception`. Never swallow exceptions silently.

### Logging & telemetry
- **Never** use `print()` or `logging` directly in `core/`. Use the injected `Telemetry` port.
- In adapters and `api/`, use `structlog` bound via the Telemetry adapter.
- Never log secrets, JWTs, full request bodies containing PII, or raw LLM API keys.

---

## Environment & configuration

Configuration is read from environment variables via `pydantic-settings`.

### Local setup

```bash
cp .env.example .env.local
# Fill in OPENAI_API_KEY at minimum
docker compose up
```

Services expected after `docker compose up`:
- `localhost:8000` — FastAPI backend
- `localhost:27017` — MongoDB
- `localhost:8081` — Mongo Express UI (browse DB in browser)
- `localhost:6379` — Redis

### Required env vars

| Var | Local default | Azure | Notes |
|---|---|---|---|
| `ENVIRONMENT` | `local` | `azure` | Drives DI container selector |
| `OPENAI_API_KEY` | (your key) | (from Key Vault) | Required for LLM |
| `MONGO_URI` | `mongodb://mongo:27017` | (from Key Vault) | Cosmos MongoDB API conn string in prod |
| `REDIS_URL` | `redis://redis:6379` | n/a in prod | Prod uses Cosmos container for cache |
| `JWT_SECRET` | dev value | (from Key Vault) | HS256 signing key |
| `MICROSOFT_CLIENT_ID` | dev value | (from Key Vault) | Entra app registration |
| `MICROSOFT_TENANT_ID` | dev value | (from Key Vault) | |
| `APPINSIGHTS_CONNECTION_STRING` | unset | (from App Insights) | Azure only |
| `RATE_LIMIT_SITUATION_DAILY` | `5` | `5` | Per user |
| `RATE_LIMIT_DESIGN_DAILY` | `2` | `2` | Per user |
| `GLOBAL_CAP_SITUATION_DAILY` | `50` | `50` | Wallet protection |
| `GLOBAL_CAP_DESIGN_DAILY` | `100` | `100` | Wallet protection |

---

## Testing

### Philosophy
- **Unit tests** run without Docker. They inject **fake adapters** (in `tests/fakes/`) — not mocks.
- **Integration tests** require `docker compose up` and hit real Mongo/Redis.
- **Contract tests** verify every adapter satisfies its port's behavioral expectations.

### Running
```bash
# Unit only, fast
pytest tests/unit

# Integration (requires docker compose running)
pytest tests/integration

# Everything
pytest

# With coverage
pytest --cov=app --cov-report=term-missing
```

### Guidelines
- Never use `unittest.mock.patch` inside `core/` tests. If you need to patch, your design is wrong — inject a fake instead.
- Every port has a `tests/contracts/test_<port>_contract.py` parametrized over all its adapters.
- New service → new unit test file. Target: 80%+ coverage on `core/services/`.

---

## LLM integration rules

The LLM is a **port** (`LLMProvider`). Follow these rules when using it:

1. **Never call OpenAI SDK directly from services.** Always via the port.
2. **Every LLM call is cached** unless explicitly marked `bypass_cache=True` (rare).
3. **Every LLM call is rate-limited** at both user and global levels.
4. **Prompts live in `core/prompts/`** as `.md` files, loaded at startup. They are versioned.
5. **Responses are Pydantic-validated.** On validation failure, retry once with stricter instructions, then fail.
6. **User input in prompts is always delimited** and preceded by an instruction to ignore any embedded instructions.
7. **Log every call's token count** via telemetry. Production cost visibility depends on it.
8. **Model selection is explicit per call**, not global. Use `gpt-4o-mini` for cheap tasks, `gpt-4o` only for feedback.

---

## Tooling

| Tool | Purpose | Command |
|---|---|---|
| `ruff` | Lint + format | `ruff check . && ruff format .` |
| `mypy` | Type check | `mypy app/` |
| `pytest` | Test | `pytest` |
| `uv` or `pip-tools` | Dep management | (see `pyproject.toml`) |
| `pre-commit` | Git hooks | `pre-commit install` |

Run `make check` (if `Makefile` exists) or the above before committing.

---

## Commit & PR conventions

- Commit messages: Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
- One logical change per PR.
- PR description must include:
  - What changed and why
  - Which ports/adapters were touched
  - Whether any ADR was added or updated
  - Manual verification steps
- If a change crosses the port/adapter boundary incorrectly, reviewers should block.

---

## Things AI assistants commonly get wrong here — avoid these

1. **Importing `pymongo` or `openai` inside `core/`.** Never. Always via a port.
2. **Instantiating services directly in routes.** Always inject via DI.
3. **Using `unittest.mock` to patch adapters in tests.** Inject a fake from `tests/fakes/` instead.
4. **Using `localStorage` for JWT in the frontend.** Use in-memory storage; MSAL handles refresh.
5. **Calling the LLM without going through the cache + rate limiter.** Every call must.
6. **Creating new collections in Mongo without updating `docs/DESIGN.md` §5.**
7. **Adding new env vars without updating `.env.example` and this AGENT.md.**
8. **Silently catching exceptions.** Raise a domain error or let it propagate.
9. **Mixing domain entities with API DTOs.** Keep them separate in `core/domain/` vs `api/schemas/`.
10. **Blocking I/O in async code.** `time.sleep`, `requests.get`, sync DB drivers — all banned.

---

## Glossary of shorthand

- **"the container"** — `app/config/container.py`, the DI wiring
- **"a port"** — a `Protocol` class in `app/core/ports/`
- **"an adapter"** — a class in `app/adapters/local/` or `app/adapters/azure/`
- **"a service"** — a use case class in `app/core/services/`
- **"the spec"** — `docs/DESIGN.md`
- **"an ADR"** — a file in `docs/adr/NNN-*.md`

---

## When in doubt

- Architectural question? → `docs/DESIGN.md`
- Why a specific tech was chosen? → `docs/adr/`
- How something should be named or placed? → this file, section "Code conventions"
- How to add a new feature? → this file, section "Adding a new capability"

If none of those answer your question, pause and ask the human before inventing a pattern.
