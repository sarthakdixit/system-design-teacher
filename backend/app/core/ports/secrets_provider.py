from __future__ import annotations

from typing import Protocol, runtime_checkable


class SecretNotFoundError(Exception):
    pass


class SecretsError(Exception):
    pass


@runtime_checkable
class SecretsProvider(Protocol):
    async def get_secret(self, name: str) -> str: ...

    async def health_check(self) -> bool: ...
