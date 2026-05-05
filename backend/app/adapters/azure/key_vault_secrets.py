from __future__ import annotations

import asyncio
import re

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
)
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from app.core.ports.secrets_provider import SecretsProvider


_VALID_SECRET_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


class SecretNotFoundError(Exception):
    pass


class KeyVaultSecretsProvider(SecretsProvider):
    def __init__(self, *, vault_url: str) -> None:
        self._vault_url = vault_url
        self._credential: DefaultAzureCredential | None = None
        self._client: SecretClient | None = None
        self._cache: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def get_secret(self, name: str) -> str:
        if name in self._cache:
            return self._cache[name]

        async with self._lock:
            if name in self._cache:
                return self._cache[name]

            client = await self._ensure_client()
            keyvault_name = self._to_keyvault_name(name)
            try:
                secret = await client.get_secret(keyvault_name)
            except ResourceNotFoundError as exc:
                raise SecretNotFoundError(
                    f"Secret {name!r} (Key Vault name {keyvault_name!r}) not found"
                ) from exc
            except ClientAuthenticationError as exc:
                raise SecretNotFoundError(
                    f"Failed to authenticate to Key Vault: {exc}"
                ) from exc
            except HttpResponseError as exc:
                raise SecretNotFoundError(
                    f"Failed to read secret {name!r}: {exc}"
                ) from exc

            if secret.value is None:
                raise SecretNotFoundError(f"Secret {name!r} has no value")

            self._cache[name] = secret.value
            return secret.value

    async def health_check(self) -> bool:
        try:
            client = await self._ensure_client()
            properties = client.list_properties_of_secrets(max_page_size=1)
            async for _ in properties:
                break
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._credential is not None:
            await self._credential.close()
            self._credential = None

    async def _ensure_client(self) -> SecretClient:
        if self._client is not None:
            return self._client
        self._credential = DefaultAzureCredential()
        self._client = SecretClient(vault_url=self._vault_url, credential=self._credential)
        return self._client

    def _to_keyvault_name(self, name: str) -> str:
        if not _VALID_SECRET_NAME.match(name):
            raise ValueError(
                f"Secret name {name!r} must match {_VALID_SECRET_NAME.pattern}"
            )
        return name.replace("_", "-").lower().replace("__", "-")