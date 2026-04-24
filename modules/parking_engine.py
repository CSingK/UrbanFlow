"""
Smart Parking Engine — Mock data & logic for Urban Enforcement & Green Zone Navigation.
Covers parking zones across Johor Bahru with simulated IoT sensor occupancy.
"""
import random
import datetime
from typing import Dict, List, Any

# ── Parking Zone Database (JB locations) ─────────────────────────────────────
PARKING_ZONES = [
    {
        "id": "GH-001", "name": "Medini Green Hub", "type": "Green Hub",
        "coords": [1.4183, 103.6330], "total_lots": 320, "hourly_rate": 2.00,
        "has_shuttle": True, "shuttle_freq_min": 10,
        "rts_distance_km": 8.2, "zone_color": "#22c55e",
    },
    {
        "id": "GH-002", "name": "Danga Bay Parking Complex", "type": "Green Hub",
        "coords": [1.4620, 103.7280], "total_lots": 450, "hourly_rate": 3.00,
        "has_shuttle": True, "shuttle_freq_min": 8,
        "rts_distance_km": 4.1, "zone_color": "#22c55e",
    },
    {
        "id": "GH-003", "name": "Taman Molek Park & Ride", "type": "Green Hub",
        "coords": [1.5320, 103.7860], "total_lots": 200, "hourly_rate": 1.50,
        "has_shuttle": True, "shuttle_freq_min": 15,
        "rts_distance_km": 6.5, "zone_color": "#22c55e",
    },
    {
        "id": "PZ-001", "name": "JB City Square Basement", "type": "Premium",
        "coords": [1.4927, 103.7414], "total_lots": 180, "hourly_rate": 5.00,
        "has_shuttle": False, "shuttle_freq_min": 0,
        "rts_distance_km": 1.2, "zone_color": "#f97316",
    },
    {
        "id": "PZ-002", "name": "KOMTAR JBCC Parking", "type": "Premium",
        "coords": [1.4630, 103.7620], "total_lots": 250, "hourly_rate": 4.00,
        "has_shuttle": False, "shuttle_freq_min": 0,
        "rts_distance_km": 2.8, "zone_color": "#f97316",
    },
    {
        "id": "PZ-003", "name": "CIQ Multi-Storey", "type": "CIQ Zone",
        "coords": [1.4635, 103.7639], "total_lots": 150, "hourly_rate": 6.00,
        "has_shuttle": False, "shuttle_freq_min": 0,
        "rts_distance_km": 0.5, "zone_color": "#ef4444",
    },
    {
        "id": "PZ-004", "name": "Bukit Chagar Terminal Lot", "type": "RTS Terminal",
        "coords": [1.4580, 103.7610], "total_lots": 100, "hourly_rate": 8.00,
        "has_shuttle": False, "shuttle_freq_min": 0,
        "rts_distance_km": 0.1, "zone_color": "#ef4444",
    },
    {
        "id": "GH-004", "name": "Iskandar Puteri Hub", "type": "Green Hub",
        "coords": [1.4272, 103.6158], "total_lots": 500, "hourly_rate": 1.00,
        "has_shuttle": True, "shuttle_freq_min": 12,
        "rts_distance_km": 12.0, "zone_color": "#22c55e",
    },
]

# ── IoT Sensor Simulation ────────────────────────────────────────────────────
def get_live_occupancy() -> List[Dict[str, Any]]:
    """Simulate live occupancy from LoRaWAN sensors for each parking zone."""
    random.seed(datetime.datetime.now().minute)  # changes every minute
    zones = []
    for z in PARKING_ZONES:
        # CIQ/RTS zones are almost always full, Green Hubs have more space
        if z["type"] in ("CIQ Zone", "RTS Terminal"):
            occupancy_pct = random.uniform(0.85, 0.98)
        elif z["type"] == "Premium":
            occupancy_pct = random.uniform(0.60, 0.90)
        else:  # Green Hub
            occupancy_pct = random.uniform(0.20, 0.55)

        occupied = int(z["total_lots"] * occupancy_pct)
        available = z["total_lots"] - occupied
        zones.append({
            **z,
            "occupied": occupied,
            "available": available,
            "occupancy_pct": round(occupancy_pct * 100, 1),
            "status": "FULL" if available <= 5 else ("LOW" if available <= 20 else "AVAILABLE"),
            "sensor_type": "LoRaWAN" if z["type"] == "Green Hub" else "CCTV",
            "last_updated": datetime.datetime.now().strftime("%H:%M:%S"),
        })
    return zones


