# CODEGEN-WORKFLOW.md — How the AI Assistant Generates Code

This document describes the step-by-step workflow the AI assistant must follow when generating code for any batch, phase, or milestone of a project. It is **project-agnostic** — keep it in your repo root and reference it from your project's `AGENT.md` or equivalent.

> **How to use this doc:** When starting a batch, tell the assistant: *"Generate Batch N following `CODEGEN-WORKFLOW.md`."* The assistant must then follow every step below in order.

---

## Guiding principles

1. **Structure before content.** The user sees the folder tree before any file is written.
2. **One file at a time.** Each file is generated individually. No zipped archives, no giant multi-file dumps.
3. **User reviews as we go.** After each file, the user can inspect it and course-correct before the next one.
4. **Summary at the end.** After every file in the batch is generated, a summary explains what each file does and how they connect.
5. **No silent assumptions.** If the assistant needs to decide something not specified, it pauses and asks before generating.

---

## The 5-step workflow

The assistant must follow these 5 steps **in order** for every batch.

### Step 1 — Confirm scope

Before generating anything, the assistant restates:

- **Which batch / milestone** is being generated.
- **Goal of the batch** in one sentence.
- **Exit criteria** — how we'll know the batch is done.
- **Any assumptions** it's making (tech choices, library versions, naming conventions) that weren't explicitly confirmed.
- **Any open questions** that must be resolved before generating.

The assistant **waits for user confirmation** ("yes, proceed" or edits/answers) before moving to Step 2.

**Why this matters:** Fixing a wrong assumption now is cheap; fixing it after 15 files are generated is expensive.

---

### Step 2 — Show the folder structure

The assistant presents the **complete folder/file tree** for the batch as a single code block. Example format:

```
batch-1-foundation/
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── ports/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── llm_provider.py
│   │   └── domain/
│   │       └── __init__.py
│   └── adapters/
│       └── local/
│           ├── __init__.py
│           └── mongodb_database.py
└── tests/
    └── __init__.py
```

Along with the tree, the assistant provides:

- **A numbered list of every file** that will be generated (so both sides can track progress).
- **A brief one-line purpose** for each file.
- **The intended generation order** (typically: config → interfaces → implementations → wiring → entry point → tests).

The assistant **waits for user confirmation** before generating any file.

**Common user responses at this step:**
- "Looks good, proceed."
- "Move X under Y instead."
- "Skip file Z for now."
- "Add a file for W."

---

### Step 3 — Generate files one at a time

For each file in the approved list, in the approved order:

1. **Announce the file:** "Generating file N of M: `path/to/file.ext`"
2. **State its purpose** in one sentence.
3. **Write the full file content.**
4. **Present the file for review** — user can open, read, copy, or request changes.
5. **Pause for user input.** User responses can be:
   - "Next" / "Continue" / "Proceed" → move to the next file.
   - "Change X" → the assistant edits the current file, presents again, waits.
   - "Skip this one" → the assistant notes it as skipped and moves on.
   - "Stop" → the assistant halts the batch and summarizes what was done.

**Rules the assistant must follow during Step 3:**

- **Never batch multiple files into one response** unless the user explicitly says "generate all remaining files without pausing."
- **Never silently change earlier decisions.** If generating file 7 reveals that file 3 needs a tweak, the assistant pauses, explains, and asks before backtracking.
- **Every file is complete and runnable as presented.** No `# ... fill this in later` comments unless the user asked for a stub.
- **Imports reference only files that exist or will exist in this batch.** No dangling imports.
- **Code must match the conventions** stated in the project's `AGENT.md` (naming, style, architecture rules).

---

### Step 4 — Generate the summary

After the final file is presented (or the user halts the batch), the assistant generates a **summary section** with:

#### 4a. File-by-file summary

A table or bulleted list covering every file generated:

| # | File | Purpose | Key contents |
|---|---|---|---|
| 1 | `pyproject.toml` | Python project config | Dependencies, ruff/mypy config |
| 2 | `app/core/ports/database.py` | Abstract DB interface | `Database` Protocol with CRUD methods |
| 3 | `app/adapters/local/mongodb_database.py` | Local Mongo adapter | Implements `Database` using `motor` |
| ... | ... | ... | ... |

#### 4b. How they connect

A short prose paragraph (or diagram) explaining the **wiring** — how files depend on each other, and how data/control flows through them.

#### 4c. What this batch delivers

Restate the exit criteria and confirm each is met. If something is incomplete, call it out explicitly.

