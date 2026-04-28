from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "azure"]


class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONGO_", case_sensitive=False)

    uri: str = "mongodb://localhost:27017"
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
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = "local"

    log_level: str = "INFO"

    openai_api_key: str = "sk-REPLACE_ME_WITH_YOUR_KEY"

    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    mongo: MongoSettings = Field(default_factory=MongoSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    microsoft: MicrosoftSettings = Field(default_factory=MicrosoftSettings)
    rate_limits: RateLimitSettings = Field(default_factory=RateLimitSettings)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()