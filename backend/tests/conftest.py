"""
conftest.py — shared pytest fixtures.
Loaded automatically by pytest before any test file.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app


# ── App client ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Reusable TestClient across the whole test session."""
    with TestClient(app) as c:
        yield c


# ── Mock user ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id    = "user-fixture-001"
    u.email = "fixture@wealthlens.app"
    u.user_metadata = {"name": "Fixture User"}
    return u


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-jwt-token"}


# ── Supabase mock ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_supabase():
    """
    A generic deep-mock of the Supabase client.
    Tests override .data and .count on result as needed.
    """
    with patch("app.db.supabase.get_supabase_client") as mock_get:
        mc = MagicMock()
        result = MagicMock()
        result.data  = []
        result.count = 0

        # Build a fluent chain that always ends in .execute() → result
        chain = mc.table.return_value
        for method in ("select", "insert", "update", "delete", "upsert",
                       "eq", "neq", "gte", "lte", "ilike", "order",
                       "range", "limit", "single"):
            getattr(chain, method).return_value = chain
        chain.execute.return_value = result

        mock_get.return_value = mc
        yield mc, result


# ── Sample transactions ───────────────────────────────────────────────────────

@pytest.fixture
def sample_transactions():
    return [
        {"id": "t1", "user_id": "user-fixture-001", "description": "Swiggy Order",
         "amount": 380.0,   "type": "debit",  "category": "Food",
         "date": "2026-05-15", "source": "manual", "created_at": "2026-05-15T10:00:00"},
        {"id": "t2", "user_id": "user-fixture-001", "description": "Salary Credit",
         "amount": 85000.0, "type": "credit", "category": "Income",
         "date": "2026-05-10", "source": "manual", "created_at": "2026-05-10T09:00:00"},
        {"id": "t3", "user_id": "user-fixture-001", "description": "Amazon Purchase",
         "amount": 2499.0,  "type": "debit",  "category": "Shopping",
         "date": "2026-05-12", "source": "upload", "created_at": "2026-05-12T14:30:00"},
        {"id": "t4", "user_id": "user-fixture-001", "description": "Netflix Sub",
         "amount": 649.0,   "type": "debit",  "category": "Entertainment",
         "date": "2026-05-18", "source": "manual", "created_at": "2026-05-18T08:00:00"},
        {"id": "t5", "user_id": "user-fixture-001", "description": "Groww SIP",
         "amount": 5000.0,  "type": "debit",  "category": "Investment",
         "date": "2026-05-20", "source": "manual", "created_at": "2026-05-20T07:30:00"},
    ]
