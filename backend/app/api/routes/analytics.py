"""
Analytics Routes — /api/v1/analytics
Pre-aggregated summaries ready for Recharts consumption.
All heavy lifting done in Python to keep the frontend thin.
"""

from collections import defaultdict
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from app.schemas.schemas import AnalyticsSummary, MonthlySummary, CategoryBreakdown

router = APIRouter()

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]


def _fetch_txns(user_id: str, start: Optional[str], end: Optional[str]):
    client = get_supabase_client()
    q = client.table("transactions").select("*").eq("user_id", user_id)
    if start:
        q = q.gte("date", start)
    if end:
        q = q.lte("date", end)
    return q.execute().data or []


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date:   Optional[str] = Query(None, description="YYYY-MM-DD"),
    user = Depends(get_current_user),
):
    """Aggregate income, expenses, savings, monthly trend and category breakdown."""
    txns = _fetch_txns(user.id, start_date, end_date)

    income  = sum(t["amount"] for t in txns if t["type"] == "credit")
    expense = sum(t["amount"] for t in txns if t["type"] == "debit")
    savings = income - expense
    savings_rate = round((savings / income * 100), 2) if income > 0 else 0.0

    # ── Monthly aggregation ──────────────────────────────────────────────────
    monthly_map: dict = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for tx in txns:
        d   = date.fromisoformat(tx["date"])
        key = (d.year, d.month)
        if tx["type"] == "credit":
            monthly_map[key]["income"] += tx["amount"]
        else:
            monthly_map[key]["expense"] += tx["amount"]

    monthly = [
        MonthlySummary(
            month=MONTH_NAMES[m - 1],
            year=y,
            income=round(v["income"], 2),
            expense=round(v["expense"], 2),
            savings=round(v["income"] - v["expense"], 2),
        )
        for (y, m), v in sorted(monthly_map.items())
    ]

    # ── Category breakdown ───────────────────────────────────────────────────
    cat_map: dict = defaultdict(lambda: {"total": 0.0, "count": 0})
    for tx in txns:
        if tx["type"] == "debit":
            cat = tx.get("category") or "Other"
            cat_map[cat]["total"] += tx["amount"]
            cat_map[cat]["count"] += 1

    by_category = sorted(
        [
            CategoryBreakdown(
                category=cat,
                total=round(v["total"], 2),
                percentage=round((v["total"] / expense * 100), 1) if expense > 0 else 0.0,
                count=v["count"],
            )
            for cat, v in cat_map.items()
        ],
        key=lambda x: x.total,
        reverse=True,
    )

    return AnalyticsSummary(
        total_income=round(income, 2),
        total_expense=round(expense, 2),
        net_savings=round(savings, 2),
        savings_rate=savings_rate,
        monthly=monthly,
        by_category=by_category,
    )


@router.get("/history")
async def get_expense_history(
    months: int = Query(6, ge=1, le=24),
    user = Depends(get_current_user),
):
    """Return the last N months of daily expense totals for sparklines."""
    from datetime import timedelta
    end   = date.today()
    start = end - timedelta(days=months * 30)
    txns  = _fetch_txns(user.id, str(start), str(end))

    daily: dict = defaultdict(float)
    for tx in txns:
        if tx["type"] == "debit":
            daily[tx["date"]] += tx["amount"]

    return {
        "data": [
            {"date": d, "amount": round(a, 2)}
            for d, a in sorted(daily.items())
        ]
    }
