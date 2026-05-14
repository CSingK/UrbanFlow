import datetime
import random
import re
import os

import streamlit as st
import streamlit.components.v1 as components


def get_logo_base64():
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo_b64_new.txt")
        with open(logo_path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

def inject_side_nav():
    """Render a lightweight, stable sidebar navigation for UrbanFlow."""
    
    # Ensure default mode exists
    if "global_view_mode" not in st.session_state:
        st.session_state.global_view_mode = "Commuter"

    mode = st.session_state.global_view_mode
    
    if mode == "Commuter":
        theme_glow = "0 -20px 40px -10px rgba(41, 211, 178, 0.3)" # Soft emerald green
        border_top = "4px solid #29d3b2"
        radio_color = "#29d3b2"
    else:
        theme_glow = "0 -20px 40px -10px rgba(220, 38, 38, 0.4)" # Glowing red / Police blue accents
        border_top = "4px solid #ef4444"
        radio_color = "#ef4444"

    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 100%; border-radius: 12px; margin-bottom: 0.5rem;" />' if logo_b64 else '<div class="uf-sidebar-title">UrbanFlow Control</div>'

    st.markdown(
        f"""
    <style>
        /* Hide default Streamlit sidebar navigation */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(7, 19, 24, 0.88), rgba(14, 33, 41, 0.92)) !important;
            border-right: 1px solid rgba(133, 224, 255, 0.20) !important;
            border-top: {border_top} !important;
            box-shadow: inset {theme_glow} !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: all 0.4s ease;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: #e8f7ff !important;
        }}

        .uf-sidebar-wrap {{
            margin-top: 0.2rem;
            margin-bottom: 0.8rem;
            border: 1px solid rgba(133, 224, 255, 0.22);
            border-radius: 14px;
            padding: 0.85rem 0.9rem;
            background: rgba(8, 22, 28, 0.65);
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.25);
            text-align: center;
        }}

        .uf-sidebar-subtitle {{
            font-size: 0.78rem;
            color: #9cc2d0;
            margin: 0;
        }}

        [data-testid="stSidebar"] .stPageLink > a {{
            border-radius: 12px;
            padding: 0.5rem 0.8rem;
            transition: all 0.25s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(255, 255, 255, 0.02);
            margin-bottom: 0.3rem;
            color: #e8f7ff !important;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }}

        [data-testid="stSidebar"] .stPageLink > a:hover {{
            background: linear-gradient(90deg, rgba(41, 211, 178, 0.15), rgba(41, 211, 178, 0.02));
            border-color: rgba(41, 211, 178, 0.4);
            transform: translateX(4px);
            box-shadow: -4px 0 0 rgba(41, 211, 178, 0.8);
            text-decoration: none;
        }}
        
        [data-testid="stSidebar"] .stPageLink > a[data-active="true"],
        [data-testid="stSidebar"] .stPageLink > a[aria-current="page"] {{
            background: linear-gradient(90deg, rgba(41, 211, 178, 0.25), rgba(41, 211, 178, 0.05));
            border-color: rgba(41, 211, 178, 0.6);
            box-shadow: -4px 0 0 rgba(41, 211, 178, 1);
        }}

        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            background: rgba(8, 22, 28, 0.4) !important;
            border: 1px solid rgba(133, 224, 255, 0.1) !important;
            border-radius: 12px !important;
            margin-bottom: 0.5rem;
        }}

        [data-testid="stSidebar"] [data-testid="stExpander"] summary {{
            padding: 0.5rem 1rem !important;
        }}

        [data-testid="stSidebar"] [data-testid="stExpander"] summary p {{
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            color: #9cc2d0 !important;
            text-transform: uppercase;
        }}

        [data-testid="stSidebar"] [data-testid="stExpanderDetails"] {{
            padding: 0.5rem !important;
        }}

        div[role="radiogroup"] > label {{
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 0.5rem 1rem !important;
            border-radius: 8px !important;
            margin-right: 0.5rem !important;
        }}
        div[role="radiogroup"] > label[data-checked="true"] {{
            border-color: {radio_color} !important;
            box-shadow: 0 0 10px {theme_glow.split(' ')[-1]} !important;
        }}

        @keyframes pulse-green {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
        }}

        @keyframes pulse-blue {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(56, 189, 248, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }}
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div class="uf-sidebar-wrap">
                {logo_html}
                <p class="uf-sidebar-subtitle">Smart mobility modules</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


        st.page_link("dashboard.py", label="Home Overview", icon="🏙️")

        with st.expander("🛠️ Orchestration", expanded=True):
            st.page_link("pages/1_🅿️_Smart_Parking.py", label="Smart Parking", icon="🅿️")
            st.page_link("pages/2_🚗_Carpool_Agent.py", label="Carpool Agent", icon="🚗")
            st.page_link("pages/3_🚌_Bus_Intelligence.py", label="Bus Intelligence", icon="🚌")

        with st.expander("⚖️ Accountability", expanded=True):
            st.page_link("pages/4_🌿_Carbon_Ledger.py", label="Carbon Ledger", icon="🌿")

        st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div style="padding: 1rem; background: #0f172a; border-radius: 12px; border: 1px solid #334155; font-family: 'Courier New', monospace; font-size: 0.75rem; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
                <div style="color: #64748b; margin-bottom: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">System Health</div>
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #22c55e; animation: pulse-green 2s infinite;"></div>
                    <span style="color: #e2e8f0; font-weight: 600;">IoT SENSORS: <span style="color: #22c55e;">ONLINE</span></span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; animation: pulse-blue 2s infinite 1s;"></div>
                    <span style="color: #e2e8f0; font-weight: 600;">LoRaWAN: <span style="color: #38bdf8;">CONNECTED</span></span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    # Render mode selector at the top right of the main page
    mode_col1, mode_col2 = st.columns([0.65, 0.35])
    with mode_col2:
        st.markdown("<div style='font-size: 0.75rem; color: #9cc2d0; font-weight: 800; margin-bottom: 0.2rem; text-transform: uppercase;'>System Mode</div>", unsafe_allow_html=True)
        st.radio("Mode", ["Commuter", "Authority"], key="global_view_mode", horizontal=True, label_visibility="collapsed")



def _apply_numeric_variation(number: float, spread: float, key: str = "") -> float:
    seed_key = f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}::{key}"
    rng = random.Random(seed_key)
    delta = rng.uniform(-spread, spread)
    return number * (1 + delta)


def synthetic_fluctuation(value, spread: float = 0.04, key: str = ""):
    """Apply a small deterministic minute-level fluctuation for synthetic demo realism."""
    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, int):
        return max(0, int(round(_apply_numeric_variation(float(value), spread, key))))

    if isinstance(value, float):
        return _apply_numeric_variation(value, spread, key)

    if isinstance(value, str):
        txt = value.strip()
        pct_match = re.fullmatch(r"(-?\d+(?:\.\d+)?)%", txt)
        if pct_match:
            base = float(pct_match.group(1))
            varied = _apply_numeric_variation(base, spread, key)
            return f"{max(0, min(100, varied)):.1f}%"

        num_unit_match = re.fullmatch(r"(-?\d+(?:\.\d+)?)(\s*.*)", txt)
        if num_unit_match:
            base = float(num_unit_match.group(1))
            suffix = num_unit_match.group(2)
            varied = _apply_numeric_variation(base, spread, key)
            if suffix:
                if float(base).is_integer():
                    return f"{max(0, int(round(varied)))}{suffix}"
                return f"{max(0, varied):.2f}{suffix}"

    return value


def inject_global_ui(page_id: str = "urbanflow"):
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Manrope:wght@400;600;700&display=swap');

        :root {
            --uf-bg-1: #071318;
            --uf-bg-2: #0f2027;
            --uf-bg-3: #16303b;
            --uf-card: rgba(13, 28, 34, 0.72);
            --uf-border: rgba(133, 224, 255, 0.20);
            --uf-text: #e8f7ff;
            --uf-muted: #9cc2d0;
            --uf-accent: #29d3b2;
            --uf-accent-2: #ffb25b;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 12%, rgba(41, 211, 178, 0.16), transparent 32%),
                radial-gradient(circle at 92% 20%, rgba(255, 178, 91, 0.14), transparent 36%),
                linear-gradient(125deg, var(--uf-bg-1), var(--uf-bg-2) 50%, var(--uf-bg-3));
            color: var(--uf-text);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Sora', sans-serif !important;
            letter-spacing: -0.02em;
            color: var(--uf-text) !important;
        }

        p, span, label, div, [data-testid="stMarkdownContainer"] {
            font-family: 'Manrope', sans-serif;
        }

        [data-testid="stMetric"],
        div[data-testid="metric-container"],
        [data-testid="stDataFrame"],
        [data-testid="stExpander"],
        [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(.glass-card) {
            border: 1px solid var(--uf-border) !important;
            border-radius: 16px !important;
            background: var(--uf-card) !important;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.28);
        }

        div[data-testid="metric-container"] {
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 40px rgba(41, 211, 178, 0.20);
        }

        .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(41, 211, 178, 0.55);
            background: linear-gradient(135deg, rgba(41, 211, 178, 0.28), rgba(255, 178, 91, 0.25));
            color: #e9fbff;
            font-weight: 700;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(41, 211, 178, 0.22);
        }

        @media (max-width: 900px) {
            [data-testid="stMetric"] {
                min-height: 112px;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    inject_gsap_animations(page_id)


def inject_gsap_animations(page_id: str = "urbanflow"):
    components.html(
        """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
        <script>
          (function() {
            const parentDoc = window.parent.document;
            const run = () => {
              const gsapRef = window.gsap || window.parent.gsap;
              if (!gsapRef) return;

              const metrics = parentDoc.querySelectorAll('div[data-testid="metric-container"]');
              const headings = parentDoc.querySelectorAll('h1, h2');
              const blocks = parentDoc.querySelectorAll('[data-testid="stHorizontalBlock"] > div');
              const charts = parentDoc.querySelectorAll('.js-plotly-plot, iframe[title*="streamlit_folium"]');

              gsapRef.fromTo(headings, { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, stagger: 0.05, ease: 'power2.out' });
              gsapRef.fromTo(metrics, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.55, stagger: 0.04, ease: 'power2.out', delay: 0.08 });
              gsapRef.fromTo(blocks, { y: 18, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, stagger: 0.03, ease: 'power2.out', delay: 0.12 });
              gsapRef.fromTo(charts, { scale: 0.985, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.55, stagger: 0.05, ease: 'power1.out', delay: 0.16 });
            };

            setTimeout(run, 80);
          })();
        </script>
        """,
        height=0,
    )
