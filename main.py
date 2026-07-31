"""
Smart Expense Tracker API
==========================
A REST API for managing personal expenses, built with FastAPI.

Features:
- Add an expense (id, title, amount, category, date)
- View all expenses
- Filter expenses by category
- Calculate total expenses (overall and by category)
- Delete an expense

Storage: expenses are kept in memory and persisted to a local JSON file
(expenses.json) so data survives a server restart. No database required.

Run with:
    uvicorn main:app --reload

Interactive docs (Swagger UI) will be available at:
    http://127.0.0.1:8000/docs
"""

import json
import uuid
from datetime import date as date_type
from pathlib import Path
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Storage setup
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).parent / "expenses.json"
_lock = Lock()  # guards read/modify/write of the JSON file


def _load_expenses() -> dict:
    """Load all expenses from the JSON file into memory as a dict keyed by id."""
    if not DATA_FILE.exists():
        return {}
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return {item["id"]: item for item in raw}
    except (json.JSONDecodeError, KeyError):
        # Corrupted or empty file -> start fresh rather than crash the app
        return {}


def _save_expenses(expenses: dict) -> None:
    """Persist the in-memory expenses dict back to the JSON file."""
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(list(expenses.values()), f, indent=2, default=str)


# In-memory store, seeded from disk at startup.
expenses_db: dict = _load_expenses()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Groceries"])
    amount: float = Field(..., gt=0, examples=[42.50])
    category: str = Field(..., min_length=1, max_length=50, examples=["Food"])
    date: Optional[date_type] = Field(
        default=None,
        description="Defaults to today if not provided (YYYY-MM-DD).",
    )

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()


class Expense(BaseModel):
    id: str
    title: str
    amount: float
    category: str
    date: date_type


class TotalResponse(BaseModel):
    total: float
    count: int
    category: Optional[str] = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Smart Expense Tracker API",
    description="A simple REST API to add, view, filter, total, and delete personal expenses.",
    version="1.0.0",
)


@app.get("/", tags=["Health"])
def root():
    """Basic health check / welcome message."""
    return {"message": "Smart Expense Tracker API is running. Visit /docs for the interactive API docs."}


@app.post("/expenses", response_model=Expense, status_code=201, tags=["Expenses"])
def add_expense(expense: ExpenseCreate):
    """Add a new expense. `date` defaults to today if omitted."""
    new_id = str(uuid.uuid4())
    record = {
        "id": new_id,
        "title": expense.title,
        "amount": round(expense.amount, 2),
        "category": expense.category,
        "date": (expense.date or date_type.today()).isoformat(),
    }
    with _lock:
        expenses_db[new_id] = record
        _save_expenses(expenses_db)
    return record


@app.get("/expenses", response_model=list[Expense], tags=["Expenses"])
def get_expenses(
    category: Optional[str] = Query(
        default=None, description="Filter results by category (case-insensitive)."
    )
):
    """View all expenses, optionally filtered by category."""
    items = list(expenses_db.values())
    if category:
        items = [e for e in items if e["category"].lower() == category.strip().lower()]
    # Most recent first
    items.sort(key=lambda e: e["date"], reverse=True)
    return items


@app.get("/expenses/{expense_id}", response_model=Expense, tags=["Expenses"])
def get_expense(expense_id: str):
    """Retrieve a single expense by id."""
    expense = expenses_db.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=200, tags=["Expenses"])
def delete_expense(expense_id: str):
    """Delete an expense by id."""
    with _lock:
        if expense_id not in expenses_db:
            raise HTTPException(status_code=404, detail="Expense not found")
        removed = expenses_db.pop(expense_id)
        _save_expenses(expenses_db)
    return {"message": "Expense deleted", "deleted": removed}


@app.get("/expenses/summary/total", response_model=TotalResponse, tags=["Summary"])
def total_expenses():
    """Calculate the total of all expenses."""
    items = list(expenses_db.values())
    total = round(sum(e["amount"] for e in items), 2)
    return {"total": total, "count": len(items)}


@app.get("/expenses/summary/by-category", tags=["Summary"])
def totals_by_category():
    """Calculate the total expenses grouped by category."""
    totals: dict = {}
    for e in expenses_db.values():
        cat = e["category"]
        bucket = totals.setdefault(cat, {"total": 0.0, "count": 0})
        bucket["total"] += e["amount"]
        bucket["count"] += 1

    return [
        {"category": cat, "total": round(data["total"], 2), "count": data["count"]}
        for cat, data in sorted(totals.items())
    ]


@app.get("/expenses/summary/total/{category}", response_model=TotalResponse, tags=["Summary"])
def total_by_category(category: str):
    """Calculate the total expenses for a single, specific category."""
    matches = [e for e in expenses_db.values() if e["category"].lower() == category.strip().lower()]
    total = round(sum(e["amount"] for e in matches), 2)
    return {"total": total, "count": len(matches), "category": category.strip().title()}
