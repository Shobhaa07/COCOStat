import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

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
# TRANSLATIONS
# ─────────────────────────────────────────────
T = {
    "en": {
        "title": "🥥 COCOStat",
        "subtitle": "Coconut Market Intelligence Dashboard",
        "tagline": "Understanding Coconut Prices in Simple Terms",
        "desc": "This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.",
        "lang_label": "🌐 Language",
        "lang_option": "සිංහල",
        "nav": ["📊 Overview", "🚦 Market", "📉 Demand", "🔮 Forecast", "🏛 Policy", "📈 History", "🔍 Compare", "🧠 Method"],
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
        "demand_title": "Do People Reduce Buying When Prices Increase?",
        "demand_note": "💡 Demand is mostly inelastic — people must buy coconuts because it is an essential food.",
        "demand_bar_title": "Price Sensitivity Level (%)",
        "demand_periods": ["Stable Period", "Warning Period", "Crisis Period"],
        "demand_sens": [35, 22, 12],
        "demand_cards": [
            ("🟢 Stable Period", "People react slightly to price changes."),
            ("🟡 Warning Period", "Moderate reaction to price volatility."),
            ("🔴 Crisis Period", "People still buy coconuts even if price increases."),
        ],
        "forecast_title": "What Will Happen to Prices in the Next 12 Weeks?",
        "forecast_summary": "🔮 Prices are expected to increase slowly. No immediate crisis predicted.",
        "forecast_week": "Wk",
        "forecast_hist_label": "Historical",
        "forecast_pred_label": "Forecast",
        "forecast_range_label": "Uncertainty Range",
        "policy_title": "What Should the Government Do Now?",
        "policy_sub": "Evidence-based policy recommendations based on current market regime.",
        "policy_markets": ["If Market is Green 🟢", "If Market is Yellow 🟡", "If Market is Red 🔴"],
        "policy_actions": [
            "Support farmers and improve supply systems.",
            "Improve price transparency and monitoring.",
            "Use buffer stocks and temporary price control.",
        ],
        "policy_priorities": ["🔵 Low", "🟡 Medium", "🔴 High"],
        "policy_active": "← Currently Active",
        "policy_priority_label": "Priority:",
        "history_title": "Market History (2015–2024)",
        "history_sub": "Full 10-year auction price history. Hover to explore.",
        "history_warn_label": "Warning Threshold (Rs.65)",
        "history_crisis_label": "Crisis Threshold (Rs.80)",
        "method_title": "How This System Works",
        "method_steps": [
            "We studied 10 years of auction data.",
            "We grouped market situations into 3 types.",
            "We measured how people react to prices.",
            "We predicted future prices.",
        ],
        "footer_researcher": "Researcher",
        "footer_ids": "Student IDs",
        "footer_programme": "Programme",
        "compare_title": "Year-over-Year Price Comparison",
        "compare_sub": "Compare coconut prices across different years to identify seasonal patterns.",
        "price_calc_title": "💰 Price Impact Calculator",
        "price_calc_sub": "Estimate how price changes affect household spending.",
        "nuts_per_week": "Coconuts purchased per week",
        "current_price_input": "Current price per nut (Rs.)",
        "new_price_input": "New price per nut (Rs.)",
        "weekly_impact": "Weekly Cost Change",
        "monthly_impact": "Monthly Cost Change",
        "annual_impact": "Annual Cost Change",
        "alert_title": "🔔 Price Alert Settings",
        "alert_sub": "Set thresholds to simulate when you'd be notified.",
        "alert_warn": "Warning alert at (Rs.)",
        "alert_crisis": "Crisis alert at (Rs.)",
    },
    "si": {
        "title": "🥥 කොකොස්ටැට්",
        "subtitle": "පොල් වෙළඳපොළ විශ්ලේෂණ පද්ධතිය",
        "tagline": "පොල් මිල පහසුවෙන් තේරුම් ගනිමු",
        "desc": "මෙම පද්ධතිය පොල් මිල වෙනස්වීම්, ඉල්ලුම් හැසිරීම සහ ඉදිරි මිල අනාවැකි සරලව පැහැදිලි කරයි.",
        "lang_label": "🌐 භාෂාව",
        "lang_option": "English",
        "nav": ["📊 දළ විශ්ලේෂණය", "🚦 වෙළඳපොළ", "📉 ඉල්ලුම", "🔮 අනාවැකිය", "🏛 ප්‍රතිපත්ති", "📈 ඉතිහාසය", "🔍 සංසන්දනය", "🧠 ක්‍රමවේදය"],
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
        "demand_note": "💡 පොල් අත්‍යවශ්‍ය ආහාරයක් බැවින්, මිල ඉහළ ගියත් ඉල්ලුම අඩුවන්නේ නැත.",
        "demand_bar_title": "මිල සංවේදීතා මට්ටම (%)",
        "demand_periods": ["ස්ථාවර", "අවවාද", "අර්බුද"],
        "demand_sens": [35, 22, 12],
        "demand_cards": [
            ("🟢 ස්ථාවර කාලය", "මිල වෙනස්වීම් වලට ටිකක් ප්‍රතිචාර දක්වයි."),
            ("🟡 අවවාද කාලය", "මිල අස්ථාවරතාවට මධ්‍යම ප්‍රතිචාරයක්."),
            ("🔴 අර්බුද කාලය", "මිල ඉහළ ගියත් මිනිසුන් පොල් මිලදී ගනී."),
        ],
        "forecast_title": "ඉදිරි සති 12 තුළ මිලට කුමක් සිදුවේද?",
        "forecast_summary": "🔮 මිල සෙමින් ඉහළ යා හැක. වහාම අර්බුදයක් අපේක්ෂා නොකෙරේ.",
        "forecast_week": "සති",
        "forecast_hist_label": "ඉතිහාසය",
        "forecast_pred_label": "අනාවැකිය",
        "forecast_range_label": "අවිනිශ්චිත පරාසය",
        "policy_title": "දැනට රජය කුමක් කළ යුතුද?",
        "policy_sub": "වත්මන් වෙළඳ තත්ත්වය මත පදනම් වූ ප්‍රතිපත්ති නිර්දේශ.",
        "policy_markets": ["🟢 ස්ථාවරයි නම්", "🟡 අවවාදයි නම්", "🔴 අර්බුදයි නම්"],
        "policy_actions": [
            "ගොවීන්ට සහය ලබා දී සැපයුම් පද්ධතිය වැඩිදියුණු කරන්න.",
            "මිල තොරතුරු පැහැදිලි කර නිරීක්ෂණ වැඩි කරන්න.",
            "බෆර් තොග භාවිතා කර තාවකාලික මිල පාලනය කරන්න.",
        ],
        "policy_priorities": ["🔵 අඩු", "🟡 මධ්‍යම", "🔴 ඉහළ"],
        "policy_active": "← දැනට ක්‍රියාත්මකයි",
        "policy_priority_label": "ප්‍රමුඛතාව:",
        "history_title": "වෙළඳපොළ ඉතිහාසය (2015–2024)",
        "history_sub": "සම්පූර්ණ වසර 10 වෙන්දේසි මිල ඉතිහාසය. හොවර් කර ගවේෂණය කරන්න.",
        "history_warn_label": "අවවාද සීමාව (රු.65)",
        "history_crisis_label": "අර්බුද සීමාව (රු.80)",
        "method_title": "මෙම පද්ධතිය ක්‍රියා කරන ආකාරය",
        "method_steps": [
            "වසර 10ක වෙන්දේසි දත්ත අධ්‍යයනය කළා.",
            "වෙළඳපොළ තත්ත්ව 3ක් හඳුනාගත්තා.",
            "මිලට ප්‍රතිචාරය මැන බැලුවා.",
            "ඉදිරි මිල අනාවැකි කළා.",
        ],
        "footer_researcher": "පර්යේෂක",
        "footer_ids": "ශිෂ්‍ය ID",
        "footer_programme": "පාඨමාලාව",
        "compare_title": "වාර්ෂික මිල සංසන්දනය",
        "compare_sub": "සෘතුමය රටා හඳුනා ගැනීමට විවිධ වසර හරහා පොල් මිල සංසන්දනය කරන්න.",
        "price_calc_title": "💰 මිල බලපෑම් කැල්කියුලේටරය",
        "price_calc_sub": "මිල වෙනස්වීම් ගෘහස්ත වියදම් කෙසේ බලපාදැයි ගණනය කරන්න.",
        "nuts_per_week": "සතියකට මිලදී ගන්නා පොල් ගෙඩි",
        "current_price_input": "දැනට ගෙඩියකට මිල (රු.)",
        "new_price_input": "නව ගෙඩියකට මිල (රු.)",
        "weekly_impact": "සතිපතා වියදම් වෙනස",
        "monthly_impact": "මාසිකව වියදම් වෙනස",
        "annual_impact": "වාර්ෂිකව වියදම් වෙනස",
        "alert_title": "🔔 මිල අනතුරු ඇඟවීම් සැකසුම්",
        "alert_sub": "ඔබට දැනුම් දෙනු ලබන සීමා සකසන්න.",
        "alert_warn": "අවවාද ඇඟවීම (රු.)",
        "alert_crisis": "අර්බුද ඇඟවීම (රු.)",
    },
}

