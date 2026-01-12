from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, Enum):
    SEV1 = "SEV1"  # Critical
    SEV2 = "SEV2"  # High
    SEV3 = "SEV3"  # Medium
    SEV4 = "SEV4"  # Low


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    incident_type = Column(String, nullable=False)  # down, recovery
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Better Stack: Status tracking
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Better Stack: Severity
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.SEV3)

    # Better Stack: Service - DISABLED until migration
    # service_id = Column(Integer, ForeignKey("services.id"), nullable=True, index=True)

    # Incident metadata
    title = Column(String, nullable=True)  # Better Stack: custom title
    duration_seconds = Column(Integer, nullable=True)  # Calculated when resolved
    failed_checks_count = Column(Integer, default=0)
    status_code = Column(Integer, nullable=True)  # HTTP status code that caused the incident
    error_message = Column(Text, nullable=True)  # Error message from the first failed check
    cause = Column(String, nullable=True)  # Human-readable cause (e.g., "HTTP 500", "Timeout", "Connection refused")

    # Intelligent incident analysis
    intelligent_cause = Column(Text, nullable=True)  # Advanced "why it went down" analysis
    analysis_data = Column(JSON, nullable=True)  # Full analysis details
    recommendations = Column(JSON, nullable=True)  # Array of recommendations
    minutes_lost = Column(Integer, default=0)
    money_lost = Column(Integer, default=0)  # In euros

    # Better Stack: MTTA/MTTR metrics
    time_to_acknowledge = Column(Integer, nullable=True)  # Seconds from start to acknowledge
    time_to_resolve = Column(Integer, nullable=True)  # Seconds from start to resolve

    # Better Stack: AI Features
    root_cause_analysis = Column(JSON, nullable=True)  # AI-generated root cause
    ai_postmortem = Column(Text, nullable=True)  # AI-generated post-mortem
    ai_postmortem_generated_at = Column(DateTime, nullable=True)

    # Better Stack: Slack Integration
    slack_channel_id = Column(String, nullable=True)
    slack_thread_ts = Column(String, nullable=True)  # Thread timestamp
    slack_message_ts = Column(String, nullable=True)  # Main message timestamp

    # Better Stack: MS Teams Integration
    teams_channel_id = Column(String, nullable=True)
    teams_message_id = Column(String, nullable=True)

    # Better Stack: Timeline events
    timeline_events = Column(JSON, nullable=True)  # [{timestamp, type, user_id, action, details}]

    # Better Stack: Escalation
    escalation_level = Column(Integer, default=0)
    escalation_policy_id = Column(Integer, ForeignKey("escalation_rules.id"), nullable=True)

    # Better Stack: On-call responder
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Notification tracking
    notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)

    # Relationships
    monitor = relationship("Monitor", back_populates="incidents")
    # service = relationship("Service", back_populates="incidents")  # DISABLED until migration
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    responder = relationship("User", foreign_keys=[responder_id])
    roles = relationship("IncidentRole", back_populates="incident", cascade="all, delete-orphan")


    def normalize_incident_status(value):
        """Normalize status value for database."""
        if value is None:
            return None
        if isinstance(value, IncidentStatus):
            return value.value
        # Return the value directly (enums are already correct)
        return str(value)

    def normalize_incident_status(value):
        """Normalize status value for database."""
        if value is None:
            return None
        if isinstance(value, IncidentStatus):
            return value.value
        # Return value directly (enums are already correct)
        return str(value)
