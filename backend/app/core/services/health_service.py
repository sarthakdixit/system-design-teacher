from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.ports.auth_provider import AuthProvider
from app.core.ports.cache import Cache
from app.core.ports.database import Database
from app.core.ports.llm_provider import LLMProvider
from app.core.ports.rate_limiter import RateLimiter
from app.core.ports.secrets_provider import SecretsProvider
from app.core.ports.telemetry import Telemetry

ComponentStatus = Literal["ok", "error"]


class ComponentHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ComponentStatus
    detail: str | None = None


class DeepHealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ComponentStatus
    environment: str
    components: dict[str, ComponentHealth]


class HealthService:
    def __init__(
        self,
        *,
        auth_provider: AuthProvider,
        database: Database,
        llm_provider: LLMProvider,
        cache: Cache,
        rate_limiter: RateLimiter,
        telemetry: Telemetry,
        secrets_provider: SecretsProvider,
    ) -> None:
        self._auth_provider = auth_provider
        self._database = database
        self._llm_provider = llm_provider
        self._cache = cache
        self._rate_limiter = rate_limiter
        self._telemetry = telemetry
        self._secrets_provider = secrets_provider

    async def check_deep(self, *, environment: str) -> DeepHealthReport:
        results = await asyncio.gather(
            self._safe_check("auth", self._auth_provider.health_check),
            self._safe_check("database", self._database.health_check),
            self._safe_check("llm", self._llm_provider.health_check),
            self._safe_check("cache", self._cache.health_check),
            self._safe_check("rate_limiter", self._rate_limiter.health_check),
            self._safe_check("telemetry", self._telemetry.health_check),
            self._safe_check("secrets", self._secrets_provider.health_check),
        )

        components = dict(results)
        overall: ComponentStatus = (
            "ok" if all(c.status == "ok" for c in components.values()) else "error"
        )

        self._telemetry.log(
            "info" if overall == "ok" else "warning",
            "health_check_completed",
            overall=overall,
            unhealthy=[name for name, c in components.items() if c.status != "ok"],
        )

        return DeepHealthReport(
            status=overall,
            environment=environment,
            components=components,
        )

    async def _safe_check(
        self,
        name: str,
        check: asyncio.Future[bool] | object,
    ) -> tuple[str, ComponentHealth]:
        try:
            ok: bool = await check()  # type: ignore[operator, misc]
            if ok:
                return name, ComponentHealth(status="ok")
            return name, ComponentHealth(status="error", detail="health_check returned False")
        except Exception as exc:
            self._telemetry.track_exception(exc, component=name)
            return name, ComponentHealth(status="error", detail=str(exc) or type(exc).__name__)
