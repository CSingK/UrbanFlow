"""
Carbon Ledger Engine — CO2 accounting, personal scores, and city-wide impact tracking.
"""
import random
import datetime
import math
from typing import Dict, List, Any

# CO2 emission factors (kg CO2 per km)
EMISSION_FACTORS = {
    "private_car": 0.21,       # avg sedan
    "carpool_per_person": 0.07, # 3-person carpool
    "bus": 0.04,               # per passenger
    "rts_train": 0.02,         # per passenger
    "motorcycle": 0.11,
}

# Reward tiers
REWARD_TIERS = [
    {"name": "🌱 Seedling", "min_kg": 0, "max_kg": 10, "color": "#86efac",
     "reward": "5% RTS ticket discount"},
    {"name": "🌿 Sapling", "min_kg": 10, "max_kg": 50, "color": "#4ade80",
     "reward": "10% RTS discount + Free parking 1hr/week"},
    {"name": "🌳 Tree", "min_kg": 50, "max_kg": 150, "color": "#22c55e",
     "reward": "15% RTS discount + Free parking 3hr/week"},
    {"name": "🏔️ Forest", "min_kg": 150, "max_kg": 500, "color": "#16a34a",
     "reward": "20% RTS discount + Priority parking + RM50 voucher"},
    {"name": "🌍 Guardian", "min_kg": 500, "max_kg": 99999, "color": "#15803d",
     "reward": "25% RTS discount + Free parking + RM100 voucher/month"},
]

def calculate_personal_score(carpool_trips=0, carpool_km=0, bus_trips=0, bus_km=0,
                              rts_trips=0, rts_km=0, parking_diversions=0):
    """Calculate a commuter's personal carbon offset score."""
    # CO2 saved = (what they would have emitted driving solo) - (what they actually emitted)
    car_baseline = (carpool_km + bus_km + rts_km) * EMISSION_FACTORS["private_car"]
    actual = (carpool_km * EMISSION_FACTORS["carpool_per_person"] +
              bus_km * EMISSION_FACTORS["bus"] + rts_km * EMISSION_FACTORS["rts_train"])
    co2_saved = max(car_baseline - actual, 0)
    # Parking diversion bonus (each diversion saves ~0.8 kg from reduced circling)
    co2_saved += parking_diversions * 0.8

    # Determine tier
    tier = REWARD_TIERS[0]
    for t in REWARD_TIERS:
        if t["min_kg"] <= co2_saved < t["max_kg"]:
            tier = t
            break

    # Progress to next tier
    next_tier = None
    for i, t in enumerate(REWARD_TIERS):
        if t["name"] == tier["name"] and i < len(REWARD_TIERS) - 1:
            next_tier = REWARD_TIERS[i + 1]
            break

    progress_pct = 0
    if next_tier:
        range_size = next_tier["min_kg"] - tier["min_kg"]
        progress_pct = min(((co2_saved - tier["min_kg"]) / range_size) * 100, 100)

    return {
        "co2_saved_kg": round(co2_saved, 2),
        "co2_saved_trees_equiv": round(co2_saved / 21, 1),  # 1 tree absorbs ~21kg/year
        "tier": tier, "next_tier": next_tier,
        "progress_pct": round(progress_pct, 1),
        "breakdown": {
            "carpool": {"trips": carpool_trips, "km": carpool_km,
                        "co2_saved": round(carpool_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["carpool_per_person"]), 2)},
            "bus": {"trips": bus_trips, "km": bus_km,
                    "co2_saved": round(bus_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["bus"]), 2)},
            "rts": {"trips": rts_trips, "km": rts_km,
                    "co2_saved": round(rts_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["rts_train"]), 2)},
            "parking_diversion": {"count": parking_diversions,
                                   "co2_saved": round(parking_diversions * 0.8, 2)},
        },
        "monthly_rm_value": round(co2_saved * 0.15, 2),  # RM 0.15 per kg saved
    }

def get_sample_personal_data():
    """Generate sample commuter data for demo."""
    random.seed(42)
    return calculate_personal_score(
        carpool_trips=random.randint(15, 40), carpool_km=random.randint(200, 600),
        bus_trips=random.randint(10, 30), bus_km=random.randint(80, 250),
        rts_trips=random.randint(20, 50), rts_km=random.randint(100, 300),
        parking_diversions=random.randint(5, 20),
    )

