from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    status = Column(String, nullable=False)  # up, down, timeout, error
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)  # milliseconds
    error_message = Column(String, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional metadata
    ip_address = Column(String, nullable=True)
    server = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    ssl_expires_at = Column(DateTime, nullable=True)
    response_headers = Column(Text, nullable=True)  # JSON string

    monitor = relationship("Monitor", back_populates="checks")
