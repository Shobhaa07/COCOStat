import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
# SESSION STATE
# ─────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

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
        "nav_label": "Navigation",
        "regime_select_label": "Market Regime",
        "sidebar_data_label": "Data Source",
        "sidebar_data_value": "Coconut Development Authority",
        "sidebar_updated": "Last Updated",
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
        "nav_label": "සංචාලනය",
        "regime_select_label": "වෙළඳ තත්ත්වය",
        "sidebar_data_label": "දත්ත මූලාශ්‍රය",
        "sidebar_data_value": "පොල් සංවර්ධන අධිකාරිය",
        "sidebar_updated": "යාවත්කාලීන කළේ",
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

    last = float(hist["price"].iloc[-1])
    future_dates = pd.date_range(hist["date"].iloc[-1] + pd.DateOffset(months=1), periods=12, freq="MS")
    future_prices = [last + i * 0.4 + np.random.normal(0, 1.5) for i in range(12)]
    upper = [p + 5 for p in future_prices]
    lower = [p - 5 for p in future_prices]
    forecast = pd.DataFrame({"date": future_dates, "price": np.round(future_prices, 2),
                              "upper": np.round(upper, 2), "lower": np.round(lower, 2)})
    return hist, forecast

history_df, forecast_df = generate_data()

# ─────────────────────────────────────────────
# MASTER CSS  – Sri Lankan / Coconut Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;500;600;700;800&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600;700&display=swap');

/* ── Variables ─────────────────────────────── */
:root {
    --palm-dark:   #1a3326;
    --palm-mid:    #2a5240;
    --palm-light:  #3d7a5c;
    --leaf-glow:   #4caf7d;
    --coconut-tan: #c9a96e;
    --coconut-drk: #8b6b3d;
    --cream:       #fdf8f0;
    --cream-mid:   #f5ede0;
    --text-dark:   #1a1a1a;
    --text-mid:    #4a5568;
    --text-light:  #94a3b8;
    --green-soft:  #f0fdf4;
    --warn-soft:   #fefce8;
    --crisis-soft: #fef2f2;
    --radius:      16px;
}

/* ── Global ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', 'Noto Sans Sinhala', sans-serif;
    color: var(--text-dark);
}

/* Subtle woven-leaf background on main body */
.stApp {
    background-color: var(--cream);
    background-image:
        radial-gradient(ellipse 80% 50% at 10% 0%, rgba(76,175,125,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 100%, rgba(201,169,110,0.08) 0%, transparent 55%);
}

/* Hide default chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Block container padding ───────────────── */
.block-container {
    padding: 0 2rem 2rem !important;
    max-width: 1400px;
}

/* ── Metric cards ────────────────────────────  */
[data-testid="metric-container"] {
    background: white;
    border-radius: var(--radius);
    border: 1.5px solid #e2e8f0;
    padding: 18px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 6px 24px rgba(26,51,38,0.10);
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-mid) !important;
    letter-spacing: 0.02em;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 800 !important;
    color: var(--palm-dark) !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Section headings ────────────────────────  */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.65rem;
    font-weight: 700;
    color: var(--palm-dark);
    margin-bottom: 4px;
    line-height: 1.25;
}
.section-sub {
    color: var(--text-mid);
    font-size: 0.9rem;
    margin-bottom: 20px;
}

/* ── Divider ─────────────────────────────────  */
.styled-divider {
    height: 2px;
    background: linear-gradient(90deg, var(--palm-light), var(--coconut-tan), var(--palm-light));
    border-radius: 2px;
    margin: 28px 0;
    opacity: 0.5;
}

/* ── Info boxes ──────────────────────────────  */
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
    background: var(--green-soft);
    border-left: 4px solid var(--leaf-glow);
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #166534;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}

/* ── SIDEBAR ─────────────────────────────────  */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, var(--palm-dark) 0%, #0f2018 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.18);
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] * {
    color: #e8f5ee !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label {
    color: #a7c9b8 !important;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
/* Radio button items in sidebar */
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
    color: #d4ead9 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
    background: rgba(76,175,125,0.15) !important;
    border-color: rgba(76,175,125,0.3) !important;
    color: white !important;
}
/* Selected radio in sidebar */
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-baseweb="radio"]:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] {
    background: rgba(76,175,125,0.2) !important;
    border-color: rgba(76,175,125,0.5) !important;
}
/* Selectbox in sidebar */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: white !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
    fill: #a7c9b8 !important;
}