def calculate_city_impact():
    """Calculate aggregate city-wide carbon impact."""
    random.seed(datetime.datetime.now().day)
    # Daily figures
    carpools_today = random.randint(200, 400)
    carpool_km = carpools_today * random.uniform(8, 15)
    bus_riders = random.randint(8000, 15000)
    bus_km = bus_riders * random.uniform(5, 12)
    rts_riders = random.randint(5000, 12000)
    rts_km = rts_riders * random.uniform(2, 5)
    diversions = random.randint(100, 300)

    baseline = ((carpool_km + bus_km + rts_km) * EMISSION_FACTORS["private_car"] +
                diversions * 2.5)
    actual = (carpool_km * EMISSION_FACTORS["carpool_per_person"] +
              bus_km * EMISSION_FACTORS["bus"] + rts_km * EMISSION_FACTORS["rts_train"])
    co2_prevented = baseline - actual

    return {
        "co2_prevented_today_kg": round(co2_prevented, 0),
        "co2_prevented_today_tonnes": round(co2_prevented / 1000, 2),
        "equivalent_trees": round(co2_prevented / 21, 0),
        "equivalent_cars_off_road": round(co2_prevented / 4.6, 0),  # avg 4.6 kg/car/day
        "breakdown": {
            "carpool_module": {"participants": carpools_today * 3,
                               "co2_saved_kg": round(carpool_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["carpool_per_person"]), 0)},
            "bus_module": {"riders": bus_riders,
                           "co2_saved_kg": round(bus_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["bus"]), 0)},
            "rts_module": {"riders": rts_riders,
                           "co2_saved_kg": round(rts_km * (EMISSION_FACTORS["private_car"] - EMISSION_FACTORS["rts_train"]), 0)},
            "parking_diversion": {"diversions": diversions, "co2_saved_kg": round(diversions * 0.8, 0)},
        },
        "net_zero_2050_progress": round(random.uniform(12, 18), 1),  # % towards goal
        "monthly_trend_pct_change": round(random.uniform(2, 8), 1),
    }

def get_emissions_heatmap_data():
    """Generate geographic emission density data for JB zones."""
    random.seed(datetime.datetime.now().day)
    zones = [
        {"name": "CIQ/RTS Zone", "coords": [1.4610, 103.7620], "base_emission": 850},
        {"name": "JB City Center", "coords": [1.4927, 103.7414], "base_emission": 720},
        {"name": "Larkin Area", "coords": [1.5250, 103.7520], "base_emission": 450},
        {"name": "Taman Molek", "coords": [1.5320, 103.7860], "base_emission": 320},
        {"name": "Skudai Corridor", "coords": [1.5370, 103.6550], "base_emission": 380},
        {"name": "Iskandar Puteri", "coords": [1.4272, 103.6158], "base_emission": 280},
        {"name": "Mount Austin", "coords": [1.5480, 103.7930], "base_emission": 340},
        {"name": "Masai Industrial", "coords": [1.5020, 103.8650], "base_emission": 520},
        {"name": "Danga Bay", "coords": [1.4620, 103.7280], "base_emission": 200},
        {"name": "Kulai", "coords": [1.6580, 103.5990], "base_emission": 310},
    ]
    for z in zones:
        prevented = round(z["base_emission"] * random.uniform(0.1, 0.3), 0)
        z["daily_emission_kg"] = z["base_emission"]
        z["co2_prevented_kg"] = prevented
        z["net_emission_kg"] = z["base_emission"] - prevented
        z["reduction_pct"] = round(prevented / z["base_emission"] * 100, 1)
        intensity = z["base_emission"]
        z["color"] = "#ef4444" if intensity > 600 else ("#f97316" if intensity > 400 else "#22c55e")
        z["radius"] = max(15, min(40, int(intensity / 25)))
    return zones

def get_monthly_trend(months=6):
    """Generate monthly CO2 savings trend data."""
    random.seed(2025)
    data = []
    base = random.uniform(800, 1200)
    now = datetime.datetime.now()
    for i in range(months, 0, -1):
        month = now - datetime.timedelta(days=30 * i)
        growth = 1 + (months - i) * 0.08
        val = base * growth * random.uniform(0.9, 1.1)
        data.append({
            "month": month.strftime("%b %Y"),
            "co2_prevented_tonnes": round(val / 1000, 2),
            "baseline_tonnes": round(val / 1000 / random.uniform(0.15, 0.25), 2),
        })
    return data

def get_carbon_stats():
    random.seed(datetime.datetime.now().hour)
    return {
        "co2_prevented_today": f"{random.randint(2, 8)} tonnes",
        "active_green_commuters": random.randint(3000, 8000),
        "credits_issued_today": random.randint(500, 2000),
        "net_zero_progress": f"{random.uniform(12, 18):.1f}%",
    }
