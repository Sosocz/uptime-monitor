from supabase import Client, create_client
from app.core.config import settings


def get_supabase_admin() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_ANON_KEY is not configured.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
