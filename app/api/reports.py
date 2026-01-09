"""
Reports API Routes

Generate CEO/Client-ready monthly reports.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.monitor import Monitor
from app.services.report_service import generate_monthly_report, generate_html_report, generate_client_ready_summary

router = APIRouter()


@router.get("/monitors/{monitor_id}/report")
def get_monitor_report(
    monitor_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monthly report data (JSON) for a monitor."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Generate report
    report_data = generate_monthly_report(db, monitor, month, year)

    return report_data


@router.get("/monitors/{monitor_id}/report/html", response_class=HTMLResponse)
def get_monitor_report_html(
    monitor_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monthly report as HTML (ready to send to client or convert to PDF)."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Generate report data
    report_data = generate_monthly_report(db, monitor, month, year)

    # Convert to HTML
    html = generate_html_report(report_data)

    return HTMLResponse(content=html)


@router.get("/monitors/{monitor_id}/report/summary")
def get_monitor_report_summary(
    monitor_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get short client-ready summary text."""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Generate report data
    report_data = generate_monthly_report(db, monitor, month, year)

    # Generate summary
    summary = generate_client_ready_summary(report_data)

    return {
        "monitor_id": monitor_id,
        "summary": summary
    }
