# ---------------------------------------------------------------------------
# Backend image for System Design Teacher.
#
# Multi-stage build:
#   stage 1 (builder): install dependencies into a venv
#   stage 2 (runtime): copy venv + app code into a slim runtime image
#
# Local dev: docker-compose.yml mounts ./backend/app over /app/app for hot reload,
# so this Dockerfile is also fine for development as-is.
# ---------------------------------------------------------------------------

ARG PYTHON_VERSION=3.12

# ---------- Stage 1: builder ----------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for any package that needs to compile (e.g., hiredis).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy dependency manifest first to maximize Docker layer caching.
COPY pyproject.toml ./

# Create a venv and install runtime + dev dependencies.
# Dev deps included so pytest and ruff are available in the image (small, worth it).
# Fail fast: if metadata generation breaks, surface the real error instead of
# masking it behind a fallback that hits the same problem.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install ".[dev]"


# ---------- Stage 2: runtime ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Non-root user for runtime.
RUN groupadd --system app && useradd --system --gid app --create-home app

# Copy the prebuilt venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy application source. (In compose, ./backend/app is mounted on top of /app/app
# for live reload — these COPYs serve `docker build` and CI use cases.)
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app app ./app
COPY --chown=app:app tests ./tests

USER app

EXPOSE 8000

# Healthcheck hits the shallow /health endpoint defined in api/routes/health.py.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status == 200 else 1)"

# --reload is fine here because the source dir is volume-mounted in compose.
# For production (Azure Functions in Batch 5) this CMD is replaced.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]