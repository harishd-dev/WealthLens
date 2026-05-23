"""
Auth Routes — /api/v1/auth
Delegates to Supabase Auth for all identity operations.
"""

from fastapi import APIRouter, HTTPException, status
from supabase import AuthApiError

from app.db.supabase import get_supabase_client
from app.schemas.schemas import (
    SignUpRequest, LoginRequest, AuthResponse, PasswordResetRequest
)

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    """Create a new user account via Supabase Auth."""
    client = get_supabase_client()
    try:
        res = client.auth.sign_up({
            "email":    body.email,
            "password": body.password,
            "options":  {"data": {"name": body.name}},
        })
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed.")
        return AuthResponse(
            access_token=res.session.access_token if res.session else "",
            user_id=res.user.id,
            email=res.user.email,
            name=body.name,
        )
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Authenticate and return a Supabase session token."""
    client = get_supabase_client()
    try:
        res = client.auth.sign_in_with_password({
            "email": body.email, "password": body.password
        })
        user_meta = res.user.user_metadata or {}
        return AuthResponse(
            access_token=res.session.access_token,
            user_id=res.user.id,
            email=res.user.email,
            name=user_meta.get("name"),
        )
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(body: PasswordResetRequest):
    """Send a password-reset email via Supabase."""
    client = get_supabase_client()
    try:
        client.auth.reset_password_email(body.email)
        return {"message": "Password reset email sent if account exists."}
    except Exception:
        return {"message": "Password reset email sent if account exists."}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """Client should discard the token; server-side Supabase invalidation."""
    return {"message": "Logged out successfully."}
