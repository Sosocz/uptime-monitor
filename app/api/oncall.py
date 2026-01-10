"""
On-Call API Routes
Endpoints for on-call schedule management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.oncall import OnCallSchedule, OnCallShift, CoverRequest
from app.services.oncall_service import OnCallService

router = APIRouter()


# === Schemas ===

class OnCallUserResponse(BaseModel):
    schedule_id: int
    schedule_name: str
    user_id: int
    timezone: str

    class Config:
        from_attributes = True


class ShiftResponse(BaseModel):
    id: int
    schedule_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    is_override: bool
    is_active: bool

    class Config:
        from_attributes = True


# === Endpoints ===

@router.get("/who-is-oncall", response_model=List[OnCallUserResponse])
def get_who_is_oncall(
    schedule_id: Optional[int] = Query(None, description="Filter by schedule ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get currently on-call users across all schedules or for a specific schedule.

    This is a quick-win feature from Better Stack that shows who is currently on-call.
    """
    if schedule_id:
        # Get specific schedule's on-call user
        user_id = OnCallService.get_current_oncall_user(schedule_id, db)
        if not user_id:
            return []

        schedule = db.query(OnCallSchedule).filter(
            OnCallSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return [{
            "schedule_id": schedule.id,
            "schedule_name": schedule.name,
            "user_id": user_id,
            "timezone": schedule.timezone
        }]

    # Get all on-call users
    return OnCallService.get_all_oncall_users(db)


@router.get("/schedules", response_model=List[dict])
def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all on-call schedules for the current user's team.
    """
    schedules = db.query(OnCallSchedule).filter(
        OnCallSchedule.team_id == current_user.id,
        OnCallSchedule.is_active == True
    ).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "timezone": s.timezone,
            "rotation_type": s.rotation_type.value if s.rotation_type else None,
            "rotation_interval_hours": s.rotation_interval_hours,
            "is_active": s.is_active
        }
        for s in schedules
    ]


@router.get("/schedules/{schedule_id}/shifts", response_model=List[ShiftResponse])
def get_schedule_shifts(
    schedule_id: int,
    days: int = Query(7, description="Number of days to look ahead"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming shifts for a schedule.
    """
    schedule = db.query(OnCallSchedule).filter(
        OnCallSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    shifts = OnCallService.get_upcoming_shifts(schedule_id, days, db)

    return shifts
