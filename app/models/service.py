from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Service(Base):
    """Service catalog - groups monitors under business services"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)

    # Ownership
    team_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Using user as team for now

    # Escalation
    escalation_policy_id = Column(Integer, ForeignKey("escalation_rules.id"), nullable=True)

    # Documentation
    runbook_url = Column(String, nullable=True)
    documentation_url = Column(String, nullable=True)

    # Metadata
    service_metadata = Column(JSON, nullable=True)  # Flexible key-value pairs
    tags = Column(JSON, nullable=True)  # Array of tags

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("User", foreign_keys=[team_id])
    incidents = relationship("Incident", back_populates="service")
    monitors = relationship("Monitor", back_populates="service")