/* Hide the default Streamlit sidebar collapse button */
[data-testid="collapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }

/* ── Hero section ────────────────────────────  */
.hero-wrapper {
    position: relative;
    background: linear-gradient(135deg, var(--palm-dark) 0%, var(--palm-mid) 60%, #2a6b48 100%);
    border-radius: 0 0 28px 28px;
    padding: 36px 32px 32px;
    margin: 0 -2rem 28px;
    overflow: hidden;
}
.hero-wrapper::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(76,175,125,0.18) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-wrapper::after {
    content: '🌴';
    position: absolute;
    bottom: -8px; right: 24px;
    font-size: 5rem;
    opacity: 0.12;
    pointer-events: none;
    line-height: 1;
}
.hero-badge {
    display: inline-block;
    background: rgba(76,175,125,0.25);
    border: 1px solid rgba(76,175,125,0.5);
    color: #a8eac8 !important;
    padding: 5px 14px;
    border-radius: 30px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.6rem, 3vw, 2.5rem);
    font-weight: 900;
    color: white !important;
    line-height: 1.2;
    margin: 0 0 10px;
    text-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.hero-desc {
    color: rgba(220,240,228,0.85) !important;
    font-size: clamp(0.82rem, 1.4vw, 0.95rem);
    max-width: 680px;
    line-height: 1.65;
    margin: 0;
}

/* ── Language toggle (top-right fixed) ───────  */
.lang-pill-wrapper {
    position: fixed;
    top: 14px;
    right: 20px;
    z-index: 9999;
}
.lang-pill-wrapper .stRadio {
    background: white;
    border-radius: 999px;
    padding: 4px 6px;
    box-shadow: 0 2px 14px rgba(0,0,0,0.14);
    border: 1px solid #e2e8f0;
}
.lang-pill-wrapper .stRadio > div {
    flex-direction: row !important;
    gap: 2px;
}
.lang-pill-wrapper .stRadio label {
    border-radius: 999px !important;
    padding: 5px 14px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-mid) !important;
    border: none !important;
    background: transparent !important;
    margin: 0 !important;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    white-space: nowrap;
}
.lang-pill-wrapper .stRadio label:hover {
    background: var(--green-soft) !important;
    color: var(--palm-mid) !important;
}
.lang-pill-wrapper [aria-checked="true"] {
    background: var(--palm-mid) !important;
    color: white !important;
}

/* ── Sidebar toggle FAB ────────────────────── */
#sidebar-toggle-btn {
    position: fixed;
    bottom: 28px;
    left: 20px;
    z-index: 9998;
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, var(--palm-mid), var(--leaf-glow));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(26,51,38,0.35);
    font-size: 1.25rem;
    transition: transform 0.2s, box-shadow 0.2s;
    border: 2px solid rgba(255,255,255,0.2);
    color: white;
    user-select: none;
}
#sidebar-toggle-btn:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 22px rgba(26,51,38,0.45);
}

/* ── Plotly chart container ─────────────────  */
.js-plotly-plot {
    border-radius: 14px;
    overflow: hidden;
}

