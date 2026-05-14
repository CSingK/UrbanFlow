import base64
import datetime
import math
import os
import random
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
from modules.ui_components import inject_side_nav, inject_global_ui, synthetic_fluctuation

st.set_page_config(page_title="Smart Parking | PBT-Vision", layout="wide", initial_sidebar_state="expanded")
inject_side_nav()
inject_global_ui("parking")

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_MODEL_PATH = ASSET_DIR / "parking_lot_uf.glb"


def _zone_status_color(status: str) -> str:
    if status == "AVAILABLE":
        return "#22c55e"
    if status == "LOW":
        return "#f97316"
    return "#ef4444"


def _sensor_status_color(utilization: float) -> str:
    """Returns a simplified 4-state color spectrum for IoT sensors."""
    if utilization >= 0.95: return "#ef4444" # Critical Red
    if utilization >= 0.80: return "#f97316" # Busy Orange
    if utilization >= 0.65: return "#facc15" # High Yellow
    return "#34d399" # Emerald Green (Moderate/Available)


def _render_zone_sensor_cloud(m: folium.Map, zones: list[dict]) -> None:
    """Render many localized IoT sensor points around each zone for a denser, realistic map."""
    seed = f"parking-sensors::{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    rng = random.Random(seed)

    for z in zones:
        lat, lng = z["coords"]
        base_util = z["occupied"] / z["total_lots"] if z["total_lots"] else 0.5

        # Denser zones produce more points; keeps map rich without overloading UI.
        sensor_count = max(10, min(30, int(z["total_lots"] / 18)))
        radius_scale = 0.0012 if z["type"] in ("CIQ Zone", "RTS Terminal", "Premium") else 0.0016

        for _ in range(sensor_count):
            angle = rng.uniform(0, 2 * math.pi)
            dist = radius_scale * (rng.random() ** 1.6)
            d_lat = math.cos(angle) * dist
            d_lng = math.sin(angle) * dist

            local_util = max(0.08, min(0.99, base_util + rng.uniform(-0.22, 0.22)))
            color = _sensor_status_color(local_util)

            # Glow effect (larger, fainter circle)
            folium.CircleMarker(
                location=[lat + d_lat, lng + d_lng],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.15,
                weight=0,
            ).add_to(m)

            # Core point
            folium.CircleMarker(
                location=[lat + d_lat, lng + d_lng],
                radius=2.5,
                color="#ffffff" if local_util < 0.1 else color,
                fill=True,
                fill_color=color,
                fill_opacity=1.0,
                weight=1.5,
                opacity=1.0,
                tooltip=f"Sensor ID: {rng.randint(1000, 9999)} · {int(local_util * 100)}% Load",
            ).add_to(m)

    # Inject real-time fluctuation script into the map's own DOM
    m.get_root().html.add_child(folium.Element("""
    <script>
    setTimeout(function() {
        setInterval(function(){
            var circles = document.querySelectorAll('path.leaflet-interactive');
            circles.forEach(function(c){
                if(Math.random() > 0.9) {
                    var op = 0.4 + Math.random() * 0.6;
                    c.setAttribute('fill-opacity', op);
                    c.style.transition = 'all 0.5s ease';
                    if(Math.random() > 0.5) {
                        c.setAttribute('stroke-width', 1 + Math.random() * 3);
                    }
                }
            });
        }, 1500);
    }, 2000);
    </script>
    """))


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
    occupied_count = zone["occupied"]
    available_count = zone["available"]
    
    components.html(
        f"""
        <style>
            .viewer-shell {{
                position: relative;
                border-radius: 20px;
                overflow: hidden;
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.96));
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
                height: 540px;
                width: 100%;
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
            #three-container {{
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at top, rgba(56, 189, 248, 0.14), rgba(15, 23, 42, 0.96));
            }}
        </style>
        
        <div class="viewer-shell">
            <div class="viewer-badge">
                {zone["name"]} · {zone["occupied"]} occupied, {zone["available"]} empty
            </div>
            <div class="empty-indicator">
                🟢 {empty_pct:.0f}% Empty Parking
            </div>
            <div id="three-container"></div>
        </div>

        <script type="importmap">
          {{
            "imports": {{
              "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
              "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
            }}
          }}
        </script>

        <script type="module">
            import * as THREE from 'three';
            import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
            import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

            const container = document.getElementById('three-container');
            const scene = new THREE.Scene();

            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
            directionalLight.position.set(5, 10, 5);
            scene.add(directionalLight);

            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 1.0;

            const loader = new GLTFLoader();
            const base64Data = "data:model/gltf-binary;base64,{encoded_model}";
            const glowingBoxes = [];

            loader.load(base64Data, (gltf) => {{
                const model = gltf.scene;
                scene.add(model);
                
                // Center model and set camera
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                
                camera.position.set(center.x + maxDim * 0.8, center.y + maxDim * 1.0, center.z + maxDim * 1.2);
                camera.lookAt(center);
                controls.target.copy(center);

                // ============================================
                // PARKING LOT CONFIGURATION (ADJUST THESE!)
                // ============================================
                const parkingConfig = {{
                    rows: 2,              // Number of parking rows
                    cols: 38,             // Number of spots per row
                    startX: -4.4,         // Left edge X position
                    startZ: -0.3,         // Front edge Z position  
                    spacingX: 0.24,        // Width of each spot
                    spacingZ: 0.9,        // Depth of each spot
                    groundY: 0.08,        // Height above ground (adjust if floating/buried)
                    spotWidth: 0.26,       // Visual width of glow box
                    spotDepth: 0.4        // Visual depth of glow box
                }};

                const totalSpots = parkingConfig.rows * parkingConfig.cols;  // 2 × 38 = 76

                // 2. Define which indices are occupied (0-indexed)
                // Top row: indices 0-37 | Bottom row: indices 38-75
                // 11th spot = index 10 | 14th spot = index 13
                const occupiedIndices = new Set([10, 13]);

                // 3. Default all spots to 'empty' (green)
                const spotStatus = Array(totalSpots).fill('empty');

                // 4. Mark specific indices as 'occupied' (red)
                occupiedIndices.forEach(idx => {{
                    if (idx < totalSpots) {{
                        spotStatus[idx] = 'occupied';
                    }}
                }});

                // Create glowing boxes for each parking spot
                for (let r = 0; r < parkingConfig.rows; r++) {{
                    for (let c = 0; c < parkingConfig.cols; c++) {{
                        const idx = r * parkingConfig.cols + c;
                        const status = spotStatus[idx];
                        
                        // Determine color based on status
                        const color = status === 'empty' ? 0x22C55E : 0xEF4444;
                        const edgeColor = status === 'empty' ? 0x4ade80 : 0xf87171;
                        
                        // Box geometry
                        const boxGeom = new THREE.BoxGeometry(
                            parkingConfig.spotWidth, 
                            0.15, 
                            parkingConfig.spotDepth
                        );

                        // Core glowing mesh
                        const coreMat = new THREE.MeshBasicMaterial({{
                            color: color,
                            transparent: true,
                            opacity: 0.0,
                            side: THREE.DoubleSide,
                            blending: THREE.AdditiveBlending,
                            depthWrite: false
                        }});
                        const glowBox = new THREE.Mesh(boxGeom, coreMat);

                        // Outline border
                        const edgesGeom = new THREE.EdgesGeometry(boxGeom);
                        const lineMat = new THREE.LineBasicMaterial({{
                            color: edgeColor,
                            linewidth: 3,
                            transparent: true,
                            opacity: 0.0,
                            blending: THREE.AdditiveBlending,
                            depthWrite: false
                        }});
                        const border = new THREE.LineSegments(edgesGeom, lineMat);
                        glowBox.add(border);

                        // Position in world space
                        const x = parkingConfig.startX + c * parkingConfig.spacingX;
                        const z = parkingConfig.startZ + r * parkingConfig.spacingZ;
                        glowBox.position.set(x, parkingConfig.groundY, z);

                        scene.add(glowBox);
                        glowingBoxes.push({{ 
                            core: glowBox, 
                            border: border, 
                            offset: Math.random() * Math.PI * 2,
                            status: status
                        }});
                    }}
                }}

                // Animation loop
                let time = 0;
                function animate() {{
                    requestAnimationFrame(animate);
                    controls.update();
                    
                    time += 0.04;
                    glowingBoxes.forEach(p => {{
                        const pulse = (Math.sin(time + p.offset) + 1) / 2;
                        // Different opacity for empty vs occupied
                        const baseOpacity = p.status === 'empty' ? 0.3 : 0.4;
                        const pulseRange = p.status === 'empty' ? 0.3 : 0.4;
                        
                        p.core.material.opacity = baseOpacity + (pulse * pulseRange);
                        p.border.material.opacity = 0.5 + (pulse * 0.5);
                    }});
                    
                    renderer.render(scene, camera);
                }}
                animate();

                // Handle resize
                window.addEventListener('resize', () => {{
                    camera.aspect = container.clientWidth / container.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(container.clientWidth, container.clientHeight);
                }});
            }});
        </script>
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

# ── Advanced Styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Panning Grid Background */
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

    /* Animated Neon Blobs */
    .stApp::before {
        content: '';
        position: fixed;
        top: -10%; left: -10%; width: 40%; height: 40%;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.08) 0%, transparent 70%);
        filter: blur(80px);
        animation: floatBlob 20s ease-in-out infinite alternate;
        z-index: -1;
    }
    @keyframes floatBlob {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(20%, 30%) scale(1.2); }
    }

    /* Glassmorphism Cards with Scanline Texture */
    .glass-card {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(133, 224, 255, 0.2) !important;
        border-radius: 24px !important;
        padding: 1.8rem !important;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5) !important;
        position: relative;
        overflow: hidden;
    }
    .glass-card::after {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: repeating-linear-gradient(0deg, rgba(0,0,0,0.03) 0px, rgba(0,0,0,0.03) 1px, transparent 1px, transparent 2px);
        pointer-events: none;
    }

    /* Metric Styling */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 16px !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.1);
    }

    /* Titles */
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

</style>
""", unsafe_allow_html=True)






