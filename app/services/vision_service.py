import random
from uuid import UUID
from typing import Tuple

async def process_station_feed(station_id: UUID, image_path: str) -> Tuple[int, int]:
    """
    Mocks a call to Google Cloud Vision AI to detect people in the station queue
    and the arriving bus occupancy via an IoT sensor or internal camera.
    
    Returns:
        tuple: (queue_count, bus_occupancy)
    """
    # Simulate processing time for GCP Vision API
    # Generate mock queue count
    queue_count = random.randint(0, 50)
    
    # Generate mock bus occupancy between 10 and 40
    bus_occupancy = random.randint(10, 40)
    
    return queue_count, bus_occupancy
