from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class RateLimitDecision(BaseModel):

    model_config = ConfigDict(frozen=True)

    allowed: bool

    current_count: int = Field(ge=0)

    limit: int = Field(gt=0)

    remaining: int = Field(ge=0)

    reset_in_seconds: int = Field(ge=0)


class RateLimitError(Exception):
    pass


@runtime_checkable
class RateLimiter(Protocol):

    async def check_and_increment(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        ...

    async def peek(self, *, key: str) -> int:
        ...

    async def health_check(self) -> bool:
        ...