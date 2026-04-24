import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Load environment variables (like GOOGLE_API_KEY)
load_dotenv()

# Import modules
from modules.parking_engine import get_live_occupancy
from modules.carpool_engine import get_carpool_stats
from modules.bus_intelligence import get_bus_stats
from modules.carbon_ledger import get_carbon_stats, calculate_city_impact

# Configure page
st.set_page_config(
    page_title="PBT-Vision | Johor Smart City",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark-Mode & Glassmorphism
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f172a, #1e293b);
    }
    
    /* Sidebar glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Cards glassmorphism for metrics and other containers */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Subtle glow on hover for metric cards */
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
        transition: all 0.3s ease;
    }

    .feature-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.25);
        transform: translateY(-2px);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .feature-title {
        color: #f8fafc;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .feature-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .feature-stat {
        color: #38bdf8;
        font-size: 1.3rem;
        font-weight: bold;
        margin-top: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Title
st.title("🏙️ PBT-Vision: Johor Smart City Platform")
st.markdown("Real-time monitoring and predictive analytics for urban management in Johor Bahru JS-SEZ.")

# ── Top-Level Stats ───────────────────────────────────────────────────────────
parking_zones = get_live_occupancy()
carpool_stats = get_carpool_stats()
bus_stats = get_bus_stats()
carbon_stats = get_carbon_stats()

c1, c2, c3, c4 = st.columns(4)
total_parking = sum(z["available"] for z in parking_zones)
c1.metric("🅿️ Parking Lots Available", total_parking, f"{len(parking_zones)} zones")
c2.metric("🚗 Active Carpools", carpool_stats["active_carpools_today"], carpool_stats["on_time_rate"])
c3.metric("🚌 Avg City PoB", bus_stats["avg_pob_city"], f"{bus_stats['active_routes']} routes")
c4.metric("🌿 CO₂ Prevented Today", carbon_stats["co2_prevented_today"])

st.markdown("---")

# ── Feature Cards ─────────────────────────────────────────────────────────────
st.subheader("🧭 Platform Modules")
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🅿️</div>
        <div class="feature-title">Smart Parking</div>
        <div class="feature-desc">Green Zone navigation, IoT sensors, autonomous enforcement & license plate detection</div>
        <div class="feature-stat">""" + str(total_parking) + """ lots free</div>
    </div>
    """, unsafe_allow_html=True)

with fc2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🚗</div>
        <div class="feature-title">Carpool Agent</div>
        <div class="feature-desc">AI-synchronized matching with RTS train schedules for first-mile optimization</div>
        <div class="feature-stat">""" + str(carpool_stats["commuters_matched"]) + """ matched</div>
    </div>
    """, unsafe_allow_html=True)

with fc3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🚌</div>
        <div class="feature-title">Bus Intelligence</div>
        <div class="feature-desc">Probability of Boarding predictor, queue counting & dynamic dispatch alerts</div>
        <div class="feature-stat">""" + bus_stats["avg_pob_city"] + """ avg PoB</div>
    </div>
    """, unsafe_allow_html=True)

with fc4:
    city_impact = calculate_city_impact()
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🌿</div>
        <div class="feature-title">Carbon Ledger</div>
        <div class="feature-desc">Verifiable CO₂ accounting, personal offset scores & Net-Zero 2050 tracking</div>
        <div class="feature-stat">""" + str(city_impact["net_zero_2050_progress"]) + """% Net-Zero</div>
    </div>
    """, unsafe_allow_html=True)

st.caption("👈 Navigate to each module from the sidebar.")

st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Control Panel")
    
    st.subheader("📊 Urban Impact Analytics")
    selected_metric = st.selectbox("Select Metric", ["Traffic Flow", "Air Quality", "Waste Management", "Energy Usage"])
    
    st.subheader("🚨 Emergency Risk Scores")
    st.slider("Flooding Risk Threshold", 0, 100, 75)
    st.slider("Fire Hazard Index", 0, 100, 50)
    
    st.markdown("---")
    st.success("System Status: All Modules Online")
    st.markdown("""
    **Connected Services:**
    - 🛰️ LoRaWAN IoT Sensors
    - 📹 ITMax CCTV (2,500+)
    - 🚆 RTS Link Schedule
    - 🤖 Vertex AI / Gemini
    - 📊 BigQuery ML
    """)

# ── Main Area Map ─────────────────────────────────────────────────────────────
st.subheader("🗺️ Live City Map")

# Create a folium map centered on Johor Bahru
johor_coords = [1.4927, 103.7414]
# Using cartodbdark_matter for dark mode aesthetics
m = folium.Map(location=johor_coords, zoom_start=12, tiles="cartodbdark_matter")

# Dynamic map layers based on the selected metric in the sidebar
if selected_metric == "Traffic Flow":
    # Highlight specific roads with traffic density colors
    # Heavy Traffic route (Red)
    folium.PolyLine(locations=[[1.4632, 103.7639], [1.4722, 103.7630]], color="#ef4444", weight=6, opacity=0.8, tooltip="Heavy Traffic: Congestion Detected").add_to(m)
    # Moderate Traffic route (Orange)
    folium.PolyLine(locations=[[1.4927, 103.7414], [1.4820, 103.7510], [1.4750, 103.7450]], color="#f97316", weight=6, opacity=0.8, tooltip="Moderate Traffic").add_to(m)
    # Clear Traffic route (Green)
    folium.PolyLine(locations=[[1.4272, 103.6158], [1.4372, 103.6300], [1.4500, 103.6400]], color="#22c55e", weight=6, opacity=0.8, tooltip="Clear Traffic: Optimal Flow").add_to(m)
elif selected_metric == "Air Quality":
    # Show AQI heatmap-like circles
    folium.CircleMarker(location=[1.4927, 103.7414], radius=25, color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.4, tooltip="AQI: 65 (Moderate)").add_to(m)
    folium.CircleMarker(location=[1.4632, 103.7639], radius=35, color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.4, tooltip="AQI: 110 (Unhealthy for Sensitive Groups)").add_to(m)
    folium.CircleMarker(location=[1.4272, 103.6158], radius=20, color="#22c55e", fill=True, fill_color="#22c55e", fill_opacity=0.4, tooltip="AQI: 35 (Good)").add_to(m)
elif selected_metric == "Waste Management":
    folium.CircleMarker(location=[1.4800, 103.7500], radius=15, color="#eab308", fill=True, fill_color="#eab308", fill_opacity=0.6, tooltip="Bin Status: 80% Full").add_to(m)

# Add some sample markers
folium.Marker([1.4927, 103.7414], popup="JB City Square", tooltip="City Center", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
folium.Marker([1.4632, 103.7639], popup="JB Sentral", tooltip="Transport Hub", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
folium.Marker([1.4272, 103.6158], popup="Iskandar Puteri", tooltip="Administrative Center", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

# RTS Terminal
folium.Marker([1.4580, 103.7610], popup="RTS Bukit Chagar Terminal", tooltip="🚆 RTS Terminal",
              icon=folium.Icon(color="red", icon="train", prefix="fa")).add_to(m)

# Display the map using streamlit-folium
st_data = st_folium(m, width=1200, height=500, returned_objects=[])

st.markdown("### Recent Activity Logs")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Active CCTV Feeds", value="142", delta="12 Online")
with col2:
    st.metric(label="Traffic Incidents", value="5", delta="-2 from yesterday", delta_color="inverse")
with col3:
    st.metric(label="Air Quality Index (AQI)", value="45", delta="Good")
