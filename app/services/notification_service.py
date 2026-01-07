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

    # ✅ safe getters (évite crash si les champs n'existent pas)
    status_code = getattr(incident, "status_code", None)
    error_message = getattr(incident, "error_message", None)

    if incident.incident_type == "down":
        if status_code:
            problem = f"HTTP {status_code}"
        elif error_message:
            problem = str(error_message)
        else:
            problem = "DOWN (cause inconnue)"

        subject = f"🔴 Site DOWN : {monitor.url}"
        body = f"""
        <h2 style="color: #dc2626;">Site DOWN</h2>
        <p><strong>URL :</strong> {monitor.url}</p>
        <p><strong>Problème :</strong> {problem}</p>
        <p><strong>Heure :</strong> {incident.started_at}</p>
        """

        telegram_msg = f"🔴 SITE DOWN\n{monitor.url}\nProblème : {problem}"

    else:
        subject = f"🟢 Site UP : {monitor.url}"
        body = f"""
        <h2 style="color: #16a34a;">Site UP</h2>
        <p><strong>URL :</strong> {monitor.url}</p>
        <p><strong>Heure :</strong> {incident.resolved_at}</p>
        """

        telegram_msg = f"🟢 SITE UP\n{monitor.url}"

    await send_email(user.email, subject, body)

    if user.telegram_chat_id:
        await send_telegram(user.telegram_chat_id, telegram_msg)

