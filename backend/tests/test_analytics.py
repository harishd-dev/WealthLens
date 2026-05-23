"""
Tests for analytics utility functions.
Pure Python — no DB, no HTTP client needed.
"""

import pytest
from app.utils.analytics import (
    compute_summary,
    compute_monthly,
    compute_category_breakdown,
    detect_anomalies,
    compute_savings_trend,
    top_spending_days,
)

SAMPLE = [
    {"amount": 85000, "type": "credit", "category": "Income",      "date": "2026-04-10"},
    {"amount": 380,   "type": "debit",  "category": "Food",        "date": "2026-04-12"},
    {"amount": 1200,  "type": "debit",  "category": "Bills",       "date": "2026-04-15"},
    {"amount": 5000,  "type": "debit",  "category": "Investment",  "date": "2026-04-20"},
    {"amount": 15000, "type": "credit", "category": "Income",      "date": "2026-05-05"},
    {"amount": 420,   "type": "debit",  "category": "Food",        "date": "2026-05-08"},
    {"amount": 85000, "type": "credit", "category": "Income",      "date": "2026-05-10"},
    {"amount": 650,   "type": "debit",  "category": "Entertainment","date": "2026-05-12"},
    {"amount": 1100,  "type": "debit",  "category": "Bills",       "date": "2026-05-15"},
    {"amount": 5000,  "type": "debit",  "category": "Investment",  "date": "2026-05-20"},
    {"amount": 890,   "type": "debit",  "category": "Health",      "date": "2026-05-22"},
    {"amount": 3200,  "type": "debit",  "category": "Shopping",    "date": "2026-05-23"},
]


class TestComputeSummary:
    def test_income_total(self):
        s = compute_summary(SAMPLE)
        assert s["total_income"] == 85000 + 15000 + 85000

    def test_expense_total(self):
        s = compute_summary(SAMPLE)
        exp = 380 + 1200 + 5000 + 420 + 650 + 1100 + 5000 + 890 + 3200
        assert s["total_expense"] == exp

    def test_net_savings(self):
        s = compute_summary(SAMPLE)
        assert s["net_savings"] == s["total_income"] - s["total_expense"]

    def test_savings_rate_between_0_100(self):
        s = compute_summary(SAMPLE)
        assert 0 <= s["savings_rate"] <= 100

    def test_tx_count(self):
        s = compute_summary(SAMPLE)
        assert s["tx_count"] == len(SAMPLE)

    def test_no_income(self):
        debits_only = [t for t in SAMPLE if t["type"] == "debit"]
        s = compute_summary(debits_only)
        assert s["total_income"]  == 0
        assert s["net_savings"]   < 0
        assert s["savings_rate"]  == 0.0

    def test_empty_list(self):
        s = compute_summary([])
        assert s["total_income"]  == 0
        assert s["total_expense"] == 0
        assert s["net_savings"]   == 0


class TestComputeMonthly:
    def test_returns_two_months(self):
        monthly = compute_monthly(SAMPLE)
        assert len(monthly) == 2

    def test_sorted_chronologically(self):
        monthly = compute_monthly(SAMPLE)
        assert monthly[0]["month"] == "Apr"
        assert monthly[1]["month"] == "May"

    def test_april_income(self):
        monthly = compute_monthly(SAMPLE)
        apr = monthly[0]
        assert apr["income"] == 85000

    def test_may_income(self):
        monthly = compute_monthly(SAMPLE)
        may = monthly[1]
        assert may["income"] == 15000 + 85000

    def test_savings_field_present(self):
        monthly = compute_monthly(SAMPLE)
        for m in monthly:
            assert "savings" in m
            assert m["savings"] == m["income"] - m["expense"]

    def test_empty_list(self):
        assert compute_monthly([]) == []


class TestComputeCategoryBreakdown:
    def test_only_debits_counted(self):
        breakdown = compute_category_breakdown(SAMPLE)
        categories = [b["category"] for b in breakdown]
        assert "Income" not in categories

    def test_sorted_descending(self):
        breakdown = compute_category_breakdown(SAMPLE)
        totals = [b["total"] for b in breakdown]
        assert totals == sorted(totals, reverse=True)

    def test_percentages_sum_to_100(self):
        breakdown = compute_category_breakdown(SAMPLE)
        total_pct = sum(b["percentage"] for b in breakdown)
        assert abs(total_pct - 100.0) < 0.5   # allow rounding

    def test_counts_are_positive(self):
        breakdown = compute_category_breakdown(SAMPLE)
        assert all(b["count"] > 0 for b in breakdown)

    def test_food_appears(self):
        breakdown = compute_category_breakdown(SAMPLE)
        food = next((b for b in breakdown if b["category"] == "Food"), None)
        assert food is not None
        assert food["total"] == 380 + 420   # April + May food


class TestDetectAnomalies:
    def test_no_anomaly_in_uniform_data(self):
        # All food transactions at the same amount → no anomaly
        uniform = [
            {"amount": 400, "type": "debit", "category": "Food", "date": f"2026-05-{d:02d}"}
            for d in range(1, 10)
        ]
        anomalies = detect_anomalies(uniform)
        assert anomalies == []

    def test_detects_spike(self):
        # 8 normal food purchases + 1 massive spike
        normal = [
            {"amount": 400, "type": "debit", "category": "Food", "date": f"2026-05-{d:02d}"}
            for d in range(1, 9)
        ]
        spike = {"amount": 50000, "type": "debit", "category": "Food", "date": "2026-05-09"}
        anomalies = detect_anomalies(normal + [spike])
        assert len(anomalies) >= 1
        assert anomalies[0]["amount"] == 50000

    def test_credits_ignored(self):
        credits = [
            {"amount": 999999, "type": "credit", "category": "Income", "date": "2026-05-01"},
            {"amount": 1,      "type": "credit", "category": "Income", "date": "2026-05-02"},
        ]
        assert detect_anomalies(credits) == []


class TestTopSpendingDays:
    def test_returns_n_items(self):
        days = top_spending_days(SAMPLE, n=3)
        assert len(days) <= 3

    def test_sorted_descending(self):
        days = top_spending_days(SAMPLE, n=5)
        totals = [d["total"] for d in days]
        assert totals == sorted(totals, reverse=True)

    def test_only_debits(self):
        credits_only = [
            {"amount": 10000, "type": "credit", "category": "Income", "date": "2026-05-01"}
        ]
        days = top_spending_days(credits_only, n=5)
        assert days == []

    def test_empty_input(self):
        assert top_spending_days([], n=5) == []


class TestComputeSavingsTrend:
    def test_returns_required_keys(self):
        result = compute_savings_trend(SAMPLE, months=1)
        assert "recent_savings" in result
        assert "prior_savings"  in result
        assert "change_pct"     in result
        assert "trend"          in result

    def test_trend_is_valid_direction(self):
        result = compute_savings_trend(SAMPLE, months=1)
        assert result["trend"] in ("up", "down")

    def test_no_prior_data_returns_none_pct(self):
        # Transactions only in future months → prior period is empty
        future = [
            {"amount": 1000, "type": "credit", "category": "Income", "date": "2030-01-15"},
            {"amount": 200,  "type": "debit",  "category": "Food",   "date": "2030-01-20"},
        ]
        result = compute_savings_trend(future, months=1)
        # Prior period has no data → change_pct should be None
        assert result["change_pct"] is None
