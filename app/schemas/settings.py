from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class AccountSettingsUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    timezone: Optional[str] = Field(default=None, max_length=64)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class AlertsSettingsUpdate(BaseModel):
    alerts_enabled: Optional[bool] = None
    alerts_paused_from: Optional[datetime] = None
    alerts_paused_until: Optional[datetime] = None


class SettingsResponse(BaseModel):
    email: EmailStr
    plan: str
    oauth_provider: Optional[str] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    gravatar_url: Optional[str] = None

    alerts_enabled: bool
    alerts_paused_from: Optional[datetime] = None
    alerts_paused_until: Optional[datetime] = None
    alerts_paused: bool

    class Config:
        from_attributes = True
