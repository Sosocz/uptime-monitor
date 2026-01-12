import logging
from datetime import datetime

from app.services.analytics import track_event as analytics_track_event

logger = logging.getLogger(__name__)


def track_event(db_or_event, event_name: str = None, user_id: int = None, event_data: dict = None, properties: dict = None):
    """Track an event for analytics."""
    if event_name is None:
        event_name = db_or_event
    payload = properties if properties is not None else event_data
    logger.info("[TRACK] %s - %s - user:%s - %s", datetime.utcnow(), event_name, user_id, payload)
    analytics_track_event(event_name, user_id=user_id, properties=payload)
    return True
