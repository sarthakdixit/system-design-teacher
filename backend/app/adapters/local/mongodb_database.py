from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError as PyMongoDuplicateKeyError

from app.core.domain.attempt import Attempt, AttemptType, NewAttempt
from app.core.domain.design_feedback import (
    CachedFeedback,
    DesignFeedback,
    NewCachedFeedback,
)
from app.core.domain.question import Difficulty, NewQuestion, Question, QuestionType
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
    return datetime.now(UTC)


def _to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise NotFoundError(f"Invalid id format: {value!r}") from exc


def _doc_to_user(doc: dict[str, Any]) -> User:
    return User(
        id=str(doc["_id"]),
        microsoft_oid=doc["microsoft_oid"],
        email=doc["email"],
        display_name=doc["display_name"],
        created_at=doc["created_at"],
        last_login_at=doc["last_login_at"],
    )


def _doc_to_question(doc: dict[str, Any]) -> Question:
    return Question(
        id=str(doc["_id"]),
        type=doc["type"],
        title=doc["title"],
        prompt=doc["prompt"],
        category=doc["category"],
        difficulty=doc["difficulty"],
        reference_answer=doc.get("reference_answer"),
        tags=doc.get("tags", []),
        is_ai_generated=doc.get("is_ai_generated", False),
        created_at=doc["created_at"],
    )


def _doc_to_attempt(doc: dict[str, Any]) -> Attempt:
    return Attempt(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        question_id=doc["question_id"],
        type=doc["type"],
        user_notes=doc.get("user_notes"),
        created_at=doc["created_at"],
    )


def _doc_to_cached_feedback(doc: dict[str, Any]) -> CachedFeedback:
    return CachedFeedback(
        key=doc["key"],
        feedback=DesignFeedback.model_validate(doc["feedback"]),
        hit_count=doc.get("hit_count", 0),
        created_at=doc["created_at"],
        expires_at=doc["expires_at"],
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

    async def insert(self, new_question: NewQuestion) -> Question:
        document = new_question.model_dump()
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return _doc_to_question(document)

    async def get_by_id(self, question_id: str) -> Question:
        oid = _to_object_id(question_id)
        document = await self._collection.find_one({"_id": oid})
        if document is None:
            raise NotFoundError(f"No question with id={question_id!r}")
        return _doc_to_question(document)

    async def random_by_filter(
        self,
        *,
        type: QuestionType,
        category: str | None = None,
        difficulty: Difficulty | None = None,
    ) -> Question:
        match: dict[str, Any] = {"type": type}
        if category is not None:
            match["category"] = category
        if difficulty is not None:
            match["difficulty"] = difficulty

        pipeline: list[dict[str, Any]] = [
            {"$match": match},
            {"$sample": {"size": 1}},
        ]
        cursor = self._collection.aggregate(pipeline)
        documents = await cursor.to_list(length=1)
        if not documents:
            raise NotFoundError(
                f"No question matching type={type!r}, category={category!r}, difficulty={difficulty!r}"
            )
        return _doc_to_question(documents[0])

    async def update_reference_answer(self, question_id: str, reference_answer: str) -> Question:
        oid = _to_object_id(question_id)
        document = await self._collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"reference_answer": reference_answer}},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            raise NotFoundError(f"No question with id={question_id!r}")
        return _doc_to_question(document)

    async def list_missing_reference_answer(self, type: QuestionType) -> list[Question]:
        cursor = self._collection.find(
            {
                "type": type,
                "$or": [
                    {"reference_answer": {"$exists": False}},
                    {"reference_answer": None},
                ],
            }
        )
        documents = await cursor.to_list(length=None)
        return [_doc_to_question(doc) for doc in documents]

    async def count(self) -> int:
        return await self._collection.count_documents({})

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
            return False
        return True


class _MongoAttemptRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["attempts"]

    async def insert(self, new_attempt: NewAttempt) -> Attempt:
        document = new_attempt.model_dump()
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return _doc_to_attempt(document)

    async def list_by_user(
        self,
        *,
        user_id: str,
        attempt_type: AttemptType | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> list[Attempt]:
        match: dict[str, Any] = {"user_id": user_id}
        if attempt_type is not None:
            match["type"] = attempt_type

        cursor = self._collection.find(match).sort("created_at", DESCENDING).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [_doc_to_attempt(doc) for doc in documents]

    async def count_by_user(
        self,
        *,
        user_id: str,
        attempt_type: AttemptType | None = None,
    ) -> int:
        match: dict[str, Any] = {"user_id": user_id}
        if attempt_type is not None:
            match["type"] = attempt_type
        return await self._collection.count_documents(match)

    async def health_check(self) -> bool:
        try:
            await self._collection.estimated_document_count()
        except Exception:
            return False
        return True


class _MongoFeedbackCacheRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["feedback_cache"]

    async def get(self, key: str) -> CachedFeedback:
        document = await self._collection.find_one({"key": key})
        if document is None:
            raise NotFoundError(f"No cached feedback for key={key!r}")
        return _doc_to_cached_feedback(document)

    async def insert(self, new_entry: NewCachedFeedback) -> CachedFeedback:
        document = {
            "key": new_entry.key,
            "feedback": new_entry.feedback.model_dump(),
            "hit_count": new_entry.hit_count,
            "created_at": new_entry.created_at,
            "expires_at": new_entry.expires_at,
        }
        try:
            await self._collection.insert_one(document)
        except PyMongoDuplicateKeyError as exc:
            raise DuplicateKeyError(
                f"Feedback cache entry with key={new_entry.key!r} already exists"
            ) from exc
        return _doc_to_cached_feedback(document)

    async def increment_hit_count(self, key: str) -> None:
        await self._collection.update_one(
            {"key": key},
            {"$inc": {"hit_count": 1}},
        )

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
        await self._db["questions"].create_index([("type", 1), ("difficulty", 1), ("category", 1)])
        await self._db["attempts"].create_index([("user_id", 1), ("created_at", DESCENDING)])
        await self._db["feedback_cache"].create_index("key", unique=True)
        await self._db["feedback_cache"].create_index(
            "expires_at",
            expireAfterSeconds=0,
        )
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
