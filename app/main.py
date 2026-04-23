from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
import app.models  # Imports all models so they are registered with Base
from app.api.v1 import trips, bus, parking, impact

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create db tables
    async with engine.begin() as conn:
        # Note: In production, it's better to use Alembic for migrations instead of create_all
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="UrbanFlow API",
    description="AI-driven urban mobility orchestrator for the MyAI Future Hackathon.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Welcome to UrbanFlow API"}

app.include_router(trips.router, prefix="/api/v1/trips", tags=["Trips"])
app.include_router(bus.router, prefix="/api/v1/bus", tags=["Bus Stations"])
app.include_router(parking.router, prefix="/api/v1/parking", tags=["Smart Parking"])
app.include_router(impact.router, prefix="/api/v1/impact", tags=["Carbon Ledger"])
