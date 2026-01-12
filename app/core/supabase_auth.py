import httpx
from app.core.config import settings


async def fetch_supabase_user(token: str) -> dict | None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_ANON_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
