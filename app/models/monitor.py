from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True, index=True)  # Better Stack: group by service
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    interval = Column(Integer, default=600)  # seconds (10min default)
    timeout = Column(Integer, default=30)  # seconds
    is_active = Column(Boolean, default=True)
    last_status = Column(String, nullable=True)  # up, down, unknown
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Intelligence features
    health_score = Column(Integer, default=100)  # 0-100
    health_grade = Column(String, default="A+")  # A+, A, B+, B, C, D
    tags = Column(Text, nullable=True)  # Comma-separated: "production,critical,client-acme"
    estimated_revenue_per_hour = Column(Float, default=0)  # For money lost calculation
    is_flapping = Column(Boolean, default=False)  # Currently flapping
    is_degrading = Column(Boolean, default=False)  # Currently degrading
    site_dna = Column(JSON, nullable=True)  # Stores pattern analysis

    owner = relationship("User", back_populates="monitors")
    service = relationship("Service", back_populates="monitors")  # Better Stack
    checks = relationship("Check", back_populates="monitor", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="monitor", cascade="all, delete-orphan")
    escalation_rules = relationship("EscalationRule", back_populates="monitor", cascade="all, delete-orphan")
