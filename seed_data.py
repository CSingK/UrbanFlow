import asyncio
import uuid
from app.database import engine, Base, async_session_maker
from app.models.user import User
from app.models.bus_station import BusStation
from app.models.parking import ParkingZone
from app.models.rts_schedule import RTSSchedule
from datetime import datetime, timezone, timedelta

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

async def seed_data():
    async with engine.begin() as conn:
        print("Recreating database tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        print("Seeding Users...")
        driver = User(name="Ahmad Driver", email="ahmad@example.com", license_plate="JQQ1234", social_cluster_tag="tech_park")
        p1 = User(name="Siti Tech", email="siti@example.com", social_cluster_tag="tech_park")
        p2 = User(name="John Doe", email="john@example.com", social_cluster_tag="tech_park")
        p3 = User(name="Ali Baba", email="ali@example.com", social_cluster_tag="different_park")
        p4 = User(name="Jane Smith", email="jane@example.com", social_cluster_tag="tech_park")
        
        session.add_all([driver, p1, p2, p3, p4])
        
        print("Seeding Bus Stations...")
        station1 = BusStation(station_name="JS-SEZ Main Station", latitude=1.4550, longitude=103.7610, bus_capacity=40, current_bus_occupancy=10)
        station2 = BusStation(station_name="Larkin Hub", latitude=1.4950, longitude=103.7430, bus_capacity=40, current_bus_occupancy=35)
        
        session.add_all([station1, station2])
        
        print("Seeding Parking Zones...")
        zone_normal = ParkingZone(zone_name="JB Sentral Drop-off", latitude=1.4628, longitude=103.7644, zone_intensity="NORMAL")
        zone_critical = ParkingZone(zone_name="RTS Express Lane", latitude=1.4650, longitude=103.7660, zone_intensity="CRITICAL")
        
        session.add_all([zone_normal, zone_critical])
        
        print("Seeding RTS Schedule...")
        now = get_utc_plus_8()
        train_departure = now + timedelta(hours=1)
        rts = RTSSchedule(train_id="RTS-1234", departure_time_jb=train_departure, arrival_time_sg=train_departure + timedelta(minutes=15))
        session.add(rts)
        
        await session.commit()
        print("Seed Data successfully injected!")
        
        # Print out the IDs for easy testing
        print("\n--- Test IDs ---")
        print(f"Driver ID: {driver.id}")
        print(f"Passengers IDs: {p1.id}, {p2.id}, {p3.id}, {p4.id}")
        print(f"RTS Slot ID: {rts.id}")
        print(f"Normal Zone ID: {zone_normal.id}")
        print(f"Critical Zone ID: {zone_critical.id}")
        print(f"Station 1 ID: {station1.id}")
        print(f"Driver License Plate: {driver.license_plate}")
        
if __name__ == "__main__":
    asyncio.run(seed_data())
