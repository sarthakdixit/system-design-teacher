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
from app.config.settings import get_settings
from app.core.services.attempt_service import AttemptService
from app.core.services.auth_service import AuthService
from app.core.services.design_feedback_service import DesignFeedbackService
from app.core.services.diagram_hash_service import DiagramHashService
from app.core.services.health_service import HealthService
from app.core.services.jwt_service import JWTService
from app.core.services.question_service import QuestionService
from app.core.services.rate_limit_service import RateLimitService


def _make_entra_auth_provider(*, tenant_id: str, client_id: str):
    from app.adapters.azure.entra_auth import EntraAuthProvider

    return EntraAuthProvider(
        tenant_id=tenant_id,
        client_id=client_id,
    )


def _make_app_insights_telemetry(*, connection_string: str):
    from app.adapters.azure.app_insights_telemetry import AppInsightsTelemetry

    return AppInsightsTelemetry(connection_string=connection_string)


def _make_keyvault_secrets(*, vault_url: str):
    from app.adapters.azure.key_vault_secrets import KeyVaultSecretsProvider

    return KeyVaultSecretsProvider(vault_url=vault_url)


def _make_cosmos_database(*, uri: str, db_name: str):
    from app.adapters.azure.cosmos_database import CosmosDatabase

    return CosmosDatabase(uri=uri, db_name=db_name)


def _make_rate_limit_configs(
    *,
    situation_user_daily: int,
    situation_global_daily: int,
    design_user_daily: int,
    design_global_daily: int,
):
    from app.core.services.rate_limit_service import RateLimitConfig, RateLimitedAction

    return {
        RateLimitedAction.SITUATION_FETCH: RateLimitConfig(
            per_user_daily=situation_user_daily,
            global_daily=situation_global_daily,
        ),
        RateLimitedAction.DESIGN_SUBMISSION: RateLimitConfig(
            per_user_daily=design_user_daily,
            global_daily=design_global_daily,
        ),
    }


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    settings = providers.Singleton(get_settings)

    secrets = providers.Selector(
        config.environment,
        local=providers.Singleton(EnvSecretsProvider),
        azure=providers.Singleton(
            _make_keyvault_secrets,
            vault_url=config.azure_keyvault_url,
        ),
    )

    telemetry = providers.Selector(
        config.environment,
        local=providers.Singleton(ConsoleTelemetry),
        azure=providers.Singleton(
            _make_app_insights_telemetry,
            connection_string=config.appinsights_connection_string,
        ),
    )

    database = providers.Selector(
        config.environment,
        local=providers.Singleton(
            MongoDBDatabase,
            uri=config.mongo_uri,
            db_name=config.mongo_db_name,
        ),
        azure=providers.Singleton(
            _make_cosmos_database,
            uri=config.mongo_uri,
            db_name=config.mongo_db_name,
        ),
    )

    cache = providers.Singleton(
        RedisCache,
        url=config.redis_url,
    )

    rate_limiter = providers.Singleton(MemoryRateLimiter)

    auth_provider = providers.Selector(
        config.environment,
        local=providers.Singleton(MockAuthProvider),
        azure=providers.Singleton(
            _make_entra_auth_provider,
            tenant_id=config.microsoft_tenant_id,
            client_id=config.microsoft_client_id,
        ),
    )

    llm_provider = providers.Selector(
        config.effective_llm_provider,
        openai=providers.Singleton(
            OpenAILLMProvider,
            api_key=config.openai_api_key,
        ),
        stub=providers.Singleton(StubLLMProvider),
    )

    jwt_service = providers.Singleton(
        JWTService,
        secret=config.jwt_secret,
        algorithm=config.jwt_algorithm,
        expiry_hours=config.jwt_expiry_hours,
    )

    rate_limit_configs = providers.Singleton(
        _make_rate_limit_configs,
        situation_user_daily=config.rate_limit_situation_daily,
        situation_global_daily=config.global_cap_situation_daily,
        design_user_daily=config.rate_limit_design_daily,
        design_global_daily=config.global_cap_design_daily,
    )

    rate_limit_service = providers.Factory(
        RateLimitService,
        rate_limiter=rate_limiter,
        telemetry=telemetry,
        configs=rate_limit_configs,
    )

    auth_service = providers.Factory(
        AuthService,
        auth_provider=auth_provider,
        database=database,
        jwt_service=jwt_service,
        telemetry=telemetry,
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
        database=database,
        cache=cache,
        rate_limiter=rate_limiter,
        llm_provider=llm_provider,
        auth_provider=auth_provider,
        secrets_provider=secrets,
        telemetry=telemetry,
    )
