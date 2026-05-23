"""
Supabase client singleton.
Uses the service-role key for server-side operations (bypasses RLS).
All user-facing calls that should respect RLS pass the user JWT instead.
"""

from functools import lru_cache
from supabase import create_client, Client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached admin Supabase client."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )


def get_user_client(jwt: str) -> Client:
    """Return a Supabase client scoped to a specific user's JWT."""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    client.auth.set_session(jwt, "")
    return client


async def init_db():
    """
    Run on startup: verify Supabase connectivity.
    Table creation is handled via Supabase migrations (see /docs/supabase_setup.sql).
    """
    try:
        client = get_supabase_client()
        client.table("transactions").select("id").limit(1).execute()
        print("✅ Supabase connection established")
    except Exception as e:
        print(f"⚠️  Supabase connection warning: {e}")
        print("   Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in .env")
