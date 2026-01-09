from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)

    # Notification details
    channel = Column(String, nullable=False)  # email, telegram, webhook, slack
    recipient = Column(String, nullable=False)  # email address, chat_id, webhook URL

    # Delivery tracking
    status = Column(String, nullable=False, default="pending")  # pending, sent, failed, retrying, dlq
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    incident = relationship("Incident")
    user = relationship("User")
    monitor = relationship("Monitor")

    # Composite index for deduplication queries
    __table_args__ = (
        Index('idx_notification_dedup', 'incident_id', 'user_id', 'channel', 'created_at'),
        Index('idx_notification_status', 'status', 'created_at'),
    )
