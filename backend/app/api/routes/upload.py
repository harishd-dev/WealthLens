"""
Upload Routes — /api/v1/upload
Two-step flow:
  POST /preview  → parse file, categorize, return preview
  POST /confirm  → user-confirmed list (with filled categories) → save to DB
"""

import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from app.schemas.schemas import (
    UploadPreviewResponse, UploadConfirmRequest, UploadConfirmResponse,
    ParsedTransaction,
)
from app.services.parser import parse_csv, parse_pdf
from app.services.categorization import categorize_with_learning

router = APIRouter()

MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def _get_learned_mappings(user_id: str) -> dict:
    """Fetch user's merchant-learning mappings from Supabase."""
    client = get_supabase_client()
    res = (
        client.table("merchant_mappings")
        .select("merchant_key, category")
        .eq("user_id", user_id)
        .execute()
    )
    return {row["merchant_key"]: row["category"] for row in (res.data or [])}


@router.post("/preview", response_model=UploadPreviewResponse)
async def preview_upload(
    file: UploadFile = File(...),
    user = Depends(get_current_user),
):
    """
    Step 1: Parse the uploaded file, auto-categorize, return preview.
    The frontend shows this to the user so they can assign unknown categories.
    """
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_MB} MB.",
        )

    # Parse raw transactions
    try:
        raw_txns = parse_csv(content) if ext == "csv" else parse_pdf(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Load merchant learning mappings
    learned = _get_learned_mappings(user.id)

    # Apply two-layer categorization
    parsed = []
    auto_count = 0
    review_count = 0

    for tx in raw_txns:
        cat, needs_review = categorize_with_learning(tx["description"], learned)
        if needs_review:
            review_count += 1
        else:
            auto_count += 1

        parsed.append(ParsedTransaction(
            temp_id=str(uuid.uuid4()),
            date=tx["date"],
            description=tx["description"],
            amount=tx["amount"],
            type=tx["type"],
            category=cat,
            needs_review=needs_review,
        ))

    return UploadPreviewResponse(
        transactions=parsed,
        total=len(parsed),
        auto_categorized=auto_count,
        needs_review=review_count,
        file_name=filename,
    )


@router.post("/confirm", response_model=UploadConfirmResponse)
async def confirm_upload(
    body: UploadConfirmRequest,
    user = Depends(get_current_user),
):
    """
    Step 2: Save confirmed transactions + persist any new merchant mappings.
    """
    client = get_supabase_client()

    # Bulk-insert transactions
    rows = [
        {
            **tx.model_dump(),
            "id":      str(uuid.uuid4()),
            "user_id": user.id,
            "source":  "upload",
            "date":    str(tx.date),
        }
        for tx in body.transactions
    ]

    if rows:
        res = client.table("transactions").insert(rows).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save transactions.")

    # Persist new merchant mappings (upsert to avoid duplicates)
    mappings_saved = 0
    if body.save_mappings:
        mapping_rows = [
            {
                "id":           str(uuid.uuid4()),
                "user_id":      user.id,
                "merchant_key": m["merchant_key"],
                "category":     m["category"],
            }
            for m in body.save_mappings
            if m.get("merchant_key") and m.get("category")
        ]
        if mapping_rows:
            client.table("merchant_mappings").upsert(
                mapping_rows, on_conflict="user_id,merchant_key"
            ).execute()
            mappings_saved = len(mapping_rows)

    return UploadConfirmResponse(
        imported=len(rows),
        mappings_saved=mappings_saved,
    )
