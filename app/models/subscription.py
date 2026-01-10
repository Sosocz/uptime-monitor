from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"


class TelemetryBundle(str, Enum):
    NONE = "none"
    NANO = "nano"      # $30/month
    MICRO = "micro"    # $120/month
    MEGA = "mega"      # $250/month
    TERA = "tera"      # $500/month


class TelemetryRegion(str, Enum):
    US_EAST = "us_east"
    US_WEST = "us_west"
    GERMANY = "germany"
    SINGAPORE = "singapore"


class WarehousePlanType(str, Enum):
    STANDARD = "standard"  # Free
    TURBO = "turbo"        # $2000/month
    ULTRA = "ultra"        # $4000/month
    HYPER = "hyper"        # $6000/month


class Subscription(Base):
    """Complete Better Stack subscription model"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Stripe
    stripe_subscription_id = Column(String, nullable=True)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)

    # --- UPTIME MONITORING ---
    responder_count = Column(Integer, default=1)  # $34 base + $34 per additional
    monitor_packs = Column(Integer, default=0)    # $25 per 50 monitors

    # --- STATUS PAGES ---
    status_page_count = Column(Integer, default=1)  # 1 free, $15 per additional
    status_page_custom_css_count = Column(Integer, default=0)      # $15 each
    status_page_whitelabel_count = Column(Integer, default=0)      # $250 each
    status_page_password_count = Column(Integer, default=0)        # $50 each
    status_page_ip_restrict_count = Column(Integer, default=0)     # $250 each
    status_page_sso_count = Column(Integer, default=0)             # $250 each
    status_page_custom_email_count = Column(Integer, default=0)    # $250 each
    status_page_subscriber_packs = Column(Integer, default=0)      # $40 per 1000 subscribers

    # --- TELEMETRY BUNDLE ---
    telemetry_bundle = Column(SQLEnum(TelemetryBundle), default=TelemetryBundle.NONE)
    telemetry_region = Column(SQLEnum(TelemetryRegion), default=TelemetryRegion.GERMANY)

    # Usage tracking (current billing period)
    logs_gb_this_month = Column(Float, default=0.0)      # $0.10-0.15/GB overage
    traces_gb_this_month = Column(Float, default=0.0)    # $0.10-0.15/GB overage
    metrics_1b_this_month = Column(Float, default=0.0)   # $5/1B overage

    # --- ERROR TRACKING ---
    error_events_this_month = Column(Integer, default=0)  # $0.00005 per event after 100k

    # --- CALL ROUTING ---
    phone_number_count = Column(Integer, default=0)  # $250 per number/month

    # --- WAREHOUSE ---
    warehouse_plan = Column(SQLEnum(WarehousePlanType), default=WarehousePlanType.STANDARD)
    warehouse_object_storage_gb = Column(Float, default=0.0)  # $0.05/GB/month
    warehouse_nvme_storage_gb = Column(Float, default=0.0)    # $1.00/GB/month
    warehouse_custom_bucket = Column(Boolean, default=False)  # $250/month premium

    # Billing period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")


class UsageRecord(Base):
    """Historical usage tracking for billing audit"""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)

    # Period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Usage breakdown
    logs_ingested_gb = Column(Float, default=0.0)
    traces_ingested_gb = Column(Float, default=0.0)
    metrics_ingested_1b = Column(Float, default=0.0)
    error_events = Column(Integer, default=0)
    call_minutes = Column(Integer, default=0)
    warehouse_queries = Column(Integer, default=0)

    # Cost breakdown
    uptime_cost = Column(Float, default=0.0)
    status_pages_cost = Column(Float, default=0.0)
    telemetry_cost = Column(Float, default=0.0)
    errors_cost = Column(Float, default=0.0)
    call_routing_cost = Column(Float, default=0.0)
    warehouse_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription")
