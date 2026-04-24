import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

class StationAnalysis(Base):
    __tablename__ = "station_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(UUID(as_uuid=True), ForeignKey("bus_stations.id"), nullable=False)
    people_count = Column(Integer, nullable=False)
    boarding_probability = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_utc_plus_8)
