import uuid
from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class BusStation(Base):
    __tablename__ = "bus_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    current_queue_count = Column(Integer, default=0)
    bus_capacity = Column(Integer, default=40)
    current_bus_occupancy = Column(Integer, default=0)
    predicted_occupancy = Column(String, default="Data Pending")
    last_updated = Column(DateTime(timezone=True), nullable=True)
