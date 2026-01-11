from fastapi import APIRouter, Depends, HTTPException, Query
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

    # Debug log
    print(f"[MONITOR CREATE] User {current_user.id} ({current_user.email}) - Plan: {current_user.plan} - Count: {current_count}/{limits['max_monitors']}")

    if current_count >= limits["max_monitors"]:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de moniteurs atteinte ({current_count}/{limits['max_monitors']}). Passez à Pro pour plus de moniteurs."
        )

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


def _period_bounds(period: str) -> tuple:
    now = datetime.utcnow()
    if period == "week":
        start = now - timedelta(days=7)
        bucket = timedelta(days=1)
    elif period == "month":
        start = now - timedelta(days=30)
        bucket = timedelta(days=1)
    else:
        start = now - timedelta(hours=24)
        bucket = timedelta(hours=1)
    return start, now, bucket


@router.get("/{monitor_id}/metrics")
def get_monitor_metrics(
    monitor_id: int,
    range_period: str = Query(default=None, alias="range", pattern="^(day|week|month)$"),
    period: str = Query(default=None, pattern="^(day|week|month)$"),
    region: str = Query(default="europe"),
    from_date: str = Query(default=None, alias="from"),
    to_date: str = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    def _parse(date_str, fallback: datetime) -> datetime:
        if not date_str:
            return fallback
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if from_date or to_date:
        start = _parse(from_date, datetime.utcnow() - timedelta(days=7))
        end = _parse(to_date, datetime.utcnow())
        if start > end:
            raise HTTPException(status_code=400, detail="From date must be before To date.")
        total_days = max((end - start).days, 1)
        bucket = timedelta(hours=1) if total_days <= 2 else timedelta(days=1)
        period_label = "custom"
    else:
        range_value = range_period or period or "day"
        start, end, bucket = _period_bounds(range_value)
        period_label = range_value

    checks = db.query(Check).filter(
        Check.monitor_id == monitor_id,
        Check.checked_at >= start,
        Check.checked_at <= end,
        Check.response_time.isnot(None)
    ).order_by(Check.checked_at.asc()).all()

    if not checks:
        return {
            "period": period_label,
            "region": region,
            "points": [],
            "message": "No data yet"
        }

    bucket_count = int((end - start) / bucket) + 1
    buckets = []
    for i in range(bucket_count):
        buckets.append(start + (bucket * i))

    sums_total = [0.0 for _ in buckets]
    sums_lookup = [0.0 for _ in buckets]
    sums_connection = [0.0 for _ in buckets]
    sums_tls = [0.0 for _ in buckets]
    sums_transfer = [0.0 for _ in buckets]
    counts = [0 for _ in buckets]

    for check in checks:
        idx = int((check.checked_at - start) / bucket)
        if idx < 0 or idx >= len(buckets):
            continue
        total = check.response_time or 0
        sums_total[idx] += total
        sums_transfer[idx] += total
        counts[idx] += 1

    data_points = []
    for idx, bucket_start in enumerate(buckets):
        if counts[idx] == 0:
            continue
        avg_total = sums_total[idx] / counts[idx]
        avg_transfer = sums_transfer[idx] / counts[idx]
        avg_lookup = sums_lookup[idx] / counts[idx]
        avg_connection = sums_connection[idx] / counts[idx]
        avg_tls = sums_tls[idx] / counts[idx]
        data_points.append({
            "ts": bucket_start.isoformat() + "Z",
            "name_lookup_ms": round(avg_lookup, 1),
            "connection_ms": round(avg_connection, 1),
            "tls_ms": round(avg_tls, 1),
            "transfer_ms": round(avg_transfer, 1),
            "total_ms": round(avg_total, 1)
        })

    return {
        "period": period_label,
        "region": region,
        "points": data_points
    }


def _availability_stats(checks: list[Check], interval_seconds: int) -> dict:
    total = len(checks)
    if total == 0:
        return {
            "availability_pct": None,
            "downtime_minutes": None,
            "incidents": 0,
            "longest_incident_minutes": None,
            "avg_incident_minutes": None,
        }

    up_checks = [c for c in checks if c.status == "up"]
    down_checks = [c for c in checks if c.status != "up"]
    availability = (len(up_checks) / total) * 100

    interval_minutes = max(interval_seconds / 60.0, 1.0)
    downtime_minutes = round(len(down_checks) * interval_minutes, 2)

    incidents = 0
    longest = 0.0
    current = 0.0
    for check in checks:
        if check.status == "up":
            if current > 0:
                incidents += 1
                longest = max(longest, current)
                current = 0.0
            continue
        current += interval_minutes
    if current > 0:
        incidents += 1
        longest = max(longest, current)

    avg_incident = round((downtime_minutes / incidents), 2) if incidents > 0 else None
    return {
        "availability_pct": round(availability, 2),
        "downtime_minutes": downtime_minutes,
        "incidents": incidents,
        "longest_incident_minutes": round(longest, 2) if incidents > 0 else None,
        "avg_incident_minutes": avg_incident,
    }


@router.get("/{monitor_id}/availability")
def get_monitor_availability(
    monitor_id: int,
    from_date: str = Query(default=None, alias="from"),
    to_date: str = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    interval_seconds = monitor.interval or 60
    now = datetime.utcnow()

    def _parse(date_str, fallback: datetime) -> datetime:
        if not date_str:
            return fallback
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if from_date or to_date:
        start = _parse(from_date, now - timedelta(days=7))
        end = _parse(to_date, now)
        if start > end:
            raise HTTPException(status_code=400, detail="From date must be before To date.")
        checks = db.query(Check).filter(
            Check.monitor_id == monitor_id,
            Check.checked_at >= start,
            Check.checked_at <= end,
        ).order_by(Check.checked_at.asc()).all()
        stats = _availability_stats(checks, interval_seconds)
        return {
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "stats": stats,
        }

    periods = [
        ("Today", now - timedelta(days=1), now),
        ("Last 7 days", now - timedelta(days=7), now),
        ("Last 30 days", now - timedelta(days=30), now),
        ("Last 365 days", now - timedelta(days=365), now),
    ]

    first_check = db.query(Check).filter(Check.monitor_id == monitor_id).order_by(Check.checked_at.asc()).first()
    if first_check:
        periods.append(("All time", first_check.checked_at, now))
    else:
        periods.append(("All time", now - timedelta(days=1), now))

    rows = []
    for label, start, end in periods:
        checks = db.query(Check).filter(
            Check.monitor_id == monitor_id,
            Check.checked_at >= start,
            Check.checked_at <= end,
        ).order_by(Check.checked_at.asc()).all()
        stats = _availability_stats(checks, interval_seconds)
        rows.append({
            "label": label,
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            **stats,
        })

    return {"rows": rows}
