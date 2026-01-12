import os


def _is_production() -> bool:
    env = (os.getenv("APP_ENV") or "development").lower()
    return env in {"production", "prod"}


def apply_template_globals(templates) -> None:
    analytics = {
        "is_production": _is_production(),
        "posthog_api_key": os.getenv("POSTHOG_API_KEY"),
        "posthog_host": os.getenv("POSTHOG_HOST") or "https://app.posthog.com",
        "clarity_id": os.getenv("CLARITY_ID"),
        "ga_measurement_id": os.getenv("GA_MEASUREMENT_ID"),
    }
    templates.env.globals["analytics"] = analytics
