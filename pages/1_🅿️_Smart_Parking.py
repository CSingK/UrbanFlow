import base64
import math
import os
import sys
from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import streamlit_folium as streamlit_folium_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.parking_engine import get_live_occupancy, get_nearest_green_hub, generate_enforcement_log
from modules.ui_components import inject_side_nav

st.set_page_config(page_title="Smart Parking | PBT-Vision", layout="wide", initial_sidebar_state="expanded")
inject_side_nav()

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_MODEL_PATH = ASSET_DIR / "parking_lot_uf.glb"


def _zone_status_color(status: str) -> str:
    if status == "AVAILABLE":
        return "#22c55e"
    if status == "LOW":
        return "#f97316"
    return "#ef4444"


def _extract_click_coords(map_state: dict) -> tuple[float | None, float | None]:
    clicked = map_state.get("last_object_clicked") or map_state.get("last_clicked")
    if isinstance(clicked, dict):
        return clicked.get("lat"), clicked.get("lng")
    if isinstance(clicked, (list, tuple)) and len(clicked) >= 2:
        return clicked[0], clicked[1]
    return None, None


def _find_nearest_zone(zones: list[dict], lat: float | None, lng: float | None) -> dict | None:
    if lat is None or lng is None:
        return None

    nearest_zone = None
    nearest_distance = float("inf")
    for zone in zones:
        zone_lat, zone_lng = zone["coords"]
        distance = math.sqrt((zone_lat - lat) ** 2 + (zone_lng - lng) ** 2)
        if distance < nearest_distance:
            nearest_zone = zone
            nearest_distance = distance

    if nearest_distance > 0.01:
        return None
    return nearest_zone


def _load_model_bytes(uploaded_model):
    if uploaded_model is not None:
        return uploaded_model.getvalue(), uploaded_model.name
    if DEFAULT_MODEL_PATH.exists():
        return DEFAULT_MODEL_PATH.read_bytes(), DEFAULT_MODEL_PATH.name
    return None, None


def _render_model_view(model_bytes: bytes, zone: dict) -> None:
    encoded_model = base64.b64encode(model_bytes).decode("ascii")
    empty_pct = (zone["available"] / zone["total_lots"] * 100) if zone["total_lots"] else 0
    green_intensity = min(empty_pct / 100 * 0.6, 0.6)
    components.html(
        f"""
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        <style>
            .viewer-shell {{
                position: relative;
                border-radius: 20px;
                overflow: hidden;
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.96));
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
            }}
            .viewer-badge {{
                position: absolute;
                left: 16px;
                top: 16px;
                z-index: 2;
                padding: 10px 14px;
                border-radius: 999px;
                font-family: Inter, sans-serif;
                font-size: 12px;
                font-weight: 700;
                color: #e2e8f0;
                background: rgba(15, 23, 42, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(12px);
            }}
            .empty-indicator {{
                position: absolute;
                bottom: 16px;
                left: 16px;
                z-index: 2;
                padding: 8px 12px;
                border-radius: 999px;
                font-family: Inter, sans-serif;
                font-size: 11px;
                font-weight: 600;
                color: #000;
                background: rgba(34, 197, 94, 0.9);
                border: 1px solid rgba(34, 197, 94, 1);
                backdrop-filter: blur(12px);
                box-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
            }}
            model-viewer {{
                width: 100%;
                height: 540px;
                background: radial-gradient(circle at top, rgba(56, 189, 248, 0.14), rgba(15, 23, 42, 0.96));
                filter: drop-shadow(0 0 25px rgba(34, 197, 94, {green_intensity})) brightness(1.1);
                transition: filter 0.3s ease;
            }}
            model-viewer:hover {{
                filter: drop-shadow(0 0 35px rgba(34, 197, 94, {green_intensity + 0.1})) brightness(1.15);
            }}
        </style>
        <div class="viewer-shell">
            <div class="viewer-badge">
                {zone["name"]} · {zone["occupied"]} occupied, {zone["available"]} empty
            </div>
            <div class="empty-indicator">
                🟢 {empty_pct:.0f}% Empty Parking
            </div>
            <model-viewer
                src="data:model/gltf-binary;base64,{encoded_model}"
                camera-controls
                auto-rotate
                shadow-intensity="1"
                exposure="1.05"
                interaction-prompt="none"
                environment-image="neutral"
                ar
                ar-modes="webxr scene-viewer quick-look"
            ></model-viewer>
        </div>
        """,
        height=580,
    )


