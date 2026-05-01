from __future__ import annotations

from dependency_injector import containers, providers

from app.adapters.local.console_telemetry import ConsoleTelemetry
from app.adapters.local.env_secrets import EnvSecretsProvider
from app.adapters.local.memory_rate_limiter import MemoryRateLimiter
from app.adapters.local.mock_auth import MockAuthProvider
from app.adapters.local.mongodb_database import MongoDBDatabase
from app.adapters.local.openai_llm import OpenAILLMProvider
from app.adapters.local.redis_cache import RedisCache
from app.adapters.local.stub_llm import StubLLMProvider
from app.core.services.attempt_service import AttemptService
from app.core.services.auth_service import AuthService
from app.core.services.design_feedback_service import DesignFeedbackService
from app.core.services.diagram_hash_service import DiagramHashService
from app.core.services.health_service import HealthService
from app.core.services.jwt_service import JWTService
from app.core.services.question_service import QuestionService
from app.core.services.rate_limit_service import (
    RateLimitConfig,
    RateLimitedAction,
    RateLimitService,
)


def build_rate_limit_configs(
    *,
    situation_per_user: int,
    situation_global: int,
    design_per_user: int,
    design_global: int,
) -> dict[RateLimitedAction, RateLimitConfig]:
    return {
        RateLimitedAction.SITUATION_FETCH: RateLimitConfig(
            per_user_daily=situation_per_user,
            global_daily=situation_global,
        ),
        RateLimitedAction.DESIGN_SUBMISSION: RateLimitConfig(
            per_user_daily=design_per_user,
            global_daily=design_global,
        ),
    }


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    auth_provider = providers.Singleton(MockAuthProvider)

    database = providers.Singleton(
        MongoDBDatabase,
        uri=config.mongo.uri,
        db_name=config.mongo.db_name,
    )

    llm_provider = providers.Selector(
        config.llm_provider,
        openai=providers.Singleton(
            OpenAILLMProvider,
            api_key=config.openai_api_key,
        ),
        stub=providers.Singleton(StubLLMProvider),
    )

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

    rate_limit_configs = providers.Singleton(
        build_rate_limit_configs,
        situation_per_user=config.rate_limits.rate_limit_situation_daily,
        situation_global=config.rate_limits.global_cap_situation_daily,
        design_per_user=config.rate_limits.rate_limit_design_daily,
        design_global=config.rate_limits.global_cap_design_daily,
    )

    rate_limit_service = providers.Factory(
        RateLimitService,
        rate_limiter=rate_limiter,
        telemetry=telemetry,
        configs=rate_limit_configs,
    )

    question_service = providers.Factory(
        QuestionService,
        database=database,
        rate_limit_service=rate_limit_service,
        telemetry=telemetry,
    )

    attempt_service = providers.Factory(
        AttemptService,
        database=database,
        telemetry=telemetry,
    )

    diagram_hash_service = providers.Singleton(DiagramHashService)

    design_feedback_service = providers.Factory(
        DesignFeedbackService,
        database=database,
        llm_provider=llm_provider,
        rate_limit_service=rate_limit_service,
        diagram_hash_service=diagram_hash_service,
        telemetry=telemetry,
        cache_ttl_days=config.feedback_cache_ttl_days,
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