#### 4d. What's NOT included

Explicitly list what was deferred to a future batch. Prevents user assumptions.

#### 4e. Verification steps

Concrete commands the user can run to verify the batch works. Example:
```bash
docker compose up
curl localhost:8000/health/deep   # expect 200 with all services "ok"
pytest tests/                     # expect all green
```

#### 4f. Suggested next actions

One of:
- "Proceed to Batch N+1" (with a one-line preview)
- "Pause to write ADR/docs for decisions made here"
- "User action needed: provision X, sign up for Y, etc."

---

### Step 5 — Handoff

The assistant ends the batch with an explicit handoff line:

> **Batch N complete.** Files: A, B, C, D. Next up: Batch N+1 (*goal*). Ready when you are — type "start Batch N+1" to continue, or ask questions about anything generated above.

No more content after this line. The user drives the next step.

---

## How to request code generation — user-side prompts

To use this workflow, the user can say things like:

- "Generate Batch 1 following `CODEGEN-WORKFLOW.md`."
- "Start Batch 2." *(assumes the workflow is the default)*
- "Continue to the next file."
- "Regenerate file 3 but use Y instead of X."
- "Skip to the summary; I'll read files myself."
- "Pause — question about file 5."

---

## Overrides the user can set upfront

At the start of a batch, the user can override defaults. The assistant must respect these for the entire batch:

| Override | Example | Effect |
|---|---|---|
| **Batch mode** | "Generate all files without pausing" | Assistant skips the per-file pause in Step 3; still does Steps 1, 2, 4, 5 normally. |
| **Abbreviated summary** | "Skip file-by-file summary" | Assistant does only 4c–4f, not 4a–4b. |
| **No stubs** | "Every file must be production-ready" | Default behavior; stated for clarity. |
| **Stubs allowed** | "Stubs OK for external adapters" | Assistant may mark specific files with `TODO` comments, flagged in the summary. |
| **Different order** | "Generate tests first, then implementation" | Assistant re-orders Step 2's list before confirming. |

---

## What the assistant must NOT do

1. **Dump a ZIP file or multi-file archive.** Files are generated and reviewed individually.
2. **Generate files not in the approved list** without asking.
3. **Skip the folder-structure step** to "save time." The user must see the plan before code arrives.
4. **Use placeholder content** (`# TODO: implement`) unless the user approved stubs.
5. **Reference files from future batches** in imports or comments without flagging it.
6. **Proceed after a user pushback** without acknowledging the change and, if relevant, updating earlier files.
7. **Produce a final summary that hides skipped or incomplete files.** Every generated, edited, and skipped file must be listed.

---

## Edge cases

**The batch has 30+ files.**
The assistant flags this at Step 2 and asks whether to (a) proceed one-at-a-time, (b) switch to "generate all without pausing" mode, or (c) split the batch into sub-batches.

**User changes a decision mid-batch.**
The assistant pauses, lists which already-generated files are affected, offers to regenerate them, and waits for instruction before continuing.

**The assistant realizes Step 2's plan was wrong.**
The assistant stops generating, explains the issue, proposes a corrected plan, and waits for approval. It does not silently "fix" things.

**User wants to see multiple files rendered at once for comparison.**
The assistant can group closely-related tiny files (e.g., several `__init__.py` files or multiple 5-line interface files) into a single response — but only after announcing the group and confirming the user is OK with it.

---

## Applying this to any project

This workflow is framework- and language-agnostic. The only project-specific inputs are:

- The **batch plan** (e.g., in the project's `DESIGN.md`, `ROADMAP.md`, or similar).
- The **coding conventions** (in `AGENT.md`, style guides, linter configs).
- The **tech stack** (so the assistant picks appropriate file types and tools).

As long as those three are documented, this workflow works for any codebase — frontend, backend, infra, scripts, mobile, data pipelines.

---

## Glossary

- **Batch / Milestone / Phase:** A scoped unit of work that produces a runnable, verifiable deliverable. Terminology varies; this doc uses "batch."
- **Stub:** A file with minimal content intended to be fleshed out later. Not allowed by default — must be explicitly approved.
- **Wiring:** How files import and compose each other into a working system.
- **Exit criteria:** Specific, verifiable conditions that define "done" for a batch.

---

## When in doubt

If the assistant is unsure whether to proceed, it pauses and asks. **Speed is not the goal; clarity and correctness are.** Skipping the workflow to move faster defeats its purpose.
