from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import secrets


class StatusPageSubscriber(Base):
    """Status page email/SMS subscriber (Better Stack)"""
    __tablename__ = "status_page_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    status_page_id = Column(Integer, ForeignKey("status_pages.id"), nullable=False, index=True)

    # Contact
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)

    # Preferences
    notify_incidents = Column(Boolean, default=True)
    notify_maintenance = Column(Boolean, default=True)
    notify_resolved = Column(Boolean, default=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Language preference
    language = Column(String, default="en")

    # Tracking
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    last_notification_at = Column(DateTime, nullable=True)

    # Unsubscribe
    is_active = Column(Boolean, default=True)
    unsubscribed_at = Column(DateTime, nullable=True)
    unsubscribe_token = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    status_page = relationship("StatusPage", back_populates="subscribers")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.verification_token:
            self.verification_token = secrets.token_urlsafe(32)
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
