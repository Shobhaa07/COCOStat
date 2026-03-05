import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="COCOStat – Coconut Market Intelligence",
    page_icon="🥥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session state for language ─────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ─── Translations (unchanged) ───────────────────────────────────────────────────
# ... keep your existing T dictionary here ...
# (I won't repeat the whole dictionary to save space)

t = T[st.session_state.lang]

# ─── Data generation (unchanged) ────────────────────────────────────────────────
@st.cache_data
def generate_data():
    # ... your existing generate_data function ...
    return hist, forecast

history_df, forecast_df = generate_data()

# ─── Theme / Coconut style CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700&family=Roboto:wght@400;500;700&display=swap');

/* Base font */
html, body, [class*="css"] {
    font-family: 'Roboto', 'Noto Sans Sinhala', sans-serif;
}

/* Hide default header & footer */
#MainMenu, footer, header {visibility: hidden !important;}

/* Hero section - keep visible / stable feel */
.hero-container {
    position: relative;
    z-index: 10;
    background: linear-gradient(to bottom, rgba(13, 71, 35, 0.07), rgba(13, 71, 35, 0.02));
    padding: 2.2rem 1rem 1.8rem;
    border-bottom: 1px solid #d1e8d9;
    margin-bottom: 1.5rem;
    text-align: center;
}

/* Language selector - top right */
.lang-switcher {
    position: absolute;
    top: 1.1rem;
    right: 2.2rem;
    z-index: 999;
    background: white;
    border-radius: 50px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    padding: 0.35rem 0.9rem;
    font-size: 0.92rem;
}

/* Sidebar improvements */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2f1a 0%, #1a3f22 100%) !important;
    border-right: 1px solid #2a5c38;
}
[data-testid="stSidebar"] * {
    color: #e8f5e9 !important;
}
.sidebar-title {
    color: #c8e6c9 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    text-align: center;
    margin: 1rem 0 1.5rem;
}
.sidebar-divider {
    background: linear-gradient(90deg, #4caf50, #81c784, #4caf50);
    height: 3px;
    border-radius: 2px;
    margin: 1.2rem 0;
}

/* Cards & metrics */
[data-testid="metric-container"] {
    background: #f1f8e9;
    border: 1px solid #c5e1a5;
    border-radius: 14px;
    padding: 1.1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* Better responsiveness for narrow screens */
@media (max-width: 768px) {
    .lang-switcher { right: 1rem; top: 0.9rem; font-size: 0.88rem; padding: 0.3rem 0.7rem; }
    .hero-container { padding: 1.6rem 0.9rem 1.3rem; }
    h1 { font-size: 1.9rem !important; }
    .stColumns > div { width: 100% !important; margin-bottom: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── Language Switcher – Top Right ──────────────────────────────────────────────
with st.container():
    st.markdown('<div class="lang-switcher">', unsafe_allow_html=True)
    col_l1, col_l2 = st.columns([1, 4])
    with col_l1:
        st.write("")  # spacer
    with col_l2:
        lang_choice = st.radio(
            "Language / භාෂාව",
            ["English", "සිංහල"],
            index=0 if st.session_state.lang == "en" else 1,
            key="lang_radio_top",
            horizontal=True,
            label_visibility="collapsed"
        )
        new_lang = "en" if lang_choice == "English" else "si"
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Hero Section (stable / always visible style) ───────────────────────────────
st.markdown(f"""
<div class="hero-container">
    <span style="background:#dcedc8; color:#1b5e20; padding:0.5rem 1.1rem; border-radius:2rem; font-weight:600; font-size:0.95rem;">
        🥥 {t["subtitle"]}
    </span>
    <h1 style="margin:1.1rem 0 0.6rem; font-size:2.6rem; font-weight:900; color:#0f2f1a; line-height:1.15;">
        {t["tagline"]}
    </h1>
    <p style="color:#37474f; font-size:1.05rem; max-width:720px; margin:0 auto;">
        {t["desc"]}
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar Navigation (cleaner + icons) ───────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🥥 COCOStat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    section = st.radio(
        "Navigation",
        t["nav"],
        format_func=lambda x: x,  # already has emoji
        label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown("**Active Market Regime**")
    active_regime = st.selectbox(
        "Explore Regime",
        t["regime_options"],
        index=0,
        label_visibility="visible"
    )
    regime_idx = t["regime_options"].index(active_regime)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Data updated: " + datetime.now().strftime("%b %Y"))
    st.caption("Source: Coconut Development Authority Auction Records")

# ─── Rest of your pages ─────────────────────────────────────────────────────────
# (keep your existing if-elif logic for Overview, Market, Demand, etc.)

# Just showing one example – replace your existing sections accordingly
if "Overview" in section or "දළ" in section:
    cols = st.columns(4)
    with cols[0]:
        st.metric(t["card_price_label"], "Rs. 68.50", t["card_price_sub"])
    # ... rest of your overview cards ...

# ─── Improved Footer ────────────────────────────────────────────────────────────
st.markdown("---")

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1b5e20, #388e3c);
    color: white;
    padding: 2.8rem 2rem;
    border-radius: 16px;
    text-align: center;
    margin: 3rem 0 1rem;
">
    <div style="font-size: 2.8rem; margin-bottom: 0.8rem;">🥥🌴</div>
    <h3 style="margin:0; font-size:1.6rem;">Coconut Market Intelligence – Sri Lanka</h3>
    <p style="margin:0.8rem 0 1.6rem; opacity:0.9; max-width:800px; margin-left:auto; margin-right:auto;">
        Real-time insights on coconut auction prices, demand elasticity, market regimes & policy guidance
    </p>

    <div style="display:flex; justify-content:center; gap:2.5rem; flex-wrap:wrap; margin:1.8rem 0;">
        <div>
            <strong style="opacity:0.8; font-size:0.85rem; text-transform:uppercase;">Data Source</strong><br>
            Coconut Development Authority (CDA)<br>
            Sri Lanka
        </div>
        <div>
            <strong style="opacity:0.8; font-size:0.85rem; text-transform:uppercase;">Last Update</strong><br>
            {datetime.now().strftime("%B %Y")}
        </div>
        <div>
            <strong style="opacity:0.8; font-size:0.85rem; text-transform:uppercase;">Contact</strong><br>
            Coconut Development Authority<br>
            No. 11, Veluwana Mawatha, Rajagiriya
        </div>
    </div>

    <div style="font-size:0.85rem; opacity:0.75; margin-top:1.5rem;">
        Dashboard developed for academic purposes • BSc (Hons) Data Science & Analytics
    </div>
</div>
""", unsafe_allow_html=True)
