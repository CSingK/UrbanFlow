"""
Bus Intelligence Engine — Probability of Boarding (PoB) predictor & queue simulation.
"""
import random
import datetime
import math
from typing import Dict, List, Any

BUS_STATIONS = [
    {"id": "BS-001", "name": "Bukit Chagar Terminal", "coords": [1.4580, 103.7610], "is_rts": True},
    {"id": "BS-002", "name": "JB Sentral", "coords": [1.4632, 103.7639], "is_rts": False},
    {"id": "BS-003", "name": "Larkin Sentral", "coords": [1.5250, 103.7520], "is_rts": False},
    {"id": "BS-004", "name": "KOMTAR JBCC", "coords": [1.4630, 103.7620], "is_rts": False},
    {"id": "BS-005", "name": "City Square Terminal", "coords": [1.4927, 103.7414], "is_rts": False},
    {"id": "BS-006", "name": "Taman Molek Hub", "coords": [1.5320, 103.7860], "is_rts": False},
    {"id": "BS-007", "name": "Mount Austin Stop", "coords": [1.5480, 103.7930], "is_rts": False},
    {"id": "BS-008", "name": "Skudai Interchange", "coords": [1.5370, 103.6550], "is_rts": False},
    {"id": "BS-009", "name": "Iskandar Puteri Hub", "coords": [1.4272, 103.6158], "is_rts": False},
    {"id": "BS-010", "name": "Perling Mall Stop", "coords": [1.5100, 103.6900], "is_rts": False},
    {"id": "BS-011", "name": "Masai Terminal", "coords": [1.5020, 103.8650], "is_rts": False},
    {"id": "BS-012", "name": "Kulai Hub", "coords": [1.6580, 103.5990], "is_rts": False},
    {"id": "BS-013", "name": "Danga Bay Stop", "coords": [1.4620, 103.7280], "is_rts": False},
    {"id": "BS-014", "name": "Gelang Patah Stop", "coords": [1.4550, 103.5980], "is_rts": False},
    {"id": "BS-015", "name": "Johor Jaya Hub", "coords": [1.5240, 103.8020], "is_rts": False},
]

BUS_ROUTES = [
    {"id": "T10", "name": "CW1 - Causeway Link", "stations": ["BS-001","BS-002","BS-003"], "capacity": 45, "freq_min": 12},
    {"id": "T11", "name": "CW2 - JB-Woodlands", "stations": ["BS-001","BS-004","BS-005"], "capacity": 45, "freq_min": 15},
    {"id": "T20", "name": "BET - Bukit Chagar Express", "stations": ["BS-001","BS-006","BS-007"], "capacity": 50, "freq_min": 10},
    {"id": "T30", "name": "ISK - Iskandar Shuttle", "stations": ["BS-009","BS-013","BS-001"], "capacity": 40, "freq_min": 20},
    {"id": "T40", "name": "LRK - Larkin Connector", "stations": ["BS-003","BS-008","BS-012"], "capacity": 50, "freq_min": 15},
    {"id": "T50", "name": "MSI - Masai-JB Express", "stations": ["BS-011","BS-015","BS-002"], "capacity": 45, "freq_min": 18},
    {"id": "T60", "name": "PLG - Perling-CIQ", "stations": ["BS-010","BS-014","BS-001"], "capacity": 40, "freq_min": 22},
    {"id": "T70", "name": "MTA - Mount Austin Loop", "stations": ["BS-007","BS-006","BS-005","BS-003"], "capacity": 50, "freq_min": 12},
]

def _get_peak_factor(hour):
    """Return a multiplier based on time of day (peak hours = higher demand)."""
    if 7 <= hour <= 9:
        return 1.8  # Morning rush
    elif 17 <= hour <= 19:
        return 1.6  # Evening rush
    elif 12 <= hour <= 14:
        return 1.2  # Lunch
    else:
        return 0.7

