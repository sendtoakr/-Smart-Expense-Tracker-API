# AI Notes

This document explains how AI (Claude) was used to build this project, what
was generated vs. reviewed, and what was verified before submission.

## What was AI-generated

The entire implementation — the FastAPI app (`src/main.py`), the pytest
suite (`tests/test_main.py`), and this documentation — was written by
Claude in a single conversational session, based on the assignment brief:
build a REST API for personal expenses supporting add / view all / filter
by category / totals (overall and by category) / delete, using in-memory or
JSON-file storage.

## Design decisions made by the AI (and why)

- **FastAPI over Flask** — chosen for built-in request validation
  (Pydantic), automatic OpenAPI/Swagger docs at `/docs`, and less
  boilerplate for this scope of project.
- **In-memory dict + JSON file persistence** — satisfies "no database
  required" while still surviving a server restart. A `Lock` guards
  read-modify-write so concurrent requests don't corrupt the file.
- **`ExpenseStore` as a class rather than bare module globals** — this was
  a refactor specifically to make the app testable: each test can spin up
  an isolated store pointed at a temp file, instead of tests sharing (and
  polluting) one global in-memory store or the real `expenses.json`.
- **Category normalization** (`.strip().title()`) and case-insensitive
  filtering/lookup — added so `food`, `Food`, and `FOOD` are treated as the
  same category, which seemed like the behavior a user would actually want,
  even though the brief didn't specify it.
- **UUIDs for expense ids** — avoids the caller needing to invent/track
  unique ids themselves, and avoids collisions.
- **`date` defaults to today if omitted** — reduces friction for the common
  case of logging an expense as it happens.

## What was manually verified (not just taken on faith)

- Ran the full test suite (`pytest tests/ -v`) from a clean checkout of this
  exact repo structure — all 23 tests pass.
- Started the server with the exact README command
  (`uvicorn src.main:app --reload`) from the repo root and manually
  exercised every endpoint with `curl`: add, list, filter, both total
  endpoints, get-by-id, delete, and the 404/422 error paths.
- Hit and fixed one real bug during development: a Pydantic v2 schema
  generation error caused by a model field named `date` shadowing the
  imported `datetime.date` type in the same module — fixed by importing it
  as `date_type`.
- Confirmed persistence actually works by checking that `expenses.json` is
  written correctly after a POST, and that data survives being reloaded
  from disk (covered by `test_expenses_persist_to_data_file`).

## Known limitations (left as-is, not hidden)

- No authentication — anyone who can reach the API can read/write all
  expenses. Fine for a local/personal tool, not for a public deployment.
- The JSON file is not safe for high-concurrency multi-process writes
  (a single-process `Lock` only protects against races within that one
  process). A real database would be needed for that.
- No pagination on `GET /expenses` — fine at personal-expense-tracker
  scale, would need revisiting if the dataset were expected to grow large.
