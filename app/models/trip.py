import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Table, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

# Junction table for the many-to-many relationship between Trips and Users (passengers)
trip_passengers = Table(
    "trip_passengers",
    Base.metadata,
    Column("trip_id", UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rts_slot_id = Column(UUID(as_uuid=True), ForeignKey("rts_schedules.id"), nullable=True)
    distance_km = Column(Float, default=0.0)
    scheduled_arrival_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")  # e.g., "pending", "active", "completed", "cancelled"
    trip_type = Column(String, default="carpool")  # e.g., "carpool", "bus"

    # Relationships
    driver = relationship("User", foreign_keys=[driver_id])
    rts_slot = relationship("RTSSchedule")
    passengers = relationship("User", secondary=trip_passengers, backref="passenger_trips")
