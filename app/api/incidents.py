from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.incident import Incident
from app.schemas.incident import IncidentResponse

router = APIRouter()


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
