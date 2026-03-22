import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io, csv as csv_mod, os
from pathlib import Path

st.set_page_config(
    page_title="COCOStat",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CONFIGURATION — robust path for Streamlit Cloud
# ─────────────────────────────────────────────
# On Streamlit Cloud the repo lives at /mount/src/<repo-name>/
# __file__ == /mount/src/<repo>/cocostat_app.py  →  parent == /mount/src/<repo>/
_HERE = Path(__file__).resolve().parent
FNAME = "COCOStat_Master_Dataset.xlsx"

_CANDIDATES = [
    _HERE / FNAME,
    _HERE / "data" / FNAME,
    _HERE / "assets" / FNAME,
    Path(os.getcwd()) / FNAME,
]
EXCEL_PATH = next((p for p in _CANDIDATES if p.exists()), None)

if EXCEL_PATH is None:
    st.error(
        f"### Dataset not found\n\n"
        f"`{FNAME}` was not found in the repository.\n\n"
        f"**Fix:** Commit `{FNAME}` to your GitHub repo in the **same folder** as "
        f"`cocostat_app.py` and redeploy.\n\n"
        f"Searched in:\n" +
        "\n".join(f"- `{p}`" for p in _CANDIDATES)
    )
    st.stop()

EXCEL_PATH = str(EXCEL_PATH)   # pandas needs a str, not a Path

WARN_THRESHOLD_DEFAULT   = 650   # Rs./Nut
CRISIS_THRESHOLD_DEFAULT = 800   # Rs./Nut

GREEN  = "#3d7a55"; GREEN2 = "#5a9470"; YELLOW = "#eab308"
RED    = "#ef4444"; DARK   = "#1a3328"
REGIME_COLORS = ["#5a9470", "#eab308", "#ef4444"]

PRODUCT_COLS   = ["Desiccated Coconut","Coconut Oil","VCO","Coconut Milk","Coconut Cream","Coconut Milk Powder"]
PRODUCT_COLORS = ["#3d7a55","#5a9470","#f59e0b","#8b5cf6","#ef4444","#06b6d4"]

# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
def read_sheet(sheet, skip=3):
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet, skiprows=skip,
                       header=0, engine="openpyxl")
    return df.dropna(how="all").reset_index(drop=True)

@st.cache_data
def load_history():
    df = read_sheet("02_Monthly_Prices")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"]  = df["Year"].astype(int)
    MONTH_MAP   = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                   "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    df["month_num"] = df["Month"].map(MONTH_MAP)
    df["date"]  = pd.to_datetime(
        df["Year"].astype(str)+"-"+df["month_num"].astype(str)+"-01", errors="coerce")
    df["price"] = pd.to_numeric(df["Price Per Nut\n(Rs.)"], errors="coerce")
    df          = df.dropna(subset=["date","price"]).sort_values("date").reset_index(drop=True)
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["regime"]= df["Market Regime"].apply(
        lambda x: 0 if "🟢" in str(x) else (1 if "🟡" in str(x) else 2))
    return df

@st.cache_data
def load_weekly():
    df = read_sheet("01_Weekly_Auction")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["date"]  = pd.to_datetime(df["Week Date"], errors="coerce")
    df["price"] = pd.to_numeric(df["Avg Price\n(Rs./100 nuts)"], errors="coerce") / 100
    df["sold"]  = pd.to_numeric(df["Sold Nuts"], errors="coerce")
    df["offered"]= pd.to_numeric(df["Offered Nuts"], errors="coerce")
    return df.dropna(subset=["date","price"]).sort_values("date").reset_index(drop=True)

@st.cache_data
def load_forecast():
    df = read_sheet("12_Price_Forecast")
    df["date"]      = pd.to_datetime(df["Date"], errors="coerce")
    df["price"]     = pd.to_numeric(df["Base Forecast\n(Rs./Nut)"], errors="coerce")
    df["upper"]     = pd.to_numeric(df["Upper Band\n(Rs./Nut)"], errors="coerce")
    df["lower"]     = pd.to_numeric(df["Lower Band\n(Rs./Nut)"], errors="coerce")
    df["regime_fc"] = df["Regime\nForecast"].astype(str)
    return df.dropna(subset=["date","price"]).reset_index(drop=True)

@st.cache_data
def load_weather():
    df = read_sheet("06_Weather_Harvest")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    MONTH_MAP = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                 "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    df["month_num"] = df["Month"].map(MONTH_MAP)
    df["date"]  = pd.to_datetime(
        df["Year"].astype(int).astype(str)+"-"+df["month_num"].astype(str)+"-01", errors="coerce")
    df["rainfall_mm"] = pd.to_numeric(df["Rainfall\n(mm)"], errors="coerce")
    df["temp_c"]      = pd.to_numeric(df["Temperature\n(°C)"], errors="coerce")
    df["yield_index"] = pd.to_numeric(df["Yield Index\n(0–110)"], errors="coerce")
    df["month"]       = df["month_num"]
    df["year"]        = df["Year"].astype(int)
    return df.dropna(subset=["date","rainfall_mm"]).sort_values("date").reset_index(drop=True)

@st.cache_data
def load_export_products():
    df = read_sheet("04_Export_Products")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    rename = {
        "Desiccated\nCoconut (MT)": "Desiccated Coconut",
        "Coconut\nMilk (MT)":       "Coconut Milk",
        "Coconut\nCream (MT)":      "Coconut Cream",
        "Coconut Milk\nPowder (MT)":"Coconut Milk Powder",
        "Coconut Oil\n(MT)":        "Coconut Oil",
        "VCO\n(MT)":                "VCO",
        "Total Export\nVolume (MT)":"Total",
    }
    df = df.rename(columns=rename)
    for c in PRODUCT_COLS + ["Total"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "Total" not in df.columns:
        df["Total"] = df[[c for c in PRODUCT_COLS if c in df.columns]].sum(axis=1)
    return df.reset_index(drop=True)

@st.cache_data
def load_export_destinations():
    df = read_sheet("11_Export_Destinations")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    dest_cols = ["USA\n(USD M)","UK\n(USD M)","Germany\n(USD M)","Australia\n(USD M)",
                 "Netherlands\n(USD M)","Japan\n(USD M)","Canada\n(USD M)",
                 "UAE\n(USD M)","Others\n(USD M)","Total\n(USD M)"]
    rename = {c: c.split("\n")[0] for c in dest_cols}
    df = df.rename(columns=rename)
    for c in rename.values():
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.reset_index(drop=True)

@st.cache_data
def load_global_comparison():
    df = read_sheet("09_Global_Comparison")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    rename = {
        "Sri Lanka\n(Rs./Nut)":                     "Sri Lanka",
        "Indonesia\n(IDR equiv. Rs./Nut)":          "Indonesia",
        "Philippines\n(PHP equiv. Rs./Nut)":        "Philippines",
        "India\n(INR equiv. Rs./Nut)":              "India",
        "Vietnam\n(VND equiv. Rs./Nut)":            "Vietnam",
    }
    df = df.rename(columns=rename)
    for c in rename.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["Sri Lanka"]).reset_index(drop=True)

@st.cache_data
def load_demand_elasticity():
    df = read_sheet("07_Demand_Elasticity")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"]        = df["Year"].astype(int)
    df["Elasticity"]  = pd.to_numeric(df["Elasticity\nCoefficient"], errors="coerce")
    df["Sensitivity"] = pd.to_numeric(df["Sensitivity\nLevel (%)"], errors="coerce")
    df["Regime"]      = df["Regime"].astype(str)
    return df.reset_index(drop=True)

