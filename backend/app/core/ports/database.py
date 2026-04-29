from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.domain.user import NewUser, User


class DatabaseError(Exception):
    pass


class NotFoundError(DatabaseError):
    pass


class DuplicateKeyError(DatabaseError):
    pass


@runtime_checkable
class UserRepository(Protocol):
    async def insert(self, new_user: NewUser) -> User: ...

    async def get_by_microsoft_oid(self, microsoft_oid: str) -> User: ...

    async def upsert_on_login(self, new_user: NewUser) -> User: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class QuestionRepository(Protocol):
    async def health_check(self) -> bool: ...


@runtime_checkable
class AttemptRepository(Protocol):
    async def health_check(self) -> bool: ...


@runtime_checkable
class FeedbackCacheRepository(Protocol):
    async def health_check(self) -> bool: ...


@runtime_checkable
class Database(Protocol):
    @property
    def users(self) -> UserRepository: ...

    @property
    def questions(self) -> QuestionRepository: ...

    @property
    def attempts(self) -> AttemptRepository: ...

    @property
    def feedback_cache(self) -> FeedbackCacheRepository: ...

    async def health_check(self) -> bool: ...

    async def server_info(self) -> dict[str, Any]: ...