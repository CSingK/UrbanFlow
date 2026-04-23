from pydantic import BaseModel
from typing import List
from uuid import UUID

class ImpactResponse(BaseModel):
    total_co2_saved_grams: float
    message: str

class LedgerEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    trip_id: UUID
    category: str
    co2_saved_grams: float
