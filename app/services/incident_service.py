from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident, IncidentStatus
from app.models.incident_role import IncidentRole, RoleType


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


# === Better Stack Features ===

def acknowledge_incident(
    incident_id: int,
    acknowledged_by_id: int,
    db: Session
) -> Incident:
    """
    Acknowledge an incident and calculate MTTA.

    Args:
        incident_id: Incident ID
        acknowledged_by_id: User acknowledging the incident
        db: Database session

    Returns:
        Updated incident
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise ValueError("Incident not found")

    if incident.status and incident.status != IncidentStatus.OPEN:
        raise ValueError(f"Cannot acknowledge incident with status {incident.status}")

    now = datetime.utcnow()
    incident.status = IncidentStatus.ACKNOWLEDGED
    incident.acknowledged_at = now
    incident.acknowledged_by_id = acknowledged_by_id

    # Calculate MTTA (Mean Time To Acknowledge)
    time_delta = now - incident.started_at
    incident.time_to_acknowledge = int(time_delta.total_seconds())

    # Add timeline event
    _add_timeline_event(
        incident,
        "acknowledged",
        acknowledged_by_id,
        {"acknowledged_at": now.isoformat()}
    )

    db.commit()
    db.refresh(incident)

    return incident


def resolve_incident(
    incident_id: int,
    db: Session,
    resolution_note: Optional[str] = None
) -> Incident:
    """
    Resolve an incident and calculate MTTR.

    Args:
        incident_id: Incident ID
        db: Database session
        resolution_note: Optional resolution note

    Returns:
        Updated incident
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise ValueError("Incident not found")

    if incident.status == IncidentStatus.RESOLVED:
        raise ValueError("Incident is already resolved")

    now = datetime.utcnow()
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = now

    # Calculate duration
    time_delta = now - incident.started_at
    incident.duration_seconds = int(time_delta.total_seconds())

    # Calculate MTTR (Mean Time To Resolve)
    incident.time_to_resolve = incident.duration_seconds

    # Add timeline event
    event_data = {"resolved_at": now.isoformat()}
    if resolution_note:
        event_data["note"] = resolution_note

    _add_timeline_event(
        incident,
        "resolved",
        None,
        event_data
    )

    db.commit()
    db.refresh(incident)

    return incident


def assign_role(
    incident_id: int,
    user_id: int,
    role_type: RoleType,
    assigned_by_id: int,
    db: Session
) -> IncidentRole:
    """
    Assign a role to a user for an incident.

    Args:
        incident_id: Incident ID
        user_id: User to assign role to
        role_type: Type of role (COMMANDER, DEPUTY, LEAD, RESPONDER)
        assigned_by_id: User making the assignment
        db: Database session

    Returns:
        Created incident role
    """
    # Check if role already assigned
    existing = db.query(IncidentRole).filter(
        IncidentRole.incident_id == incident_id,
        IncidentRole.role_type == role_type
    ).first()

    if existing:
        # Update existing role
        existing.user_id = user_id
        existing.assigned_by_id = assigned_by_id
        existing.assigned_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    # Create new role
    role = IncidentRole(
        incident_id=incident_id,
        user_id=user_id,
        role_type=role_type,
        assigned_by_id=assigned_by_id
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    # Add timeline event
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        _add_timeline_event(
            incident,
            "role_assigned",
            assigned_by_id,
            {
                "role": role_type.value,
                "assigned_to_user_id": user_id
            }
        )
        db.commit()

    return role


def get_mtta_mttr_metrics(
    db: Session,
    team_id: Optional[int] = None,
    service_id: Optional[int] = None,
    days: int = 30
) -> Dict:
    """
    Calculate MTTA and MTTR metrics.

    Args:
        db: Database session
        team_id: Optional team filter
        service_id: Optional service filter
        days: Number of days to analyze

    Returns:
        Dict with MTTA, MTTR, and count metrics
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(Incident).filter(
        Incident.started_at >= start_date
    )

    if service_id:
        query = query.filter(Incident.service_id == service_id)

    incidents = query.all()

    if not incidents:
        return {
            "total_incidents": 0,
            "acknowledged_incidents": 0,
            "resolved_incidents": 0,
            "mtta_seconds": None,
            "mtta_minutes": None,
            "mttr_seconds": None,
            "mttr_minutes": None,
            "period_days": days
        }

    # Calculate MTTA (only for acknowledged incidents)
    acknowledged = [i for i in incidents if i.time_to_acknowledge is not None]
    mtta_seconds = None
    if acknowledged:
        mtta_seconds = sum(i.time_to_acknowledge for i in acknowledged) / len(acknowledged)

    # Calculate MTTR (only for resolved incidents)
    resolved = [i for i in incidents if i.time_to_resolve is not None]
    mttr_seconds = None
    if resolved:
        mttr_seconds = sum(i.time_to_resolve for i in resolved) / len(resolved)

    return {
        "total_incidents": len(incidents),
        "acknowledged_incidents": len(acknowledged),
        "resolved_incidents": len(resolved),
        "mtta_seconds": int(mtta_seconds) if mtta_seconds else None,
        "mtta_minutes": round(mtta_seconds / 60, 2) if mtta_seconds else None,
        "mttr_seconds": int(mttr_seconds) if mttr_seconds else None,
        "mttr_minutes": round(mttr_seconds / 60, 2) if mttr_seconds else None,
        "period_days": days
    }


def _add_timeline_event(
    incident: Incident,
    event_type: str,
    user_id: Optional[int],
    details: Dict
):
    """
    Add an event to the incident timeline.

    Args:
        incident: Incident object
        event_type: Type of event
        user_id: User performing the action (optional)
        details: Event details
    """
    if incident.timeline_events is None:
        incident.timeline_events = []

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "user_id": user_id,
        **details
    }

    # SQLAlchemy doesn't detect changes to JSONB arrays by default
    # We need to explicitly mark as modified
    timeline = list(incident.timeline_events)
    timeline.append(event)
    incident.timeline_events = timeline
