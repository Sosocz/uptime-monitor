import os
from datetime import datetime
from typing import Any

import httpx


def _is_production() -> bool:
    env = (os.getenv("APP_ENV") or "development").lower()
    return env in {"production", "prod"}


def _analytics_enabled() -> bool:
    if not _is_production():
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return True


def _posthog_config() -> tuple[str | None, str | None]:
    api_key = os.getenv("POSTHOG_API_KEY")
    host = os.getenv("POSTHOG_HOST") or "https://app.posthog.com"
    return api_key, host


def track_event(event_name: str, user_id: int | None = None, properties: dict[str, Any] | None = None) -> bool:
    """Send a product analytics event when enabled; otherwise no-op."""
    if not _analytics_enabled():
        return False

    api_key, host = _posthog_config()
    if not api_key:
        return False

    payload = {
        "api_key": api_key,
        "event": event_name,
        "distinct_id": str(user_id or "anonymous"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "properties": {
            "source": "backend",
            **(properties or {}),
        },
    }

    try:
        httpx.post(
            f"{host.rstrip('/')}/capture/",
            json=payload,
            timeout=2.0,
        )
    except Exception:
        return False

    return True
