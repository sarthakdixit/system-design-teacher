# ADR-007: Docker Compose for Local Development

- **Status**: Accepted
- **Date**: 2026-04-21 (revisited 2026-05-02 with Batch 5 deployment context)
- **Deciders**: Project owner

## Context

The platform has multiple stateful dependencies — MongoDB for persistence, Redis for caching, the FastAPI backend itself, optionally a Mongo Express UI for browsing the DB. New contributors (and the project owner moving between machines) need to bring all of these up locally with minimal friction.

Three patterns were considered for orchestrating local development:

1. **Docker Compose** — single YAML file declares all services, one command (`docker compose up`) brings them up.
2. **Manual installation** — `brew install mongodb`, `brew install redis`, then run each as a service. Backend runs natively via `uvicorn`.
3. **Devcontainer** — VS Code's `.devcontainer` system, which uses Docker under the hood but adds a richer in-IDE experience.

The local-dev pattern needs to satisfy three constraints:

- **Zero-to-running in under 5 minutes** for a new contributor with Docker installed.
- **Local-prod parity** — the backend container in production (Azure Container Apps, per Batch 5) is the same runtime image as local. Diverging here breaks the architecture's promise.
- **Cross-platform** — must work on Linux, macOS, and Windows (WSL).

## Decision

**Use Docker Compose.** A single `docker-compose.yml` at the repo root brings up:

- `backend` — FastAPI app via local `Dockerfile`, mounted source for hot-reload
- `mongo` — MongoDB 7 (port 27018 on host → 27017 in container, to avoid conflicts with system Mongo)
- `mongo-express` — Mongo Express UI on port 8081, for visual DB browsing
- `redis` — Redis 7 alpine variant on port 6379

`docker compose up -d` brings everything up. `docker compose logs -f backend` tails the running app.

## Consequences

### Positive

- **Zero-to-running** is genuinely fast: with Docker already installed, `git clone && cp .env.example .env.local && docker compose up -d` is the entire setup.
- **Local-prod parity preserved.** The same `Dockerfile` (and its production sibling `Dockerfile.functions`) is what builds the container in CI, pushes to Docker Hub, and runs in Azure Container Apps. No "works on my machine but breaks in prod" surface area.
- **Cross-platform** for free. Docker handles the OS abstraction.
- **Easy reset.** `docker compose down -v` wipes all state (Mongo data, Redis cache) for a clean restart.
- **Mongo Express bundled.** The included Mongo Express UI gives non-CLI users a way to browse the DB without installing MongoDB Compass or learning `mongosh`.
- **Composes well with later services.** When Batch 5 needed an LLM stub variant for offline dev, adding it was a 6-line addition to `docker-compose.yml`. Same for any future services.

### Negative

- **Docker is a hard dependency** for new contributors. If someone wants to run the project without Docker, they have to manually install Mongo, Redis, and run `uvicorn` themselves — possible but unsupported.
- **Resource usage.** Docker Desktop on macOS/Windows uses a lightweight VM and consumes ~2 GB of RAM at idle. Linux native is leaner. Acceptable cost for the parity benefit.
- **Hot-reload requires file mounts**, which are slow on macOS Docker Desktop's default filesystem driver. Using `:cached` mount or VirtioFS mitigates but doesn't eliminate. Not a problem on Linux.
- **Networking inside the compose network** is different from outside it. The backend reaches Mongo at `mongodb://mongo:27017` (service name); the host reaches Mongo at `localhost:27018` (mapped port). Seed scripts running on the host must use the second form. We document this in `backend/.env.example` and `backend/AGENT.md`.

## Alternatives considered

### Manual installation

- ✅ Slightly faster on bare metal (no Docker overhead).
- ❌ Per-platform install instructions (`brew` on macOS, `apt` on Ubuntu, MSI installer on Windows). High maintenance.
- ❌ Loses local-prod parity. Locally you'd run `uvicorn` natively against system Python; in production it's a Docker container. Different filesystem layouts, different process trees, different DNS. Subtle bugs lurk in the gap.
- ❌ Conflicts with already-installed system Mongo / Redis (which is why we map Mongo to host port 27018 — many devs already have a system Mongo on 27017).
- **Rejected** on parity grounds.

### Devcontainer

- ✅ Tight VS Code integration: pre-installed extensions, formatter setup, debug configs all defined declaratively.
- ✅ Onboarding is "open repo in VS Code → Reopen in Container" — zero terminal commands.
- ❌ Forces VS Code as the editor. Vim/JetBrains/Neovim users have to set up their own thing.
- ❌ Devcontainers are themselves Docker Compose under the hood for multi-service projects, so we'd be using both anyway.
- ❌ Adds a second config file (`.devcontainer/devcontainer.json`) on top of `docker-compose.yml`.
- **Rejected** for editor-agnostic reasons. Could be added later as a layer on top of Compose if there's demand.

### Tilt / Skaffold / Tilt-style "build + watch" tools

- ✅ Better for Kubernetes-native local dev (live sync into pods).
- ❌ Wildly over-engineered for our service count (4 services, no Kubernetes locally).
- ❌ Steep learning curve for new contributors.
- **Rejected.** Compose is the right granularity for this project size.

## Status & next steps

This decision has held since Batch 1 and has been validated through Batches 2–5. No reason to revisit. Future considerations:

- If we ever add Kubernetes locally (e.g., for testing Container Apps revisions), we'd add Kind or k3d alongside Compose, not replace it.
- If we add E2E tests with Playwright (Batch 6 polish), the test runner runs _outside_ Compose and hits `localhost:8000` and the frontend dev server.

## References

- `docker-compose.yml` (repo root)
- `Dockerfile` (local), `Dockerfile.functions` (production — Batch 5)
- `backend/AGENT.md` § Environment & configuration
- ADR-001 (ports & adapters) — explains why local and prod adapters differ at the port level but the orchestration shouldn't
