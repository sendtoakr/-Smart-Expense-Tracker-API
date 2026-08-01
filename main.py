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
so data survives a server restart. No database required. The file path
can be overridden with the EXPENSES_DATA_FILE environment variable
(the test suite uses this to avoid touching real data).
"""

import json
import os
import uuid
from datetime import date as date_type
from pathlib import Path
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


class ExpenseStore:
    """A tiny in-memory store, backed by a JSON file on disk.

    Kept as a class (rather than bare module globals) so tests can spin up
    isolated, throwaway stores instead of sharing state with the app used
    for manual/local runs.
    """

    def __init__(self, data_file: Path):
        self.data_file = data_file
        self._lock = Lock()
        self._expenses: dict = self._load()

    def _load(self) -> dict:
        if not self.data_file.exists():
            return {}
        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            return {item["id"]: item for item in raw}
        except (json.JSONDecodeError, KeyError):
            # Corrupted or empty file -> start fresh rather than crash the app
            return {}

    def _save(self) -> None:
        with self.data_file.open("w", encoding="utf-8") as f:
            json.dump(list(self._expenses.values()), f, indent=2, default=str)

    def add(self, record: dict) -> dict:
        with self._lock:
            self._expenses[record["id"]] = record
            self._save()
        return record

    def all(self) -> list:
        return list(self._expenses.values())

    def get(self, expense_id: str) -> Optional[dict]:
        return self._expenses.get(expense_id)

    def delete(self, expense_id: str) -> Optional[dict]:
        with self._lock:
            if expense_id not in self._expenses:
                return None
            removed = self._expenses.pop(expense_id)
            self._save()
        return removed


DEFAULT_DATA_FILE = Path(os.environ.get("EXPENSES_DATA_FILE", Path(__file__).parent.parent / "expenses.json"))
store = ExpenseStore(DEFAULT_DATA_FILE)


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
    record = {
        "id": str(uuid.uuid4()),
        "title": expense.title,
        "amount": round(expense.amount, 2),
        "category": expense.category,
        "date": (expense.date or date_type.today()).isoformat(),
    }
    return store.add(record)


@app.get("/expenses", response_model=list[Expense], tags=["Expenses"])
def get_expenses(
    category: Optional[str] = Query(
        default=None, description="Filter results by category (case-insensitive)."
    )
):
    """View all expenses, optionally filtered by category."""
    items = store.all()
    if category:
        items = [e for e in items if e["category"].lower() == category.strip().lower()]
    items.sort(key=lambda e: e["date"], reverse=True)  # most recent first
    return items


@app.get("/expenses/summary/total", response_model=TotalResponse, tags=["Summary"])
def total_expenses():
    """Calculate the total of all expenses.

    NOTE: registered before /expenses/{expense_id} so "summary" isn't
    swallowed by the dynamic id route.
    """
    items = store.all()
    total = round(sum(e["amount"] for e in items), 2)
    return {"total": total, "count": len(items)}


@app.get("/expenses/summary/by-category", tags=["Summary"])
def totals_by_category():
    """Calculate the total expenses grouped by category."""
    totals: dict = {}
    for e in store.all():
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
    matches = [e for e in store.all() if e["category"].lower() == category.strip().lower()]
    total = round(sum(e["amount"] for e in matches), 2)
    return {"total": total, "count": len(matches), "category": category.strip().title()}


@app.get("/expenses/{expense_id}", response_model=Expense, tags=["Expenses"])
def get_expense(expense_id: str):
    """Retrieve a single expense by id."""
    expense = store.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=200, tags=["Expenses"])
def delete_expense(expense_id: str):
    """Delete an expense by id."""
    removed = store.delete(expense_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted", "deleted": removed}
