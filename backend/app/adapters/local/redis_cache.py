from __future__ import annotations

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.ports.cache import CacheError


class RedisCache:

    def __init__(self, url: str) -> None:
        self._client: Redis = Redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        try:
            value = await self._client.get(key)
        except RedisError as exc:
            raise CacheError(f"Redis GET failed for key={key!r}: {exc}") from exc
        return value  # type: ignore[no-any-return]

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        try:
            await self._client.set(key, value, ex=ttl_seconds)
        except RedisError as exc:
            raise CacheError(f"Redis SET failed for key={key!r}: {exc}") from exc

    async def delete(self, key: str) -> bool:
        try:
            deleted_count = await self._client.delete(key)
        except RedisError as exc:
            raise CacheError(f"Redis DEL failed for key={key!r}: {exc}") from exc
        return deleted_count > 0

    async def health_check(self) -> bool:
        try:
            return bool(await self._client.ping())
        except RedisError:
            return False
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        await self._client.aclose()