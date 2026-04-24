import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.bus_intelligence import (
    predict_pob, get_all_stations_overview, generate_dispatch_alerts,
    get_historical_trend, get_bus_stats, BUS_STATIONS
)

st.set_page_config(page_title="Bus Intelligence | PBT-Vision", layout="wide", initial_sidebar_state="expanded")

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

st.title("🚌 Predictive Bus Intelligence")
st.markdown("Live **Probability of Boarding (PoB)** scores, queue monitoring, and dynamic dispatch recommendations.")

with st.sidebar:
    st.header("🚌 Bus Control")
    view_mode = st.radio("View Mode", ["🧑 Commuter", "🏛️ Authority"], index=0)
    st.markdown("---")
    bus_stats = get_bus_stats()
    st.metric("Stations Monitored", bus_stats["total_stations_monitored"])
    st.metric("Active Routes", bus_stats["active_routes"])
    st.metric("Avg City PoB", bus_stats["avg_pob_city"])
    st.metric("Surge Alerts Today", bus_stats["surge_alerts_today"])
    st.markdown("---")
    st.info("📹 ITMax CCTV: 2,500+ feeds\n\n🤖 BigQuery ML: Active")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🧑 Commuter":
    st.subheader("🔍 Search Your Commute")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        station = st.selectbox("Select Station", [s["name"] for s in BUS_STATIONS])
    with sc2:
        travel_time = st.time_input("Travel Time", value=None)
    with sc3:
        day = st.selectbox("Day", ["Weekday", "Saturday", "Sunday"])

    station_obj = next((s for s in BUS_STATIONS if s["name"] == station), BUS_STATIONS[0])

    if travel_time and st.button("🔍 Check Probability of Boarding", use_container_width=True):
        time_str = travel_time.strftime("%H:%M")
        result = predict_pob(station_obj["id"], time_str, day)

        if "error" in result:
            st.error(result["error"])
        elif not result["routes"]:
            st.warning("No routes serve this station at the selected time.")
        else:
            st.success(f"📍 **{result['station']}** — {result['target_time']} ({result['day']})")

            for route in result["routes"]:
                with st.container():
                    st.markdown(f"""
                    <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.1);
                                border-radius:12px;padding:1.2rem;margin-bottom:1rem;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <h3 style="margin:0;color:#f8fafc !important;">🚌 {route['route_name']}</h3>
                                <p style="color:#94a3b8;margin:0.3rem 0 0 0;">Route {route['route_id']} • Every {route['frequency_min']} min</p>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:2.5rem;font-weight:bold;color:{route['pob_color']};">
                                    {route['pob_score']}%
                                </div>
                                <div style="color:{route['pob_color']};font-size:0.9rem;">PoB: {route['pob_label']}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    rc1, rc2, rc3, rc4 = st.columns(4)
                    rc1.metric("Next Bus", f"{route['next_bus_min']} min")
                    rc2.metric("Bus Occupancy", f"{route['bus_occupancy_pct']}%")
                    rc3.metric("Seats Left", route["space_available"])
                    rc4.metric("Queue at Station", f"{route['queue_count']} people")

            # ── Historical Trend ──────────────────────────────────────────
            st.markdown("---")
            st.subheader("📈 Historical PoB Trend (Today)")
            trend = get_historical_trend(station_obj["id"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[t["hour"] for t in trend], y=[t["pob"] for t in trend],
                mode="lines+markers", name="PoB %",
                line=dict(color="#38bdf8", width=3), marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(56,189,248,0.1)"
            ))
            fig.add_trace(go.Bar(
                x=[t["hour"] for t in trend], y=[t["queue"] for t in trend],
                name="Queue Count", marker_color="rgba(249,115,22,0.5)", yaxis="y2"
            ))
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=350, margin=dict(t=30, b=50),
                font=dict(family="Inter", color="#f8fafc"),
                yaxis=dict(title="PoB %", range=[0, 100]),
                yaxis2=dict(title="Queue", overlaying="y", side="right", range=[0, 50]),
                legend=dict(orientation="h", y=1.15),
            )
            st.plotly_chart(fig, use_container_width=True)

    elif not travel_time:
        st.info("👆 Select a travel time and click 'Check Probability of Boarding' to get predictions.")

# ══════════════════════════════════════════════════════════════════════════════
# AUTHORITY VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("🏛️ City-Wide Bus Station Overview")

    overview = get_all_stations_overview()

    # ── Metrics Row ───────────────────────────────────────────────────────────
    oc1, oc2, oc3, oc4 = st.columns(4)
    surge_count = sum(1 for s in overview if "Surge" in s["status"])
    oc1.metric("Stations in Surge", surge_count)
    oc2.metric("Avg Queue City-Wide", f"{sum(s['queue_count'] for s in overview)//len(overview)}")
    oc3.metric("Relief Buses Deployed", bus_stats["relief_buses_deployed"])
    oc4.metric("Commuters Served Today", f"{bus_stats['commuters_served_today']:,}")

    # ── Station Map ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Live Station Map")
    sm = folium.Map(location=[1.5000, 103.7300], zoom_start=11, tiles="cartodbdark_matter")
    for s in overview:
        color = "#ef4444" if "Surge" in s["status"] else ("#f97316" if "Busy" in s["status"] else "#22c55e")
        folium.CircleMarker(
            location=s["coords"], radius=max(8, s["queue_count"] // 2),
            color=color, fill=True, fill_color=color, fill_opacity=0.5,
            tooltip=f"{s['station_name']}: Queue={s['queue_count']} | PoB={s['avg_pob']}% | {s['status']}"
        ).add_to(sm)
        if s["is_rts"]:
            folium.Marker(s["coords"], tooltip="🚆 RTS Terminal",
                          icon=folium.Icon(color="red", icon="train", prefix="fa")).add_to(sm)
    
    # FIX: Use folium_static
    folium_static(sm, width=1100, height=400)

    # ── Station Table ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Station Status Table")
    df = pd.DataFrame(overview)
    df_show = df[["station_name", "queue_count", "avg_pob", "routes_served", "status"]].copy()
    df_show.columns = ["Station", "Queue", "Avg PoB %", "Routes", "Status"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # ── Dispatch Alerts ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🚨 Dynamic Dispatch Alerts")
    alerts = generate_dispatch_alerts()
    if alerts:
        for a in alerts:
            sev_icon = "🔴" if a["severity"] == "Critical" else "🟡"
            st.markdown(f"""
            <div style="background:rgba(30,41,59,0.5);border:1px solid {'rgba(239,68,68,0.4)' if a['severity']=='Critical' else 'rgba(249,115,22,0.4)'};
                        border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <b style="color:#f8fafc;">{sev_icon} {a['station']}</b>
                        <p style="color:#94a3b8;margin:0.3rem 0 0 0;">
                            Predicted queue: <b>{a['predicted_queue']}</b> at <b>{a['surge_time']}</b> |
                            Confidence: {a['confidence']}
                        </p>
                    </div>
                    <div style="color:#38bdf8;font-size:0.85rem;">{a['recommended_action']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No surge alerts at this time.")
