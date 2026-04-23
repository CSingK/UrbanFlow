from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models.parking import ParkingLog, ParkingZone
from app.models.user import User
from app.models.carbon_ledger import CarbonLedger

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

async def detect_illegal_parking(session: AsyncSession, license_plate: str, zone_id: str) -> ParkingLog:
    # Get Zone
    zone = await session.get(ParkingZone, zone_id)
    if not zone:
        raise ValueError("Zone not found")
        
    grace_period = 180 if zone.zone_intensity == "CRITICAL" else 300
    nudge_threshold = grace_period - 60 # e.g. 120s or 240s
    
    stmt = select(ParkingLog).where(
        ParkingLog.license_plate == license_plate,
        ParkingLog.zone_id == zone_id
    )
    result = await session.execute(stmt)
    log = result.scalars().first()
    
    current_time = get_utc_plus_8()
    
    if log:
        # Check for Stale Log (> 2 hours)
        time_since_first_seen = (current_time - log.first_seen).total_seconds()
        if time_since_first_seen > 7200: # 2 hours
            await session.delete(log)
            await session.commit()
            log = None # Proceed to create a new log entry
        else:
            log.last_seen = current_time
            if time_since_first_seen > grace_period:
                log.status = "illegal"
            elif time_since_first_seen > nudge_threshold:
                log.status = "warning"
            else:
                log.status = "grace_period"
            
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    if not log:
        new_log = ParkingLog(
            license_plate=license_plate,
            zone_id=zone_id,
            status="grace_period",
            first_seen=current_time,
            last_seen=current_time
        )
        session.add(new_log)
        await session.commit()
        await session.refresh(new_log)
        return new_log

async def register_departure(session: AsyncSession, license_plate: str, zone_id: str) -> dict:
    stmt = select(ParkingLog).where(
        ParkingLog.license_plate == license_plate,
        ParkingLog.zone_id == zone_id
    )
    result = await session.execute(stmt)
    log = result.scalars().first()
    
    if not log:
        return {"status": "ignored", "duration_seconds": 0, "message": "No active parking log found."}
        
    zone = await session.get(ParkingZone, zone_id)
    grace_period = 180 if zone and zone.zone_intensity == "CRITICAL" else 300
    
    current_time = get_utc_plus_8()
    duration = (current_time - log.first_seen).total_seconds()
    
    # Try to find user to apply Carbon Ledger impacts
    user_stmt = select(User).where(User.license_plate == license_plate)
    user_result = await session.execute(user_stmt)
    user = user_result.scalars().first()
    
    impact_message = "Car left."
    if user:
        if duration <= grace_period:
            # Reward
            entry = CarbonLedger(
                user_id=user.id,
                category="CONGESTION_AVOIDED",
                co2_saved_grams=50.0
            )
            session.add(entry)
            impact_message = "Congestion Avoided reward applied: +50g CO2."
        else:
            # Penalty
            overstay_minutes = (duration - grace_period) / 60.0
            penalty = -10.0 * overstay_minutes
            entry = CarbonLedger(
                user_id=user.id,
                category="IDLING_PENALTY",
                co2_saved_grams=penalty
            )
            session.add(entry)
            impact_message = f"Idling Penalty applied: {penalty:.2f}g CO2."
            
    # Remove the log
    await session.delete(log)
    await session.commit()
    
    return {"status": "departed", "duration_seconds": duration, "message": impact_message}

async def get_green_zone_reroute(current_coords: tuple) -> dict:
    """Mocks Google Maps Platform logic for nearest Green Zone"""
    return {
        "zone_name": "JB Sentral Park & Ride",
        "coordinates": (1.4630, 103.7640),
        "available_spots": 42
    }
