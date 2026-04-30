from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.adapters.local.mongodb_database import MongoDBDatabase
from app.config.settings import get_settings
from app.core.domain.question import NewQuestion


SEED_FILE = Path(__file__).parent / "seed_questions.json"


def _load_seed_data(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Seed file {path} must contain a JSON array, got {type(data).__name__}")
    return data


def _to_new_question(record: dict) -> NewQuestion:
    return NewQuestion(
        type="situation",
        title=record["title"],
        prompt=record["prompt"],
        category=record["category"],
        difficulty=record["difficulty"],
        tags=record.get("tags", []),
        is_ai_generated=False,
    )


async def _existing_titles(database: MongoDBDatabase) -> set[str]:
    cursor = database._db["questions"].find({"type": "situation"}, {"title": 1})
    documents = await cursor.to_list(length=None)
    return {doc["title"] for doc in documents}


async def main() -> int:
    settings = get_settings()
    database = MongoDBDatabase(uri=settings.mongo.uri, db_name=settings.mongo.db_name)

    try:
        await database.ensure_indexes()

        records = _load_seed_data(SEED_FILE)
        print(f"Loaded {len(records)} records from {SEED_FILE.name}")

        already_seeded = await _existing_titles(database)
        to_insert = [r for r in records if r["title"] not in already_seeded]
        skipped = len(records) - len(to_insert)

        if not to_insert:
            print(f"All {len(records)} questions already seeded. Nothing to do.")
            return 0

        print(f"Inserting {len(to_insert)} new questions ({skipped} already present, skipped).")

        for record in to_insert:
            new_question = _to_new_question(record)
            inserted = await database.questions.insert(new_question)
            print(f"  + {inserted.id}  {inserted.category}/{inserted.difficulty}  {inserted.title[:60]}")

        total = await database.questions.count()
        print(f"\nDone. {len(to_insert)} inserted. Total questions in database: {total}")
        return 0

    finally:
        await database.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))