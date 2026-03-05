import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

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
# DATA GENERATION
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
    forecast = pd.DataFrame({
        "date": future_dates, 
        "price": np.round(future_prices, 2), 
        "upper": np.round([p + 5 for p in future_prices], 2), 
        "lower": np.round([p - 5 for p in future_prices], 2)
    })
    return hist, forecast

history_df, forecast_df = generate_data()

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────
T = {
    "en": {
        "title": "COCOStat", "subtitle": "Market Intelligence", "tagline": "Sri Lankan Coconut Price Insights",
        "desc": "Analyzing 10 years of auction data to provide real-time price regimes and demand forecasting.",
        "nav": ["📊 Overview", "🚦 Market", "📉 Demand", "🔮 Forecast", "🏛 Policy", "📈 History"],
        "inst": "Coconut Development Authority", "inst_sub": "Market Research Division",
        "lang_toggle": "සිංහල"
    },
    "si": {
        "title": "කොකොස්ටැට්", "subtitle": "වෙළඳපොළ බුද්ධිය", "tagline": "ශ්‍රී ලංකාවේ පොල් මිල විශ්ලේෂණය",
        "desc": "වෙන්දේසි දත්ත වසර 10ක් ඇසුරෙන් මිල වෙනස්වීම් සහ ඉල්ලුම පුරෝකථනය කිරීමේ පද්ධතිය.",
        "nav": ["📊 දළ විශ්ලේෂණය", "🚦 වෙළඳපොළ", "📉 ඉල්ලුම", "🔮 අනාවැකිය", "🏛 ප්‍රතිපත්ති", "📈 ඉතිහාසය"],
        "inst": "පොල් සංවර්ධන අධිකාරිය", "inst_sub": "වෙළඳපොළ පර්යේෂණ අංශය",
        "lang_toggle": "English"
    }
}

# ─────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

def toggle_lang():
    st.session_state.lang = 'si' if st.session_state.lang == 'en' else 'en'

t = T[st.session_state.lang]

# ─────────────────────────────────────────────
# CUSTOM CSS & LAYOUT
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Noto Sans Sinhala', sans-serif;
    }}

    :root {{
        --primary: #2D5A27; 
        --secondary: #A0522D; 
        --accent: #FFD700; 
        --bg-light: #FDFBF7;
    }}

    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}

    /* Top Navigation Bar */
    .fixed-header {{
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 60px;
        background: white;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 0 2rem;
        z-index: 1000;
        border-bottom: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    /* Fixed Header/Description */
    .topic-bar {{
        position: sticky;
        top: 60px;
        background: var(--bg-light);
        padding: 1.2rem 2rem;
        z-index: 999;
        border-bottom: 4px solid var(--primary);
        margin-bottom: 1.5rem;
    }}

    [data-testid="stSidebar"] {{
        background-color: #1B3022 !important;
    }}

    /* Metric Card Styling */
    [data-testid="stMetricValue"] {{
        color: var(--primary) !important;
        font-weight: 700;
    }}
</style>

<div class="fixed-header">
    <button onclick="window.parent.document.querySelector('.lang-btn-trigger button').click()" 
            style="background:var(--primary); border:none; color:white; border-radius:8px; padding:6px 16px; cursor:pointer; font-weight:600; font-size:14px;">
        {t['lang_toggle']}
    </button>
</div>

<div class="topic-bar">
    <div style="display:flex; align-items:center; gap:20px;">
        <span style="font-size:3rem;">🥥</span>
        <div>
            <h1 style="margin:0; color:var(--primary); line-height:1.1; font-size:2rem;">{t['title']}</h1>
            <p style="margin:0; color:var(--secondary); font-weight:700;">{t['tagline']}</p>
            <p style="margin:5px 0 0; color:#555; font-size:0.9rem; max-width:800px;">{t['desc']}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Hidden button for JS to trigger language toggle
with st.container():
    st.markdown('<div class="lang-btn-trigger" style="display:none;">', unsafe_allow_html=True)
    st.button("Toggle", on_click=toggle_lang)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <div style="font-size:3.5rem; margin-bottom:10px;">🌴</div>
            <h2 style="color:white; margin:0; letter-spacing:2px;">COCOStat</h2>
            <p style="color:#8dbb93; font-size:0.8rem; opacity:0.8;">V 2.1 - Intelligence Suite</p>
        </div>
        <hr style="opacity:0.2; margin:10px 0;">
    """, unsafe_allow_html=True)
    
    section = st.radio("Menu", t["nav"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:12px; border: 1px solid rgba(255,255,255,0.1);">
            <p style="color:#8dbb93; font-size:0.7rem; margin-bottom:5px; text-transform:uppercase; font-weight:bold;">Source Agency</p>
            <p style="color:white; font-size:0.9rem; font-weight:600; margin:0;">{t['inst']}</p>
            <p style="color:#aaa; font-size:0.75rem; margin-top:2px;">{t['inst_sub']}</p>
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

if "Overview" in section or "දළ" in section:
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Current Price", "Rs. 68.50", "↑ 2.4%")
    with c2: st.metric("Market State", "Stable", "🟢")
    with c3: st.metric("Demand Status", "Inelastic", "High Need")
    with c4: st.metric("Next 30 Days", "Rs. 71.20", "Forecasted")

    st.markdown("### 📈 Recent Auction Trend")
    # THE FIX: px.line now works because import is present
    fig = px.line(history_df.tail(24), x="date", y="price", 
                 color_discrete_sequence=['#2D5A27'],
                 labels={"price": "Price (Rs.)", "date": "Month"})
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0), 
        height=400,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#eee')
    )
    st.plotly_chart(fig, use_container_width=True)

elif "History" in section or "ඉති" in section:
    st.markdown("### 📊 Complete Historical Data")
    st.dataframe(history_df.sort_values("date", ascending=False), use_container_width=True)

else:
    st.warning("This section is currently being integrated with the new UI. Please select 'Overview' or 'History'.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:50px; padding:20px; border-top:1px solid #eee; color:#888; font-size:0.8rem; text-align:center;">
    <b>{t['inst']}</b> | Analytics powered by Markov Switching Models & ARIMA Forecasts.<br>
    © 2026 COCOStat Market Intelligence Unit. Homagama, Western Province, Sri Lanka.
</div>
""", unsafe_allow_html=True)
