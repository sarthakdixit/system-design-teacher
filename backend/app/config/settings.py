from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "azure"]
LLMProviderName = Literal["openai", "stub"]

_OPENAI_PLACEHOLDER = "sk-REPLACE_ME_WITH_YOUR_KEY"
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONGO_", case_sensitive=False)

    uri: str = "mongodb://localhost:27018"
    db_name: str = "sdt"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", case_sensitive=False)

    url: str = "redis://localhost:6379"


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_", case_sensitive=False)

    secret: str = "dev-only-do-not-use-in-prod-replace-me"
    algorithm: str = "HS256"
    expiry_hours: int = 24


class MicrosoftSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MICROSOFT_", case_sensitive=False)

    client_id: str = "dev-placeholder"
    tenant_id: str = "common"


class RateLimitSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    rate_limit_situation_daily: int = Field(default=5, ge=1)
    rate_limit_design_daily: int = Field(default=2, ge=1)
    global_cap_situation_daily: int = Field(default=50, ge=1)
    global_cap_design_daily: int = Field(default=100, ge=1)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = "local"

    log_level: str = "INFO"

    openai_api_key: str = _OPENAI_PLACEHOLDER

    llm_provider: LLMProviderName | None = Field(
        default=None,
        description=(
            "Which LLM adapter the DI container should use. "
            "Defaults to 'openai' if OPENAI_API_KEY is set to a real value, otherwise 'stub'."
        ),
    )

    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    mongo: MongoSettings = Field(default_factory=MongoSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    microsoft: MicrosoftSettings = Field(default_factory=MicrosoftSettings)
    rate_limits: RateLimitSettings = Field(default_factory=RateLimitSettings)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def effective_llm_provider(self) -> LLMProviderName:
        if self.llm_provider is not None:
            return self.llm_provider
        if self.openai_api_key and self.openai_api_key != _OPENAI_PLACEHOLDER:
            return "openai"
        return "stub"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()