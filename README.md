# System Design Teacher

A web platform for practicing system-design interviews. Two modes:

1. **Situation-based practice** — read a real-world scenario and study a detailed reference answer.
2. **Design System practice** — drag-and-drop architecture components on a canvas, submit your design, and get **structured AI feedback**.

> **Status:** 🚧 Under active development. See [`docs/DESIGN.md`](./docs/DESIGN.md) for the full spec and [`docs/DESIGN.md` §13](./docs/DESIGN.md#13-project-batches) for the batch roadmap.

---

## Why this project exists

This is a portfolio project showcasing:

- **Hexagonal architecture** (ports & adapters) for clean separation between business logic and infrastructure
- **Local-first development** — fully runnable on a laptop with Docker Compose, no cloud account required
- **Cloud-portable design** — flip a config switch to swap MongoDB → Cosmos DB, console logging → Application Insights, mock auth → Microsoft Entra ID
- **Pragmatic LLM integration** — caching, rate limiting, structured output validation, and aggressive cost protection
- **Production engineering basics** — CI/CD, observability, ADRs, infrastructure as code

---

## Tech stack

| Layer     | Local                                  | Production (Azure)                 |
| --------- | -------------------------------------- | ---------------------------------- |
| Frontend  | React + Vite + TypeScript + React Flow | Azure Static Web Apps              |
| Backend   | FastAPI (Python 3.11+) in Docker       | Azure Functions (Consumption plan) |
| Database  | MongoDB 7                              | Cosmos DB (MongoDB API)            |
| Cache     | Redis 7                                | Cosmos DB container with TTL       |
| LLM       | OpenAI API (`gpt-4o-mini`, `gpt-4o`)   | Same                               |
| Auth      | Mock JWT provider                      | Microsoft Entra ID via MSAL.js     |
| Telemetry | `structlog` → stdout                   | Application Insights               |
| Secrets   | `.env.local`                           | Azure Key Vault                    |
| CI/CD     | —                                      | GitHub Actions                     |

See [`docs/adr/`](./docs/adr/) for the _why_ behind each choice.

---

## Repository layout

```
.
├── backend/          # FastAPI service (see backend/AGENT.md)
├── frontend/         # React SPA (see frontend/AGENT.md, populated in Batch 2)
├── docs/
│   ├── DESIGN.md             # Source-of-truth spec
│   ├── CODEGEN-WORKFLOW.md   # How AI assistants generate code here
│   └── adr/                  # Architecture Decision Records
├── docker-compose.yml
└── README.md
```

---

## Quickstart (local development)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)
- Git

### Run it

```bash
# 1. Clone
git clone <repo-url>
cd system-design-teacher

# 2. Set up backend env (placeholder OpenAI key is fine for Batch 1 — the LLM adapter is stubbed)
cp backend/.env.example backend/.env.local

# 3. Bring up backend + Mongo + Mongo Express + Redis
docker compose up

# 4. Verify everything is wired correctly
curl http://localhost:8000/health/deep
# → 200 OK with status of every dependency
```

### What's running

| Service       | URL                       | Purpose                                |
| ------------- | ------------------------- | -------------------------------------- |
| Backend API   | http://localhost:8000     | FastAPI + auto OpenAPI docs at `/docs` |
| MongoDB       | mongodb://localhost:27017 | Primary data store                     |
| Mongo Express | http://localhost:8081     | Browse the DB in your browser          |
| Redis         | redis://localhost:6379    | Cache + rate limiter                   |

---

## Development workflow

- **For backend code:** read [`backend/AGENT.md`](./backend/AGENT.md) before making changes.
- **For frontend code:** read [`frontend/AGENT.md`](./frontend/AGENT.md) (added in Batch 2).
- **For AI-assisted code generation:** see [`docs/CODEGEN-WORKFLOW.md`](./docs/CODEGEN-WORKFLOW.md).
- **For the big picture / new features:** [`docs/DESIGN.md`](./docs/DESIGN.md) is the spec.

---

## Project status

| Batch | Goal                                            | Status         |
| ----- | ----------------------------------------------- | -------------- |
| 1     | Foundation: ports, adapters, DI, `/health/deep` | 🚧 In progress |
| 2     | Auth & user (Microsoft login, mocked locally)   | ⏳ Not started |
| 3     | Situation practice flow + rate limiting         | ⏳ Not started |
| 4     | Design canvas + AI feedback (headline feature)  | ⏳ Not started |
| 5     | Azure migration + CI/CD                         | ⏳ Not started |
| 6     | Polish & portfolio (README, ADRs, demo)         | ⏳ Not started |

---

## License

TBD (likely MIT).

---

## Contact

Portfolio project — feedback welcome via GitHub issues.
