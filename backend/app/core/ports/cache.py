from __future__ import annotations

from typing import Protocol, runtime_checkable


class CacheError(Exception):
    pass


@runtime_checkable
class Cache(Protocol):

    async def get(self, key: str) -> str | None:
        ...

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        ...

    async def delete(self, key: str) -> bool:
        ...

    async def health_check(self) -> bool:
        ...
        ...