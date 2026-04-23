from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.parking import DetectionRequest, ParkingLogResponse, RerouteResponse, LeaveRequest, LeaveResponse
from app.services.parking_service import detect_illegal_parking, get_green_zone_reroute, register_departure

router = APIRouter()

@router.post("/detect", response_model=ParkingLogResponse)
async def detect_parking(request: DetectionRequest, session: AsyncSession = Depends(get_db)):
    """
    Simulates identifying a vehicle outside a 'Legal Box'. 
    Enforces dynamic grace periods and handles 2-hour Stale Log resets.
    """
    try:
        log = await detect_illegal_parking(session, request.license_plate, str(request.zone_id))
        return ParkingLogResponse(
            id=log.id,
            license_plate=log.license_plate,
            zone_id=log.zone_id,
            status=log.status,
            first_seen=log.first_seen,
            last_seen=log.last_seen
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/leave", response_model=LeaveResponse)
async def leave_parking(request: LeaveRequest, session: AsyncSession = Depends(get_db)):
    """
    Registers departure, calculates duration, and applies Carbon Ledger impacts (Reward/Penalty).
    """
    result = await register_departure(session, request.license_plate, str(request.zone_id))
    return LeaveResponse(**result)

@router.get("/reroute", response_model=RerouteResponse)
async def reroute(lat: float, lng: float):
    """
    Uses Google Maps Platform logic (mocked) to suggest the nearest available 'Green Zone'.
    """
    reroute_data = await get_green_zone_reroute((lat, lng))
    return RerouteResponse(
        zone_name=reroute_data["zone_name"],
        coordinates=list(reroute_data["coordinates"]),
        available_spots=reroute_data["available_spots"]
    )
