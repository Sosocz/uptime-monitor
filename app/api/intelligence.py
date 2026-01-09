"""
Intelligence API Routes

Provides access to:
- Health score and grade
- Site DNA (patterns)
- Smart views (critical, unstable, stable monitors)
- Intelligent incident analysis
- Value stats (incidents detected, time saved)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Dict
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.monitor import Monitor
from app.models.incident import Incident
from app.models.check import Check
from app.services.intelligent_incident_service import (
    calculate_health_score,
    detect_patterns,
    calculate_time_and_money_lost
)

router = APIRouter()


@router.get("/monitors/{monitor_id}/health")
def get_monitor_health(
    monitor_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health score and grade for a monitor."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    health_data = calculate_health_score(db, monitor, days)

    return {
        "monitor_id": monitor_id,
        "monitor_name": monitor.name,
        "health_score": health_data['score'],
        "health_grade": health_data['grade'],
        "uptime_pct": health_data['uptime_pct'],
        "incidents_count": health_data['incidents_count'],
        "avg_response_time": health_data['avg_response_time'],
        "days_analyzed": health_data['days_analyzed'],
        "is_flapping": monitor.is_flapping,
        "is_degrading": monitor.is_degrading
    }


@router.get("/monitors/{monitor_id}/dna")
def get_monitor_dna(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Site DNA - patterns and trends for a monitor."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    patterns = detect_patterns(db, monitor)

    return {
        "monitor_id": monitor_id,
        "monitor_name": monitor.name,
        "url": monitor.url,
        "site_dna": {
            "high_risk_hours": patterns['high_risk_hours'],
            "high_risk_days": patterns['high_risk_days'],
            "total_incidents": patterns['total_incidents'],
            "stability_trend": patterns['stability_trend']
        },
        "health_score": monitor.health_score,
        "health_grade": monitor.health_grade
    }


@router.get("/monitors/views/critical")
def get_critical_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monitors with critical status (health score < 70 or currently down)."""
    monitors = db.query(Monitor).filter(
        Monitor.user_id == current_user.id,
        Monitor.is_active == True
    ).all()

    critical = []
    for monitor in monitors:
        if monitor.last_status == "down" or (monitor.health_score and monitor.health_score < 70):
            critical.append({
                "id": monitor.id,
                "name": monitor.name,
                "url": monitor.url,
                "status": monitor.last_status,
                "health_score": monitor.health_score,
                "health_grade": monitor.health_grade,
                "is_flapping": monitor.is_flapping,
                "is_degrading": monitor.is_degrading,
                "tags": monitor.tags.split(",") if monitor.tags else []
            })

    return {
        "view": "critical",
        "count": len(critical),
        "monitors": critical
    }


@router.get("/monitors/views/unstable")
def get_unstable_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monitors that are unstable (flapping or degrading)."""
    monitors = db.query(Monitor).filter(
        Monitor.user_id == current_user.id,
        Monitor.is_active == True
    ).filter(
        (Monitor.is_flapping == True) | (Monitor.is_degrading == True)
    ).all()

    unstable = []
    for monitor in monitors:
        unstable.append({
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "status": monitor.last_status,
            "health_score": monitor.health_score,
            "health_grade": monitor.health_grade,
            "is_flapping": monitor.is_flapping,
            "is_degrading": monitor.is_degrading,
            "tags": monitor.tags.split(",") if monitor.tags else []
        })

    return {
        "view": "unstable",
        "count": len(unstable),
        "monitors": unstable
    }


@router.get("/monitors/views/stable")
def get_stable_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monitors with no incidents in last 30 days (healthy)."""
    since = datetime.utcnow() - timedelta(days=30)

    # Get all monitors
    all_monitors = db.query(Monitor).filter(
        Monitor.user_id == current_user.id,
        Monitor.is_active == True
    ).all()

    stable = []
    for monitor in all_monitors:
        # Check if monitor has incidents in last 30 days
        recent_incidents = db.query(Incident).filter(
            Incident.monitor_id == monitor.id,
            Incident.started_at >= since
        ).count()

        if recent_incidents == 0 and monitor.last_status == "up":
            stable.append({
                "id": monitor.id,
                "name": monitor.name,
                "url": monitor.url,
                "status": monitor.last_status,
                "health_score": monitor.health_score,
                "health_grade": monitor.health_grade,
                "tags": monitor.tags.split(",") if monitor.tags else []
            })

    return {
        "view": "stable",
        "count": len(stable),
        "monitors": stable
    }


