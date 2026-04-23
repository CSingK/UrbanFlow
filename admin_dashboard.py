import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import requests
import random
import string

# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/urbanflow"
engine = create_engine(DATABASE_URL)

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# Helper function to run DB queries
def fetch_data(query):
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# Simulation Functions
def sim_random_carpool():
    users_df = fetch_data("SELECT id, social_cluster_tag FROM users")
    if len(users_df) < 4:
        st.sidebar.error("Not enough users to simulate carpool.")
        return
        
    rts_df = fetch_data("SELECT id FROM rts_schedules LIMIT 1")
    if rts_df.empty:
        st.sidebar.error("No RTS schedules found.")
        return
        
    driver_id = str(users_df.iloc[0]['id'])
    passenger_ids = [str(x) for x in users_df.iloc[1:4]['id'].tolist()]
    rts_slot_id = str(rts_df.iloc[0]['id'])
    
    payload = {
        "rts_slot_id": rts_slot_id,
        "driver_id": driver_id,
        "passenger_ids": passenger_ids
    }
    
    res = requests.post(f"{API_BASE_URL}/trips/match", json=payload)
    if res.status_code == 200:
        st.sidebar.success("Carpool matched!")
    else:
        st.sidebar.error("Failed to match carpool.")

def sim_bus_crowd():
    stations_df = fetch_data("SELECT id FROM bus_stations")
    if stations_df.empty:
        st.sidebar.error("No bus stations found.")
        return
    station_id = str(stations_df.sample(1).iloc[0]['id'])
    
    payload = {"image_path": "/mock/camera_feed_01.jpg"}
    res = requests.post(f"{API_BASE_URL}/bus/update-feed/{station_id}", json=payload)
    if res.status_code == 200:
        st.sidebar.success("Bus crowd updated!")
    else:
        st.sidebar.error("Failed to update bus crowd.")

def sim_parking_event():
    zones_df = fetch_data("SELECT id FROM parking_zones")
    if zones_df.empty:
        st.sidebar.error("No parking zones found.")
        return
    zone_id = str(zones_df.sample(1).iloc[0]['id'])
    
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=4))
    plate = f"{letters}{numbers}"
    
    payload = {"image_path": "/mock/camera_feed_02.jpg", "zone_id": zone_id, "license_plate": plate}
    res = requests.post(f"{API_BASE_URL}/parking/detect", json=payload)
    if res.status_code == 200:
        st.sidebar.success(f"Detected {plate}!")
    else:
        st.sidebar.error("Failed to detect parking.")

# Layout Configuration
st.set_page_config(page_title="UrbanFlow Admin Portal", layout="wide")

st.sidebar.title("🚦 UrbanFlow Admin")
view = st.sidebar.radio("Navigation", ["City Overview", "Mobility Hub", "Sustainability Ledger"])

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎮 Simulation Control")
if st.sidebar.button("Simulate Random Carpool"):
    sim_random_carpool()
if st.sidebar.button("Simulate Bus Crowd"):
    sim_bus_crowd()
if st.sidebar.button("Simulate Parking Event"):
    sim_parking_event()

st.title(view)

# View 1: City Overview
if view == "City Overview":
    st.markdown("Monitor real-time system performance and enforcement.")
    
    # Hero Metric
    co2_df = fetch_data("SELECT SUM(co2_saved_grams) as total FROM carbon_ledger")
    total_co2 = co2_df.iloc[0]['total'] if not pd.isna(co2_df.iloc[0]['total']) else 0.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🌱 Total CO₂ Avoided (grams)", value=f"{total_co2:,.2f}")
        
    with col2:
        parking_df = fetch_data("SELECT COUNT(*) as cnt FROM parking_logs WHERE status='illegal'")
        illegals = parking_df.iloc[0]['cnt'] if not pd.isna(parking_df.iloc[0]['cnt']) else 0
        st.metric(label="⚠️ Active Parking Violations", value=illegals)
        
    st.subheader("Live Parking Enforcement Feed")
    feed_df = fetch_data("""
        SELECT license_plate, p.zone_name, status, last_seen 
        FROM parking_logs l
        JOIN parking_zones p ON l.zone_id = p.id
        ORDER BY last_seen DESC LIMIT 5
    """)
    if feed_df.empty:
        st.info("No active parking logs.")
    else:
        st.dataframe(feed_df, use_container_width=True)

# View 2: Mobility Hub
elif view == "Mobility Hub":
    st.markdown("Real-time Transit & Carpool synchronization.")
    
    st.subheader("Bus Stations Intelligence")
    bus_df = fetch_data("SELECT station_name, current_queue_count, predicted_occupancy as pob_score, last_updated FROM bus_stations")
    if bus_df.empty:
        st.info("No bus data available.")
    else:
        st.dataframe(bus_df, use_container_width=True)
        
    st.subheader("Upcoming RTS Slots (Carpool Sync)")
    rts_df = fetch_data("""
        SELECT r.train_id, r.departure_time_jb, count(t.id) as carpool_trips
        FROM rts_schedules r
        LEFT JOIN trips t ON r.id = t.rts_slot_id
        GROUP BY r.id
        ORDER BY departure_time_jb ASC LIMIT 5
    """)
    if rts_df.empty:
        st.info("No RTS schedules found.")
    else:
        st.dataframe(rts_df, use_container_width=True)

# View 3: Sustainability Ledger
elif view == "Sustainability Ledger":
    st.markdown("Detailed breakdown of carbon impact by transport shift.")
    
    ledger_df = fetch_data("SELECT category, SUM(co2_saved_grams) as total_saved FROM carbon_ledger GROUP BY category")
    
    if ledger_df.empty:
        st.info("No carbon data recorded yet.")
    else:
        ledger_df = ledger_df.set_index('category')
        st.bar_chart(ledger_df)
