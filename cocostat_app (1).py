import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="COCOStat – Coconut Market Intelligence",
    page_icon="🥥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE – Language first!
# ─────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ─────────────────────────────────────────────
# TRANSLATIONS  (your original dictionary – shortened here for brevity)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# TRANSLATIONS – COMPLETE version
# ─────────────────────────────────────────────
T = {
    "en": {
        "title": "🥥 COCOStat",
        "subtitle": "Coconut Market Intelligence Dashboard",
        "tagline": "Understanding Coconut Prices in Simple Terms",
        "desc": "This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.",
        "lang_label": "🌐 Language",
        "lang_option": "සිංහල",
        "nav": ["📊 Overview", "🚦 Market", "📉 Demand", "🔮 Forecast", "🏛 Policy", "📈 History", "🧠 Method"],
        "card_price_label": "💰 Current Price",
        "card_price_value": "Rs. 68.50",
        "card_price_sub": "Per Nut (Auction)",
        "card_market_label": "📊 Market Condition",
        "card_market_value": "🟢 Stable",
        "card_market_sub": "Normal conditions",
        "card_demand_label": "📉 Demand Response",
        "card_demand_value": "Inelastic",
        "card_demand_sub": "People still buy",
        "card_forecast_label": "🔮 Future Trend",
        "card_forecast_value": "↑ Slight Rise",
        "card_forecast_sub": "Next 12 Weeks",
        "regime_title": "What is the Current Market Situation?",
        "regime_select": "Select Market Type to Explore",
        "regime_options": ["🟢 Stable Market", "🟡 Warning Market", "🔴 Crisis Market"],
        "regime_desc": [
            "Prices are normal and stable.",
            "Prices are changing moderately.",
            "Prices are very unstable.",
        ],
        "regime_avg": ["Rs. 52–65", "Rs. 65–80", "Rs. 80+"],
        "regime_vol": ["Low", "Medium", "High"],
        "regime_avg_label": "Average Price",
        "regime_vol_label": "Volatility",
        "regime_status_label": "Status",
        "regime_status": ["✅ OK", "⚠️ Watch", "🚨 Alert"],
        # Add remaining English keys from your original file if needed...
        "demand_title": "Do People Reduce Buying When Prices Increase?",
        # ... etc.
    },
    "si": {
        "title": "🥥 කොකොස්ටැට්",
        "subtitle": "පොල් වෙළඳපොළ විශ්ලේෂණ පද්ධතිය",
        "tagline": "පොල් මිල පහසුවෙන් තේරුම් ගනිමු",
        "desc": "මෙම පද්ධතිය පොල් මිල වෙනස්වීම්, ඉල්ලුම් හැසිරීම සහ ඉදිරි මිල අනාවැකි සරලව පැහැදිලි කරයි.",
        "lang_label": "🌐 භාෂාව",
        "lang_option": "English",
        "nav": ["📊 දළ විශ්ලේෂණය", "🚦 වෙළඳපොළ", "📉 ඉල්ලුම", "🔮 අනාවැකිය", "🏛 ප්‍රතිපත්ති", "📈 ඉතිහාසය", "🧠 ක්‍රමවේදය"],
        "card_price_label": "💰 වත්මන් මිල",
        "card_price_value": "රු. 68.50",
        "card_price_sub": "පොල් ගෙඩියකට (වෙන්දේසි)",
        "card_market_label": "📊 වෙළඳපොළ තත්ත්වය",
        "card_market_value": "🟢 ස්ථාවරයි",
        "card_market_sub": "සාමාන්‍ය තත්ත්වය",
        "card_demand_label": "📉 මිලට ප්‍රතිචාරය",
        "card_demand_value": "අජඩ",
        "card_demand_sub": "ඉල්ලුම අඩු නැත",
        "card_forecast_label": "🔮 ඉදිරි ප්‍රවණතාව",
        "card_forecast_value": "↑ සෙමින් ඉහළ",
        "card_forecast_sub": "ඉදිරි සති 12",
        "regime_title": "දැනට වෙළඳපොළේ තත්ත්වය කුමක්ද?",
        "regime_select": "ගවේෂණය කිරීමට වෙළඳ වර්ගයක් තෝරන්න",
        "regime_options": ["🟢 ස්ථාවර වෙළඳපොළ", "🟡 අවවාද වෙළඳපොළ", "🔴 අර්බුද වෙළඳපොළ"],
        "regime_desc": [
            "මිල ස්ථාවරයි, සාමාන්‍ය තත්ත්වය.",
            "මිල මධ්‍යම ලෙස වෙනස් වේ.",
            "මිල අතිශයින් අස්ථාවරයි.",
        ],
        "regime_avg": ["රු. 52–65", "රු. 65–80", "රු. 80+"],
        "regime_vol": ["අඩු", "මධ්‍යම", "ඉහළ"],
        "regime_avg_label": "සාමාන්‍ය මිල",
        "regime_vol_label": "අස්ථාවරතාව",
        "regime_status_label": "තත්ත්වය",
        "regime_status": ["✅ හොඳයි", "⚠️ නිරීක්ෂණය", "🚨 අවදානම"],
        "demand_title": "මිල ඉහළ ගෙලේ මිනිසුන් මිලදී ගැනීම අඩු කරයිද?",
        # ... add the rest of Sinhala keys from your original post ...
    }
}
t = T[st.session_state.lang]

