import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.parking_engine import get_live_occupancy, get_nearest_green_hub, generate_enforcement_log
import vision_engine

st.set_page_config(page_title="Smart Parking | PBT-Vision", layout="wide", initial_sidebar_state="expanded")

# ── Shared CSS ────────────────────────────────────────────────────────────────
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
    .glass-card { background: rgba(30,41,59,0.5); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem;
        margin-bottom: 1rem; }
    .glass-card:hover { box-shadow: 0 0 20px rgba(56,189,248,0.2); transition: all 0.3s ease; }
</style>
""", unsafe_allow_html=True)

st.title("🅿️ Urban Enforcement & Smart Parking")
st.markdown("Green Zone navigation, real-time occupancy monitoring, and autonomous enforcement.")

# ── Sidebar — Mode Toggle ────────────────────────────────────────────────────
with st.sidebar:
    st.header("🅿️ Parking Control")
    view_mode = st.radio("View Mode", ["🚗 Commuter", "🛡️ Authority"], index=0)
    st.markdown("---")
    if view_mode == "🚗 Commuter":
        st.subheader("📍 Your Location")
        user_loc = st.selectbox("Starting Point", [
            "JB City Center", "CIQ / Customs", "Taman Pelangi", "Taman Molek",
            "Skudai", "Iskandar Puteri", "Mount Austin"
        ])
        loc_map = {
            "JB City Center": (1.4927, 103.7414), "CIQ / Customs": (1.4635, 103.7639),
            "Taman Pelangi": (1.4850, 103.7560), "Taman Molek": (1.5320, 103.7860),
            "Skudai": (1.5370, 103.6550), "Iskandar Puteri": (1.4272, 103.6158),
            "Mount Austin": (1.5480, 103.7930),
        }
        user_coords = loc_map.get(user_loc, (1.4927, 103.7414))
    else:
        st.subheader("🔧 Enforcement Filters")
        severity_filter = st.multiselect("Severity", ["Low", "Medium", "High", "Critical"],
                                          default=["High", "Critical"])
    st.markdown("---")
    st.info("🛰️ IoT Sensors: Online\n\n📡 LoRaWAN: Connected")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🚗 Commuter":
    zones = get_live_occupancy()

    # ── Metrics Row ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    total_avail = sum(z["available"] for z in zones)
    green_hubs = [z for z in zones if z["type"] == "Green Hub"]
    c1.metric("Total Available Lots", f"{total_avail}", f"{len(zones)} zones")
    c2.metric("Green Hubs Open", f"{sum(1 for g in green_hubs if g['status']!='FULL')}/{len(green_hubs)}")
    c3.metric("Avg Green Hub Cost", f"RM {sum(g['hourly_rate'] for g in green_hubs)/len(green_hubs):.2f}/hr")
    c4.metric("Nearest Shuttle", f"~{min(g['shuttle_freq_min'] for g in green_hubs if g['has_shuttle'])} min")

    st.markdown("---")

    # ── Live Parking Map ──────────────────────────────────────────────────────
    st.subheader("🗺️ Live Parking Zone Map")
    m = folium.Map(location=[1.4800, 103.7200], zoom_start=12, tiles="cartodbdark_matter")

    for z in zones:
        popup_html = f"""
        <div style='font-family:Inter,sans-serif;min-width:180px'>
            <b>{z['name']}</b><br>
            Type: {z['type']}<br>
            Available: <b>{z['available']}/{z['total_lots']}</b><br>
            Rate: RM {z['hourly_rate']:.2f}/hr<br>
            Sensor: {z['sensor_type']}<br>
            {'🚐 Shuttle: Every '+str(z['shuttle_freq_min'])+' min' if z['has_shuttle'] else ''}
        </div>"""

        color = "#22c55e" if z["status"] == "AVAILABLE" else ("#f97316" if z["status"] == "LOW" else "#ef4444")
        folium.CircleMarker(
            location=z["coords"], radius=max(8, z["available"]//8),
            color=color, fill=True, fill_color=color, fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{z['name']}: {z['available']} lots ({z['status']})"
        ).add_to(m)

    # User location marker
    folium.Marker(
        location=list(user_coords), tooltip="📍 You are here",
        icon=folium.Icon(color="lightblue", icon="user", prefix="fa")
    ).add_to(m)

    # FIX: Use folium_static instead of st_folium to avoid serialization errors
    folium_static(m, width=1100, height=450)

    # ── Smart Reroute ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔄 Smart Green Hub Reroute")
    if st.button("🔍 Find Best Parking Option", use_container_width=True):
        reroute = get_nearest_green_hub(user_coords[0], user_coords[1])
        if "error" in reroute:
            st.error(reroute["error"])
        else:
            st.success(f"✅ Recommended: **{reroute['recommended_hub']}**")
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("Distance", f"{reroute['distance_km']} km")
            rc2.metric("Drive Time", f"{reroute['drive_time_min']} min")
            rc3.metric("Available Lots", reroute["available_lots"])
            rc4.metric("Savings", reroute["savings_vs_ciq"])

            if reroute["shuttle_available"]:
                st.info(f"🚐 **Shuttle to RTS**: {reroute['shuttle_frequency']} | "
                        f"Distance to terminal: {reroute['rts_connection']}")

    # ── Occupancy Chart ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Zone Occupancy Overview")
    fig = go.Figure()
    zone_names = [z["name"] for z in zones]
    fig.add_trace(go.Bar(name="Occupied", x=zone_names, y=[z["occupied"] for z in zones],
                         marker_color="#ef4444", opacity=0.8))
    fig.add_trace(go.Bar(name="Available", x=zone_names, y=[z["available"] for z in zones],
                         marker_color="#22c55e", opacity=0.8))
    fig.update_layout(barmode="stack", template="plotly_dark",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=350, margin=dict(t=30, b=80),
                      font=dict(family="Inter", color="#f8fafc"),
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTHORITY VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("🛡️ Autonomous Enforcement Dashboard")

    incidents = generate_enforcement_log(15)
    filtered = [inc for inc in incidents if inc["severity"] in severity_filter]

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Incidents", len(incidents))
    c2.metric("Critical", sum(1 for i in incidents if i["severity"] == "Critical"))
    c3.metric("Sent to PDRM", sum(1 for i in incidents if i["status"] == "Sent to PDRM"))
    c4.metric("Fines Issued", sum(1 for i in incidents if i["status"] == "Fine Issued"))

    # ── Incident Table ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Violation Log")
    if filtered:
        df = pd.DataFrame(filtered)
        df_display = df[["incident_id", "timestamp", "license_plate", "violation",
                         "location", "severity", "status", "confidence"]].copy()
        st.dataframe(df_display, use_container_width=True, hide_index=True,
                     column_config={
                         "incident_id": "ID", "timestamp": "Time", "license_plate": "Plate",
                         "violation": "Violation", "location": "Location",
                         "severity": "Severity", "status": "Status", "confidence": "AI Conf."
                     })
    else:
        st.info("No incidents matching the selected severity filters.")

    # ── Enforcement Map ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Violation Locations")
    em = folium.Map(location=[1.4800, 103.7300], zoom_start=12, tiles="cartodbdark_matter")
    sev_colors = {"Low": "green", "Medium": "orange", "High": "red", "Critical": "darkred"}
    for inc in filtered:
        folium.Marker(
            location=inc["coords"],
            tooltip=f"{inc['violation']} — {inc['license_plate']}",
            icon=folium.Icon(color=sev_colors.get(inc["severity"], "gray"), icon="exclamation-sign")
        ).add_to(em)
    
    # FIX: Use folium_static instead of st_folium
    folium_static(em, width=1100, height=400)

    # ── CCTV Analysis ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔍 CCTV AI Analysis (Gemini 1.5 Flash)")
    st.markdown("Upload a CCTV frame to detect parking violations and empty lots.")
    uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded CCTV Frame", use_column_width=True)
        if st.button("⚡ Analyze with Gemini"):
            with st.spinner("Analyzing with Gemini 1.5 Flash..."):
                os.makedirs(os.path.join("data", "cctv_feeds"), exist_ok=True)
                temp_path = os.path.join("data", "cctv_feeds",
                                         "temp_upload" + os.path.splitext(uploaded_file.name)[1])
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                try:
                    results = vision_engine.analyze_cctv_image(temp_path)
                    if "error" in results:
                        st.error(results["error"])
                    else:
                        st.subheader("Analysis Results")
                        ca, cb = st.columns(2)
                        with ca:
                            score = results.get("congestion_impact_score", "N/A")
                            st.metric("Congestion Impact Score", f"{score}/10")
                        with cb:
                            st.json(results)
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
