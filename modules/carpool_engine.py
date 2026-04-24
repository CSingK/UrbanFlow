"""
Carpool Engine — AI-synchronized carpool matching for RTS commuter coordination.
"""
import random
import datetime
from typing import Dict, List, Any

# RTS Train Schedule (Bukit Chagar, every 10 min from 6AM-10PM)
RTS_SCHEDULE = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in [2, 12, 22, 32, 42, 52]]

NEIGHBORHOODS = [
    {"name": "Taman Molek", "coords": [1.5320, 103.7860], "population": 25000},
    {"name": "Taman Pelangi", "coords": [1.4850, 103.7560], "population": 18000},
    {"name": "Taman Sentosa", "coords": [1.4750, 103.7480], "population": 22000},
    {"name": "Taman Mount Austin", "coords": [1.5480, 103.7930], "population": 35000},
    {"name": "Taman Daya", "coords": [1.5580, 103.7850], "population": 28000},
    {"name": "Skudai", "coords": [1.5370, 103.6550], "population": 40000},
    {"name": "Perling", "coords": [1.5100, 103.6900], "population": 20000},
    {"name": "Iskandar Puteri", "coords": [1.4272, 103.6158], "population": 30000},
    {"name": "Masai", "coords": [1.5020, 103.8650], "population": 15000},
    {"name": "Ulu Tiram", "coords": [1.5950, 103.8100], "population": 32000},
    {"name": "Johor Jaya", "coords": [1.5240, 103.8020], "population": 26000},
    {"name": "Taman Universiti", "coords": [1.5580, 103.6420], "population": 21000},
    {"name": "Gelang Patah", "coords": [1.4550, 103.5980], "population": 18000},
    {"name": "Kulai", "coords": [1.6580, 103.5990], "population": 45000},
    {"name": "Nusajaya", "coords": [1.4350, 103.6400], "population": 24000},
]

SG_WORKPLACES = [
    {"name": "Jurong East (JTC)"}, {"name": "Tuas Industrial"},
    {"name": "Woodlands (North)"}, {"name": "Raffles Place (CBD)"},
    {"name": "One-North (Tech Park)"}, {"name": "Changi Business Park"},
]

def _generate_commuters(count=60):
    random.seed(2025)
    commuters = []
    names = ["Ahmad", "Siti", "Wei Ming", "Priya", "Rizal", "Nur", "Jin", "Kumar",
             "Mei Ling", "Hafiz", "Aisyah", "Raj", "Xiao", "Farah", "Amir", "Lina"]
    for i in range(count):
        hood = random.choice(NEIGHBORHOODS)
        wp = random.choice(SG_WORKPLACES)
        ph = random.choice([7, 8, 9])
        pm = random.choice([0, 12, 22, 32, 42, 52])
        commuters.append({
            "id": f"CMT-{i+1:04d}", "name": f"{random.choice(names)} {chr(65+i%26)}.",
            "neighborhood": hood["name"],
            "home_coords": [hood["coords"][0]+random.uniform(-0.005,0.005), hood["coords"][1]+random.uniform(-0.005,0.005)],
            "workplace": wp["name"], "target_train": f"{ph:02d}:{pm:02d}",
            "flexibility_min": random.choice([5, 10, 15]),
            "seats_available": random.randint(1, 3), "rating": round(random.uniform(4.2, 5.0), 1),
            "trips_completed": random.randint(5, 200),
        })
    return commuters

COMMUTER_DB = _generate_commuters()

