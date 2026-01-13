"""
Integration notification services - Slack, Discord, Teams, PagerDuty
"""
import httpx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


async def send_slack_notification(webhook_url: str, message: str, incident_data: Optional[Dict] = None) -> bool:
    """
    Send notification to Slack via webhook.
    
    Args:
        webhook_url: Slack webhook URL
        message: Plain text message
        incident_data: Optional incident data for rich formatting
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not webhook_url:
            return False
        
        # Build rich payload if incident data is available
        payload = {"text": message}
        
        if incident_data:
            payload["blocks"] = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Site DOWN" if incident_data.get("status") == "down" else "✅ Site RECOVERED"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Monitor:*\n{incident_data.get('monitor_name', 'Unknown')}"},
                        {"type": "mrkdwn", "text": f"*URL:*\n{incident_data.get('url', 'Unknown')}"}
                    ]
                }
            ]
            
            if incident_data.get("cause"):
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🧠 Cause:* {incident_data.get('cause')}"
                    }
                })
            
            if incident_data.get("status_code"):
                payload["blocks"].append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Status Code:* {incident_data.get('status_code')}"},
                        {"type": "mrkdwn", "text": f"*Severity:* {incident_data.get('severity', 'Unknown')}"}
                    ]
                })
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


async def send_discord_notification(webhook_url: str, message: str, incident_data: Optional[Dict] = None) -> bool:
    """
    Send notification to Discord via webhook.
    
    Args:
        webhook_url: Discord webhook URL
        message: Plain text message
        incident_data: Optional incident data for rich formatting
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not webhook_url:
            return False
        
        # Build rich embed if incident data is available
        color = 16711680 if incident_data and incident_data.get("status") == "down" else 5763719  # Red for down, Green for up
        
        payload = {
            "content": message,
            "embeds": []
        }
        
        if incident_data:
            embed = {
                "title": "🚨 Site DOWN" if incident_data.get("status") == "down" else "✅ Site RECOVERED",
                "color": color,
                "fields": [
                    {"name": "Monitor", "value": incident_data.get('monitor_name', 'Unknown'), "inline": True},
                    {"name": "URL", "value": incident_data.get('url', 'Unknown'), "inline": True}
                ]
            }
            
            if incident_data.get("cause"):
                embed["fields"].append({
                    "name": "🧠 Cause",
                    "value": incident_data.get("cause"),
                    "inline": False
                })
            
            if incident_data.get("status_code"):
                embed["fields"].extend([
                    {"name": "Status Code", "value": str(incident_data.get('status_code')), "inline": True},
                    {"name": "Severity", "value": incident_data.get('severity', 'Unknown'), "inline": True}
                ])
            
            payload["embeds"].append(embed)
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code in [200, 204]
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False


async def send_teams_notification(webhook_url: str, message: str, incident_data: Optional[Dict] = None) -> bool:
    """
    Send notification to Microsoft Teams via webhook.
    
    Args:
        webhook_url: Teams webhook URL
        message: Plain text message
        incident_data: Optional incident data for rich formatting
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not webhook_url:
            return False
        
        # Build Adaptive Card for Teams
        color = "#ff4444" if incident_data and incident_data.get("status") == "down" else "#44cc44"
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": message,
            "themeColor": color,
            "title": "🚨 Site DOWN" if incident_data and incident_data.get("status") == "down" else "✅ Site RECOVERED",
            "sections": [
                {
                    "facts": [
                        {"title": "Monitor", "value": incident_data.get('monitor_name', 'Unknown') if incident_data else 'Unknown'},
                        {"title": "URL", "value": incident_data.get('url', 'Unknown') if incident_data else 'Unknown'}
                    ]
                }
            ]
        }
        
        if incident_data and incident_data.get("cause"):
            payload["sections"][0]["facts"].append({
                "title": "🧠 Cause",
                "value": incident_data.get("cause")
            })
        
        if incident_data and incident_data.get("status_code"):
            payload["sections"][0]["facts"].extend([
                {"title": "Status Code", "value": str(incident_data.get('status_code'))},
                {"title": "Severity", "value": incident_data.get('severity', 'Unknown')}
            ])
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Teams notification: {e}")
        return False


async def send_pagerduty_notification(integration_key: str, incident_data: Dict) -> bool:
    """
    Create incident in PagerDuty via Events API v2.
    
    Args:
        integration_key: PagerDuty integration key
        incident_data: Incident data
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not integration_key:
            return False
        
        routing_key = integration_key
        event_action = "trigger"
        
        payload = {
            "routing_key": routing_key,
            "event_action": event_action,
            "payload": {
                "summary": f"Site DOWN: {incident_data.get('monitor_name', 'Unknown')}",
                "severity": "SEV1",
                "source": "TrezApp",
                "custom_details": {
                    "url": incident_data.get('url', 'Unknown'),
                    "status_code": incident_data.get('status_code', 'Unknown'),
                    "cause": incident_data.get('cause', 'Unknown')
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            )
            return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send PagerDuty notification: {e}")
        return False
