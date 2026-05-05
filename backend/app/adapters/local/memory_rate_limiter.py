from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from app.core.ports.rate_limiter import RateLimitDecision


@dataclass
class _Counter:
    count: int
    expires_at: float


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._counters: dict[str, _Counter] = {}
        self._lock = asyncio.Lock()

    async def check_and_increment(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if limit <= 0:
            raise ValueError(f"limit must be > 0, got {limit}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds must be > 0, got {window_seconds}")

        now = time.monotonic()
        async with self._lock:
            existing = self._counters.get(key)
            if existing is None or existing.expires_at <= now:
                new_counter = _Counter(count=1, expires_at=now + window_seconds)
                self._counters[key] = new_counter
                return RateLimitDecision(
                    allowed=True,
                    current_count=1,
                    limit=limit,
                    remaining=limit - 1,
                    reset_in_seconds=window_seconds,
                )

            existing.count += 1
            current = existing.count
            reset_in = max(0, int(existing.expires_at - now))
            return RateLimitDecision(
                allowed=current <= limit,
                current_count=current,
                limit=limit,
                remaining=max(0, limit - current),
                reset_in_seconds=reset_in,
            )

    async def peek(self, *, key: str) -> int:
        now = time.monotonic()
        async with self._lock:
            existing = self._counters.get(key)
            if existing is None or existing.expires_at <= now:
                return 0
            return existing.count

    async def health_check(self) -> bool:
        return True
