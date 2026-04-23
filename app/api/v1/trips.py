from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.trip import MatchRequest, MatchResponse
from app.services.matching import create_carpool_match

router = APIRouter()

# FUTURE-PROOFING: Currently we accept a manual list of passenger IDs to test the math and cluster priority.
# In the future, this will transition to Autonomous Matching from a pool of active requests 
# (e.g., dynamically querying users who have requested rides in the same time window).
@router.post("/match", response_model=MatchResponse)
async def match_carpool(request: MatchRequest, session: AsyncSession = Depends(get_db)):
    try:
        trip, overflow_ids = await create_carpool_match(
            session=session,
            rts_slot_id=request.rts_slot_id,
            driver_id=request.driver_id,
            passenger_ids=request.passenger_ids
        )
        
        overflow_count = len(overflow_ids)
        if overflow_count > 0:
            msg = f"Carpool full. 3 passengers matched, {overflow_count} passengers moved to the next available queue."
        else:
            msg = "Carpool match successful. All passengers accommodated."
            
        return MatchResponse(
            trip_id=trip.id,
            driver_id=trip.driver_id,
            matched_passenger_ids=[p.id for p in trip.passengers],
            scheduled_arrival_time=trip.scheduled_arrival_time,
            message=msg
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