# ─────────────────────────────────────────────
# GENERATE DATA (your original function)
# ─────────────────────────────────────────────
@st.cache_data
def generate_data():
    np.random.seed(42)
    dates = pd.date_range("2015-01-01", "2024-08-01", freq="MS")
    n = len(dates)
    base = 45 + np.sin(np.arange(n) / 8) * 12 + np.arange(n) * 0.18
    noise = np.random.normal(0, 4, n)
    prices = base + noise
    hist = pd.DataFrame({"date": dates, "price": prices.round(2)})
    hist["regime"] = pd.cut(hist["price"], bins=[0, 65, 80, 999], labels=[0, 1, 2]).astype(int)

    last = float(hist["price"].iloc[-1])
    future_dates = pd.date_range(hist["date"].iloc[-1] + pd.DateOffset(months=1), periods=12, freq="MS")
    future_prices = [last + i * 0.4 + np.random.normal(0, 1.5) for i in range(12)]
    upper = [p + 5 for p in future_prices]
    lower = [p - 5 for p in future_prices]
    forecast = pd.DataFrame({"date": future_dates, "price": np.round(future_prices, 2), "upper": np.round(upper, 2), "lower": np.round(lower, 2)})
    return hist, forecast

history_df, forecast_df = generate_data()

# ─────────────────────────────────────────────
# CUSTOM CSS – Coconut / Sri Lankan theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700&display=swap');

/* Light palm leaf subtle background */
.stApp {
    background: linear-gradient(rgba(240, 248, 240, 0.92), rgba(240, 248, 240, 0.88)),
                url('https://www.transparenttextures.com/patterns/coconut-palm-leaf.png') repeat;
    background-attachment: fixed;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans Sinhala', sans-serif;
}

/* Hide default header/footer */
#MainMenu, footer, header {visibility: hidden;}

/* Language selector top-right */
.lang-container {
    position: fixed;
    top: 12px;
    right: 24px;
    z-index: 999;
    background: white;
    border-radius: 999px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.12);
    padding: 6px 16px;
    font-size: 0.95rem;
}

/* Sidebar – coconut green theme */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e3a2f 0%, #2e5c48 100%) !important;
}
[data-testid="stSidebar"] * {
    color: #e8f5e9 !important;
}
.sidebar-title {
    color: #d4f4dd !important;
    font-size: 1.6rem !important;
    font-weight: 700;
    text-align: center;
    margin: 1.2rem 0;
}

/* Metrics / cards */
[data-testid="metric-container"] {
    background: #f0f9f0;
    border: 1px solid #a8d5a8;
    border-radius: 14px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}

/* Responsive fix */
@media (max-width: 768px) {
    .lang-container { right: 12px; top: 8px; padding: 5px 12px; font-size: 0.9rem; }
    .block-container { padding: 1rem 0.8rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── Language Selector – Top Right ──────────────────────────────────────────────
with st.container():
    st.markdown('<div class="lang-container">', unsafe_allow_html=True)
    lang_choice = st.radio(
        "Language / භාෂාව",
        ["English", "සිංහල"],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="lang_top"
    )
    new_lang = "en" if lang_choice == "English" else "si"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Hero Section (stable look) ─────────────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center; padding: 40px 20px 24px; background: rgba(240,248,240,0.6); border-radius: 0 0 24px 24px; margin-bottom: 24px;'>
    <span style='background:#dcedc8; padding:8px 18px; border-radius:30px; font-weight:700; color:#1b5e20;'>
        🥥🌴 {t["subtitle"]}
    </span>
    <h1 style='font-size:2.6rem; font-weight:900; color:#1e3a2f; margin:16px 0 8px;'>{t["tagline"]}</h1>
    <p style='color:#37474f; font-size:1.05rem; max-width:720px; margin:0 auto;'>{t["desc"]}</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🥥 COCOStat 🌴</div>', unsafe_allow_html=True)
    st.markdown("---")

    section = st.radio("Navigation 🍃", t["nav"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Active Market Regime** 🌴")
    active_regime = st.selectbox("", t["regime_options"], index=0)
    regime_idx = t["regime_options"].index(active_regime)

    st.markdown("<br>"*3, unsafe_allow_html=True)
    st.caption("Data last refreshed: " + datetime.now().strftime("%b %Y"))
    st.caption("Source: Coconut Development Authority – Sri Lanka")

# ─── Your page content logic (Overview / Market / etc.) ─────────────────────────
# Replace this block with your full if-elif chain from the original code
# Example placeholder – insert your real content here

if "Overview" in section or "දළ" in section:
    cols = st.columns(4)
    with cols[0]:
        st.metric(t["card_price_label"], t["card_price_value"], t["card_price_sub"])
    # ... continue with your other metrics, charts, etc. ...

# (insert the rest of your sections: Market, Demand, Forecast, Policy, History, Method)

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a2f, #2e5c48); color:white; padding:40px 24px; border-radius:16px; text-align:center; margin:40px 0 20px;">
    <div style="font-size:3rem; margin-bottom:12px;">🥥🌴🍃</div>
    <h3 style="margin:0; font-size:1.7rem;">Coconut Market Intelligence – Sri Lanka</h3>
    <p style="margin:12px 0 24px; opacity:0.9; max-width:800px; margin-left:auto; margin-right:auto;">
        Providing insights on coconut auction prices, demand behaviour and policy recommendations
    </p>
    <div style="display:flex; justify-content:center; gap:40px; flex-wrap:wrap;">
        <div>
            <strong style="opacity:0.8;">Institution</strong><br>
            Coconut Development Authority
        </div>
        <div>
            <strong style="opacity:0.8;">Address</strong><br>
            No. 11, Veluwana Mawatha<br>Rajagiriya, Sri Lanka
        </div>
        <div>
            <strong style="opacity:0.8;">Last Update</strong><br>
            {datetime.now().strftime("%B %Y")}
        </div>
    </div>
    <div style="margin-top:28px; font-size:0.9rem; opacity:0.75;">
        Academic project • BSc (Hons) Data Science & Analytics
    </div>
</div>
""", unsafe_allow_html=True)
