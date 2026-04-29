from __future__ import annotations

from dependency_injector import containers, providers

from app.adapters.local.console_telemetry import ConsoleTelemetry
from app.adapters.local.env_secrets import EnvSecretsProvider
from app.adapters.local.memory_rate_limiter import MemoryRateLimiter
from app.adapters.local.mock_auth import MockAuthProvider
from app.adapters.local.mongodb_database import MongoDBDatabase
from app.adapters.local.redis_cache import RedisCache
from app.adapters.local.stub_llm import StubLLMProvider
from app.core.services.auth_service import AuthService
from app.core.services.health_service import HealthService
from app.core.services.jwt_service import JWTService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    auth_provider = providers.Singleton(MockAuthProvider)

    database = providers.Singleton(
        MongoDBDatabase,
        uri=config.mongo.uri,
        db_name=config.mongo.db_name,
    )

    llm_provider = providers.Singleton(StubLLMProvider)

    cache = providers.Singleton(
        RedisCache,
        url=config.redis.url,
    )

    rate_limiter = providers.Singleton(MemoryRateLimiter)

    telemetry = providers.Singleton(
        ConsoleTelemetry,
        level=config.log_level,
    )

    secrets_provider = providers.Singleton(EnvSecretsProvider)

    jwt_service = providers.Singleton(
        JWTService,
        secret=config.jwt.secret,
        algorithm=config.jwt.algorithm,
        expiry_hours=config.jwt.expiry_hours,
    )

    auth_service = providers.Factory(
        AuthService,
        auth_provider=auth_provider,
        database=database,
        jwt_service=jwt_service,
        telemetry=telemetry,
    )

    health_service = providers.Factory(
        HealthService,
        auth_provider=auth_provider,
        database=database,
        llm_provider=llm_provider,
        cache=cache,
        rate_limiter=rate_limiter,
        telemetry=telemetry,
        secrets_provider=secrets_provider,
    )