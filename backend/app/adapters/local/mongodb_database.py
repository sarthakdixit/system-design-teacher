from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.ports.database import (
    AttemptRepository,
    DatabaseError,
    FeedbackCacheRepository,
    QuestionRepository,
    UserRepository,
)


class _MongoUserRepository:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["users"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:  # noqa: BLE001
            return False
        return True


class _MongoQuestionRepository:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["questions"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:  # noqa: BLE001
            return False
        return True


class _MongoAttemptRepository:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["attempts"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:  # noqa: BLE001
            return False
        return True


class _MongoFeedbackCacheRepository:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["feedback_cache"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:  # noqa: BLE001
            return False
        return True


class MongoDBDatabase:

    def __init__(self, uri: str, db_name: str = "sdt") -> None:
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(uri)
        self._db: AsyncIOMotorDatabase = self._client[db_name]
        self._db_name = db_name

        self._users = _MongoUserRepository(self._db)
        self._questions = _MongoQuestionRepository(self._db)
        self._attempts = _MongoAttemptRepository(self._db)
        self._feedback_cache = _MongoFeedbackCacheRepository(self._db)

    @property
    def users(self) -> UserRepository:
        return self._users

    @property
    def questions(self) -> QuestionRepository:
        return self._questions

    @property
    def attempts(self) -> AttemptRepository:
        return self._attempts

    @property
    def feedback_cache(self) -> FeedbackCacheRepository:
        return self._feedback_cache

    async def health_check(self) -> bool:
        try:
            await self._db.command("ping")
        except Exception:  # noqa: BLE001
            return False
        return True

    async def server_info(self) -> dict[str, Any]:
        try:
            info = await self._client.server_info()
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(f"server_info failed: {exc}") from exc

        return {
            "version": info.get("version"),
            "ok": info.get("ok"),
            "db_name": self._db_name,
        }

    async def close(self) -> None:
        self._client.close()