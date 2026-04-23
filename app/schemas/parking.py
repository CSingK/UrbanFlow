from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class DetectionRequest(BaseModel):
    image_path: str
    zone_id: UUID
    license_plate: str # Simulating the extracted license plate

class ParkingLogResponse(BaseModel):
    id: UUID
    license_plate: str
    zone_id: UUID
    status: str
    first_seen: datetime
    last_seen: datetime

class RerouteResponse(BaseModel):
    zone_name: str
    coordinates: List[float]
    available_spots: int

class LeaveRequest(BaseModel):
    zone_id: UUID
    license_plate: str

class LeaveResponse(BaseModel):
    status: str
    duration_seconds: float
    message: str
