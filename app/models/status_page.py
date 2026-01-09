from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import secrets


class StatusPage(Base):
    """
    Public status page for displaying monitor uptime.

    Users can create a public status page to share with their customers.
    """
    __tablename__ = "status_pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Page identification
    slug = Column(String, unique=True, nullable=False, index=True)  # e.g., "acme-services"
    name = Column(String, nullable=False)  # e.g., "ACME Services Status"

    # Branding
    logo_url = Column(String, nullable=True)
    custom_domain = Column(String, nullable=True)  # e.g., "status.acme.com"

    # Access control
    is_public = Column(Boolean, default=True)  # False requires access_token
    access_token = Column(String, nullable=True)  # For private pages

    # Customization
    header_text = Column(Text, nullable=True)  # Custom header message
    brand_color = Column(String, nullable=True, default="#3b82f6")  # Hex color

    # Settings
    show_uptime_percentage = Column(Boolean, default=True)
    show_response_time = Column(Boolean, default=True)
    show_incident_history = Column(Boolean, default=True)
    show_powered_by = Column(Boolean, default=True)  # "Powered by TrezApp" badge (can be disabled for PAID users)

    # Relationships
    owner = relationship("User", back_populates="status_pages")
    monitors = relationship("StatusPageMonitor", back_populates="status_page", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug:
            self.slug = secrets.token_urlsafe(8)
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(32)


class StatusPageMonitor(Base):
    """
    Monitors displayed on a status page.
    """
    __tablename__ = "status_page_monitors"

    id = Column(Integer, primary_key=True, index=True)
    status_page_id = Column(Integer, ForeignKey("status_pages.id"), nullable=False, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)

    # Display order
    position = Column(Integer, default=0)

    # Relationships
    status_page = relationship("StatusPage", back_populates="monitors")
    monitor = relationship("Monitor")
