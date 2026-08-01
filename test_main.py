"""
Test suite for the Smart Expense Tracker API.

Each test gets a fresh, isolated ExpenseStore backed by a temporary JSON
file (via the `client` fixture), so tests never touch real data and never
leak state into one another.
"""

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Reload the app module with EXPENSES_DATA_FILE pointed at a temp file.

    Reloading (rather than just monkeypatching `store`) guarantees every
    test starts with a completely empty, disposable store.
    """
    data_file = tmp_path / "expenses.json"
    monkeypatch.setenv("EXPENSES_DATA_FILE", str(data_file))

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import src.main as main_module

    importlib.reload(main_module)  # re-run module top-level with new env var

    return TestClient(main_module.app)


def _add(client, title="Coffee", amount=4.5, category="Food", date=None):
    payload = {"title": title, "amount": amount, "category": category}
    if date:
        payload["date"] = date
    return client.post("/expenses", json=payload)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_root_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# Add expense
# ---------------------------------------------------------------------------

def test_add_expense_returns_201_and_full_record(client):
    resp = _add(client, title="Groceries", amount=45.5, category="food", date="2026-07-28")
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Groceries"
    assert body["amount"] == 45.5
    assert body["category"] == "Food"  # normalized to Title Case
    assert body["date"] == "2026-07-28"
    assert "id" in body and len(body["id"]) > 0


def test_add_expense_defaults_date_to_today(client):
    resp = _add(client, date=None)
    assert resp.status_code == 201
    assert resp.json()["date"] is not None


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"title": "", "amount": 5, "category": "Food"}, "title"),
        ({"title": "X", "amount": -5, "category": "Food"}, "amount"),
        ({"title": "X", "amount": 0, "category": "Food"}, "amount"),
        ({"title": "X", "amount": 5, "category": ""}, "category"),
        ({"amount": 5, "category": "Food"}, "title"),
    ],
)
def test_add_expense_rejects_invalid_input(client, payload, field):
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List / filter expenses
# ---------------------------------------------------------------------------

def test_get_expenses_empty_initially(client):
    resp = client.get("/expenses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_expenses_lists_all_added(client):
    _add(client, title="Groceries", category="Food")
    _add(client, title="Uber", category="Transport")
    resp = client.get("/expenses")
    assert resp.status_code == 200
    titles = {e["title"] for e in resp.json()}
    assert titles == {"Groceries", "Uber"}


def test_filter_by_category_is_case_insensitive(client):
    _add(client, title="Groceries", category="Food")
    _add(client, title="Coffee", category="food")
    _add(client, title="Uber", category="Transport")

    resp = client.get("/expenses", params={"category": "FOOD"})
    assert resp.status_code == 200
    titles = {e["title"] for e in resp.json()}
    assert titles == {"Groceries", "Coffee"}


def test_filter_by_category_no_matches_returns_empty_list(client):
    _add(client, category="Food")
    resp = client.get("/expenses", params={"category": "Nonexistent"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_single_expense_by_id(client):
    created = _add(client, title="Groceries").json()
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Groceries"


def test_get_single_expense_404_when_missing(client):
    resp = client.get("/expenses/does-not-exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Totals
# ---------------------------------------------------------------------------

def test_total_expenses_overall(client):
    _add(client, amount=10)
    _add(client, amount=20.5)
    resp = client.get("/expenses/summary/total")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 30.5
    assert body["count"] == 2


def test_total_expenses_zero_when_no_expenses(client):
    resp = client.get("/expenses/summary/total")
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "count": 0, "category": None}


def test_totals_by_category_groups_correctly(client):
    _add(client, amount=10, category="Food")
    _add(client, amount=5, category="food")
    _add(client, amount=20, category="Transport")

    resp = client.get("/expenses/summary/by-category")
    assert resp.status_code == 200
    data = {row["category"]: row for row in resp.json()}
    assert data["Food"]["total"] == 15
    assert data["Food"]["count"] == 2
    assert data["Transport"]["total"] == 20
    assert data["Transport"]["count"] == 1


def test_total_for_single_category(client):
    _add(client, amount=10, category="Food")
    _add(client, amount=20, category="Transport")

    resp = client.get("/expenses/summary/total/food")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10
    assert body["count"] == 1
    assert body["category"] == "Food"


def test_total_for_category_with_no_expenses_is_zero(client):
    resp = client.get("/expenses/summary/total/nonexistent")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["count"] == 0


# ---------------------------------------------------------------------------
# Delete expense
# ---------------------------------------------------------------------------

def test_delete_expense_removes_it(client):
    created = _add(client, title="Groceries").json()
    expense_id = created["id"]

    resp = client.delete(f"/expenses/{expense_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"]["id"] == expense_id

    # It should no longer show up in the list or be fetchable directly
    assert client.get(f"/expenses/{expense_id}").status_code == 404
    assert all(e["id"] != expense_id for e in client.get("/expenses").json())


def test_delete_missing_expense_returns_404(client):
    resp = client.delete("/expenses/does-not-exist")
    assert resp.status_code == 404


def test_delete_affects_totals(client):
    created = _add(client, amount=15, category="Food").json()
    _add(client, amount=5, category="Food")

    client.delete(f"/expenses/{created['id']}")

    resp = client.get("/expenses/summary/total/food")
    assert resp.json()["total"] == 5
    assert resp.json()["count"] == 1


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_expenses_persist_to_data_file(client, tmp_path, monkeypatch):
    _add(client, title="Groceries")
    data_file = Path(__import__("os").environ["EXPENSES_DATA_FILE"])
    assert data_file.exists()

    import json
    saved = json.loads(data_file.read_text())
    assert len(saved) == 1
    assert saved[0]["title"] == "Groceries"
