from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MonitorCreate(BaseModel):
    name: str
    url: str
    interval: int = 600
    timeout: int = 30


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None


class MonitorResponse(BaseModel):
    id: int
    name: str
    url: str
    interval: int
    timeout: int
    is_active: bool
    last_status: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
