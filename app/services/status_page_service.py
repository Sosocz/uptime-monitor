"""
Status page service - calculates uptime statistics and incident history.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident


def calculate_uptime_percentage(db: Session, monitor_id: int, days: int = 7) -> float:
    """
    Calculate uptime percentage for a monitor over the last N days.

    Args:
        db: Database session
        monitor_id: Monitor ID
        days: Number of days to calculate (default: 7)

    Returns:
        Uptime percentage (0-100)
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get all checks in the period
    total_checks = db.query(Check).filter(
        Check.monitor_id == monitor_id,
        Check.checked_at >= since
    ).count()

    if total_checks == 0:
        return 100.0

    # Count successful checks
    successful_checks = db.query(Check).filter(
        Check.monitor_id == monitor_id,
        Check.checked_at >= since,
        Check.status == "up"
    ).count()

    uptime = (successful_checks / total_checks) * 100
    return round(uptime, 2)


def get_average_response_time(db: Session, monitor_id: int, days: int = 7) -> float:
    """
    Calculate average response time for successful checks.

    Args:
        db: Database session
        monitor_id: Monitor ID
        days: Number of days to calculate (default: 7)

    Returns:
        Average response time in milliseconds
    """
    since = datetime.utcnow() - timedelta(days=days)

    avg_response_time = db.query(func.avg(Check.response_time)).filter(
        Check.monitor_id == monitor_id,
        Check.checked_at >= since,
        Check.status == "up",
        Check.response_time.isnot(None)
    ).scalar()

    return round(avg_response_time, 2) if avg_response_time else 0.0


def get_recent_incidents(db: Session, monitor_id: int, limit: int = 10):
    """
    Get recent incidents for a monitor.

    Args:
        db: Database session
        monitor_id: Monitor ID
        limit: Maximum number of incidents to return

    Returns:
        List of incidents with duration
    """
    incidents = db.query(Incident).filter(
        Incident.monitor_id == monitor_id
    ).order_by(Incident.started_at.desc()).limit(limit).all()

    result = []
    for incident in incidents:
        result.append({
            "id": incident.id,
            "type": incident.incident_type,
            "started_at": incident.started_at.isoformat() if incident.started_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "duration_seconds": incident.duration_seconds,
            "cause": incident.cause,
            "failed_checks_count": incident.failed_checks_count
        })

    return result


def get_daily_uptime(db: Session, monitor_id: int, days: int = 90):
    """
    Get uptime percentage for each day.

    Args:
        db: Database session
        monitor_id: Monitor ID
        days: Number of days to retrieve (default: 90)

    Returns:
        List of {date, uptime_percentage} dictionaries
    """
    result = []
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())

        # Count total checks for the day
        total = db.query(Check).filter(
            Check.monitor_id == monitor_id,
            Check.checked_at >= start_of_day,
            Check.checked_at <= end_of_day
        ).count()

        if total == 0:
            continue

        # Count successful checks
        successful = db.query(Check).filter(
            Check.monitor_id == monitor_id,
            Check.checked_at >= start_of_day,
            Check.checked_at <= end_of_day,
            Check.status == "up"
        ).count()

        uptime = (successful / total) * 100

        result.append({
            "date": date.isoformat(),
            "uptime_percentage": round(uptime, 2),
            "total_checks": total
        })

    return list(reversed(result))  # Oldest first
