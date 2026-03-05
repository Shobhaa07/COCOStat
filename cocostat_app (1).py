import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
# DATA GENERATION (Keep stable)
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
# STATE MANAGEMENT & UI OVERRIDES
# ─────────────────────────────────────────────
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

def toggle_lang():
    st.session_state.lang = 'si' if st.session_state.lang == 'en' else 'en'

t = T[st.session_state.lang]

# CUSTOM CSS FOR THEME AND FIXED ELEMENTS
st.markdown(f"""
<style>
    /* Traditional Sri Lankan Palette */
    :root {{
        --primary: #2D5A27; /* Coconut Leaf Green */
        --secondary: #A0522D; /* Terracotta */
        --accent: #FFD700; /* Ceylon Gold */
        --bg-light: #FDFBF7;
    }}

    /* Hide Default Elements */
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebarNav"] {{display: none;}}

    /* Fixed Header with Language Switcher */
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

    /* Fixed Topic Description (Sticky Top) */
    .topic-bar {{
        position: sticky;
        top: 60px;
        background: var(--bg-light);
        padding: 1rem 2rem;
        z-index: 999;
        border-bottom: 3px solid var(--primary);
        margin-bottom: 2rem;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #1B3022 !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }}
    
    .sidebar-btn {{
        display: block;
        padding: 12px 20px;
        color: white;
        text-decoration: none;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: 0.3s;
    }}
    
    .sidebar-btn:hover {{
        background: rgba(255,255,255,0.1);
    }}

    /* Custom Toggle Button Styling */
    .custom-toggle {{
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 1001;
        background: var(--primary);
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}

    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .topic-bar h1 {{ font-size: 1.5rem; }}
        .topic-bar p {{ font-size: 0.8rem; }}
    }}
</style>

<div class="fixed-header">
    <button onclick="window.parent.document.querySelector('.stButton button').click()" 
            style="background:none; border:1px solid #2D5A27; color:#2D5A27; border-radius:20px; padding:5px 15px; cursor:pointer; font-weight:600;">
        {t['lang_toggle']}
    </button>
</div>

<div class="topic-bar">
    <div style="display:flex; align-items:center; gap:15px;">
        <span style="font-size:2.5rem;">🥥</span>
        <div>
            <h1 style="margin:0; color:var(--primary); line-height:1.1;">{t['title']} <small style="font-size:1rem; color:var(--secondary);">{t['subtitle']}</small></h1>
            <p style="margin:0; color:#666; font-size:0.95rem;"><b>{t['tagline']}</b> | {t['desc']}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Hidden button to bridge HTML click to Streamlit state
if st.button(t['lang_toggle'], key="lang_trigger", on_click=toggle_lang):
    pass

# ─────────────────────────────────────────────
# CUSTOM SIDEBAR CONTENT
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <div style="font-size:3rem;">🌴</div>
            <h2 style="color:white; margin:0;">COCOStat</h2>
            <p style="color:#8dbb93; font-size:0.8rem;">Intelligence Dashboard</p>
        </div>
        <hr style="opacity:0.2; margin:10px 0;">
    """, unsafe_allow_html=True)
    
    section = st.radio("Navigation", t["nav"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;">
            <p style="color:#aaa; font-size:0.7rem; margin-bottom:5px; text-transform:uppercase;">Institutional Data</p>
            <p style="color:white; font-size:0.85rem; font-weight:600; margin:0;">{t['inst']}</p>
            <p style="color:#8dbb93; font-size:0.75rem; margin:0;">{t['inst_sub']}</p>
        </div>
    """, unsafe_allow_html=True)

# JavaScript for Sidebar Toggle Control
components.html("""
<script>
    const sideBar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    const mainContent = window.parent.document.querySelector('.main');
    
    // Auto-inject a custom toggle icon if needed
    // Streamlit's native toggle is usually enough, but we can style it via CSS
</script>
""", height=0)

# ─────────────────────────────────────────────
# MAIN DASHBOARD LOGIC
# ─────────────────────────────────────────────

# Space for the fixed header
st.markdown("<br><br>", unsafe_allow_html=True)

if "Overview" in section or "දළ" in section:
    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Current Price", "Rs. 68.50", "↑ 2.4%")
    with c2: st.metric("Market State", "Stable", "Normal")
    with c3: st.metric("Export Volume", "14.2M", "Nuts")
    with c4: st.metric("Forecast", "↑ Slight Rise", "12 Wks")

    # Main Chart
    st.markdown("### Recent Auction Performance")
    fig = px.line(history_df.tail(24), x="date", y="price", color_discrete_sequence=['#2D5A27'])
    fig.update_layout(plot_bgcolor='white', margin=dict(l=0, r=0, t=20, b=0), height=350)
    st.plotly_chart(fig, use_container_width=True)

elif "Market" in section or "වෙළඳ" in section:
    st.info("Market Regime Analysis based on Volatility Clustering.")
    # Add Regime content here...

elif "History" in section or "ඉති" in section:
    st.markdown("### Historical Records (2015-2024)")
    st.dataframe(history_df, use_container_width=True)

# Final Institutional Footer
st.markdown("---")
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    st.markdown(f"**{t['inst']}** \n© 2024 Market Data Analysis Unit. Information provided for research purposes.")
with col_f2:
    st.markdown("Source: CDA Auction Data / Customs Returns")

# NEXT STEP
# Would you like me to add the specific Markov Switching charts to the Market section?
