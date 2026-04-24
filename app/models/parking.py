import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone, timedelta
from app.database import Base
from sqlalchemy.orm import relationship

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

class ParkingZone(Base):
    __tablename__ = "parking_zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name = Column(String, nullable=False, unique=True)
    zone_intensity = Column(String, default="NORMAL") # "NORMAL" or "CRITICAL"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class ParkingLog(Base):
    __tablename__ = "parking_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_plate = Column(String, nullable=False, index=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("parking_zones.id"), nullable=False)
    status = Column(String, default="grace_period")  # "grace_period", "warning", "illegal"
    first_seen = Column(DateTime(timezone=True), default=get_utc_plus_8)
    last_seen = Column(DateTime(timezone=True), default=get_utc_plus_8)
    
    zone = relationship("ParkingZone")
