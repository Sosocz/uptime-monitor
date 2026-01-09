from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident


def _build_cause(check: Check) -> str:
    """Build a human-readable cause from check data."""
    if check.status_code:
        if check.status_code >= 500:
            return f"Server Error (HTTP {check.status_code})"
        elif check.status_code >= 400:
            return f"Client Error (HTTP {check.status_code})"
        else:
            return f"HTTP {check.status_code}"
    elif check.error_message:
        if "timeout" in check.error_message.lower():
            return "Request Timeout"
        elif "connection" in check.error_message.lower():
            return "Connection Failed"
        elif "dns" in check.error_message.lower() or "name resolution" in check.error_message.lower():
            return "DNS Resolution Failed"
        else:
            return "Network Error"
    return "Unknown Cause"


def _count_consecutive_failures(db: Session, monitor_id: int, current_check: Check) -> int:
    """Count consecutive DOWN checks including the current one."""
    count = 1  # Include current check

    # Get recent checks in descending order (most recent first)
    recent_checks = db.query(Check).filter(
        Check.monitor_id == monitor_id,
        Check.id < current_check.id
    ).order_by(Check.id.desc()).limit(20).all()

    for check in recent_checks:
        if check.status == "down":
            count += 1
        else:
            break

    return count


def detect_and_create_incident(db: Session, monitor: Monitor, current_check: Check):
    """
    Detect status transitions and create/resolve incidents accordingly.

    Returns an Incident object only on state transitions (UP→DOWN or DOWN→UP).
    Implements deduplication to prevent multiple DOWN incidents.
    """
    # Get the previous check
    previous_checks = db.query(Check).filter(
        Check.monitor_id == monitor.id,
        Check.id < current_check.id
    ).order_by(Check.id.desc()).limit(1).all()

    if not previous_checks:
        # First check ever - only create incident if it's DOWN
        if current_check.status == "down":
            cause = _build_cause(current_check)
            incident = Incident(
                monitor_id=monitor.id,
                incident_type="down",
                started_at=datetime.utcnow(),
                status_code=current_check.status_code,
                error_message=current_check.error_message,
                cause=cause,
                failed_checks_count=1
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)
            return incident
        return None

    previous_check = previous_checks[0]

    # === Transition UP → DOWN (new incident) ===
    if previous_check.status == "up" and current_check.status == "down":
        # Check if there's already an open incident (deduplication)
        open_incident = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.resolved_at == None,
            Incident.incident_type == "down"
        ).first()

        if open_incident:
            # Update existing incident instead of creating a new one
            open_incident.failed_checks_count += 1
            db.commit()
            return None  # Don't notify again

        # Create new DOWN incident
        cause = _build_cause(current_check)
        incident = Incident(
            monitor_id=monitor.id,
            incident_type="down",
            started_at=datetime.utcnow(),
            status_code=current_check.status_code,
            error_message=current_check.error_message,
            cause=cause,
            failed_checks_count=1
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    # === Still DOWN - update failure count ===
    if previous_check.status == "down" and current_check.status == "down":
        # Find open incident and increment failure count
        open_incident = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.resolved_at == None,
            Incident.incident_type == "down"
        ).first()

        if open_incident:
            open_incident.failed_checks_count = _count_consecutive_failures(db, monitor.id, current_check)
            db.commit()

        return None  # No notification on continuous DOWN state

    # === Transition DOWN → UP (recovery) ===
    if previous_check.status == "down" and current_check.status == "up":
        # Find and resolve all open DOWN incidents
        open_incidents = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.resolved_at == None,
            Incident.incident_type == "down"
        ).all()

        if not open_incidents:
            return None  # No open incident to resolve

        for incident in open_incidents:
            incident.resolved_at = datetime.utcnow()
            incident.incident_type = "recovery"

            # Calculate duration in seconds
            if incident.started_at:
                duration = (incident.resolved_at - incident.started_at).total_seconds()
                incident.duration_seconds = int(duration)

        db.commit()
        return open_incidents[0]  # Return first incident for notification

    # === Still UP - no incident ===
    return None
