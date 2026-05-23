"""
Analytics Utilities
Helper functions for computing financial metrics server-side.
Designed to be voice-assistant-friendly (returns plain dicts).
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import List, Dict, Any, Optional


def compute_summary(transactions: List[Dict[str, Any]]) -> Dict:
    """Full financial summary from a list of transaction dicts."""
    income  = sum(t["amount"] for t in transactions if t["type"] == "credit")
    expense = sum(t["amount"] for t in transactions if t["type"] == "debit")
    savings = income - expense
    savings_rate = round((savings / income * 100), 2) if income > 0 else 0.0

    return {
        "total_income":  round(income, 2),
        "total_expense": round(expense, 2),
        "net_savings":   round(savings, 2),
        "savings_rate":  savings_rate,
        "tx_count":      len(transactions),
    }


def compute_monthly(transactions: List[Dict[str, Any]]) -> List[Dict]:
    """Aggregate transactions by month → list sorted chronologically."""
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly: Dict[tuple, Dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})

    for tx in transactions:
        d   = date.fromisoformat(str(tx["date"]))
        key = (d.year, d.month)
        if tx["type"] == "credit":
            monthly[key]["income"] += tx["amount"]
        else:
            monthly[key]["expense"] += tx["amount"]

    return [
        {
            "month":   MONTHS[m - 1],
            "year":    y,
            "income":  round(v["income"],  2),
            "expense": round(v["expense"], 2),
            "savings": round(v["income"] - v["expense"], 2),
        }
        for (y, m), v in sorted(monthly.items())
    ]


def compute_category_breakdown(transactions: List[Dict[str, Any]]) -> List[Dict]:
    """Return expense totals per category, sorted descending."""
    cat_map: Dict[str, Dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    expense_total = sum(t["amount"] for t in transactions if t["type"] == "debit")

    for tx in transactions:
        if tx["type"] == "debit":
            cat = tx.get("category") or "Other"
            cat_map[cat]["total"] += tx["amount"]
            cat_map[cat]["count"] += 1

    return sorted(
        [
            {
                "category":   cat,
                "total":      round(v["total"], 2),
                "percentage": round(v["total"] / expense_total * 100, 1) if expense_total > 0 else 0.0,
                "count":      v["count"],
            }
            for cat, v in cat_map.items()
        ],
        key=lambda x: x["total"],
        reverse=True,
    )


def detect_anomalies(transactions: List[Dict[str, Any]]) -> List[Dict]:
    """
    Simple anomaly detection:
    Flag transactions whose amount is > 2 std-deviations above
    the per-category mean.
    """
    import math

    # Group by category
    cat_amounts: Dict[str, List[float]] = defaultdict(list)
    for tx in transactions:
        if tx["type"] == "debit":
            cat = tx.get("category") or "Other"
            cat_amounts[cat].append(tx["amount"])

    # Compute mean + std per category
    stats: Dict[str, Dict] = {}
    for cat, amounts in cat_amounts.items():
        if len(amounts) < 3:
            continue
        mean = sum(amounts) / len(amounts)
        variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
        std  = math.sqrt(variance)
        stats[cat] = {"mean": mean, "std": std}

    anomalies = []
    for tx in transactions:
        if tx["type"] != "debit":
            continue
        cat = tx.get("category") or "Other"
        if cat not in stats:
            continue
        s = stats[cat]
        if s["std"] > 0 and (tx["amount"] - s["mean"]) > 2 * s["std"]:
            anomalies.append({
                "transaction": tx,
                "category":    cat,
                "amount":      tx["amount"],
                "mean":        round(s["mean"], 2),
                "deviation":   round((tx["amount"] - s["mean"]) / s["std"], 1),
            })

    return sorted(anomalies, key=lambda x: x["deviation"], reverse=True)


def compute_savings_trend(
    transactions: List[Dict[str, Any]],
    months: int = 3,
) -> Dict:
    """
    Compare savings of the last N months vs the N months before that.
    Returns trend direction and percentage change.
    """
    today    = date.today()
    recent_start = today.replace(day=1) - timedelta(days=months * 30)
    prior_start  = recent_start - timedelta(days=months * 30)

    def savings_for_range(start: date, end: date) -> float:
        inc = exp = 0.0
        for tx in transactions:
            d = date.fromisoformat(str(tx["date"]))
            if start <= d <= end:
                if tx["type"] == "credit":
                    inc += tx["amount"]
                else:
                    exp += tx["amount"]
        return inc - exp

    recent_savings = savings_for_range(recent_start, today)
    prior_savings  = savings_for_range(prior_start, recent_start)

    if prior_savings == 0:
        change_pct = None
    else:
        change_pct = round((recent_savings - prior_savings) / abs(prior_savings) * 100, 1)

    return {
        "recent_savings": round(recent_savings, 2),
        "prior_savings":  round(prior_savings, 2),
        "change_pct":     change_pct,
        "trend":          "up" if (change_pct or 0) > 0 else "down",
    }


def top_spending_days(
    transactions: List[Dict[str, Any]],
    n: int = 5,
) -> List[Dict]:
    """Return the N days with highest total spending."""
    daily: Dict[str, float] = defaultdict(float)
    for tx in transactions:
        if tx["type"] == "debit":
            daily[str(tx["date"])] += tx["amount"]

    return sorted(
        [{"date": d, "total": round(v, 2)} for d, v in daily.items()],
        key=lambda x: x["total"],
        reverse=True,
    )[:n]
