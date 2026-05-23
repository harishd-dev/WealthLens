"""
API Integration Tests — FastAPI TestClient
Run: pytest tests/ -v -k "api"

These tests mock Supabase so they run without a live DB.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def mock_user():
    u = MagicMock()
    u.id    = "user-test-123"
    u.email = "test@wealthlens.app"
    u.user_metadata = {"name": "Test User"}
    return u

def mock_supabase_client(data=None, count=None):
    """Return a deeply-mocked Supabase client."""
    m = MagicMock()
    result = MagicMock()
    result.data  = data or []
    result.count = count or 0
    # Chain: table().select().eq()...execute()
    m.table.return_value.select.return_value.eq.return_value.order.return_value \
     .range.return_value.execute.return_value = result
    m.table.return_value.insert.return_value.execute.return_value = result
    m.table.return_value.delete.return_value.eq.return_value.eq.return_value \
     .execute.return_value = result
    return m


# ── Health Check ──────────────────────────────────────────────────────────────

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ── Auth Routes ───────────────────────────────────────────────────────────────

class TestAuthRoutes:
    @patch("app.api.routes.auth.get_supabase_client")
    def test_login_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.user.id    = "uid-123"
        mock_session.user.email = "test@test.com"
        mock_session.user.user_metadata = {"name": "Test"}
        mock_session.session.access_token = "fake-jwt"
        mock_client.auth.sign_in_with_password.return_value = mock_session
        mock_get_client.return_value = mock_client

        res = client.post("/api/v1/auth/login", json={
            "email": "test@test.com", "password": "password123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    @patch("app.api.routes.auth.get_supabase_client")
    def test_login_invalid_credentials(self, mock_get_client):
        from supabase import AuthApiError
        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError("Invalid", 400, {})
        mock_get_client.return_value = mock_client

        res = client.post("/api/v1/auth/login", json={
            "email": "bad@test.com", "password": "wrongpass"
        })
        assert res.status_code == 401

    def test_forgot_password_always_200(self):
        with patch("app.api.routes.auth.get_supabase_client") as m:
            m.return_value.auth.reset_password_email.return_value = None
            res = client.post("/api/v1/auth/forgot-password",
                              json={"email": "anyone@test.com"})
            assert res.status_code == 200


# ── Transaction Routes ────────────────────────────────────────────────────────

AUTH_HEADER = {"Authorization": "Bearer fake-token"}

class TestTransactionRoutes:
    def _patch_auth(self):
        return patch(
            "app.core.security.get_current_user",
            return_value=mock_user()
        )

    @patch("app.api.routes.transactions.get_supabase_client")
    def test_list_transactions(self, mock_get_client):
        mock_get_client.return_value = mock_supabase_client(
            data=[{"id":"1","description":"Test","amount":100,
                   "type":"debit","category":"Food",
                   "date":"2026-05-15","user_id":"user-test-123",
                   "source":"manual","created_at":"2026-05-15T00:00:00"}],
            count=1
        )
        with self._patch_auth():
            res = client.get("/api/v1/transactions", headers=AUTH_HEADER)
        assert res.status_code == 200
        body = res.json()
        assert "data"  in body
        assert "total" in body

    @patch("app.api.routes.transactions.get_supabase_client")
    def test_create_transaction(self, mock_get_client):
        new_tx = {
            "id":"new-1","description":"Lunch","amount":250,
            "type":"debit","category":"Food",
            "date":"2026-05-20","user_id":"user-test-123",
            "source":"manual","created_at":"2026-05-20T00:00:00"
        }
        mc = MagicMock()
        mc.table.return_value.insert.return_value.execute.return_value.data = [new_tx]
        mock_get_client.return_value = mc
        with self._patch_auth():
            res = client.post("/api/v1/transactions", headers=AUTH_HEADER, json={
                "description": "Lunch", "amount": 250,
                "type": "debit", "category": "Food", "date": "2026-05-20"
            })
        assert res.status_code == 201
        assert res.json()["description"] == "Lunch"

    def test_create_transaction_missing_amount(self):
        with patch("app.core.security.get_current_user", return_value=mock_user()):
            res = client.post("/api/v1/transactions", headers=AUTH_HEADER, json={
                "description": "No amount", "type": "debit",
                "category": "Food", "date": "2026-05-20"
            })
        assert res.status_code == 422   # Pydantic validation error

    @patch("app.api.routes.transactions.get_supabase_client")
    def test_delete_transaction(self, mock_get_client):
        mc = MagicMock()
        mc.table.return_value.eq.return_value.eq.return_value \
          .delete.return_value.execute.return_value.data = [{"id": "tx-1"}]
        # Simpler: patch the whole chain
        result = MagicMock()
        result.data = [{"id": "tx-1"}]
        mc.table.return_value.delete.return_value.eq.return_value \
          .eq.return_value.execute.return_value = result
        mock_get_client.return_value = mc
        with patch("app.core.security.get_current_user", return_value=mock_user()):
            res = client.delete("/api/v1/transactions/tx-1", headers=AUTH_HEADER)
        assert res.status_code == 204


# ── Analytics Routes ──────────────────────────────────────────────────────────

class TestAnalyticsRoutes:
    SAMPLE_TXS = [
        {"amount": 85000, "type": "credit", "category": "Income",   "date": "2026-05-10", "description": "Salary"},
        {"amount": 380,   "type": "debit",  "category": "Food",     "date": "2026-05-15", "description": "Swiggy"},
        {"amount": 1200,  "type": "debit",  "category": "Bills",    "date": "2026-05-18", "description": "Electricity"},
        {"amount": 5000,  "type": "debit",  "category": "Investment","date": "2026-05-20", "description": "SIP"},
    ]

    @patch("app.api.routes.analytics.get_supabase_client")
    def test_summary_structure(self, mock_get_client):
        mc = MagicMock()
        result = MagicMock()
        result.data = self.SAMPLE_TXS
        mc.table.return_value.select.return_value.eq.return_value \
          .execute.return_value = result
        mock_get_client.return_value = mc
        with patch("app.core.security.get_current_user", return_value=mock_user()):
            res = client.get("/api/v1/analytics/summary", headers=AUTH_HEADER)
        assert res.status_code == 200
        body = res.json()
        assert "total_income"  in body
        assert "total_expense" in body
        assert "net_savings"   in body
        assert "monthly"       in body
        assert "by_category"  in body

    @patch("app.api.routes.analytics.get_supabase_client")
    def test_summary_calculations(self, mock_get_client):
        mc = MagicMock()
        result = MagicMock()
        result.data = self.SAMPLE_TXS
        mc.table.return_value.select.return_value.eq.return_value \
          .execute.return_value = result
        mock_get_client.return_value = mc
        with patch("app.core.security.get_current_user", return_value=mock_user()):
            res = client.get("/api/v1/analytics/summary", headers=AUTH_HEADER)
        body = res.json()
        assert body["total_income"]  == 85000.0
        assert body["total_expense"] == 6580.0
        assert body["net_savings"]   == 78420.0
