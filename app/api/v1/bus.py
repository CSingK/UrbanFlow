from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.bus_station import BusStation
from app.models.station_analysis import StationAnalysis
from app.schemas.bus import UpdateFeedRequest, BusStatusResponse
from app.services.vision_service import analyze_station_crowd
from app.services.bigquery_service import bq_service

router = APIRouter()

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

@router.post("/{station_id}/analyze")
async def analyze_station(
    station_id: UUID, 
    file: UploadFile = File(...), 
    session: AsyncSession = Depends(get_db)
):
    """
    SENSE: High-performance endpoint for multimodal CCTV analysis.
    REASON: Calls Gemini 2.5 Flash via Vision Service.
    EXECUTE: Updates Neon PostgreSQL with crowd metrics and boarding intent.
    """
    station = await session.get(BusStation, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    try:
        # Task 2: Read bytes and analyze
        image_data = await file.read()
        analysis_result = await analyze_station_crowd(image_data)
        
        people_count = analysis_result.get("count", 0)
        boarding_prob = analysis_result.get("boarding_probability", 0.0)

        # Task 2: Save to StationAnalysis
        analysis_record = StationAnalysis(
            station_id=station_id,
            people_count=people_count,
            boarding_probability=boarding_prob
        )
        
        # Task 2: Update BusStation occupancy
        # As per architect requirements, we update real-time metrics based on AI vision
        station.current_bus_occupancy = people_count
        station.last_updated = get_utc_plus_8()

        session.add(analysis_record)
        session.add(station)
        
        await session.commit()
        await session.refresh(analysis_record)
        
        return {
            "id": str(analysis_record.id),
            "station_id": str(station_id),
            "people_count": people_count,
            "boarding_probability": boarding_prob,
            "timestamp": analysis_record.timestamp.isoformat()
        }

    except Exception as e:
        await session.rollback()
        print(f"--- [FASTAPI ERROR] Analysis failed for {station_id}: {e} ---")
        raise HTTPException(status_code=500, detail="Multimodal analysis or database write failed.")

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
    
    # REASON: Predict Probability of Boarding via BigQuery ML
    pob_score = bq_service.predict_pob(
        queue_count=queue_count, 
        bus_occupancy=bus_occupancy, 
        station_id=str(station_id)
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