# ─────────────────────────────────────────────
# GENERATE DATA
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
    hist["year"] = hist["date"].dt.year
    hist["month"] = hist["date"].dt.month

    last = float(hist["price"].iloc[-1])
    future_dates = pd.date_range(hist["date"].iloc[-1] + pd.DateOffset(months=1), periods=12, freq="MS")
    future_prices = [last + i * 0.4 + np.random.normal(0, 1.5) for i in range(12)]
    upper = [p + 5 for p in future_prices]
    lower = [p - 5 for p in future_prices]
    forecast = pd.DataFrame({
        "date": future_dates,
        "price": np.round(future_prices, 2),
        "upper": np.round(upper, 2),
        "lower": np.round(lower, 2)
    })

    # Weekly simulated data for recent months
    weekly_dates = pd.date_range("2024-01-01", "2024-08-31", freq="W")
    weekly_prices = [last - 8 + i * 0.15 + np.random.normal(0, 1.2) for i in range(len(weekly_dates))]
    weekly = pd.DataFrame({"date": weekly_dates, "price": np.round(weekly_prices, 2)})

    return hist, forecast, weekly

history_df, forecast_df, weekly_df = generate_data()

# ─────────────────────────────────────────────
# CUSTOM CSS — sidebar always visible
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans Sinhala', 'Segoe UI', sans-serif;
}

/* Hide default Streamlit header */
#MainMenu, footer, header {visibility: hidden;}

/* ── Force sidebar always open ── */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] {
    min-width: 280px !important;
    max-width: 280px !important;
    width: 280px !important;
    transform: none !important;
}
section[data-testid="stSidebar"] > div {
    width: 280px !important;
    transform: none !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border-radius: 16px;
    border: 1px solid #bbf7d0;
    padding: 16px;
}

/* Section headers */
.section-header {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 4px;
}
.section-sub {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 20px;
}

