import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random
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
        "footer_date": "Last Updated",
        "footer_location": "Key Coconut Markets in Sri Lanka",
        "footer_info": "Coconut Board of Sri Lanka",
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
        "demand_periods": ["ස්ථාවර", "අවවාද", "අර්බ���ද"],
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
        "history_sub": "සම්පූර්ණ වසර 10 වෙන්දේසි මිල ඉතිහාසය. හො���ර් කර ගවේෂණය කරන්න.",
        "history_warn_label": "අවවාද සීමාව (රු.65)",
        "history_crisis_label": "අර්බුද සීමාව (රු.80)",
        "method_title": "මෙම පද්ධතිය ක්‍රියා කරන ආකාරය",
        "method_steps": [
            "වසර 10ක වෙන්දේසි දත්ත අධ්‍යයනය කළා.",
            "වෙළඳපොළ තත්ත්ව 3ක් හඳුනාගත්තා.",
            "මිලට ප්‍රතිචාරය මැන බැලුවා.",
            "ඉදිරි මිල අනාවැකි කළා.",
        ],
        "footer_date": "අවසාන වරට යාවත්කාලීන කරන ලද",
        "footer_location": "ශ්‍රී ලංකාවේ ප්‍රධාන පොල් වෙළඳපොළ",
        "footer_info": "ශ්‍රී ලංකා පොල් මණ්ඩලිය",
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
    forecast = pd.DataFrame({"date": future_dates, "price": np.round(future_prices, 2), "upper": np.round(upper, 2), "lower": np.round(lower, 2)})
    return hist, forecast

history_df, forecast_df = generate_data()

# ─────────────────────────────────────────────
# CUSTOM CSS - ENHANCED WITH SRI LANKAN THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans Sinhala', 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #fdf8f3 0%, #f5f0eb 100%);
}

/* Hide default Streamlit header */
#MainMenu, footer {visibility: hidden;}

/* Top bar styling */
.top-bar-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border-radius: 0 0 20px 20px;
    box-shadow: 0 4px 16px rgba(139, 69, 19, 0.1);
    margin: -16px -16px 24px -16px;
}

.lang-selector {
    display: flex;
    gap: 8px;
    align-items: center;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #fff9f0, #ffe4d6);
    border-radius: 16px;
    border: 2px solid #D2691E;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(210, 105, 30, 0.08);
}

/* Section headers */
.section-header {
    font-size: 1.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #8B4513, #A0522D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
}
.section-sub {
    color: #725835;
    font-size: 0.95rem;
    margin-bottom: 20px;
    font-weight: 500;
}

/* Regime card */
.regime-card {
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}

.regime-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}