def get_nearest_green_hub(user_lat: float = 1.4927, user_lon: float = 103.7414) -> Dict[str, Any]:
    """Find the nearest Green Hub with availability and generate reroute plan."""
    zones = get_live_occupancy()
    green_hubs = [z for z in zones if z["type"] == "Green Hub" and z["status"] != "FULL"]

    if not green_hubs:
        return {"error": "All Green Hubs are currently full. Please wait."}

    # Simple distance calculation (good enough for demo)
    for hub in green_hubs:
        dist = ((hub["coords"][0] - user_lat)**2 + (hub["coords"][1] - user_lon)**2) ** 0.5 * 111
        hub["distance_km"] = round(dist, 1)
        hub["drive_time_min"] = round(dist * 3.5, 0)  # ~17 km/h in JB traffic

    green_hubs.sort(key=lambda x: x["distance_km"])
    best = green_hubs[0]

    return {
        "recommended_hub": best["name"],
        "hub_id": best["id"],
        "distance_km": best["distance_km"],
        "drive_time_min": int(best["drive_time_min"]),
        "available_lots": best["available"],
        "hourly_rate": best["hourly_rate"],
        "shuttle_available": best["has_shuttle"],
        "shuttle_frequency": f"Every {best['shuttle_freq_min']} min" if best["has_shuttle"] else "N/A",
        "rts_connection": f"{best['rts_distance_km']} km to RTS Terminal",
        "coords": best["coords"],
        "savings_vs_ciq": f"RM {6.00 - best['hourly_rate']:.2f}/hr cheaper",
    }


# ── Enforcement Module ────────────────────────────────────────────────────────
VIOLATION_TYPES = [
    "Double Parking on Yellow Line",
    "Lane Hogging (>15 min stationary)",
    "Queue Cutting at CIQ Approach",
    "Illegal Stopping at Bus Lane",
    "Parking on Emergency Lane",
    "Obstruction at Loading Zone",
]

def generate_enforcement_log(count: int = 10) -> List[Dict[str, Any]]:
    """Generate simulated enforcement incidents with timestamps and plates."""
    random.seed(42)
    incidents = []
    plate_prefixes = ["JQH", "JMR", "JKP", "JDF", "WA", "BKE", "SGP"]

    for i in range(count):
        hour = random.randint(6, 22)
        minute = random.randint(0, 59)
        plate = f"{random.choice(plate_prefixes)} {random.randint(1000, 9999)}"
        violation = random.choice(VIOLATION_TYPES)

        zone_idx = random.randint(0, len(PARKING_ZONES) - 1)
        zone = PARKING_ZONES[zone_idx]

        incidents.append({
            "incident_id": f"ENF-{2025}{i+1:04d}",
            "timestamp": f"{datetime.date.today()} {hour:02d}:{minute:02d}",
            "license_plate": plate,
            "violation": violation,
            "location": zone["name"],
            "coords": zone["coords"],
            "severity": random.choice(["Low", "Medium", "High", "Critical"]),
            "status": random.choice(["Detected", "Verified", "Sent to PDRM", "Fine Issued"]),
            "confidence": f"{random.uniform(85, 99):.1f}%",
            "camera_id": f"CAM-{zone['id']}-{random.randint(1,5):02d}",
        })
    return incidents
