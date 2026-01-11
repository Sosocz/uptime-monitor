from datetime import datetime


def track_event(db_or_event, event_name: str = None, user_id: int = None, event_data: dict = None, properties: dict = None):
    """Track an event for analytics."""
    if event_name is None:
        event_name = db_or_event
    payload = properties if properties is not None else event_data
    print(f"[TRACK] {datetime.utcnow()} - {event_name} - user:{user_id} - {payload}")
    return True
