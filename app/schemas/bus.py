from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class UpdateFeedRequest(BaseModel):
    image_path: str

class BusStatusResponse(BaseModel):
    station_id: UUID
    station_name: str
    current_queue_count: int
    current_bus_occupancy: int
    bus_capacity: int
    predicted_occupancy: str
    last_updated: Optional[datetime]
