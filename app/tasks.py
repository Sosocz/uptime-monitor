"""
ARQ task queue configuration and notification tasks.

This module handles async task processing for notifications with retry/backoff logic.
"""
import logging
from datetime import datetime, timedelta
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from arq.cron import cron
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.notification_log import NotificationLog
from app.models.user import User
from app.models.monitor import Monitor
from app.models.incident import Incident
from app.services.notification_service import send_email, send_telegram, send_webhook
from app.services.integration_notifications import (
    send_slack_notification,
    send_discord_notification,
    send_teams_notification,
    send_pagerduty_notification
)
from app.services.email_onboarding_service import (
    get_welcome_email_html,
    get_j1_reminder_email_html,
    get_j3_reminder_email_html
)

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session."""
    return SessionLocal()


async def send_email_notification(
    ctx,
    incident_id: int,
    user_id: int,
    monitor_id: int,
    recipient: str,
    subject: str,
    body: str
):
    """
    Send email notification via ARQ queue.

    Args:
        ctx: ARQ context
        incident_id: Incident ID
        user_id: User ID
        monitor_id: Monitor ID
        recipient: Email address
        subject: Email subject
        body: Email body (HTML)
    """
    db = get_db()
    log_entry = None

    try:
        # Create notification log entry
        log_entry = NotificationLog(
            incident_id=incident_id,
            user_id=user_id,
            monitor_id=monitor_id,
            channel="email",
            recipient=recipient,
            status="pending",
            attempts=0
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Attempt to send email
        log_entry.attempts += 1
        log_entry.last_attempt_at = datetime.utcnow()
        db.commit()

        await send_email(recipient, subject, body)

        # Mark as sent
        log_entry.status = "sent"
        log_entry.sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Email sent successfully to {recipient} for incident {incident_id}")
        return {"status": "sent", "log_id": log_entry.id}

    except Exception as e:
        logger.error(f"Email send failed to {recipient}: {e}", exc_info=True)

        if log_entry:
            log_entry.status = "failed"
            log_entry.error_message = str(e)[:1000]
            log_entry.retry_count += 1
            db.commit()

        # Raise exception to trigger ARQ retry
        raise

    finally:
        db.close()


async def send_telegram_notification(
    ctx,
    incident_id: int,
    user_id: int,
    monitor_id: int,
    recipient: str,
    message: str
):
    """
    Send Telegram notification via ARQ queue.

    Args:
        ctx: ARQ context
        incident_id: Incident ID
        user_id: User ID
        monitor_id: Monitor ID
        recipient: Telegram chat_id
        message: Message text
    """
    db = get_db()
    log_entry = None

    try:
        # Create notification log entry
        log_entry = NotificationLog(
            incident_id=incident_id,
            user_id=user_id,
            monitor_id=monitor_id,
            channel="telegram",
            recipient=recipient,
            status="pending",
            attempts=0
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Attempt to send Telegram message
        log_entry.attempts += 1
        log_entry.last_attempt_at = datetime.utcnow()
        db.commit()

        await send_telegram(recipient, message)

        # Mark as sent
        log_entry.status = "sent"
        log_entry.sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Telegram sent successfully to {recipient} for incident {incident_id}")
        return {"status": "sent", "log_id": log_entry.id}

    except Exception as e:
        logger.error(f"Telegram send failed to {recipient}: {e}", exc_info=True)

        if log_entry:
            log_entry.status = "failed"
            log_entry.error_message = str(e)[:1000]
            log_entry.retry_count += 1
            db.commit()

        # Raise exception to trigger ARQ retry
        raise

    finally:
        db.close()


async def send_webhook_notification(
    ctx,
    incident_id: int,
    user_id: int,
    monitor_id: int,
    recipient: str,
    payload: dict
):
    """
    Send webhook notification via ARQ queue.

    Args:
        ctx: ARQ context
        incident_id: Incident ID
        user_id: User ID
        monitor_id: Monitor ID
        recipient: Webhook URL
        payload: JSON payload
    """
    db = get_db()
    log_entry = None

    try:
        # Create notification log entry
        log_entry = NotificationLog(
            incident_id=incident_id,
            user_id=user_id,
            monitor_id=monitor_id,
            channel="webhook",
            recipient=recipient,
            status="pending",
            attempts=0
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Attempt to send webhook
        log_entry.attempts += 1
        log_entry.last_attempt_at = datetime.utcnow()
        db.commit()

        await send_webhook(recipient, payload)

        # Mark as sent
        log_entry.status = "sent"
        log_entry.sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Webhook sent successfully to {recipient} for incident {incident_id}")
        return {"status": "sent", "log_id": log_entry.id}

    except Exception as e:
        logger.error(f"Webhook send failed to {recipient}: {e}", exc_info=True)

        if log_entry:
            log_entry.status = "failed"
            log_entry.error_message = str(e)[:1000]
            log_entry.retry_count += 1
            db.commit()

        # Raise exception to trigger ARQ retry
        raise

    finally:
        db.close()


def should_send_notification(db: Session, incident_id: int, user_id: int, channel: str) -> bool:
    """
    Check if a notification should be sent based on cooldown settings.

    Args:
        db: Database session
        incident_id: Incident ID
        user_id: User ID
        channel: Notification channel (email, telegram, etc.)

    Returns:
        True if notification should be sent, False if in cooldown period
    """
    cooldown_seconds = settings.NOTIFICATION_COOLDOWN_SECONDS

    # Check for recent notifications for the same incident/user/channel
    cutoff_time = datetime.utcnow() - timedelta(seconds=cooldown_seconds)

    recent_notification = db.query(NotificationLog).filter(
        NotificationLog.incident_id == incident_id,
        NotificationLog.user_id == user_id,
        NotificationLog.channel == channel,
        NotificationLog.created_at > cutoff_time,
        NotificationLog.status == "sent"
    ).first()

    if recent_notification:
        logger.info(
            f"Notification cooldown active for incident {incident_id}, "
            f"user {user_id}, channel {channel}. Skipping."
        )
        return False

    return True


async def send_onboarding_welcome_email(ctx, user_id: int):
    """
    Send welcome email (J0) to a new user.

    Args:
        ctx: ARQ context
        user_id: User ID
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for welcome email")
            return

        subject = "🎉 Bienvenue sur TrezApp - Ajoute ton premier monitor"
        body = get_welcome_email_html(user.email)

        await send_email(user.email, subject, body)
        logger.info(f"Welcome email sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user_id}: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def send_password_reset_email(ctx, user_id: int, reset_url: str):
    """
    Send password reset email.

    Args:
        ctx: ARQ context
        user_id: User ID
        reset_url: Password reset URL with token
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for password reset email")
            return

        subject = "🔐 Réinitialisation de votre mot de passe TrezApp"
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #ffffff; margin: 0; padding: 40px 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 48px 32px; }}
                .logo {{ text-align: center; margin-bottom: 32px; font-size: 48px; }}
                h1 {{ font-size: 28px; font-weight: 700; margin: 0 0 16px 0; color: #ffffff; }}
                p {{ font-size: 16px; line-height: 1.6; color: rgba(255, 255, 255, 0.8); margin: 0 0 24px 0; }}
                .btn {{ display: inline-block; background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3)); border: 2px solid rgba(102, 126, 234, 0.5); border-radius: 12px; padding: 16px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; margin: 24px 0; }}
                .btn:hover {{ background: linear-gradient(135deg, rgba(102, 126, 234, 0.5), rgba(118, 75, 162, 0.5)); }}
                .footer {{ margin-top: 32px; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.1); text-align: center; font-size: 14px; color: rgba(255, 255, 255, 0.5); }}
                .warning {{ background: rgba(255, 71, 87, 0.2); border: 1px solid rgba(255, 71, 87, 0.3); border-radius: 12px; padding: 16px; margin: 24px 0; color: #ff6b7a; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔐</div>
                <h1>Réinitialisation de mot de passe</h1>
                <p>Bonjour,</p>
                <p>Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte TrezApp.</p>
                <p>Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>

                <div style="text-align: center;">
                    <a href="{reset_url}" class="btn">Réinitialiser mon mot de passe</a>
                </div>

                <div class="warning">
                    <strong>⚠️ Important :</strong> Ce lien est valide pendant 1 heure seulement.
                </div>

                <p style="font-size: 14px; color: rgba(255, 255, 255, 0.6);">
                    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email. Votre mot de passe restera inchangé.
                </p>

                <div class="footer">
                    <p>TrezApp - Surveillance Uptime 24/7</p>
                    <p>{settings.APP_BASE_URL}</p>
                </div>
            </div>
        </body>
        </html>
        """

        await send_email(user.email, subject, body)
        logger.info(f"Password reset email sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user_id}: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def send_onboarding_j1_email(ctx, user_id: int):
    """
    Send J+1 reminder email.

    Args:
        ctx: ARQ context
        user_id: User ID
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.onboarding_email_j1_sent or user.onboarding_completed:
            return

        # Check if user has monitors
        has_monitors = len(user.monitors) > 0

        # Logic:
        # - If no monitors: remind to add first monitor
        # - If monitors but no Telegram: suggest Telegram activation
        if not has_monitors:
            subject = "Tu n'as pas encore ajouté de monitor 🤔"
        elif not user.telegram_chat_id:
            subject = "💡 Active les notifications Telegram"
        else:
            # User has monitors + Telegram already, skip email
            user.onboarding_email_j1_sent = True
            db.commit()
            return

        body = get_j1_reminder_email_html(user.email, has_monitors)

        await send_email(user.email, subject, body)

        # Mark as sent
        user.onboarding_email_j1_sent = True
        db.commit()

        logger.info(f"J+1 email sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send J+1 email to user {user_id}: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def send_onboarding_j3_email(ctx, user_id: int):
    """
    Send J+3 reminder email.

    Args:
        ctx: ARQ context
        user_id: User ID
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.onboarding_email_j3_sent or user.onboarding_completed:
            return

        # Only send if user has at least 1 monitor
        has_monitors = len(user.monitors) > 0
        if not has_monitors:
            # Skip email if no monitors yet (not relevant)
            user.onboarding_email_j3_sent = True
            db.commit()
            return

        # Check if user has status page
        has_status_page = len(user.status_pages) > 0
        if has_status_page:
            # Already has status page, skip
            user.onboarding_email_j3_sent = True
            db.commit()
            return

        subject = "📊 Crée une status page publique"
        body = get_j3_reminder_email_html(user.email, has_status_page)

        await send_email(user.email, subject, body)

        # Mark as sent
        user.onboarding_email_j3_sent = True
        db.commit()

        logger.info(f"J+3 email sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send J+3 email to user {user_id}: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def check_and_send_onboarding_emails(ctx):
    """
    Periodic task to check and send onboarding emails (J+1 and J+3).
    Runs every hour.
    """
    db = get_db()
    redis_pool: ArqRedis = ctx['redis']

    try:
        now = datetime.utcnow()

        # Find users who need J+1 email (created 24-25 hours ago, not sent yet)
        j1_start = now - timedelta(hours=25)
        j1_end = now - timedelta(hours=24)

        users_j1 = db.query(User).filter(
            User.created_at >= j1_start,
            User.created_at <= j1_end,
            User.onboarding_email_j1_sent == False,
            User.onboarding_completed == False,
            User.is_active == True
        ).all()

        for user in users_j1:
            await redis_pool.enqueue_job('send_onboarding_j1_email', user.id)
            logger.info(f"Enqueued J+1 email for user {user.id}")

        # Find users who need J+3 email (created 72-73 hours ago, not sent yet)
        j3_start = now - timedelta(hours=73)
        j3_end = now - timedelta(hours=72)

        users_j3 = db.query(User).filter(
            User.created_at >= j3_start,
            User.created_at <= j3_end,
            User.onboarding_email_j3_sent == False,
            User.onboarding_completed == False,
            User.is_active == True
        ).all()

        for user in users_j3:
            await redis_pool.enqueue_job('send_onboarding_j3_email', user.id)
            logger.info(f"Enqueued J+3 email for user {user.id}")

        logger.info(f"Onboarding check complete: {len(users_j1)} J+1 emails, {len(users_j3)} J+3 emails")

    except Exception as e:
        logger.error(f"Failed to check onboarding emails: {e}", exc_info=True)
    finally:
        db.close()


# ARQ Worker Settings
class WorkerSettings:
    """ARQ worker configuration."""

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    functions = [
        send_email_notification,
        send_telegram_notification,
        send_webhook_notification,
        send_onboarding_welcome_email,
        send_onboarding_j1_email,
        send_onboarding_j3_email,
        send_password_reset_email,  # ADDED: Password reset email function
        check_and_send_onboarding_emails,
    ]

    # Cron jobs
    cron_jobs = [
        cron(check_and_send_onboarding_emails, hour={0, 6, 12, 18}, minute=0)  # Every 6 hours
    ]

    # Retry configuration
    max_tries = settings.MAX_NOTIFICATION_RETRIES + 1  # +1 for initial attempt
    retry_jobs = True

    # Exponential backoff: 5s, 30s, 2min
    job_timeout = 60  # 60 seconds max per job
    keep_result = 3600  # Keep results for 1 hour


async def enqueue_notification(
    incident: Incident,
    user: User,
    monitor: Monitor,
    channels: list[str] = None
):
    """
    Enqueue notification tasks to ARQ.

    Args:
        incident: Incident object
        user: User object
        monitor: Monitor object
        channels: List of channels to notify (default: ['email', 'telegram'])
    """
    if channels is None:
        channels = ['email']
        if user.telegram_chat_id:
            channels.append('telegram')
        if user.webhook_url:
            channels.append('webhook')
        if user.slack_webhook_url:
            channels.append('slack')
        if user.discord_webhook_url:
            channels.append('discord')
        if user.teams_webhook_url:
            channels.append('teams')
        if user.pagerduty_integration_key:
            channels.append('pagerduty')

    redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    db = get_db()

    try:
        for channel in channels:
            # Check cooldown
            if not should_send_notification(db, incident.id, user.id, channel):
                continue

            if channel == 'email':
                # Build email content with INTELLIGENT ANALYSIS
                if incident.incident_type == "down":
                    severity_emoji = "🔴" if incident.severity == "SEV1" else "🟡"
                    subject = f"{severity_emoji} Site DOWN: {monitor.name}"

                    # FREE vs PRO content
                    is_free = user.plan == "FREE"

                    if is_free:
                        # FREE: Show basic cause + tease PRO features
                        basic_cause = incident.cause or "Unknown cause"

                        # Show money lost to create urgency
                        loss_html = ""
                        if incident.minutes_lost > 0 or incident.money_lost > 0:
                            loss_html = f"<p><strong>💸 Estimated Loss:</strong> "
                            if incident.money_lost > 0:
                                loss_html += f"~€{incident.money_lost}"
                            if incident.minutes_lost > 0:
                                loss_html += f" • {incident.minutes_lost} minutes down"
                            loss_html += "</p>"

                        body = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #dc2626;">{severity_emoji} Site DOWN</h2>
                            <div style="background: #fee2e2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0;">
                                <p style="margin: 0;"><strong>URL:</strong> <a href="{monitor.url}">{monitor.url}</a></p>
                            </div>

                            <div style="margin: 20px 0;">
                                <p><strong>Status:</strong> {basic_cause}</p>
                                <p><strong>⚠️ Severity:</strong> {incident.severity}</p>
                                <p><strong>Started At:</strong> {incident.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                                {loss_html}
                            </div>

                            <!-- PRO Upsell -->
                            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 25px; border-radius: 12px; margin: 30px 0; text-align: center;">
                                <div style="font-size: 48px; margin-bottom: 15px;">🔒</div>
                                <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 22px;">Want to know WHY it went down?</h3>
                                <p style="color: rgba(255,255,255,0.9); margin: 0 0 20px 0; font-size: 16px;">
                                    Upgrade to PRO for intelligent root cause analysis, fix recommendations, and client-ready reports.
                                </p>
                                <a href="{settings.APP_BASE_URL}/upgrade" style="display: inline-block; background: #fff; color: #667eea; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                                    Upgrade to PRO - €19/month
                                </a>
                                <p style="color: rgba(255,255,255,0.7); margin: 15px 0 0 0; font-size: 13px;">
                                    Unlock: Root cause analysis • Recommendations • Money tracking • Client reports
                                </p>
                            </div>

                            <div style="background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 6px; text-align: center;">
                                <p style="font-size: 12px; color: #666; margin: 0;">Monitored by <strong>TrezApp</strong> - Professional Uptime Monitoring</p>
                            </div>
                        </div>
                        """
                    else:
                        # PRO: Show full intelligent analysis
                        cause = incident.intelligent_cause or incident.cause or "Unknown cause"

                        # Build recommendations HTML
                        recommendations_html = ""
                        if incident.recommendations:
                            recommendations_html = "<h3 style='color: #f59e0b;'>💡 Recommended Actions:</h3><ul>"
                            for rec in incident.recommendations[:3]:  # Max 3 recommendations
                                recommendations_html += f"<li>{rec}</li>"
                            recommendations_html += "</ul>"

                        # Time/money lost
                        loss_html = ""
                        if incident.minutes_lost > 0:
                            loss_html = f"<p><strong>⏱️ Time Lost:</strong> {incident.minutes_lost} minutes"
                            if incident.money_lost > 0:
                                loss_html += f" (~€{incident.money_lost})"
                            loss_html += "</p>"

                        body = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #dc2626;">{severity_emoji} Site DOWN</h2>
                            <div style="background: #fee2e2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0;">
                                <p style="margin: 0;"><strong>URL:</strong> <a href="{monitor.url}">{monitor.url}</a></p>
                            </div>

                            <h3 style="color: #1e40af;">🧠 Why it went down</h3>
                            <p style="background: #f0f9ff; padding: 15px; border-radius: 6px;">{cause}</p>

                            {recommendations_html}

                            <div style="margin: 20px 0;">
                                <p><strong>⚠️ Severity:</strong> {incident.severity}</p>
                                <p><strong>Failed Checks:</strong> {incident.failed_checks_count}</p>
                                <p><strong>Started At:</strong> {incident.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                                {loss_html}
                            </div>

                            <div style="background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 6px; text-align: center;">
                                <p style="font-size: 12px; color: #666; margin: 0;">Monitored by <strong>TrezApp</strong> - Professional Uptime Monitoring</p>
                            </div>
                        </div>
                        """
                else:  # recovery
                    duration_str = f"{incident.duration_seconds // 60}min {incident.duration_seconds % 60}s" if incident.duration_seconds else "N/A"

                    # Time/money lost summary
                    loss_html = ""
                    if incident.minutes_lost > 0:
                        loss_html = f"<p><strong>⏱️ Total Downtime:</strong> {incident.minutes_lost} minutes"
                        if incident.money_lost > 0:
                            loss_html += f" (Estimated loss: ~{incident.money_lost}€)"
                        loss_html += "</p>"

                    subject = f"🟢 Site UP: {monitor.name}"
                    body = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #16a34a;">✅ Site RECOVERED</h2>
                        <div style="background: #d1fae5; padding: 15px; border-left: 4px solid #16a34a; margin: 20px 0;">
                            <p style="margin: 0;"><strong>URL:</strong> <a href="{monitor.url}">{monitor.url}</a></p>
                        </div>

                        <div style="margin: 20px 0;">
                            <p><strong>⏱️ Downtime:</strong> {duration_str}</p>
                            <p><strong>Resolved At:</strong> {incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S UTC") if incident.resolved_at else "Now"}</p>
                            {loss_html}
                        </div>

                        <div style="background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 6px; text-align: center;">
                            <p style="font-size: 12px; color: #666; margin: 0;">Monitored by <strong>TrezApp</strong> - Professional Uptime Monitoring</p>
                        </div>
                    </div>
                    """

                await redis_pool.enqueue_job(
                    'send_email_notification',
                    incident.id,
                    user.id,
                    monitor.id,
                    user.email,
                    subject,
                    body
                )
                logger.info(f"Enqueued email notification for incident {incident.id}")

            elif channel == 'telegram' and user.telegram_chat_id:
                # Build Telegram message with INTELLIGENT ANALYSIS
                if incident.incident_type == "down":
                    cause = incident.intelligent_cause or incident.cause or "Unknown cause"
                    severity_emoji = "🔴" if incident.severity == "SEV1" else "🟡"

                    message = f"{severity_emoji} <b>SITE DOWN</b>\n"
                    message += f"<b>{monitor.name}</b>\n"
                    message += f"{monitor.url}\n\n"
                    message += f"🧠 <b>Why:</b> {cause}\n"
                    message += f"⚠️ <b>Severity:</b> {incident.severity}\n"
                    message += f"<b>Failed checks:</b> {incident.failed_checks_count}\n"

                    if incident.minutes_lost > 0:
                        message += f"\n⏱️ <b>Time lost:</b> {incident.minutes_lost} min"
                        if incident.money_lost > 0:
                            message += f" (~{incident.money_lost}€)"

                    if incident.recommendations and len(incident.recommendations) > 0:
                        message += f"\n\n💡 <b>Recommended:</b>\n• {incident.recommendations[0]}"

                else:
                    duration_str = f"{incident.duration_seconds // 60}min {incident.duration_seconds % 60}s" if incident.duration_seconds else "N/A"

                    message = f"✅ <b>SITE RECOVERED</b>\n"
                    message += f"<b>{monitor.name}</b>\n"
                    message += f"{monitor.url}\n\n"
                    message += f"⏱️ <b>Downtime:</b> {duration_str}\n"

                    if incident.minutes_lost > 0:
                        message += f"<b>Total lost:</b> {incident.minutes_lost} min"
                        if incident.money_lost > 0:
                            message += f" (~{incident.money_lost}€)"

                await redis_pool.enqueue_job(
                    'send_telegram_notification',
                    incident.id,
                    user.id,
                    monitor.id,
                    user.telegram_chat_id,
                    message
                )
                logger.info(f"Enqueued Telegram notification for incident {incident.id}")

            elif channel == 'webhook' and user.webhook_url:
                # Build webhook payload
                payload = {
                    "event": "incident." + incident.incident_type,
                    "incident_id": incident.id,
                    "monitor": {
                        "id": monitor.id,
                        "name": monitor.name,
                        "url": monitor.url
                    },
                    "incident": {
                        "type": incident.incident_type,
                        "started_at": incident.started_at.isoformat() if incident.started_at else None,
                        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                        "duration_seconds": incident.duration_seconds,
                        "cause": incident.cause,
                        "failed_checks_count": incident.failed_checks_count,
                        "status_code": incident.status_code,
                        "error_message": incident.error_message
                    }
                }

                await redis_pool.enqueue_job(
                    'send_webhook_notification',
                    incident.id,
                    user.id,
                    monitor.id,
                    user.webhook_url,
                    payload
                )
                logger.info(f"Enqueued webhook notification for incident {incident.id}")
            
            elif channel == 'slack' and user.slack_webhook_url:
                message = "🚨 Site DOWN" if incident.incident_type == "down" else "✅ Site RECOVERED"
                incident_data = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "status": incident.incident_type,
                    "cause": incident.intelligent_cause or incident.cause,
                    "status_code": incident.status_code,
                    "severity": incident.severity
                }
                await redis_pool.enqueue_job(
                    'send_slack_notification',
                    user.slack_webhook_url,
                    message,
                    incident_data
                )
                logger.info(f"Enqueued Slack notification for incident {incident.id}")
            
            elif channel == 'discord' and user.discord_webhook_url:
                message = "🚨 Site DOWN" if incident.incident_type == "down" else "✅ Site RECOVERED"
                incident_data = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "status": incident.incident_type,
                    "cause": incident.intelligent_cause or incident.cause,
                    "status_code": incident.status_code,
                    "severity": incident.severity
                }
                await redis_pool.enqueue_job(
                    'send_discord_notification',
                    user.discord_webhook_url,
                    message,
                    incident_data
                )
                logger.info(f"Enqueued Discord notification for incident {incident.id}")
            
            elif channel == 'teams' and user.teams_webhook_url:
                message = "🚨 Site DOWN" if incident.incident_type == "down" else "✅ Site RECOVERED"
                incident_data = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "status": incident.incident_type,
                    "cause": incident.intelligent_cause or incident.cause,
                    "status_code": incident.status_code,
                    "severity": incident.severity
                }
                await redis_pool.enqueue_job(
                    'send_teams_notification',
                    user.teams_webhook_url,
                    message,
                    incident_data
                )
                logger.info(f"Enqueued Teams notification for incident {incident.id}")
            
            elif channel == 'pagerduty' and user.pagerduty_integration_key and incident.incident_type == "down":
                incident_data = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "status_code": incident.status_code,
                    "cause": incident.intelligent_cause or incident.cause
                }
                await redis_pool.enqueue_job(
                    'send_pagerduty_notification',
                    user.pagerduty_integration_key,
                    incident_data
                )
                logger.info(f"Enqueued PagerDuty notification for incident {incident.id}")

    finally:
        db.close()
        await redis_pool.close()


# ============================================================================
# LIFECYCLE EMAILS (Monthly reports, upgrade nudges, re-engagement)
# ============================================================================

async def send_monthly_reports(ctx):
    """
    Send monthly uptime reports to all active users.
    Run on 1st of each month via cron.
    """
    from app.services.email_lifecycle_service import get_monthly_report_email
    from app.models.check import Check
    from datetime import datetime, timedelta

    db = get_db()
    try:
        # Get all active users with at least 1 monitor
        users = db.query(User).filter(
            User.is_active == True,
            User.email.isnot(None)
        ).all()

        for user in users:
            monitors = db.query(Monitor).filter(Monitor.user_id == user.id).all()
            if not monitors:
                continue

            # Calculate stats for last month
            last_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            last_month_start = last_month_start.replace(day=1)
            last_month_end = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            total_checks = 0
            up_checks = 0
            total_response_time = 0
            response_time_count = 0
            best_monitor = None
            best_uptime = 0

            for monitor in monitors:
                checks = db.query(Check).filter(
                    Check.monitor_id == monitor.id,
                    Check.checked_at >= last_month_start,
                    Check.checked_at < last_month_end
                ).all()

                if checks:
                    monitor_up = len([c for c in checks if c.status == "up"])
                    monitor_uptime = (monitor_up / len(checks)) * 100 if checks else 0
                    total_checks += len(checks)
                    up_checks += monitor_up

                    if monitor_uptime > best_uptime:
                        best_uptime = monitor_uptime
                        best_monitor = monitor.name

                    for check in checks:
                        if check.response_time:
                            total_response_time += check.response_time
                            response_time_count += 1

            if total_checks == 0:
                continue

            avg_uptime = (up_checks / total_checks) * 100
            avg_response_time = int(total_response_time / response_time_count) if response_time_count > 0 else 0
            incidents_count = db.query(Incident).filter(
                Incident.user_id == user.id,
                Incident.started_at >= last_month_start,
                Incident.started_at < last_month_end
            ).count()

            month_data = {
                "month": last_month_start.strftime("%B %Y"),
                "total_uptime": round(avg_uptime, 2),
                "incidents_count": incidents_count,
                "most_reliable_site": best_monitor or monitors[0].name,
                "avg_response_time": avg_response_time,
                "total_checks": total_checks
            }

            html_content = get_monthly_report_email(user.email, month_data)
            send_email(
                to_email=user.email,
                subject=f"📊 Your {month_data['month']} Uptime Report",
                html_content=html_content
            )
            logger.info(f"Sent monthly report to {user.email}")

    finally:
        db.close()


async def send_upgrade_nudges(ctx):
    """
    Send upgrade emails to engaged FREE users.
    Run daily via cron.
    """
    from app.services.email_lifecycle_service import get_upgrade_nudge_email
    from datetime import datetime, timedelta

    db = get_db()
    try:
        # Find engaged FREE users (3+ monitors, active for 14+ days)
        cutoff_date = datetime.utcnow() - timedelta(days=14)

        users = db.query(User).filter(
            User.plan == "FREE",
            User.is_active == True,
            User.created_at <= cutoff_date
        ).all()

        for user in users:
            monitors_count = db.query(Monitor).filter(Monitor.user_id == user.id).count()

            if monitors_count >= 3:  # Engaged user
                # Check if we already sent upgrade nudge recently
                last_nudge = db.query(TrackingEvent).filter(
                    TrackingEvent.user_id == user.id,
                    TrackingEvent.event_type == "email.upgrade_nudge_sent"
                ).order_by(TrackingEvent.created_at.desc()).first()

                if last_nudge and (datetime.utcnow() - last_nudge.created_at).days < 30:
                    continue  # Don't spam

                # Calculate usage data
                months_active = (datetime.utcnow() - user.created_at).days // 30
                alerts_sent = db.query(NotificationLog).filter(
                    NotificationLog.user_id == user.id,
                    NotificationLog.status == "sent"
                ).count()

                # Calculate avg uptime
                checks = db.query(Check).join(Monitor).filter(
                    Monitor.user_id == user.id,
                    Check.checked_at >= datetime.utcnow() - timedelta(days=30)
                ).all()

                avg_uptime = 99.0
                if checks:
                    up_count = len([c for c in checks if c.status == "up"])
                    avg_uptime = round((up_count / len(checks)) * 100, 1)

                usage_data = {
                    "monitors_count": monitors_count,
                    "months_active": max(1, months_active),
                    "alerts_sent": alerts_sent,
                    "avg_uptime": avg_uptime
                }

                html_content = get_upgrade_nudge_email(user.email, usage_data)
                send_email(
                    to_email=user.email,
                    subject="🎉 You're getting a lot of value from TrezApp!",
                    html_content=html_content
                )

                # Track event
                track_event(db, "email.upgrade_nudge_sent", user_id=user.id, event_data=usage_data)
                logger.info(f"Sent upgrade nudge to {user.email}")

    finally:
        db.close()


async def send_annual_upsells(ctx):
    """
    Send annual billing upsell to monthly PRO users.
    Run weekly via cron.
    """
    from app.services.email_lifecycle_service import get_annual_upsell_email
    from datetime import datetime, timedelta

    db = get_db()
    try:
        # Find PRO users on monthly billing for 3+ months
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        users = db.query(User).filter(
            User.plan == "PAID",
            User.is_active == True,
            User.stripe_subscription_id.isnot(None),
            User.created_at <= cutoff_date
        ).all()

        for user in users:
            # Check if already on annual (TODO: add field to track billing frequency)
            # For now, just check if we sent this email before
            last_upsell = db.query(TrackingEvent).filter(
                TrackingEvent.user_id == user.id,
                TrackingEvent.event_type == "email.annual_upsell_sent"
            ).first()

            if last_upsell:
                continue  # Already sent, skip

            months_on_monthly = (datetime.utcnow() - user.created_at).days // 30
            html_content = get_annual_upsell_email(user.email, months_on_monthly)
            send_email(
                to_email=user.email,
                subject="💰 Save €48/year with annual billing",
                html_content=html_content
            )

            # Track event
            track_event(db, "email.annual_upsell_sent", user_id=user.id)
            logger.info(f"Sent annual upsell to {user.email}")

    finally:
        db.close()


async def send_reengagement_emails(ctx):
    """
    Send re-engagement emails to inactive users.
    Run weekly via cron.
    """
    from app.services.email_lifecycle_service import get_reengagement_email
    from datetime import datetime, timedelta

    db = get_db()
    try:
        # Find users inactive for 30+ days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        users = db.query(User).filter(
            User.is_active == True,
            User.last_login_at.isnot(None),
            User.last_login_at <= cutoff_date
        ).all()

        for user in users:
            # Check if we already sent reengagement email
            last_reengagement = db.query(TrackingEvent).filter(
                TrackingEvent.user_id == user.id,
                TrackingEvent.event_type == "email.reengagement_sent"
            ).order_by(TrackingEvent.created_at.desc()).first()

            if last_reengagement and (datetime.utcnow() - last_reengagement.created_at).days < 60:
                continue  # Don't spam

            days_inactive = (datetime.utcnow() - user.last_login_at).days
            html_content = get_reengagement_email(user.email, days_inactive)
            send_email(
                to_email=user.email,
                subject="👋 We miss you!",
                html_content=html_content
            )

            # Track event
            track_event(db, "email.reengagement_sent", user_id=user.id, event_data={"days_inactive": days_inactive})
            logger.info(f"Sent reengagement email to {user.email} ({days_inactive} days inactive)")

    finally:
        db.close()
