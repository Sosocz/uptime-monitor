from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.monitor import Monitor
from app.models.check import Check
from app.schemas.monitor import MonitorCreate, MonitorUpdate, MonitorResponse
from app.schemas.check import CheckResponse
from app.services.subscription_service import get_user_limits

router = APIRouter()


@router.get("", response_model=List[MonitorResponse])
@router.get("/", response_model=List[MonitorResponse], include_in_schema=False)
def get_monitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).all()
    return monitors


@router.post("", response_model=MonitorResponse)
@router.post("/", response_model=MonitorResponse, include_in_schema=False)
def create_monitor(monitor_data: MonitorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