/* ── Footer ──────────────────────────────────  */
.footer-box {
    background: linear-gradient(135deg, var(--palm-dark) 0%, #0d1f16 100%);
    border-radius: 20px;
    padding: 36px 32px;
    color: white;
    text-align: center;
    margin-top: 40px;
    position: relative;
    overflow: hidden;
}
.footer-box::before {
    content: '🥥';
    position: absolute;
    left: -10px; bottom: -10px;
    font-size: 6rem;
    opacity: 0.06;
}
.footer-box::after {
    content: '🌴';
    position: absolute;
    right: -10px; top: -10px;
    font-size: 6rem;
    opacity: 0.06;
}
.footer-grid {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 32px 48px;
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 24px;
    margin-top: 20px;
}
.footer-col-label {
    font-size: 0.65rem;
    opacity: 0.45;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}
.footer-col-value {
    font-weight: 700;
    font-size: 0.9rem;
    line-height: 1.6;
}
.footer-stat {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 12px 20px;
    min-width: 130px;
}

/* ── Responsive tweaks ───────────────────────  */
@media (max-width: 768px) {
    .block-container { padding: 0 0.75rem 1.5rem !important; }
    .hero-wrapper { padding: 28px 18px 24px; margin: 0 -0.75rem 20px; }
    .hero-title { font-size: 1.5rem; }
    .hero-desc { font-size: 0.82rem; }
    .lang-pill-wrapper { right: 10px; top: 10px; }
    .lang-pill-wrapper .stRadio label { padding: 4px 10px !important; font-size: 0.78rem !important; }
    .footer-grid { gap: 20px 24px; }
    .section-header { font-size: 1.3rem; }
}
@media (max-width: 480px) {
    [data-testid="metric-container"] { padding: 12px 14px; }
    [data-testid="stMetricValue"] { font-size: 1.15rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# JAVASCRIPT  – sidebar toggle + hide default button
# ─────────────────────────────────────────────
st.markdown("""
<script>
(function() {
    function hideSLToggle() {
        // Hide Streamlit's own collapse chevron
        var btns = document.querySelectorAll('[data-testid="collapsedControl"], button[kind="header"]');
        btns.forEach(function(b){ b.style.display='none'; });
    }
    function injectFAB() {
        if (document.getElementById('sidebar-toggle-btn')) return;
        var btn = document.createElement('div');
        btn.id = 'sidebar-toggle-btn';
        btn.title = 'Toggle sidebar';
        btn.innerHTML = '☰';
        btn.onclick = function() {
            var sb = document.querySelector('[data-testid="stSidebar"]');
            if (!sb) return;
            var collapsed = sb.getAttribute('aria-expanded') === 'false';
            var nativeBtn = document.querySelector('[data-testid="collapsedControl"] button, [data-testid="stSidebar"] ~ div button');
            if (!collapsed) {
                sb.style.marginLeft = '-300px';
                sb.style.transition = 'margin-left 0.3s ease';
                sb.setAttribute('aria-expanded', 'false');
                btn.innerHTML = '☰';
            } else {
                sb.style.marginLeft = '0';
                sb.style.transition = 'margin-left 0.3s ease';
                sb.setAttribute('aria-expanded', 'true');
                btn.innerHTML = '✕';
            }
        };
        document.body.appendChild(btn);
    }
    // Run after DOM is ready
    window.addEventListener('load', function() {
        setTimeout(function(){ hideSLToggle(); injectFAB(); }, 600);
        setTimeout(function(){ hideSLToggle(); injectFAB(); }, 1500);
    });
    // MutationObserver to keep it hidden on re-renders
    var obs = new MutationObserver(function(){ hideSLToggle(); injectFAB(); });
    obs.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LANGUAGE SWITCHER  – top-right fixed
# ─────────────────────────────────────────────
with st.container():
    st.markdown('<div class="lang-pill-wrapper">', unsafe_allow_html=True)
    lang_choice = st.radio(
        "lang",
        ["🇬🇧 EN", "🇱🇰 සි"],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="lang_topright",
    )
    st.markdown('</div>', unsafe_allow_html=True)

new_lang = "en" if "EN" in lang_choice else "si"
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    st.rerun()

lang = st.session_state.lang
t = T[lang]

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    # Brand header
    st.markdown(f"""
    <div style="padding: 28px 20px 18px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 8px;">
        <div style="font-size: 2.4rem; margin-bottom: 4px; text-align:center;">🥥</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.45rem; font-weight:900; color:white; text-align:center; line-height:1.2; letter-spacing:-0.01em;">COCOStat</div>
        <div style="font-size:0.72rem; color:#6aac85; text-align:center; letter-spacing:0.1em; text-transform:uppercase; margin-top:4px;">Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation label
    st.markdown(f"""<div style="font-size:0.72rem; font-weight:700; color:#6aac85; letter-spacing:0.12em; text-transform:uppercase; padding: 12px 4px 8px;">{t["nav_label"]} 🍃</div>""", unsafe_allow_html=True)
    section = st.radio("nav", t["nav"], label_visibility="collapsed", key="nav_radio")

    st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.08); margin:16px 0 12px;"></div>', unsafe_allow_html=True)

    # Regime selector
    st.markdown(f"""<div style="font-size:0.72rem; font-weight:700; color:#6aac85; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:8px;">{t["regime_select_label"]} 🌡️</div>""", unsafe_allow_html=True)
    active_regime = st.selectbox("regime", t["regime_options"], index=0, label_visibility="collapsed")
    regime_idx = t["regime_options"].index(active_regime)

    st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.08); margin:16px 0 14px;"></div>', unsafe_allow_html=True)

    # Institutional info block
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:14px 14px 12px;">
        <div style="font-size:0.65rem; color:#6aac85; letter-spacing:0.1em; text-transform:uppercase; font-weight:700; margin-bottom:10px;">
            ℹ️ {"About" if lang=="en" else "විස්තර"}
        </div>
        <div style="font-size:0.78rem; color:#b8d8c5; line-height:1.8;">
            <div>🏛 <b style="color:#d4ead9;">{t["sidebar_data_label"]}</b></div>
            <div style="padding-left:18px; opacity:0.8;">{t["sidebar_data_value"]}</div>
            <div style="margin-top:6px;">📅 <b style="color:#d4ead9;">{t["sidebar_updated"]}</b></div>
            <div style="padding-left:18px; opacity:0.8;">{datetime.now().strftime("%b %Y")}</div>
            <div style="margin-top:6px;">🗓️ <b style="color:#d4ead9;">{"Data Range" if lang=="en" else "දත්ත සීමාව"}</b></div>
            <div style="padding-left:18px; opacity:0.8;">2015 – 2024</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick fact
    st.markdown(f"""
    <div style="margin-top:12px; background:rgba(76,175,125,0.12); border:1px solid rgba(76,175,125,0.25); border-radius:12px; padding:12px 14px; font-size:0.78rem; color:#a8eac8; line-height:1.6;">
        🥥 {"Sri Lanka is the world's 4th largest coconut producer." if lang=="en" else "ශ්‍රී ලංකාව ලොව 4 වෙනි විශාලතම පොල් නිෂ්පාදකයාය."}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO  –  STICKY TOPIC DESCRIPTION
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero-wrapper">
    <div class="hero-badge">🥥 {t["subtitle"]}</div>
    <h1 class="hero-title">{t["tagline"]}</h1>
    <p class="hero-desc">{t["desc"]}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTIONS
# ─────────────────────────────────────────────

# ── OVERVIEW ─────────────────────────────────
if "📊 Overview" in section or "📊 දළ" in section:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(t["card_price_label"], t["card_price_value"], t["card_price_sub"])
    with col2: st.metric(t["card_market_label"], t["card_market_value"], t["card_market_sub"])
    with col3: st.metric(t["card_demand_label"], t["card_demand_value"], t["card_demand_sub"])
    with col4: st.metric(t["card_forecast_label"], t["card_forecast_value"], t["card_forecast_sub"])

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    recent = history_df.tail(36).copy()
    fig_hero = go.Figure()
    fig_hero.add_trace(go.Scatter(
        x=recent["date"], y=recent["price"],
        fill="tozeroy", fillcolor="rgba(61,122,92,0.10)",
        line=dict(color="#2a5240", width=2.5), name="Price",
    ))
    fig_hero.add_hline(y=65, line_dash="dash", line_color="#d97706",
        annotation_text="⚠ Warning", annotation_position="top right", annotation_font_color="#d97706")
    fig_hero.add_hline(y=80, line_dash="dash", line_color="#dc2626",
        annotation_text="🔴 Crisis", annotation_position="bottom right", annotation_font_color="#dc2626")
    fig_hero.update_layout(
        title=dict(text="📈 " + ("Recent 3-Year Price Trend" if lang=="en" else "මෑත කාල මිල ප්‍රවණතාව"),
                   font=dict(size=14, color="#1a3326", family="DM Sans")),
        height=280, margin=dict(l=10, r=80, t=44, b=10),
        plot_bgcolor="#fafdf9", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#64748b")),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11, color="#64748b")),
        showlegend=False,
    )
    st.plotly_chart(fig_hero, use_container_width=True)

# ── MARKET ───────────────────────────────────
elif "🚦 Market" in section or "🚦 වෙළඳ" in section:
    st.markdown(f'<div class="section-header">{t["regime_title"]}</div>', unsafe_allow_html=True)

    regime_colors = ["#16a34a", "#d97706", "#dc2626"]
    regime_bgs    = ["#f0fdf4", "#fffbeb", "#fef2f2"]
    regime_emoji  = ["🟢", "🟡", "🔴"]

    col1, col2, col3 = st.columns(3)
    for i, col in enumerate([col1, col2, col3]):
        border = f"2.5px solid {regime_colors[i]}" if i == regime_idx else "1.5px solid #e2e8f0"
        bg = regime_bgs[i] if i == regime_idx else "white"
        shadow = f"0 6px 20px {regime_colors[i]}22" if i == regime_idx else "0 2px 8px rgba(0,0,0,0.04)"
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:{border}; border-radius:16px; padding:22px 18px; text-align:center; box-shadow:{shadow}; transition:all 0.2s;'>
                <div style='font-size:2.2rem; margin-bottom:8px;'>{regime_emoji[i]}</div>
                <div style='font-weight:800; font-size:0.95rem; color:{regime_colors[i]}; margin-bottom:8px; letter-spacing:0.01em;'>{t["regime_options"][i]}</div>
                <div style='font-size:0.85rem; color:#475569; line-height:1.55;'>{t["regime_desc"][i]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    rc, rb = regime_colors[regime_idx], regime_bgs[regime_idx]
    c1, c2, c3 = st.columns(3)
    for col, lbl, val in zip([c1, c2, c3],
            [t["regime_avg_label"], t["regime_vol_label"], t["regime_status_label"]],
            [t["regime_avg"][regime_idx], t["regime_vol"][regime_idx], t["regime_status"][regime_idx]]):
        with col:
            st.markdown(f"""<div style='background:{rb}; border-radius:12px; padding:18px; text-align:center; border:1px solid {rc}22;'>
            <div style='font-size:0.7rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>{lbl}</div>
            <div style='font-size:1.7rem; font-weight:900; color:{rc};'>{val}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    fig_reg = go.Figure()
    for r_i, (r_col, r_name) in enumerate(zip(regime_colors, t["regime_options"])):
        mask = history_df["regime"] == r_i
        subset = history_df[mask]
        if not subset.empty:
            fig_reg.add_trace(go.Scatter(
                x=subset["date"], y=subset["price"],
                mode="markers", marker=dict(color=r_col, size=5, opacity=0.75),
                name=r_name,
            ))
    fig_reg.add_hline(y=65, line_dash="dash", line_color="#d97706")
    fig_reg.add_hline(y=80, line_dash="dash", line_color="#dc2626")
    fig_reg.update_layout(
        title=dict(text="📊 " + ("Price History by Market Regime" if lang=="en" else "වෙළඳ තත්ත්වය අනුව මිල ඉතිහාසය"),
                   font=dict(size=14, color="#1a3326")),
        height=300, margin=dict(l=10, r=10, t=44, b=10),
        plot_bgcolor="#fafdf9", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#64748b")),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11, color="#64748b")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# ── DEMAND ───────────────────────────────────
elif "📉 Demand" in section or "📉 ඉල්ලුම" in section:
    st.markdown(f'<div class="section-header">{t["demand_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-blue">{t["demand_note"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        fig_bar = go.Figure(go.Bar(
            x=t["demand_periods"], y=t["demand_sens"],
            marker=dict(color=["#16a34a", "#d97706", "#dc2626"], line=dict(width=0)),
            text=t["demand_sens"], textposition="outside", width=0.5,
        ))
        fig_bar.update_layout(
            title=dict(text=t["demand_bar_title"], font=dict(size=13)),
            height=280, margin=dict(l=10, r=10, t=50, b=10),
            plot_bgcolor="#fafdf9", paper_bgcolor="white",
            yaxis=dict(gridcolor="#f1f5f9", range=[0, 50]),
            xaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        colors_d = [("#f0fdf4", "#16a34a"), ("#fffbeb", "#d97706"), ("#fef2f2", "#dc2626")]
        for i, (period, desc) in enumerate(t["demand_cards"]):
            bg, border = colors_d[i]
            st.markdown(f"""
            <div style='background:{bg}; border-left:4px solid {border}; border-radius:0 12px 12px 0; padding:14px 16px; margin-bottom:12px;'>
                <div style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:{border};'>{period}</div>
                <div style='font-size:0.85rem; color:#475569; line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### " + ("📊 Elasticity Summary" if lang=="en" else "📊 ස්ථිතිස්ථික සාරාංශය"))
    c1, c2, c3 = st.columns(3)
    data_e = [("-0.35", "Stable" if lang=="en" else "ස්ථාවර", "#16a34a", "#f0fdf4"),
              ("-0.22", "Warning" if lang=="en" else "අවවාද", "#d97706", "#fffbeb"),
              ("-0.12", "Crisis" if lang=="en" else "අර්බුද", "#dc2626", "#fef2f2")]
    for col, (val, period, clr, bg) in zip([c1, c2, c3], data_e):
        with col:
            st.markdown(f"""<div style='background:{bg}; border-radius:12px; padding:18px; text-align:center; border:1px solid {clr}22;'>
            <div style='font-size:0.7rem; font-weight:700; color:#64748b; margin-bottom:6px;'>
            {"Elasticity" if lang=="en" else "ස්ථිතිස්ථිකය"} — {period}</div>
            <div style='font-size:2rem; font-weight:900; color:{clr};'>{val}</div>
            <div style='font-size:0.78rem; color:#64748b; margin-top:4px;'>{"Inelastic" if lang=="en" else "අජඩ"}</div>
            </div>""", unsafe_allow_html=True)

# ── FORECAST ─────────────────────────────────
elif "🔮 Forecast" in section or "🔮 අනා" in section:
    st.markdown(f'<div class="section-header">{t["forecast_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-green">{t["forecast_summary"]}</div>', unsafe_allow_html=True)

    hist_recent = history_df.tail(16).copy()
    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(217,119,6,0.12)",
        line=dict(color="rgba(0,0,0,0)"), name=t["forecast_range_label"], hoverinfo="skip",
    ))
    fig_fore.add_trace(go.Scatter(
        x=hist_recent["date"], y=hist_recent["price"],
        line=dict(color="#2563eb", width=2.5), name=t["forecast_hist_label"], mode="lines",
    ))
    fig_fore.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["price"],
        line=dict(color="#d97706", width=2.5, dash="dash"),
        name=t["forecast_pred_label"], mode="lines+markers",
        marker=dict(size=6, color="#d97706"),
    ))
    fig_fore.add_vline(
        x=forecast_df["date"].iloc[0].timestamp() * 1000,
        line_dash="dot", line_color="#94a3b8",
        annotation_text="Forecast →", annotation_position="top right",
    )
    fig_fore.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="#fafdf9", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#64748b")),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11, color="#64748b")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    )
    st.plotly_chart(fig_fore, use_container_width=True)

    st.markdown("#### " + ("📅 Weekly Forecast" if lang=="en" else "📅 සතිපතා අනාවැකිය"))
    cols = st.columns(6)
    for i, (_, row) in enumerate(forecast_df.iterrows()):
        if i >= 12: break
        price = row["price"]
        clr = "#dc2626" if price > 75 else "#d97706" if price > 65 else "#16a34a"
        bg  = "#fef2f2" if price > 75 else "#fffbeb" if price > 65 else "#f0fdf4"
        with cols[i % 6]:
            st.markdown(f"""
            <div style='background:{bg}; border:1px solid {clr}22; border-radius:10px; padding:10px 6px; text-align:center; margin-bottom:8px;'>
                <div style='font-size:0.68rem; color:#94a3b8; margin-bottom:3px; font-weight:600;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:0.92rem; font-weight:800; color:{clr};'>Rs.{price:.1f}</div>
            </div>""", unsafe_allow_html=True)

# ── POLICY ────────────────────────────────────
elif "🏛 Policy" in section or "🏛 ප්‍රති" in section:
    st.markdown(f'<div class="section-header">{t["policy_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["policy_sub"]}</div>', unsafe_allow_html=True)

    policy_colors = ["#16a34a", "#d97706", "#dc2626"]
    col1, col2, col3 = st.columns(3)
    for i, col in enumerate([col1, col2, col3]):
        is_active = (i == regime_idx)
        border = f"2.5px solid {policy_colors[i]}" if is_active else "1.5px solid #e2e8f0"
        shadow = f"0 6px 20px {policy_colors[i]}22" if is_active else "0 2px 8px rgba(0,0,0,0.04)"
        active_badge = f"""<div style='margin-top:10px; background:{policy_colors[i]}18; border-radius:8px; padding:6px 10px; font-size:0.78rem; color:{policy_colors[i]}; font-weight:700; display:inline-block;'>{t["policy_active"]}</div>""" if is_active else ""
        with col:
            st.markdown(f"""
            <div style='border-radius:16px; overflow:hidden; box-shadow:{shadow}; border:{border};'>
                <div style='background:{policy_colors[i]}; padding:14px 18px;'>
                    <span style='font-weight:800; font-size:0.95rem; color:white;'>{t["policy_markets"][i]}</span>
                </div>
                <div style='padding:16px 18px; background:white;'>
                    <p style='font-size:0.88rem; color:#475569; line-height:1.65; margin:0 0 12px;'>{t["policy_actions"][i]}</p>
                    <span style='font-size:0.75rem; font-weight:700; color:#94a3b8;'>{t["policy_priority_label"]}</span>
                    <span style='background:{policy_colors[i]}; color:white; font-size:0.75rem; font-weight:800; padding:3px 10px; border-radius:12px; margin-left:6px;'>{t["policy_priorities"][i]}</span>
                    {active_badge}
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### " + ("📋 Policy Decision Framework" if lang=="en" else "📋 ප්‍රතිපත්ති තීරණ රාමුව"))
    steps = [
        ("1️⃣", "Detect Regime" if lang=="en" else "තත්ත්වය හඳුනන්න", "#2563eb"),
        ("2️⃣", "Assess Priority" if lang=="en" else "ප්‍රමුඛතාව තීරණය", "#7c3aed"),
        ("3️⃣", "Implement Policy" if lang=="en" else "ප්‍රතිපත්තිය ක්‍රියාත්මක", "#16a34a"),
        ("4️⃣", "Monitor & Review" if lang=="en" else "නිරීක්ෂණය කරන්න", "#d97706"),
    ]
    cols = st.columns(4)
    for col, (emoji, step, clr) in zip(cols, steps):
        with col:
            st.markdown(f"""<div style='text-align:center; background:white; border-radius:14px; padding:20px 10px; border:1.5px solid #e2e8f0; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <div style='font-size:1.9rem; margin-bottom:8px;'>{emoji}</div>
            <div style='font-weight:700; font-size:0.85rem; color:{clr};'>{step}</div>
            </div>""", unsafe_allow_html=True)

# ── HISTORY ───────────────────────────────────
elif "📈 History" in section or "📈 ඉති" in section:
    st.markdown(f'<div class="section-header">{t["history_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["history_sub"]}</div>', unsafe_allow_html=True)

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=history_df["date"], y=history_df["price"],
        fill="tozeroy", fillcolor="rgba(42,82,64,0.09)",
        line=dict(color="#2a5240", width=1.8), name="Price", mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y}<extra></extra>",
    ))
    fig_hist.add_hline(y=65, line_dash="dash", line_color="#d97706",
        annotation_text=t["history_warn_label"], annotation_position="top right",
        annotation_font_color="#d97706")
    fig_hist.add_hline(y=80, line_dash="dash", line_color="#dc2626",
        annotation_text=t["history_crisis_label"], annotation_position="bottom right",
        annotation_font_color="#dc2626")
    fig_hist.update_layout(
        height=360, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="#fafdf9", paper_bgcolor="white",
        xaxis=dict(showgrid=False, rangeslider=dict(visible=True),
                   tickfont=dict(size=11, color="#64748b")),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11, color="#64748b")),
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("#### " + ("📊 Summary Statistics" if lang=="en" else "📊 සාරාංශ සංඛ්‍යාන"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 " + ("Max Price" if lang=="en" else "උපරිම මිල"), f"Rs. {history_df['price'].max():.2f}")
    c2.metric("📉 " + ("Min Price" if lang=="en" else "අවම මිල"), f"Rs. {history_df['price'].min():.2f}")
    c3.metric("📊 " + ("Avg Price" if lang=="en" else "සාමාන්‍ය මිල"), f"Rs. {history_df['price'].mean():.2f}")
    c4.metric("📐 " + ("Std Dev" if lang=="en" else "ප්‍රමිති අපගමනය"), f"Rs. {history_df['price'].std():.2f}")

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    regime_counts = history_df["regime"].value_counts().sort_index()
    fig_pie = go.Figure(go.Pie(
        labels=t["regime_options"], values=regime_counts.values, hole=0.5,
        marker=dict(colors=["#16a34a", "#d97706", "#dc2626"]),
        textinfo="label+percent", textfont=dict(size=12),
    ))
    fig_pie.update_layout(
        title=dict(text="🥧 " + ("Regime Distribution (2015–2024)" if lang=="en" else "තත්ත්ව බෙදා හැරීම (2015–2024)"),
                   font=dict(size=13)),
        height=320, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white", showlegend=True,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── METHOD ────────────────────────────────────
elif "🧠 Method" in section or "🧠 ක්‍රමවේදය" in section:
    st.markdown(f'<div class="section-header">{t["method_title"]}</div>', unsafe_allow_html=True)

    step_icons  = ["📚", "🔍", "📏", "🔮"]
    step_colors = ["#2563eb", "#7c3aed", "#16a34a", "#d97706"]
    cols = st.columns(4)
    for i, (col, icon, clr, step) in enumerate(zip(cols, step_icons, step_colors, t["method_steps"])):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:white; border-radius:16px; padding:28px 14px; border:1.5px solid #e2e8f0;
                        box-shadow:0 2px 10px rgba(0,0,0,0.04); min-height:170px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                <div style='width:48px; height:48px; background:linear-gradient(135deg,{clr},{clr}88); border-radius:50%;
                            display:flex; align-items:center; justify-content:center; font-size:1rem; color:white;
                            font-weight:900; margin:0 auto 12px; box-shadow:0 4px 14px {clr}44;'>{i+1}</div>
                <div style='font-size:1.4rem; margin-bottom:10px;'>{icon}</div>
                <div style='font-size:0.84rem; color:#475569; line-height:1.6; font-weight:500;'>{step}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    with st.expander("🔬 " + ("Technical Details (Advanced)" if lang=="en" else "තාක්ෂණික විස්තර (උසස්)")):
        st.markdown("""
| Component | Method |
|-----------|--------|
| Regime Detection | Markov Switching Model (3-State) |
| Demand Estimation | OLS with HC3 Robust Standard Errors |
| Forecasting | ARIMA / SARIMA with seasonal adjustment |
| Data Source | Sri Lanka Coconut Auction Records 2015–2024 |
        """)

# ─────────────────────────────────────────────
# FOOTER  –  Institutional / Coconut-themed
# ─────────────────────────────────────────────
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="footer-box">
    <div style='font-size:2.8rem; margin-bottom:8px;'>🥥</div>
    <div style='font-family:Playfair Display,serif; font-weight:900; font-size:1.5rem; margin-bottom:4px; letter-spacing:-0.01em;'>COCOStat</div>
    <div style='font-size:0.82rem; opacity:0.55; margin-bottom:6px; letter-spacing:0.08em; text-transform:uppercase;'>
        {"Coconut Market Intelligence · Sri Lanka" if lang=="en" else "පොල් වෙළඳපොළ බුද්ධිය · ශ්‍රී ලංකාව"}
    </div>

    <div class="footer-grid">
        <div class="footer-stat">
            <div class="footer-col-label">{"Institution" if lang=="en" else "ආයතනය"}</div>
            <div class="footer-col-value">{"Coconut Development" if lang=="en" else "පොල් සංවර්ධන"}<br>{"Authority, Sri Lanka" if lang=="en" else "අධිකාරිය, ශ්‍රී ලංකාව"}</div>
        </div>
        <div class="footer-stat">
            <div class="footer-col-label">{"Address" if lang=="en" else "ලිපිනය"}</div>
            <div class="footer-col-value">No. 11, Vauxhall Lane<br>Colombo 02, Sri Lanka</div>
        </div>
        <div class="footer-stat">
            <div class="footer-col-label">{"Production (2023)" if lang=="en" else "නිෂ්පාදනය (2023)"}</div>
            <div class="footer-col-value">{"~3 Billion Nuts/yr" if lang=="en" else "~කෝටි 300 ගෙඩි/වසර"}</div>
        </div>
        <div class="footer-stat">
            <div class="footer-col-label">{"Data Updated" if lang=="en" else "දත්ත යාවත්කාලීන"}</div>
            <div class="footer-col-value">{datetime.now().strftime("%B %Y")}</div>
        </div>
    </div>

    <div style='margin-top:22px; font-size:0.75rem; opacity:0.35; letter-spacing:0.04em;'>
        {"Academic research project · BSc (Hons) Data Science & Analytics · University of Westminster" if lang=="en" else "අධ්‍යාපනික පර්යේෂණ ව්‍යාපෘතිය · BSc (Hons) දත්ත විද්‍යාව · Westminster විශ්ව විද්‍යාලය"}
    </div>
</div>
""", unsafe_allow_html=True)
