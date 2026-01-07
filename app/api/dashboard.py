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


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/monitors/{monitor_id}", response_class=HTMLResponse)
def monitor_detail_page(request: Request, monitor_id: int):
    return templates.TemplateResponse("monitor_detail.html", {"request": request, "monitor_id": monitor_id})


@router.get("/incidents", response_class=HTMLResponse)
def incidents_page(request: Request):
    return templates.TemplateResponse("incidents.html", {"request": request})
