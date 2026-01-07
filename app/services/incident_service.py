from datetime import datetime
from sqlalchemy.orm import Session
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident


def detect_and_create_incident(db: Session, monitor: Monitor, current_check: Check):
    """Detect status transitions and create/resolve incidents accordingly."""
    # Get the previous check
    previous_checks = db.query(Check).filter(
        Check.monitor_id == monitor.id,
        Check.id < current_check.id
    ).order_by(Check.id.desc()).limit(1).all()
    
    if not previous_checks:
        return None
    
    previous_check = previous_checks[0]
    
    # Transition up -> down (new incident)
    if previous_check.status == "up" and current_check.status in ["down", "timeout", "error"]:
        incident = Incident(
            monitor_id=monitor.id,
            incident_type="down",
            started_at=datetime.utcnow()
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident
    
    # Transition down -> up (recovery)
    if previous_check.status in ["down", "timeout", "error"] and current_check.status == "up":
        # Find and resolve open incidents
        open_incidents = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.resolved_at == None
        ).all()
        
        for incident in open_incidents:
            incident.resolved_at = datetime.utcnow()
            incident.incident_type = "recovery"
        
        db.commit()
        return open_incidents[0] if open_incidents else None
    
    return None
