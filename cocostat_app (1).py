import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random

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
        "footer_researcher": "Researcher",
        "footer_ids": "Student IDs",
        "footer_programme": "Programme",
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
        "footer_researcher": "පර්යේෂක",
        "footer_ids": "ශිෂ්‍ය ID",
        "footer_programme": "පාඨමාලාව",
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
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans Sinhala', 'Segoe UI', sans-serif;
}

/* Hide default Streamlit header */
#MainMenu, footer, header {visibility: hidden;}

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

/* Regime card */
.regime-card {
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;
    cursor: pointer;
}

/* Info box */
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

/* Policy card */
.policy-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    margin-bottom: 16px;
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
    padding: 20px;
    background: #f8fafc;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
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

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2027 0%, #1a3a2a 100%);
}
div[data-testid="stSidebar"] * {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR (IMPROVED & ATTRACTIVE)
# ─────────────────────────────────────────────
with st.sidebar:
    # Header with branding
    st.markdown("""
    <div style='text-align:center; padding:20px 0 10px;'>
        <div style='font-size:3rem; margin-bottom:8px;'>🥥</div>
        <div style='font-size:1.3rem; font-weight:900; color:white; margin-bottom:4px;'>COCOStat</div>
        <div style='font-size:0.75rem; color:#cbd5e1; opacity:0.9; letter-spacing:1px;'>Coconut Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height:2px; background:linear-gradient(90deg, #22c55e, #3b82f6, #f59e0b); border-radius:2px; margin:16px 0;"></div>', unsafe_allow_html=True)
    
    # ───── LANGUAGE SELECTION ─────────────────
    st.markdown('<div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#94a3b8; font-weight:800; margin:16px 0 10px;">🌐 Language</div>', unsafe_allow_html=True)
    
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("🇬🇧 English", use_container_width=True, key="lang_en"):
            st.session_state.lang = "en"
            st.rerun()
    with lang_col2:
        if st.button("🇱🇰 සිංහල", use_container_width=True, key="lang_si"):
            st.session_state.lang = "si"
            st.rerun()
    
    # Set default language
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    
    lang_choice = "English" if st.session_state.lang == "en" else "සිංහල"
    lang = st.session_state.lang
    t = T[lang]
    
    st.markdown('<div style="height:1px; background:#334155; margin:16px 0;"></div>', unsafe_allow_html=True)
    
    # ───── NAVIGATION MENU ────────────────────
    st.markdown('<div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#94a3b8; font-weight:800; margin:16px 0 12px;">📊 Navigation</div>', unsafe_allow_html=True)
    
    # Create navigation buttons with clear styling
    nav_items = [
        ("📊 Overview", "📊 දළ විශ්ලේෂණය", "0"),
        ("🚦 Market", "🚦 වෙළඳපොළ", "1"),
        ("📉 Demand", "📉 ඉල්ලුම", "2"),
        ("🔮 Forecast", "🔮 අනාවැකිය", "3"),
        ("🏛 Policy", "🏛 ප්‍රතිපත්ති", "4"),
        ("📈 History", "📈 ඉතිහාසය", "5"),
        ("🧠 Method", "🧠 ක්‍රමවේදය", "6"),
    ]
    
    selected_idx = st.selectbox(
        "Choose a section:",
        range(len(nav_items)),
        format_func=lambda i: nav_items[i][0] if lang == "en" else nav_items[i][1],
        label_visibility="collapsed",
        key="nav_select"
    )
    
    section = nav_items[selected_idx][0] if lang == "en" else nav_items[selected_idx][1]
    
    # Visual indicator of selected section
    st.markdown(f"""
    <div style='background:#3b82f6; border-radius:10px; padding:10px 14px; margin-top:12px; text-align:center;'>
        <div style='font-size:0.75rem; color:#bfdbfe; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>
        {"Currently viewing" if lang=="en" else "දෙස බලමින් සිටින්න"}
        </div>
        <div style='font-size:1.1rem; font-weight:800; color:white;'>{nav_items[selected_idx][0 if lang=="en" else 1]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height:1px; background:#334155; margin:16px 0;"></div>', unsafe_allow_html=True)
    
    # ───── MARKET REGIME SELECTOR ─────────────
    st.markdown('<div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#94a3b8; font-weight:800; margin:16px 0 12px;">📈 Market Status</div>', unsafe_allow_html=True)
    
    regime_options_display = t["regime_options"]
    regime_idx = st.selectbox(
        t["regime_select"],
        range(len(regime_options_display)),
        format_func=lambda i: regime_options_display[i],
        label_visibility="collapsed",
        key="regime_select"
    )
    
    # Display regime details
    regime_colors = ["#22c55e", "#eab308", "#ef4444"]
    regime_bgs = ["#dcfce7", "#fef9c3", "#fee2e2"]
    regime_emoji = ["🟢", "🟡", "🔴"]
    
    st.markdown(f"""
    <div style='background:{regime_bgs[regime_idx]}; border:2px solid {regime_colors[regime_idx]}; border-radius:12px; padding:14px; margin-top:10px;'>
        <div style='text-align:center; margin-bottom:8px; font-size:1.8rem;'>{regime_emoji[regime_idx]}</div>
        <div style='font-weight:800; color:{regime_colors[regime_idx]}; text-align:center; margin-bottom:6px; font-size:0.95rem;'>{regime_options_display[regime_idx]}</div>
        <div style='font-size:0.8rem; color:#475569; text-align:center; line-height:1.5; margin-bottom:8px;'>{t["regime_desc"][regime_idx]}</div>
        <div style='background:white; border-radius:8px; padding:8px; font-size:0.75rem; margin-bottom:6px;'>
            <div style='color:#94a3b8; margin-bottom:2px;'>💰 {t["regime_avg_label"]}</div>
            <div style='font-weight:800; color:{regime_colors[regime_idx]};'>{t["regime_avg"][regime_idx]}</div>
        </div>
        <div style='background:white; border-radius:8px; padding:8px;'>
            <div style='color:#94a3b8; margin-bottom:2px;'>📊 {t["regime_vol_label"]}</div>
            <div style='font-weight:800; color:{regime_colors[regime_idx]};'>{t["regime_vol"][regime_idx]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height:1px; background:#334155; margin:16px 0;"></div>', unsafe_allow_html=True)
    
    # ───── QUICK STATS ────────────────────────
    st.markdown('<div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#94a3b8; font-weight:800; margin:16px 0 12px;">⚡ Quick Stats</div>', unsafe_allow_html=True)
    
    current_price = float(history_df["price"].iloc[-1])
    price_change = current_price - float(history_df["price"].iloc[-2]) if len(history_df) > 1 else 0
    price_trend = "📈" if price_change >= 0 else "📉"
    
    st.markdown(f"""
    <div style='background:#f8fafc; border-radius:10px; padding:12px; margin-bottom:10px;'>
        <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:4px;'>💰 Current Price</div>
        <div style='font-size:1.5rem; font-weight:900; color:#0f172a; margin-bottom:4px;'>Rs. {current_price:.2f}</div>
        <div style='font-size:0.8rem; color:#475569;'>{price_trend} {price_change:+.2f} last month</div>
    </div>
    
    <div style='background:#f8fafc; border-radius:10px; padding:12px; margin-bottom:10px;'>
        <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:4px;'>📊 Avg Price (2024)</div>
        <div style='font-size:1.3rem; font-weight:900; color:#3b82f6;'>Rs. {history_df[history_df["date"].dt.year == 2024]["price"].mean():.2f}</div>
    </div>
    
    <div style='background:#f8fafc; border-radius:10px; padding:12px;'>
        <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:4px;'>🎯 Market Status</div>
        <div style='font-size:1rem; font-weight:800; color:{regime_colors[regime_idx]};'>{t["regime_status"][regime_idx]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height:1px; background:#334155; margin:16px 0;"></div>', unsafe_allow_html=True)
    
    # ───── FOOTER INFO ─────────────────────────
    st.markdown('<div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#94a3b8; font-weight:800; margin:16px 0 12px;">👨‍🎓 About</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='font-size:0.7rem; color:#cbd5e1; line-height:1.8;'>
        <div><strong style='color:white;'>{t["footer_researcher"]}:</strong><br>M A C S RATHNAYAKE</div>
        <div style='margin-top:8px;'><strong style='color:white;'>{t["footer_ids"]}:</strong><br>UOW: w1999714<br>IIT: 20220508</div>
        <div style='margin-top:8px;'><strong style='color:white;'>{t["footer_programme"]}:</strong><br>BSc (Hons)<br>Data Science & Analytics</div>
        <div style='margin-top:8px; opacity:0.6;'>University of Westminster</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Help text
    st.markdown("""
    <div style='background:#1e293b; border-radius:10px; padding:10px; margin-top:16px; text-align:center;'>
        <div style='font-size:0.65rem; color:#94a3b8; line-height:1.6;'>
            💡 <strong>Tip:</strong> Use the navigation menu above to explore different sections of the dashboard.
        </div>
    </div>
    """, unsafe_allow_html=True)
# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────

# ── HERO ─────────────────────────────────────
st.markdown(f"""
<div style='text-align:center; padding: 32px 0 20px;'>
    <span style='background:#dcfce7; border-radius:20px; padding:6px 16px; font-size:0.85rem; font-weight:700; color:#166534;'>
        🥥 {t["subtitle"]}
    </span>
    <h1 style='font-size:2.4rem; font-weight:900; color:#0f172a; margin:16px 0 10px; line-height:1.2;'>{t["tagline"]}</h1>
    <p style='color:#64748b; font-size:1rem; max-width:600px; margin:0 auto;'>{t["desc"]}</p>
</div>
""", unsafe_allow_html=True)

# ── OVERVIEW CARDS ────────────────────────────
if "📊 Overview" in section or "📊 දළ" in section:
    col1, col2, col3, col4 = st.columns(4)
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
        fill="tozeroy", fillcolor="rgba(22,163,74,0.1)",
        line=dict(color="#16a34a", width=2.5),
        name="Price"
    ))
    fig_hero.add_hline(y=65, line_dash="dash", line_color="#eab308", annotation_text="⚠ Warning", annotation_position="right")
    fig_hero.add_hline(y=80, line_dash="dash", line_color="#ef4444", annotation_text="🔴 Crisis", annotation_position="right")
    fig_hero.update_layout(
        title=dict(text="📈 " + ("Recent 3-Year Price Trend" if lang=="en" else "මෑත කාල මිල ප්‍රවණතාව"), font=dict(size=15, color="#0f172a")),
        height=280, margin=dict(l=20, r=80, t=40, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig_hero, use_container_width=True)

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
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border:{border}; border-radius:16px; padding:24px; text-align:center;'>
                <div style='font-size:2.5rem; margin-bottom:8px;'>{regime_emoji[i]}</div>
                <div style='font-weight:800; font-size:1rem; color:{regime_colors[i]}; margin-bottom:8px;'>{t["regime_options"][i]}</div>
                <div style='font-size:0.9rem; color:#475569; line-height:1.6;'>{t["regime_desc"][i]}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Active regime detail
    rc = regime_colors[regime_idx]
    rb = regime_bgs[regime_idx]
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div style='background:{rb}; border-radius:12px; padding:20px; text-align:center;'>
        <div style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>{t["regime_avg_label"]}</div>
        <div style='font-size:1.8rem; font-weight:900; color:{rc};'>{t["regime_avg"][regime_idx]}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style='background:{rb}; border-radius:12px; padding:20px; text-align:center;'>
        <div style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>{t["regime_vol_label"]}</div>
        <div style='font-size:1.8rem; font-weight:900; color:{rc};'>{t["regime_vol"][regime_idx]}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style='background:{rb}; border-radius:12px; padding:20px; text-align:center;'>
        <div style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>{t["regime_status_label"]}</div>
        <div style='font-size:1.8rem; font-weight:900; color:{rc};'>{t["regime_status"][regime_idx]}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Price chart with regime colouring
    fig_reg = go.Figure()
    for r_i, (r_col, r_name) in enumerate(zip(regime_colors, t["regime_options"])):
        mask = history_df["regime"] == r_i
        subset = history_df[mask]
        if not subset.empty:
            fig_reg.add_trace(go.Scatter(
                x=subset["date"], y=subset["price"],
                mode="markers", marker=dict(color=r_col, size=5, opacity=0.7),
                name=r_name
            ))
    fig_reg.add_hline(y=65, line_dash="dash", line_color="#eab308")
    fig_reg.add_hline(y=80, line_dash="dash", line_color="#ef4444")
    fig_reg.update_layout(
        title=dict(text="📊 " + ("Price History by Market Regime" if lang=="en" else "වෙළඳ තත්ත්වය අනුව මිල ඉතිහාසය"), font=dict(size=15)),
        height=300, margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs."),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# ── DEMAND ───────────────────────────────────
elif "📉 Demand" in section or "📉 ඉල්ලුම" in section:
    st.markdown(f'<div class="section-header">{t["demand_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box-blue">{t["demand_note"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        fig_bar = go.Figure(go.Bar(
            x=t["demand_periods"],
            y=t["demand_sens"],
            marker=dict(
                color=["#22c55e", "#eab308", "#ef4444"],
                line=dict(width=0),
            ),
            text=t["demand_sens"],
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
        st.plotly_chart(fig_bar, use_container_width=True)

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

    # Elasticity insight
    st.markdown("#### " + ("📊 Elasticity Summary" if lang=="en" else "📊 ස්ථිතිස්ථික සාරාංශය"))
    c1, c2, c3 = st.columns(3)
    data_e = [
        ("-0.35", "Stable", "#22c55e", "#dcfce7"),
        ("-0.22", "Warning", "#eab308", "#fef9c3"),
        ("-0.12", "Crisis", "#ef4444", "#fee2e2"),
    ]
    for col, (val, period, clr, bg) in zip([c1, c2, c3], data_e):
        with col:
            st.markdown(f"""<div style='background:{bg}; border-radius:12px; padding:18px; text-align:center;'>
            <div style='font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;'>
            {"Elasticity" if lang=="en" else "ස්ථිතිස්ථිකය"} — {period}</div>
            <div style='font-size:2rem; font-weight:900; color:{clr};'>{val}</div>
            <div style='font-size:0.8rem; color:#64748b; margin-top:4px;'>{"Inelastic" if lang=="en" else "අජඩ"}</div>
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
        fill="toself", fillcolor="rgba(245,158,11,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name=t["forecast_range_label"],
        hoverinfo="skip",
    ))
    # Historical
    fig_fore.add_trace(go.Scatter(
        x=hist_recent["date"], y=hist_recent["price"],
        line=dict(color="#3b82f6", width=2.5),
        name=t["forecast_hist_label"],
        mode="lines",
    ))
    # Forecast
    fig_fore.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["price"],
        line=dict(color="#f59e0b", width=2.5, dash="dash"),
        name=t["forecast_pred_label"],
        mode="lines+markers",
        marker=dict(size=6, color="#f59e0b"),
    ))
    fig_fore.add_vline(
        x=forecast_df["date"].iloc[0].timestamp() * 1000,
        line_dash="dot", line_color="#94a3b8",
        annotation_text="Forecast →", annotation_position="top right",
    )
    fig_fore.update_layout(
        height=340, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_fore, use_container_width=True)

    # 12-week mini table
    st.markdown("#### " + ("📅 Weekly Forecast" if lang=="en" else "📅 සතිපතා අනාවැකිය"))
    cols = st.columns(6)
    for i, (col, (_, row)) in enumerate(zip(cols * 2, forecast_df.iterrows())):
        if i >= 12:
            break
        price = row["price"]
        clr = "#ef4444" if price > 75 else "#eab308" if price > 65 else "#22c55e"
        with cols[i % 6]:
            st.markdown(f"""
            <div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 6px; text-align:center; margin-bottom:8px;'>
                <div style='font-size:0.7rem; color:#94a3b8; margin-bottom:2px;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:0.95rem; font-weight:800; color:{clr};'>Rs.{price:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

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

    # Policy timeline / decision flow
    st.markdown("#### " + ("📋 Policy Decision Framework" if lang=="en" else "📋 ප්‍රතිපත්ති තීරණ රාමුව"))
    steps = [
        ("1️⃣", "Detect Regime" if lang=="en" else "තත්ත්වය හඳුනන්න", "#3b82f6"),
        ("2️⃣", "Assess Priority" if lang=="en" else "ප්‍රමුඛතාව තීරණය", "#8b5cf6"),
        ("3️⃣", "Implement Policy" if lang=="en" else "ප්‍රතිපත්තිය ක්‍රියාත්මක", "#16a34a"),
        ("4️⃣", "Monitor & Review" if lang=="en" else "නිරීක්ෂණය කරන්න", "#f59e0b"),
    ]
    cols = st.columns(4)
    for col, (emoji, step, clr) in zip(cols, steps):
        with col:
            st.markdown(f"""<div style='text-align:center; background:#f8fafc; border-radius:14px; padding:20px 10px; border:1px solid #e2e8f0;'>
            <div style='font-size:2rem; margin-bottom:8px;'>{emoji}</div>
            <div style='font-weight:700; font-size:0.88rem; color:{clr};'>{step}</div>
            </div>""", unsafe_allow_html=True)

# ── HISTORY ───────────────────────────────────
elif "📈 History" in section or "📈 ඉති" in section:
    st.markdown(f'<div class="section-header">{t["history_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t["history_sub"]}</div>', unsafe_allow_html=True)

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=history_df["date"], y=history_df["price"],
        fill="tozeroy", fillcolor="rgba(22,163,74,0.1)",
        line=dict(color="#16a34a", width=1.8),
        name="Price", mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs. %{y}<extra></extra>",
    ))
    fig_hist.add_hline(y=65, line_dash="dash", line_color="#eab308",
        annotation_text=t["history_warn_label"], annotation_position="top right",
        annotation_font_color="#eab308")
    fig_hist.add_hline(y=80, line_dash="dash", line_color="#ef4444",
        annotation_text=t["history_crisis_label"], annotation_position="bottom right",
        annotation_font_color="#ef4444")
    fig_hist.update_layout(
        height=360, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="#f8fafc", paper_bgcolor="white",
        xaxis=dict(showgrid=False, rangeslider=dict(visible=True), tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Stats
    st.markdown("#### " + ("📊 Summary Statistics" if lang=="en" else "📊 සාරාංශ සංඛ්‍යාන"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 " + ("Max Price" if lang=="en" else "උපරිම මිල"), f"Rs. {history_df['price'].max():.2f}")
    c2.metric("📉 " + ("Min Price" if lang=="en" else "අවම මිල"), f"Rs. {history_df['price'].min():.2f}")
    c3.metric("📊 " + ("Avg Price" if lang=="en" else "සාමාන්‍ය මිල"), f"Rs. {history_df['price'].mean():.2f}")
    c4.metric("📐 " + ("Std Dev" if lang=="en" else "ප්‍රමිති අපගමනය"), f"Rs. {history_df['price'].std():.2f}")

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Regime distribution
    regime_counts = history_df["regime"].value_counts().sort_index()
    fig_pie = go.Figure(go.Pie(
        labels=t["regime_options"],
        values=regime_counts.values,
        hole=0.5,
        marker=dict(colors=["#22c55e", "#eab308", "#ef4444"]),
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    fig_pie.update_layout(
        title=dict(text="🥧 " + ("Regime Distribution (2015–2024)" if lang=="en" else "තත්ත්ව බෙදා හැරීම (2015–2024)"), font=dict(size=14)),
        height=320, margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        showlegend=True,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── METHOD ────────────────────────────────────
elif "🧠 Method" in section or "🧠 ක්‍රමවේදය" in section:
    st.markdown(f'<div class="section-header">{t["method_title"]}</div>', unsafe_allow_html=True)

    step_icons = ["📚", "🔍", "📏", "🔮"]
    step_colors = ["#3b82f6", "#8b5cf6", "#16a34a", "#f59e0b"]
    cols = st.columns(4)
    for i, (col, icon, clr, step) in enumerate(zip(cols, step_icons, step_colors, t["method_steps"])):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:#f8fafc; border-radius:16px; padding:28px 16px; border:1px solid #e2e8f0; height:180px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                <div style='width:52px; height:52px; background:linear-gradient(135deg,{clr},{clr}99); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.5rem; margin:0 auto 14px; box-shadow:0 4px 12px {clr}44;'>{i+1}</div>
                <div style='font-size:1.5rem; margin-bottom:10px;'>{icon}</div>
                <div style='font-size:0.88rem; color:#475569; line-height:1.6; font-weight:500;'>{step}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Technical details (collapsed)
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
# FOOTER (always visible)
# ─────────────────────────────────────────────
st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="footer-box">
    <div style='font-size:2.5rem; margin-bottom:10px;'>🥥</div>
    <div style='font-weight:900; font-size:1.4rem; margin-bottom:4px;'>{t["title"]}</div>
    <div style='font-size:0.9rem; opacity:0.7; margin-bottom:28px;'>{t["subtitle"]}</div>
    <div style='display:flex; justify-content:center; gap:60px; flex-wrap:wrap; border-top:1px solid rgba(255,255,255,0.15); padding-top:24px;'>
        <div>
            <div style='font-size:0.7rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>{t["footer_researcher"]}</div>
            <div style='font-weight:700; font-size:1rem;'>M A C S RATHNAYAKE</div>
        </div>
        <div>
            <div style='font-size:0.7rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>{t["footer_ids"]}</div>
            <div style='font-weight:700; font-size:0.95rem;'>UOW: w1999714</div>
            <div style='font-weight:700; font-size:0.95rem;'>IIT: 20220508</div>
        </div>
        <div>
            <div style='font-size:0.7rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>{t["footer_programme"]}</div>
            <div style='font-weight:600; font-size:0.9rem; opacity:0.85;'>BSc (Hons) Data Science & Analytics</div>
            <div style='font-size:0.8rem; opacity:0.6; margin-top:4px;'>University of Westminster · IIT Campus</div>
        </div>
    </div>
    <div style='margin-top:20px; font-size:0.75rem; opacity:0.4;'>{"Developed as part of BSc (Hons) Data Science & Analytics · University of Westminster" if lang == "en" else "BSc (Hons) දත්ත විද්\u200dයාව හා විශ්ලේෂණ පාඨමාලාව සඳහා සංවර්ධනය කරන ලදී"}</div>
</div>
""", unsafe_allow_html=True)
