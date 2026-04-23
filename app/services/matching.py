from uuid import UUID
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from app.models.user import User
from app.models.rts_schedule import RTSSchedule
from app.models.trip import Trip

async def calculate_required_arrival(train_departure_time):
    """Calculates arrival time 15 minutes before train departure."""
    return train_departure_time - timedelta(minutes=15)

async def create_carpool_match(
    session: AsyncSession, 
    rts_slot_id: UUID, 
    driver_id: UUID, 
    passenger_ids: List[UUID]
) -> Tuple[Trip, List[UUID]]:
    """
    Groups passengers with a driver, prioritizing the same social_cluster_tag.
    Returns the created Trip and a list of overflow passenger IDs.
    """
    # Fetch driver
    driver = await session.get(User, driver_id)
    if not driver:
        raise ValueError("Driver not found")
        
    # Fetch RTS schedule
    rts_schedule = await session.get(RTSSchedule, rts_slot_id)
    if not rts_schedule:
        raise ValueError("RTS Schedule not found")
        
    # Calculate arrival time (Departure - 15m)
    target_arrival = await calculate_required_arrival(rts_schedule.departure_time_jb)
    
    # Fetch available passengers
    if not passenger_ids:
        raise ValueError("No passengers provided")
        
    stmt = select(User).where(User.id.in_(passenger_ids))
    result = await session.execute(stmt)
    passengers = result.scalars().all()
    
    # Sort passengers: prioritize those with the same social_cluster_tag as the driver
    def sort_key(p: User):
        # We want the same cluster to be first (False is smaller than True, so we use `not` to sort True first)
        is_same_cluster = (p.social_cluster_tag == driver.social_cluster_tag)
        return (not is_same_cluster, str(p.id)) # Secondary sort by ID for stability
        
    sorted_passengers = sorted(passengers, key=sort_key)
    
    # Pick top 3
    matched_passengers = sorted_passengers[:3]
    overflow_passengers = sorted_passengers[3:]
    
    # Create the Trip
    new_trip = Trip(
        driver_id=driver.id,
        rts_slot_id=rts_schedule.id,
        scheduled_arrival_time=target_arrival,
        status="active"
    )
    # The ORM handles the junction table insertion automatically when appending to the relationship list
    new_trip.passengers = matched_passengers
    
    session.add(new_trip)
    await session.commit()
    await session.refresh(new_trip)
    
    overflow_ids = [p.id for p in overflow_passengers]
    return new_trip, overflow_ids
