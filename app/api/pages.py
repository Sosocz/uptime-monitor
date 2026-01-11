"""
Additional page routes for feature-complete UI
Serves templates for Intelligence, Status Pages Management, and Reports
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/intelligence", response_class=HTMLResponse)
async def intelligence_dashboard(request: Request):
    """Intelligence Dashboard - AI insights, health scores, pattern detection"""
    return templates.TemplateResponse("intelligence.html", {"request": request})


@router.get("/intelligence/health", response_class=HTMLResponse)
async def health_scores_page(request: Request):
    """Health Scores page - Monitor grades and health metrics"""
    return templates.TemplateResponse("intelligence_health.html", {"request": request})


@router.get("/intelligence/dna", response_class=HTMLResponse)
async def site_dna_page(request: Request):
    """Site DNA page - Pattern detection and behavior analysis"""
    return templates.TemplateResponse("intelligence_dna.html", {"request": request})


@router.get("/intelligence/views", response_class=HTMLResponse)
async def smart_views_page(request: Request):
    """Smart Views page - Critical/Unstable/Stable monitor groupings"""
    return templates.TemplateResponse("intelligence_views.html", {"request": request})


@router.get("/status-pages", response_class=HTMLResponse)
async def status_pages_management(request: Request):
    """Status Pages Management - Create and manage public status pages"""
    return templates.TemplateResponse("status_pages.html", {"request": request})


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page - Generate monthly PDF reports"""
    return templates.TemplateResponse("reports.html", {"request": request})


@router.get("/escalation-policies", response_class=HTMLResponse)
async def escalation_policies_page(request: Request):
    """Escalation Policies page - Manage incident escalation rules"""
    return templates.TemplateResponse("escalation_policies.html", {"request": request})


@router.get("/heartbeats", response_class=HTMLResponse)
async def heartbeats_page(request: Request):
    """Heartbeats page - Monitor cron jobs and scheduled tasks"""
    return templates.TemplateResponse("heartbeats.html", {"request": request})


@router.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request):
    """Integrations page - Connect with Slack, PagerDuty, webhooks, etc."""
    return templates.TemplateResponse("integrations.html", {"request": request})


@router.get("/uptime-reports", response_class=HTMLResponse)
async def uptime_reports_page(request: Request):
    """Uptime Reports page - Historical uptime reports and SLA tracking"""
    return templates.TemplateResponse("uptime_reports.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page - Account, alerts, billing, and organization"""
    return templates.TemplateResponse("settings.html", {"request": request})


@router.get("/onboarding-guide", response_class=HTMLResponse)
async def onboarding_guide(request: Request):
    """Onboarding Guide page - Introduction to uptime monitoring"""
    return templates.TemplateResponse("onboarding_guide.html", {"request": request})
