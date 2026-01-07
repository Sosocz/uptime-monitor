from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class IncidentResponse(BaseModel):
    id: int
    monitor_id: int
    incident_type: str
    started_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
