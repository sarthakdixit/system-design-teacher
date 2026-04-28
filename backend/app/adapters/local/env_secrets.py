from __future__ import annotations

import os

from app.core.ports.secrets_provider import SecretNotFoundError


def _to_env_name(secret_name: str) -> str:
    return secret_name.upper().replace("-", "_")


class EnvSecretsProvider:

    async def get_secret(self, name: str) -> str:
        env_name = _to_env_name(name)
        value = os.environ.get(env_name)
        if value is None:
            raise SecretNotFoundError(
                f"Secret {name!r} not found in environment (looked for ${env_name})"
            )
        return value

    async def health_check(self) -> bool:
        return True