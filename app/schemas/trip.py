from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class MatchRequest(BaseModel):
    rts_slot_id: UUID
    driver_id: UUID
    passenger_ids: List[UUID]

class MatchResponse(BaseModel):
    trip_id: UUID
    driver_id: UUID
    matched_passenger_ids: List[UUID]
    scheduled_arrival_time: datetime
    message: str
