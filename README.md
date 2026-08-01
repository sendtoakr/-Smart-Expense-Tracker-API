# Smart Expense Tracker API
A REST API built with FastAPI to manage personal expenses. The API stores expenses in memory and persists them to a local JSON file so data is retained across server restarts.


## Features
- Add a new expense
- View all expenses
- Filter expenses by category
- View total expenses
- Delete an expense
- View total expenses by category
- Automatic Swagger/OpenAPI documentation (/docs) (Bonus Feature)

## Project layout
your-repo/
│── README.md
│── AI_NOTES.md
│── requirements.txt
│── src/
│   └── main.py
│── tests/
│   └── test_main.py


## Install Dependencies
From the project root:

pip install -r requirements.txt

If your system blocks package installation (for example Debian/Ubuntu):

pip install -r requirements.txt --break-system-packages


## Start the Server
From the project root:

uvicorn src.main:app --reload

The API will be available at:

http://127.0.0.1:8000

Swagger Documentation:

http://127.0.0.1:8000/docs


## Run the Test Suite
From the project root:

pytest tests/ -v

The tests use a temporary JSON file, so they do not modify real application data.


## API Endpoint

| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Add a new expense |
| GET | `/expenses` | List all expenses (optional `?category=` filter) |
| GET | `/expenses/{id}` | Get a single expense |
| DELETE | `/expenses/{id}` | Delete an expense |
| GET | `/expenses/summary/total` | Total of all expenses |
| GET | `/expenses/summary/by-category` | Totals grouped by every category |
| GET | `/expenses/summary/total/{category}` | Total for one specific category |


## Notes

- Expense `id`s are auto-generated UUIDs.
- Categories are normalized to Title Case.
- Expenses are stored in a local JSON file for persistence.
- Invalid input returns HTTP 422.
- Missing records return HTTP 404.
