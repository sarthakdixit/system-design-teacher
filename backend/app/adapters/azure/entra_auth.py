from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from app.core.ports.auth_provider import AuthenticatedUser, AuthError


_JWKS_CACHE_TTL = timedelta(hours=1)
_HTTPX_TIMEOUT = 10.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EntraAuthProvider:
    def __init__(self, *, tenant_id: str, client_id: str) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id

        self._jwks_url = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        self._issuer_specific = (
            f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        )
        self._jwks_client: PyJWKClient | None = None
        self._jwks_fetched_at: datetime | None = None
        self._jwks_lock = asyncio.Lock()

    async def verify_token(self, token: str) -> AuthenticatedUser:
        if not token or not token.strip():
            raise AuthError("Empty token")

        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:
            raise AuthError(f"Malformed token header: {exc}") from exc

        signing_key = await self._get_signing_key(unverified_header.get("kid"))

        try:
            claims = jwt.decode(
                token,
                key=signing_key,
                algorithms=["RS256"],
                audience=self._client_id,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": False,
                    "require": ["exp", "iat", "aud"],
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Microsoft token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError(f"Microsoft token validation failed: {exc}") from exc

        self._validate_issuer(claims.get("iss"))

        return self._claims_to_user(claims)

    async def health_check(self) -> bool:
        try:
            await self._ensure_jwks_client()
            return self._jwks_client is not None
        except Exception:
            return False

    async def _get_signing_key(self, kid: str | None) -> Any:
        if not kid:
            raise AuthError("Token header missing 'kid' claim")

        await self._ensure_jwks_client()
        client = self._jwks_client
        if client is None:
            raise AuthError("JWKS client unavailable")

        try:
            return await asyncio.to_thread(client.get_signing_key, kid)
        except jwt.PyJWKClientError as exc:
            raise AuthError(f"Unknown signing key '{kid}': {exc}") from exc

    async def _ensure_jwks_client(self) -> None:
        async with self._jwks_lock:
            if self._jwks_client is not None and self._jwks_fetched_at is not None:
                age = _utcnow() - self._jwks_fetched_at
                if age < _JWKS_CACHE_TTL:
                    return

            try:
                async with httpx.AsyncClient(timeout=_HTTPX_TIMEOUT) as http:
                    response = await http.get(self._jwks_url)
                    response.raise_for_status()
            except httpx.HTTPError as exc:
                raise AuthError(
                    f"Failed to fetch JWKS from Microsoft: {exc}"
                ) from exc

            self._jwks_client = PyJWKClient(self._jwks_url, cache_keys=True)
            self._jwks_fetched_at = _utcnow()

    def _validate_issuer(self, issuer: str | None) -> None:
        if issuer is None:
            raise AuthError("Token missing 'iss' claim")

        if issuer == self._issuer_specific:
            return
        if (
            self._tenant_id in {"common", "organizations", "consumers"}
            and issuer.startswith("https://login.microsoftonline.com/")
            and issuer.endswith("/v2.0")
        ):
            return

        raise AuthError(
            f"Token issuer {issuer!r} does not match expected for tenant "
            f"{self._tenant_id!r}"
        )

    def _claims_to_user(self, claims: dict[str, Any]) -> AuthenticatedUser:
        oid = claims.get("oid")
        if not oid:
            raise AuthError("Token missing 'oid' claim")

        email = (
            claims.get("preferred_username")
            or claims.get("email")
            or claims.get("upn")
        )
        if not email:
            raise AuthError("Token missing email-like claim")

        display_name = claims.get("name") or email.split("@")[0]

        return AuthenticatedUser(
            microsoft_oid=oid,
            email=email,
            display_name=display_name,
        )