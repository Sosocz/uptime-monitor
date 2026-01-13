from datetime import datetime
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.settings import AccountSettingsUpdate, AlertsSettingsUpdate, SettingsResponse

router = APIRouter()


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    return value


def _gravatar_url(email: str) -> str:
    if not email:
        return ""
    digest = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?d=404&s=160"


def _alerts_paused(user: User) -> bool:
    if not user.alerts_enabled:
        return True
    if user.alerts_paused_from and user.alerts_paused_until:
        now = datetime.utcnow()
        return user.alerts_paused_from <= now <= user.alerts_paused_until
    return False


@router.get("/settings/me", response_model=SettingsResponse)
def get_settings(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "plan": current_user.plan,
        "oauth_provider": current_user.oauth_provider,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "timezone": current_user.timezone or "UTC",
        "avatar_url": current_user.avatar_url,
        "gravatar_url": _gravatar_url(current_user.email),
        "alerts_enabled": bool(current_user.alerts_enabled),
        "alerts_paused_from": current_user.alerts_paused_from,
        "alerts_paused_until": current_user.alerts_paused_until,
        "alerts_paused": _alerts_paused(current_user),
    }


@router.put("/settings/account", response_model=SettingsResponse)
def update_account_settings(
    data: AccountSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.first_name is not None:
        current_user.first_name = _normalize_value(data.first_name)
    if data.last_name is not None:
        current_user.last_name = _normalize_value(data.last_name)
    if data.phone is not None:
        current_user.phone = _normalize_value(data.phone)
    if data.timezone is not None:
        current_user.timezone = _normalize_value(data.timezone) or "UTC"
    if data.avatar_url is not None:
        current_user.avatar_url = _normalize_value(data.avatar_url)

    try:
        db.commit()
        db.refresh(current_user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database schema out of date. Run alembic upgrade head.")
    return get_settings(current_user)


@router.put("/settings/alerts", response_model=SettingsResponse)
def update_alerts_settings(
    data: AlertsSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.alerts_enabled is not None:
        current_user.alerts_enabled = data.alerts_enabled

    if data.alerts_paused_from is not None or data.alerts_paused_until is not None:
        if data.alerts_paused_from and data.alerts_paused_until:
            if data.alerts_paused_from > data.alerts_paused_until:
                raise HTTPException(status_code=400, detail="La date de début doit être avant la date de fin.")
        current_user.alerts_paused_from = data.alerts_paused_from
        current_user.alerts_paused_until = data.alerts_paused_until

    try:
        db.commit()
        db.refresh(current_user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database schema out of date. Run alembic upgrade head.")
    return get_settings(current_user)
