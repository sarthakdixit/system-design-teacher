from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["local", "azure"] = "local"

    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db_name: str = "sdt"

    redis_url: str = "redis://redis:6379"

    openai_api_key: str = Field(
        default="sk-placeholder",
        description="OpenAI API key. Use a real key for production behavior; the default keeps the app bootable.",
    )
    llm_provider: Literal["auto", "openai", "stub"] = "auto"

    jwt_secret: str = Field(
        default="dev-secret-change-me",
        description="HS256 signing key for our session JWT.",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    microsoft_client_id: str = "dev-client-id"
    microsoft_tenant_id: str = "common"

    rate_limit_situation_daily: int = 5
    rate_limit_design_daily: int = 2
    global_cap_situation_daily: int = 50
    global_cap_design_daily: int = 100

    feedback_cache_ttl_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="How many days a feedback cache entry lives before MongoDB TTL deletes it.",
    )

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    azure_keyvault_url: str = Field(
        default="",
        description="Azure Key Vault URL. Required when ENVIRONMENT=azure.",
    )
    appinsights_connection_string: str = Field(
        default="",
        description="Application Insights connection string. Required when ENVIRONMENT=azure.",
    )

    @computed_field
    @property
    def effective_llm_provider(self) -> Literal["openai", "stub"]:
        if self.llm_provider == "openai":
            return "openai"
        if self.llm_provider == "stub":
            return "stub"
        if self.openai_api_key.startswith("sk-") and not self.openai_api_key.startswith(
            "sk-placeholder"
        ):
            return "openai"
        return "stub"


_KEYVAULT_BACKED_FIELDS = (
    "openai_api_key",
    "jwt_secret",
    "mongo_uri",
    "microsoft_client_id",
    "microsoft_tenant_id",
)


async def _hydrate_from_keyvault(settings: Settings) -> Settings:
    from app.adapters.azure.key_vault_secrets import KeyVaultSecretsProvider

    if not settings.azure_keyvault_url:
        raise RuntimeError(
            "AZURE_KEYVAULT_URL is required when ENVIRONMENT=azure but was not set"
        )

    provider = KeyVaultSecretsProvider(vault_url=settings.azure_keyvault_url)
    overrides: dict[str, str] = {}
    try:
        for field_name in _KEYVAULT_BACKED_FIELDS:
            try:
                overrides[field_name] = await provider.get_secret(field_name.upper())
            except Exception:
                pass
    finally:
        await provider.close()

    if not overrides:
        return settings
    return settings.model_copy(update=overrides)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == "azure":
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return settings
            return loop.run_until_complete(_hydrate_from_keyvault(settings))
        except RuntimeError:
            return asyncio.run(_hydrate_from_keyvault(settings))
    return settings