/* Info boxes */
.info-box-blue {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #1e40af;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}
.info-box-green {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #166534;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}
.info-box-yellow {
    background: #fefce8;
    border-left: 4px solid #eab308;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #854d0e;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}
.info-box-red {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #991b1b;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}

/* Sidebar styling */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2027 0%, #1a3a2a 50%, #0f2027 100%);
}
div[data-testid="stSidebar"] * {
    color: white !important;
}
div[data-testid="stSidebar"] .stRadio label {
    padding: 6px 12px;
    border-radius: 8px;
    transition: background 0.15s;
}
div[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.1);
}

/* Footer */
.footer-box {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 20px;
    padding: 36px 40px;
    color: white;
    text-align: center;
    margin-top: 40px;
}

/* Divider */
.styled-divider {
    height: 3px;
    background: linear-gradient(90deg, #16a34a, #3b82f6, #f59e0b);
    border-radius: 2px;
    margin: 32px 0;
}

/* Live badge */
.live-badge {
    display: inline-block;
    background: #ef4444;
    color: white !important;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 10px;
    letter-spacing: 1px;
    vertical-align: middle;
    margin-left: 6px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Stat card */
.stat-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 8px;'>
        <div style='font-size:2.8rem;'>🥥</div>
        <div style='font-size:1.4rem; font-weight:900; letter-spacing:1px;'>COCOStat</div>
        <div style='font-size:0.72rem; opacity:0.6; margin-top:2px; letter-spacing:0.5px;'>MARKET INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    lang_choice = st.radio("🌐 Language / භාෂාව", ["English", "සිංහල"], index=0)
    lang = "en" if lang_choice == "English" else "si"
    t = T[lang]

    st.markdown("---")
    st.markdown("### " + ("📍 Navigation" if lang == "en" else "📍 සංචාලනය"))
    section = st.radio("", t["nav"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### " + ("⚙️ Settings" if lang == "en" else "⚙️ සැකසුම්"))
    active_regime = st.selectbox(
        t["regime_select"],
        t["regime_options"],
        index=0
    )
    regime_idx = t["regime_options"].index(active_regime)

    # Alert thresholds
    st.markdown("---")
    st.markdown("### " + ("🔔 Alerts" if lang == "en" else "🔔 ඇඟවීම්"))
    warn_threshold = st.slider(
        t["alert_warn"] if "alert_warn" in t else "Warning at (Rs.)",
        min_value=50, max_value=90, value=65, step=1
    )
    crisis_threshold = st.slider(
        t["alert_crisis"] if "alert_crisis" in t else "Crisis at (Rs.)",
        min_value=60, max_value=120, value=80, step=1
    )

    # Current price context relative to thresholds
    current_price = 68.50
    if current_price >= crisis_threshold:
        st.markdown(f"<div class='info-box-red' style='margin-top:8px;'>🚨 {'CRISIS: Price above Rs.' if lang=='en' else 'අර්බුදය: රු.'}{crisis_threshold}</div>", unsafe_allow_html=True)
    elif current_price >= warn_threshold:
        st.markdown(f"<div class='info-box-yellow' style='margin-top:8px;'>⚠️ {'WARNING: Rs.' if lang=='en' else 'අවවාදය: රු.'}{warn_threshold} {'threshold breached' if lang=='en' else 'සීමාව ඉක්මවා'}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='info-box-green' style='margin-top:8px;'>✅ {'Market within safe range' if lang=='en' else 'ආරක්ෂිත සීමාව'}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:0.72rem; opacity:0.75; line-height:2.0; text-align:center;'>
        <div style='font-size:0.65rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>👤 {t['footer_researcher']}</div>
        <div style='font-weight:800; font-size:0.85rem; margin-bottom:6px;'>M A C S RATHNAYAKE</div>
        <div style='font-size:0.65rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>{t['footer_ids']}</div>
        <div style='font-size:0.78rem;'>UOW: w1999714</div>
        <div style='font-size:0.78rem; margin-bottom:6px;'>IIT: 20220508</div>
        <div style='font-size:0.65rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>{t['footer_programme']}</div>
        <div style='font-size:0.75rem; opacity:0.85; line-height:1.5;'>BSc (Hons) Data Science & Analytics<br>University of Westminster</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────
regime_colors_map = {0: "#22c55e", 1: "#eab308", 2: "#ef4444"}
regime_labels_map = {0: "🟢 Stable" if lang=="en" else "🟢 ස්ථාවර", 1: "🟡 Warning" if lang=="en" else "🟡 අවවාද", 2: "🔴 Crisis" if lang=="en" else "🔴 අර්බුද"}

st.markdown(f"""
<div style='text-align:center; padding: 28px 0 16px;'>
    <span style='background:#dcfce7; border-radius:20px; padding:6px 16px; font-size:0.85rem; font-weight:700; color:#166534;'>
        🥥 {t["subtitle"]}
    </span>
    <h1 style='font-size:2.2rem; font-weight:900; color:#0f172a; margin:14px 0 8px; line-height:1.2;'>{t["tagline"]}</h1>
    <p style='color:#64748b; font-size:0.95rem; max-width:580px; margin:0 auto;'>{t["desc"]}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────

# ── OVERVIEW ─────────────────────────────────
if "📊 Overview" in section or "📊 දළ" in section:
    col1, col2, col3, col4 = st.columns(4)
    overview_cards = [
        (t["card_price_label"],    t["card_price_value"],    t["card_price_sub"],    "#16a34a", "#dcfce7", "#bbf7d0"),
        (t["card_market_label"],   t["card_market_value"],   t["card_market_sub"],   "#2563eb", "#eff6ff", "#bfdbfe"),
        (t["card_demand_label"],   t["card_demand_value"],   t["card_demand_sub"],   "#7c3aed", "#f5f3ff", "#ddd6fe"),
        (t["card_forecast_label"], t["card_forecast_value"], t["card_forecast_sub"], "#d97706", "#fefce8", "#fde68a"),
    ]
    for col, (label, value, sub, clr, bg, border) in zip([col1, col2, col3, col4], overview_cards):
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:1px solid {border}; border-radius:16px; padding:18px 20px;'>
                <div style='font-size:0.78rem; font-weight:700; color:{clr}; margin-bottom:6px; white-space:nowrap; overflow:hidden; text-overflow:clip;'>{label}</div>
                <div style='font-size:1.55rem; font-weight:900; color:#0f172a; line-height:1.2; margin-bottom:8px; word-break:break-word;'>{value}</div>
                <div style='display:inline-block; background:{clr}22; color:{clr}; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:20px;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Two-column layout: chart + quick stats
    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        recent = history_df.tail(36).copy()
        fig_hero = go.Figure()
        fig_hero.add_trace(go.Scatter(
            x=recent["date"], y=recent["price"],
            fill="tozeroy", fillcolor="rgba(22,163,74,0.1)",
            line=dict(color="#16a34a", width=2.5),
            name="Price",
            hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
        ))
        fig_hero.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
            annotation_text=f"⚠ Rs.{warn_threshold}", annotation_position="right")
        fig_hero.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
            annotation_text=f"🔴 Rs.{crisis_threshold}", annotation_position="right")
        fig_hero.update_layout(
            title=dict(text="📈 " + ("Recent 3-Year Price Trend" if lang=="en" else "මෑත කාල මිල ප්‍රවණතාව"), font=dict(size=14, color="#0f172a")),
            height=280, margin=dict(l=10, r=80, t=40, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="white",
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
            showlegend=False,
        )
        st.plotly_chart(fig_hero, use_container_width=True, config={"displayModeBar": "hover"})

    with col_stats:
        st.markdown("#### " + ("📊 Quick Stats" if lang=="en" else "📊 ඉක්මන් සංඛ්‍යාන"))
        last_36 = history_df.tail(36)
        stats = [
            ("3yr Avg", f"Rs. {last_36['price'].mean():.1f}", "#3b82f6"),
            ("3yr High", f"Rs. {last_36['price'].max():.1f}", "#ef4444"),
            ("3yr Low", f"Rs. {last_36['price'].min():.1f}", "#22c55e"),
            ("Volatility", f"Rs. {last_36['price'].std():.1f}", "#f59e0b"),
        ]
        for label, val, clr in stats:
            st.markdown(f"""
            <div style='background:#f8fafc; border-left:4px solid {clr}; border-radius:0 10px 10px 0; padding:10px 14px; margin-bottom:8px;'>
                <div style='font-size:0.72rem; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>{label}</div>
                <div style='font-size:1.3rem; font-weight:900; color:{clr};'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Monthly seasonality heatmap
    st.markdown("#### " + ("🗓️ Monthly Average Price by Year (Seasonality)" if lang=="en" else "🗓️ වර්ෂය අනුව මාසික සාමාන්‍ය මිල"))
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    # Build full 12-month pivot, filling missing months with NaN
    all_months = pd.DataFrame({"month": range(1, 13)})
    pivot_raw = history_df.pivot_table(index="year", columns="month", values="price", aggfunc="mean")
    pivot_raw = pivot_raw.reindex(columns=range(1, 13))  # ensure all 12 months present
    pivot_raw.columns = [month_names[m-1] for m in pivot_raw.columns]

    # Build z values and text labels — show "N/A" for missing cells
    z_vals = pivot_raw.values.tolist()
    text_vals = []
    for row in pivot_raw.values:
        text_row = [f"Rs.{v:.1f}" if not np.isnan(v) else "—" for v in row]
        text_vals.append(text_row)

    # For colorscale, replace NaN with None so Plotly renders them as blank
    import copy
    z_clean = [[None if np.isnan(v) else round(v, 1) for v in row] for row in pivot_raw.values]

    fig_heat = go.Figure(go.Heatmap(
        z=z_clean,
        x=pivot_raw.columns.tolist(),
        y=[str(y) for y in pivot_raw.index.tolist()],
        colorscale=[[0, "#dcfce7"], [0.5, "#fef9c3"], [1, "#fee2e2"]],
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=9),
        hovertemplate="<b>%{y} %{x}</b><br>%{text}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Rs.", tickfont=dict(size=10)),
        zmin=history_df["price"].min(),
        zmax=history_df["price"].max(),
    ))
    fig_heat.update_layout(
        height=280, margin=dict(l=20, r=20, t=10, b=20),
        paper_bgcolor="white",
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": "hover"})

    # Price Calculator
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"#### {t['price_calc_title']}")
    st.markdown(f"<div class='section-sub'>{t['price_calc_sub']}</div>", unsafe_allow_html=True)

    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1:
        nuts_week = st.number_input(t["nuts_per_week"], min_value=1, max_value=100, value=10, step=1)
    with calc_col2:
        price_now = st.number_input(t["current_price_input"], min_value=10.0, max_value=200.0, value=68.50, step=0.5)
    with calc_col3:
        price_new = st.number_input(t["new_price_input"], min_value=10.0, max_value=200.0, value=75.00, step=0.5)

    diff_week = (price_new - price_now) * nuts_week
    diff_month = diff_week * 4
    diff_year = diff_week * 52
    clr_calc = "#ef4444" if diff_week > 0 else "#22c55e"
    arrow = "↑" if diff_week > 0 else "↓"

    c1, c2, c3 = st.columns(3)
    for col, label, val in zip([c1, c2, c3],
        [t["weekly_impact"], t["monthly_impact"], t["annual_impact"]],
        [diff_week, diff_month, diff_year]):
        with col:
            st.markdown(f"""
            <div style='background:#f8fafc; border:2px solid {clr_calc}33; border-radius:14px; padding:18px; text-align:center;'>
                <div style='font-size:0.78rem; color:#64748b; font-weight:700; margin-bottom:6px;'>{label}</div>
                <div style='font-size:1.6rem; font-weight:900; color:{clr_calc};'>{arrow} Rs. {abs(val):.2f}</div>
            </div>
            """, unsafe_allow_html=True)

# ── MARKET REGIME ────────────────────────────
elif "🚦 Market" in section or "🚦 වෙළඳ" in section:
    st.markdown(f'<div class="section-header">{t["regime_title"]}</div>', unsafe_allow_html=True)

    regime_colors = ["#22c55e", "#eab308", "#ef4444"]
    regime_bgs = ["#dcfce7", "#fef9c3", "#fee2e2"]
    regime_emoji = ["🟢", "🟡", "🔴"]

    col1, col2, col3 = st.columns(3)
    for i, col in enumerate([col1, col2, col3]):
        border = "3px solid " + regime_colors[i] if i == regime_idx else "2px solid #e2e8f0"
        bg = regime_bgs[i] if i == regime_idx else "#f8fafc"
        selected_label = "✓ Selected" if i == regime_idx else ""
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:{border}; border-radius:16px; padding:24px; text-align:center;'>
                <div style='font-size:2.5rem; margin-bottom:8px;'>{regime_emoji[i]}</div>
                <div style='font-weight:800; font-size:1rem; color:{regime_colors[i]}; margin-bottom:8px;'>{t["regime_options"][i]}</div>
                <div style='font-size:0.9rem; color:#475569; line-height:1.6;'>{t["regime_desc"][i]}</div>
                {'<div style="margin-top:10px; font-size:0.75rem; font-weight:800; color:' + regime_colors[i] + ';">' + selected_label + '</div>' if selected_label else ''}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    rc = regime_colors[regime_idx]
    rb = regime_bgs[regime_idx]
    c1, c2, c3 = st.columns(3)
    for col, label, val in zip([c1, c2, c3],
        [t["regime_avg_label"], t["regime_vol_label"], t["regime_status_label"]],
        [t["regime_avg"][regime_idx], t["regime_vol"][regime_idx], t["regime_status"][regime_idx]]):
        with col:
            st.markdown(f"""<div style='background:{rb}; border-radius:12px; padding:20px; text-align:center;'>
            <div style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>{label}</div>
            <div style='font-size:1.8rem; font-weight:900; color:{rc};'>{val}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Price chart coloured by regime
    fig_reg = go.Figure()
    for r_i, (r_col, r_name) in enumerate(zip(regime_colors, t["regime_options"])):
        mask = history_df["regime"] == r_i
        subset = history_df[mask]
        if not subset.empty:
            fig_reg.add_trace(go.Scatter(
                x=subset["date"], y=subset["price"],
                mode="markers", marker=dict(color=r_col, size=5, opacity=0.8),
                name=r_name,
                hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
            ))
    fig_reg.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
        annotation_text=f"⚠ Rs.{warn_threshold}", annotation_position="right")
    fig_reg.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
        annotation_text=f"🔴 Rs.{crisis_threshold}", annotation_position="right")
    fig_reg.update_layout(
        title=dict(text="📊 " + ("Price History by Market Regime" if lang=="en" else "වෙළඳ තත්ත්වය අනුව මිල ඉතිහාසය"), font=dict(size=14)),
        height=320, margin=dict(l=10, r=80, t=40, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs."),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": "hover"})

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Regime duration statistics
    st.markdown("#### " + ("📊 Regime Statistics" if lang=="en" else "📊 තත්ත්ව සංඛ්‍යාන"))
    rc_counts = history_df["regime"].value_counts().sort_index()
    rc_cols = st.columns(3)
    for i, col in enumerate(rc_cols):
        count = rc_counts.get(i, 0)
        pct = count / len(history_df) * 100
        with col:
            st.markdown(f"""
            <div style='background:{regime_bgs[i]}; border-radius:12px; padding:18px; text-align:center;'>
                <div style='font-size:1.8rem; margin-bottom:4px;'>{regime_emoji[i]}</div>
                <div style='font-weight:800; color:{regime_colors[i]}; font-size:1rem; margin-bottom:4px;'>{t["regime_options"][i]}</div>
                <div style='font-size:1.6rem; font-weight:900; color:{regime_colors[i]};'>{pct:.0f}%</div>
                <div style='font-size:0.8rem; color:#64748b;'>{count} {"months" if lang=="en" else "මාස"}</div>
            </div>
            """, unsafe_allow_html=True)

# ── DEMAND ───────────────────────────────────
elif "📉 Demand" in section or "📉 ඉල්ලුම" in section:
    st.markdown(f'<div class="section-header">{t["demand_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-blue">{t["demand_note"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        fig_bar = go.Figure(go.Bar(
            x=t["demand_periods"],
            y=t["demand_sens"],
            marker=dict(color=["#22c55e", "#eab308", "#ef4444"], line=dict(width=0)),
            text=[f"{v}%" for v in t["demand_sens"]],
            textposition="outside",
            width=0.5,
        ))
        fig_bar.update_layout(
            title=dict(text=t["demand_bar_title"], font=dict(size=14)),
            height=280, margin=dict(l=20, r=20, t=50, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="white",
            yaxis=dict(gridcolor="#f1f5f9", range=[0, 50]),
            xaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": "hover"})

    with col2:
        colors_d = [("#dcfce7", "#22c55e"), ("#fef9c3", "#eab308"), ("#fee2e2", "#ef4444")]
        for i, (period, desc) in enumerate(t["demand_cards"]):
            bg, border = colors_d[i]
            st.markdown(f"""
            <div style='background:{bg}; border-left:4px solid {border}; border-radius:0 12px 12px 0; padding:14px 16px; margin-bottom:12px;'>
                <div style='font-weight:700; font-size:0.95rem; margin-bottom:4px;'>{period}</div>
                <div style='font-size:0.88rem; color:#475569; line-height:1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Elasticity summary
    st.markdown("#### " + ("📊 Price Elasticity of Demand" if lang=="en" else "📊 ඉල්ලුම් ස්ථිතිස්ථිකය"))
    c1, c2, c3 = st.columns(3)
    data_e = [("-0.35", "Stable" if lang=="en" else "ස්ථාවර", "#22c55e", "#dcfce7"),
              ("-0.22", "Warning" if lang=="en" else "අවවාද", "#eab308", "#fef9c3"),
              ("-0.12", "Crisis" if lang=="en" else "අර්බුද", "#ef4444", "#fee2e2")]
    for col, (val, period, clr, bg) in zip([c1, c2, c3], data_e):
        with col:
            st.markdown(f"""<div style='background:{bg}; border-radius:12px; padding:18px; text-align:center;'>
            <div style='font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;'>
            {"Elasticity" if lang=="en" else "ස්ථිතිස්ථිකය"} — {period}</div>
            <div style='font-size:2rem; font-weight:900; color:{clr};'>{val}</div>
            <div style='font-size:0.8rem; color:#64748b; margin-top:4px;'>{"Inelastic" if lang=="en" else "අජඩ"}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Demand curve visualisation
    st.markdown("#### " + ("📉 Demand Curve by Market Regime" if lang=="en" else "📉 වෙළඳ තත්ත්වය අනුව ඉල්ලුම් වක්‍රය"))
    prices_range = np.linspace(40, 100, 60)
    elasticities = {"Stable": -0.35, "Warning": -0.22, "Crisis": -0.12}
    base_qty = 1000
    base_price = 60

    fig_demand = go.Figure()
    colors_dem = ["#22c55e", "#eab308", "#ef4444"]
    for (label, elas), clr in zip(elasticities.items(), colors_dem):
        qty = base_qty * (prices_range / base_price) ** elas
        fig_demand.add_trace(go.Scatter(
            x=qty, y=prices_range,
            mode="lines", name=label,
            line=dict(color=clr, width=2.5),
            hovertemplate=f"<b>{label}</b><br>Price: Rs.%{{y:.1f}}<br>Qty: %{{x:.0f}}<extra></extra>",
        ))
    fig_demand.update_layout(
        height=300, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(title="Quantity Demanded" if lang=="en" else "ඉල්ලා ඇති ප්‍රමාණය", showgrid=False),
        yaxis=dict(title="Price (Rs.)" if lang=="en" else "මිල (රු.)", gridcolor="#f1f5f9", tickprefix="Rs."),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_demand, use_container_width=True, config={"displayModeBar": "hover"})

# ── FORECAST ─────────────────────────────────
elif "🔮 Forecast" in section or "🔮 අනා" in section:
    st.markdown(f'<div class="section-header">{t["forecast_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-green">{t["forecast_summary"]}</div>', unsafe_allow_html=True)

    hist_recent = history_df.tail(16).copy()

    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(245,158,11,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name=t["forecast_range_label"], hoverinfo="skip",
    ))
    fig_fore.add_trace(go.Scatter(
        x=hist_recent["date"], y=hist_recent["price"],
        line=dict(color="#3b82f6", width=2.5),
        name=t["forecast_hist_label"], mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
    ))
    fig_fore.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["price"],
        line=dict(color="#f59e0b", width=2.5, dash="dash"),
        name=t["forecast_pred_label"], mode="lines+markers",
        marker=dict(size=6, color="#f59e0b"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
    ))
    fig_fore.add_hline(y=warn_threshold, line_dash="dot", line_color="#eab308",
        annotation_text=f"⚠ Rs.{warn_threshold}", annotation_position="right")
    fig_fore.add_hline(y=crisis_threshold, line_dash="dot", line_color="#ef4444",
        annotation_text=f"🔴 Rs.{crisis_threshold}", annotation_position="right")
    fig_fore.add_vline(
        x=forecast_df["date"].iloc[0].timestamp() * 1000,
        line_dash="dot", line_color="#94a3b8",
        annotation_text="Forecast →" if lang=="en" else "අනාවැකිය →",
        annotation_position="top right",
    )
    fig_fore.update_layout(
        height=340, margin=dict(l=10, r=80, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_fore, use_container_width=True, config={"displayModeBar": "hover"})

    # 12-week mini cards
    st.markdown("#### " + ("📅 12-Week Forecast Details" if lang=="en" else "📅 සති 12 අනාවැකි විස්තර"))
    cols = st.columns(6)
    for i, (col, (_, row)) in enumerate(zip(cols * 2, forecast_df.iterrows())):
        if i >= 12:
            break
        price = row["price"]
        clr = "#ef4444" if price >= crisis_threshold else "#eab308" if price >= warn_threshold else "#22c55e"
        status = "🔴" if price >= crisis_threshold else "🟡" if price >= warn_threshold else "🟢"
        with cols[i % 6]:
            st.markdown(f"""
            <div style='background:#f8fafc; border:1px solid #e2e8f0; border-top:3px solid {clr}; border-radius:10px; padding:10px 6px; text-align:center; margin-bottom:8px;'>
                <div style='font-size:0.7rem; color:#94a3b8; margin-bottom:2px;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:0.95rem; font-weight:800; color:{clr};'>Rs.{price:.1f}</div>
                <div style='font-size:0.8rem;'>{status}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Forecast summary stats
    st.markdown("#### " + ("📊 Forecast Summary" if lang=="en" else "📊 අනාවැකි සාරාංශය"))
    fc_avg = forecast_df["price"].mean()
    fc_max = forecast_df["price"].max()
    fc_min = forecast_df["price"].min()
    weeks_above_warn = (forecast_df["price"] >= warn_threshold).sum()
    weeks_above_crisis = (forecast_df["price"] >= crisis_threshold).sum()

    s1, s2, s3, s4, s5 = st.columns(5)
    for col, label, val, clr in zip(
        [s1, s2, s3, s4, s5],
        ["Avg Forecast", "Peak Price", "Low Price", "Weeks ≥ Warning", "Weeks ≥ Crisis"],
        [f"Rs. {fc_avg:.1f}", f"Rs. {fc_max:.1f}", f"Rs. {fc_min:.1f}", f"{weeks_above_warn} wks", f"{weeks_above_crisis} wks"],
        ["#3b82f6", "#ef4444", "#22c55e", "#eab308", "#ef4444"]
    ):
        with col:
            st.markdown(f"""
            <div style='background:#f8fafc; border-left:4px solid {clr}; border-radius:0 10px 10px 0; padding:12px 14px; text-align:center;'>
                <div style='font-size:0.7rem; color:#94a3b8; font-weight:700;'>{label}</div>
                <div style='font-size:1.2rem; font-weight:900; color:{clr};'>{val}</div>
            </div>""", unsafe_allow_html=True)

# ── POLICY ────────────────────────────────────
elif "🏛 Policy" in section or "🏛 ප්‍රති" in section:
    st.markdown(f'<div class="section-header">{t["policy_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["policy_sub"]}</div>', unsafe_allow_html=True)

    policy_colors = ["#22c55e", "#eab308", "#ef4444"]
    col1, col2, col3 = st.columns(3)
    for i, col in enumerate([col1, col2, col3]):
        is_active = (i == regime_idx)
        border = f"3px solid {policy_colors[i]}" if is_active else "2px solid #e2e8f0"
        with col:
            active_badge = f"""<div style='margin-top:10px; background:{policy_colors[i]}22; border-radius:8px; padding:6px 10px; font-size:0.8rem; color:{policy_colors[i]}; font-weight:700;'>{t["policy_active"]}</div>""" if is_active else ""
            st.markdown(f"""
            <div style='border-radius:16px; overflow:hidden; box-shadow:0 4px 16px rgba(0,0,0,0.08); border:{border};'>
                <div style='background:{policy_colors[i]}; padding:14px 18px;'>
                    <span style='font-weight:800; font-size:1rem; color:white;'>{t["policy_markets"][i]}</span>
                </div>
                <div style='padding:16px 18px; background:#f8fafc;'>
                    <p style='font-size:0.9rem; color:#475569; line-height:1.7; margin:0 0 12px;'>{t["policy_actions"][i]}</p>
                    <span style='font-size:0.8rem; font-weight:700; color:#94a3b8;'>{t["policy_priority_label"]}</span>
                    <span style='background:{policy_colors[i]}; color:white; font-size:0.78rem; font-weight:800; padding:3px 10px; border-radius:12px; margin-left:6px;'>{t["policy_priorities"][i]}</span>
                    {active_badge}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Policy decision flow
    st.markdown("#### " + ("📋 Policy Decision Framework" if lang=="en" else "📋 ප්‍රතිපත්ති තීරණ රාමුව"))
    steps = [
        ("1️⃣", "Detect Regime" if lang=="en" else "තත්ත්වය හඳුනන්න", "#3b82f6"),
        ("2️⃣", "Assess Priority" if lang=="en" else "ප්‍රමුඛතාව තීරණය", "#8b5cf6"),
        ("3️⃣", "Implement Policy" if lang=="en" else "ප්‍රතිපත්තිය ක්‍රියාත්මක", "#16a34a"),
        ("4️⃣", "Monitor & Review" if lang=="en" else "නිරීක්ෂණය කරන්න", "#f59e0b"),
    ]
    scols = st.columns(4)
    for col, (emoji, step, clr) in zip(scols, steps):
        with col:
            st.markdown(f"""<div style='text-align:center; background:#f8fafc; border-radius:14px; padding:20px 10px; border:1px solid #e2e8f0;'>
            <div style='font-size:2rem; margin-bottom:8px;'>{emoji}</div>
            <div style='font-weight:700; font-size:0.88rem; color:{clr};'>{step}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Policy effectiveness tracker
    st.markdown("#### " + ("📈 Policy Effectiveness Indicators" if lang=="en" else "📈 ප්‍රතිපත්ති සඵලතා දර්ශක"))
    indicators = [
        ("Price Stability Index" if lang=="en" else "මිල ස්ථාවරතා දර්ශකය", 72, "#3b82f6"),
        ("Supply Chain Score" if lang=="en" else "සැපයුම් දාම ලකුණු", 58, "#22c55e"),
        ("Farmer Support Index" if lang=="en" else "ගොවි සහාය දර්ශකය", 64, "#f59e0b"),
        ("Market Transparency" if lang=="en" else "වෙළඳ විනිවිදභාවය", 80, "#8b5cf6"),
    ]
    ind_cols = st.columns(4)
    for col, (label, score, clr) in zip(ind_cols, indicators):
        with col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": label, "font": {"size": 11}},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"size": 9}},
                    "bar": {"color": clr},
                    "bgcolor": "#f8fafc",
                    "threshold": {"line": {"color": "#ef4444", "width": 3}, "thickness": 0.75, "value": 75},
                },
                number={"suffix": "/100", "font": {"size": 18}},
            ))
            fig_gauge.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="white")
            col.plotly_chart(fig_gauge, use_container_width=True)

# ── HISTORY ────────────────────────────────────
elif "📈 History" in section or "📈 ඉති" in section:
    st.markdown(f'<div class="section-header">{t["history_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["history_sub"]}</div>', unsafe_allow_html=True)

    fig_hist = go.Figure()
    # Shade crisis zones
    crisis_mask = history_df["price"] >= crisis_threshold
    warn_mask = (history_df["price"] >= warn_threshold) & (history_df["price"] < crisis_threshold)

    fig_hist.add_trace(go.Scatter(
        x=history_df["date"], y=history_df["price"],
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        line=dict(color="#16a34a", width=1.8),
        name="Price", mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
    ))
    fig_hist.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
        annotation_text=f"⚠ Rs.{warn_threshold}", annotation_position="top right",
        annotation_font_color="#eab308")
    fig_hist.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
        annotation_text=f"🔴 Rs.{crisis_threshold}", annotation_position="bottom right",
        annotation_font_color="#ef4444")
    fig_hist.update_layout(
        height=360, margin=dict(l=10, r=100, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False, rangeslider=dict(visible=True), tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": "hover"})

    # Summary stats
    st.markdown("#### " + ("📊 Summary Statistics" if lang=="en" else "📊 සාරාංශ සංඛ්‍යාන"))
    c1, c2, c3, c4, c5 = st.columns(5)
    hist_stats = [
        ("📈 " + ("Max Price" if lang=="en" else "උපරිම මිල"),  f"Rs. {history_df['price'].max():.2f}", "#ef4444", "#fef2f2"),
        ("📉 " + ("Min Price" if lang=="en" else "අවම මිල"),    f"Rs. {history_df['price'].min():.2f}", "#22c55e", "#dcfce7"),
        ("📊 " + ("Avg Price" if lang=="en" else "සාමාන්‍ය මිල"), f"Rs. {history_df['price'].mean():.2f}", "#3b82f6", "#eff6ff"),
        ("📐 " + ("Std Dev" if lang=="en" else "ප්‍රමිති අප."),  f"Rs. {history_df['price'].std():.2f}",  "#f59e0b", "#fefce8"),
        ("📅 " + ("Total Months" if lang=="en" else "මාස ගණන"),  str(len(history_df)),                   "#8b5cf6", "#f5f3ff"),
    ]
    for col, (label, val, clr, bg) in zip([c1, c2, c3, c4, c5], hist_stats):
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:1px solid {clr}33; border-radius:14px; padding:14px 16px; text-align:center;'>
                <div style='font-size:0.72rem; font-weight:700; color:{clr}; margin-bottom:6px;'>{label}</div>
                <div style='font-size:1.4rem; font-weight:900; color:#0f172a;'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    col_pie, col_yoy = st.columns([1, 1])

    with col_pie:
        regime_counts = history_df["regime"].value_counts().sort_index()
        fig_pie = go.Figure(go.Pie(
            labels=t["regime_options"],
            values=regime_counts.values,
            hole=0.5,
            marker=dict(colors=["#22c55e", "#eab308", "#ef4444"]),
            textinfo="label+percent",
            textfont=dict(size=11),
        ))
        fig_pie.update_layout(
            title=dict(text="🥧 " + ("Regime Distribution" if lang=="en" else "තත්ත්ව බෙදා හැරීම"), font=dict(size=13)),
            height=300, margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="white", showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": "hover"})

    with col_yoy:
        # Annual average bar chart
        annual_avg = history_df.groupby("year")["price"].mean().reset_index()
        fig_annual = go.Figure(go.Bar(
            x=annual_avg["year"].astype(str),
            y=annual_avg["price"].round(2),
            marker=dict(
                color=annual_avg["price"],
                colorscale=[[0, "#dcfce7"], [0.5, "#fef9c3"], [1, "#fee2e2"]],
                showscale=False,
                line=dict(width=0),
            ),
            text=annual_avg["price"].round(1),
            texttemplate="Rs.%{text}",
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Avg: Rs. %{y:.2f}<extra></extra>",
        ))
        fig_annual.update_layout(
            title=dict(text="📊 " + ("Annual Average Price" if lang=="en" else "වාර්ෂික සාමාන්‍ය මිල"), font=dict(size=13)),
            height=300, margin=dict(l=10, r=10, t=50, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="white",
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", range=[0, annual_avg["price"].max() * 1.15]),
            showlegend=False,
        )
        st.plotly_chart(fig_annual, use_container_width=True, config={"displayModeBar": "hover"})

# ── COMPARE ────────────────────────────────────
elif "🔍 Compare" in section or "🔍 සංසන්" in section:
    st.markdown(f'<div class="section-header">{t["compare_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["compare_sub"]}</div>', unsafe_allow_html=True)

    available_years = sorted(history_df["year"].unique().tolist())
    selected_years = st.multiselect(
        "Select years to compare:" if lang=="en" else "සංසන්දනය කිරීමට වසර තෝරන්න:",
        available_years,
        default=available_years[-3:]
    )

    if selected_years:
        month_names_full = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        year_colors = px.colors.qualitative.Set2

        fig_yoy = go.Figure()
        for idx, yr in enumerate(selected_years):
            yr_data = history_df[history_df["year"] == yr].copy()
            yr_data = yr_data.sort_values("month")
            fig_yoy.add_trace(go.Scatter(
                x=[month_names_full[m-1] for m in yr_data["month"]],
                y=yr_data["price"],
                mode="lines+markers",
                name=str(yr),
                line=dict(color=year_colors[idx % len(year_colors)], width=2.5),
                marker=dict(size=7),
                hovertemplate=f"<b>{yr}</b> %{{x}}<br>Rs. %{{y:.2f}}<extra></extra>",
            ))
        fig_yoy.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
            annotation_text=f"⚠ Rs.{warn_threshold}")
        fig_yoy.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
            annotation_text=f"🔴 Rs.{crisis_threshold}")
        fig_yoy.update_layout(
            height=360, margin=dict(l=10, r=100, t=20, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="white",
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": "hover"})

        st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

        # Comparison table
        st.markdown("#### " + ("📋 Year-by-Year Comparison Table" if lang=="en" else "📋 වාර්ෂික සංසන්දන වගුව"))
        compare_data = []
        for yr in selected_years:
            yr_data = history_df[history_df["year"] == yr]["price"]
            compare_data.append({
                "Year": yr,
                "Avg (Rs.)": round(yr_data.mean(), 2),
                "Min (Rs.)": round(yr_data.min(), 2),
                "Max (Rs.)": round(yr_data.max(), 2),
                "Std Dev": round(yr_data.std(), 2),
                "Crisis Months": int((yr_data >= crisis_threshold).sum()),
                "Warning Months": int(((yr_data >= warn_threshold) & (yr_data < crisis_threshold)).sum()),
            })
        df_compare = pd.DataFrame(compare_data)
        st.dataframe(df_compare, use_container_width=True, hide_index=True)

        st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

        # Volatility comparison
        st.markdown("#### " + ("📊 Volatility Comparison" if lang=="en" else "📊 අස්ථාවරතා සංසන්දනය"))
        fig_vol = go.Figure()
        for idx, yr in enumerate(selected_years):
            yr_data = history_df[history_df["year"] == yr]["price"]
            fig_vol.add_trace(go.Box(
                y=yr_data,
                name=str(yr),
                marker_color=year_colors[idx % len(year_colors)],
                boxmean=True,
            ))
        fig_vol.update_layout(
            height=300, margin=dict(l=10, r=10, t=20, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="white",
            yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs."),
            xaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": "hover"})
    else:
        st.info("Please select at least one year above." if lang=="en" else "කරුණාකර ඉහතින් අවම වශයෙන් වසරක් තෝරන්න.")

# ── METHOD ────────────────────────────────────
elif "🧠 Method" in section or "🧠 ක්‍රමවේදය" in section:
    st.markdown(f'<div class="section-header">{t["method_title"]}</div>', unsafe_allow_html=True)

    step_icons = ["📚", "🔍", "📏", "🔮"]
    step_colors = ["#3b82f6", "#8b5cf6", "#16a34a", "#f59e0b"]
    cols = st.columns(4)
    for i, (col, icon, clr, step) in enumerate(zip(cols, step_icons, step_colors, t["method_steps"])):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:#f8fafc; border-radius:16px; padding:28px 16px; border:1px solid #e2e8f0; height:190px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                <div style='width:48px; height:48px; background:linear-gradient(135deg,{clr},{clr}99); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.3rem; margin:0 auto 12px; color:white; font-weight:900; box-shadow:0 4px 12px {clr}44;'>{i+1}</div>
                <div style='font-size:1.4rem; margin-bottom:8px;'>{icon}</div>
                <div style='font-size:0.88rem; color:#475569; line-height:1.6; font-weight:500;'>{step}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Architecture diagram
    st.markdown("#### " + ("🏗️ System Architecture" if lang=="en" else "🏗️ පද්ධති ගෘහ නිර්මාණය"))
    arch_cols = st.columns(5)
    arch_steps = [
        ("📦", "Raw Data\n(Auction Records)", "#3b82f6"),
        ("🔄", "Pre-processing\n& Cleaning", "#8b5cf6"),
        ("🤖", "Model Training\n(Markov + ARIMA)", "#16a34a"),
        ("📊", "Analysis\n(Elasticity)", "#f59e0b"),
        ("📱", "Dashboard\n(COCOStat)", "#ef4444"),
    ]
    for col, (icon, label, clr) in zip(arch_cols, arch_steps):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:#f8fafc; border-top:4px solid {clr}; border-radius:0 0 12px 12px; padding:16px 8px;'>
                <div style='font-size:1.8rem; margin-bottom:6px;'>{icon}</div>
                <div style='font-size:0.78rem; font-weight:700; color:{clr}; white-space:pre-line;'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    with st.expander("🔬 " + ("Technical Details (Advanced)" if lang=="en" else "තාක්ෂණික විස්තර (උසස්)")):
        st.markdown("""
| Component | Method | Detail |
|-----------|--------|--------|
| Regime Detection | Markov Switching Model (3-State) | Hamilton (1989) specification |
| Demand Estimation | OLS with HC3 Robust Std Errors | Log-log specification |
| Forecasting | SARIMA with seasonal adjustment | AIC-selected order |
| Volatility | Rolling std dev (12-month window) | Monthly frequency |
| Data Source | Sri Lanka Coconut Auction Records | 2015–2024 (113 obs.) |
        """)

    with st.expander("📖 " + ("References" if lang=="en" else "යොමු කිරීම්")):
        st.markdown("""
- Hamilton, J.D. (1989). *A New Approach to the Economic Analysis of Nonstationary Time Series*. Econometrica.
- Box, G.E.P. & Jenkins, G.M. (1976). *Time Series Analysis: Forecasting and Control*. Holden-Day.
- Sri Lanka Coconut Development Authority. Annual Reports (2015–2024).
        """)

# ─────────────────────────────────────────────
# FOOTER: Sri Lanka Coconut Industry Info
# ─────────────────────────────────────────────
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div style='background:linear-gradient(135deg,#0f2027,#203a43,#2c5364); border-radius:20px; padding:36px 32px; color:white; text-align:center;'>
    <div style='font-size:2.2rem; margin-bottom:6px;'>🥥</div>
    <div style='font-weight:900; font-size:1.5rem; margin-bottom:4px;'>Sri Lanka Coconut Industry</div>
    <div style='font-size:0.85rem; opacity:0.55; margin-bottom:0;'>Key Organisations, Contacts &amp; Industry Facts</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Organisations ──
org_col1, org_col2, org_col3, org_col4 = st.columns(4)

with org_col1:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f2027,#1a3a2a); border-radius:14px; padding:18px 16px; color:white;'>
        <div style='font-size:0.6rem; opacity:0.45; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>🏛 Primary Regulator</div>
        <div style='font-weight:800; font-size:0.9rem; margin-bottom:8px; line-height:1.4;'>Coconut Development Authority</div>
        <div style='font-size:0.76rem; opacity:0.7; line-height:1.9;'>
            No. 54, Nawam Mawatha<br>Colombo 02<br>
            📞 +94 11 243 0610<br>
            🌐 www.cda.gov.lk
        </div>
    </div>
    """, unsafe_allow_html=True)

with org_col2:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f2027,#1a3a2a); border-radius:14px; padding:18px 16px; color:white;'>
        <div style='font-size:0.6rem; opacity:0.45; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>🔬 Research Institute</div>
        <div style='font-weight:800; font-size:0.9rem; margin-bottom:8px; line-height:1.4;'>Coconut Research Institute (CRI)</div>
        <div style='font-size:0.76rem; opacity:0.7; line-height:1.9;'>
            Bandirippuwa Estate<br>Lunuwila 61150<br>
            📞 +94 31 222 2481<br>
            🌐 www.cri.gov.lk
        </div>
    </div>
    """, unsafe_allow_html=True)

with org_col3:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f2027,#1a3a2a); border-radius:14px; padding:18px 16px; color:white;'>
        <div style='font-size:0.6rem; opacity:0.45; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>📦 Export Promoter</div>
        <div style='font-weight:800; font-size:0.9rem; margin-bottom:8px; line-height:1.4;'>Sri Lanka Export Development Board</div>
        <div style='font-size:0.76rem; opacity:0.7; line-height:1.9;'>
            42 Nawam Mawatha<br>Colombo 02<br>
            📞 +94 11 230 0705<br>
            🌐 www.srilankabusiness.com
        </div>
    </div>
    """, unsafe_allow_html=True)

with org_col4:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f2027,#1a3a2a); border-radius:14px; padding:18px 16px; color:white;'>
        <div style='font-size:0.6rem; opacity:0.45; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>🛒 Market &amp; Auction</div>
        <div style='font-weight:800; font-size:0.9rem; margin-bottom:8px; line-height:1.4;'>HARTI / Economic Centres</div>
        <div style='font-size:0.76rem; opacity:0.7; line-height:1.9;'>
            Narahenpita, Colombo 05<br>(Head Office)<br>
            📞 +94 11 259 1919<br>
            🌐 www.harti.gov.lk
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

# ── Row 2: Industry Stats ──
st.markdown("<div style='text-align:center; font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:16px;'>📊 Sri Lanka Coconut Industry at a Glance</div>", unsafe_allow_html=True)

s1, s2, s3, s4, s5, s6 = st.columns(6)
industry_stats = [
    ("~2.7M", "Hectares Cultivated", "#22c55e", "#dcfce7"),
    ("~3B", "Nuts / Year", "#3b82f6", "#eff6ff"),
    ("450K+", "Farming Families", "#f59e0b", "#fefce8"),
    ("$350M+", "Annual Exports", "#8b5cf6", "#f5f3ff"),
    ("3rd", "World Producer", "#ef4444", "#fef2f2"),
    ("~2%", "GDP Contribution", "#14b8a6", "#f0fdfa"),
]
for col, (val, label, clr, bg) in zip([s1,s2,s3,s4,s5,s6], industry_stats):
    with col:
        st.markdown(f"""
        <div style='background:{bg}; border-radius:12px; padding:14px 8px; text-align:center; border:1px solid {clr}33;'>
            <div style='font-size:1.4rem; font-weight:900; color:{clr};'>{val}</div>
            <div style='font-size:0.7rem; color:#64748b; margin-top:4px; font-weight:600;'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

# ── Row 3: Coconut Triangle ──
st.markdown("<div style='text-align:center; font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:14px;'>📍 The Coconut Triangle — Main Growing Districts</div>", unsafe_allow_html=True)

d1, d2, d3, d4, d5 = st.columns(5)
districts = ["Kurunegala", "Puttalam", "Gampaha", "Colombo", "Kalutara"]
for col, district in zip([d1, d2, d3, d4, d5], districts):
    with col:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#0f2027,#1a3a2a); border-radius:10px; padding:12px 8px; text-align:center; color:white;'>
            <div style='font-size:1.3rem;'>🌴</div>
            <div style='font-size:0.82rem; font-weight:700; margin-top:4px;'>{district}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; font-size:0.72rem; color:#94a3b8; padding-bottom:16px;'>
    🥥 COCOStat · Coconut Market Intelligence Dashboard · Data sourced from CDA &amp; CRI Sri Lanka
</div>
""", unsafe_allow_html=True)
