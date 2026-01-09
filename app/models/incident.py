from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    incident_type = Column(String, nullable=False)  # down, recovery
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Incident metadata
    duration_seconds = Column(Integer, nullable=True)  # Calculated when resolved
    failed_checks_count = Column(Integer, default=0)
    status_code = Column(Integer, nullable=True)  # HTTP status code that caused the incident
    error_message = Column(Text, nullable=True)  # Error message from the first failed check
    cause = Column(String, nullable=True)  # Human-readable cause (e.g., "HTTP 500", "Timeout", "Connection refused")

    # Intelligent incident analysis
    intelligent_cause = Column(Text, nullable=True)  # Advanced "why it went down" analysis
    severity = Column(String, default="warning")  # critical, warning, info
    analysis_data = Column(JSON, nullable=True)  # Full analysis details
    recommendations = Column(JSON, nullable=True)  # Array of recommendations
    minutes_lost = Column(Integer, default=0)
    money_lost = Column(Integer, default=0)  # In euros

    # Notification tracking
    notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)

    monitor = relationship("Monitor", back_populates="incidents")
