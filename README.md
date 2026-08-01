# Smart Expense Tracker API

A REST API for managing personal expenses, built with **FastAPI**. Data is
stored in memory and persisted to a local JSON file — no database required.

## What it does

- Add an expense (`title`, `amount`, `category`, `date`)
- View all expenses
- Filter expenses by category
- Calculate total expenses (overall and by category)
- Delete an expense

## Project layout

```
your-repo/
  README.md
  AI_NOTES.md
  requirements.txt
  src/
    __init__.py
    main.py          # FastAPI app, models, and storage
  tests/
    test_main.py      # pytest suite (23 tests)
```

## Install

From the repo root:

```bash
pip install -r requirements.txt
```

(If you're on a system that requires it, e.g. Debian/Ubuntu with an
externally-managed Python: `pip install -r requirements.txt --break-system-packages`.)

## Run the server

From the repo root:

```bash
uvicorn src.main:app --reload
```

The API is served at `http://127.0.0.1:8000`.
Interactive Swagger docs: `http://127.0.0.1:8000/docs`

## Run the tests

From the repo root:

```bash
pytest tests/ -v
```

Tests run against an isolated, temporary JSON file (via a `tmp_path` fixture
and the `EXPENSES_DATA_FILE` env var), so they never touch or depend on real
data and never leak state between each other.

## API reference

| Method | Path | Description |
|---|---|---|
| POST | `/expenses` | Add a new expense |
| GET | `/expenses` | List all expenses (optional `?category=` filter) |
| GET | `/expenses/{id}` | Get a single expense |
| DELETE | `/expenses/{id}` | Delete an expense |
| GET | `/expenses/summary/total` | Total of all expenses |
| GET | `/expenses/summary/by-category` | Totals grouped by every category |
| GET | `/expenses/summary/total/{category}` | Total for one specific category |

### Example usage

**Add an expense**
```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "food", "date": "2026-07-28"}'
```
`date` is optional and defaults to today. `category` is auto-normalized to
Title Case (e.g. `food` → `Food`), and filtering/lookups are case-insensitive.

**List / filter**
```bash
curl http://127.0.0.1:8000/expenses
curl "http://127.0.0.1:8000/expenses?category=food"
```

**Totals**
```bash
curl http://127.0.0.1:8000/expenses/summary/total
curl http://127.0.0.1:8000/expenses/summary/by-category
curl http://127.0.0.1:8000/expenses/summary/total/food
```

**Delete**
```bash
curl -X DELETE http://127.0.0.1:8000/expenses/<expense-id>
```

## Notes

- Expense `id`s are auto-generated UUIDs.
- Every write is persisted to `expenses.json` (created at the repo root the
  first time you add an expense while running the server), so data survives
  a restart.
- Invalid input (negative/zero `amount`, empty `title`/`category`) returns
  `422` with details on what's wrong. Fetching or deleting an id that
  doesn't exist returns `404`.
- No auth layer — this is intentionally minimal for personal/local use. For
  anything public-facing, add authentication and swap the JSON file for a
  real database (e.g. SQLite) to get safe concurrent writes.
