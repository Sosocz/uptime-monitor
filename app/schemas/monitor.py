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

    # Intelligence fields
    health_score: Optional[int] = 100
    health_grade: Optional[str] = "A+"
    is_flapping: bool = False
    is_degrading: bool = False
    tags: Optional[str] = None
    estimated_revenue_per_hour: Optional[float] = 0

    class Config:
        from_attributes = True
