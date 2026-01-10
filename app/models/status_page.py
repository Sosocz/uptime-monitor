from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base
import secrets


class SSOProvider(str, Enum):
    GOOGLE = "google"
    AZURE = "azure"
    OKTA = "okta"


class StatusPage(Base):
    """
    Public status page for displaying monitor uptime.

    Users can create a public status page to share with their customers.
    Better Stack compatible with all advanced features.
    """
    __tablename__ = "status_pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Page identification
    slug = Column(String, unique=True, nullable=False, index=True)  # e.g., "acme-services"
    subdomain = Column(String, unique=True, nullable=True, index=True)  # Better Stack: betterstack subdomain
    name = Column(String, nullable=False)  # e.g., "ACME Services Status"

    # Branding
    logo_url = Column(String, nullable=True)
    custom_domain = Column(String, nullable=True)  # e.g., "status.acme.com"

    # Better Stack: Custom CSS/JS ($15/page)
    custom_css = Column(Text, nullable=True)
    custom_js = Column(Text, nullable=True)
    has_custom_styling = Column(Boolean, default=False)  # Paid feature flag

    # Better Stack: White-label ($250/page)
    is_white_label = Column(Boolean, default=False)
    footer_text = Column(Text, nullable=True)  # Custom footer when white-labeled

    # Access control
    is_public = Column(Boolean, default=True)  # False requires access_token

    # Better Stack: Password protection ($50/page)
    is_password_protected = Column(Boolean, default=False)
    password_hash = Column(String, nullable=True)
    access_token = Column(String, nullable=True)  # For private pages

    # Better Stack: IP restrictions ($250/page)
    is_ip_restricted = Column(Boolean, default=False)
    ip_whitelist = Column(JSON, nullable=True)  # ["1.2.3.4", "5.6.7.0/24"]

    # Better Stack: SSO ($250/page)
    sso_enabled = Column(Boolean, default=False)
    sso_provider = Column(SQLEnum(SSOProvider), nullable=True)
    sso_client_id = Column(String, nullable=True)
    sso_client_secret = Column(String, nullable=True)
    sso_tenant_id = Column(String, nullable=True)  # For Azure

    # Customization
    header_text = Column(Text, nullable=True)  # Custom header message
    brand_color = Column(String, nullable=True, default="#3b82f6")  # Hex color

    # Better Stack: Custom email domain ($250/page)
    custom_email_domain = Column(String, nullable=True)  # e.g., "status@acme.com"
    custom_email_enabled = Column(Boolean, default=False)

    # Better Stack: Analytics
    google_analytics_id = Column(String, nullable=True)
    mixpanel_token = Column(String, nullable=True)
    intercom_app_id = Column(String, nullable=True)

    # Better Stack: Multi-language
    languages = Column(JSON, nullable=True)  # ["en", "fr", "de"]
    default_language = Column(String, default="en")

    # Better Stack: Subscribers (1000 free, $40 per 1000)
    subscriber_quota = Column(Integer, default=1000)
    subscriber_count = Column(Integer, default=0)

    # Settings
    show_uptime_percentage = Column(Boolean, default=True)
    show_response_time = Column(Boolean, default=True)
    show_incident_history = Column(Boolean, default=True)
    show_powered_by = Column(Boolean, default=True)  # Disabled when white-label

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="status_pages")
    monitors = relationship("StatusPageMonitor", back_populates="status_page", cascade="all, delete-orphan")
    subscribers = relationship("StatusPageSubscriber", back_populates="status_page", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug:
            self.slug = secrets.token_urlsafe(8)
        if not self.subdomain:
            self.subdomain = self.slug
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
