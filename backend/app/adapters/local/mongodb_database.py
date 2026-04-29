from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError as PyMongoDuplicateKeyError

from app.core.domain.user import NewUser, User
from app.core.ports.database import (
    AttemptRepository,
    DatabaseError,
    DuplicateKeyError,
    FeedbackCacheRepository,
    NotFoundError,
    QuestionRepository,
    UserRepository,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _doc_to_user(doc: dict[str, Any]) -> User:
    return User(
        id=str(doc["_id"]),
        microsoft_oid=doc["microsoft_oid"],
        email=doc["email"],
        display_name=doc["display_name"],
        created_at=doc["created_at"],
        last_login_at=doc["last_login_at"],
    )


class _MongoUserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["users"]

    async def insert(self, new_user: NewUser) -> User:
        document = new_user.model_dump()
        try:
            result = await self._collection.insert_one(document)
        except PyMongoDuplicateKeyError as exc:
            raise DuplicateKeyError(
                f"User with microsoft_oid={new_user.microsoft_oid!r} already exists"
            ) from exc
        document["_id"] = result.inserted_id
        return _doc_to_user(document)

    async def get_by_microsoft_oid(self, microsoft_oid: str) -> User:
        document = await self._collection.find_one({"microsoft_oid": microsoft_oid})
        if document is None:
            raise NotFoundError(f"No user with microsoft_oid={microsoft_oid!r}")
        return _doc_to_user(document)

    async def upsert_on_login(self, new_user: NewUser) -> User:
        now = _utcnow()
        document = await self._collection.find_one_and_update(
            {"microsoft_oid": new_user.microsoft_oid},
            {
                "$set": {
                    "email": new_user.email,
                    "display_name": new_user.display_name,
                    "last_login_at": now,
                },
                "$setOnInsert": {
                    "microsoft_oid": new_user.microsoft_oid,
                    "created_at": new_user.created_at,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return _doc_to_user(document)

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
            return False
        return True


class _MongoQuestionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["questions"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
            return False
        return True


class _MongoAttemptRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["attempts"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
            return False
        return True


class _MongoFeedbackCacheRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["feedback_cache"]

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
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

        self._indexes_ensured = False

    async def ensure_indexes(self) -> None:
        if self._indexes_ensured:
            return
        await self._db["users"].create_index("microsoft_oid", unique=True)
        self._indexes_ensured = True

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
        except Exception:
            return False
        return True

    async def server_info(self) -> dict[str, Any]:
        try:
            info = await self._client.server_info()
        except Exception as exc:
            raise DatabaseError(f"server_info failed: {exc}") from exc
        return {
            "version": info.get("version"),
            "ok": info.get("ok"),
            "db_name": self._db_name,
        }

    async def close(self) -> None:
        self._client.close()