from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health as health_routes
from app.config.container import Container
from app.config.settings import Settings, get_settings


def _build_container(settings: Settings) -> Container:
    container = Container()
    container.config.from_dict(
        {
            "environment": settings.environment,
            "log_level": settings.log_level,
            "mongo": {
                "uri": settings.mongo.uri,
                "db_name": settings.mongo.db_name,
            },
            "redis": {
                "url": settings.redis.url,
            },
        }
    )
    container.wire(modules=[health_routes])
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
        log_level=settings.log_level,
    )

    try:
        yield
    finally:
        try:
            await container.database().close()
        except Exception as exc:  # noqa: BLE001
            telemetry.track_exception(exc, component="database_close")
        try:
            await container.cache().close()
        except Exception as exc:  # noqa: BLE001
            telemetry.track_exception(exc, component="cache_close")

        telemetry.log("info", "app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="System Design Teacher API",
        version="0.1.0",
        description=(
            "Backend for the System Design Teacher platform. "
            "See /health/deep for end-to-end dependency status."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_routes.router)

    return app


app = create_app()