def _safe_st_folium(
    fig,
    key: str | None = None,
    height: int = 700,
    width: int | None = 500,
    returned_objects=None,
    zoom: int | None = None,
    center: tuple[float, float] | None = None,
    feature_group_to_add=None,
    return_on_hover: bool = False,
    use_container_width: bool = False,
    layer_control=None,
    pixelated: bool = False,
    debug: bool = False,
    render: bool = True,
    wrap_longitude: bool = False,
):
    if use_container_width:
        width = None

    folium_map = fig
    if render:
        if isinstance(fig, folium.plugins.DualMap):
            folium_map.render()
        else:
            folium_map.get_root().render()

    if not isinstance(fig, (folium.Map, folium.plugins.DualMap)):
        folium_map = next(iter(fig._children.values()))

    folium_map.render()

    html = streamlit_folium_module._get_html(folium_map)
    header = streamlit_folium_module._get_header(folium_map)
    leaflet = streamlit_folium_module._get_map_string(folium_map)
    m_id = streamlit_folium_module.get_full_id(folium_map)

    def bounds_to_dict(bounds_list):
        southwest, northeast = bounds_list
        return {
            "_southWest": {"lat": southwest[0], "lng": southwest[1]},
            "_northEast": {"lat": northeast[0], "lng": northeast[1]},
        }

    try:
        bounds = folium_map.get_bounds()
    except AttributeError:
        bounds = [[None, None], [None, None]]

    defaults = {
        "last_clicked": None,
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_object_clicked_popup": None,
        "all_drawings": None,
        "last_active_drawing": None,
        "bounds": bounds_to_dict(bounds),
        "zoom": folium_map.options.get("zoom") if hasattr(folium_map, "options") else {},
        "last_circle_radius": None,
        "last_circle_polygon": None,
        "selected_layers": None,
        "selected_tags": None,
        "last_geocoder_result": None,
    }

    defaults = {k: v for k, v in defaults.items() if returned_objects is None or k in returned_objects}

    feature_group_string = None
    if feature_group_to_add is not None:
        if isinstance(feature_group_to_add, folium.FeatureGroup):
            feature_group_to_add = [feature_group_to_add]
        feature_group_string = ""
        for idx, feature_group in enumerate(feature_group_to_add):
            feature_group_string += streamlit_folium_module._get_feature_group_string(
                feature_group,
                map=folium_map,
                idx=idx,
            )

    layer_control_string = None
    if layer_control is not None:
        layer_control_string = streamlit_folium_module._get_layer_control_string(layer_control, folium_map)

    if debug:
        with st.expander("Show generated code"):
            if html:
                st.info("HTML:")
                st.code(html)
            if header:
                st.info("HEADER:")
                st.code(header)
            st.info("Main Map Leaflet js:")
            st.code(leaflet)
            if feature_group_string is not None:
                st.info("Feature group js:")
                st.code(feature_group_string)
            if layer_control_string is not None:
                st.info("Layer control js:")
                st.code(layer_control_string)

    css_links = []
    js_links = []

    def walk(fig_obj):
        if isinstance(fig_obj, streamlit_folium_module.branca.colormap.ColorMap):
            yield fig_obj
        if isinstance(fig_obj, folium.plugins.DualMap):
            yield from walk(fig_obj.m1)
            yield from walk(fig_obj.m2)
        if isinstance(fig_obj, folium.elements.JSCSSMixin):
            yield fig_obj
        if hasattr(fig_obj, "_children"):
            for child in fig_obj._children.values():
                yield from walk(child)

    for elem in walk(folium_map):
        if isinstance(elem, streamlit_folium_module.branca.colormap.ColorMap):
            js_links.insert(0, "https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js")
            js_links.insert(0, "https://d3js.org/d3.v4.min.js")
        css_links.extend([href for _, href in getattr(elem, "default_css", [])])
        js_links.extend([src for _, src in getattr(elem, "default_js", [])])

    css_links = list(dict.fromkeys(css_links))
    js_links = list(dict.fromkeys(js_links))
    hash_key = streamlit_folium_module.generate_js_hash(leaflet, key, return_on_hover)

    return streamlit_folium_module._component_func(
        script=leaflet,
        header=header,
        html=html,
        id=m_id,
        key=hash_key,
        height=height,
        width=width,
        returned_objects=returned_objects,
        default=defaults,
        zoom=zoom,
        center=center,
        feature_group=feature_group_string,
        return_on_hover=return_on_hover,
        layer_control=layer_control_string,
        pixelated=pixelated,
        css_links=css_links,
        js_links=js_links,
        wrap_longitude=wrap_longitude,
    )

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
        user_loc = st.selectbox(
            "Starting Point",
            [
                "JB City Center",
                "CIQ / Customs",
                "Taman Pelangi",
                "Taman Molek",
                "Skudai",
                "Iskandar Puteri",
                "Mount Austin",
            ],
        )
        loc_map = {
            "JB City Center": (1.4927, 103.7414),
            "CIQ / Customs": (1.4635, 103.7639),
            "Taman Pelangi": (1.4850, 103.7560),
            "Taman Molek": (1.5320, 103.7860),
            "Skudai": (1.5370, 103.6550),
            "Iskandar Puteri": (1.4272, 103.6158),
            "Mount Austin": (1.5480, 103.7930),
        }
        user_coords = loc_map.get(user_loc, (1.4927, 103.7414))
    else:
        st.subheader("🔧 Enforcement Filters")
        severity_filter = st.multiselect(
            "Severity",
            ["Low", "Medium", "High", "Critical"],
            default=["High", "Critical"],
        )
    st.markdown("---")
    st.info("🛰️ IoT Sensors: Online\n\n📡 LoRaWAN: Connected")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🚗 Commuter":
    zones = get_live_occupancy()
    st.session_state.setdefault("selected_parking_zone", zones[0]["id"])

    # ── Live Parking Map ──────────────────────────────────────────────────────
    st.subheader("🗺️ Live Parking Zone Map")
    st.caption("Click a parking circle to inspect that zone and load the 3D parking lot preview.")
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

        color = _zone_status_color(z["status"])
        folium.CircleMarker(
            location=z["coords"],
            radius=max(8, z["available"] // 8),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{z['name']}: {z['available']} lots ({z['status']})",
        ).add_to(m)

    folium.Marker(
        location=list(user_coords),
        tooltip="📍 You are here",
        icon=folium.Icon(color="lightblue", icon="user", prefix="fa"),
    ).add_to(m)

    map_state = _safe_st_folium(m, width=1100, height=450, key="parking_map")
    click_lat, click_lng = _extract_click_coords(map_state or {})
    nearest_zone = _find_nearest_zone(zones, click_lat, click_lng)
    if nearest_zone is not None:
        st.session_state["selected_parking_zone"] = nearest_zone["id"]

    selected_zone = next((z for z in zones if z["id"] == st.session_state["selected_parking_zone"]), zones[0])

    st.markdown("---")
    detail_col, model_col = st.columns([0.95, 1.4], gap="large")

    with detail_col:
        st.subheader("🧭 Selected Parking Zone")
        st.markdown(
            f"""
            <div class="glass-card">
                <h4 style="margin-bottom:0.4rem;">{selected_zone['name']}</h4>
                <div style="color:#cbd5e1; margin-bottom:0.75rem;">{selected_zone['type']} · {selected_zone['sensor_type']}</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
                    <div>
                        <div style="color:#94a3b8; font-size:0.8rem;">EMPTY</div>
                        <div style="font-size:1.7rem; font-weight:800; color:#22c55e;">{selected_zone['available']}</div>
                    </div>
                    <div>
                        <div style="color:#94a3b8; font-size:0.8rem;">OCCUPIED</div>
                        <div style="font-size:1.7rem; font-weight:800; color:#ef4444;">{selected_zone['occupied']}</div>
                    </div>
                </div>
                <div style="margin-top:1rem; color:#e2e8f0; font-weight:700;">Occupancy: {selected_zone['occupancy_pct']}%</div>
                <div style="margin-top:0.5rem; color:#94a3b8;">Status: {selected_zone['status']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(selected_zone["occupied"] / selected_zone["total_lots"] if selected_zone["total_lots"] else 0)
        st.metric("Rate", f"RM {selected_zone['hourly_rate']:.2f}/hr")
        if selected_zone["has_shuttle"]:
            st.info(f"🚐 Shuttle: Every {selected_zone['shuttle_freq_min']} min")
        st.caption("Tip: click another circle on the map to switch the preview.")

    with model_col:
        st.subheader("🧊 3D Parking Lot Preview")
        model_bytes, model_name = _load_model_bytes(None)
        _render_model_view(model_bytes, selected_zone)

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
            icon=folium.Icon(color=sev_colors.get(inc["severity"], "gray"), icon="exclamation-sign"),
        ).add_to(em)
    
    _safe_st_folium(em, width=1100, height=400, key="enforcement_map")
