import os


def _is_production() -> bool:
    env = (os.getenv("APP_ENV") or "development").lower()
    return env in {"production", "prod"}


def apply_template_globals(templates) -> None:
    site_url = (os.getenv("SITE_URL") or "https://trezapp.fr").rstrip("/")
    analytics = {
        "is_production": _is_production(),
        "posthog_api_key": os.getenv("POSTHOG_API_KEY"),
        "posthog_host": os.getenv("POSTHOG_HOST") or "https://app.posthog.com",
        "posthog_proxy_host": os.getenv("POSTHOG_PROXY_HOST"),
        "clarity_id": os.getenv("CLARITY_ID"),
        "ga_measurement_id": os.getenv("GA_MEASUREMENT_ID"),
    }
    supabase = {
        "url": os.getenv("SUPABASE_URL") or "",
        "anon_key": os.getenv("SUPABASE_ANON_KEY") or "",
    }
    site = {
        "url": site_url,
        "name": "TrezApp",
    }
    templates.env.globals["analytics"] = analytics
    templates.env.globals["supabase"] = supabase
    templates.env.globals["site"] = site
