from sqlalchemy.orm import Session
from app.models.user import User


def get_monitor_limit(user: User) -> int:
    """Get the maximum number of monitors allowed for a user based on their plan."""
    if user.plan == "PAID":
        return 50
    return 1


def get_check_interval(user: User) -> int:
    """Get the check interval in seconds based on user's plan."""
    if user.plan == "PAID":
        return 60  # 1 minute
    return 600  # 10 minutes


def can_create_monitor(db: Session, user: User) -> bool:
    """Check if a user can create a new monitor based on their plan limits."""
    current_count = len(user.monitors)
    limit = get_monitor_limit(user)
    return current_count < limit

def get_user_limits(user: User) -> dict:
    """Return plan limits in the format expected by monitors API."""
    return {
        "max_monitors": get_monitor_limit(user),
        "check_interval": get_check_interval(user),
    }
