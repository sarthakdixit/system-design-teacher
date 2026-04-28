from __future__ import annotations

from app.core.ports.auth_provider import AuthenticatedUser, AuthError

_MOCK_USER = AuthenticatedUser(
    microsoft_oid="00000000-0000-0000-0000-000000000001",
    email="dev.user@example.com",
    display_name="Dev User",
)


class MockAuthProvider:

    async def verify_token(self, token: str) -> AuthenticatedUser:
        if not token or not token.strip():
            raise AuthError("Empty token")
        return _MOCK_USER

    async def health_check(self) -> bool:
        return True