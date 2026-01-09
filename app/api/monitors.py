from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from app.core.deps import get_db, get_current_user
from app.core.security_ssrf import validate_url_for_ssrf
from app.models.user import User
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident
from app.schemas.monitor import MonitorCreate, MonitorUpdate, MonitorResponse
from app.schemas.check import CheckResponse
from app.services.subscription_service import get_user_limits
from app.services.tracking_service import track_event

router = APIRouter()


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get global dashboard stats for revenue protector."""
    monitor_ids = [m.id for m in db.query(Monitor).filter(Monitor.user_id == current_user.id).all()]

    if not monitor_ids:
        return {
            "money_protected_this_month": 0,
            "incidents_detected_this_month": 0,
            "minutes_saved_this_month": 0,
            "plan": current_user.plan
        }

    # This month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    month_incidents = db.query(Incident).filter(
        Incident.monitor_id.in_(monitor_ids),
        Incident.started_at >= month_start
    ).all()

    money_protected = sum(inc.money_lost or 0 for inc in month_incidents)
    minutes_saved = sum(inc.minutes_lost or 0 for inc in month_incidents)
    incidents_count = len(month_incidents)

    return {
        "money_protected_this_month": money_protected,
        "incidents_detected_this_month": incidents_count,
        "minutes_saved_this_month": minutes_saved,
        "plan": current_user.plan
    }


@router.get("/dashboard/enriched")
def get_monitors_enriched(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get monitors with enriched dashboard data including money lost today."""
    monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).all()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    enriched_monitors = []
    for monitor in monitors:
        # Calculate money lost today
        today_incidents = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.started_at >= today_start
        ).all()

        money_lost_today = sum(inc.money_lost or 0 for inc in today_incidents)
        minutes_lost_today = sum(inc.minutes_lost or 0 for inc in today_incidents)
        incidents_today = len(today_incidents)

        enriched_monitors.append({
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "interval": monitor.interval,
            "timeout": monitor.timeout,
            "is_active": monitor.is_active,
            "last_status": monitor.last_status,
            "last_checked_at": monitor.last_checked_at,
            "created_at": monitor.created_at,
            "health_score": monitor.health_score,
            "health_grade": monitor.health_grade,
            "is_flapping": monitor.is_flapping,
            "is_degrading": monitor.is_degrading,
            "tags": monitor.tags,
            "estimated_revenue_per_hour": monitor.estimated_revenue_per_hour,
            # Today's stats
            "money_lost_today": money_lost_today,
            "minutes_lost_today": minutes_lost_today,
            "incidents_today": incidents_today
        })

    return enriched_monitors


@router.get("", response_model=List[MonitorResponse])
@router.get("/", response_model=List[MonitorResponse], include_in_schema=False)
def get_monitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).all()
    return monitors


@router.post("", response_model=MonitorResponse)
@router.post("/", response_model=MonitorResponse, include_in_schema=False)
def create_monitor(monitor_data: MonitorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # SSRF Protection: Validate URL before creating monitor
    is_valid, error_msg = validate_url_for_ssrf(monitor_data.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    limits = get_user_limits(current_user)
    current_count = db.query(Monitor).filter(Monitor.user_id == current_user.id).count()

    if current_count >= limits["max_monitors"]:
        raise HTTPException(status_code=400, detail=f"Monitor limit reached ({limits['max_monitors']}). Upgrade to Pro for more.")

    monitor = Monitor(
        user_id=current_user.id,
        name=monitor_data.name,
        url=monitor_data.url,
        interval=limits["check_interval"],
        timeout=monitor_data.timeout,
        is_active=True
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    # Track monitor creation
    track_event(db, "monitor.created", user_id=current_user.id, event_data={
        "monitor_id": monitor.id,
        "url": monitor.url,
        "is_first": current_count == 0
    })

    return monitor


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.put("/{monitor_id}", response_model=MonitorResponse)
def update_monitor(monitor_id: int, monitor_data: MonitorUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if monitor_data.name is not None:
        monitor.name = monitor_data.name
    if monitor_data.url is not None:
        # SSRF Protection: Validate URL before updating
        is_valid, error_msg = validate_url_for_ssrf(monitor_data.url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        monitor.url = monitor_data.url
    if monitor_data.timeout is not None:
        monitor.timeout = monitor_data.timeout
    if monitor_data.is_active is not None:
        monitor.is_active = monitor_data.is_active
    
    db.commit()
    db.refresh(monitor)
    return monitor


@router.delete("/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    db.delete(monitor)
    db.commit()
    return {"message": "Monitor deleted"}


@router.get("/{monitor_id}/checks", response_model=List[CheckResponse])
def get_monitor_checks(monitor_id: int, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    checks = db.query(Check).filter(Check.monitor_id == monitor_id).order_by(Check.checked_at.desc()).limit(limit).all()
    return checks
