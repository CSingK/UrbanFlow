from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.impact import ImpactResponse, LedgerEntryResponse
from app.models.carbon_ledger import CarbonLedger
from app.services.carbon_ledger import calculate_impact

router = APIRouter()

@router.post("/calculate/{trip_id}", response_model=List[LedgerEntryResponse])
async def trigger_calculation(trip_id: UUID, session: AsyncSession = Depends(get_db)):
    """
    Triggers the math formula to calculate avoided emissions and inserts double-entry records
    into the Carbon Ledger for the driver and each passenger.
    """
    try:
        ledgers = await calculate_impact(session, trip_id)
        return [
            LedgerEntryResponse(
                id=l.id,
                user_id=l.user_id,
                trip_id=l.trip_id,
                category=l.category,
                co2_saved_grams=l.co2_saved_grams
            ) for l in ledgers
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/total", response_model=ImpactResponse)
async def get_total_impact(session: AsyncSession = Depends(get_db)):
    """
    Sums up all co2_saved_grams from the National Carbon Ledger to show the grand total savings.
    """
    stmt = select(func.sum(CarbonLedger.co2_saved_grams))
    result = await session.execute(stmt)
    total = result.scalar() or 0.0
    
    return ImpactResponse(
        total_co2_saved_grams=total,
        message="This is the grand total of CO2 emissions avoided by UrbanFlow."
    )
