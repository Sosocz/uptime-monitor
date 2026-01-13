import os

import sentry_sdk


def _is_production() -> bool:
    env = (os.getenv("APP_ENV") or "development").lower()
    return env in {"production", "prod"}


def init_sentry() -> bool:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn or not _is_production():
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV") or "production",
        traces_sample_rate=0.0,
    )
    return True
