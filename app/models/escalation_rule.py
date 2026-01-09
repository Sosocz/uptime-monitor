from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class EscalationRule(Base):
    """
    Escalation rules for monitors.

    If a monitor is down for longer than threshold_minutes, send additional
    notifications on escalation_channels.
    """
    __tablename__ = "escalation_rules"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)

    # Escalation threshold
    threshold_minutes = Column(Integer, nullable=False, default=10)  # Escalate after 10 minutes down

    # Channels to notify on escalation (comma-separated: "email,telegram,webhook")
    escalation_channels = Column(String, nullable=False, default="telegram")

    # Whether this rule is active
    is_active = Column(Boolean, default=True)

    # Whether escalation has already been triggered for current incident
    escalated = Column(Boolean, default=False)

    monitor = relationship("Monitor", back_populates="escalation_rules")