def match_carpool(user_neighborhood, target_train_time, flexibility_min=15):
    """Match user with carpool partners heading to RTS at similar time."""
    try:
        target_h, target_m = map(int, target_train_time.split(":"))
        target_minutes = target_h * 60 + target_m
    except Exception:
        return {"error": "Invalid time format. Use HH:MM."}

    best_train, best_diff = None, 999
    for t in RTS_SCHEDULE:
        th, tm = map(int, t.split(":"))
        diff = abs((th*60+tm) - target_minutes)
        if diff < best_diff:
            best_diff, best_train = diff, t

    user_hood = next((h for h in NEIGHBORHOODS if h["name"] == user_neighborhood), None)
    if not user_hood:
        return {"error": f"Neighborhood '{user_neighborhood}' not found."}

    matches = []
    for c in COMMUTER_DB:
        if c["neighborhood"] == user_neighborhood:
            continue
        ch, cm = map(int, c["target_train"].split(":"))
        time_diff = abs((ch*60+cm) - target_minutes)
        if time_diff > flexibility_min + c["flexibility_min"]:
            continue
        c_hood = next((h for h in NEIGHBORHOODS if h["name"] == c["neighborhood"]), None)
        if not c_hood:
            continue
        dist = ((c_hood["coords"][0]-user_hood["coords"][0])**2 + (c_hood["coords"][1]-user_hood["coords"][1])**2)**0.5 * 111
        if dist > 8:
            continue
        matches.append({**c, "distance_km": round(dist,1), "time_diff_min": time_diff,
                        "compatibility_score": round(100-(time_diff*2+dist*5), 1)})

    matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
    top = matches[:3]

    train_h, train_m = map(int, best_train.split(":"))
    arrival = train_h*60 + train_m - 15
    schedule = []
    cur = arrival - len(top)*8
    for i, m in enumerate(top):
        schedule.append({"order": i+1, "name": m["name"], "neighborhood": m["neighborhood"],
                         "pickup_time": f"{cur//60:02d}:{cur%60:02d}"})
        cur += 8

    total_km = sum(m["distance_km"] for m in top) + 5
    solo = round(total_km*0.55, 2)
    shared = round(solo/(len(top)+1), 2) if top else solo

    return {
        "target_train": best_train,
        "arrival_at_terminal": f"{arrival//60:02d}:{arrival%60:02d}",
        "matches": top, "pickup_schedule": schedule,
        "cost_savings": {"solo_cost_rm": solo, "shared_cost_rm": shared,
                         "savings_rm": round(solo-shared, 2),
                         "co2_saved_kg": round(total_km*0.21*(1-1/max(len(top)+1,1)), 2)},
        "total_passengers": len(top)+1,
    }

def get_demand_clusters():
    """Aggregate carpool demand by neighborhood for authority heat map."""
    clusters = {}
    for c in COMMUTER_DB:
        hood = c["neighborhood"]
        if hood not in clusters:
            h = next((n for n in NEIGHBORHOODS if n["name"] == hood), None)
            clusters[hood] = {"neighborhood": hood, "coords": h["coords"] if h else [0,0],
                              "commuter_count": 0, "avg_target_hour": 0, "workplaces": {},
                              "population": h["population"] if h else 0}
        clusters[hood]["commuter_count"] += 1
        hv, _ = map(int, c["target_train"].split(":"))
        clusters[hood]["avg_target_hour"] += hv
        wp = c["workplace"]
        clusters[hood]["workplaces"][wp] = clusters[hood]["workplaces"].get(wp, 0) + 1

    result = []
    for hood, d in clusters.items():
        if d["commuter_count"] > 0:
            d["avg_target_hour"] = round(d["avg_target_hour"]/d["commuter_count"], 1)
            d["demand_density"] = round(d["commuter_count"]/d["population"]*10000, 1)
            d["top_workplace"] = max(d["workplaces"], key=d["workplaces"].get)
            del d["workplaces"]
            result.append(d)
    result.sort(key=lambda x: x["commuter_count"], reverse=True)
    return result

def get_carpool_stats():
    random.seed(datetime.datetime.now().hour)
    return {
        "active_carpools_today": random.randint(180, 320),
        "commuters_matched": random.randint(500, 900),
        "avg_occupancy": round(random.uniform(2.8, 3.5), 1),
        "co2_saved_today_kg": random.randint(400, 900),
        "on_time_rate": f"{random.uniform(92, 98):.1f}%",
    }
