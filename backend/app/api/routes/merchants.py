"""
Merchants Routes — /api/v1/merchants
Manage the user's merchant → category learning table.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from app.schemas.schemas import MerchantMappingCreate, MerchantMappingOut

router = APIRouter()


@router.get("", response_model=list[MerchantMappingOut])
async def list_mappings(user = Depends(get_current_user)):
    """Return all learned merchant → category mappings for this user."""
    client = get_supabase_client()
    res = (
        client.table("merchant_mappings")
        .select("*")
        .eq("user_id", user.id)
        .order("merchant_key")
        .execute()
    )
    return res.data or []


@router.post("", response_model=MerchantMappingOut, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    body: MerchantMappingCreate,
    user = Depends(get_current_user),
):
    """Save a new merchant → category mapping."""
    client = get_supabase_client()
    payload = {
        "id":           str(uuid.uuid4()),
        "user_id":      user.id,
        "merchant_key": body.merchant_key.lower().strip(),
        "category":     body.category,
    }
    res = (
        client.table("merchant_mappings")
        .upsert(payload, on_conflict="user_id,merchant_key")
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="Could not save mapping.")
    return res.data[0]


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(mapping_id: str, user = Depends(get_current_user)):
    """Remove a learned mapping."""
    client = get_supabase_client()
    res = (
        client.table("merchant_mappings")
        .delete()
        .eq("id", mapping_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Mapping not found.")
