from __future__ import annotations


class DomainError(Exception):
    pass


class AuthenticationFailed(DomainError):
    pass


class TokenExpired(AuthenticationFailed):
    pass


class TokenInvalid(AuthenticationFailed):
    pass


class UserNotFound(DomainError):
    pass


class RateLimitExceeded(DomainError):
    def __init__(self, *, limit: int, reset_in_seconds: int) -> None:
        super().__init__(f"Rate limit of {limit} exceeded; resets in {reset_in_seconds}s")
        self.limit = limit
        self.reset_in_seconds = reset_in_seconds