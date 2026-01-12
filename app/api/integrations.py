"""
Integrations API - manage Slack, Discord, Teams, PagerDuty, Webhook integrations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter()


class IntegrationRequest(BaseModel):
    integration_type: str  # slack, discord, teams, pagerduty, webhook
    config: dict


@router.get("/integrations")
async def get_integrations(current_user: User = Depends(get_current_user)):
    """Get all integrations status for current user."""
    return {
        "slack": {
            "connected": bool(current_user.slack_webhook_url),
            "url": current_user.slack_webhook_url
        },
        "discord": {
            "connected": bool(current_user.discord_webhook_url),
            "url": current_user.discord_webhook_url
        },
        "teams": {
            "connected": bool(current_user.teams_webhook_url),
            "url": current_user.teams_webhook_url
        },
        "pagerduty": {
            "connected": bool(current_user.pagerduty_integration_key),
            "integration_key": current_user.pagerduty_integration_key
        },
        "webhook": {
            "connected": bool(current_user.webhook_url),
            "url": current_user.webhook_url
        },
        "telegram": {
            "connected": bool(current_user.telegram_chat_id),
            "chat_id": current_user.telegram_chat_id
        }
    }


@router.post("/integrations")
async def connect_integration(
    integration: IntegrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Connect or update an integration."""
    
    integration_type = integration.integration_type.lower()
    config = integration.config
    
    if integration_type == "slack":
        if "webhook_url" not in config:
            raise HTTPException(status_code=400, detail="webhook_url required for Slack")
        current_user.slack_webhook_url = config["webhook_url"]
    
    elif integration_type == "discord":
        if "webhook_url" not in config:
            raise HTTPException(status_code=400, detail="webhook_url required for Discord")
        current_user.discord_webhook_url = config["webhook_url"]
    
    elif integration_type == "teams":
        if "webhook_url" not in config:
            raise HTTPException(status_code=400, detail="webhook_url required for Teams")
        current_user.teams_webhook_url = config["webhook_url"]
    
    elif integration_type == "pagerduty":
        if "integration_key" not in config:
            raise HTTPException(status_code=400, detail="integration_key required for PagerDuty")
        current_user.pagerduty_integration_key = config["integration_key"]
    
    elif integration_type == "webhook":
        if "url" not in config:
            raise HTTPException(status_code=400, detail="url required for Webhook")
        current_user.webhook_url = config["url"]
    
    elif integration_type == "telegram":
        if "chat_id" not in config:
            raise HTTPException(status_code=400, detail="chat_id required for Telegram")
        current_user.telegram_chat_id = config["chat_id"]
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown integration type: {integration_type}")
    
    db.commit()
    
    return {
        "success": True,
        "message": f"{integration_type} integration connected successfully"
    }


@router.delete("/integrations/{integration_type}")
async def disconnect_integration(
    integration_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect an integration."""
    
    integration_type = integration_type.lower()
    
    if integration_type == "slack":
        current_user.slack_webhook_url = None
    elif integration_type == "discord":
        current_user.discord_webhook_url = None
    elif integration_type == "teams":
        current_user.teams_webhook_url = None
    elif integration_type == "pagerduty":
        current_user.pagerduty_integration_key = None
    elif integration_type == "webhook":
        current_user.webhook_url = None
    elif integration_type == "telegram":
        current_user.telegram_chat_id = None
    else:
        raise HTTPException(status_code=400, detail=f"Unknown integration type: {integration_type}")
    
    db.commit()
    
    return {
        "success": True,
        "message": f"{integration_type} integration disconnected"
    }


@router.post("/integrations/test/{integration_type}")
async def test_integration(
    integration_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send test notification to an integration."""
    from app.services.integration_notifications import (
        send_slack_notification,
        send_discord_notification,
        send_teams_notification,
        send_pagerduty_notification
    )
    
    integration_type = integration_type.lower()
    test_message = "🧪 Test notification from TrezApp - Integration is working!"
    
    incident_data = {
        "monitor_name": "Test Monitor",
        "url": "https://example.com",
        "status": "down",
        "cause": "Test incident",
        "status_code": 500,
        "severity": "SEV1"
    }
    
    success = False
    
    if integration_type == "slack" and current_user.slack_webhook_url:
        success = await send_slack_notification(current_user.slack_webhook_url, test_message, incident_data)
    elif integration_type == "discord" and current_user.discord_webhook_url:
        success = await send_discord_notification(current_user.discord_webhook_url, test_message, incident_data)
    elif integration_type == "teams" and current_user.teams_webhook_url:
        success = await send_teams_notification(current_user.teams_webhook_url, test_message, incident_data)
    elif integration_type == "pagerduty" and current_user.pagerduty_integration_key:
        success = await send_pagerduty_notification(current_user.pagerduty_integration_key, incident_data)
    elif integration_type == "webhook" and current_user.webhook_url:
        from app.services.notification_service import send_webhook
        success = await send_webhook(current_user.webhook_url, incident_data)
    else:
        raise HTTPException(status_code=400, detail=f"{integration_type} not configured")
    
    if success:
        return {"success": True, "message": f"Test notification sent to {integration_type}"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification to {integration_type}")
