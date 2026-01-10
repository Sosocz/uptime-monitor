from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.incident import Incident
from app.models.incident_role import RoleType
from app.schemas.incident import IncidentResponse
from app.services import incident_service

router = APIRouter()


# === Schemas ===

class AcknowledgeRequest(BaseModel):
    """Request to acknowledge an incident."""
    pass


class ResolveRequest(BaseModel):
    """Request to resolve an incident."""
    note: Optional[str] = None


class AssignRoleRequest(BaseModel):
    """Request to assign a role to a user."""
    user_id: int
    role_type: RoleType


class MTTAMTTRResponse(BaseModel):
    """MTTA/MTTR metrics response."""
    total_incidents: int
    acknowledged_incidents: int
    resolved_incidents: int
    mtta_seconds: Optional[int]
    mtta_minutes: Optional[float]
    mttr_seconds: Optional[int]
    mttr_minutes: Optional[float]
    period_days: int


# === Endpoints ===

@router.get("/", response_model=List[IncidentResponse])
def list_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all incidents for the current user's monitors."""
    monitor_ids = [m.id for m in current_user.monitors]
    incidents = db.query(Incident).filter(
        Incident.monitor_id.in_(monitor_ids)
    ).order_by(Incident.started_at.desc()).limit(50).all()

    return incidents


@router.post("/{incident_id}/acknowledge")
def acknowledge_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Acknowledge an incident and calculate MTTA (Mean Time To Acknowledge).

    Better Stack feature: Incident acknowledgment with automatic MTTA tracking.
    """
    try:
        incident = incident_service.acknowledge_incident(
            incident_id,
            current_user.id,
            db
        )
        return {
            "success": True,
            "incident_id": incident.id,
            "status": incident.status.value if incident.status else None,
            "acknowledged_at": incident.acknowledged_at.isoformat() if incident.acknowledged_at else None,
            "time_to_acknowledge_seconds": incident.time_to_acknowledge
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/resolve")
def resolve_incident(
    incident_id: int,
    request: ResolveRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolve an incident and calculate MTTR (Mean Time To Resolve).

    Better Stack feature: Incident resolution with automatic MTTR tracking.
    """
    try:
        incident = incident_service.resolve_incident(
            incident_id,
            db,
            resolution_note=request.note
        )
        return {
            "success": True,
            "incident_id": incident.id,
            "status": incident.status.value if incident.status else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "time_to_resolve_seconds": incident.time_to_resolve,
            "duration_seconds": incident.duration_seconds
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/assign-role")
def assign_incident_role(
    incident_id: int,
    request: AssignRoleRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a role (COMMANDER, DEPUTY, LEAD, RESPONDER) to a user for an incident.

    Better Stack feature: Incident role management.
    """
    try:
        role = incident_service.assign_role(
            incident_id,
            request.user_id,
            request.role_type,
            current_user.id,
            db
        )
        return {
            "success": True,
            "role_id": role.id,
            "incident_id": incident_id,
            "user_id": role.user_id,
            "role_type": role.role_type.value,
            "assigned_at": role.assigned_at.isoformat() if role.assigned_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/mtta-mttr", response_model=MTTAMTTRResponse)
def get_mtta_mttr_metrics(
    service_id: Optional[int] = None,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get MTTA (Mean Time To Acknowledge) and MTTR (Mean Time To Resolve) metrics.

    Better Stack feature: Incident performance metrics.

    Args:
        service_id: Optional filter by service
        days: Number of days to analyze (default: 30)
    """
    metrics = incident_service.get_mtta_mttr_metrics(
        db,
        team_id=current_user.id,
        service_id=service_id,
        days=days
    )

    return metrics


@router.get("/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the timeline of events for an incident.

    Better Stack feature: Incident timeline tracking.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": incident_id,
        "timeline_events": incident.timeline_events or []
    }
