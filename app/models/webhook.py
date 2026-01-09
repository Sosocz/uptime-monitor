"""
Webhook model - for future webhook management.

This model provides the structure for managing multiple webhooks per user,
with filtering capabilities and retry logic. Currently, the basic webhook
functionality uses User.webhook_url field.

Future implementation:
- Multiple webhooks per user
- Event filtering (see WEBHOOK_EVENTS below)
- Custom headers and authentication
- Retry configuration per webhook
- Webhook logs and debugging

WEBHOOK_EVENTS - Standard event types:
---------------------------------------

Monitor events:
  - monitor.created: New monitor added
  - monitor.updated: Monitor configuration changed
  - monitor.deleted: Monitor removed
  - monitor.paused: Monitor paused by user
  - monitor.resumed: Monitor resumed

Incident events:
  - incident.down: Site went down (critical)
  - incident.recovery: Site recovered from downtime
  - incident.degraded: Performance degraded (response time > threshold)

Check events:
  - check.failed: Single check failed (before incident triggered)
  - check.ssl_expiring: SSL certificate expiring soon (< 7 days)
  - check.ssl_expired: SSL certificate expired

Status page events:
  - statuspage.created: Status page created
  - statuspage.updated: Status page updated
  - statuspage.incident_posted: Manual incident posted on status page

User events:
  - user.upgraded: User upgraded to PRO
  - user.downgraded: User downgraded to FREE
  - user.limit_reached: User reached monitor limit

Payload format:
--------------
{
  "event": "incident.down",
  "timestamp": "2026-01-08T12:34:56Z",
  "monitor": {
    "id": 123,
    "name": "My Website",
    "url": "https://example.com"
  },
  "incident": {
    "id": 456,
    "type": "down",
    "started_at": "2026-01-08T12:34:56Z",
    "cause": "Connection timeout",
    "status_code": null,
    "error_message": "Connection timed out after 10s"
  },
  "user": {
    "id": 789,
    "email": "user@example.com"
  }
}
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Webhook(Base):
    """
    Webhook endpoint configuration.

    Future enhancement to replace User.webhook_url with more flexible system.
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Configuration
    name = Column(String, nullable=False)  # e.g., "Slack notifications"
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Event filtering
    events = Column(JSON, nullable=True)  # e.g., ["incident.down", "incident.recovery"]
    monitor_ids = Column(JSON, nullable=True)  # Limit to specific monitors (null = all)

    # Authentication
    auth_type = Column(String, nullable=True)  # "none", "bearer", "basic", "custom"
    auth_header = Column(String, nullable=True)  # e.g., "Authorization"
    auth_value = Column(Text, nullable=True)  # Encrypted token/credentials

    # Custom headers
    custom_headers = Column(JSON, nullable=True)  # e.g., {"X-Custom": "value"}

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)

    # Relationships
    owner = relationship("User", back_populates="webhooks")


class WebhookLog(Base):
    """
    Webhook delivery log for debugging.

    Tracks all webhook delivery attempts with full request/response data.
    """
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Request details
    event_type = Column(String, nullable=False)  # e.g., "incident.down"
    payload = Column(JSON, nullable=False)  # Full JSON payload sent

    # Response details
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Status
    status = Column(String, nullable=False)  # "pending", "sent", "failed"
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    webhook = relationship("Webhook")


# Add to User model (future):
# webhooks = relationship("Webhook", back_populates="owner", cascade="all, delete-orphan")
