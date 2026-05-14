import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.carpool_engine import (
    match_carpool, get_demand_clusters, get_carpool_stats,
    NEIGHBORHOODS, RTS_SCHEDULE
)
from modules.ui_components import inject_side_nav, inject_global_ui, synthetic_fluctuation

st.set_page_config(page_title="Carpool Agent | PBT-Vision", layout="wide", initial_sidebar_state="expanded")
inject_side_nav()
inject_global_ui("carpool")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;800&family=JetBrains+Mono:wght@700&display=swap');
    
    .stApp {
        background-color: #050b14;
        background-image: 
            linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
        background-size: 50px 50px;
        background-position: center;
        animation: pan 60s linear infinite;
    }
    @keyframes pan {
        from { background-position: 0 0; }
        to { background-position: 500px 500px; }
    }

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

    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Carpool Agent</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-top:-0.5rem; margin-bottom:2rem;'>Intelligent carpool matching synchronized with RTS train schedules for first-mile/last-mile optimization.</p>", unsafe_allow_html=True)

view_mode = "🧑 Commuter" if st.session_state.get("global_view_mode", "Commuter") == "Commuter" else "🏛️ Authority"

stats = get_carpool_stats()
active_carpools = synthetic_fluctuation(stats["active_carpools_today"], 0.05, "carpool_active")
commuters_matched = synthetic_fluctuation(stats["commuters_matched"], 0.04, "carpool_matched")
on_time_rate = synthetic_fluctuation(stats["on_time_rate"], 0.01, "carpool_ontime")

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Carpools Today", int(active_carpools) if isinstance(active_carpools, float) else active_carpools)
c2.metric("Commuters Matched", int(commuters_matched) if isinstance(commuters_matched, float) else commuters_matched)
c3.metric("On-Time Rate", on_time_rate)
with c4:
    st.info("🚆 RTS Link: Online\n\n🛰️ Routes API: Connected")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🧑 Commuter":
    st.subheader("🎯 Set Your Target Train")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        neighborhood = st.selectbox("Your Neighborhood", [n["name"] for n in NEIGHBORHOODS])
    with col_input2:
        # Show a subset of trains for usability
        morning_trains = [t for t in RTS_SCHEDULE if t.startswith(("07", "08", "09"))]
        target_train = st.selectbox("Target RTS Train", morning_trains, index=3)
    if st.button("🔍 Find Carpool Matches", use_container_width=True):
        result = match_carpool(neighborhood, target_train)

        if "error" in result:
            st.error(result["error"])
        elif not result["matches"]:
            st.warning("No matches found. Try choosing a different train time or neighborhood.")
        else:
            # ── Match Results ─────────────────────────────────────────────
            st.success(f"✅ Found {len(result['matches'])} matches for the **{result['target_train']}** RTS train!")

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Target Train", result["target_train"])
            mc2.metric("Arrive at Terminal", result["arrival_at_terminal"])
            mc3.metric("Total Passengers", result["total_passengers"])
            mc4.metric("CO₂ Saved", f"{result['cost_savings']['co2_saved_kg']} kg")

            st.markdown("---")

            # ── Pickup Schedule ───────────────────────────────────────────
            st.subheader("📋 Pickup Schedule")
            schedule_data = []
            for p in result["pickup_schedule"]:
                schedule_data.append({
                    "Order": f"🔵 Stop {p['order']}",
                    "Passenger": p["name"],
                    "Neighborhood": p["neighborhood"],
                    "Pickup Time": p["pickup_time"],
                })
            st.table(pd.DataFrame(schedule_data))

            # ── Matched Commuters ─────────────────────────────────────────
            st.subheader("👥 Matched Commuters")
            for match in result["matches"]:
                with st.expander(f"🚘 {match['name']} — {match['neighborhood']} ({match['compatibility_score']}% match)"):
                    ec1, ec2, ec3, ec4 = st.columns(4)
                    ec1.metric("Distance", f"{match['distance_km']} km")
                    ec2.metric("Rating", f"⭐ {match['rating']}")
                    ec3.metric("Trips Done", match["trips_completed"])
                    ec4.metric("Seats", match["seats_available"])
                    st.caption(f"Target train: {match['target_train']} | Workplace: {match['workplace']}")

            # ── Cost Savings ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("💰 Trip Savings")
            savings = result["cost_savings"]
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Solo Cost", f"RM {savings['solo_cost_rm']}")
            sc2.metric("Shared Cost", f"RM {savings['shared_cost_rm']}")
            sc3.metric("You Save", f"RM {savings['savings_rm']}", delta=f"-{savings['co2_saved_kg']} kg CO₂" if 'co2_saved_kg' in savings else "0 kg CO2")

            # ── Route Map ─────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("🗺️ Pickup Route")
            rm = folium.Map(location=[1.4900, 103.7400], zoom_start=12, tiles="cartodbdark_matter")
            # RTS Terminal marker
            folium.Marker([1.4580, 103.7610], tooltip="🚆 RTS Bukit Chagar Terminal",
                          icon=folium.Icon(color="red", icon="train", prefix="fa")).add_to(rm)
            # Match markers
            route_coords = []
            for match in result["matches"]:
                folium.Marker(match["home_coords"], tooltip=f"📍 {match['name']} ({match['neighborhood']})",
                              icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(rm)
                route_coords.append(match["home_coords"])
            route_coords.append([1.4580, 103.7610])  # End at RTS
            if len(route_coords) > 1:
                folium.PolyLine(route_coords, color="#38bdf8", weight=4, opacity=0.8,
                                dash_array="10").add_to(rm)
            
            # FIX: Use folium_static for stability
            folium_static(rm, width=1100, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# AUTHORITY VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("🏛️ Social Mobility Clusters & Demand Analysis")

    clusters = get_demand_clusters()

    # ── Metrics ───────────────────────────────────────────────────────────────
    ac1, ac2, ac3, ac4 = st.columns(4)
    ac1.metric("Neighborhoods Tracked", synthetic_fluctuation(len(clusters), 0.02, "carpool_neighborhoods"))
    ac2.metric("Total Commuters", synthetic_fluctuation(sum(c["commuter_count"] for c in clusters), 0.03, "carpool_total_commuters"))
    ac3.metric("Avg Peak Hour", f"{sum(c['avg_target_hour'] for c in clusters)/len(clusters):.0f}:00")
    ac4.metric("CO₂ Saved Today", synthetic_fluctuation(f"{stats['co2_saved_today_kg']} kg", 0.04, "carpool_co2_saved"))

    # ── Demand Heatmap ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Carpool Demand Heat Map")
    hm = folium.Map(location=[1.5000, 103.7300], zoom_start=11, tiles="cartodbdark_matter")
    max_count = max(c["commuter_count"] for c in clusters)
    for c in clusters:
        intensity = c["commuter_count"] / max_count
        color = f"#ef4444" if intensity > 0.7 else ("#f97316" if intensity > 0.4 else "#22c55e")
        radius = max(10, int(intensity * 30))
        folium.CircleMarker(
            location=c["coords"], radius=radius, color=color, fill=True,
            fill_color=color, fill_opacity=0.5,
            tooltip=f"{c['neighborhood']}: {c['commuter_count']} commuters (Density: {c['demand_density']})"
        ).add_to(hm)
    
    # FIX: Use folium_static for stability
    folium_static(hm, width=1100, height=400)

    # ── Cluster Table ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Demand by Neighborhood")
    df_clusters = pd.DataFrame(clusters)
    df_display = df_clusters[["neighborhood", "commuter_count", "demand_density",
                               "avg_target_hour", "top_workplace"]].copy()
    df_display.columns = ["Neighborhood", "Commuters", "Demand Density", "Avg Peak Hour", "Top SG Workplace"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ── Suggested Shuttle Routes ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🚐 Suggested New Shuttle Routes")
    top_clusters = clusters[:3]
    for i, c in enumerate(top_clusters):
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.1);
                    border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
            <h4 style="margin:0;color:#38bdf8 !important;">Route Suggestion #{i+1}: {c['neighborhood']} → RTS Terminal</h4>
            <p style="color:#94a3b8;margin:0.5rem 0 0 0;">
                Demand: <b>{c['commuter_count']}</b> commuters | Peak: <b>{c['avg_target_hour']:.0f}:00</b> |
                Top Destination: <b>{c['top_workplace']}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