st.markdown("<div class='main-title'>Smart Parking</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-top:-0.5rem; margin-bottom:2rem;'>IoT-integrated Green Zone navigation & autonomous enforcement logic.</p>", unsafe_allow_html=True)


view_mode = "Commuter" if st.session_state.get("global_view_mode", "Commuter") == "Commuter" else "Authority"

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "Commuter":
    st.subheader("Your Location")

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

    zones = get_live_occupancy()
    st.session_state.setdefault("selected_parking_zone", zones[0]["id"])

    # ── Live Parking Map ──────────────────────────────────────────────────────
    st.subheader("Live Parking Zone Map")

    st.caption("Dense IoT sensor cloud: green=available, orange=busy, red=near full. Click a zone circle to inspect and load the 3D preview.")
    m = folium.Map(location=[1.4800, 103.7200], zoom_start=12, tiles="cartodbdark_matter")

    _render_zone_sensor_cloud(m, zones)

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

    # Override with actual 3D model data
    selected_zone["name"] = user_loc
    selected_zone["total_lots"] = 76
    selected_zone["occupied"] = 2
    selected_zone["available"] = 74
    selected_zone["occupancy_pct"] = round(2 / 76 * 100, 1)
    selected_zone["status"] = "AVAILABLE" if selected_zone["available"] > 10 else "LOW"


    st.markdown("---")
    detail_col, model_col = st.columns([0.95, 1.4], gap="large")

    with detail_col:
        st.subheader("Terminal Dashboard")
        status_class = "status-available" if selected_zone["available"] > 10 else "status-low"
        
        st.markdown(
            f"""
<div class="glass-card">
<div class="status-badge {status_class}">{selected_zone['status']}</div>
<h3 style="margin: 0 0 0.2rem 0; font-family: 'Sora', sans-serif;">{selected_zone['name']}</h3>
<div style="color:#64748b; font-size:0.85rem; margin-bottom:1.5rem; font-family:'JetBrains Mono';">ZONE_ID: {selected_zone['id'].upper()} // {selected_zone['sensor_type']}</div>

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; background:rgba(255,255,255,0.03); padding:1rem; border-radius:12px;">
<div>
<div style="color:#94a3b8; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">Available</div>
<div id="lots-avail" class="cockpit-metric" style="font-size:2.2rem; color:#22c55e;">{selected_zone['available']}</div>
</div>
<div style="text-align:right;">
<div style="color:#94a3b8; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">Occupied</div>
<div id="lots-occ" class="cockpit-metric" style="font-size:2.2rem; color:#ef4444;">{selected_zone['occupied']}</div>
</div>
</div>

<div style="margin-top:1.5rem;">
<div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
<span style="color:#e2e8f0; font-weight:700; font-size:0.9rem;">Occupancy Density</span>
<span id="lots-pct" style="color:#38bdf8; font-family:'JetBrains Mono';">{selected_zone['occupancy_pct']}%</span>
</div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.progress(selected_zone["occupied"] / selected_zone["total_lots"] if selected_zone["total_lots"] else 0)

        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Hourly Rate", f"RM {selected_zone['hourly_rate']:.2f}/hr")
        with m_col2:
            if selected_zone["has_shuttle"]:
                st.metric("Shuttle Freq.", f"{selected_zone['shuttle_freq_min']} min")
            else:
                st.metric("Walkability", "High")
        
        st.caption("✨ Data updates automatically via IoT feed. Tap a map circle to switch zones.")


    with model_col:
        st.subheader("🧊 3D Parking Lot Preview")
        model_bytes, model_name = _load_model_bytes(None)
        _render_model_view(model_bytes, selected_zone)

    # ── Smart Reroute ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Smart Green Hub Reroute")

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

    st.markdown("---")
    st.subheader("Zone Occupancy Overview")

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
    st.subheader("Autonomous Enforcement Dashboard")

    
    st.markdown("---")
    st.subheader("Enforcement Filters")

    severity_filter = st.multiselect(
        "Severity",
        ["Low", "Medium", "High", "Critical"],
        default=["High", "Critical"],
    )

    incidents = generate_enforcement_log(15)
    filtered = [inc for inc in incidents if inc["severity"] in severity_filter]

    # ── Metrics ───────────────────────────────────────────────────────────────
    total_incidents = synthetic_fluctuation(len(incidents), 0.08, "parking_total_incidents")
    critical_incidents = synthetic_fluctuation(sum(1 for i in incidents if i["severity"] == "Critical"), 0.10, "parking_critical_incidents")
    sent_to_pdrm = synthetic_fluctuation(sum(1 for i in incidents if i["status"] == "Sent to PDRM"), 0.10, "parking_sent_pdrm")
    fines_issued = synthetic_fluctuation(sum(1 for i in incidents if i["status"] == "Fine Issued"), 0.10, "parking_fines_issued")
    mc1, mc2, mc3, mc4 = st.columns(4)
    
    with mc1:
        st.markdown(f"""
            <div class="glass-card" style="padding:1rem !important; text-align:center;">
                <div style="color:#94a3b8; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Total Incidents</div>
                <div id="auth-total" class="cockpit-metric" style="font-size:1.8rem; color:#f8fafc;">{int(total_incidents)}</div>
            </div>
        """, unsafe_allow_html=True)
    with mc2:
        st.markdown(f"""
            <div class="glass-card" style="padding:1rem !important; text-align:center; border-color:rgba(239, 68, 68, 0.3) !important;">
                <div style="color:#f87171; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Critical</div>
                <div id="auth-critical" class="cockpit-metric" style="font-size:1.8rem; color:#ef4444;">{int(critical_incidents)}</div>
            </div>
        """, unsafe_allow_html=True)
    with mc3:
        st.markdown(f"""
            <div class="glass-card" style="padding:1rem !important; text-align:center;">
                <div style="color:#94a3b8; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Sent to PDRM</div>
                <div id="auth-pdrm" class="cockpit-metric" style="font-size:1.8rem; color:#38bdf8;">{int(sent_to_pdrm)}</div>
            </div>
        """, unsafe_allow_html=True)
    with mc4:
        st.markdown(f"""
            <div class="glass-card" style="padding:1rem !important; text-align:center;">
                <div style="color:#94a3b8; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Fines Issued</div>
                <div id="auth-fines" class="cockpit-metric" style="font-size:1.8rem; color:#facc15;">{int(fines_issued)}</div>
            </div>
        """, unsafe_allow_html=True)


    # ── Incident Table ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Violation Log")

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
    st.subheader("Violation Locations")

    em = folium.Map(location=[1.4800, 103.7300], zoom_start=12, tiles="cartodbdark_matter")
    sev_colors = {"Low": "green", "Medium": "orange", "High": "red", "Critical": "darkred"}
    for inc in filtered:
        folium.Marker(
            location=inc["coords"],
            tooltip=f"{inc['violation']} — {inc['license_plate']}",
            icon=folium.Icon(color=sev_colors.get(inc["severity"], "gray"), icon="exclamation-sign"),
        ).add_to(em)
    
    _safe_st_folium(em, width=1100, height=400, key="enforcement_map")

# ── Real-Time Fluctuation Script ──────────────────────────────────────────
components.html(
    """
    <script>
    (function() {
        const parentDoc = window.parent.document;
        const updateMetrics = () => {
            const availEl = parentDoc.getElementById('lots-avail');
            const occEl = parentDoc.getElementById('lots-occ');
            const pctEl = parentDoc.getElementById('lots-pct');
            if (availEl && occEl) {
                let avail = parseInt(availEl.innerText);
                let occ = parseInt(occEl.innerText);
                if (Math.random() > 0.6) {
                    const shift = Math.random() > 0.5 ? 1 : -1;
                    if (avail - shift >= 0 && occ + shift >= 0) {
                        avail -= shift; occ += shift;
                        availEl.innerText = avail; occEl.innerText = occ;
                        if (pctEl) {
                            const total = avail + occ;
                            pctEl.innerText = ((occ / total) * 100).toFixed(1) + '%';
                        }
                    }
                }
            }
            const authTotal = parentDoc.getElementById('auth-total');
            if (authTotal && Math.random() > 0.8) {
                let val = parseInt(authTotal.innerText);
                authTotal.innerText = val + 1;
            }
        };
        setInterval(updateMetrics, 4000);
    })();
    </script>
    """,
    height=0
)




