import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class RTSSchedule(Base):
    __tablename__ = "rts_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    train_id = Column(String, nullable=False, index=True)
    departure_time_jb = Column(DateTime(timezone=True), nullable=False)
    arrival_time_sg = Column(DateTime(timezone=True), nullable=False)
