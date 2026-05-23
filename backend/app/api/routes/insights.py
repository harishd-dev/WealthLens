"""
Insights Routes — /api/v1/insights
Proxies to Claude via the insights service.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from app.schemas.schemas import InsightsResponse
from app.services.insights import generate_insights

router = APIRouter()


@router.post("", response_model=InsightsResponse)
async def get_insights(user = Depends(get_current_user)):
    """Generate AI-powered spending insights for the authenticated user."""
    client = get_supabase_client()
    res    = (
        client.table("transactions")
        .select("amount,type,category,date,description")
        .eq("user_id", user.id)
        .order("date", desc=True)
        .limit(300)          # cap context window cost
        .execute()
    )
    txns = res.data or []

    if len(txns) < 3:
        raise HTTPException(
            status_code=422,
            detail="Need at least 3 transactions to generate insights.",
        )

    try:
        items = await generate_insights(txns)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return InsightsResponse(
        insights=items,
        generated_at=datetime.utcnow(),
        tx_count=len(txns),
    )
