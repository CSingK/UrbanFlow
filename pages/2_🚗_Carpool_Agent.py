import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.carpool_engine import (
    match_carpool, get_demand_clusters, get_carpool_stats,
    NEIGHBORHOODS, RTS_SCHEDULE
)

st.set_page_config(page_title="Carpool Agent | PBT-Vision", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a, #1e293b); }
    [data-testid="stSidebar"] { background: rgba(15,23,42,0.4); backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="metric-container"] { background: rgba(30,41,59,0.5) !important;
        backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div[data-testid="metric-container"]:hover { box-shadow: 0 0 15px rgba(56,189,248,0.3);
        transition: all 0.3s ease; }
    h1,h2,h3,h4,h5,h6 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("🚗 AI-Synchronized Carpool Agent")
st.markdown("Intelligent carpool matching synchronized with RTS train schedules for first-mile/last-mile optimization.")

with st.sidebar:
    st.header("🚗 Carpool Control")
    view_mode = st.radio("View Mode", ["🧑 Commuter", "🏛️ Authority"], index=0)
    st.markdown("---")
    stats = get_carpool_stats()
    st.metric("Active Carpools Today", stats["active_carpools_today"])
    st.metric("Commuters Matched", stats["commuters_matched"])
    st.metric("On-Time Rate", stats["on_time_rate"])
    st.markdown("---")
    st.info("🚆 RTS Link: Online\n\n🛰️ Routes API: Connected")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🧑 Commuter":
    st.subheader("🎯 Set Your Target Train")

    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        neighborhood = st.selectbox("Your Neighborhood", [n["name"] for n in NEIGHBORHOODS])
    with col_input2:
        # Show a subset of trains for usability
        morning_trains = [t for t in RTS_SCHEDULE if t.startswith(("07", "08", "09"))]
        target_train = st.selectbox("Target RTS Train", morning_trains, index=3)
    with col_input3:
        flexibility = st.slider("Flexibility (± minutes)", 5, 30, 15)

    if st.button("🔍 Find Carpool Matches", use_container_width=True):
        result = match_carpool(neighborhood, target_train, flexibility)

        if "error" in result:
            st.error(result["error"])
        elif not result["matches"]:
            st.warning("No matches found. Try increasing flexibility or choosing a different time.")
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
            sc3.metric("You Save", f"RM {savings['savings_rm']}", delta=f"-{savings['co2_saved_kg']} kg CO₂")

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
            st_folium(rm, width=1200, height=400, returned_objects=[])

# ══════════════════════════════════════════════════════════════════════════════
# AUTHORITY VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("🏛️ Social Mobility Clusters & Demand Analysis")

    clusters = get_demand_clusters()

    # ── Metrics ───────────────────────────────────────────────────────────────
    ac1, ac2, ac3, ac4 = st.columns(4)
    ac1.metric("Neighborhoods Tracked", len(clusters))
    ac2.metric("Total Commuters", sum(c["commuter_count"] for c in clusters))
    ac3.metric("Avg Peak Hour", f"{sum(c['avg_target_hour'] for c in clusters)/len(clusters):.0f}:00")
    ac4.metric("CO₂ Saved Today", f"{stats['co2_saved_today_kg']} kg")

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
    st_folium(hm, width=1200, height=400, returned_objects=[])

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
