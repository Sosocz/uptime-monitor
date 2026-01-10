from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class RotationType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class CoverRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OnCallSchedule(Base):
    """On-call schedule with rotation configuration"""
    __tablename__ = "oncall_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Ownership
    team_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Timezone
    timezone = Column(String, default="UTC", nullable=False)

    # Rotation configuration
    rotation_type = Column(SQLEnum(RotationType), default=RotationType.WEEKLY)
    rotation_start = Column(DateTime, nullable=False)
    rotation_interval_hours = Column(Integer, default=168)  # 1 week default

    # Rotation users (order matters)
    rotation_user_ids = Column(JSON, nullable=False)  # [user_id1, user_id2, ...]

    # Calendar sync
    google_calendar_id = Column(String, nullable=True)
    outlook_calendar_id = Column(String, nullable=True)
    sync_enabled = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("User", foreign_keys=[team_id])
    shifts = relationship("OnCallShift", back_populates="schedule", cascade="all, delete-orphan")


class OnCallShift(Base):
    """Individual on-call shift assignment"""
    __tablename__ = "oncall_shifts"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("oncall_schedules.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Time range
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)

    # Override
    is_override = Column(Boolean, default=False)
    overridden_shift_id = Column(Integer, ForeignKey("oncall_shifts.id"), nullable=True)
    override_reason = Column(String, nullable=True)
    overridden_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    schedule = relationship("OnCallSchedule", back_populates="shifts")
    user = relationship("User", foreign_keys=[user_id])
    overridden_by = relationship("User", foreign_keys=[overridden_by_id])


class CoverRequest(Base):
    """Request for someone to cover an on-call shift"""
    __tablename__ = "cover_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("oncall_shifts.id"), nullable=False, index=True)

    # Request details
    reason = Column(String, nullable=True)
    potential_covers = Column(JSON, nullable=True)  # [user_id1, user_id2, ...]

    # Response
    status = Column(SQLEnum(CoverRequestStatus), default=CoverRequestStatus.PENDING)
    accepted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    response_message = Column(String, nullable=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    shift = relationship("OnCallShift")
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])
