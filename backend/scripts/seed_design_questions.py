from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.adapters.local.mongodb_database import MongoDBDatabase
from app.config.settings import get_settings
from app.core.domain.question import NewQuestion


_SEED_PATH = Path(__file__).resolve().parent / "seed_design_questions.json"


def _load_seed() -> list[dict]:
    with _SEED_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{_SEED_PATH} must contain a JSON array")
    return data


async def _existing_titles(database: MongoDBDatabase) -> set[str]:
    cursor = database._db["questions"].find(
        {"type": "design_system"},
        projection={"title": 1, "_id": 0},
    )
    documents = await cursor.to_list(length=None)
    return {doc["title"] for doc in documents}


async def main() -> int:
    settings = get_settings()
    print(f"MONGO_URI: {settings.mongo_uri}")
    print(f"MONGO_DB_NAME: {settings.mongo_db_name}")

    seed_entries = _load_seed()
    print(f"Loaded {len(seed_entries)} design questions from {_SEED_PATH.name}")

    database = MongoDBDatabase(uri=settings.mongo_uri, db_name=settings.mongo_db_name)
    try:
        await database.ensure_indexes()
        existing = await _existing_titles(database)

        to_insert = [entry for entry in seed_entries if entry["title"] not in existing]

        if not to_insert:
            print(f"All {len(seed_entries)} design questions already seeded. Nothing to do.")
            return 0

        print(f"Inserting {len(to_insert)} new design questions:")
        for entry in to_insert:
            new_question = NewQuestion(
                type="design_system",
                title=entry["title"],
                prompt=entry["prompt"],
                category=entry["category"],
                difficulty=entry["difficulty"],
                tags=entry.get("tags", []),
                is_ai_generated=False,
            )
            inserted = await database.questions.insert(new_question)
            print(f"  + {inserted.title} [{inserted.category}/{inserted.difficulty}]")

        total = await database.questions.count()
        print(f"Done. Total questions in DB (all types): {total}")
        return 0
    finally:
        await database.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))