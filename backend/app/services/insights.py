"""
AI Insights Service
Builds a financial summary and calls Anthropic Claude to generate
personalized spending insights.
Designed to be voice-assistant-friendly (returns structured JSON).
"""

import json
from datetime import datetime
from typing import List, Dict, Any

import anthropic

from app.core.config import settings
from app.schemas.schemas import InsightItem


SYSTEM_PROMPT = """You are a knowledgeable, empathetic personal finance advisor specializing in Indian household budgeting. Analyze the user's spending data and generate exactly 6 concise, specific, and actionable insights.

Return ONLY a valid JSON array. Each element must have:
- "title": 4-6 word heading
- "body": 2-3 sentences with specific numbers, percentages, or comparisons. Be precise and helpful.
- "type": one of "positive", "warning", "tip", "alert"
- "emoji": a single relevant emoji

Rules:
- Reference actual figures from the data (e.g. "₹3,200 on Shopping")
- For warnings/alerts, always suggest a concrete corrective action
- For tips, provide a specific actionable recommendation
- No generic platitudes — every insight must be data-driven
- Use Indian financial context (Rupees, SIPs, UPI, etc.)
- Do NOT include any markdown, preamble, or explanation outside the JSON array"""


def _build_summary(transactions: List[Dict[str, Any]]) -> str:
    """Construct a compact financial summary string for the LLM prompt."""
    income  = sum(t["amount"] for t in transactions if t["type"] == "credit")
    expense = sum(t["amount"] for t in transactions if t["type"] == "debit")
    savings = income - expense

    # Category totals
    cat_totals: Dict[str, float] = {}
    for tx in transactions:
        if tx["type"] == "debit":
            cat = tx.get("category", "Other")
            cat_totals[cat] = cat_totals.get(cat, 0) + tx["amount"]

    top_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    # Monthly breakdown
    monthly: Dict[str, Dict[str, float]] = {}
    for tx in transactions:
        try:
            d = tx["date"] if isinstance(tx["date"], str) else str(tx["date"])
            ym = d[:7]  # "YYYY-MM"
        except Exception:
            continue
        if ym not in monthly:
            monthly[ym] = {"income": 0, "expense": 0}
        key = "income" if tx["type"] == "credit" else "expense"
        monthly[ym][key] += tx["amount"]

    recent_months = sorted(monthly.items())[-3:]

    summary_parts = [
        f"Period: {len(transactions)} transactions",
        f"Total income: ₹{income:,.0f}",
        f"Total expenses: ₹{expense:,.0f}",
        f"Net savings: ₹{savings:,.0f}",
        f"Savings rate: {(savings/income*100):.1f}%" if income > 0 else "Savings rate: N/A",
        f"Top spending categories: {', '.join(f'{c}:₹{v:,.0f}' for c, v in top_cats)}",
        "Monthly breakdown (last 3): " + ", ".join(
            f"{m}(inc:₹{v['income']:,.0f} exp:₹{v['expense']:,.0f})" for m, v in recent_months
        ),
    ]

    # Detect unusual spikes
    if len(recent_months) >= 2:
        prev_exp = recent_months[-2][1]["expense"]
        curr_exp = recent_months[-1][1]["expense"]
        if prev_exp > 0:
            delta_pct = ((curr_exp - prev_exp) / prev_exp) * 100
            summary_parts.append(
                f"Month-over-month expense change: {delta_pct:+.1f}%"
            )

    return ". ".join(summary_parts)


async def generate_insights(
    transactions: List[Dict[str, Any]],
) -> List[InsightItem]:
    """
    Call Claude to generate spending insights.
    Returns a list of InsightItem objects.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured.")

    if len(transactions) < 3:
        raise ValueError("Need at least 3 transactions to generate insights.")

    summary = _build_summary(transactions)
    client  = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze my finances and give me 6 insights:\n\n{summary}",
            }
        ],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if Claude added them anyway
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw: {raw_text[:300]}")

    return [InsightItem(**item) for item in data]
