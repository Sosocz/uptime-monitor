import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from app.core.config import settings
from app.models.user import User
from app.models.monitor import Monitor
from app.models.incident import Incident


async def send_email(to: str, subject: str, body: str):
    """Send an email notification."""
    try:
        message = MIMEMultipart()
        message["From"] = settings.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True
        )
    except Exception as e:
        print(f"Email send error: {e}")


async def send_telegram(chat_id: str, message: str):
    """Send a Telegram notification."""
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "text": message})
    except Exception as e:
        print(f"Telegram send error: {e}")


async def notify_incident(user: User, monitor: Monitor, incident: Incident):
    """Send notifications for an incident (down or recovery)."""
    if incident.incident_type == "down":
        subject = f"🔴 Monitor DOWN: {monitor.name}"
        body = f"""
        <h2 style="color: #dc2626;">Monitor is DOWN</h2>
        <p><strong>Monitor:</strong> {monitor.name}</p>
        <p><strong>URL:</strong> {monitor.url}</p>
        <p><strong>Time:</strong> {incident.started_at}</p>
        <p><a href="{settings.APP_BASE_URL}/monitors/{monitor.id}">View Details</a></p>
        """
        telegram_msg = f"🔴 Monitor DOWN\n{monitor.name}\n{monitor.url}"
    else:
        subject = f"🟢 Monitor RECOVERED: {monitor.name}"
        body = f"""
        <h2 style="color: #16a34a;">Monitor is RECOVERED</h2>
        <p><strong>Monitor:</strong> {monitor.name}</p>
        <p><strong>URL:</strong> {monitor.url}</p>
        <p><strong>Time:</strong> {incident.resolved_at}</p>
        <p><a href="{settings.APP_BASE_URL}/monitors/{monitor.id}">View Details</a></p>
        """
        telegram_msg = f"🟢 Monitor RECOVERED\n{monitor.name}\n{monitor.url}"
    
    # Send email notification
    await send_email(user.email, subject, body)
    
    # Send Telegram notification if configured
    if user.telegram_chat_id:
        await send_telegram(user.telegram_chat_id, telegram_msg)
