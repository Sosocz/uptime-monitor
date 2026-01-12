"""
Monitor check worker - schedules and executes monitor health checks.

This worker runs on a schedule (every 30 seconds by default) and:
1. Performs HTTP checks on all active monitors
2. Detects status transitions (UP→DOWN, DOWN→UP)
3. Enqueues notification tasks to ARQ for delivery
"""
import asyncio
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.monitor import Monitor
from app.models.incident import Incident
from app.models.check import Check
from app.services.monitor_service import perform_check
from app.services.incident_service import detect_and_create_incident
from app.services.escalation_service import check_escalation, reset_escalation_flags
from app.services.intelligent_incident_service import (
    analyze_why_it_went_down,
    detect_flapping,
    detect_progressive_degradation,
    calculate_health_score,
    detect_patterns,
    calculate_time_and_money_lost
)
from app.tasks import enqueue_notification

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

            try:
                # Perform the HTTP check
                check = await perform_check(db, monitor)
                ttfb_ms = None
                if check.total_ms is not None and check.transfer_ms is not None and check.total_ms >= check.transfer_ms:
                    ttfb_ms = check.total_ms - check.transfer_ms
                logger.info(
                    "  Status: %s, total_ms=%s, dns_ms=%s, conn_ms=%s, tls_ms=%s, ttfb_ms=%s, transfer_ms=%s (monitor_id=%s url=%s)",
                    check.status,
                    check.total_ms,
                    check.name_lookup_ms,
                    check.connection_ms,
                    check.tls_ms,
                    ttfb_ms,
                    check.transfer_ms,
                    monitor.id,
                    monitor.url,
                )

                # === INTELLIGENT ANALYSIS ===

                # 1. Detect flapping
                flapping_info = detect_flapping(db, monitor)
                if flapping_info:
                    monitor.is_flapping = True
                    logger.warning(f"  ⚠️  FLAPPING: {flapping_info['message']}")
                else:
                    monitor.is_flapping = False

                # 2. Detect progressive degradation (slowdown before crash)
                degradation_info = detect_progressive_degradation(db, monitor, check)
                if degradation_info:
                    monitor.is_degrading = True
                    logger.warning(f"  ⚠️  DEGRADING: {degradation_info['message']}")
                else:
                    monitor.is_degrading = False

                # 3. Update health score (every check)
                health_data = calculate_health_score(db, monitor, days=30)
                monitor.health_score = health_data['score']
                monitor.health_grade = health_data['grade']
                logger.info(f"  Health: {health_data['score']}/100 ({health_data['grade']})")

                # 4. Update site DNA patterns (less frequently - every 10 checks)
                if monitor.last_checked_at:
                    checks_count = db.query(func.count(Check.id)).filter(
                        Check.monitor_id == monitor.id
                    ).scalar()
                    if checks_count % 10 == 0:
                        patterns = detect_patterns(db, monitor)
                        monitor.site_dna = patterns
                        logger.info(f"  Site DNA updated: {patterns['stability_trend']}")

                db.commit()

                # === INCIDENT DETECTION ===
                incident = detect_and_create_incident(db, monitor, check)

                # Enqueue notifications if incident detected (UP→DOWN or DOWN→UP transition)
                if incident:
                    logger.info(f"  🚨 Incident detected: {incident.incident_type}")

                    # Perform intelligent analysis if incident is DOWN
                    if incident.incident_type == "down":
                        analysis = analyze_why_it_went_down(db, monitor, check)
                        incident.intelligent_cause = analysis['cause']
                        incident.severity = analysis['severity']
                        incident.analysis_data = analysis.get('details', {})
                        incident.recommendations = analysis.get('recommendations', [])

                        logger.info(f"  💡 Analysis: {analysis['cause']}")
                        logger.info(f"  🎯 Severity: {analysis['severity']}")

                    # Calculate time and money lost
                    loss = calculate_time_and_money_lost(
                        incident,
                        monitor.estimated_revenue_per_hour
                    )
                    incident.minutes_lost = loss['minutes_lost']
                    incident.money_lost = int(loss['money_lost_eur'])

                    db.commit()

                    try:
                        # Enqueue notification to ARQ (async task queue)
                        await enqueue_notification(incident, monitor.owner, monitor)
                        logger.info(f"  📧 Notification enqueued to ARQ")

                        # Reset escalation flags if this is a recovery
                        if incident.incident_type == "recovery":
                            reset_escalation_flags(db, monitor.id)

                    except Exception as e:
                        logger.error(f"  Failed to enqueue notification: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"  Error checking monitor {monitor.name}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)

    finally:
        db.close()


async def check_escalations():
    """Check all open incidents for escalation."""
    db = get_db()

    try:
        # Get all open (unresolved) DOWN incidents
        open_incidents = db.query(Incident).filter(
            Incident.resolved_at == None,
            Incident.incident_type == "down"
        ).all()

        logger.info(f"Checking {len(open_incidents)} open incidents for escalation...")

        for incident in open_incidents:
            try:
                # Get the monitor
                monitor = db.query(Monitor).filter(Monitor.id == incident.monitor_id).first()
                if not monitor:
                    continue

                # Check if escalation is needed
                should_escalate, escalation_channels = check_escalation(db, incident, monitor)

                if should_escalate:
                    logger.info(
                        f"Escalating incident {incident.id} for monitor {monitor.name} "
                        f"on channels: {escalation_channels}"
                    )

                    # Send escalation notifications
                    await enqueue_notification(
                        incident,
                        monitor.owner,
                        monitor,
                        channels=escalation_channels
                    )

            except Exception as e:
                logger.error(f"Error checking escalation for incident {incident.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Escalation check error: {e}", exc_info=True)

    finally:
        db.close()


def run_check_job():
    """Wrapper to run async check in sync scheduler."""
    asyncio.run(check_monitors())


def run_escalation_job():
    """Wrapper to run async escalation check in sync scheduler."""
    asyncio.run(check_escalations())


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

    # Check for escalations every 2 minutes
    scheduler.add_job(
        run_escalation_job,
        'interval',
        minutes=2,
        id='check_escalations',
        max_instances=1
    )

    try:
        logger.info("Worker started. Checking monitors every 30 seconds, escalations every 2 minutes.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped.")


if __name__ == '__main__':
    run_worker()
