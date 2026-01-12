from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    auth_user_id = Column(String, unique=True, index=True, nullable=True)
    plan = Column(String, default="FREE")  # FREE or PAID
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)  # Webhook endpoint for notifications
    
    # Integration webhooks
    slack_webhook_url = Column(String, nullable=True)
    discord_webhook_url = Column(String, nullable=True)
    teams_webhook_url = Column(String, nullable=True)
    pagerduty_integration_key = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Account settings
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    avatar_url = Column(String, nullable=True)

    # Alerts settings
    alerts_enabled = Column(Boolean, default=True)
    alerts_paused_from = Column(DateTime, nullable=True)
    alerts_paused_until = Column(DateTime, nullable=True)

    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # google, twitter, github
    oauth_id = Column(String, nullable=True)  # Provider's user ID

    # Password reset fields
    password_reset_token = Column(String, nullable=True, index=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    # Onboarding tracking
    onboarding_completed = Column(Boolean, default=False)
    onboarding_email_j1_sent = Column(Boolean, default=False)
    onboarding_email_j3_sent = Column(Boolean, default=False)
    
    monitors = relationship("Monitor", back_populates="owner", cascade="all, delete-orphan")
    status_pages = relationship("StatusPage", back_populates="owner", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
