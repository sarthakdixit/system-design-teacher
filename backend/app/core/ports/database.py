from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.domain.attempt import Attempt, AttemptType, NewAttempt
from app.core.domain.design_feedback import CachedFeedback, NewCachedFeedback
from app.core.domain.question import Difficulty, NewQuestion, Question, QuestionType
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
    async def insert(self, new_question: NewQuestion) -> Question: ...

    async def get_by_id(self, question_id: str) -> Question: ...

    async def random_by_filter(
        self,
        *,
        type: QuestionType,
        category: str | None = None,
        difficulty: Difficulty | None = None,
    ) -> Question: ...

    async def update_reference_answer(
        self, question_id: str, reference_answer: str
    ) -> Question: ...

    async def list_missing_reference_answer(self, type: QuestionType) -> list[Question]: ...

    async def count(self) -> int: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class AttemptRepository(Protocol):
    async def insert(self, new_attempt: NewAttempt) -> Attempt: ...

    async def list_by_user(
        self,
        *,
        user_id: str,
        attempt_type: AttemptType | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> list[Attempt]: ...

    async def count_by_user(
        self, *, user_id: str, attempt_type: AttemptType | None = None
    ) -> int: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class FeedbackCacheRepository(Protocol):
    async def get(self, key: str) -> CachedFeedback: ...

    async def insert(self, new_entry: NewCachedFeedback) -> CachedFeedback: ...

    async def increment_hit_count(self, key: str) -> None: ...

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

    async def ensure_indexes(self) -> None: ...
