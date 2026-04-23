from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.trip import Trip
from app.models.carbon_ledger import CarbonLedger

async def calculate_impact(session: AsyncSession, trip_id: UUID):
    # Fetch trip with passengers
    stmt = select(Trip).options(selectinload(Trip.passengers)).where(Trip.id == trip_id)
    result = await session.execute(stmt)
    trip = result.scalars().first()
    
    if not trip:
        raise ValueError("Trip not found")
        
    occupants_count = 1 + len(trip.passengers)
    distance = trip.distance_km
    
    if occupants_count < 1:
        occupants_count = 1 # Safety net
        
    if trip.trip_type == "carpool":
        # Avoided Emissions Formula: (Distance * 170g) * (Occupants - 1)
        total_co2_saved = (distance * 170.0) * (occupants_count - 1)
        category = "CARPOOL"
    elif trip.trip_type == "bus":
        # 1.2kg per person per 10km -> 120g per km per person
        total_co2_saved = (120.0 * distance) * occupants_count
        category = "BUS_SHIFT"
    else:
        total_co2_saved = 0
        category = "UNKNOWN"
        
    # Double-entry logic: spread savings evenly across driver and passengers
    savings_per_person = total_co2_saved / occupants_count if occupants_count > 0 else 0
    
    # List of all users in the trip
    users_in_trip = [trip.driver_id] + [p.id for p in trip.passengers]
    
    ledgers = []
    for uid in users_in_trip:
        ledger_entry = CarbonLedger(
            user_id=uid,
            trip_id=trip.id,
            category=category,
            co2_saved_grams=savings_per_person
        )
        session.add(ledger_entry)
        ledgers.append(ledger_entry)
        
    await session.commit()
    for ledger in ledgers:
        await session.refresh(ledger)
    return ledgers
