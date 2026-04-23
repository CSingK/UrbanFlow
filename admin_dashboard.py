import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import requests
import random
import string
from datetime import datetime, timezone, timedelta

# Database setup
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "urbanflow")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def get_utc_plus_8():
    return datetime.now(timezone(timedelta(hours=8)))

# Helper function to run DB queries
def fetch_data(query):
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except OperationalError as e:
        st.error(f"Database Connection Failed. Please ensure the {DB_NAME} database is running at {DB_HOST}:{DB_PORT}.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Simulation Functions
def sim_random_carpool():
    users_df = fetch_data("SELECT id, social_cluster_tag FROM users")
    if users_df.empty or len(users_df) < 4:
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
    
    try:
        res = requests.post(f"{API_BASE_URL}/trips/match", json=payload)
        if res.status_code == 200:
            st.sidebar.success("Carpool matched!")
        else:
            st.sidebar.error("Failed to match carpool.")
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {e}")

def sim_bus_crowd():
    stations_df = fetch_data("SELECT id FROM bus_stations")
    if stations_df.empty:
        st.sidebar.error("No bus stations found.")
        return
    station_id = str(stations_df.sample(1).iloc[0]['id'])
    
    payload = {"image_path": "/mock/camera_feed_01.jpg"}
    try:
        res = requests.post(f"{API_BASE_URL}/bus/update-feed/{station_id}", json=payload)
        if res.status_code == 200:
            st.sidebar.success("Bus crowd updated!")
        else:
            st.sidebar.error("Failed to update bus crowd.")
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {e}")

def sim_parking_event():
    zones_df = fetch_data("SELECT id FROM parking_zones")
    if zones_df.empty:
        st.sidebar.error("No parking zones found.")
        return
    zone_id = str(zones_df.sample(1).iloc[0]['id'])
    
    # 50% chance to re-detect an existing car if any exist
    existing_logs = fetch_data("SELECT license_plate FROM parking_logs")
    if not existing_logs.empty and random.random() > 0.5:
        plate = existing_logs.sample(1).iloc[0]['license_plate']
    else:
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=4))
        plate = f"{letters}{numbers}"
    
    payload = {"image_path": "/mock/camera_feed_02.jpg", "zone_id": zone_id, "license_plate": plate}
    try:
        res = requests.post(f"{API_BASE_URL}/parking/detect", json=payload)
        if res.status_code == 200:
            st.sidebar.success(f"Detected {plate}!")
        else:
            st.sidebar.error("Failed to detect parking.")
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {e}")

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
@st.experimental_fragment
def view_city_overview():
    st.markdown("Monitor real-time system performance and enforcement.")
    
    # Hero Metric
    co2_df = fetch_data("SELECT SUM(co2_saved_grams) as total FROM carbon_ledger")
    total_co2_grams = co2_df.iloc[0]['total'] if not co2_df.empty and not pd.isna(co2_df.iloc[0]['total']) else 0.0
    total_co2_kg = total_co2_grams / 1000.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🌱 Total CO₂ Avoided (kg)", value=f"{total_co2_kg:,.2f} kg")
        
    with col2:
        # Improved logic: Count cars that are EXPLICITLY illegal OR those in grace period whose time has run out
        violation_query = """
            SELECT COUNT(*) as cnt 
            FROM parking_logs l
            JOIN parking_zones p ON l.zone_id = p.id
            WHERE l.status = 'illegal' 
               OR (l.status = 'grace_period' AND 
                   EXTRACT(EPOCH FROM (NOW() AT TIME ZONE 'UTC' + INTERVAL '8 hours' - l.first_seen)) > 
                   CASE WHEN p.zone_intensity = 'CRITICAL' THEN 120 ELSE 300 END)
        """
        parking_df = fetch_data(violation_query)
        illegals = parking_df.iloc[0]['cnt'] if not parking_df.empty and not pd.isna(parking_df.iloc[0]['cnt']) else 0
        st.metric(label="⚠️ Active Parking Violations", value=illegals)
        
    st.subheader("Live Parking Enforcement Feed")
    feed_df = fetch_data("""
        SELECT license_plate, p.zone_intensity, status, first_seen, last_seen 
        FROM parking_logs l
        JOIN parking_zones p ON l.zone_id = p.id
        ORDER BY last_seen DESC LIMIT 5
    """)
    if feed_df.empty:
        st.info("No active parking logs.")
    else:
        now = get_utc_plus_8()
        
        # Calculate current status and time remaining dynamically
        def update_row(row):
            first_seen = pd.to_datetime(row['first_seen'])
            if first_seen.tzinfo is None:
                first_seen = first_seen.tz_localize(timezone.utc)
            
            grace_mins = 2 if row['zone_intensity'] == 'CRITICAL' else 5
            deadline = first_seen + pd.Timedelta(minutes=grace_mins)
            diff = (deadline - now).total_seconds()
            
            if row['status'] == 'grace_period':
                if diff > 0:
                    return 'grace_period', f"{int(diff)}s"
                else:
                    return 'illegal', "0s"
            return row['status'], "-"
            
        # Apply dynamic status update
        res_cols = feed_df.apply(update_row, axis=1, result_type='expand')
        feed_df['status'] = res_cols[0]
        feed_df['time_remaining'] = res_cols[1]
        
        # Format timestamps safely handling timezone aware objects
        if 'last_seen' in feed_df and not feed_df['last_seen'].empty:
            feed_df['last_seen'] = pd.to_datetime(feed_df['last_seen']).dt.strftime('%H:%M:%S')
        if 'first_seen' in feed_df and not feed_df['first_seen'].empty:
            feed_df['first_seen'] = pd.to_datetime(feed_df['first_seen']).dt.strftime('%H:%M:%S')
        
        # Apply styling
        def style_status(val):
            if val == 'grace_period': return 'color: #3b82f6; font-weight: bold;'
            if val in ['violation', 'illegal']: return 'color: #ef4444; font-weight: bold;'
            return ''
        
        styled_df = feed_df.style.map(style_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# View 2: Mobility Hub
@st.experimental_fragment
def view_mobility_hub():
    st.markdown("Real-time Transit & Carpool synchronization.")
    
    st.subheader("Bus Stations Intelligence")
    bus_df = fetch_data("SELECT station_name, current_queue_count, predicted_occupancy as pob_score, last_updated FROM bus_stations")
    if bus_df.empty:
        st.info("No bus data available.")
    else:
        if 'last_updated' in bus_df and not bus_df['last_updated'].empty:
            bus_df['last_updated'] = pd.to_datetime(bus_df['last_updated']).dt.strftime('%H:%M:%S')
            
        def style_pob(val):
            try:
                v = float(val)
                if v >= 0.7: return 'color: #22c55e; font-weight: bold;'
                if v >= 0.4: return 'color: #eab308; font-weight: bold;'
                return 'color: #ef4444; font-weight: bold;'
            except:
                return ''
                
        styled_bus = bus_df.style.map(style_pob, subset=['pob_score'])
        st.dataframe(styled_bus, use_container_width=True, hide_index=True)
        
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
        if 'departure_time_jb' in rts_df and not rts_df['departure_time_jb'].empty:
            rts_df['departure_time_jb'] = pd.to_datetime(rts_df['departure_time_jb']).dt.strftime('%H:%M:%S')
        st.dataframe(rts_df, use_container_width=True, hide_index=True)

# View 3: Sustainability Ledger
@st.experimental_fragment
def view_sustainability_ledger():
    st.markdown("Detailed breakdown of carbon impact by transport shift.")
    
    ledger_df = fetch_data("SELECT category, SUM(co2_saved_grams) as total_saved FROM carbon_ledger GROUP BY category")
    
    if ledger_df.empty:
        st.info("No carbon data recorded yet.")
    else:
        chart_df = ledger_df.set_index('category')
        st.bar_chart(chart_df)
        
        st.subheader("Verifiable Carbon Log")
        log_df = fetch_data("""
            SELECT u.name as user_name, c.category, c.co2_saved_grams, c.timestamp
            FROM carbon_ledger c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.timestamp DESC
        """)
        if not log_df.empty:
            if 'timestamp' in log_df and not log_df['timestamp'].empty:
                log_df['timestamp'] = pd.to_datetime(log_df['timestamp']).dt.strftime('%H:%M:%S')
            st.dataframe(log_df, use_container_width=True, hide_index=True)

# Main render
if view == "City Overview":
    view_city_overview()
elif view == "Mobility Hub":
    view_mobility_hub()
elif view == "Sustainability Ledger":
    view_sustainability_ledger()
