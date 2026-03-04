# ============================================================
# 🥥 COCOStat – Coconut Market Intelligence Dashboard
# Fully Redesigned Version (Sri Lankan Coconut Theme)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="COCOStat – Coconut Market Intelligence",
    page_icon="🥥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# SESSION STATE (Sidebar Toggle)
# ------------------------------------------------------------
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

def toggle_sidebar():
    st.session_state.sidebar_open = not st.session_state.sidebar_open

# ------------------------------------------------------------
# TRADITIONAL SRI LANKAN COCONUT THEME CSS
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans Sinhala', sans-serif;
}

/* Hide Streamlit default */
#MainMenu, footer, header {visibility:hidden;}

/* Sidebar */
div[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#3a5a40,#588157);
    padding-top:20px;
}
div[data-testid="stSidebar"] *{
    color:white !important;
    font-weight:600;
}

/* Toggle Button */
.toggle-btn{
    font-size:1.6rem;
    cursor:pointer;
}

/* Hero */
.hero-box{
    background: linear-gradient(135deg,#fefae0,#faedcd);
    padding:40px 20px;
    border-radius:20px;
    text-align:center;
    border:2px solid #dda15e;
}

/* Metric Cards */
[data-testid="metric-container"]{
    background:linear-gradient(135deg,#e9edc9,#ccd5ae);
    border-radius:18px;
    padding:20px;
    border:1px solid #a3b18a;
}

/* Footer */
.footer-box{
    background:linear-gradient(135deg,#344e41,#3a5a40);
    padding:40px;
    border-radius:20px;
    color:white;
    margin-top:50px;
}
.footer-title{
    font-weight:800;
    font-size:1.1rem;
    margin-bottom:8px;
}
.small-text{
    font-size:0.85rem;
    opacity:0.85;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# LANGUAGE ICON (TOP RIGHT CORNER)
# ------------------------------------------------------------
top_col1, top_col2 = st.columns([9,1])
with top_col2:
    lang = st.selectbox("🌐", ["English","සිංහල"], label_visibility="collapsed")

# ------------------------------------------------------------
# SIDEBAR CONTROL ICON
# ------------------------------------------------------------
icon_col1, icon_col2 = st.columns([1,20])
with icon_col1:
    if st.button("☰" if not st.session_state.sidebar_open else "✖"):
        toggle_sidebar()

if st.session_state.sidebar_open:
    with st.sidebar:
        st.markdown("## 🥥 COCOStat")
        st.markdown("### Navigation")
        section = st.radio(
            "",
            ["📊 Overview","🚦 Market","📉 Demand","🔮 Forecast","🏛 Policy","📈 History","🧠 Method"],
            label_visibility="collapsed"
        )
else:
    section = "📊 Overview"

# ------------------------------------------------------------
# GENERATE DATA
# ------------------------------------------------------------
@st.cache_data
def generate():
    dates = pd.date_range("2015-01-01","2024-08-01",freq="MS")
    n=len(dates)
    base=45+np.sin(np.arange(n)/8)*12+np.arange(n)*0.18
    noise=np.random.normal(0,4,n)
    prices=base+noise
    df=pd.DataFrame({"date":dates,"price":prices})
    return df

history_df=generate()

# ------------------------------------------------------------
# HERO SECTION (UNCHANGED CONTENT)
# ------------------------------------------------------------
st.markdown("""
<div class="hero-box">
<h2>Coconut Market Intelligence Dashboard</h2>
<p>Understanding Coconut Prices in Simple Terms</p>
<p>This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# OVERVIEW SECTION
# ------------------------------------------------------------
if section=="📊 Overview":
    col1,col2,col3,col4=st.columns(4)
    col1.metric("💰 Current Price","Rs. 68.50","Per Nut (Auction)")
    col2.metric("📊 Market Condition","🟢 Stable","Normal conditions")
    col3.metric("📉 Demand Response","Inelastic","People still buy")
    col4.metric("🔮 Future Trend","↑ Slight Rise","Next 12 Weeks")

    fig=go.Figure()
    fig.add_trace(go.Scatter(
        x=history_df["date"],
        y=history_df["price"],
        fill="tozeroy"
    ))
    fig.update_layout(
        height=350,
        margin=dict(l=20,r=20,t=30,b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
    )
    st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------------------
# FOOTER (USEFUL SRI LANKA INFO)
# ------------------------------------------------------------
today=datetime.now().strftime("%d %B %Y")

st.markdown(f"""
<div class="footer-box">

<div style="text-align:center;font-size:2rem;">🥥</div>
<div style="text-align:center;font-size:1.3rem;font-weight:900;">COCOStat – Sri Lanka Coconut Intelligence</div>

<hr style="border:0.5px solid rgba(255,255,255,0.2);margin:25px 0;">

<div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:40px;">

<div>
<div class="footer-title">📅 Current Date</div>
<div class="small-text">{today}</div>
</div>

<div>
<div class="footer-title">🏢 Coconut Development Authority</div>
<div class="small-text">
Head Office – Colombo 02<br>
Regional Offices – Kurunegala, Gampaha, Matara
</div>
</div>

<div>
<div class="footer-title">📍 Major Coconut Producing Districts</div>
<div class="small-text">
Kurunegala<br>
Puttalam<br>
Gampaha<br>
Colombo
</div>
</div>

<div>
<div class="footer-title">🌴 Sri Lanka Coconut Industry</div>
<div class="small-text">
Over 2,500 million nuts annually<br>
Exports: Coconut oil, desiccated coconut, coconut milk
</div>
</div>

</div>

<div style="text-align:center;margin-top:30px;font-size:0.8rem;opacity:0.7;">
Traditional Sri Lankan Coconut Theme Dashboard
</div>

</div>
""", unsafe_allow_html=True)
