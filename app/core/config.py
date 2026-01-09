from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_MONTHLY: str
    STRIPE_PRICE_ID_PRO_YEARLY: str = "price_xxxxx"  # Annual PRO plan (€180/year)
    STRIPE_PRICE_ID_AGENCY_MONTHLY: str = "price_xxxxx"  # Agency plan (€99/month)
    STRIPE_PRICE_ID_AGENCY_YEARLY: str = "price_xxxxx"  # Agency plan (€950/year)

    # App
    APP_BASE_URL: str

    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Notifications
    NOTIFICATION_COOLDOWN_SECONDS: int = 300  # 5 minutes cooldown between duplicate notifications
    MAX_NOTIFICATION_RETRIES: int = 3

    class Config:
        env_file = ".env"


settings = Settings()


# Plan limits and features
PLAN_LIMITS = {
    "FREE": {
        "max_monitors": 10,
        "check_interval_min": 300,  # 5 min
        "team_members": 1,
        "webhooks": 0,
        "custom_domains": False,
        "status_pages": True,
        "white_label": False,
        "api_rate_limit": 10,  # req/min
        "priority_support": False,
    },
    "PAID": {  # PRO plan
        "max_monitors": -1,  # unlimited
        "check_interval_min": 60,  # 1 min
        "team_members": 1,
        "webhooks": 5,
        "custom_domains": False,
        "status_pages": True,
        "white_label": True,
        "api_rate_limit": 100,  # req/min
        "priority_support": False,
    },
    "AGENCY": {
        "max_monitors": -1,  # unlimited
        "check_interval_min": 60,  # 1 min
        "team_members": -1,  # unlimited
        "webhooks": -1,  # unlimited
        "custom_domains": True,
        "status_pages": True,
        "white_label": True,
        "api_rate_limit": 1000,  # req/min
        "priority_support": True,
        "sub_accounts": True,
        "white_label_reports": True,
        "sla": "99.9%",
    }
}


def get_plan_limit(plan: str, feature: str) -> any:
    """Get limit for a specific feature based on user plan."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["FREE"]).get(feature)


def can_create_monitor(plan: str, current_count: int) -> bool:
    """Check if user can create a new monitor based on plan."""
    max_monitors = get_plan_limit(plan, "max_monitors")
    if max_monitors == -1:  # unlimited
        return True
    return current_count < max_monitors


def get_min_check_interval(plan: str) -> int:
    """Get minimum check interval allowed for plan (in seconds)."""
    return get_plan_limit(plan, "check_interval_min")