/* Info box */
.info-box-blue {
    background: linear-gradient(135deg, #eff6ff, #e0f2fe);
    border-left: 5px solid #3b82f6;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #1e40af;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}
.info-box-green {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border-left: 5px solid #22c55e;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    color: #166534;
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 20px;
}

/* Policy card */
.policy-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    margin-bottom: 16px;
    transition: transform 0.2s;
}

.policy-card:hover {
    transform: translateY(-2px);
}

.policy-header {
    padding: 14px 18px;
    font-weight: 800;
    font-size: 1rem;
    color: white;
}
.policy-body {
    padding: 16px 18px;
    background: #f8fafc;
}

/* Method steps */
.method-step {
    text-align: center;
    padding: 24px;
    background: linear-gradient(135deg, #fff9f0, #ffe4d6);
    border-radius: 16px;
    border: 2px solid #D2691E;
    transition: transform 0.2s;
}

.method-step:hover {
    transform: translateY(-4px);
}

/* Footer - Sri Lankan themed */
.footer-box {
    background: linear-gradient(135deg, #5C3D2E 0%, #7A4A38 50%, #8B5A3C 100%);
    border-radius: 20px;
    padding: 48px 40px;
    color: white;
    text-align: center;
    margin-top: 40px;
    border: 2px solid #D2691E;
    box-shadow: 0 8px 32px rgba(92, 61, 46, 0.2);
}

.footer-box h3 {
    color: #FFD700;
    margin-bottom: 16px;
    font-size: 1.3rem;
}

.footer-location-list {
    text-align: left;
    display: inline-block;
    margin: 20px 0;
    background: rgba(255,255,255,0.1);
    padding: 20px 30px;
    border-radius: 12px;
    border-left: 4px solid #FFD700;
}

.footer-location-list li {
    margin: 8px 0;
    line-height: 1.8;
}

/* Divider */
.styled-divider {
    height: 4px;
    background: linear-gradient(90deg, #8B4513, #D2691E, #A0522D);
    border-radius: 2px;
    margin: 32px 0;
    box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
}

/* Sidebar - Enhanced Sri Lankan theme */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #5C3D2E 0%, #6B4538 50%, #7A4A38 100%);
    border-right: 3px solid #D2691E;
}

div[data-testid="stSidebar"] * {
    color: white !important;
}

.sidebar-title {
    font-size: 1.4rem;
    font-weight: 900;
    margin-bottom: 12px;
    background: linear-gradient(135deg, #FFD700, #FFC700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Button styling */
button {
    background: linear-gradient(135deg, #D2691E, #8B4513) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 700 !important;
    transition: all 0.3s !important;
}

button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(139, 69, 19, 0.3) !important;
}

/* Chart styling */
.plotly-graph-div {
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(139, 69, 19, 0.08);
}

/* Responsive */
@media (max-width: 768px) {
    .section-header { font-size: 1.4rem; }
    .footer-box { padding: 24px 20px; }
    .top-bar-container { flex-direction: column; gap: 12px; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE FOR SIDEBAR TOGGLE
# ─────────────────────────────────────────────
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

# ─────────────────────────────────────────────
# TOP BAR WITH LANGUAGE SELECTOR
# ─────────────────────────────────────────────
col_left, col_right = st.columns([4, 1])

with col_left:
    st.markdown("""
    <div style='text-align:left; padding: 12px 0;'>
        <span style='font-size:2rem; font-weight:900; color:#FFD700;'>🥥 COCOStat</span>
        <span style='color:white; font-size:0.95rem; margin-left:12px; opacity:0.9;'>Coconut Market Intelligence</span>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div style='text-align:right; padding-top:12px;'>
    </div>
    """, unsafe_allow_html=True)
    lang_choice = st.selectbox("🌐", ["English", "සිංහල"], index=0, label_visibility="collapsed")

lang = "en" if lang_choice == "English" else "si"
t = T[lang]

st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="sidebar-title">{t["title"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f"### {t['nav'][0]}")
    section = st.radio(
        "Navigate Sections",
        t["nav"],
        label_visibility="collapsed",
        key="nav_radio"
    )

    st.markdown("---")
    
    st.markdown("### 📊 Market Analysis")
    active_regime = st.selectbox(
        t["regime_select"],
        t["regime_options"],
        index=0,
        key="regime_select"
    )
    regime_idx = t["regime_options"].index(active_regime)

    st.markdown("---")
    
    st.markdown("""
    <div style='background:rgba(255,255,255,0.1); border-radius:12px; padding:16px; margin-top:20px;'>
        <div style='font-size:0.85rem; opacity:0.9; line-height:2;'>
            <strong>📋 Dashboard Info:</strong><br>
            Last Updated: 2024-08-01<br>
            Data Period: 2015-2024<br>
            Markets Tracked: 5<br>
            <strong style='color:#FFD700;'>Status: Active ✓</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style='font-size:0.75rem; opacity:0.7; line-height:2; text-align:center;'>
        <strong style='color:#FFD700;'>🥥 Coconut Board Sri Lanka</strong><br>
        www.coconutboard.lk
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────

# ── HERO SECTION ─────────────────────────────
st.markdown(f"""
<div style='text-align:center; padding: 32px 0 20px;'>
    <span style='background:linear-gradient(135deg, #FFD700, #FFC700); border-radius:20px; padding:8px 20px; font-size:0.9rem; font-weight:700; color:#5C3D2E;'>
        🌟 {t["subtitle"]}
    </span>
    <h1 style='font-size:2.6rem; font-weight:900; background:linear-gradient(135deg, #8B4513, #A0522D); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:16px 0 10px; line-height:1.2;'>{t["tagline"]}</h1>
    <p style='color:#725835; font-size:1.05rem; max-width:800px; margin:0 auto; line-height:1.6;'>{t["desc"]}</p>
</div>
""", unsafe_allow_html=True)

# ── OVERVIEW CARDS ────────────────────────────
if "📊 Overview" in section or "📊 දළ" in section:
    col1, col2, col3, col4 = st.columns(4, gap="large")
    with col1:
        st.metric(t["card_price_label"], t["card_price_value"], t["card_price_sub"])
    with col2:
        st.metric(t["card_market_label"], t["card_market_value"], t["card_market_sub"])
    with col3:
        st.metric(t["card_demand_label"], t["card_demand_value"], t["card_demand_sub"])
    with col4:
        st.metric(t["card_forecast_label"], t["card_forecast_value"], t["card_forecast_sub"])

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Quick summary chart
    recent = history_df.tail(36).copy()
    fig_hero = go.Figure()
    fig_hero.add_trace(go.Scatter(
        x=recent["date"], y=recent["price"],
        fill="tozeroy", fillcolor="rgba(210, 105, 30, 0.15)",
        line=dict(color="#8B4513", width=3),
        name="Price",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>"
    ))
    fig_hero.add_hline(y=65, line_dash="dash", line_color="#D2691E", line_width=2, annotation_text="⚠ Warning Threshold", annotation_position="right")
    fig_hero.add_hline(y=80, line_dash="dash", line_color="#A0522D", line_width=2, annotation_text="🔴 Crisis Threshold", annotation_position="right")
    fig_hero.update_layout(
        title=dict(text="📈 " + ("Recent 3-Year Price Trend" if lang=="en" else "මෑත කාල මිල ප්‍රවණතාව"), font=dict(size=16, color="#5C3D2E", family="Arial Black")),
        height=320, margin=dict(l=20, r=120, t=50, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="#fdf8f3",
        xaxis=dict(showgrid=False, tickfont=dict(size=11), zeroline=False),
        yaxis=dict(gridcolor="#e8dcc8", tickprefix="Rs.", tickfont=dict(size=11)),
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig_hero, use_container_width=True, config={'displayModeBar': True})

# ── MARKET REGIME ────────────────────────────
elif "🚦 Market" in section or "🚦 වෙළඳ" in section:
    st.markdown(f'<div class="section-header">{t["regime_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Explore market conditions and volatility patterns</div>', unsafe_allow_html=True)

    regime_colors = ["#22c55e", "#D2691E", "#ef4444"]
    regime_bgs = ["#dcfce7", "#FFE4C4", "#fee2e2"]
    regime_emoji = ["🟢", "🟡", "🔴"]

    col1, col2, col3 = st.columns(3, gap="medium")
    for i, col in enumerate([col1, col2, col3]):
        border = "3px solid " + regime_colors[i] if i == regime_idx else "2px solid #D2691E"
        bg = regime_bgs[i] if i == regime_idx else "#f8fafc"
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:{border}; border-radius:16px; padding:28px; text-align:center; transition:all 0.3s;'>
                <div style='font-size:3rem; margin-bottom:12px;'>{regime_emoji[i]}</div>
                <div style='font-weight:800; font-size:1.1rem; color:{regime_colors[i]}; margin-bottom:10px;'>{t["regime_options"][i]}</div>
                <div style='font-size:0.95rem; color:#475569; line-height:1.8;'>{t["regime_desc"][i]}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Active regime detail
    rc = regime_colors[regime_idx]
    rb = regime_bgs[regime_idx]
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""<div style='background:{rb}; border-radius:14px; padding:24px; text-align:center; border:2px solid {rc};'>
        <div style='font-size:0.8rem; font-weight:900; color:#64748b; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px;'>{t["regime_avg_label"]}</div>
        <div style='font-size:2rem; font-weight:900; color:{rc};'>{t["regime_avg"][regime_idx]}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style='background:{rb}; border-radius:14px; padding:24px; text-align:center; border:2px solid {rc};'>
        <div style='font-size:0.8rem; font-weight:900; color:#64748b; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px;'>{t["regime_vol_label"]}</div>
        <div style='font-size:2rem; font-weight:900; color:{rc};'>{t["regime_vol"][regime_idx]}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style='background:{rb}; border-radius:14px; padding:24px; text-align:center; border:2px solid {rc};'>
        <div style='font-size:0.8rem; font-weight:900; color:#64748b; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px;'>{t["regime_status_label"]}</div>
        <div style='font-size:2rem; font-weight:900; color:{rc};'>{t["regime_status"][regime_idx]}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Price chart with regime colouring
    fig_reg = go.Figure()
    for r_i, (r_col, r_name) in enumerate(zip(regime_colors, t["regime_options"])):
        mask = history_df["regime"] == r_i
        subset = history_df[mask]
        if not subset.empty:
            fig_reg.add_trace(go.Scatter(
                x=subset["date"], y=subset["price"],
                mode="markers", 
                marker=dict(color=r_col, size=7, opacity=0.8, line=dict(width=1, color="white")),
                name=r_name,
                hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>"
            ))
    fig_reg.add_hline(y=65, line_dash="dash", line_color="#D2691E", line_width=2)
    fig_reg.add_hline(y=80, line_dash="dash", line_color="#A0522D", line_width=2)
    fig_reg.update_layout(
        title=dict(text="📊 " + ("Price History by Market Regime" if lang=="en" else "වෙළඳ තත්ත්වය අනුව මිල ඉතිහාසය"), font=dict(size=16)),
        height=350, margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="#fdf8f3",
        xaxis=dict(showgrid=False, zeroline=False), 
        yaxis=dict(gridcolor="#e8dcc8", tickprefix="Rs."),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)", bordercolor="#D2691E", borderwidth=1),
        hovermode="closest",
    )
    st.plotly_chart(fig_reg, use_container_width=True, config={'displayModeBar': True})

# ── DEMAND ───────────────────────────────────
elif "📉 Demand" in section or "📉 ඉල්ලුම" in section:
    st.markdown(f'<div class="section-header">{t["demand_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-blue">{t["demand_note"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")
    with col1:
        fig_bar = go.Figure(go.Bar(
            x=t["demand_periods"],
            y=t["demand_sens"],
            marker=dict(
                color=["#22c55e", "#D2691E", "#ef4444"],
                line=dict(color="white", width=2),
            ),
            text=t["demand_sens"],
            textposition="outside",
            texttemplate="%{text}%",
            width=0.6,
            hovertemplate="<b>%{x}</b><br>Sensitivity: %{y}%<extra></extra>"
        ))
        fig_bar.update_layout(
            title=dict(text=t["demand_bar_title"], font=dict(size=15, color="#5C3D2E")),
            height=320, margin=dict(l=20, r=20, t=60, b=20),
            plot_bgcolor="#f8fafc", paper_bgcolor="#fdf8f3",
            yaxis=dict(gridcolor="#e8dcc8", range=[0, 50], title="Sensitivity %"),
            xaxis=dict(showgrid=False, title="Market Period"),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    with col2:
        colors_d = [("#dcfce7", "#22c55e"), ("#FFE4C4", "#D2691E"), ("#fee2e2", "#ef4444")]
        for i, (period, desc) in enumerate(t["demand_cards"]):
            bg, border = colors_d[i]
            st.markdown(f"""
            <div style='background:{bg}; border-left:5px solid {border}; border-radius:0 12px 12px 0; padding:16px 16px; margin-bottom:14px; transition:all 0.2s;'>
                <div style='font-weight:800; font-size:1rem; margin-bottom:6px;'>{period}</div>
                <div style='font-size:0.9rem; color:#475569; line-height:1.6;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Elasticity insight
    st.markdown("#### 📊 " + ("Elasticity Summary" if lang=="en" else "ස්ථිතිස්ථිකතා සාරාංශය"))
    c1, c2, c3 = st.columns(3, gap="medium")
    data_e = [
        ("-0.35", "Stable", "#22c55e", "#dcfce7"),
        ("-0.22", "Warning", "#D2691E", "#FFE4C4"),
        ("-0.12", "Crisis", "#ef4444", "#fee2e2"),
    ]
    for col, (val, period, clr, bg) in zip([c1, c2, c3], data_e):
        with col:
            st.markdown(f"""<div style='background:{bg}; border-radius:14px; padding:24px; text-align:center; border:2px solid {clr};'>
            <div style='font-size:0.8rem; font-weight:900; color:#64748b; margin-bottom:8px;'>
            {"Elasticity" if lang=="en" else "ස්ථිතිස්ථිකය"} — {period}</div>
            <div style='font-size:2.2rem; font-weight:900; color:{clr};'>{val}</div>
            <div style='font-size:0.85rem; color:#64748b; margin-top:6px;'>{"Highly Inelastic" if lang=="en" else "අතිශයින් අජඩ"}</div>
            </div>""", unsafe_allow_html=True)

# ── FORECAST ─────────────────────────────────
elif "🔮 Forecast" in section or "🔮 අනා" in section:
    st.markdown(f'<div class="section-header">{t["forecast_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-green">{t["forecast_summary"]}</div>', unsafe_allow_html=True)

    hist_recent = history_df.tail(16).copy()

    fig_fore = go.Figure()
    # Uncertainty band
    fig_fore.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(210, 105, 30, 0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name=t["forecast_range_label"],
        hoverinfo="skip",
    ))
    # Historical
    fig_fore.add_trace(go.Scatter(
        x=hist_recent["date"], y=hist_recent["price"],
        line=dict(color="#5C3D2E", width=3),
        name=t["forecast_hist_label"],
        mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>"
    ))
    # Forecast
    fig_fore.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["price"],
        line=dict(color="#D2691E", width=3, dash="dash"),
        name=t["forecast_pred_label"],
        mode="lines+markers",
        marker=dict(size=8, color="#D2691E", symbol="diamond"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>"
    ))
    fig_fore.add_vline(
        x=forecast_df["date"].iloc[0].timestamp() * 1000,
        line_dash="dot", line_color="#94a3b8", line_width=2,
        annotation_text="📍 Forecast Start", annotation_position="top right",
    )
    fig_fore.update_layout(
        height=380, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="#fdf8f3",
        xaxis=dict(showgrid=False, tickfont=dict(size=11), zeroline=False),
        yaxis=dict(gridcolor="#e8dcc8", tickprefix="Rs.", tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)", bordercolor="#D2691E", borderwidth=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_fore, use_container_width=True, config={'displayModeBar': True})

    # 12-week mini table
    st.markdown("#### 📅 " + ("Weekly Forecast Breakdown" if lang=="en" else "සතිපතා අනාවැකි විශ්ලේෂණය"))
    
    # Create responsive grid
    cols_per_row = 6
    rows = (len(forecast_df) + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row, gap="small")
        for col_idx in range(cols_per_row):
            idx = row * cols_per_row + col_idx
            if idx < len(forecast_df):
                row_data = forecast_df.iloc[idx]
                price = row_data["price"]
                clr = "#ef4444" if price > 75 else "#D2691E" if price > 65 else "#22c55e"
                with cols[col_idx]:
                    st.markdown(f"""
                    <div style='background:#f8fafc; border:2px solid {clr}; border-radius:12px; padding:14px 8px; text-align:center; margin-bottom:8px;'>
                        <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:4px; font-weight:700;'>{t["forecast_week"]} {idx+1}</div>
                        <div style='font-size:1.1rem; font-weight:900; color:{clr};'>₨{price:.1f}</div>
                        <div style='font-size:0.7rem; color:#94a3b8; margin-top:2px;'>{row_data["date"].strftime("%b")}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ── POLICY ────────────────────────────────────
elif "🏛 Policy" in section or "🏛 ප්‍රති" in section:
    st.markdown(f'<div class="section-header">{t["policy_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["policy_sub"]}</div>', unsafe_allow_html=True)

    policy_colors = ["#22c55e", "#D2691E", "#ef4444"]
    col1, col2, col3 = st.columns(3, gap="large")
    for i, col in enumerate([col1, col2, col3]):
        is_active = (i == regime_idx)
        border = f"3px solid {policy_colors[i]}" if is_active else "2px solid #D2691E"
        with col:
            active_badge = f"""<div style='margin-top:12px; background:{policy_colors[i]}22; border-radius:10px; padding:8px 12px; font-size:0.85rem; color:{policy_colors[i]}; font-weight:900; border:2px solid {policy_colors[i]};'>✓ {t["policy_active"]}</div>""" if is_active else ""
            st.markdown(f"""
            <div style='border-radius:16px; overflow:hidden; box-shadow:0 6px 16px rgba(0,0,0,0.1); border:{border};'>
                <div style='background:{policy_colors[i]}; padding:16px 18px;'>
                    <span style='font-weight:900; font-size:1.1rem; color:white;'>{t["policy_markets"][i]}</span>
                </div>
                <div style='padding:18px 18px; background:#f8fafc;'>
                    <p style='font-size:0.95rem; color:#475569; line-height:1.8; margin:0 0 14px;'>{t["policy_actions"][i]}</p>
                    <span style='font-size:0.85rem; font-weight:800; color:#94a3b8;'>{t["policy_priority_label"]}</span>
                    <span style='background:{policy_colors[i]}; color:white; font-size:0.8rem; font-weight:900; padding:4px 12px; border-radius:12px; margin-left:8px;'>{t["policy_priorities"][i]}</span>
                    {active_badge}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Policy timeline / decision flow
    st.markdown("#### 📋 " + ("Policy Decision Framework" if lang=="en" else "ප්‍රතිපත්ති තීරණ රාමුව"))
    steps = [
        ("1️⃣", "Detect Regime" if lang=="en" else "තත්ත්වය හඳුනන්න", "#8B4513", "Identify current market state"),
        ("2️⃣", "Assess Priority" if lang=="en" else "ප්‍රමුඛතාව තීරණය", "#D2691E", "Determine urgency level"),
        ("3️⃣", "Implement Policy" if lang=="en" else "ප්‍රතිපත්තිය ක්‍රියාත්මක", "#A0522D", "Execute response plan"),
        ("4️⃣", "Monitor & Review" if lang=="en" else "නිරීක්ෂණය කරන්න", "#5C3D2E", "Track effectiveness"),
    ]
    cols = st.columns(4, gap="medium")
    for col, (emoji, step, clr, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""<div style='text-align:center; background:#f8fafc; border-radius:14px; padding:24px 14px; border:2px solid {clr}; transition:all 0.3s;'>
            <div style='font-size:2.2rem; margin-bottom:10px;'>{emoji}</div>
            <div style='font-weight:900; font-size:0.95rem; color:{clr}; margin-bottom:6px;'>{step}</div>
            <div style='font-size:0.8rem; color:#64748b; line-height:1.6;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

# ── HISTORY ───────────────────────────────────
elif "📈 History" in section or "📈 ඉති" in section:
    st.markdown(f'<div class="section-header">{t["history_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["history_sub"]}</div>', unsafe_allow_html=True)

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=history_df["date"], y=history_df["price"],
        fill="tozeroy", fillcolor="rgba(210, 105, 30, 0.12)",
        line=dict(color="#8B4513", width=2.5),
        name="Auction Price", mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y:.2f}<extra></extra>",
    ))
    fig_hist.add_hline(y=65, line_dash="dash", line_color="#D2691E", line_width=2.5,
        annotation_text=t["history_warn_label"], annotation_position="top right",
        annotation_font_color="#D2691E")
    fig_hist.add_hline(y=80, line_dash="dash", line_color="#A0522D", line_width=2.5,
        annotation_text=t["history_crisis_label"], annotation_position="bottom right",
        annotation_font_color="#A0522D")
    fig_hist.update_layout(
        height=400, margin=dict(l=20, r=120, t=50, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="#fdf8f3",
        xaxis=dict(showgrid=False, zeroline=False, rangeslider=dict(visible=True, thickness=0.05), tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#e8dcc8", tickprefix="Rs. ", tickfont=dict(size=11)),
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': True})

    # Stats
    st.markdown("#### 📊 " + ("Summary Statistics (2015-2024)" if lang=="en" else "සාරාංශ සංඛ්‍යාන (2015-2024)"))
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("📈 " + ("Max Price" if lang=="en" else "උපරිම"), f"₨ {history_df['price'].max():.2f}", f"({history_df['date'].iloc[history_df['price'].idxmax()].strftime('%b %Y')})")
    c2.metric("📉 " + ("Min Price" if lang=="en" else "අවම"), f"₨ {history_df['price'].min():.2f}", f"({history_df['date'].iloc[history_df['price'].idxmin()].strftime('%b %Y')})")
    c3.metric("📊 " + ("Average" if lang=="en" else "සාමාන්‍ය"), f"₨ {history_df['price'].mean():.2f}")
    c4.metric("📐 " + ("Volatility" if lang=="en" else "අස්ථාවරතා"), f"₨ {history_df['price'].std():.2f}")

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Regime distribution
    regime_counts = history_df["regime"].value_counts().sort_index()
    fig_pie = go.Figure(go.Pie(
        labels=t["regime_options"],
        values=regime_counts.values,
        hole=0.5,
        marker=dict(colors=["#22c55e", "#D2691E", "#ef4444"], line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13, color="white", family="Arial Black"),
        hovertemplate="<b>%{label}</b><br>Months: %{value}<br>Percentage: %{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        title=dict(text="🥧 " + ("Regime Distribution (2015–2024)" if lang=="en" else "තත්ත්ව බෙදා හැරීම (2015–2024)"), font=dict(size=15, color="#5C3D2E")),
        height=360, margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#fdf8f3",
        showlegend=True,
        legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#D2691E", borderwidth=1),
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

# ── METHOD ────────────────────────────────────
elif "🧠 Method" in section or "🧠 ක්‍රමවේදය" in section:
    st.markdown(f'<div class="section-header">{t["method_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Understand the science behind our analysis</div>', unsafe_allow_html=True)

    step_icons = ["📚", "🔍", "📏", "🔮"]
    step_colors = ["#8B4513", "#D2691E", "#A0522D", "#5C3D2E"]
    cols = st.columns(4, gap="medium")
    for i, (col, icon, clr, step) in enumerate(zip(cols, step_icons, step_colors, t["method_steps"])):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:#f8fafc; border-radius:16px; padding:32px 16px; border:2px solid {clr}; height:220px; display:flex; flex-direction:column; align-items:center; justify-content:center; transition:all 0.3s;'>
                <div style='width:56px; height:56px; background:linear-gradient(135deg,{clr},{clr}99); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.6rem; margin:0 auto 14px; box-shadow:0 6px 16px {clr}44;'>{i+1}</div>
                <div style='font-size:1.8rem; margin-bottom:12px;'>{icon}</div>
                <div style='font-size:0.9rem; color:#475569; line-height:1.7; font-weight:600;'>{step}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Technical details (collapsed)
    with st.expander("🔬 " + ("Technical Details (Advanced)" if lang=="en" else "තාක්ෂණික විස්තර (උසස්)"), expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            #### 🔧 Methodology
            
            **Regime Detection:** Markov Switching Model (3-State)
            
            **Demand Analysis:** OLS with HC3 Robust Standard Errors
            
            **Price Forecasting:** ARIMA/SARIMA with Seasonal Adjustment
            """)
        with col2:
            st.markdown("""
            #### 📊 Data Source
            
            **Historical Period:** 2015–2024
            
            **Data Type:** Weekly Auction Prices
            
            **Provider:** Sri Lanka Coconut Auction System
            
            **Markets Covered:** All major coconut auction centers
            """)

# ─────────────────────────────────────────────
# ENHANCED FOOTER
# ─────────────────────────────────────────────
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

coconut_locations = [
    ("🥥 Colombo Central Market", "Colombo 12"),
    ("🌴 Matara Auction Center", "Matara"),
    ("🏝️ Galle
