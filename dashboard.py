import streamlit as st
import pandas as pd
import os, sys
from datetime import datetime
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# Import modules to get real stats
from modules.carbon_ledger import calculate_city_impact
from modules.bus_intelligence import get_bus_stats
from modules.parking_engine import get_live_occupancy

st.set_page_config(page_title="UrbanFlow | Smart City Orchestrator", layout="wide")

# ── Custom CSS for the Logo Page ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@800&display=swap');
    .stApp {
        background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
    }
    .hero-container {
        text-align: center;
        padding: 1.5rem 1rem;
    }
    .logo-img {
        max-width: 300px;
        margin-bottom: 2rem;
        filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.4));
    }
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 5rem;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(to right, #38bdf8, #818cf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.2);
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.4rem;
        max-width: 700px;
        margin: 0 auto 3rem auto;
    }
    .stat-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        border-color: #38bdf8;
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(56, 189, 248, 0.15);
    }
    .stat-val {
        font-size: 2.5rem;
        font-weight: bold;
        color: #f8fafc;
    }
    .stat-label {
        color: #38bdf8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(15px);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("<div style='text-align:center; padding: 1rem;'><h2 style='color:#38bdf8;'>🏙️ UrbanFlow</h2></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.info("Welcome. Navigate through the core mobility modules above.")
st.sidebar.markdown("---")
st.sidebar.caption(f"System Time: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.caption("Node: JS-SEZ-JB-01")

# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown("<div class='hero-container'>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>URBAN FLOW</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Next-generation AI orchestration for the Johor-Singapore Special Economic Zone. Seamless mobility, sustainable growth.</div>", unsafe_allow_html=True)

# Fetch real data for the "Big Numbers"
city_impact = calculate_city_impact()
bus_stats = get_bus_stats()
parking_zones = get_live_occupancy()
total_avail_lots = sum(z["available"] for z in parking_zones)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-val'>{city_impact['co2_prevented_today_tonnes']} t</div>
        <div class='stat-label'>🌱 CO₂ Prevented Today</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-val'>{total_avail_lots}</div>
        <div class='stat-label'>🅿️ Smart Lots Available</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-val'>{bus_stats['active_routes']}</div>
        <div class='stat-label'>🚌 Active Transit Lines</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-val'>98.2%</div>
        <div class='stat-label'>🤖 AI Core Health</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center; color:#64748b;'>Select a module from the sidebar to begin orchestration.</div>", unsafe_allow_html=True)
