from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CheckResponse(BaseModel):
    id: int
    monitor_id: int
    status: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime
    
    class Config:
        from_attributes = True
