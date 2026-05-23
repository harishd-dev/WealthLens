"""
Transactions Routes — /api/v1/transactions
Full CRUD + filtering/pagination.
All operations are scoped to the authenticated user.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from app.schemas.schemas import (
    TransactionCreate, TransactionUpdate,
    TransactionOut, TransactionListResponse,
)

router = APIRouter()


def _tx_table(user_id: str):
    """Return a Supabase query builder pre-filtered to the user."""
    return get_supabase_client().table("transactions").eq("user_id", user_id)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page:     int           = Query(1, ge=1),
    size:     int           = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    type:     Optional[str] = Query(None),
    search:   Optional[str] = Query(None),
    sort_by:  str           = Query("date"),
    order:    str           = Query("desc"),
    user = Depends(get_current_user),
):
    client = get_supabase_client()
    q = client.table("transactions").select("*", count="exact").eq("user_id", user.id)

    if category:
        q = q.eq("category", category)
    if type:
        q = q.eq("type", type)
    if search:
        q = q.ilike("description", f"%{search}%")

    desc = order.lower() == "desc"
    q = q.order(sort_by, desc=desc)

    offset = (page - 1) * size
    q = q.range(offset, offset + size - 1)

    res = q.execute()
    return TransactionListResponse(
        data=res.data or [],
        total=res.count or 0,
        page=page,
        size=size,
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user = Depends(get_current_user),
):
    client = get_supabase_client()
    payload = {
        **body.model_dump(),
        "user_id": user.id,
        "source":  "manual",
        "date":    str(body.date),
    }
    res = client.table("transactions").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create transaction.")
    return res.data[0]


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(tx_id: str, user = Depends(get_current_user)):
    res = _tx_table(user.id).eq("id", tx_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return res.data


@router.patch("/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: str,
    body:  TransactionUpdate,
    user = Depends(get_current_user),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    if "date" in payload:
        payload["date"] = str(payload["date"])
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update.")

    res = _tx_table(user.id).eq("id", tx_id).update(payload).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return res.data[0]


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: str, user = Depends(get_current_user)):
    res = _tx_table(user.id).eq("id", tx_id).delete().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found.")
