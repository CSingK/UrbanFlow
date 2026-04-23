import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Float, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

class CarbonLedger(Base):
    __tablename__ = "carbon_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    category = Column(String, nullable=False)  # "CARPOOL" or "BUS_SHIFT"
    co2_saved_grams = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_utc_plus_8)

    # Relationships
    user = relationship("User")
    trip = relationship("Trip")
