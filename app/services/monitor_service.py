import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.monitor import Monitor
from app.models.check import Check


async def perform_check(db: Session, monitor: Monitor) -> Check:
    """Perform an HTTP check on a monitor and record the result."""
    start_time = datetime.utcnow()
    
    try:
        async with httpx.AsyncClient(timeout=monitor.timeout) as client:
            response = await client.get(monitor.url)
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            check = Check(
                monitor_id=monitor.id,
                status="up" if response.status_code < 400 else "down",
                status_code=response.status_code,
                response_time=response_time,
                checked_at=datetime.utcnow()
            )
    except httpx.TimeoutException:
        check = Check(
            monitor_id=monitor.id,
            status="down",
            error_message="Request timeout",
            checked_at=datetime.utcnow()
        )
    except Exception as e:
        check = Check(
            monitor_id=monitor.id,
            status="down",
            error_message=str(e)[:500],
            checked_at=datetime.utcnow()
        )
    
    db.add(check)
    db.commit()
    db.refresh(check)
    
    # Update monitor's last status
    monitor.last_status = check.status
    monitor.last_checked_at = check.checked_at
    db.commit()
    
    return check
