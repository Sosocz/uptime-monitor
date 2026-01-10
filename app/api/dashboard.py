from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset-password.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/monitors/{monitor_id}", response_class=HTMLResponse)
def monitor_detail_page(request: Request, monitor_id: int):
    return templates.TemplateResponse("monitor_detail.html", {"request": request, "monitor_id": monitor_id})


@router.get("/incidents", response_class=HTMLResponse)
def incidents_page(request: Request):
    return templates.TemplateResponse("incidents.html", {"request": request})


@router.get("/upgrade", response_class=HTMLResponse)
def upgrade_page(request: Request):
    return templates.TemplateResponse("upgrade.html", {"request": request})


@router.get("/why-trezapp", response_class=HTMLResponse)
def why_trezapp_page(request: Request):
    return templates.TemplateResponse("why_trezapp.html", {"request": request})


@router.get("/incident-analytics", response_class=HTMLResponse)
def incident_analytics_page(request: Request):
    """Incident Analytics page - MTTA/MTTR metrics and incident management."""
    return templates.TemplateResponse("incident_analytics.html", {"request": request})


@router.get("/oncall", response_class=HTMLResponse)
def oncall_page(request: Request):
    """On-Call Management page - See who's currently on-call."""
    return templates.TemplateResponse("oncall.html", {"request": request})


@router.get("/status-page-subscribers", response_class=HTMLResponse)
def status_page_subscribers_page(request: Request):
    """Status Page Subscribers Management - View and manage email subscribers."""
    return templates.TemplateResponse("status_page_subscribers.html", {"request": request})
