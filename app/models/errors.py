from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON, Enum as SQLEnum, Boolean, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class ErrorLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ErrorGroupStatus(str, Enum):
    UNRESOLVED = "unresolved"
    IGNORED = "ignored"
    RESOLVED = "resolved"


class ErrorProject(Base):
    """Error tracking project (Sentry SDK compatible)"""
    __tablename__ = "error_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Sentry compatibility
    dsn = Column(String, nullable=False, unique=True)  # Data Source Name
    platform = Column(String, nullable=True)  # python, javascript, go, etc.

    # API keys
    public_key = Column(String, nullable=False, unique=True, index=True)
    secret_key = Column(String, nullable=False)
    project_key = Column(String, nullable=False, unique=True)

    # Usage & Quota
    events_this_month = Column(Integer, default=0)
    events_quota = Column(Integer, default=100000)  # Free tier: 100k events

    # Settings
    sample_rate = Column(Float, default=1.0)  # 0.0 to 1.0
    filter_localhost = Column(Boolean, default=True)

    # Integrations
    linear_api_key = Column(String, nullable=True)
    jira_url = Column(String, nullable=True)
    jira_api_token = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    error_groups = relationship("ErrorGroup", back_populates="project", cascade="all, delete-orphan")
    error_events = relationship("ErrorEvent", back_populates="project", cascade="all, delete-orphan")


class ErrorGroup(Base):
    """Grouped errors by fingerprint"""
    __tablename__ = "error_groups"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("error_projects.id"), nullable=False, index=True)
    fingerprint = Column(String, nullable=False, index=True)  # Hash for grouping

    # Summary
    title = Column(String, nullable=False)
    exception_type = Column(String, nullable=True)
    exception_value = Column(Text, nullable=True)

    # Stats
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)
    event_count = Column(Integer, default=0)
    user_count = Column(Integer, default=0)  # Unique users affected

    # Status
    status = Column(SQLEnum(ErrorGroupStatus), default=ErrorGroupStatus.UNRESOLVED, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    snoozed_until = Column(DateTime, nullable=True)

    # AI features
    bugfix_prompt = Column(Text, nullable=True)  # AI-generated fix suggestion

    # Integrations
    linear_issue_id = Column(String, nullable=True)
    jira_issue_key = Column(String, nullable=True)

    # Release tracking
    resolved_in_release = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("ErrorProject", back_populates="error_groups")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    events = relationship("ErrorEvent", back_populates="error_group", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_project_fingerprint', 'project_id', 'fingerprint', unique=True),
    )


class ErrorEvent(Base):
    """Individual error event (Sentry protocol compatible)"""
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("error_projects.id"), nullable=False, index=True)
    error_group_id = Column(Integer, ForeignKey("error_groups.id"), nullable=False, index=True)

    # Event identification
    event_id = Column(String, nullable=False, unique=True, index=True)  # UUID from Sentry SDK
    fingerprint = Column(String, nullable=False, index=True)

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Error details
    level = Column(SQLEnum(ErrorLevel), default=ErrorLevel.ERROR)
    message = Column(Text, nullable=True)
    exception_type = Column(String, nullable=True)
    exception_value = Column(Text, nullable=True)
    stacktrace = Column(JSON, nullable=True)  # Full stacktrace

    # Context
    user_id_context = Column(String, nullable=True)  # User ID from app context
    user_email = Column(String, nullable=True)
    user_username = Column(String, nullable=True)

    # Environment
    release = Column(String, nullable=True, index=True)
    environment = Column(String, nullable=True, index=True)  # production, staging, etc.
    server_name = Column(String, nullable=True)

    # Request context
    request_url = Column(Text, nullable=True)
    request_method = Column(String, nullable=True)
    request_headers = Column(JSON, nullable=True)

    # Device/Browser
    platform = Column(String, nullable=True)  # python, javascript, etc.
    sdk_name = Column(String, nullable=True)
    sdk_version = Column(String, nullable=True)

    # Tags & Extra
    tags = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)

    # Breadcrumbs (user actions leading to error)
    breadcrumbs = Column(JSON, nullable=True)

    # AI features
    bugfix_prompt_generated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("ErrorProject", back_populates="error_events")
    error_group = relationship("ErrorGroup", back_populates="events")

    __table_args__ = (
        Index('idx_project_timestamp', 'project_id', 'timestamp'),
        Index('idx_group_timestamp', 'error_group_id', 'timestamp'),
    )