def predict_pob(station_id, target_time_str, day_of_week="Weekday"):
    """Predict Probability of Boarding for a given station and time."""
    try:
        th, tm = map(int, target_time_str.split(":"))
    except Exception:
        return {"error": "Invalid time format."}

    station = next((s for s in BUS_STATIONS if s["id"] == station_id), None)
    if not station:
        return {"error": "Station not found."}

    random.seed(hash(f"{station_id}{target_time_str}{day_of_week}"))
    peak = _get_peak_factor(th)
    is_weekend = day_of_week in ("Saturday", "Sunday")
    if is_weekend:
        peak *= 0.5

    routes_at_station = [r for r in BUS_ROUTES if station_id in r["stations"]]
    results = []
    for route in routes_at_station:
        base_occupancy = random.uniform(0.3, 0.6)
        occupancy = min(base_occupancy * peak, 0.98)
        queue_count = int(random.uniform(3, 25) * peak)
        space_left = int(route["capacity"] * (1 - occupancy))
        pob = min(max(space_left / max(queue_count, 1) * 100, 5), 99)
        next_bus_min = random.randint(1, route["freq_min"])

        results.append({
            "route_id": route["id"], "route_name": route["name"],
            "next_bus_min": next_bus_min,
            "bus_occupancy_pct": round(occupancy * 100, 1),
            "space_available": space_left,
            "queue_count": queue_count,
            "pob_score": round(pob, 1),
            "pob_label": "High" if pob >= 70 else ("Medium" if pob >= 40 else "Low"),
            "pob_color": "#22c55e" if pob >= 70 else ("#f97316" if pob >= 40 else "#ef4444"),
            "frequency_min": route["freq_min"],
        })

    results.sort(key=lambda x: x["pob_score"], reverse=True)
    return {"station": station["name"], "target_time": target_time_str,
            "day": day_of_week, "routes": results}

def get_all_stations_overview():
    """Live overview of all stations for authority dashboard."""
    random.seed(datetime.datetime.now().minute)
    hour = datetime.datetime.now().hour
    peak = _get_peak_factor(hour)
    overview = []
    for s in BUS_STATIONS:
        queue = int(random.uniform(2, 30) * peak)
        routes_here = [r for r in BUS_ROUTES if s["id"] in r["stations"]]
        avg_pob = random.uniform(40, 95) / peak if routes_here else 0
        overview.append({
            "station_id": s["id"], "station_name": s["name"], "coords": s["coords"],
            "queue_count": queue, "avg_pob": round(min(avg_pob, 99), 1),
            "routes_served": len(routes_here), "is_rts": s["is_rts"],
            "status": "🔴 Surge" if queue > 20 else ("🟡 Busy" if queue > 10 else "🟢 Normal"),
        })
    return overview

def generate_dispatch_alerts():
    """Generate dynamic dispatch alerts for predicted queue surges."""
    random.seed(datetime.datetime.now().minute)
    alerts = []
    hour = datetime.datetime.now().hour
    for s in BUS_STATIONS:
        if random.random() > 0.7:
            predicted_queue = random.randint(25, 60)
            surge_time_h = min(hour + random.randint(0, 2), 22)
            surge_time_m = random.choice([0, 15, 30, 45])
            alerts.append({
                "station": s["name"], "station_id": s["id"],
                "predicted_queue": predicted_queue,
                "surge_time": f"{surge_time_h:02d}:{surge_time_m:02d}",
                "recommended_action": f"Deploy 1 relief bus on routes serving {s['name']}",
                "severity": "Critical" if predicted_queue > 40 else "Warning",
                "confidence": f"{random.uniform(78, 96):.1f}%",
            })
    alerts.sort(key=lambda x: x["predicted_queue"], reverse=True)
    return alerts[:5]

def get_historical_trend(station_id, route_id=None):
    """Generate simulated historical PoB trend for charting (24 hours)."""
    random.seed(hash(f"{station_id}{route_id}"))
    hours = list(range(6, 23))
    data = []
    for h in hours:
        peak = _get_peak_factor(h)
        base_pob = random.uniform(50, 85)
        pob = max(min(base_pob / peak, 99), 10)
        queue = int(random.uniform(5, 15) * peak)
        data.append({"hour": f"{h:02d}:00", "pob": round(pob, 1), "queue": queue})
    return data

def get_bus_stats():
    random.seed(datetime.datetime.now().hour)
    return {
        "total_stations_monitored": len(BUS_STATIONS),
        "active_routes": len(BUS_ROUTES),
        "avg_pob_city": f"{random.uniform(60, 80):.1f}%",
        "surge_alerts_today": random.randint(2, 8),
        "relief_buses_deployed": random.randint(1, 5),
        "commuters_served_today": random.randint(8000, 15000),
    }
