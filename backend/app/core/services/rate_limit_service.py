from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.core.domain.errors import RateLimitExceeded
from app.core.ports.rate_limiter import RateLimitDecision, RateLimiter
from app.core.ports.telemetry import Telemetry


class RateLimitedAction(str, Enum):
    SITUATION_FETCH = "situation_fetch"
    DESIGN_SUBMISSION = "design_submission"


class RateLimitConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    per_user_daily: int
    global_daily: int


class RateLimitOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: RateLimitDecision
    global_: RateLimitDecision


_SECONDS_PER_DAY = 24 * 60 * 60


def _today_utc_string() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _user_key(microsoft_oid: str, action: RateLimitedAction, day: str) -> str:
    return f"user:{microsoft_oid}:{action.value}:{day}"


def _global_key(action: RateLimitedAction, day: str) -> str:
    return f"global:{action.value}:{day}"


class RateLimitService:
    def __init__(
        self,
        *,
        rate_limiter: RateLimiter,
        telemetry: Telemetry,
        configs: dict[RateLimitedAction, RateLimitConfig],
    ) -> None:
        self._rate_limiter = rate_limiter
        self._telemetry = telemetry
        self._configs = configs

    async def check_and_consume(
        self,
        *,
        action: RateLimitedAction,
        microsoft_oid: str,
    ) -> RateLimitOutcome:
        config = self._require_config(action)
        day = _today_utc_string()

        global_decision = await self._rate_limiter.check_and_increment(
            key=_global_key(action, day),
            limit=config.global_daily,
            window_seconds=_SECONDS_PER_DAY,
        )
        if not global_decision.allowed:
            self._telemetry.track_metric(
                "rate_limit_rejection_count",
                1.0,
                layer="global",
                action=action.value,
            )
            raise RateLimitExceeded(
                limit=global_decision.limit,
                reset_in_seconds=global_decision.reset_in_seconds,
            )

        user_decision = await self._rate_limiter.check_and_increment(
            key=_user_key(microsoft_oid, action, day),
            limit=config.per_user_daily,
            window_seconds=_SECONDS_PER_DAY,
        )
        if not user_decision.allowed:
            self._telemetry.track_metric(
                "rate_limit_rejection_count",
                1.0,
                layer="user",
                action=action.value,
            )
            raise RateLimitExceeded(
                limit=user_decision.limit,
                reset_in_seconds=user_decision.reset_in_seconds,
            )

        return RateLimitOutcome(user=user_decision, global_=global_decision)

    async def peek(
        self,
        *,
        action: RateLimitedAction,
        microsoft_oid: str,
    ) -> RateLimitOutcome:
        config = self._require_config(action)
        day = _today_utc_string()

        user_count = await self._rate_limiter.peek(key=_user_key(microsoft_oid, action, day))
        global_count = await self._rate_limiter.peek(key=_global_key(action, day))

        return RateLimitOutcome(
            user=RateLimitDecision(
                allowed=user_count < config.per_user_daily,
                current_count=user_count,
                limit=config.per_user_daily,
                remaining=max(0, config.per_user_daily - user_count),
                reset_in_seconds=_seconds_until_utc_midnight(),
            ),
            global_=RateLimitDecision(
                allowed=global_count < config.global_daily,
                current_count=global_count,
                limit=config.global_daily,
                remaining=max(0, config.global_daily - global_count),
                reset_in_seconds=_seconds_until_utc_midnight(),
            ),
        )

    def _require_config(self, action: RateLimitedAction) -> RateLimitConfig:
        config = self._configs.get(action)
        if config is None:
            raise ValueError(f"No rate-limit config for action {action.value!r}")
        return config


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    seconds_into_day = now.hour * 3600 + now.minute * 60 + now.second
    return _SECONDS_PER_DAY - seconds_into_day