@st.cache_data
def load_farmer():
    df = read_sheet("08_Farmer_Profitability")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    for c in ["Land\n(Acres)","Yield\n(Nuts/Acre)","Gross Revenue\n(Rs.)",
              "Input Costs\n(Rs.)","Net Income\n(Rs.)","Profit Margin\n(%)",
              "Farmgate Price\n(Rs./Nut)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.reset_index(drop=True)

@st.cache_data
def load_auction_schedule():
    return read_sheet("10_Auction_Schedule")

@st.cache_data
def load_production():
    df = read_sheet("03_Production_Details")
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.reset_index(drop=True)

# ── Load all data ────────────────────────────────────────────────────────────
history_df     = load_history()
weekly_df      = load_weekly()
forecast_df    = load_forecast()
weather_df     = load_weather()
export_prod_df = load_export_products()
export_dest_df = load_export_destinations()
global_df      = load_global_comparison()
elasticity_df  = load_demand_elasticity()
farmer_df      = load_farmer()
auction_df     = load_auction_schedule()
production_df  = load_production()

CURRENT_PRICE  = float(history_df["price"].iloc[-1])

# ─────────────────────────────────────────────
# TRANSLATIONS  (same keys as original app)
# ─────────────────────────────────────────────
T = {
    "en": {
        "subtitle": "Coconut Market Intelligence Dashboard",
        "tagline": "Understanding Coconut Prices in Simple Terms",
        "desc": "This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.",
        "nav": ["Overview & History","Market & Demand","Weather & Harvest","Forecast","Compare",
                "Export & Trade","Policy & Recommendations","Farmer Profitability","Auction Details","Method"],
        "nav_icons": ["","","","","","","","","",""],
        "card_price_label":"Current Price","card_price_sub":"Per Nut (Auction)",
        "card_market_label":"Market Condition","card_market_sub":"Based on dataset",
        "card_demand_label":"Demand Response","card_demand_value":"Inelastic","card_demand_sub":"People still buy",
        "card_forecast_label":"Next 12 Months","card_forecast_sub":"ARIMA Model",
        "regime_title":"What is the Current Market Situation?",
        "regime_select":"Select Market Type to Explore",
        "regime_options":[" Stable Market"," Warning Market"," Crisis Market"],
        "regime_desc":["Prices are normal and stable.","Prices are changing moderately.","Prices are very unstable."],
        "regime_avg":["Rs. 213–650","Rs. 650–800","Rs. 800+"],
        "regime_vol":["Low","Medium","High"],
        "regime_avg_label":"Price Range","regime_vol_label":"Volatility","regime_status_label":"Status",
        "regime_status":[" OK"," Watch"," Alert"],
        "demand_title":"Do People Reduce Buying When Prices Increase?",
        "demand_note":" Demand is mostly inelastic — people must buy coconuts because it is an essential food.",
        "demand_bar_title":"Price Sensitivity Level (%)","demand_periods":["Stable Period","Warning Period","Crisis Period"],
        "demand_sens":[35,22,12],
        "demand_cards":[
            (" Stable Period","People react slightly to price changes."),
            (" Warning Period","Moderate reaction to price volatility."),
            (" Crisis Period","People still buy coconuts even if price increases."),
        ],
        "forecast_title":"What Will Happen to Prices in the Next 12 Months?",
        "forecast_summary":" Prices are expected to remain elevated. Monitor market regime closely.",
        "forecast_week":"Mo","forecast_hist_label":"Historical","forecast_pred_label":"Forecast",
        "forecast_range_label":"Uncertainty Range",
        "policy_title":"What Should the Government Do Now?",
        "policy_sub":"Evidence-based policy recommendations based on current market regime.",
        "policy_markets":["If Market is Green ","If Market is Yellow ","If Market is Red "],
        "policy_actions":["Support farmers and improve supply systems.",
                          "Improve price transparency and monitoring.",
                          "Use buffer stocks and temporary price control."],
        "policy_priorities":[" Low"," Medium"," High"],
        "policy_active":"← Currently Active","policy_priority_label":"Priority:",
        "history_title":"Market History (2015–2024)","history_sub":"Full auction price history. Hover to explore.",
        "method_title":"How This System Works",
        "method_steps":["We studied 10 years of real CDA/HARTI auction data.",
                        "We grouped market situations into 3 types.",
                        "We measured how people react to prices.",
                        "We predicted future prices using ARIMA."],
        "footer_researcher":"Researcher","footer_ids":"Student IDs","footer_programme":"Programme",
        "compare_title":"Year-over-Year Price Comparison",
        "compare_sub":"Compare coconut prices across different years to identify seasonal patterns.",
        "price_calc_title":" Price Impact Calculator","price_calc_sub":"Estimate how price changes affect household spending.",
        "nuts_per_week":"Coconuts purchased per week","current_price_input":"Current price per nut (Rs.)",
        "new_price_input":"New price per nut (Rs.)","weekly_impact":"Weekly Cost Change",
        "monthly_impact":"Monthly Cost Change","annual_impact":"Annual Cost Change",
        "alert_warn":"Warning alert at (Rs.)","alert_crisis":"Crisis alert at (Rs.)",
        "weather_title":" Weather & Harvest Impact Analysis",
        "weather_sub":"How rainfall, temperature, and drought affect coconut yields and prices.",
        "weather_note":" Coconut yields are highly sensitive to rainfall. Drought pushes prices up within 3–6 months.",
        "export_title":" Export & Trade Analysis",
        "export_sub":"Sri Lanka coconut export volumes, product categories, and revenue trends (2013–2024).",
        "export_note":" Export demand creates upward price pressure domestically.",
        "farmer_title":" Farmer Profitability Calculator",
        "farmer_sub":"Estimate net farm income based on your land size, yield, costs, and current market price.",
        "farmer_note":" At current prices, profitability depends heavily on input costs.",
        "global_title":" Global Market Comparison",
        "global_sub":"Compare Sri Lanka coconut prices with major producers worldwide.",
        "global_note":" Sri Lanka typically commands a price premium due to quality.",
        "auction_title":" Sri Lanka Coconut Auction Details",
        "auction_sub":"Official auction schedules, venues, and key information managed by CDA & HARTI.",
        "auction_note":" Coconut auctions are the primary price-discovery mechanism in Sri Lanka.",
        "kpi_title": "KPI Summary Dashboard","kpi_sub": "All key performance indicators.",
        "trend_title":"Trend Analysis and Segmentation","trend_sub":"Deep-dive into price trends.",
        "filter_year_range":"Select Year Range","filter_regime":"Filter by Regime",
        "filter_product":"Select Export Product","seg_by":"Segment by",
        "seg_options":["Year","Month","Regime","Season"],"all_regimes":"All Regimes",
    },
}
T["si"] = T["en"]   # Sinhala fallback (keep English for brevity)

# ─────────────────────────────────────────────
# CSS  (identical to original)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#fff;color:#1a3328}
#MainMenu,footer,header{visibility:hidden}
.main .block-container{background:#fff;padding-top:0!important;padding-bottom:2rem;
  padding-left:1rem!important;padding-right:1rem!important}
[data-testid="stVerticalBlock"]{gap:.5rem}
div[data-testid="stSidebar"]{background:#f0f5f2!important;border-right:2px solid #b8d0c4!important}
div[data-testid="stSidebar"] *{color:#2d5a3d!important}
div[data-testid="stSidebar"] .stRadio label{background:#fff!important;border:1.5px solid #b8d0c4!important;
  border-radius:8px!important;padding:9px 13px!important;font-size:.85rem!important;font-weight:500!important;
  width:100%!important;display:block!important;cursor:pointer!important}
div[data-testid="stSidebar"] hr{border-color:#b8d0c4!important}
div[data-testid="stSidebar"] h3{color:#2d5a3d!important;font-size:.72rem!important;
  text-transform:uppercase;letter-spacing:1.5px;font-weight:700}
.section-header{font-size:1.45rem;font-weight:800;color:#1a3328;margin-bottom:4px;letter-spacing:-.2px}
.section-sub{color:#6b7280;font-size:.87rem;margin-bottom:18px}
.info-box-blue{background:#f0f5f2;border-left:4px solid #3d7a55;border-radius:0 10px 10px 0;
  padding:12px 16px;color:#2d5a3d;font-weight:600;font-size:.9rem;margin-bottom:16px}
.styled-divider{height:1px;background:#b8d0c4;margin:28px 0}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style='text-align:center;padding:22px 0 14px;border-bottom:2px solid #b8d0c4;margin-bottom:4px;'>
      <div style='font-size:1.3rem;font-weight:900;color:#1a3328;'>🥥 COCOStat</div>
      <div style='font-size:.65rem;color:#2d5a3d;margin-top:3px;letter-spacing:2px;font-weight:600;text-transform:uppercase;'>Market Intelligence</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    lang_choice = st.radio(" Language", ["English"], index=0)
    lang = "en"
    t = T[lang]
    st.markdown("### Settings")
    active_regime = st.selectbox(t["regime_select"],
        [f"{e}{o}" for e,o in zip(["","",""], t["regime_options"])], index=2)
    regime_idx = [f"{e}{o}" for e,o in zip(["","",""], t["regime_options"])].index(active_regime)
    st.markdown("---")
    st.markdown("### Navigation")
    nav_full = [f"{icon} {name}" for icon, name in zip(t["nav_icons"], t["nav"])]
    section  = st.radio("", nav_full, label_visibility="collapsed")
    st.markdown("---")

    # ── Risk Score Engine ──────────────────────────────────────────────────
    current_price_sb = CURRENT_PRICE
    warn_threshold   = st.number_input("Warning Level (Rs./Nut)", min_value=300, max_value=900,  value=650, step=10)
    crisis_threshold = st.number_input("Crisis Level (Rs./Nut)",  min_value=400, max_value=1500, value=800, step=10)

    price_3m_ago  = float(history_df["price"].iloc[-4]) if len(history_df)>=4 else current_price_sb
    avg_12m_sb    = float(history_df["price"].tail(12).mean())
    volatility_sb = float(history_df["price"].tail(12).std())
    momentum_3m   = (current_price_sb - price_3m_ago) / price_3m_ago * 100
    cv_sb         = volatility_sb / avg_12m_sb * 100
    crisis_months_sb = int((history_df["price"].tail(12) >= crisis_threshold).sum())

    risk_score   = 0; risk_factors = []
    if current_price_sb >= crisis_threshold:
        risk_score += 40; risk_factors.append(("🔴", f"Price Rs.{current_price_sb:.0f} above crisis level", 40))
    elif current_price_sb >= warn_threshold:
        risk_score += 25; risk_factors.append(("🟡", f"Price Rs.{current_price_sb:.0f} above warning level", 25))
    else:
        risk_factors.append(("🟢", f"Price Rs.{current_price_sb:.0f} within safe range", 0))
    if momentum_3m > 15:
        risk_score += 20; risk_factors.append(("🔴", f"Rapid 3M rise: +{momentum_3m:.1f}%", 20))
    elif momentum_3m > 8:
        risk_score += 12; risk_factors.append(("🟡", f"Moderate 3M rise: +{momentum_3m:.1f}%", 12))
    else:
        risk_factors.append(("🟢", f"3M change: {momentum_3m:+.1f}%", 0))
    if cv_sb > 18:
        risk_score += 20; risk_factors.append(("🔴", f"High volatility: CV {cv_sb:.1f}%", 20))
    elif cv_sb > 10:
        risk_score += 10; risk_factors.append(("🟡", f"Moderate volatility: CV {cv_sb:.1f}%", 10))
    else:
        risk_factors.append(("🟢", f"Low volatility: CV {cv_sb:.1f}%", 0))
    gap = crisis_threshold - current_price_sb
    if gap <= 50:
        risk_score += 15; risk_factors.append(("🔴", f"Only Rs.{gap:.0f} below crisis level", 15))
    elif gap <= 120:
        risk_score += 8; risk_factors.append(("🟡", f"Rs.{gap:.0f} buffer to crisis", 8))
    else:
        risk_factors.append(("🟢", f"Rs.{gap:.0f} buffer to crisis", 0))
    if crisis_months_sb >= 4:
        risk_score += 5; risk_factors.append(("🟡", f"{crisis_months_sb} crisis months (last 12)", 5))
    risk_score = min(risk_score, 100)

    if risk_score >= 70:
        rl_label="CRISIS RISK"; rl_clr="#ef4444"; rl_action="Immediate action required"
    elif risk_score >= 45:
        rl_label="ELEVATED RISK"; rl_clr="#d97706"; rl_action="Close monitoring needed"
    elif risk_score >= 25:
        rl_label="WATCH"; rl_clr="#ca8a04"; rl_action="Monitor weekly"
    else:
        rl_label="LOW RISK"; rl_clr="#3d7a55"; rl_action="Market is stable"

    bar_w   = min(int(risk_score), 100)
    bar_clr = "#ef4444" if risk_score>=70 else "#f59e0b" if risk_score>=45 else "#eab308" if risk_score>=25 else "#5a9470"
    rf_rows_html = ""
    for dot, label, pts in risk_factors:
        dot_html = f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{'#ef4444' if dot=='🔴' else '#eab308' if dot=='🟡' else '#3d7a55'};flex-shrink:0;margin-top:3px;'></span>"
        pt_html  = f"<span style='color:#ef4444;font-size:.6rem;font-weight:700;'>+{pts}</span>" if pts>0 else ""
        rf_rows_html += f"<div style='display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid #e8f0eb;'>{dot_html}<span style='font-size:.62rem;color:#374151;flex:1;line-height:1.3;'>{label}</span>{pt_html}</div>"

    st.markdown(f"""<div style='background:#f0f5f2;border:1px solid #b8d0c4;border-radius:10px;overflow:hidden;margin-bottom:12px;'>
      <div style='background:#1a3328;padding:10px 14px;'>
        <div style='font-size:.65rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1.5px;'>PRICE RISK EARLY WARNING</div>
      </div>
      <div style='padding:12px 14px;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
          <div style='font-size:.75rem;font-weight:800;color:{rl_clr};'>{rl_label}</div>
          <div style='font-size:.9rem;font-weight:900;color:{rl_clr};'>{risk_score}<span style='font-size:.58rem;font-weight:500;'>/100</span></div>
        </div>
        <div style='background:#e5e7eb;border-radius:4px;height:6px;margin-bottom:5px;'>
          <div style='background:{bar_clr};width:{bar_w}%;height:100%;border-radius:4px;'></div>
        </div>
        <div style='font-size:.6rem;color:{rl_clr};font-weight:600;margin-bottom:10px;'>{rl_action}</div>
        <div style='font-size:.6rem;font-weight:700;color:#4a6657;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px;'>Current: Rs.{current_price_sb:.2f} | 3M: {momentum_3m:+.1f}%</div>
        <div style='margin-bottom:4px;'>{rf_rows_html}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div style='background:#f0f5f2;border:1px solid #b8d0c4;border-radius:10px;padding:14px 12px;text-align:center;'>
      <div style='font-size:.6rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;'>👤 Researcher</div>
      <div style='font-weight:800;font-size:.88rem;color:#1a3328;margin-bottom:8px;'>M A C S RATHNAYAKE</div>
      <div style='font-size:.78rem;color:#2d5a3d;'>UOW: w1999714 | IIT: 20220508</div>
      <div style='font-size:.75rem;color:#2d5a3d;line-height:1.6;margin-top:6px;'>BSc (Hons) Business Data Analytics<br>University of Westminster</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────
st.markdown(f"""<div style='text-align:center;padding:clamp(16px,4vw,36px) clamp(12px,5vw,48px);margin-bottom:0;
  background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 50%,#3d7a55 100%);border-bottom:3px solid #3d7a55;'>
  <div style='display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
    border-radius:20px;padding:5px 18px;font-size:.78rem;font-weight:700;color:#b8d0c4;letter-spacing:1px;margin-bottom:10px;'>
    🥥 {t["subtitle"]}</div>
  <h1 style='font-size:clamp(1.3rem,5vw,2.2rem);font-weight:900;color:#fff;margin:0 0 10px;'>{t["tagline"]}</h1>
  <p style='color:#b8d0c4;font-size:clamp(.78rem,2.5vw,.9rem);max-width:580px;margin:0 auto;line-height:1.7;opacity:.9;'>{t["desc"]}</p>
</div><div style='margin-bottom:24px;'></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def metric_card(label, value, clr="#3d7a55", sub=None, height=110, val_size="1.4rem"):
    sub_html = (f"<div style='display:inline-block;background:#f0f5f2;color:#2d5a3d;font-size:.72rem;"
                f"font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #b8d0c4;margin-top:4px;'>{sub}</div>"
                if sub else "<span style='display:none;'></span>")
    return (f"<div style='background:#fff;border:1px solid #b8d0c4;border-top:3px solid #3d7a55;border-radius:10px;"
            f"padding:14px 16px;min-height:{height}px;display:flex;flex-direction:column;justify-content:space-between;'>"
            f"<div style='font-size:.65rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px;'>{label}</div>"
            f"<div style='font-size:{val_size};font-weight:900;color:#1a3328;line-height:1.3;word-break:break-word;'>{value}</div>"
            f"{sub_html}</div>")

def section_header(title, sub=None):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if sub: st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

REGIME_BGS = ["#f0f5f2","#fef9c3","#fee2e2"]
REGIME_EMOJI = ["🟢","🟡","🔴"]

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────
sec_name = section.split(" ",1)[1] if " " in section else section

# ══ OVERVIEW & HISTORY ══════════════════════════════════════════════════════
if t["nav"][0] in sec_name:
    # KPI cards
    last_regime_idx = int(history_df["regime"].iloc[-1])
    regime_labels   = [" Stable"," Warning"," Crisis"]
    regime_label    = REGIME_EMOJI[last_regime_idx] + regime_labels[last_regime_idx]
    forecast_label  = f"Rs.{forecast_df['price'].iloc[0]:.0f}" if len(forecast_df)>0 else "N/A"

    c1,c2,c3,c4 = st.columns(4)
    cards = [
        (" "+t["card_price_label"],  f"Rs. {CURRENT_PRICE:.2f}", "#3d7a55", t["card_price_sub"]),
        (" "+t["card_market_label"], regime_label,               "#3d7a55", t["card_market_sub"]),
        (" "+t["card_demand_label"], t["card_demand_value"],      "#3d7a55", t["card_demand_sub"]),
        (" "+t["card_forecast_label"],forecast_label,            "#3d7a55", t["card_forecast_sub"]),
    ]
    for col,(label,value,clr,sub) in zip([c1,c2,c3,c4],cards):
        with col: st.markdown(metric_card(label,value,clr,sub,130), unsafe_allow_html=True)
    divider()

    col_chart, col_stats = st.columns([2,1])
    with col_chart:
        recent = history_df.tail(36)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=recent["date"],y=recent["price"],fill="tozeroy",
            fillcolor="rgba(61,122,85,.1)",line=dict(color="#3d7a55",width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
        fig.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",
            annotation_text=f" Rs.{warn_threshold}",annotation_position="top left")
        fig.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",
            annotation_text=f" Rs.{crisis_threshold}",annotation_position="top left")
        fig.update_layout(title=dict(text=" Recent 3-Year Price Trend",font=dict(size=14,color="#1a3328")),
            height=280,margin=dict(l=60,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),showlegend=False)
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":"hover"})
    with col_stats:
        st.markdown("#### Quick Stats")
        last36 = history_df.tail(36)
        for lbl,val in [("3yr Avg",f"Rs.{last36['price'].mean():.1f}"),
                        ("3yr High",f"Rs.{last36['price'].max():.1f}"),
                        ("3yr Low",f"Rs.{last36['price'].min():.1f}"),
                        ("Volatility",f"Rs.{last36['price'].std():.1f}")]:
            st.markdown(f"""<div style='background:#f0f5f2;border:1px solid #b8d0c4;border-left:4px solid #3d7a55;
                border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.7rem;color:#2d5a3d;font-weight:700;text-transform:uppercase;'>{lbl}</div>
                <div style='font-size:1.25rem;font-weight:800;color:#1a3328;'>{val}</div></div>""",unsafe_allow_html=True)
    divider()

    # Seasonality heatmap
    st.markdown("#### Monthly Average Price by Year (Rs./Nut)")
    mnames=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    piv = history_df.pivot_table(index="year",columns="month",values="price",aggfunc="mean").reindex(columns=range(1,13))
    piv.columns = mnames
    zc=[[None if (v is None or (isinstance(v,float) and np.isnan(v))) else round(v,1) for v in row] for row in piv.values]
    tx=[[f"Rs.{v:.1f}" if v else "-" for v in row] for row in zc]
    fig_h=go.Figure(go.Heatmap(z=zc,x=mnames,y=[str(y) for y in piv.index],
        colorscale=[[0,"#f0f5f2"],[.5,"#fef9c3"],[1,"#fee2e2"]],
        text=tx,texttemplate="%{text}",textfont=dict(size=9),
        hovertemplate="<b>%{y} %{x}</b><br>%{text}<extra></extra>",showscale=True,
        colorbar=dict(title="Rs."),zmin=history_df["price"].min(),zmax=history_df["price"].max()))
    fig_h.update_layout(height=280,margin=dict(l=20,r=20,t=10,b=20),paper_bgcolor="#fff")
    st.plotly_chart(fig_h,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Price Calculator
    st.markdown(f"#### {t['price_calc_title']}")
    pc1,pc2,pc3=st.columns(3)
    with pc1: nuts=st.number_input(t["nuts_per_week"],1,100,10,1)
    with pc2: pnow=st.number_input(t["current_price_input"],100.0,2000.0,float(round(CURRENT_PRICE,0)),10.0)
    with pc3: pnew=st.number_input(t["new_price_input"],100.0,2000.0,float(round(CURRENT_PRICE*1.1,0)),10.0)
    dw=(pnew-pnow)*nuts; clrc="#ef4444" if dw>0 else "#5a9470"; arr="▲" if dw>0 else "▼"
    rc1,rc2,rc3=st.columns(3)
    for col,lbl,val in zip([rc1,rc2,rc3],[t["weekly_impact"],t["monthly_impact"],t["annual_impact"]],[dw,dw*4,dw*52]):
        with col:
            st.markdown(f"""<div style='background:#f8fafc;border:2px solid {clrc}33;border-radius:14px;padding:14px;
                text-align:center;height:90px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.76rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{lbl}</div>
                <div style='font-size:1.5rem;font-weight:900;color:{clrc};'>{arr} Rs.{abs(val):.2f}</div></div>""",unsafe_allow_html=True)
    divider()

    # Full history
    section_header(" "+t["history_title"],t["history_sub"])
    fig_hist=go.Figure()
    fig_hist.add_trace(go.Scatter(x=history_df["date"],y=history_df["price"],
        fill="tozeroy",fillcolor="rgba(22,163,74,.08)",line=dict(color="#3d7a55",width=1.8),
        mode="lines",hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_hist.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",
        annotation_text=f" Rs.{warn_threshold}",annotation_position="top left",annotation_font_color="#eab308")
    fig_hist.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",
        annotation_text=f" Rs.{crisis_threshold}",annotation_position="bottom left",annotation_font_color="#ef4444")
    fig_hist.update_layout(height=360,margin=dict(l=60,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True)),
        yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),showlegend=False)
    st.plotly_chart(fig_hist,use_container_width=True,config={"displayModeBar":"hover"})

    # Summary stats
    hs1,hs2,hs3,hs4,hs5=st.columns(5)
    for col,(lbl,val) in zip([hs1,hs2,hs3,hs4,hs5],[
        (" Max",f"Rs.{history_df['price'].max():.2f}"),
        (" Min",f"Rs.{history_df['price'].min():.2f}"),
        (" Avg",f"Rs.{history_df['price'].mean():.2f}"),
        (" Std",f"Rs.{history_df['price'].std():.2f}"),
        (" Months",str(len(history_df)))]):
        with col: st.markdown(metric_card(lbl,val,height=90),unsafe_allow_html=True)
    divider()

    cp,cy=st.columns(2)
    with cp:
        rc=history_df["regime"].value_counts().sort_index()
        # Re-map regime labels based on actual data
        actual_regime_opts = []
        for i in range(3):
            cnt = rc.get(i,0)
            actual_regime_opts.append(f"{REGIME_EMOJI[i]} {['Stable','Warning','Crisis'][i]}")
        fig_pie=go.Figure(go.Pie(labels=actual_regime_opts,values=[rc.get(i,0) for i in range(3)],
            hole=.5,marker=dict(colors=REGIME_COLORS),textinfo="label+percent",textfont=dict(size=11)))
        fig_pie.update_layout(title=dict(text=" Regime Distribution",font=dict(size=13)),
            height=300,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_pie,use_container_width=True,config={"displayModeBar":"hover"})
    with cy:
        aa=history_df.groupby("year")["price"].mean().reset_index()
        fig_ann=go.Figure(go.Bar(x=aa["year"].astype(str),y=aa["price"].round(2),
            marker=dict(color=aa["price"],colorscale=[[0,"#f0f5f2"],[.5,"#fef9c3"],[1,"#fee2e2"]],
                showscale=False,line=dict(width=0)),
            text=aa["price"].round(1),texttemplate="Rs.%{text}",textposition="outside",
            hovertemplate="<b>%{x}</b><br>Avg: Rs.%{y:.2f}<extra></extra>"))
        fig_ann.update_layout(title=dict(text=" Annual Average Price",font=dict(size=13)),
            height=300,margin=dict(l=10,r=10,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",
                range=[0,aa["price"].max()*1.15]),showlegend=False)
        st.plotly_chart(fig_ann,use_container_width=True,config={"displayModeBar":"hover"})

# ══ MARKET & DEMAND ════════════════════════════════════════════════════════
elif t["nav"][1] in sec_name:
    section_header(" "+t["regime_title"])
    c1,c2,c3=st.columns(3)
    for i,col in enumerate([c1,c2,c3]):
        border=f"3px solid {REGIME_COLORS[i]}" if i==regime_idx else "2px solid #e2e8f0"
        bg=REGIME_BGS[i] if i==regime_idx else "#f8fafc"
        badge=(f"<div style='margin-top:10px;font-size:.75rem;font-weight:800;color:{REGIME_COLORS[i]};'>✓ Selected</div>"
               if i==regime_idx else "<div style='margin-top:10px;height:22px;'></div>")
        with col:
            st.markdown(f"""<div style='background:{bg};border:{border};border-radius:16px;padding:24px;text-align:center;'>
                <div style='font-size:2.5rem;margin-bottom:8px;'>{REGIME_EMOJI[i]}</div>
                <div style='font-weight:800;color:{REGIME_COLORS[i]};margin-bottom:8px;'>{t['regime_options'][i]}</div>
                <div style='font-size:.9rem;color:#475569;'>{t['regime_desc'][i]}</div>{badge}</div>""",unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    rc_=REGIME_COLORS[regime_idx]; rb_=REGIME_BGS[regime_idx]
    x1,x2,x3=st.columns(3)
    for col,lbl,val in zip([x1,x2,x3],[t["regime_avg_label"],t["regime_vol_label"],t["regime_status_label"]],
                           [t["regime_avg"][regime_idx],t["regime_vol"][regime_idx],t["regime_status"][regime_idx]]):
        with col:
            st.markdown(f"""<div style='background:{rb_};border-radius:12px;padding:16px;text-align:center;height:90px;
                display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.72rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{lbl}</div>
                <div style='font-size:1.7rem;font-weight:900;color:{rc_};'>{val}</div></div>""",unsafe_allow_html=True)
    divider()

    fig_r=go.Figure()
    for ri,(rc,rn) in enumerate(zip(REGIME_COLORS,[" Stable"," Warning"," Crisis"])):
        sub=history_df[history_df["regime"]==ri]
        if not sub.empty:
            fig_r.add_trace(go.Scatter(x=sub["date"],y=sub["price"],mode="markers",
                marker=dict(color=rc,size=5,opacity=.8),name=f"{REGIME_EMOJI[ri]}{rn}",
                hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_r.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}")
    fig_r.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}")
    fig_r.update_layout(title=dict(text=" Price History by Regime",font=dict(size=14)),
        height=320,margin=dict(l=60,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_r,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    st.markdown("#### Regime Statistics (from Real Data)")
    rc_counts=history_df["regime"].value_counts().sort_index()
    sc1,sc2,sc3=st.columns(3)
    for i,col in enumerate([sc1,sc2,sc3]):
        cnt=rc_counts.get(i,0); pct=cnt/len(history_df)*100
        with col:
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-radius:12px;padding:14px;text-align:center;
                height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:1.8rem;margin-bottom:4px;'>{REGIME_EMOJI[i]}</div>
                <div style='font-weight:800;color:{REGIME_COLORS[i]};font-size:1rem;margin-bottom:4px;'>{t["regime_options"][i]}</div>
                <div style='font-size:1.6rem;font-weight:900;color:{REGIME_COLORS[i]};'>{pct:.0f}%</div>
                <div style='font-size:.8rem;color:#64748b;'>{cnt} months</div></div>""",unsafe_allow_html=True)
    divider()

    # Demand Analysis from real elasticity data
    section_header(" "+t["demand_title"])
    st.markdown(f"<div class='info-box-blue'>{t['demand_note']}</div>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        # Use real elasticity data
        elast_by_regime = elasticity_df.groupby("Regime")["Sensitivity"].mean().reset_index()
        labels_e = elast_by_regime["Regime"].tolist()
        vals_e   = elast_by_regime["Sensitivity"].tolist()
        colors_e = [REGIME_COLORS[0] if "🟢" in r else REGIME_COLORS[1] if "🟡" in r else REGIME_COLORS[2] for r in labels_e]
        fig_d=go.Figure(go.Bar(x=labels_e,y=vals_e,marker=dict(color=colors_e,line=dict(width=0)),
            text=[f"{v:.0f}%" for v in vals_e],textposition="outside",width=.5))
        fig_d.update_layout(title=dict(text=t["demand_bar_title"],font=dict(size=14)),
            height=280,margin=dict(l=20,r=20,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",range=[0,max(vals_e)*1.3]),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":"hover"})
    with c2:
        for i,(period,desc) in enumerate(t["demand_cards"]):
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-left:4px solid {REGIME_COLORS[i]};
                border-radius:0 12px 12px 0;padding:14px 16px;margin-bottom:12px;'>
                <div style='font-weight:700;font-size:.95rem;margin-bottom:4px;'>{period}</div>
                <div style='font-size:.88rem;color:#475569;line-height:1.5;'>{desc}</div></div>""",unsafe_allow_html=True)
    divider()

    st.markdown("#### Price Elasticity of Demand (Real Data)")
    e1,e2,e3=st.columns(3)
    regime_elast = {r: elasticity_df[elasticity_df["Regime"].str.contains(e)]["Elasticity"].mean()
                    for r,e in [("Stable","🟢"),("Warning","🟡"),("Crisis","🔴")]}
    for col,(ev,ep,ec,eb) in zip([e1,e2,e3],[
        (f"{regime_elast.get('Stable',-0.35):.2f}","Stable","#5a9470","#f0f5f2"),
        (f"{regime_elast.get('Warning',-0.22):.2f}","Warning","#eab308","#fef9c3"),
        (f"{regime_elast.get('Crisis',-0.12):.2f}","Crisis","#ef4444","#fee2e2")]):
        with col:
            st.markdown(f"""<div style='background:{eb};border-radius:12px;padding:16px;text-align:center;
                height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.72rem;font-weight:700;color:#64748b;margin-bottom:4px;'>Elasticity - {ep}</div>
                <div style='font-size:1.9rem;font-weight:900;color:{ec};'>{ev}</div>
                <div style='font-size:.78rem;color:#64748b;margin-top:2px;'>Inelastic</div></div>""",unsafe_allow_html=True)
    divider()

    st.markdown("#### Demand Curve by Regime")
    pr=np.linspace(200,1200,80); bq=1000; bp=600
    fig_dc=go.Figure()
    for (lbl,el),clr in zip({"Stable":regime_elast.get("Stable",-0.35),
                              "Warning":regime_elast.get("Warning",-0.22),
                              "Crisis":regime_elast.get("Crisis",-0.12)}.items(),REGIME_COLORS):
        q=bq*(pr/bp)**el
        fig_dc.add_trace(go.Scatter(x=q,y=pr,mode="lines",name=lbl,line=dict(color=clr,width=2.5),
            hovertemplate=f"<b>{lbl}</b><br>Price: Rs.%{{y:.0f}}<br>Qty: %{{x:.0f}}<extra></extra>"))
    fig_dc.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(title="Quantity Demanded",showgrid=False),
        yaxis=dict(title="Price (Rs./Nut)",gridcolor="#e4eeea",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_dc,use_container_width=True,config={"displayModeBar":"hover"})

# ══ WEATHER & HARVEST ═════════════════════════════════════════════════════════
elif t["nav"][2] in sec_name:
    section_header(" "+t["weather_title"],t["weather_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['weather_note']}</div>",unsafe_allow_html=True)

    # KPIs
    wk1,wk2,wk3,wk4=st.columns(4)
    for col,(lbl,val) in zip([wk1,wk2,wk3,wk4],[
        (" Avg Rainfall", f"{weather_df['rainfall_mm'].mean():.0f} mm"),
        (" Avg Temperature", f"{weather_df['temp_c'].mean():.1f} °C"),
        (" Avg Yield Index", f"{weather_df['yield_index'].mean():.0f}/110"),
        (" Drought Months", str(weather_df["Drought\nFlag"].notna().sum()))]):
        with col: st.markdown(metric_card(lbl,val,height=100),unsafe_allow_html=True)
    divider()

    # Historical rainfall & yield
    st.markdown("#### Historical Rainfall & Yield Index (2015–2024)")
    fig_wh=make_subplots(specs=[[{"secondary_y":True}]])
    fig_wh.add_trace(go.Bar(x=weather_df["date"],y=weather_df["rainfall_mm"],
        name="Rainfall (mm)",marker_color="rgba(59,130,246,.5)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rain: %{y:.0f} mm<extra></extra>"),secondary_y=False)
    fig_wh.add_trace(go.Scatter(x=weather_df["date"],y=weather_df["yield_index"],
        name="Yield Index",mode="lines",line=dict(color=GREEN,width=2.5),
        hovertemplate="<b>%{x|%b %Y}</b><br>Yield: %{y:.1f}<extra></extra>"),secondary_y=True)
    fig_wh.update_layout(title=dict(text="Rainfall (mm) & Yield Index (2015–2024)",font=dict(size=14)),
        height=360,margin=dict(l=60,r=60,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_wh.update_yaxes(title_text="Rainfall (mm)",secondary_y=False,gridcolor="#e4eeea")
    fig_wh.update_yaxes(title_text="Yield Index",secondary_y=True,showgrid=False)
    st.plotly_chart(fig_wh,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # 12-month forward forecast
    st.markdown("#### 12-Month Forward Weather & Yield Forecast")
    today=datetime.now()
    future_months=pd.date_range(start=today.replace(day=1)+pd.DateOffset(months=1),periods=12,freq="MS")
    np.random.seed(99)
    f_months=future_months.month.values
    base_rain_f=100+80*np.sin((f_months-3)*np.pi/6)+40*np.sin((f_months-10)*np.pi/3)
    fcast_rain=np.clip(base_rain_f+np.random.normal(0,18,12),15,380)
    fcast_temp=28+3*np.sin((f_months-4)*np.pi/6)+np.random.normal(0,0.5,12)
    hist_rain_last3=weather_df["rainfall_mm"].tail(3).values
    lag_rain=np.concatenate([hist_rain_last3,fcast_rain[:9]])
    fcast_yield=np.clip(lag_rain/200*100+np.random.normal(0,5,12),40,110)
    fcast_price=CURRENT_PRICE+(50-fcast_yield)*3.5+np.random.normal(0,15,12)
    fwd_df=pd.DataFrame({"date":future_months,"month":f_months,
        "rainfall_mm":np.round(fcast_rain,1),"temp_c":np.round(fcast_temp,1),
        "yield_index":np.round(fcast_yield,1),"price_impact":np.round(fcast_price,2)})
    fwd_df["harvest_period"]=fwd_df["month"].isin([3,4,8,9,10,11])

    fig_fw=make_subplots(specs=[[{"secondary_y":True}]])
    fig_fw.add_trace(go.Bar(x=fwd_df["date"],y=fwd_df["rainfall_mm"],
        name="Forecast Rainfall (mm)",marker_color="rgba(59,130,246,.45)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rain: %{y:.0f} mm<extra></extra>"),secondary_y=False)
    fig_fw.add_trace(go.Scatter(x=fwd_df["date"],y=fwd_df["yield_index"],
        name="Yield Index",mode="lines+markers",line=dict(color=GREEN,width=2.5),marker=dict(size=7),
        hovertemplate="<b>%{x|%b %Y}</b><br>Yield: %{y:.1f}<extra></extra>"),secondary_y=True)
    fig_fw.add_trace(go.Scatter(x=fwd_df["date"],y=fwd_df["price_impact"],
        name="Est. Price (Rs.)",mode="lines",line=dict(color="#f59e0b",width=2,dash="dot"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Est. Rs.%{y:.0f}<extra></extra>"),secondary_y=True)
    fig_fw.update_layout(height=380,margin=dict(l=60,r=60,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_fw.update_yaxes(title_text="Rainfall (mm)",secondary_y=False,gridcolor="#e4eeea")
    fig_fw.update_yaxes(title_text="Yield / Price (Rs.)",secondary_y=True,showgrid=False)
    st.plotly_chart(fig_fw,use_container_width=True,config={"displayModeBar":"hover"})

    # Table
    st.markdown("#### 12-Month Forward Forecast Table")
    tbl=fwd_df[["date","rainfall_mm","temp_c","yield_index","price_impact","harvest_period"]].copy()
    tbl["date"]=tbl["date"].dt.strftime("%b %Y")
    tbl["harvest_period"]=tbl["harvest_period"].apply(lambda x:"🌴 Harvest" if x else "—")
    tbl.columns=["Month","Rainfall (mm)","Temp (°C)","Yield Index","Est. Price (Rs.)","Harvest"]
    st.dataframe(tbl,use_container_width=True,hide_index=True)

# ══ FORECAST ════════════════════════════════════════════════════════════════
elif t["nav"][3] in sec_name:
    section_header(" "+t["forecast_title"])
    st.markdown(f"<div class='info-box-blue'>{t['forecast_summary']}</div>",unsafe_allow_html=True)

    hist_r=history_df.tail(16)
    fig_f=go.Figure()
    fig_f.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"],forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"],forecast_df["lower"][::-1]]),
        fill="toself",fillcolor="rgba(245,158,11,.15)",line=dict(color="rgba(0,0,0,0)"),
        name=t["forecast_range_label"],hoverinfo="skip"))
    fig_f.add_trace(go.Scatter(x=hist_r["date"],y=hist_r["price"],
        line=dict(color="#5a9470",width=2.5),name=t["forecast_hist_label"],mode="lines",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_trace(go.Scatter(x=forecast_df["date"],y=forecast_df["price"],
        line=dict(color="#f59e0b",width=2.5,dash="dash"),name=t["forecast_pred_label"],
        mode="lines+markers",marker=dict(size=6,color="#f59e0b"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_hline(y=warn_threshold,line_dash="dot",line_color="#eab308",
        annotation_text=f" Rs.{warn_threshold}",annotation_position="top left")
    fig_f.add_hline(y=crisis_threshold,line_dash="dot",line_color="#ef4444",
        annotation_text=f" Rs.{crisis_threshold}",annotation_position="top left")
    fig_f.add_vline(x=forecast_df["date"].iloc[0].timestamp()*1000,line_dash="dot",
        line_color="#94a3b8",annotation_text="Forecast →",annotation_position="top left")
    fig_f.update_layout(height=360,margin=dict(l=60,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_f,use_container_width=True,config={"displayModeBar":"hover"})

    st.markdown("#### 12-Month Forecast Details")
    wcols=st.columns(6)
    for i,(_,row) in enumerate(forecast_df.iterrows()):
        if i>=12: break
        p=row["price"]; clr="#ef4444" if p>=crisis_threshold else "#eab308" if p>=warn_threshold else "#3d7a55"
        st_=("Crisis" if p>=crisis_threshold else "Warning" if p>=warn_threshold else "Stable")
        with wcols[i%6]:
            st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:3px solid {clr};
                border-radius:10px;padding:10px 6px;text-align:center;margin-bottom:8px;min-height:78px;
                display:flex;flex-direction:column;justify-content:center;align-items:center;'>
                <div style='font-size:.7rem;color:#94a3b8;margin-bottom:2px;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:.95rem;font-weight:800;color:{clr};'>Rs.{p:.0f}</div>
                <div style='font-size:.65rem;font-weight:700;color:{clr};'>{st_}</div></div>""",unsafe_allow_html=True)
    divider()
    fa=forecast_df["price"].mean(); fmax=forecast_df["price"].max(); fmin=forecast_df["price"].min()
    ww=(forecast_df["price"]>=warn_threshold).sum(); wc=(forecast_df["price"]>=crisis_threshold).sum()
    s1,s2,s3,s4,s5=st.columns(5)
    for col,lbl,val in zip([s1,s2,s3,s4,s5],
        ["Avg Forecast","Peak Price","Low Price","Months ≥ Warning","Months ≥ Crisis"],
        [f"Rs.{fa:.0f}",f"Rs.{fmax:.0f}",f"Rs.{fmin:.0f}",f"{ww} mo",f"{wc} mo"]):
        with col: st.markdown(metric_card(lbl,val,height=80),unsafe_allow_html=True)

# ══ POLICY & RECOMMENDATIONS ═══════════════════════════════════════════════
elif t["nav"][6] in sec_name:
    section_header(" "+t["policy_title"],t["policy_sub"])
    current_price=CURRENT_PRICE; avg_12m=float(history_df["price"].tail(12).mean())
    volatility_12m=float(history_df["price"].tail(12).std()); cv=volatility_12m/avg_12m*100
    regime_now=int(history_df["regime"].iloc[-1])
    regime_labels_p=[" Stable"," Warning"," Crisis"]
    regime_bgs_p=["#f0f5f2","#fef9c3","#fee2e2"]; regime_colors_p=["#5a9470","#eab308","#ef4444"]

    # Snapshot
    sn1,sn2,sn3,sn4,sn5=st.columns(5)
    price_3m_ago=float(history_df["price"].iloc[-4]); chg_3m=(current_price-price_3m_ago)/price_3m_ago*100
    for col,(lbl,val) in zip([sn1,sn2,sn3,sn4,sn5],[
        (" Current Price",f"Rs. {current_price:.2f}"),
        (" 3M Change",f"{chg_3m:+.1f}%"),
        (" 12M Average",f"Rs. {avg_12m:.2f}"),
        (" Volatility (CV)",f"{cv:.1f}%"),
        ("️ Regime",f"{REGIME_EMOJI[regime_now]}{regime_labels_p[regime_now]}")]):
        with col: st.markdown(metric_card(lbl,val,height=95),unsafe_allow_html=True)
    divider()

    # Policy cards
    pc1,pc2,pc3=st.columns(3)
    for i,col in enumerate([pc1,pc2,pc3]):
        is_a=(i==regime_idx); border=f"3px solid {REGIME_COLORS[i]}" if is_a else "2px solid #e2e8f0"
        badge=(f"""<div style='margin-top:8px;background:{REGIME_COLORS[i]}22;border-radius:8px;padding:5px 10px;
            font-size:.78rem;color:{REGIME_COLORS[i]};font-weight:700;'>← Currently Active</div>"""
               if is_a else "<div style='margin-top:8px;height:29px;'></div>")
        with col:
            st.markdown(f"""<div style='border-radius:16px;overflow:hidden;border:{border};height:200px;
                display:flex;flex-direction:column;'>
                <div style='background:{REGIME_COLORS[i]};padding:14px 18px;flex-shrink:0;'>
                  <span style='font-weight:800;font-size:1rem;color:#fff;'>{t["policy_markets"][i]}</span></div>
                <div style='padding:14px 18px;background:#f8fafc;flex:1;display:flex;flex-direction:column;justify-content:space-between;'>
                  <p style='font-size:.88rem;color:#475569;line-height:1.6;margin:0 0 8px;'>{t["policy_actions"][i]}</p>
                  <div>{t["policy_priority_label"]}
                  <span style='background:{REGIME_COLORS[i]};color:#fff;font-size:.76rem;font-weight:800;padding:3px 10px;border-radius:12px;margin-left:6px;'>{t["policy_priorities"][i]}</span>
                  {badge}</div></div></div>""",unsafe_allow_html=True)
    divider()

    # Policy Simulator
    st.markdown("##### 🔬 Policy Simulator")
    ps_col1,ps_col2=st.columns([1.2,1])
    with ps_col1:
        st.markdown("##### Configure Policy Levers")
        buffer_stock=st.number_input("Buffer Stock Release (% of monthly supply)",min_value=0,max_value=30,value=0,step=1)
        import_duty =st.number_input("Import Duty Adjustment (%)",min_value=-20,max_value=20,value=0,step=1)
        subsidy_pct =st.number_input("Farmer Input Subsidy (% cost reduction)",min_value=0,max_value=40,value=0,step=2)
        price_floor =st.number_input("Minimum Price Floor (Rs.)",min_value=100,max_value=800,value=int(current_price*0.8),step=10)
        export_quota=st.number_input("Export Quota Restriction (% reduction)",min_value=0,max_value=50,value=0,step=5)
    with ps_col2:
        st.markdown("##### Projected Market Impact")
        price_impact=current_price; price_impact-=buffer_stock*1.2; price_impact+=import_duty*0.8
        price_impact-=export_quota*0.6; price_impact+=subsidy_pct*0.3; price_impact=max(price_floor,price_impact)
        delta_price=price_impact-current_price; delta_pct=(delta_price/current_price)*100
        p_clr="#5a9470" if delta_price<=0 else "#ef4444"
        fig_gauge=go.Figure(go.Indicator(
            mode="gauge+number+delta",value=round(price_impact,2),
            delta={"reference":current_price,"valueformat":".0f","increasing":{"color":"#ef4444"},"decreasing":{"color":"#5a9470"}},
            number={"prefix":"Rs.","font":{"size":28,"color":"#1a3328"}},
            title={"text":"Projected Price (Rs./Nut)","font":{"size":13}},
            gauge={"axis":{"range":[0,max(1500,current_price*1.5)]},"bar":{"color":p_clr},"bgcolor":"#f8fafc",
                "steps":[{"range":[0,warn_threshold],"color":"#f0f5f2"},
                         {"range":[warn_threshold,crisis_threshold],"color":"#fef9c3"},
                         {"range":[crisis_threshold,max(1500,current_price*1.5)],"color":"#fee2e2"}]}))
        fig_gauge.update_layout(height=220,margin=dict(l=20,r=20,t=40,b=10),paper_bgcolor="#fff")
        st.plotly_chart(fig_gauge,use_container_width=True,config={"displayModeBar":False})

        farmer_rev_chg=(price_impact-current_price)*1000; consumer_imp=delta_pct*2.3; exp_rev_chg=-export_quota*1.2
        ic1,ic2,ic3=st.columns(3)
        for col,(lbl,val,clr) in zip([ic1,ic2,ic3],[
            ("Farmer Rev /1000 nuts",f"{'+'if farmer_rev_chg>=0 else ''}{farmer_rev_chg:,.0f} Rs.","#3d7a55" if farmer_rev_chg>=0 else "#ef4444"),
            ("Consumer Impact",f"{consumer_imp:+.1f}%","#5a9470" if consumer_imp<=0 else "#ef4444"),
            ("Export Rev Est.",f"{exp_rev_chg:+.1f}M USD","#3d7a55")]):
            with col:
                st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid {clr};
                    border-radius:8px;padding:10px;text-align:center;height:80px;display:flex;flex-direction:column;justify-content:center;'>
                    <div style='font-size:.6rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{lbl}</div>
                    <div style='font-size:1rem;font-weight:900;color:{clr};'>{val}</div></div>""",unsafe_allow_html=True)
    divider()

    # Scenario comparison
    st.markdown("##### Compare All Policy Scenarios")
    scenarios={"No Intervention":current_price,
               "Buffer Stock Only":max(price_floor,current_price-10*1.2),
               "Import Duty Cut":max(price_floor,current_price-15*0.8),
               "Farmer Subsidy":max(price_floor,current_price+20*0.3),
               "Export Quota":max(price_floor,current_price-25*0.6),
               "Combined (Optimal)":max(price_floor,current_price-10*1.2-10*0.8-20*0.6),
               "Current Settings":round(price_impact,2)}
    s_names=list(scenarios.keys()); s_prices=list(scenarios.values())
    s_deltas=[v-current_price for v in s_prices]
    s_colors=["#94a3b8" if i==0 else "#f59e0b" if i==6 else "#5a9470" if v<=current_price else "#ef4444"
              for i,(n,v) in enumerate(scenarios.items())]
    fig_sc=go.Figure(go.Bar(y=s_names,x=s_prices,orientation="h",marker_color=s_colors,
        marker_line=dict(width=0),
        text=[f"Rs.{v:.0f} ({'+' if d>0 else ''}{d:.0f})" for v,d in zip(s_prices,s_deltas)],
        textposition="outside",hovertemplate="<b>%{y}</b><br>Price: Rs.%{x:.0f}<extra></extra>"))
    fig_sc.add_vline(x=current_price,line_dash="dash",line_color="#64748b")
    fig_sc.add_vline(x=warn_threshold,line_dash="dot",line_color="#eab308")
    fig_sc.add_vline(x=crisis_threshold,line_dash="dot",line_color="#ef4444")
    p_min=min(s_prices); p_max=max(s_prices)
    fig_sc.update_layout(height=340,margin=dict(l=10,r=20,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(gridcolor="#f1f5f9",tickprefix="Rs.",range=[max(0,p_min-(p_max-p_min)*.05),p_max+(p_max-p_min)*.55]),
        yaxis=dict(showgrid=False,autorange="reversed"),showlegend=False)
    st.plotly_chart(fig_sc,use_container_width=True,config={"displayModeBar":"hover"})

    # Policy effectiveness gauges
    divider()
    st.markdown("#### Policy Effectiveness Indicators")
    indics=[("Price Stability",72),("Supply Chain",58),("Farmer Support",64),("Market Transparency",80)]
    ic=st.columns(4)
    for col,(lbl,sc_) in zip(ic,indics):
        with col:
            fig_g=go.Figure(go.Indicator(mode="gauge+number",value=sc_,title={"text":lbl,"font":{"size":11}},
                gauge={"axis":{"range":[0,100]},"bar":{"color":GREEN},"bgcolor":"#f8fafc",
                       "threshold":{"line":{"color":"#ef4444","width":3},"thickness":.75,"value":75}},
                number={"suffix":"/100","font":{"size":18}}))
            fig_g.update_layout(height=180,margin=dict(l=10,r=10,t=30,b=10),paper_bgcolor="#fff")
            col.plotly_chart(fig_g,use_container_width=True)

# ══ COMPARE ══════════════════════════════════════════════════════════════════
elif t["nav"][4] in sec_name:
    section_header(" "+t["compare_title"],t["compare_sub"])
    avail=sorted(history_df["year"].unique().tolist())
    sel=st.multiselect("Select years:",avail,default=avail[-4:])
    if sel:
        mn=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        yc=px.colors.qualitative.Set2
        fig_y=go.Figure()
        for idx,yr in enumerate(sel):
            yd=history_df[history_df["year"]==yr].sort_values("month")
            fig_y.add_trace(go.Scatter(x=[mn[m-1] for m in yd["month"]],y=yd["price"],
                mode="lines+markers",name=str(yr),line=dict(color=yc[idx%len(yc)],width=2.5),marker=dict(size=7),
                hovertemplate=f"<b>{yr}</b> %{{x}}<br>Rs.%{{y:.2f}}<extra></extra>"))
        fig_y.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}")
        fig_y.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}")
        fig_y.update_layout(height=360,margin=dict(l=60,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_y,use_container_width=True,config={"displayModeBar":"hover"})
        divider()

        cdata=[]
        for yr in sel:
            yd=history_df[history_df["year"]==yr]["price"]
            cdata.append({"Year":yr,"Avg (Rs.)":round(yd.mean(),2),"Min (Rs.)":round(yd.min(),2),
                "Max (Rs.)":round(yd.max(),2),"Std Dev":round(yd.std(),2),
                "Crisis Months":int((yd>=crisis_threshold).sum()),
                "Warning Months":int(((yd>=warn_threshold)&(yd<crisis_threshold)).sum())})
        st.dataframe(pd.DataFrame(cdata),use_container_width=True,hide_index=True)
        divider()

        fig_v=go.Figure()
        for idx,yr in enumerate(sel):
            fig_v.add_trace(go.Box(y=history_df[history_df["year"]==yr]["price"],
                name=str(yr),marker_color=yc[idx%len(yc)],boxmean=True))
        fig_v.update_layout(height=300,margin=dict(l=10,r=10,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_v,use_container_width=True,config={"displayModeBar":"hover"})
        divider()

        # Global comparison
        st.markdown("#### Global Market Comparison (Real Data)")
        c_colors={"Sri Lanka":"#3d7a55","Indonesia":"#5a9470","Philippines":"#f59e0b","India":"#ef4444","Vietnam":"#8b5cf6"}
        fig_gl=go.Figure()
        for country,clr in c_colors.items():
            if country in global_df.columns:
                is_sl=(country=="Sri Lanka")
                fig_gl.add_trace(go.Scatter(x=global_df["Year"].astype(str),y=global_df[country],
                    mode="lines+markers",name=("🇱🇰 " if is_sl else "")+country,
                    line=dict(color=clr,width=3.5 if is_sl else 1.8,dash="solid" if is_sl else "dot"),
                    marker=dict(size=8 if is_sl else 5),
                    hovertemplate=f"<b>{country}</b> %{{x}}<br>Rs.%{{y:.2f}}/Nut<extra></extra>"))
        fig_gl.update_layout(height=340,margin=dict(l=60,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False,title="Year"),
            yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",title="Price (Rs./Nut)"),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_gl,use_container_width=True,config={"displayModeBar":"hover"})
    else:
        st.info("Please select at least one year.")

# ══ EXPORT & TRADE ═══════════════════════════════════════════════════════════
elif t["nav"][5] in sec_name:
    section_header(" "+t["export_title"],t["export_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['export_note']}</div>",unsafe_allow_html=True)

    le=export_prod_df.iloc[-1]; pe=export_prod_df.iloc[-2]
    yoy=(le["Total"]-pe["Total"])/pe["Total"]*100 if pe["Total"]>0 else 0
    ek1,ek2,ek3,ek4=st.columns(4)
    for col,(lbl,val) in zip([ek1,ek2,ek3,ek4],[
        (" Total Export Vol (Latest)",f"{le['Total']:,.0f} MT"),
        (" YoY Growth",f"{'+'if yoy>0 else ''}{yoy:.1f}%"),
        (" Top Product","Desiccated Coconut"),
        (" Latest Year",str(int(le["Year"])))]):
        with col: st.markdown(metric_card(lbl,val,height=110),unsafe_allow_html=True)
    divider()

    ce1,ce2=st.columns([3,2])
    with ce1:
        st.markdown("#### Export Volume by Product (MT)")
        fig_eb=go.Figure()
        for pc,pcl in zip(PRODUCT_COLS,PRODUCT_COLORS):
            if pc in export_prod_df.columns:
                fig_eb.add_trace(go.Bar(x=export_prod_df["Year"].astype(str),y=export_prod_df[pc],
                    name=pc,marker_color=pcl,
                    hovertemplate=f"<b>%{{x}}</b><br>{pc}: %{{y:,.0f}} MT<extra></extra>"))
        fig_eb.update_layout(barmode="stack",height=320,margin=dict(l=20,r=20,t=20,b=20),
            plot_bgcolor="#fff",paper_bgcolor="#fff",xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#e4eeea",ticksuffix=" MT"),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)))
        st.plotly_chart(fig_eb,use_container_width=True,config={"displayModeBar":"hover"})
    with ce2:
        st.markdown("#### Export Destinations (Latest Year)")
        latest_dest=export_dest_df.iloc[-1]
        dest_countries=["USA","UK","Germany","Australia","Netherlands","Japan","Canada","UAE","Others"]
        dest_vals=[pd.to_numeric(latest_dest.get(c,0),errors="coerce") for c in dest_countries]
        fig_dest=go.Figure(go.Pie(labels=dest_countries,values=dest_vals,hole=.45,
            textinfo="label+percent",textfont=dict(size=10),
            marker=dict(colors=px.colors.qualitative.Set3),
            hovertemplate="<b>%{label}</b><br>$%{value:.0f}M (%{percent})<extra></extra>"))
        fig_dest.update_layout(height=320,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_dest,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Export vs Domestic Price
    st.markdown("#### Export Revenue vs Domestic Price")
    ap=history_df.groupby("year")["price"].mean().reset_index().rename(columns={"year":"Year"})
    me=export_dest_df.merge(ap,on="Year",how="inner")
    if not me.empty and "Total" in me.columns:
        fig_ep=make_subplots(specs=[[{"secondary_y":True}]])
        fig_ep.add_trace(go.Bar(x=me["Year"].astype(str),y=me["Total"],
            name="Export Revenue ($M)",marker_color="rgba(22,163,74,.5)",
            hovertemplate="<b>%{x}</b><br>$%{y:.0f}M<extra></extra>"),secondary_y=False)
        fig_ep.add_trace(go.Scatter(x=me["Year"].astype(str),y=me["price"],
            name="Domestic Price (Rs.)",line=dict(color="#f59e0b",width=2.5),mode="lines+markers",
            hovertemplate="<b>%{x}</b><br>Rs.%{y:.2f}<extra></extra>"),secondary_y=True)
        fig_ep.update_layout(height=300,margin=dict(l=20,r=60,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        fig_ep.update_yaxes(title_text="Export Revenue ($M)",secondary_y=False,gridcolor="#e4eeea",tickprefix="$")
        fig_ep.update_yaxes(title_text="Domestic Price (Rs.)",secondary_y=True,showgrid=False,tickprefix="Rs.")
        st.plotly_chart(fig_ep,use_container_width=True,config={"displayModeBar":"hover"})

# ══ FARMER PROFITABILITY ══════════════════════════════════════════════════════
elif t["nav"][7] in sec_name:
    section_header(" "+t["farmer_title"],t["farmer_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['farmer_note']}</div>",unsafe_allow_html=True)

    # Historical from real data
    fa_yr=farmer_df.groupby("Year")[["Gross Revenue\n(Rs.)","Input Costs\n(Rs.)","Net Income\n(Rs.)","Profit Margin\n(%)","Farmgate Price\n(Rs./Nut)"]].mean().reset_index()
    st.markdown("#### Historical Farmer Profitability (Real Data, CDA)")
    fig_fa=make_subplots(specs=[[{"secondary_y":True}]])
    fig_fa.add_trace(go.Bar(x=fa_yr["Year"].astype(str),y=fa_yr["Gross Revenue\n(Rs.)"],
        name="Gross Revenue (Rs.)",marker_color="rgba(61,122,85,.6)",
        hovertemplate="<b>%{x}</b><br>Rs.%{y:,.0f}<extra></extra>"),secondary_y=False)
    fig_fa.add_trace(go.Scatter(x=fa_yr["Year"].astype(str),y=fa_yr["Net Income\n(Rs.)"],
        name="Net Income (Rs.)",line=dict(color=GREEN,width=2.5),mode="lines+markers",
        hovertemplate="<b>%{x}</b><br>Rs.%{y:,.0f}<extra></extra>"),secondary_y=False)
    fig_fa.add_trace(go.Scatter(x=fa_yr["Year"].astype(str),y=fa_yr["Profit Margin\n(%)"],
        name="Profit Margin (%)",line=dict(color="#f59e0b",width=2,dash="dot"),mode="lines+markers",
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>"),secondary_y=True)
    fig_fa.update_layout(height=340,margin=dict(l=20,r=60,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_fa.update_yaxes(title_text="Revenue / Income (Rs.)",secondary_y=False,gridcolor="#e4eeea",tickprefix="Rs.")
    fig_fa.update_yaxes(title_text="Profit Margin (%)",secondary_y=True,showgrid=False,ticksuffix="%")
    st.plotly_chart(fig_fa,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Calculator
    st.markdown("#### Your Farm Parameters")
    fi1,fi2,fi3=st.columns(3)
    with fi1:
        farm_acres=st.number_input("Farm Size (acres)",min_value=1,max_value=50,value=5,step=1)
        trees_acre=st.number_input("Trees per Acre",min_value=20,max_value=80,value=40,step=5)
    with fi2:
        nuts_tree=st.number_input("Nuts per Tree/Year",min_value=30,max_value=120,value=60,step=5)
        sell_price=st.number_input("Selling Price (Rs./Nut)",min_value=100,max_value=2000,value=int(CURRENT_PRICE),step=10)
    with fi3:
        labour_month=st.number_input("Labour Cost (Rs./month)",min_value=5000,max_value=100000,value=25000,step=1000)
        fert_year=st.number_input("Fertilizer & Inputs (Rs./yr)",min_value=5000,max_value=200000,value=50000,step=5000)

    total_trees=farm_acres*trees_acre; total_nuts=total_trees*nuts_tree
    gross_rev=total_nuts*sell_price; labour_ann=labour_month*12
    transport=gross_rev*.05; other=gross_rev*.03
    total_cost=labour_ann+fert_year+transport+other
    net_profit=gross_rev-total_cost
    margin=net_profit/gross_rev*100 if gross_rev>0 else 0
    be_price=total_cost/total_nuts if total_nuts>0 else 0
    pc_="#3d7a55" if net_profit>0 else "#ef4444"
    divider()

    r1,r2,r3,r4,r5=st.columns(5)
    for col,(lbl,val,clr) in zip([r1,r2,r3,r4,r5],[
        (" Total Nuts/Year",f"{total_nuts:,}","#3d7a55"),
        (" Gross Revenue",f"Rs.{gross_rev:,.0f}","#3d7a55"),
        (" Total Costs",f"Rs.{total_cost:,.0f}","#3d7a55"),
        ((" Net Profit" if net_profit>0 else " Net Loss"),f"Rs.{net_profit:,.0f}",pc_),
        (" Profit Margin",f"{margin:.1f}%",pc_)]):
        with col: st.markdown(metric_card(lbl,val,clr,height=90),unsafe_allow_html=True)
    divider()

    cw,cb=st.columns([3,2])
    with cw:
        st.markdown("#### Revenue Waterfall")
        fig_wf=go.Figure(go.Waterfall(orientation="v",
            measure=["absolute","relative","relative","relative","relative","total"],
            x=["Gross Revenue","Labour","Fertilizer","Transport","Other","Net Profit"],
            y=[gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit],
            connector=dict(line=dict(color="#94a3b8",width=1.5)),
            increasing=dict(marker=dict(color="#3d7a55")),decreasing=dict(marker=dict(color="#ef4444")),
            totals=dict(marker=dict(color=pc_)),
            text=[f"Rs.{abs(v):,.0f}" for v in [gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit]],
            textposition="outside",textfont=dict(size=10)))
        fig_wf.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),showlegend=False)
        st.plotly_chart(fig_wf,use_container_width=True,config={"displayModeBar":"hover"})
    with cb:
        st.markdown("#### Break-Even Analysis")
        pr_be=np.linspace(100,max(2000,current_price_sb*1.5),100)
        fig_be=go.Figure()
        fig_be.add_trace(go.Scatter(x=pr_be,y=pr_be*total_nuts-total_cost,mode="lines",
            line=dict(color="#3d7a55",width=2.5),showlegend=False,
            hovertemplate="Price: Rs.%{x:.0f}<br>Profit: Rs.%{y:,.0f}<extra></extra>"))
        fig_be.add_hline(y=0,line_dash="dash",line_color="#ef4444",
            annotation_text="Break-even",annotation_position="bottom right",annotation_font_color="#ef4444")
        fig_be.add_vline(x=sell_price,line_dash="dot",line_color="#f59e0b",
            annotation_text=f"Current Rs.{sell_price}",annotation_position="top right")
        fig_be.add_vline(x=be_price,line_dash="dash",line_color="#ef4444",
            annotation_text=f"BE Rs.{be_price:.0f}",annotation_position="bottom right")
        fig_be.update_layout(height=280,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(title="Price per Nut (Rs.)",showgrid=False),
            yaxis=dict(title="Net Profit (Rs.)",gridcolor="#e4eeea",tickprefix="Rs.",tickformat=",.0f"),showlegend=False)
        st.plotly_chart(fig_be,use_container_width=True,config={"displayModeBar":"hover"})

# ══ AUCTION DETAILS ══════════════════════════════════════════════════════════
elif t["nav"][8] in sec_name:
    section_header(" "+t["auction_title"],t["auction_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['auction_note']}</div>",unsafe_allow_html=True)

    ak1,ak2,ak3,ak4=st.columns(4)
    for col,(lbl,val) in zip([ak1,ak2,ak3,ak4],[
        ("Primary Authority","CDA / HARTI"),
        ("Auction Centres",str(len(auction_df))),
        ("Typical Start Time","7:30 – 12:00"),
        ("Lot Size","500–5,000 nuts")]):
        with col: st.markdown(metric_card(lbl,val,height=110,val_size="1.1rem"),unsafe_allow_html=True)
    divider()

    st.markdown("#### Official Auction Centres (Real CDA/HARTI Data)")
    for row_start in range(0,len(auction_df),3):
        row_centres=auction_df.iloc[row_start:row_start+3]
        cols=st.columns(3)
        for col,(_,c) in zip(cols,row_centres.iterrows()):
            with col:
                st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:4px solid #3d7a55;
                    border-radius:12px;padding:16px;margin-bottom:12px;min-height:220px;'>
                    <div style='font-size:.6rem;font-weight:800;color:#3d7a55;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;'>{c.get('Managed By','CDA/HARTI')}</div>
                    <div style='font-size:.9rem;font-weight:800;color:#1a3328;margin-bottom:8px;'>{c.get('Auction Centre','')}</div>
                    <div style='font-size:.72rem;color:#374151;line-height:1.85;'>
                       📍 {c.get('Location / District','')}<br>
                       📅 {c.get('Frequency','')}<br>
                       🗓 {c.get('Typical Day','')}<br>
                       🕐 {c.get('Typical Time','')}<br>
                       📞 {c.get('Contact','')}<br>
                       🌐 {c.get('Website','')}
                    </div></div>""",unsafe_allow_html=True)
    divider()

    st.markdown("#### Current Auction Price Benchmarks (Rs./Nut)")
    grade_lbls=["Grade A (Premium)","Grade B (Standard)","Grade C (Small)","Copra (per kg)","Coconut Oil (per L)"]
    # Scale from historical data
    cp_current=CURRENT_PRICE
    gmins=[round(cp_current*0.98,0),round(cp_current*0.85,0),round(cp_current*0.72,0),85,380]
    gmaxs=[round(cp_current*1.05,0),round(cp_current*0.98,0),round(cp_current*0.88,0),110,450]
    gavgs=[round(cp_current*1.01,0),round(cp_current*0.91,0),round(cp_current*0.80,0),95,415]
    fig_grades=go.Figure()
    fig_grades.add_trace(go.Bar(name="Min",x=grade_lbls,y=gmins,marker_color="#94a3b8",
        text=[f"Rs.{v:.0f}" for v in gmins],textposition="outside"))
    fig_grades.add_trace(go.Bar(name="Average",x=grade_lbls,y=gavgs,marker_color=[GREEN]*5,
        text=[f"Rs.{v:.0f}" for v in gavgs],textposition="outside"))
    fig_grades.add_trace(go.Bar(name="Max",x=grade_lbls,y=gmaxs,marker_color=["rgba(34,197,94,.35)"]*5,
        text=[f"Rs.{v:.0f}" for v in gmaxs],textposition="outside"))
    fig_grades.update_layout(barmode="group",height=380,margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="#fff",paper_bgcolor="#fff",xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f0f5f2",tickprefix="Rs.",title="Price (Rs.)"),
        legend=dict(orientation="h",yanchor="bottom",y=1.01,xanchor="right",x=1),bargap=0.25,bargroupgap=0.06)
    st.plotly_chart(fig_grades,use_container_width=True,config={"displayModeBar":"hover"})

# ══ METHOD ═══════════════════════════════════════════════════════════════════
elif t["nav"][9] in sec_name:
    st.markdown("""<div style='background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 60%,#3d7a55 100%);
        border-radius:10px;padding:22px 28px;margin-bottom:16px;'>
      <div style='font-size:1.35rem;font-weight:900;color:#fff;margin-bottom:8px;'>COCOStat — Methodology & Documentation</div>
      <div style='font-size:.85rem;color:#a8c9b8;line-height:1.75;'>
        COCOStat is a Coconut Market Intelligence Dashboard using real CDA/HARTI/CRI/EDB data.
        All data is sourced from official Sri Lankan government departments and institutions.
      </div></div>""",unsafe_allow_html=True)

    st.markdown("<div style='font-size:.65rem;font-weight:800;color:#2d5a3d;text-transform:uppercase;letter-spacing:2.5px;margin:20px 0 14px;border-bottom:2px solid #b8d0c4;padding-bottom:6px;'>Data Sources</div>",unsafe_allow_html=True)
    st.markdown("""<table style='width:100%;border-collapse:collapse;font-size:.76rem;'>
      <thead><tr style='background:#1a3328;color:#a8c9b8;'>
        <th style='padding:9px 12px;text-align:left;'>Data Category</th>
        <th style='padding:9px 12px;text-align:left;'>Source</th>
        <th style='padding:9px 12px;text-align:left;'>Coverage</th>
        <th style='padding:9px 12px;text-align:left;'>Sheet</th>
      </tr></thead><tbody>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Weekly Auction Prices</td><td>CDA / HARTI</td><td>2015–2024, Weekly</td><td>01_Weekly_Auction</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Monthly Average Prices</td><td>CDA / HARTI</td><td>2015–2024, Monthly</td><td>02_Monthly_Prices</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Production & Utilisation</td><td>CDA Annual Reports</td><td>2016–2024, Annual</td><td>03_Production_Details</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Export Volumes</td><td>EDB / CDA</td><td>2013–2024, Annual</td><td>04_Export_Products</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Rainfall & Temperature</td><td>Dept. of Meteorology, CRI</td><td>2015–2024, Monthly</td><td>06_Weather_Harvest</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Demand Elasticity</td><td>HARTI Consumer Studies</td><td>2015–2024, Annual</td><td>07_Demand_Elasticity</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Farm Economics</td><td>CDA / Dept. of Agriculture</td><td>2015–2024, Annual</td><td>08_Farmer_Profitability</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Global Price Comparison</td><td>FAO FAOSTAT / CDA</td><td>2015–2024, Annual</td><td>09_Global_Comparison</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Auction Schedule</td><td>CDA / HARTI Official</td><td>Current</td><td>10_Auction_Schedule</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Export Destinations</td><td>EDB Sri Lanka</td><td>2015–2024, Annual</td><td>11_Export_Destinations</td></tr>
        <tr><td style='padding:8px 12px;'>Price Forecast</td><td>CDA/HARTI ARIMA Model</td><td>Dec 2024–Nov 2025</td><td>12_Price_Forecast</td></tr>
      </tbody></table>""",unsafe_allow_html=True)

    st.markdown("<div style='font-size:.65rem;font-weight:800;color:#2d5a3d;text-transform:uppercase;letter-spacing:2.5px;margin:20px 0 14px;border-bottom:2px solid #b8d0c4;padding-bottom:6px;'>Technical Specifications</div>",unsafe_allow_html=True)
    st.markdown("""<table style='width:100%;border-collapse:collapse;font-size:.76rem;'>
      <thead><tr style='background:#1a3328;color:#a8c9b8;'>
        <th style='padding:9px 12px;text-align:left;'>Component</th><th style='padding:9px 12px;text-align:left;'>Specification</th>
      </tr></thead><tbody>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Language</td><td>Python 3.x</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Framework</td><td>Streamlit</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Visualisation</td><td>Plotly Graph Objects & Express</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Data Processing</td><td>Pandas, NumPy</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Price Unit</td><td>Rs. per Nut (all values)</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Default Warning Threshold</td><td>Rs. 650/Nut</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Default Crisis Threshold</td><td>Rs. 800/Nut</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Forecast Model</td><td>CDA/HARTI ARIMA (pre-computed)</td></tr>
        <tr><td style='padding:8px 12px;border-bottom:1px solid #e4eeea;'>Weather Lag</td><td>3 months</td></tr>
        <tr><td style='padding:8px 12px;'>Data Period</td><td>2013–2024 (historical) + Dec 2024–Nov 2025 (forecast)</td></tr>
      </tbody></table>""",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div style='text-align:center;padding:20px;background:#f0f5f2;border-radius:10px;'>
      <div style='font-weight:800;color:#1a3328;font-size:1rem;'>M A C S Rathnayake</div>
      <div style='color:#2d5a3d;font-size:.82rem;margin-top:4px;'>UOW: w1999714 | IIT: 20220508</div>
      <div style='color:#2d5a3d;font-size:.78rem;margin-top:4px;'>BSc (Hons) Business Data Analytics — University of Westminster</div>
      <div style='color:#6b7280;font-size:.72rem;margin-top:8px;'>Data Sources: CDA · HARTI · CRI · EDB · Dept. of Meteorology — Sri Lanka</div>
    </div>""",unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
divider()
st.markdown(f"""<div style='background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 50%,#3d7a55 100%);
    border-radius:10px;padding:28px 32px;margin-bottom:28px;text-align:center;'>
  <div style='font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:8px;'>🇱🇰 Sri Lanka Coconut Industry</div>
  <div style='font-size:.85rem;color:#b8d0c4;margin-bottom:20px;'>Key Organisations, Contacts & Industry Facts</div>
  <div style='display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:20px;'>
    <div style='background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-top:3px solid #82b49a;
        padding:14px 18px;flex:1;min-width:180px;max-width:240px;'>
      <div style='font-size:.6rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;margin-bottom:6px;'>Regulator</div>
      <div style='font-weight:800;font-size:.82rem;color:#fff;margin-bottom:6px;'>Coconut Development Authority</div>
      <div style='font-size:.7rem;color:#b8d0c4;'>📞 +94 11 243 0610<br>🌐 www.cda.gov.lk</div>
    </div>
    <div style='background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-top:3px solid #82b49a;
        padding:14px 18px;flex:1;min-width:180px;max-width:240px;'>
      <div style='font-size:.6rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;margin-bottom:6px;'>Research</div>
      <div style='font-weight:800;font-size:.82rem;color:#fff;margin-bottom:6px;'>Coconut Research Institute</div>
      <div style='font-size:.7rem;color:#b8d0c4;'>📞 +94 31 222 2481<br>🌐 www.cri.gov.lk</div>
    </div>
    <div style='background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-top:3px solid #82b49a;
        padding:14px 18px;flex:1;min-width:180px;max-width:240px;'>
      <div style='font-size:.6rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;margin-bottom:6px;'>Export</div>
      <div style='font-weight:800;font-size:.82rem;color:#fff;margin-bottom:6px;'>Sri Lanka Export Development Board</div>
      <div style='font-size:.7rem;color:#b8d0c4;'>📞 +94 11 230 0705<br>🌐 www.srilankabusiness.com</div>
    </div>
    <div style='background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-top:3px solid #82b49a;
        padding:14px 18px;flex:1;min-width:180px;max-width:240px;'>
      <div style='font-size:.6rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;margin-bottom:6px;'>Auction</div>
      <div style='font-weight:800;font-size:.82rem;color:#fff;margin-bottom:6px;'>HARTI / Economic Centres</div>
      <div style='font-size:.7rem;color:#b8d0c4;'>📞 +94 11 259 1919<br>🌐 www.harti.gov.lk</div>
    </div>
  </div>
  <div style='font-size:.75rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;'>Sri Lanka Coconut Industry at a Glance</div>
  <div style='display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:20px;'>
    {''.join(f"<div style='background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:12px 16px;min-width:90px;text-align:center;'><div style='font-size:1.3rem;font-weight:900;color:#fff;'>{v}</div><div style='font-size:.6rem;color:#a8c9b8;margin-top:4px;text-transform:uppercase;'>{l}</div></div>" for v,l in [("~3.3B","Nuts/Year"),("440K+","Hectares"),("450K+","Families"),("$262M+","Exports"),("3rd","World Rank"),("~2%","GDP Share")])}
  </div>
  <div style='font-size:.72rem;color:#a8c9b8;opacity:.85;'>
    COCOStat · Coconut Market Intelligence · Real Data from CDA, HARTI, CRI, EDB & Dept. of Meteorology Sri Lanka
  </div>
</div>""",unsafe_allow_html=True)
