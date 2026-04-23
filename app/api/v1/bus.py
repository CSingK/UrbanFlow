from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.bus_station import BusStation
from app.schemas.bus import UpdateFeedRequest, BusStatusResponse
from app.services.vision_service import process_station_feed
from app.services.bus_intelligence import calculate_pob

router = APIRouter()

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

@router.get("/status/{station_id}", response_model=BusStatusResponse)
async def get_station_status(station_id: UUID, session: AsyncSession = Depends(get_db)):
    """
    Returns the station's current queue count and the PoB score.
    """
    station = await session.get(BusStation, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
        
    return BusStatusResponse(
        station_id=station.id,
        station_name=station.station_name,
        current_queue_count=station.current_queue_count,
        current_bus_occupancy=station.current_bus_occupancy,
        bus_capacity=station.bus_capacity,
        predicted_occupancy=station.predicted_occupancy,
        last_updated=station.last_updated
    )

@router.post("/update-feed/{station_id}", response_model=BusStatusResponse)
async def update_station_feed(station_id: UUID, request: UpdateFeedRequest, session: AsyncSession = Depends(get_db)):
    """
    'Uploads' an image path to trigger the AI counting logic, calculates PoB,
    and updates the station status.
    """
    station = await session.get(BusStation, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
        
    # Simulate Vision AI
    queue_count, bus_occupancy = await process_station_feed(station_id, request.image_path)
    
    # Calculate Probability of Boarding
    pob_score = calculate_pob(
        queue_count=queue_count, 
        bus_occupancy=bus_occupancy, 
        bus_capacity=station.bus_capacity
    )
    
    # Update Database
    station.current_queue_count = queue_count
    station.current_bus_occupancy = bus_occupancy
    station.predicted_occupancy = pob_score
    station.last_updated = get_utc_plus_8()
    
    session.add(station)
    await session.commit()
    await session.refresh(station)
    
    return BusStatusResponse(
        station_id=station.id,
        station_name=station.station_name,
        current_queue_count=station.current_queue_count,
        current_bus_occupancy=station.current_bus_occupancy,
        bus_capacity=station.bus_capacity,
        predicted_occupancy=station.predicted_occupancy,
        last_updated=station.last_updated
    )
