"""
Notification service - low-level email and Telegram sending functions.

These functions are called by ARQ tasks and should not be called directly
from the application code. Use app.tasks.enqueue_notification() instead.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str):
    """
    Send an email notification.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (HTML format)

    Raises:
        Exception: If email sending fails
    """
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
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Email send error to {to}: {e}", exc_info=True)
        raise


async def send_telegram(chat_id: str, message: str):
    """
    Send a Telegram notification.

    Args:
        chat_id: Telegram chat ID
        message: Message text

    Raises:
        Exception: If Telegram sending fails
    """
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            response.raise_for_status()
        logger.info(f"Telegram sent to {chat_id}")
    except Exception as e:
        logger.error(f"Telegram send error to {chat_id}: {e}", exc_info=True)
        raise


async def send_webhook(webhook_url: str, payload: dict):
    """
    Send a webhook notification.

    Args:
        webhook_url: Webhook endpoint URL
        payload: JSON payload to send

    Raises:
        Exception: If webhook delivery fails
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        logger.info(f"Webhook sent to {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook send error to {webhook_url}: {e}", exc_info=True)
        raise

