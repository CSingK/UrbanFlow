import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.carbon_ledger import (
    get_sample_personal_data, calculate_city_impact, get_emissions_heatmap_data,
    get_monthly_trend, get_carbon_stats, REWARD_TIERS
)
from modules.ui_components import inject_side_nav, inject_global_ui, synthetic_fluctuation

st.set_page_config(page_title="Carbon Ledger | PBT-Vision", layout="wide", initial_sidebar_state="expanded")
inject_side_nav()
inject_global_ui("carbon")

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

    .reward-tier-card {
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(30,41,59,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }

    .reward-tier-card:hover {
        border-color: rgba(34,197,94,0.9);
        box-shadow: 0 0 0 1px rgba(34,197,94,0.35), 0 8px 22px rgba(34,197,94,0.16);
        transform: translateY(-1px);
    }

    .reward-tier-card.reward-tier-active {
        background: rgba(34,197,94,0.08);
        border: 1px solid rgba(255,255,255,0.12);
    }
</style>
""", unsafe_allow_html=True)

st.title("🌿 National Carbon Ledger")
st.markdown("Real-time verifiable CO₂ accounting — personal offset scores and city-wide impact tracking for Net-Zero 2050.")

view_mode = "🧑 Commuter" if st.session_state.get("global_view_mode", "Commuter") == "Commuter" else "🏛️ Authority"

c_stats = get_carbon_stats()
co2_prevented = synthetic_fluctuation(c_stats["co2_prevented_today"], 0.04, "carbon_co2_today")
green_commuters = synthetic_fluctuation(c_stats['active_green_commuters'], 0.03, 'carbon_green_commuters')
credits_issued = synthetic_fluctuation(c_stats["credits_issued_today"], 0.06, "carbon_credits_issued")
net_zero = synthetic_fluctuation(c_stats["net_zero_progress"], 0.015, "carbon_net_zero_progress")

st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("CO₂ Prevented Today", co2_prevented)
c2.metric("Green Commuters", f"{int(green_commuters) if isinstance(green_commuters, float) else green_commuters:,}")
c3.metric("Credits Issued", credits_issued)
c4.metric("Net-Zero Progress", net_zero)
with c5:
    st.info("🌍 Ledger: Verified\n\n📊 BigQuery: Connected")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# COMMUTER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🧑 Commuter":
    personal = get_sample_personal_data()

    # ── Hero Score ────────────────────────────────────────────────────────────
    tier = personal["tier"]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9));
                border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:2rem;
                text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:3.5rem;">{tier['name'].split(' ')[0]}</div>
        <div style="font-size:1.5rem;color:#f8fafc;font-weight:bold;margin:0.5rem 0;">
            {tier['name']}
        </div>
        <div style="font-size:3rem;font-weight:bold;color:{tier['color']};">
            {personal['co2_saved_kg']} kg CO₂
        </div>
        <div style="color:#94a3b8;margin-top:0.5rem;">saved this month</div>
        <div style="color:#94a3b8;margin-top:0.3rem;">
            🌳 Equivalent to <b>{personal['co2_saved_trees_equiv']}</b> trees planted
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Progress to Next Tier ─────────────────────────────────────────────────
    if personal["next_tier"]:
        st.markdown(f"**Progress to {personal['next_tier']['name']}:**")
        st.progress(personal["progress_pct"] / 100)
        st.caption(f"{personal['progress_pct']}% — Need {personal['next_tier']['min_kg'] - personal['co2_saved_kg']:.1f} kg more")

    # ── Reward ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);
                border-radius:12px;padding:1rem;margin:1rem 0;">
        <b style="color:#22c55e;">🎁 Your Reward:</b>
        <span style="color:#f8fafc;"> {tier['reward']}</span>
        <br><span style="color:#94a3b8;">Monthly value: <b>RM {personal['monthly_rm_value']}</b></span>
    </div>
    """, unsafe_allow_html=True)

    # ── Breakdown ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Savings Breakdown")

    bd = personal["breakdown"]
    bc1, bc2, bc3, bc4 = st.columns(4)
    bc1.metric("🚗 Carpool", f"{bd['carpool']['co2_saved']} kg", f"{bd['carpool']['trips']} trips")
    bc2.metric("🚌 Bus", f"{bd['bus']['co2_saved']} kg", f"{bd['bus']['trips']} trips")
    bc3.metric("🚆 RTS", f"{bd['rts']['co2_saved']} kg", f"{bd['rts']['trips']} trips")
    bc4.metric("🅿️ Parking", f"{bd['parking_diversion']['co2_saved']} kg",
               f"{bd['parking_diversion']['count']} diversions")

    # ── Donut Chart ───────────────────────────────────────────────────────────
    labels = ["Carpool", "Bus", "RTS", "Parking Diversion"]
    values = [bd["carpool"]["co2_saved"], bd["bus"]["co2_saved"],
              bd["rts"]["co2_saved"], bd["parking_diversion"]["co2_saved"]]
    colors = ["#38bdf8", "#f97316", "#a78bfa", "#22c55e"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent", textfont=dict(color="#f8fafc"),
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=350,
                      font=dict(family="Inter", color="#f8fafc"),
                      legend=dict(orientation="h", y=-0.1),
                      margin=dict(t=20, b=40))
    st.plotly_chart(fig, use_container_width=True)

    # ── Tier Overview ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏆 Reward Tiers")
    for t in REWARD_TIERS:
        is_current = t["name"] == tier["name"]
        active_cls = " reward-tier-active" if is_current else ""
        st.markdown(f"""
        <div class="reward-tier-card{active_cls}">
            <div>
                <b style="color:{t['color']};">{t['name']}</b>
                <span style="color:#94a3b8;"> — {t['min_kg']}–{t['max_kg'] if t['max_kg']<99999 else '∞'} kg</span>
            </div>
            <div style="color:#94a3b8;font-size:0.85rem;">{t['reward']}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTHORITY VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    city = calculate_city_impact()
    city_tonnes = synthetic_fluctuation(city['co2_prevented_today_tonnes'], 0.03, "carbon_city_tonnes")

    # ── Hero Counter ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(22,163,74,0.2), rgba(15,23,42,0.9));
                border:1px solid rgba(34,197,94,0.3); border-radius:16px; padding:2rem;
                text-align:center; margin-bottom:1.5rem;">
        <div style="color:#94a3b8;font-size:1rem;">CO₂ PREVENTED TODAY</div>
        <div style="font-size:4rem;font-weight:bold;color:#22c55e;">
            {city_tonnes:.2f} tonnes
        </div>
        <div style="color:#94a3b8;margin-top:0.5rem;">
            🌳 = {city['equivalent_trees']:.0f} trees | 🚗 = {city['equivalent_cars_off_road']:.0f} cars off road
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Module Breakdown ──────────────────────────────────────────────────────
    st.subheader("📊 Impact by Module")
    bd = city["breakdown"]
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("🚗 Carpool", f"{bd['carpool_module']['co2_saved_kg']:,} kg",
               f"{bd['carpool_module']['participants']} participants")
    mc2.metric("🚌 Bus", f"{bd['bus_module']['co2_saved_kg']:,} kg",
               f"{bd['bus_module']['riders']:,} riders")
    mc3.metric("🚆 RTS", f"{bd['rts_module']['co2_saved_kg']:,} kg",
               f"{bd['rts_module']['riders']:,} riders")
    mc4.metric("🅿️ Parking", f"{bd['parking_diversion']['co2_saved_kg']:,} kg",
               f"{bd['parking_diversion']['diversions']} diversions")

    # ── Emissions Heat Map ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Emissions Heat Map — Johor Bahru")
    heatmap_data = get_emissions_heatmap_data()
    em = folium.Map(location=[1.5000, 103.7300], zoom_start=11, tiles="cartodbdark_matter")
    for z in heatmap_data:
        popup_html = f"""
        <div style='font-family:Inter,sans-serif;min-width:160px'>
            <b>{z['name']}</b><br>
            Daily emission: {z['daily_emission_kg']} kg<br>
            CO₂ prevented: <b style='color:#22c55e'>{z['co2_prevented_kg']}</b> kg<br>
            Reduction: {z['reduction_pct']}%
        </div>"""
        folium.CircleMarker(
            location=z["coords"], radius=z["radius"],
            color=z["color"], fill=True, fill_color=z["color"], fill_opacity=0.4,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{z['name']}: {z['daily_emission_kg']} kg/day (↓{z['reduction_pct']}%)"
        ).add_to(em)
    
    # FIX: Use folium_static
    folium_static(em, width=1100, height=400)

    # ── Monthly Trends ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Monthly CO₂ Prevented Trend")
    trend = get_monthly_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[t["month"] for t in trend], y=[t["baseline_tonnes"] for t in trend],
        name="Baseline (Without Interventions)", mode="lines+markers",
        line=dict(color="#ef4444", width=2, dash="dash"), marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=[t["month"] for t in trend], y=[t["co2_prevented_tonnes"] for t in trend],
        name="CO₂ Prevented", mode="lines+markers",
        line=dict(color="#22c55e", width=3), marker=dict(size=8),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.1)"
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=350, margin=dict(t=30, b=50),
        font=dict(family="Inter", color="#f8fafc"),
        yaxis_title="Tonnes CO₂",
        legend=dict(orientation="h", y=1.15),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Net-Zero Progress ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎯 Net-Zero 2050 Progress")
    progress = city["net_zero_2050_progress"]
    st.progress(progress / 100)
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;color:#94a3b8;">
        <span>Current: <b style="color:#22c55e;">{progress}%</b></span>
        <span>Monthly growth: <b style="color:#38bdf8;">+{city['monthly_trend_pct_change']}%</b></span>
        <span>Target: <b>2050</b></span>
    </div>
    """, unsafe_allow_html=True)
