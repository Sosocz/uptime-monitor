from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class RoleType(str, Enum):
    COMMANDER = "commander"
    DEPUTY = "deputy"
    LEAD = "lead"
    RESPONDER = "responder"


class IncidentRole(Base):
    """Roles assigned to incidents for clear ownership"""
    __tablename__ = "incident_roles"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Role
    role_type = Column(SQLEnum(RoleType), nullable=False)

    # Tracking
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="roles")
    user = relationship("User", foreign_keys=[user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
