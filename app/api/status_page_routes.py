"""
Status page API routes - public endpoints for status pages.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.status_page import StatusPage, StatusPageMonitor
from app.models.monitor import Monitor
from app.models.user import User
from app.services.status_page_service import (
    calculate_uptime_percentage,
    get_average_response_time,
    get_recent_incidents,
    get_daily_uptime
)
from app.services.tracking_service import track_event
from app.core.deps import get_current_user
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter()

# Setup Jinja2 templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


# ===== Schemas =====

class StatusPageCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    is_public: bool = True
    header_text: Optional[str] = None
    brand_color: Optional[str] = "#3b82f6"
    monitor_ids: List[int] = []


class StatusPageUpdate(BaseModel):
    name: Optional[str] = None
    is_public: Optional[bool] = None
    header_text: Optional[str] = None
    brand_color: Optional[str] = None
    logo_url: Optional[str] = None
    show_powered_by: Optional[bool] = None


class AddMonitorToPage(BaseModel):
    monitor_id: int


# ===== Private API (authenticated) =====

@router.post("/status-pages", tags=["status-pages"])
async def create_status_page(
    data: StatusPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new status page."""
    # Check if slug is already taken
    if data.slug:
        existing = db.query(StatusPage).filter(StatusPage.slug == data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already taken")

    # Create status page
    status_page = StatusPage(
        user_id=current_user.id,
        name=data.name,
        slug=data.slug,
        is_public=data.is_public,
        header_text=data.header_text,
        brand_color=data.brand_color
    )
    db.add(status_page)
    db.commit()
    db.refresh(status_page)

    # Add monitors
    for monitor_id in data.monitor_ids:
        # Verify monitor belongs to user
        monitor = db.query(Monitor).filter(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id
        ).first()

        if monitor:
            page_monitor = StatusPageMonitor(
                status_page_id=status_page.id,
                monitor_id=monitor_id
            )
            db.add(page_monitor)

    db.commit()

    # Track status page creation
    track_event(db, "statuspage.created", user_id=current_user.id, event_data={
        "statuspage_id": status_page.id,
        "slug": status_page.slug,
        "monitor_count": len(data.monitor_ids)
    })

    return {
        "id": status_page.id,
        "slug": status_page.slug,
        "name": status_page.name,
        "public_url": f"/status/{status_page.slug}",
        "access_token": status_page.access_token if not status_page.is_public else None
    }


@router.get("/status-pages", tags=["status-pages"])
async def list_status_pages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all status pages for the current user."""
    pages = db.query(StatusPage).filter(StatusPage.user_id == current_user.id).all()

    return [
        {
            "id": page.id,
            "slug": page.slug,
            "name": page.name,
            "is_public": page.is_public,
            "monitor_count": len(page.monitors),
            "public_url": f"/status/{page.slug}"
        }
        for page in pages
    ]


@router.put("/status-pages/{page_id}", tags=["status-pages"])
async def update_status_page(
    page_id: int,
    data: StatusPageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a status page."""
    page = db.query(StatusPage).filter(
        StatusPage.id == page_id,
        StatusPage.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")

    if data.name is not None:
        page.name = data.name
    if data.is_public is not None:
        page.is_public = data.is_public
    if data.header_text is not None:
        page.header_text = data.header_text
    if data.brand_color is not None:
        page.brand_color = data.brand_color
    if data.logo_url is not None:
        page.logo_url = data.logo_url
    if data.show_powered_by is not None:
        # Only PAID users can disable the badge
        if current_user.plan != "PAID" and not data.show_powered_by:
            raise HTTPException(status_code=403, detail="Upgrade to PAID plan to remove 'Powered by TrezApp' badge")
        page.show_powered_by = data.show_powered_by

    db.commit()

    return {"success": True}


@router.delete("/status-pages/{page_id}", tags=["status-pages"])
async def delete_status_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a status page."""
    page = db.query(StatusPage).filter(
        StatusPage.id == page_id,
        StatusPage.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")

    db.delete(page)
    db.commit()

    return {"success": True}


@router.post("/status-pages/{page_id}/monitors", tags=["status-pages"])
async def add_monitor_to_page(
    page_id: int,
    data: AddMonitorToPage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a monitor to a status page."""
    page = db.query(StatusPage).filter(
        StatusPage.id == page_id,
        StatusPage.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")

    # Verify monitor belongs to user
    monitor = db.query(Monitor).filter(
        Monitor.id == data.monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Check if already added
    existing = db.query(StatusPageMonitor).filter(
        StatusPageMonitor.status_page_id == page_id,
        StatusPageMonitor.monitor_id == data.monitor_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Monitor already on this page")

    # Add monitor
    page_monitor = StatusPageMonitor(
        status_page_id=page_id,
        monitor_id=data.monitor_id
    )
    db.add(page_monitor)
    db.commit()

    return {"success": True}


# ===== Badge API (public, embeddable) =====

# Simple in-memory rate limiter for badges
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

badge_rate_limiter = defaultdict(list)
BADGE_RATE_LIMIT = 100  # Max 100 requests per IP per minute

def check_badge_rate_limit(request: Request) -> bool:
    """Simple rate limiter for badge endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()

    # Clean old entries
    badge_rate_limiter[client_ip] = [
        timestamp for timestamp in badge_rate_limiter[client_ip]
        if now - timestamp < timedelta(minutes=1)
    ]

    # Check limit
    if len(badge_rate_limiter[client_ip]) >= BADGE_RATE_LIMIT:
        return False

    badge_rate_limiter[client_ip].append(now)
    return True


def is_monitor_public(db: Session, monitor_id: int) -> bool:
    """Check if monitor is publicly accessible via status page."""
    from app.models.status_page import StatusPageMonitor, StatusPage

    # Check if monitor is on any public status page
    public_monitor = db.query(StatusPageMonitor).join(StatusPage).filter(
        StatusPageMonitor.monitor_id == monitor_id,
        StatusPage.is_public == True
    ).first()

    return public_monitor is not None


@router.get("/badge/{monitor_id}/uptime.svg", tags=["badge"])
async def get_uptime_badge(
    request: Request,
    monitor_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Generate an embeddable uptime badge (SVG) for a monitor.

    Security:
    - Only monitors on public status pages can have badges
    - Rate limited to 100 req/min per IP

    Usage:
    - Image tag: <img src="https://yourdomain.com/api/badge/123/uptime.svg?days=30" alt="Uptime">
    - Markdown: ![Uptime](https://yourdomain.com/api/badge/123/uptime.svg?days=30)

    Query params:
    - days: Number of days to calculate uptime (default: 7, max: 90)
    """
    # Rate limiting
    if not check_badge_rate_limit(request):
        svg = generate_badge_svg("error", "rate limited", "#ef4444")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()

    if not monitor:
        svg = generate_badge_svg("uptime", "not found", "#6b7280")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    # Check if monitor is public
    if not is_monitor_public(db, monitor_id):
        svg = generate_badge_svg("uptime", "private", "#6b7280")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    # Calculate uptime
    uptime = calculate_uptime_percentage(db, monitor_id, days=days)

    # Choose color based on uptime
    if uptime >= 99:
        color = "#10b981"  # green
    elif uptime >= 95:
        color = "#f59e0b"  # orange
    else:
        color = "#ef4444"  # red

    uptime_text = f"{uptime:.2f}%"
    label = f"{days}d uptime"

    svg = generate_badge_svg(label, uptime_text, color)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
            "Content-Type": "image/svg+xml; charset=utf-8"
        }
    )


def generate_badge_svg(label: str, value: str, color: str) -> str:
    """Generate SVG badge with label and value."""
    # Calculate text widths (approximate)
    label_width = len(label) * 6 + 10
    value_width = len(value) * 7 + 10
    total_width = label_width + value_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {value}">
    <title>{label}: {value}</title>
    <linearGradient id="s" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="r">
        <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#r)">
        <rect width="{label_width}" height="20" fill="#555"/>
        <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
        <rect width="{total_width}" height="20" fill="url(#s)"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
        <text aria-hidden="true" x="{label_width // 2 * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(label_width - 10) * 10}">{label}</text>
        <text x="{label_width // 2 * 10}" y="140" transform="scale(.1)" fill="#fff" textLength="{(label_width - 10) * 10}">{label}</text>
        <text aria-hidden="true" x="{(label_width + value_width // 2) * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(value_width - 10) * 10}">{value}</text>
        <text x="{(label_width + value_width // 2) * 10}" y="140" transform="scale(.1)" fill="#fff" textLength="{(value_width - 10) * 10}">{value}</text>
    </g>
</svg>'''

    return svg


@router.get("/badge/{monitor_id}/status.svg", tags=["badge"])
async def get_status_badge(
    request: Request,
    monitor_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate an embeddable status badge (SVG) for a monitor.

    Security:
    - Only monitors on public status pages can have badges
    - Rate limited to 100 req/min per IP

    Usage:
    - Image tag: <img src="https://yourdomain.com/api/badge/123/status.svg" alt="Status">
    - Markdown: ![Status](https://yourdomain.com/api/badge/123/status.svg)
    """
    # Rate limiting
    if not check_badge_rate_limit(request):
        svg = generate_badge_svg("error", "rate limited", "#ef4444")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()

    if not monitor:
        svg = generate_badge_svg("status", "not found", "#6b7280")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    # Check if monitor is public
    if not is_monitor_public(db, monitor_id):
        svg = generate_badge_svg("status", "private", "#6b7280")
        return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    status = monitor.last_status or "unknown"

    # Choose color and text based on status
    if status == "up":
        color = "#10b981"
        status_text = "operational"
    elif status == "down":
        color = "#ef4444"
        status_text = "down"
    else:
        color = "#6b7280"
        status_text = "unknown"

    svg = generate_badge_svg("status", status_text, color)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=60",  # Cache for 1 minute
            "Content-Type": "image/svg+xml; charset=utf-8"
        }
    )


# ===== Public API (no authentication) =====

@router.get("/status/{slug}", response_class=HTMLResponse, tags=["public"])
async def get_public_status_page(
    request: Request,
    slug: str,
    token: Optional[str] = Query(None),
    format: Optional[str] = Query("html", regex="^(html|json)$"),
    db: Session = Depends(get_db)
):
    """Get public status page (HTML or JSON)."""
    page = db.query(StatusPage).filter(StatusPage.slug == slug).first()

    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")

    # Check access control
    if not page.is_public:
        if not token or token != page.access_token:
            raise HTTPException(status_code=403, detail="Access denied")

    # Build monitor statuses
    monitors_data = []

    for page_monitor in page.monitors:
        monitor = page_monitor.monitor

        # Get current status
        current_status = monitor.last_status or "unknown"

        # Calculate uptime percentages
        uptime_7d = calculate_uptime_percentage(db, monitor.id, days=7) if page.show_uptime_percentage else None
        uptime_30d = calculate_uptime_percentage(db, monitor.id, days=30) if page.show_uptime_percentage else None
        uptime_90d = calculate_uptime_percentage(db, monitor.id, days=90) if page.show_uptime_percentage else None

        # Get average response time
        avg_response_time = get_average_response_time(db, monitor.id, days=7) if page.show_response_time else None

        # Get recent incidents
        incidents = get_recent_incidents(db, monitor.id, limit=5) if page.show_incident_history else []

        # Get daily uptime chart data
        daily_uptime = get_daily_uptime(db, monitor.id, days=90)

        monitors_data.append({
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "status": current_status,
            "last_checked_at": monitor.last_checked_at.isoformat() if monitor.last_checked_at else None,
            "uptime_7d": uptime_7d,
            "uptime_30d": uptime_30d,
            "uptime_90d": uptime_90d,
            "avg_response_time": avg_response_time,
            "recent_incidents": incidents,
            "daily_uptime": daily_uptime
        })

    # Determine overall status
    overall_status = "up"
    for monitor in monitors_data:
        if monitor["status"] == "down":
            overall_status = "down"
            break
        elif monitor["status"] == "unknown":
            overall_status = "unknown"

    # Return JSON if requested
    if format == "json":
        return {
            "name": page.name,
            "header_text": page.header_text,
            "brand_color": page.brand_color,
            "logo_url": page.logo_url,
            "monitors": monitors_data
        }

    # Get user to check plan (for powered by badge)
    user = db.query(User).filter(User.id == page.user_id).first()
    show_powered_by = page.show_powered_by
    # Force show badge for FREE users
    if user and user.plan == "FREE":
        show_powered_by = True

    # Render HTML template
    return templates.TemplateResponse("status_page.html", {
        "request": request,
        "name": page.name,
        "header_text": page.header_text,
        "brand_color": page.brand_color,
        "logo_url": page.logo_url,
        "overall_status": overall_status,
        "monitors": monitors_data,
        "show_powered_by": show_powered_by
    })
