import asyncio
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.monitor import Monitor
from app.services.monitor_service import perform_check
from app.services.incident_service import detect_and_create_incident
from app.services.notification_service import notify_incident

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session."""
    return SessionLocal()


async def check_monitors():
    """Check all active monitors and handle incidents."""
    db = get_db()
    
    try:
        monitors = db.query(Monitor).filter(Monitor.is_active == True).all()
        logger.info(f"Checking {len(monitors)} monitors...")
        
        for monitor in monitors:
            current_time = time.time()
            
            # Check if enough time has passed since last check
            if monitor.last_checked_at:
                elapsed = current_time - monitor.last_checked_at.timestamp()
                if elapsed < monitor.interval:
                    continue
            
            logger.info(f"Checking monitor: {monitor.name} ({monitor.url})")
            
            # Perform the HTTP check
            check = await perform_check(db, monitor)
            logger.info(f"  Status: {check.status}, Response time: {check.response_time}ms")
            
            # Detect incidents (status transitions)
            incident = detect_and_create_incident(db, monitor, check)
            
            # Send notifications if incident detected
            if incident:
                logger.info(f"  Incident detected: {incident.incident_type}")
                try:
                    await notify_incident(monitor.owner, monitor, incident)
                    logger.info(f"  Notification sent")
                except Exception as e:
                    logger.error(f"  Notification error: {e}")
    
    except Exception as e:
        logger.error(f"Worker error: {e}")
    
    finally:
        db.close()


def run_check_job():
    """Wrapper to run async check in sync scheduler."""
    asyncio.run(check_monitors())


def run_worker():
    """Start the worker scheduler."""
    logger.info("Starting Uptime Monitor Worker...")
    
    scheduler = BlockingScheduler()
    
    # Run checks every 30 seconds
    scheduler.add_job(
        run_check_job,
        'interval',
        seconds=30,
        id='check_monitors',
        max_instances=1
    )
    
    try:
        logger.info("Worker started. Checking monitors every 30 seconds.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped.")


if __name__ == '__main__':
    run_worker()
