import httpx
from app.core.config import settings


async def fetch_supabase_user(token: str) -> dict | None:
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not configured.")

    api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not api_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": api_key,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
