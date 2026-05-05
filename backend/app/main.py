from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import deps as auth_deps
from app.api.exceptions import register_exception_handlers
from app.api.routes import attempts as attempts_routes
from app.api.routes import auth as auth_routes
from app.api.routes import health as health_routes
from app.api.routes import questions as questions_routes
from app.api.routes import rate_limits as rate_limits_routes
from app.config.container import Container
from app.config.settings import Settings, get_settings


def _build_container(settings: Settings) -> Container:
    container = Container()
    container.config.from_dict(settings.model_dump())
    container.wire(
        modules=[
            health_routes,
            auth_routes,
            auth_deps,
            questions_routes,
            attempts_routes,
            rate_limits_routes,
        ]
    )
    return container


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    container = _build_container(settings)
    app.state.container = container

    telemetry = container.telemetry()
    telemetry.log(
        "info",
        "app_starting",
        environment=settings.environment,
        llm_provider=settings.effective_llm_provider,
        feedback_cache_ttl_days=settings.feedback_cache_ttl_days,
    )

    database = container.database()
    try:
        await database.ensure_indexes()
        telemetry.log("info", "indexes_ensured")
    except Exception as exc:
        telemetry.track_exception(exc, component="ensure_indexes")

    try:
        yield
    finally:
        try:
            await container.database().close()
        except Exception as exc:
            telemetry.track_exception(exc, component="database_close")
        try:
            await container.cache().close()
        except Exception as exc:
            telemetry.track_exception(exc, component="cache_close")
        telemetry.log("info", "app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="System Design Teacher API",
        version="0.5.0",
        description=(
            "Backend for the System Design Teacher platform. "
            "See /health/deep for end-to-end dependency status."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(questions_routes.router)
    app.include_router(attempts_routes.router)
    app.include_router(rate_limits_routes.router)

    return app


app = create_app()