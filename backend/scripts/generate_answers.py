from __future__ import annotations

import argparse
import asyncio
import sys

from app.adapters.local.mongodb_database import MongoDBDatabase
from app.adapters.local.openai_llm import OpenAILLMProvider
from app.config.settings import get_settings
from app.core.domain.question import Question
from app.core.ports.llm_provider import LLMMessage, LLMProvider, LLMUsage


_PLACEHOLDER_API_KEY = "sk-REPLACE_ME_WITH_YOUR_KEY"
_MODEL = "gpt-4o"
_MAX_CONCURRENCY = 3
_PROMPT_TOKEN_COST_PER_1M = 2.50
_COMPLETION_TOKEN_COST_PER_1M = 10.00


SYSTEM_PROMPT = """You are a senior software engineer who has spent years interviewing candidates and \
has been on both sides of system-design conversations. Write detailed, well-structured reference \
answers to system-design situation questions for engineers preparing for interviews.

Your answer should:
- Open with a one-sentence summary of the core insight or trade-off.
- Walk through the reasoning a strong candidate would use, including alternatives considered.
- Include specific technologies, data structures, or patterns by name where relevant.
- Highlight the trade-offs explicitly — what does each choice give up?
- Close with what an interviewer is looking for (depth, follow-up questions, common mistakes).

Use clear, well-organized markdown. Aim for roughly 400–700 words. Be concrete and pragmatic — \
avoid hand-wavy generalities. Assume the reader is a working engineer, not a beginner."""


def _build_messages(question: Question) -> list[LLMMessage]:
    user_prompt = f"""Difficulty level: {question.difficulty}
Category: {question.category}

Question:
{question.prompt}

Write a detailed reference answer following the guidance in the system prompt."""
    return [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_prompt),
    ]


def _estimate_cost(usage: LLMUsage) -> float:
    prompt_cost = (usage.prompt_tokens / 1_000_000) * _PROMPT_TOKEN_COST_PER_1M
    completion_cost = (usage.completion_tokens / 1_000_000) * _COMPLETION_TOKEN_COST_PER_1M
    return prompt_cost + completion_cost


async def _generate_one(
    *,
    question: Question,
    llm: LLMProvider,
    database: MongoDBDatabase,
) -> tuple[str, LLMUsage]:
    response = await llm.generate(
        model=_MODEL,
        messages=_build_messages(question),
        temperature=0.4,
        max_tokens=1500,
    )
    await database.questions.update_reference_answer(question.id, response.content)
    return question.id, response.usage


async def _generate_with_semaphore(
    *,
    question: Question,
    llm: LLMProvider,
    database: MongoDBDatabase,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str, LLMUsage] | tuple[str, str, Exception]:
    async with semaphore:
        try:
            qid, usage = await _generate_one(question=question, llm=llm, database=database)
            return qid, "ok", usage
        except Exception as exc:
            return question.id, "error", exc


def _confirm_or_exit(*, count: int, force: bool, dry_run: bool) -> None:
    if dry_run:
        return
    if count == 0:
        return
    print(f"About to call OpenAI {_MODEL} for {count} question(s).")
    print(f"Estimated cost: ~${count * 0.02:.2f} – ${count * 0.04:.2f} based on prior runs.")
    print(f"({'--force' if force else '--limit'} mode active.)" if force else "")
    response = input("Proceed? [y/N] ").strip().lower()
    if response not in {"y", "yes"}:
        print("Cancelled.")
        sys.exit(1)


async def main(args: argparse.Namespace) -> int:
    settings = get_settings()

    if settings.openai_api_key == _PLACEHOLDER_API_KEY:
        print(
            "ERROR: OPENAI_API_KEY is the placeholder value. "
            "Set a real key in backend/.env.local before running this script.",
            file=sys.stderr,
        )
        return 2

    database = MongoDBDatabase(uri=settings.mongo_uri, db_name=settings.mongo_db_name)
    llm: LLMProvider = OpenAILLMProvider(api_key=settings.openai_api_key)

    try:
        await database.ensure_indexes()

        if args.force:
            cursor = database._db["questions"].find({"type": "situation"})
            documents = await cursor.to_list(length=None)
            from app.adapters.local.mongodb_database import _doc_to_question
            candidates = [_doc_to_question(doc) for doc in documents]
            print(f"--force: regenerating ALL {len(candidates)} situation questions.")
        else:
            candidates = await database.questions.list_missing_reference_answer(type="situation")
            print(f"Found {len(candidates)} situation question(s) missing a reference answer.")

        if args.limit is not None and args.limit > 0:
            candidates = candidates[: args.limit]
            print(f"--limit {args.limit}: processing first {len(candidates)} only.")

        if not candidates:
            print("Nothing to do.")
            return 0

        if args.dry_run:
            print("\n--dry-run: would generate answers for these questions:")
            for q in candidates:
                print(f"  - [{q.difficulty}] {q.category}: {q.title}")
            return 0

        _confirm_or_exit(count=len(candidates), force=args.force, dry_run=args.dry_run)

        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
        tasks = [
            _generate_with_semaphore(
                question=q,
                llm=llm,
                database=database,
                semaphore=semaphore,
            )
            for q in candidates
        ]

        total_cost = 0.0
        succeeded = 0
        failed = 0
        for completed in asyncio.as_completed(tasks):
            qid, status, payload = await completed
            if status == "ok":
                usage: LLMUsage = payload  # type: ignore[assignment]
                cost = _estimate_cost(usage)
                total_cost += cost
                succeeded += 1
                print(
                    f"  ok    {qid}  "
                    f"prompt={usage.prompt_tokens}  completion={usage.completion_tokens}  "
                    f"cost=${cost:.4f}"
                )
            else:
                failed += 1
                print(f"  FAIL  {qid}  {payload}", file=sys.stderr)

        print(
            f"\nDone. Succeeded: {succeeded}. Failed: {failed}. "
            f"Total estimated cost: ${total_cost:.4f}."
        )
        return 0 if failed == 0 else 1

    finally:
        await database.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-generate reference answers for situation questions via OpenAI.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate answers even for questions that already have one.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N questions (useful for testing on 1 first).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without calling OpenAI.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    sys.exit(asyncio.run(main(parsed)))