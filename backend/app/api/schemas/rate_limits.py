from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RateLimitStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_current: int = Field(ge=0)
    user_limit: int = Field(gt=0)
    user_remaining: int = Field(ge=0)
    global_current: int = Field(ge=0)
    global_limit: int = Field(gt=0)
    global_remaining: int = Field(ge=0)
    reset_in_seconds: int = Field(ge=0)


class AllRateLimitsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    situation_fetch: RateLimitStatus
    design_submission: RateLimitStatus