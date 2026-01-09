from datetime import datetime

def track_event(event_name: str, user_id: int = None, properties: dict = None):
    """Track an event for analytics"""
    print(f"[TRACK] {datetime.utcnow()} - {event_name} - user:{user_id} - {properties}")
    return True