@router.get("/monitors/by-tag/{tag}")
def get_monitors_by_tag(
    tag: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all monitors with a specific tag."""
    monitors = db.query(Monitor).filter(
        Monitor.user_id == current_user.id,
        Monitor.is_active == True,
        Monitor.tags.like(f"%{tag}%")
    ).all()

    result = []
    for monitor in monitors:
        result.append({
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "status": monitor.last_status,
            "health_score": monitor.health_score,
            "health_grade": monitor.health_grade,
            "tags": monitor.tags.split(",") if monitor.tags else []
        })

    return {
        "tag": tag,
        "count": len(result),
        "monitors": result
    }


@router.patch("/monitors/{monitor_id}/tags")
def update_monitor_tags(
    monitor_id: int,
    tags: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update tags for a monitor."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Clean and join tags
    clean_tags = [tag.strip().lower() for tag in tags if tag.strip()]
    monitor.tags = ",".join(clean_tags)

    db.commit()

    return {
        "monitor_id": monitor_id,
        "tags": clean_tags
    }


@router.patch("/monitors/{monitor_id}/revenue")
def update_monitor_revenue(
    monitor_id: int,
    estimated_revenue_per_hour: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update estimated revenue per hour for money lost calculation."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    monitor.estimated_revenue_per_hour = estimated_revenue_per_hour
    db.commit()

    return {
        "monitor_id": monitor_id,
        "estimated_revenue_per_hour": estimated_revenue_per_hour
    }


@router.get("/stats/value")
def get_value_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get value stats to show user the value they're getting.

    Shows:
    - Total incidents detected
    - Total time monitored
    - Average response time
    - Money saved (estimated)
    """
    # Get all user's monitors
    monitor_ids = [m.id for m in db.query(Monitor).filter(
        Monitor.user_id == current_user.id
    ).all()]

    if not monitor_ids:
        return {
            "incidents_detected": 0,
            "total_checks": 0,
            "avg_response_time": 0,
            "total_minutes_lost": 0,
            "total_money_lost": 0
        }

    # Total incidents detected
    incidents_count = db.query(func.count(Incident.id)).filter(
        Incident.monitor_id.in_(monitor_ids)
    ).scalar() or 0

    # Total checks performed
    total_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id.in_(monitor_ids)
    ).scalar() or 0

    # Average response time
    avg_response = db.query(func.avg(Check.response_time)).filter(
        Check.monitor_id.in_(monitor_ids),
        Check.response_time.isnot(None)
    ).scalar() or 0

    # Total minutes and money lost
    incidents = db.query(Incident).filter(
        Incident.monitor_id.in_(monitor_ids)
    ).all()

    total_minutes_lost = sum(i.minutes_lost for i in incidents if i.minutes_lost)
    total_money_lost = sum(i.money_lost for i in incidents if i.money_lost)

    return {
        "incidents_detected": incidents_count,
        "total_checks": total_checks,
        "avg_response_time": int(avg_response),
        "total_minutes_lost": total_minutes_lost,
        "total_money_lost": total_money_lost,
        "monitors_count": len(monitor_ids)
    }


@router.get("/incidents/{incident_id}/analysis")
def get_incident_analysis(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed intelligent analysis for an incident."""
    incident = db.query(Incident).join(Monitor).filter(
        Incident.id == incident_id,
        Monitor.user_id == current_user.id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": incident_id,
        "monitor_id": incident.monitor_id,
        "incident_type": incident.incident_type,
        "started_at": incident.started_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "duration_seconds": incident.duration_seconds,
        "basic_cause": incident.cause,
        "intelligent_cause": incident.intelligent_cause,
        "severity": incident.severity,
        "analysis_data": incident.analysis_data,
        "recommendations": incident.recommendations,
        "minutes_lost": incident.minutes_lost,
        "money_lost": incident.money_lost
    }
