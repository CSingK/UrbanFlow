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
from modules.ui_components import inject_side_nav, inject_global_ui, synthetic_fluctuation

st.set_page_config(page_title="UrbanFlow | Smart City Orchestrator", layout="wide")

# Inject Custom Side Nav
inject_side_nav("dashboard")
inject_global_ui("dashboard")

# ── Custom CSS for the Logo Page ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;800&family=JetBrains+Mono:wght@700&display=swap');
    
    .stApp {
        background-color: #050b14;
        background-image: 
            linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
        background-size: 40px 40px;
        background-position: center top;
        animation: panGrid 20s linear infinite;
    }
    
    @keyframes panGrid {
        0% { background-position: 0 0; }
        100% { background-position: 0 40px; }
    }

    .hero-container {
        text-align: center;
        padding: 1rem 1rem 2rem 1rem;
        position: relative;
    }
    
    .radar-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 2px solid rgba(56, 189, 248, 0.3);
        margin: 0 auto 2rem auto;
        position: relative;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.2), inset 0 0 20px rgba(56, 189, 248, 0.1);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .radar-circle::before {
        content: '';
        position: absolute;
        width: 100%; height: 100%;
        border-radius: 50%;
        border-top: 2px solid #38bdf8;
        animation: spin 3s linear infinite;
        filter: drop-shadow(0 0 10px #38bdf8);
    }
    .radar-circle::after {
        content: 'AI';
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2rem;
        color: #e0f2fe;
        text-shadow: 0 0 15px #38bdf8;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 6.5rem;
        font-weight: 800;
        letter-spacing: -3px;
        background: linear-gradient(to right, #38bdf8, #818cf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 40px rgba(56, 189, 248, 0.3);
        line-height: 1.1;
    }
    .sub-title {
        color: #94a3b8;
        font-family: 'Outfit', sans-serif;
        font-size: 1.3rem;
        max-width: 800px;
        margin: 0 auto 4rem auto;
        line-height: 1.6;
        font-weight: 400;
    }
    .stat-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-top: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 20px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }
    .stat-card::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle at center, rgba(56, 189, 248, 0.08) 0%, transparent 50%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .stat-card:hover::after {
        opacity: 1;
    }
    .stat-card:hover {
        border-color: rgba(56, 189, 248, 0.8);
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 30px 60px rgba(56, 189, 248, 0.2), inset 0 0 20px rgba(56, 189, 248, 0.05);
    }
    .stat-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        font-weight: 700;
        color: #f8fafc;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
        margin-bottom: 0.5rem;
    }
    .stat-label {
        color: #7dd3fc;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)



# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown("<div class='hero-container'>", unsafe_allow_html=True)

st.markdown("<div class='radar-circle gsap-hero'></div>", unsafe_allow_html=True)
st.markdown("<div class='main-title gsap-hero'>URBAN FLOW</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title gsap-hero'>Next-generation AI orchestration for the Johor-Singapore Special Economic Zone. Seamless mobility, sustainable growth.</div>", unsafe_allow_html=True)

# Fetch real data for the "Big Numbers"
city_impact = calculate_city_impact()
bus_stats = get_bus_stats()
parking_zones = get_live_occupancy()
total_avail_lots = synthetic_fluctuation(sum(z["available"] for z in parking_zones), 0.04, "dash_total_lots")
co2_tonnes = synthetic_fluctuation(city_impact['co2_prevented_today_tonnes'], 0.03, "dash_co2_tonnes")
active_routes = synthetic_fluctuation(bus_stats['active_routes'], 0.03, "dash_active_routes")
core_health = synthetic_fluctuation(98.2, 0.01, "dash_core_health")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='stat-card gsap-card'>
        <div class='stat-val' id='val-co2' data-base='{co2_tonnes:.2f}'>{co2_tonnes:.2f} t</div>
        <div class='stat-label'>CO₂ Prevented</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stat-card gsap-card'>
        <div class='stat-val' id='val-lots' data-base='{total_avail_lots}'>{total_avail_lots}</div>
        <div class='stat-label'>Smart Lots Avail</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stat-card gsap-card'>
        <div class='stat-val' id='val-routes' data-base='{active_routes}'>{active_routes}</div>
        <div class='stat-label'>Active Lines</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='stat-card gsap-card'>
        <div class='stat-val' id='val-health' data-base='{core_health:.1f}'>{core_health:.1f}%</div>
        <div class='stat-label'>AI Core Health</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center; color:#64748b; font-family: Outfit; font-weight: 600; letter-spacing: 1px;' class='gsap-hero'>SELECT A MODULE FROM THE SIDEBAR TO BEGIN ORCHESTRATION</div>", unsafe_allow_html=True)

import streamlit.components.v1 as components
components.html("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script>
    (function() {
        const parentDoc = window.parent.document;
        
        // 1. GSAP Entrance Animations
        const runAnimations = () => {
            const gsapRef = window.gsap || window.parent.gsap;
            if (!gsapRef) return;
            
            const heroes = parentDoc.querySelectorAll('.gsap-hero');
            const cards = parentDoc.querySelectorAll('.stat-card');
            
            gsapRef.fromTo(heroes, 
                { y: 30, opacity: 0, scale: 0.95 }, 
                { y: 0, opacity: 1, scale: 1, duration: 0.8, stagger: 0.15, ease: 'back.out(1.5)', delay: 0.1 }
            );
            
            gsapRef.fromTo(cards, 
                { y: 50, opacity: 0, rotationX: 10 }, 
                { y: 0, opacity: 1, rotationX: 0, duration: 0.8, stagger: 0.1, ease: 'power3.out', delay: 0.4 }
            );
        };
        
        // Run slightly delayed to ensure DOM is ready
        setTimeout(runAnimations, 150);

        // 2. Live Data Fluctuation
        setInterval(() => {
            const co2 = parentDoc.getElementById('val-co2');
            const lots = parentDoc.getElementById('val-lots');
            const health = parentDoc.getElementById('val-health');
            
            if (co2) {
                let base = parseFloat(co2.getAttribute('data-base'));
                let tick = base + (Math.random() * 0.4 - 0.2);
                co2.innerHTML = tick.toFixed(2) + ' t';
            }
            if (lots) {
                let base = parseInt(lots.getAttribute('data-base'));
                let tick = base + Math.floor(Math.random() * 5 - 2);
                lots.innerHTML = Math.max(0, tick);
            }
            if (health) {
                let base = parseFloat(health.getAttribute('data-base'));
                let tick = base + (Math.random() * 0.2 - 0.1);
                health.innerHTML = Math.min(100, Math.max(90, tick)).toFixed(1) + '%';
            }
        }, 2000);

    })();
</script>
""", height=0)

