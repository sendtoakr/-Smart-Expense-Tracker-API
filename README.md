# Smart Expense Tracker API

A lightweight REST API for managing personal expenses, built with **FastAPI**.
Data is stored in memory and persisted to a local `expenses.json` file — no
database required.

## Features

- Add an expense (`title`, `amount`, `category`, `date`)
- View all expenses
- Filter expenses by category
- Calculate total expenses (overall and by category)
- Delete an expense

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive Swagger docs (try every endpoint from the browser): `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/expenses` | Add a new expense |
| GET | `/expenses` | List all expenses (optional `?category=` filter) |
| GET | `/expenses/{id}` | Get a single expense |
| DELETE | `/expenses/{id}` | Delete an expense |
| GET | `/expenses/summary/total` | Total of all expenses |
| GET | `/expenses/summary/by-category` | Totals grouped by every category |
| GET | `/expenses/summary/total/{category}` | Total for one specific category |

## Example usage

**Add an expense**
```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "food", "date": "2026-07-28"}'
```
`date` is optional — it defaults to today. `category` is auto-capitalized (e.g. `food` → `Food`) so
filtering isn't case-sensitive.

**List all expenses**
```bash
curl http://127.0.0.1:8000/expenses
```

**Filter by category**
```bash
curl "http://127.0.0.1:8000/expenses?category=food"
```

**Total of everything**
```bash
curl http://127.0.0.1:8000/expenses/summary/total
```

**Totals broken down by category**
```bash
curl http://127.0.0.1:8000/expenses/summary/by-category
```

**Total for one category**
```bash
curl http://127.0.0.1:8000/expenses/summary/total/food
```

**Delete an expense**
```bash
curl -X DELETE http://127.0.0.1:8000/expenses/<expense-id>
```

## Notes

- Expense `id`s are auto-generated UUIDs — you don't supply your own.
- All writes are saved to `expenses.json` in the project folder, so your data survives a restart.
- Invalid requests (e.g. negative `amount`, missing `title`) return a `422` with details on what
  went wrong. Deleting or fetching an id that doesn't exist returns a `404`.
- This is intentionally dependency-light and has no auth layer — fine for personal/local use.
  If you want to expose it publicly, add authentication and consider swapping the JSON file for
  a real database (e.g. SQLite) for concurrent-write safety.
