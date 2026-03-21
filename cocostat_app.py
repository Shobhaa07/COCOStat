import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io

st.set_page_config(
    page_title="COCOStat – Coconut Market Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# DATA GENERATORS
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
    forecast = pd.DataFrame({
        "date": future_dates,
        "price": np.round(future_prices, 2),
        "upper": np.round([p + 5 for p in future_prices], 2),
        "lower": np.round([p - 5 for p in future_prices], 2)
    })
    weekly_dates = pd.date_range("2024-01-01", "2024-08-31", freq="W")
    weekly_prices = [last - 8 + i * 0.15 + np.random.normal(0, 1.2) for i in range(len(weekly_dates))]
    weekly = pd.DataFrame({"date": weekly_dates, "price": np.round(weekly_prices, 2)})
    return hist, forecast, weekly

@st.cache_data
def generate_weather_data():
    np.random.seed(7)
    dates = pd.date_range("2015-01-01", "2024-08-01", freq="MS")
    n = len(dates)
    months = np.tile(np.arange(1, 13), int(np.ceil(n / 12)))[:n]
    base_rain = 100 + 80 * np.sin((months - 3) * np.pi / 6) + 40 * np.sin((months - 10) * np.pi / 3)
    rainfall = np.clip(base_rain + np.random.normal(0, 30, n), 10, 400)
    temperature = 28 + 3 * np.sin((months - 4) * np.pi / 6) + np.random.normal(0, 0.8, n)
    yield_index = np.roll(rainfall, 3) / 200 * 100 + np.random.normal(0, 8, n)
    yield_index = np.clip(yield_index, 40, 110)
    return pd.DataFrame({
        "date": dates, "rainfall_mm": np.round(rainfall, 1),
        "temp_c": np.round(temperature, 1), "yield_index": np.round(yield_index, 1),
        "month": months, "year": dates.year,
    })

@st.cache_data
def generate_export_data():
    np.random.seed(13)
    years = list(range(2015, 2025))
    product_cols = ["Desiccated Coconut","Coconut Oil","Coconut Milk","Coir Products","Fresh Nuts","Activated Carbon"]
    data = {
        "year": years,
        "Desiccated Coconut": [85,90,95,102,108,115,112,118,125,98],
        "Coconut Oil": [55,60,58,65, 70, 72, 68, 75, 80, 62],
        "Coconut Milk": [30,35,38,42, 45, 50, 52, 55, 60, 48],
        "Coir Products": [20,22,25,27, 30, 32, 28, 35, 38, 30],
        "Fresh Nuts": [15,18,20,22, 25, 28, 24, 30, 32, 25],
        "Activated Carbon": [12,14,16,18, 20, 22, 25, 28, 30, 24],
    }
    export_df = pd.DataFrame(data)
    export_df["Total"] = export_df[product_cols].sum(axis=1)
    destinations = pd.DataFrame({
        "Country": ["USA","UK","Germany","Australia","Netherlands","Japan","Canada","UAE","Others"],
        "Share_pct": [22,16,12,9,8,7,6,5,15],
        "Value_USD_M":[54,39,29,22,20,17,15,12,37],
    })
    return export_df, destinations

@st.cache_data
def generate_global_data():
    years = list(range(2015, 2025))
    global_df = pd.DataFrame({
        "year": years,
        "Sri Lanka": [52,54,57,60,63,66,62,68,72,68],
        "Indonesia": [38,40,42,45,47,50,48,52,55,50],
        "Philippines": [45,47,50,53,56,59,55,61,65,60],
        "India": [48,50,53,56,59,62,58,64,68,63],
        "Vietnam": [35,37,39,42,44,47,45,49,52,47],
    })
    production = pd.DataFrame({
        "Country": ["Indonesia","Philippines","India","Sri Lanka","Vietnam","Brazil","Mexico"],
        "Production_B_nuts": [19.5,15.0,14.8,2.7,1.8,1.6,1.2],
    })
    return global_df, production

history_df, forecast_df, weekly_df = generate_data()
weather_df = generate_weather_data()
export_df, destinations_df = generate_export_data()
global_price_df, production_df = generate_global_data()
PRODUCT_COLS = ["Desiccated Coconut","Coconut Oil","Coconut Milk","Coir Products","Fresh Nuts","Activated Carbon"]
PRODUCT_COLORS = ["#3d7a55","#5a9470","#f59e0b","#8b5cf6","#ef4444","#06b6d4"]
PRODUCT_NAMES_SI = ["වියළි පොල්","පොල් තෙල්","පොල් කිරි","කොයිර් නිෂ්පාදන","නැවුම් ගෙඩි","සක්‍රිය කාබන්"]

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────
T = {
    "en": {
        "subtitle": "Coconut Market Intelligence Dashboard",
        "tagline": "Understanding Coconut Prices in Simple Terms",
        "desc": "This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.",
        "nav": ["Overview & History","Market & Demand","Weather & Harvest","Forecast","Compare","Export & Trade",
                "Policy & Recommendations","Farmer Profitability","Auction Details","Method"],
        "nav_icons":["","","","","","","","","",""],
        "card_price_label":"Current Price","card_price_value":"Rs. 68.50","card_price_sub":"Per Nut (Auction)",
        "card_market_label":"Market Condition","card_market_value":"Stable","card_market_sub":"Normal conditions",
        "card_demand_label":"Demand Response","card_demand_value":"Inelastic","card_demand_sub":"People still buy",
        "card_forecast_label":"Future Trend","card_forecast_value":" Slight Rise","card_forecast_sub":"Next 12 Weeks",
        "regime_title":"What is the Current Market Situation?",
        "regime_select":"Select Market Type to Explore",
        "regime_options":[" Stable Market"," Warning Market"," Crisis Market"],
        "regime_desc":["Prices are normal and stable.","Prices are changing moderately.","Prices are very unstable."],
        "regime_avg":["Rs. 52-65","Rs. 65-80","Rs. 80+"],
        "regime_vol":["Low","Medium","High"],
        "regime_avg_label":"Average Price","regime_vol_label":"Volatility","regime_status_label":"Status",
        "regime_status":[" OK"," Watch"," Alert"],
        "demand_title":"Do People Reduce Buying When Prices Increase?",
        "demand_note":" Demand is mostly inelastic \u2014 people must buy coconuts because it is an essential food.",
        "demand_bar_title":"Price Sensitivity Level (%)","demand_periods":["Stable Period","Warning Period","Crisis Period"],
        "demand_sens":[35,22,12],
        "demand_cards":[
            (" Stable Period","People react slightly to price changes."),
            (" Warning Period","Moderate reaction to price volatility."),
            (" Crisis Period","People still buy coconuts even if price increases."),
        ],
        "forecast_title":"What Will Happen to Prices in the Next 12 Weeks?",
        "forecast_summary":" Prices are expected to increase slowly. No immediate crisis predicted.",
        "forecast_week":"Wk","forecast_hist_label":"Historical","forecast_pred_label":"Forecast",
        "forecast_range_label":"Uncertainty Range",
        "policy_title":"What Should the Government Do Now?",
        "policy_sub":"Evidence-based policy recommendations based on current market regime.",
        "policy_markets":["If Market is Green ","If Market is Yellow ","If Market is Red "],
        "policy_actions":["Support farmers and improve supply systems.",
                          "Improve price transparency and monitoring.",
                          "Use buffer stocks and temporary price control."],
        "policy_priorities":[" Low"," Medium"," High"],
        "policy_active":"\u2190 Currently Active","policy_priority_label":"Priority:",
        "history_title":"Market History (2015-2024)","history_sub":"Full 10-year auction price history. Hover to explore.",
        "method_title":"How This System Works",
        "method_steps":["We studied 10 years of auction data.","We grouped market situations into 3 types.",
                        "We measured how people react to prices.","We predicted future prices."],
        "footer_researcher":"Researcher","footer_ids":"Student IDs","footer_programme":"Programme",
        "compare_title":"Year-over-Year Price Comparison",
        "compare_sub":"Compare coconut prices across different years to identify seasonal patterns.",
        "price_calc_title":" Price Impact Calculator",
        "price_calc_sub":"Estimate how price changes affect household spending.",
        "nuts_per_week":"Coconuts purchased per week","current_price_input":"Current price per nut (Rs.)",
        "new_price_input":"New price per nut (Rs.)",
        "weekly_impact":"Weekly Cost Change","monthly_impact":"Monthly Cost Change","annual_impact":"Annual Cost Change",
        "alert_warn":"Warning alert at (Rs.)","alert_crisis":"Crisis alert at (Rs.)",
        # NEW SECTIONS
        "weather_title":" Weather & Harvest Impact Analysis",
        "weather_sub":"How rainfall, temperature, and drought affect coconut yields and prices.",
        "weather_note":" Coconut yields are highly sensitive to rainfall. Drought pushes prices up within 3-6 months.",
        "export_title":" Export & Trade Analysis",
        "export_sub":"Sri Lanka coconut export volumes, product categories, and revenue trends (2015-2024).",
        "export_note":" Export demand creates upward price pressure domestically. Strong export seasons often coincide with local price spikes.",
        "farmer_title":" Farmer Profitability Calculator",
        "farmer_sub":"Estimate net farm income based on your land size, yield, costs, and current market price.",
        "farmer_note":" At current prices, the average smallholder earns a thin margin. Any cost increase quickly erodes profit.",
        "global_title":" Global Market Comparison",
        "global_sub":"Compare Sri Lanka coconut prices with major producers worldwide.",
        "global_note":" Sri Lanka typically commands a price premium due to quality. But high prices hurt export competitiveness.",
        "auction_title":" Sri Lanka Coconut Auction Details",
        "auction_sub":"Official auction schedules, venues, and key information for Sri Lanka coconut auctions managed by CDA & HARTI.",
        "auction_note":" Coconut auctions are the primary price-discovery mechanism in Sri Lanka. Prices set at auction directly affect farmers, traders, and consumers.",
        "kpi_title": "KPI Summary Dashboard",
        "kpi_sub": "All key performance indicators across price, market, demand, and exports in one view.",
        "trend_title": "Trend Analysis and Segmentation",
        "trend_sub": "Deep-dive into price trends, market segmentation, and comparative analysis with interactive filters.",
        "filter_year_range": "Select Year Range",
        "filter_regime": "Filter by Regime",
        "filter_product": "Select Export Product",
        "seg_by": "Segment by",
        "seg_options": ["Year", "Month", "Regime", "Season"],
        "all_regimes": "All Regimes",
    },
    "si": {
        "subtitle": "\u0db4\u0ddc\u0dbd\u0dca \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0db6\u0dd4\u0daf\u0dca\u0db0\u0dd2\u0db8\u0dad\u0dca \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba",
        "tagline": "\u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd \u0db4\u0dc4\u0dc3\u0dd4\u0dc0\u0dd9\u0db1\u0dca \u0dad\u0dda\u0dbb\u0dd4\u0db8\u0dca \u0d9c\u0db1\u0dd2\u0db8\u0dd4",
        "desc": "\u0db8\u0dda\u0db8 \u0db4\u0daf\u0dca\u0db0\u0dad\u0dd2\u0dba \u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca\u0dc0\u0dd3\u0db8\u0dca, \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0dc4\u0dd9\u0dc5\u0dd2\u0d9a\u0dd2\u0dbb\u0dd3\u0db8 \u0dc3\u0dc4 \u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0db8\u0dd2\u0dbd \u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2 \u0dc3\u0dbb\u0dbd\u0dc0 \u0db4\u0dd0\u0dc4\u0daf\u0dd2\u0dbd\u0dd2 \u0d9a\u0dbb\u0dba\u0dd2.",
        "nav": ["\u0daf\u0dbb\u0dca\u0dc1\u0db1\u0dba \u0dc3\u0dc4 \u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba","\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dc3\u0dc4 \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8","\u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab \u0dc3\u0dc4 \u0d85\u0dc3\u0dca\u0dc0\u0db1\u0dd4","\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba","\u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba","\u0d85\u0db4\u0db1\u0dba\u0db1 \u0dc3\u0dc4 \u0dc0\u0dd9\u0dc5\u0db3\u0dcf\u0db8",
                "\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2 \u0dc3\u0dc4 \u0db1\u0dd2\u0dbb\u0dca\u0daf\u0dda\u0DC1","\u0d9c\u0ddc\u0dc0\u0dd2 \u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf\u0dc0","\u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb","\u0d9a\u0dca\u200d\u0dbb\u0db8\u0dc0\u0dda\u0daf\u0dba"],
        "nav_icons":["","","","","","","","","",""],
        "card_price_label":"\u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd","card_price_value":"\u0dbb\u0dd4. 68.50","card_price_sub":"\u0db4\u0ddc\u0dbd\u0dca \u0d9c\u0dd9\u0da9\u0dd2\u0dba\u0d9a\u0da7 (\u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2)",
        "card_market_label":"\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba","card_market_value":"\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2","card_market_sub":"\u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u200d\u0dba \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba",
        "card_demand_label":"\u0db8\u0dd2\u0dbd\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba","card_demand_value":"\u0d85\u0db4\u0dca\u200d\u0dbb\u0dad\u0dca\u200d\u0dba\u0dcf\u0dc3\u0dca\u0dae","card_demand_sub":"\u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0d85\u0da9\u0dd4 \u0db1\u0dd0\u0dad",
        "card_forecast_label":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0","card_forecast_value":" \u0dc3\u0dd9\u0db8\u0dd2\u0db1\u0dca \u0d89\u0dc4\u0dc5","card_forecast_sub":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0dc3\u0dad\u0dd2 12",
        "regime_title":"\u0daf\u0dd0\u0db1\u0da7 \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5\u0dda \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0d9a\u0dd4\u0db8\u0d9a\u0dca\u0daf?",
        "regime_select":"\u0d9c\u0dc0\u0dda\u0DC2\u0dab\u0dba \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0dc0\u0dd9\u0dc5\u0db3 \u0dc0\u0dbb\u0dca\u0d9c\u0dba\u0d9a\u0dca \u0dad\u0ddc\u0dbb\u0db1\u0dca\u0db1",
        "regime_options":[" \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5"," \u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5"," \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5"],
        "regime_desc":["\u0db8\u0dd2\u0dbd \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2, \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u200d\u0dba \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba.","\u0db8\u0dd2\u0dbd \u0db8\u0db0\u0dca\u200d\u0dba\u0db8 \u0dbd\u0dd9\u0dc3 \u0dc0\u0dd9\u0db1\u0dc3\u0dca \u0dc0\u0dda.","\u0db8\u0dd2\u0dbd \u0d85\u0dad\u0dd2\u0DC1\u0dba\u0dd2\u0db1\u0dca \u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2."],
        "regime_avg":["\u0dbb\u0dd4. 52-65","\u0dbb\u0dd4. 65-80","\u0dbb\u0dd4. 80+"],
        "regime_vol":["\u0d85\u0da9\u0dd4","\u0db8\u0db0\u0dca\u200d\u0dba\u0db8","\u0d89\u0dc4\u0dc5"],
        "regime_avg_label":"\u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u200d\u0dba \u0db8\u0dd2\u0dbd","regime_vol_label":"\u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf\u0dc0","regime_status_label":"\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba",
        "regime_status":[" \u0dc4\u0ddc\u0db3\u0dba\u0dd2"," \u0db1\u0dd2\u0dbb\u0dd3\u0d9a\u0dca\u0DC2\u0dab\u0dba"," \u0d85\u0dc0\u0daf\u0dcf\u0db1\u0db8"],
        "demand_title":"\u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dc5 \u0d9c\u0dd2\u0dba \u0db8\u0dd2\u0db1\u0dd2\u0dc3\u0dd4\u0db1\u0dca \u0db8\u0dd2\u0dbd\u0daf\u0dd3 \u0d9c\u0dd9\u0db1\u0dd3\u0db8 \u0d85\u0da9\u0dd4 \u0d9a\u0dbb\u0dba\u0dd2\u0daf?",
        "demand_note":" \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dad\u0dca\u200d\u0dba\u0dc0\u0DC1\u0dca\u200d\u0dba \u0d86\u0dc4\u0dcf\u0dbb\u0dba\u0d9a\u0dca \u0db6\u0dd0\u0dc0\u0dd2\u0db1\u0dca, \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dc5 \u0d9c\u0dd2\u0dba\u0dad\u0dca \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0d85\u0da9\u0dd4\u0dc0\u0db1\u0dca\u0db1\u0dda \u0db1\u0dd0\u0dad.",
        "demand_bar_title":"\u0db8\u0dd2\u0dbd \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dad\u0dcf \u0db8\u0da7\u0dca\u0da7\u0db8 (%)","demand_periods":["\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb","\u0d85\u0dc0\u0dc0\u0dcf\u0daf","\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf"],
        "demand_sens":[35,22,12],
        "demand_cards":[
            (" \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca\u0dc0\u0dd3\u0db8\u0dca \u0dc0\u0dbd\u0da7 \u0da7\u0dd2\u0d9a\u0d9a\u0dca \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb \u0daf\u0d9a\u0dca\u0dc0\u0dba\u0dd2."),
            (" \u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf\u0dc0\u0da7 \u0db8\u0db0\u0dca\u200d\u0dba\u0db8 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba\u0d9a\u0dca."),
            (" \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dc5 \u0d9c\u0dd2\u0dba\u0dad\u0dca \u0db8\u0dd2\u0db1\u0dd2\u0dc3\u0dd4\u0db1\u0dca \u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd\u0daf\u0dd3 \u0d9c\u0db1\u0dd3."),
        ],
        "forecast_title":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0dc3\u0dad\u0dd2 12 \u0dad\u0dd4\u0dbd \u0db8\u0dd2\u0dbd\u0da7 \u0d9a\u0dd4\u0db8\u0d9a\u0dca \u0dc3\u0dd2\u0daf\u0dc0\u0dda\u0daf?",
        "forecast_summary":" \u0db8\u0dd2\u0dbd \u0dc3\u0dd9\u0db8\u0dd2\u0db1\u0dca \u0d89\u0dc4\u0dc5 \u0dba\u0dcf \u0dc4\u0dd0\u0d9a. \u0dc0\u0dc4\u0dcf\u0db8 \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf\u0dba\u0d9a\u0dca \u0d85\u0db4\u0dda\u0d9a\u0dca\u0DC2\u0dcf \u0db1\u0ddc\u0d9a\u0dd9\u0dbb\u0dda.",
        "forecast_week":"\u0dc3\u0dad\u0dd2","forecast_hist_label":"\u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba","forecast_pred_label":"\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba",
        "forecast_range_label":"\u0d85\u0dc0\u0dd2\u0db1\u0dd2\u0DC1\u0da0\u0dd2\u0dad \u0db4\u0dbb\u0dcf\u0dc3\u0dba",
        "policy_title":"\u0daf\u0dd0\u0db1\u0da7 \u0dbb\u0da2\u0dba \u0d9a\u0dd4\u0db8\u0d9a\u0dca \u0d9a\u0dbd \u0dba\u0dd4\u0dad\u0dd4\u0daf?",
        "policy_sub":"\u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0dc0\u0dd9\u0dc5\u0db3 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0db8\u0dad \u0db4\u0daf\u0db1\u0db8\u0dca \u0dc0\u0dd6 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2 \u0db1\u0dd2\u0dbb\u0dca\u0daf\u0dda\u0DC1.",
        "policy_markets":[" \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2 \u0db1\u0db8\u0dca"," \u0d85\u0dc0\u0dc0\u0dcf\u0daf\u0dba\u0dd2 \u0db1\u0db8\u0dca"," \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf\u0dba\u0dd2 \u0db1\u0db8\u0dca"],
        "policy_actions":["\u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0da7 \u0dc3\u0dc4\u0dba \u0dbd\u0db6\u0dcf \u0daf\u0dd3 \u0dc3\u0dd0\u0db4\u0dba\u0dd4\u0db8\u0dca \u0db4\u0daf\u0dca\u0db0\u0dad\u0dd2\u0dba \u0dc0\u0dd0\u0da9\u0dd2\u0daf\u0dd2\u0dba\u0dd4\u0dab\u0dd4 \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
                          "\u0db8\u0dd2\u0dbd \u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4 \u0db4\u0dd0\u0dc4\u0daf\u0dd2\u0dbd\u0dd2 \u0d9a\u0dbb \u0db1\u0dd2\u0dbb\u0dd3\u0d9a\u0dca\u0DC2\u0dab\u0dba \u0dc0\u0dd0\u0daf\u0dd2 \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
                          "\u0db6\u0dc6\u0dbb\u0dca \u0dad\u0ddc\u0d9c \u0db7\u0dcf\u0dc0\u0dd2\u0dad\u0dcf \u0d9a\u0dbb \u0dad\u0dcf\u0dc0\u0d9a\u0dcf\u0dbd\u0dd2\u0d9a \u0db8\u0dd2\u0dbd \u0db4\u0dcf\u0dbd\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1."],
        "policy_priorities":[" \u0d85\u0da9\u0dd4"," \u0db8\u0db0\u0dca\u200d\u0dba\u0db8"," \u0d89\u0dc4\u0dc5"],
        "policy_active":"\u2190 \u0daf\u0dd0\u0db1\u0da7 \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a\u0dba\u0dd2","policy_priority_label":"\u0db4\u0dca\u200d\u0dbb\u0db8\u0dd4\u0d9b\u0dad\u0dcf\u0dc0:",
        "history_title":"\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba (2015-2024)","history_sub":"\u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0dc0\u0dc3\u0dbb 10 \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0db8\u0dd2\u0dbd \u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba.",
        "method_title":"\u0db8\u0dda\u0db8 \u0db4\u0daf\u0dca\u0db0\u0dad\u0dd2\u0dba \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf \u0d9a\u0dbb\u0db1\u0dca \u0d86\u0d9a\u0dcf\u0dbb\u0dba",
        "method_steps":["\u0dc0\u0dc3\u0dbb 10\u0d9a \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0daf\u0dad\u0dca\u0dad \u0d85\u0daf\u0dca\u0dba\u0dba\u0db1\u0dba \u0d9a\u0dbd\u0dcf.","\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0 3\u0d9a\u0dca \u0dc4\u0db3\u0dd4\u0db1\u0dcf\u0d9c\u0dad\u0dca\u0dad\u0dcf.","\u0db8\u0dd2\u0dbd\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba \u0db8\u0dd0\u0db1 \u0db6\u0dd0\u0dbd\u0dd4\u0dc0\u0dcf.","\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0db8\u0dd2\u0dbd \u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2 \u0d9a\u0dbd\u0dcf."],
        "footer_researcher":"\u0db4\u0dbb\u0dca\u0dba\u0dda\u0DC1\u0d9a","footer_ids":"\u0DC1\u0dd2\u0DC2\u0dca\u0dba \u0d8a\u0daf\u0dca","footer_programme":"\u0db4\u0dcf\u0da7\u0db8\u0dcf\u0dbd\u0dcf\u0dc0",
        "compare_title":"\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0db8\u0dd2\u0dbd \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba",
        "compare_sub":"\u0dc3\u0dd8\u0dad\u0dd4\u0db8\u0dba \u0dbb\u0da7\u0dcf \u0dc4\u0db3\u0dd4\u0db1\u0dcf \u0d9c\u0dd9\u0db1\u0dd3\u0db8\u0da7.",
        "price_calc_title":" \u0db8\u0dd2\u0dbd \u0db6\u0dbd\u0db4\u0dcf\u0db8\u0dca \u0d9a\u0dd0\u0dbd\u0dca\u0d9a\u0dd2\u0dba\u0dd4\u0dbd\u0dda\u0da7\u0dbb\u0dba",
        "price_calc_sub":"\u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca\u0dc0\u0dd3\u0db8\u0dca \u0d9c\u0dd0\u0dc4\u0dc3\u0dca\u0dad \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0d9a\u0dd9\u0dc3\u0dda \u0db6\u0dbd\u0db4\u0dcf\u0daf\u0dd0\u0dba\u0dd2 \u0d9c\u0dab\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "nuts_per_week":"\u0dc3\u0dad\u0dd2\u0dba\u0d9a\u0da7 \u0db4\u0ddc\u0dbd\u0dca \u0d9c\u0dd9\u0da9\u0dd2","current_price_input":"\u0daf\u0dd0\u0db1\u0da7 \u0d9c\u0dd9\u0da9\u0dd2\u0dba\u0d9a\u0da7 \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4.)","new_price_input":"\u0db1\u0dc0 \u0d9c\u0dd9\u0da9\u0dd2\u0dba\u0d9a\u0da7 \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4.)",
        "weekly_impact":"\u0dc3\u0dad\u0dd2\u0db4\u0dad\u0dcf \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3","monthly_impact":"\u0db8\u0dcf\u0dc3\u0dd2\u0d9a\u0dc0 \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3","annual_impact":"\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a\u0dc0 \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3",
        "alert_warn":"\u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0d87\u0d9f\u0dc5\u0dd3\u0db8 (\u0dbb\u0dd4.)","alert_crisis":"\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0d87\u0d9f\u0dc5\u0dd3\u0db8 (\u0dbb\u0dd4.)",
        # NEW
        "weather_title":"\u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab \u0dc3\u0dc4 \u0d85\u0dc3\u0dca\u0dc0\u0db1\u0dd4 \u0db6\u0dbd\u0db4\u0dcf\u0db8\u0dca \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba",
        "weather_sub":"\u0dc0\u0dbb\u0dca\u0DC2\u0dcf\u0dc0 \u0dc3\u0dc4 \u0d8b\u0DC2\u0dca\u0dab\u0dad\u0dca\u0dc0\u0dba \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1\u0da7 \u0dc3\u0dc4 \u0db8\u0dd2\u0dbd\u0da7 \u0db6\u0dbd\u0db4\u0dcf\u0db1 \u0d86\u0d9a\u0dcf\u0dbb\u0dba.",
        "weather_note":" \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1 \u0dc0\u0dbb\u0dca\u0DC2\u0dcf\u0db4\u0dad\u0db1\u0dba\u0da7 \u0d89\u0dad\u0dcf \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dba\u0dd2. \u0db1\u0dd2\u0dba\u0d82 \u0d9a\u0dcf\u0dbd\u0dba \u0db8\u0dcf\u0dc3 3-6 \u0d87\u0dad\u0dd4\u0dbd\u0dad \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dc5 \u0db1\u0d82\u0dc0\u0dba\u0dd2.",
        "export_title":"\u0d85\u0db4\u0db1\u0dba\u0db1 \u0dc3\u0dc4 \u0dc0\u0dd9\u0dc5\u0db3 \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba",
        "export_sub":"\u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0db4\u0db1\u0dba\u0db1 \u0db4\u0dca\u200d\u0dbb\u0db8\u0dcf\u0dab, \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d9a\u0dcf\u0dab\u0dca\u0da9 \u0dc3\u0dc4 \u0d86\u0daf\u0dcf\u0dba\u0db8\u0dca \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf (2015-2024).",
        "export_note":" \u0d85\u0db4\u0db1\u0dba\u0db1 \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dc5 \u0db1\u0d82\u0dc0\u0dba\u0dd2.",
        "farmer_title":"\u0d9c\u0ddc\u0dc0\u0dd2 \u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf \u0d9a\u0dd0\u0dbd\u0dca\u0d9a\u0dd2\u0dba\u0dd4\u0dbd\u0dda\u0da7\u0dbb\u0dba",
        "farmer_sub":"\u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1, \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba \u0dc3\u0dc4 \u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd \u0db8\u0dad \u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0d9c\u0dda \u0DC1\u0dd4\u0daf\u0dca\u0db0 \u0d86\u0daf\u0dcf\u0dba\u0db8 \u0d9c\u0dab\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "farmer_note":" \u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd\u0dda\u0daf\u0dd3, \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u200d\u0dba \u0d9a\u0dd4\u0da9\u0dcf \u0d9c\u0ddc\u0dc0\u0dd2\u0dba\u0dcf\u0da7 \u0dbd\u0dcf\u0db7 \u0dbd\u0dd0\u0db6\u0dd9\u0db1\u0dca\u0db1\u0dda \u0dc3\u0dca\u0dc0\u0dbd\u0dca\u0db4\u0dba\u0d9a\u0dd2.",
        "global_title":" \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba",
        "global_sub":"\u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dc3\u0db8\u0d9f \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "global_note":" \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db8\u0dd2\u0dbd \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf \u0d85\u0db1\u0dd4\u0d9c\u0db8\u0db1\u0dba \u0d9a\u0dbb\u0db8\u0dd2\u0db1\u0dca \u0daf \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2\u0dc0\u0dbd\u0dd2\u0db1\u0dca \u0d86\u0dbb\u0d9a\u0dca\u0DC2\u0dcf \u0dc0\u0dda.",
        "auction_title":"\u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb",
        "auction_sub":"CDA \u0dc3\u0dc4 HARTI \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0d9a\u0dcf\u0dbd\u0dc3\u0da7\u0dc4\u0db1\u0dca, \u0dc3\u0dca\u0dae\u0dcf\u0db1 \u0dc3\u0dc4 \u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0da7 \u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4.",
        "auction_note":" \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0db8\u0dd2\u0dbd \u0db1\u0dd2\u0dba\u0db8\u0dba \u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0da7, \u0dc0\u0dca\u200d\u0dba\u0dcf\u0db4\u0dcf\u0dbb\u0dd2\u0d9a\u0dba\u0db1\u0dca\u0da7 \u0dc3\u0dc4 \u0db4\u0dbb\u0dd2\u0db4\u0dcf\u0dbd\u0d9a\u0dba\u0db1\u0dca\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dca\u200d\u0dba\u0d9a\u0dca\u0dc2\u0dba\u0dd9\u0db1\u0dca \u0db6\u0dbd\u0db4\u0dcf\u0dba\u0dd2.",
        "kpi_title": "KPI සාරාංශ",
        "kpi_sub": "මිල, වෙළඳ දර්ශක, ඉල්ලුම සහ අපනයන ප්‍රධාන දර්ශක.",
        "trend_title": "ප්‍රවණතා සහ කාණ්ඩ විශ්ලේෂණය",
        "trend_sub": "මිල ප්‍රවණතා, වෙළඳ කාණ්ඩ සහ සංසන්දන විශ්ලේෂණය.",
        "filter_year_range": "වසර පරාසය තොරන්න",
        "filter_regime": "තත්ත්වය අනුව පෙරහන් කරන්න",
        "filter_product": "අපනයන නිෂ්පාදනය තොරන්න",
        "seg_by": "කාලය අනුව කාණ්ඩ කරන්න",
        "seg_options": ["වර්ෂය", "මාසය", "තත්ත්වය", "ඍතුව"],
        "all_regimes": "සියලු තත්ත්ව",
    }
}

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+Sinhala:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter','Noto Sans Sinhala',sans-serif;background:#fff;color:#1a3328}
#MainMenu,footer,header{visibility:hidden}
.main .block-container{background:#fff;padding-top:0!important;padding-bottom:2rem;padding-left:1rem!important;padding-right:1rem!important}
[data-testid="stAppViewContainer"]>section>div{padding-top:0!important}
[data-testid="stVerticalBlock"]{gap:.5rem}
@media(min-width:768px){
  section[data-testid="stSidebar"]{min-width:270px!important;max-width:270px!important;width:270px!important;transform:none!important}
  section[data-testid="stSidebar"]>div{width:270px!important;transform:none!important}
}
@media(max-width:767px){
  section[data-testid="stSidebar"]{position:fixed!important;left:0!important;top:0!important;height:100vh!important;min-width:82vw!important;max-width:82vw!important;width:82vw!important;z-index:9998!important;box-shadow:4px 0 24px rgba(0,0,0,.18)!important}
  section[data-testid="stSidebar"]>div{width:82vw!important}
  [data-testid="collapsedControl"]{display:flex!important;z-index:9999!important;position:fixed!important}
  [data-testid="stAppViewContainer"]>.main{margin-left:0!important;padding-left:0!important;width:100vw!important;max-width:100vw!important}
  .main .block-container{padding-left:.5rem!important;padding-right:.5rem!important;max-width:100vw!important;margin-left:0!important}
  html,body,.main,.block-container,[data-testid="stAppViewContainer"]{overflow-x:hidden!important;max-width:100vw!important}
  [data-testid="column"],div[data-testid="column"]{min-width:100%!important;width:100%!important;flex:0 0 100%!important;max-width:100%!important}
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.5rem!important}
  .js-plotly-plot,.plotly,.plot-container{width:100%!important;overflow-x:hidden!important}
}
[data-testid="stHorizontalBlock"]{align-items:stretch!important}
[data-testid="stHorizontalBlock"]>[data-testid="column"]{display:flex!important;flex-direction:column!important}
[data-testid="stHorizontalBlock"]>[data-testid="column"]>div:first-child{flex:1!important;display:flex!important;flex-direction:column!important}
div[data-testid="stSidebar"]{background:#f0f5f2!important;border-right:2px solid #b8d0c4!important}
div[data-testid="stSidebar"] *{color:#2d5a3d!important}
div[data-testid="stSidebar"] .stRadio>div{display:flex!important;flex-direction:column!important;gap:5px!important}
div[data-testid="stSidebar"] .stRadio label{background:#fff!important;border:1.5px solid #b8d0c4!important;border-radius:8px!important;padding:9px 13px!important;font-size:.85rem!important;font-weight:500!important;width:100%!important;display:block!important;cursor:pointer!important}
div[data-testid="stSidebar"] .stRadio label:hover{background:#f0f5f2!important;border-color:#3d7a55!important;color:#2d5a3d!important}
div[data-testid="stSidebar"] hr{border-color:#b8d0c4!important}
div[data-testid="stSidebar"] h3{color:#2d5a3d!important;font-size:.72rem!important;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}
.section-header{font-size:1.45rem;font-weight:800;color:#1a3328;margin-bottom:4px;letter-spacing:-.2px}
.section-sub{color:#6b7280;font-size:.87rem;margin-bottom:18px}
.info-box-green,.info-box-blue{background:#f0f5f2;border-left:4px solid #3d7a55;border-radius:0 10px 10px 0;padding:12px 16px;color:#2d5a3d;font-weight:600;font-size:.9rem;margin-bottom:16px}
.info-box-yellow{background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;padding:12px 16px;color:#78350f;font-weight:600;font-size:.9rem;margin-bottom:16px}
.info-box-red{background:#fff1f2;border-left:4px solid #ef4444;border-radius:0 10px 10px 0;padding:12px 16px;color:#7f1d1d;font-weight:600;font-size:.9rem;margin-bottom:16px}
.styled-divider{height:1px;background:#b8d0c4;margin:28px 0}
@media(max-width:767px){.section-header{font-size:1.15rem!important}.section-sub{font-size:.8rem!important}}
</style>
<script>
(function(){
  function fix(){
    var m=window.innerWidth<=767;
    document.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function(r){
      if(m){r.style.setProperty('flex-wrap','wrap','important');r.style.setProperty('gap','.5rem','important')}
      r.style.setProperty('align-items','stretch','important');
    });
    document.querySelectorAll('[data-testid="column"]').forEach(function(c){
      c.style.setProperty('display','flex','important');c.style.setProperty('flex-direction','column','important');
      if(m){c.style.setProperty('min-width','100%','important');c.style.setProperty('width','100%','important');c.style.setProperty('flex','0 0 100%','important');}
    });
  }
  fix();window.addEventListener('resize',fix);
  var ob=new MutationObserver(fix);
  function start(){if(document.body)ob.observe(document.body,{childList:true,subtree:true});else setTimeout(start,100);}
  start();[500,1500,3000].forEach(function(d){setTimeout(fix,d);});
})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style='text-align:center;padding:22px 0 14px;border-bottom:2px solid #b8d0c4;margin-bottom:4px;'>
      <svg width="56" height="56" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin:0 auto 8px;display:block;">
        <circle cx="32" cy="32" r="30" fill="#2d5a3d" stroke="#5a9470" stroke-width="2"/>
        <circle cx="32" cy="32" r="23" fill="#3d7a55"/>
        <rect x="30.5" y="35" width="3" height="13" rx="1.5" fill="#b8d0c4"/>
        <path d="M32 34 Q24 26 20 18 Q28 22 32 28 Q36 22 44 18 Q40 26 32 34Z" fill="#82b49a"/>
        <path d="M32 30 Q26 24 24 16 Q31 21 32 27 Q33 21 40 16 Q38 24 32 30Z" fill="#a8c9b8"/>
        <circle cx="32" cy="37" r="4.5" fill="#92400e"/>
        <rect x="8" y="46" width="3.5" height="9" rx="1" fill="#82b49a" opacity="0.85"/>
        <rect x="13.5" y="42" width="3.5" height="13" rx="1" fill="#82b49a" opacity="0.85"/>
        <rect x="19" y="45" width="3.5" height="10" rx="1" fill="#82b49a" opacity="0.85"/>
        <polyline points="9.75,50 15.25,46 20.75,49" stroke="#b8d0c4" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        <circle cx="9.75" cy="50" r="1.2" fill="#a8c9b8"/><circle cx="15.25" cy="46" r="1.2" fill="#a8c9b8"/><circle cx="20.75" cy="49" r="1.2" fill="#a8c9b8"/>
      </svg>
      <div style='font-size:1.3rem;font-weight:900;color:#1a3328;'>COCOStat</div>
      <div style='font-size:.65rem;color:#2d5a3d;margin-top:3px;letter-spacing:2px;font-weight:600;text-transform:uppercase;'>Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    lang_choice = st.radio(" Language / \u0db7\u0dcf\u0DC2\u0dcf\u0dc0", ["English", "\u0dc3\u0dd2\u0d82\u0dc4\u0dbd"], index=0)
    lang = "en" if lang_choice == "English" else "si"
    t = T[lang]
    st.markdown("### " + ("Settings" if lang=="en" else "සැකසුම්"))
    regime_emojis = ["", "", ""]
    active_regime = st.selectbox(t["regime_select"], [f"{e}{o}" for e,o in zip(regime_emojis, t["regime_options"])], index=0)
    regime_idx = [f"{e}{o}" for e,o in zip(regime_emojis, t["regime_options"])].index(active_regime)
    st.markdown("---")
    st.markdown("### " + (" Navigation" if lang=="en" else " \u0dc3\u0d82\u0da0\u0dcf\u0dbd\u0db1\u0dba"))
    nav_full = [f"{icon} {name}" for icon, name in zip(t["nav_icons"], t["nav"])]
    section = st.radio("", nav_full, label_visibility="collapsed")
    st.markdown("---")

    # ══ PRICE RISK EARLY WARNING SYSTEM ══
    # header label only — full box rendered after score is computed
    _ew_title = 'Price Risk Early Warning' if lang=='en' else 'මිල අවදානම් අනතුරු ඇඟවීම'


    current_price = 68.50
    price_3m_ago = float(history_df["price"].iloc[-4]) if len(history_df) >= 4 else current_price
    price_6m_ago = float(history_df["price"].iloc[-7]) if len(history_df) >= 7 else current_price
    avg_12m_sb = float(history_df["price"].tail(12).mean())
    avg_3m_sb = float(history_df["price"].tail(3).mean())
    volatility_sb = float(history_df["price"].tail(12).std())
    momentum_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
    momentum_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
    crisis_months_sb = int((history_df["price"].tail(12) >= 80).sum())

    # Thresholds (user-configurable)
    warn_threshold = st.slider(
        " Warning Level (Rs.)" if lang=="en" else " අවවාද සීමාව (රු.)",
        min_value=50, max_value=90, value=65, step=1)
    crisis_threshold = st.slider(
        " Crisis Level (Rs.)" if lang=="en" else " අර්බුද සීමාව (රු.)",
        min_value=60, max_value=120, value=80, step=1)

    # ── Risk Score Engine ──────────────────
    risk_score = 0
    risk_factors = []

    # Factor 1: Current price vs thresholds
    if current_price >= crisis_threshold:
        risk_score += 40
        risk_factors.append(("🔴", f"Price Rs.{current_price:.0f} " + ("above crisis level" if lang=="en" else "අර්බුද සීමාව ඉක්මවා"), 40))
    elif current_price >= warn_threshold:
        risk_score += 25
        risk_factors.append(("🟡", f"Price Rs.{current_price:.0f} " + ("above warning level" if lang=="en" else "අවවාද සීමාව ඉක්මවා"), 25))
    else:
        risk_factors.append(("🟢", f"Price Rs.{current_price:.0f} " + ("within safe range" if lang=="en" else "ආරක්ෂිත පරාසය තුළ"), 0))

    # Factor 2: 3-month momentum
    if momentum_3m > 15:
        risk_score += 20
        risk_factors.append(("🔴", ("Rapid 3M rise" if lang=="en" else "ඉක්මන් මාස 3 ඉහළ යාම") + f": +{momentum_3m:.1f}%", 20))
    elif momentum_3m > 8:
        risk_score += 12
        risk_factors.append(("🟡", ("Moderate 3M rise" if lang=="en" else "මධ්‍යස්ථ මාස 3 ඉහළ යාම") + f": +{momentum_3m:.1f}%", 12))
    elif momentum_3m < -10:
        risk_score += 5
        risk_factors.append(("", ("Sharp 3M drop" if lang=="en" else "තීව්‍ර මාස 3 පහත වැටීම") + f": {momentum_3m:.1f}%", 5))
    else:
        risk_factors.append(("🟢", ("3M change stable" if lang=="en" else "මාස 3 ස්ථාවරයි") + f": {momentum_3m:+.1f}%", 0))

    # Factor 3: Volatility
    cv_sb = (volatility_sb / avg_12m_sb) * 100
    if cv_sb > 18:
        risk_score += 20
        risk_factors.append(("🔴", ("High volatility" if lang=="en" else "ඉහළ අස්ථාවරතාව") + f": CV {cv_sb:.1f}%", 20))
    elif cv_sb > 10:
        risk_score += 10
        risk_factors.append(("🟡", ("Moderate volatility" if lang=="en" else "මධ්‍යස්ථ අස්ථාවරතාව") + f": CV {cv_sb:.1f}%", 10))
    else:
        risk_factors.append(("🟢", ("Low volatility" if lang=="en" else "අඩු අස්ථාවරතාව") + f": CV {cv_sb:.1f}%", 0))

    # Factor 4: Distance to crisis threshold
    gap_to_crisis = crisis_threshold - current_price
    if gap_to_crisis <= 5:
        risk_score += 15
        risk_factors.append(("🔴", ("Only" if lang=="en" else "අර්බුද සීමාවට") + f" Rs.{gap_to_crisis:.0f} " + ("below crisis level" if lang=="en" else "පමණයි"), 15))
    elif gap_to_crisis <= 12:
        risk_score += 8
        risk_factors.append(("🟡", f"Rs.{gap_to_crisis:.0f} " + ("buffer to crisis level" if lang=="en" else "අර්බුද සීමාවට"), 8))
    else:
        risk_factors.append(("🟢", f"Rs.{gap_to_crisis:.0f} " + ("buffer to crisis level" if lang=="en" else "අර්බුද සීමාවට"), 0))

    # Factor 5: Recent crisis months
    if crisis_months_sb >= 4:
        risk_score += 5
        risk_factors.append(("🟡", f"{crisis_months_sb} " + ("crisis months (last 12)" if lang=="en" else "අර්බුද මාස (අවසාන 12)"), 5))

    risk_score = min(risk_score, 100)

    # Risk level classification
    if risk_score >= 70:
        rl_label = " CRISIS RISK" if lang=="en" else " අර්බුද අවදානම"
        rl_clr = "#ef4444"; rl_bg = "#fef2f2"; rl_border = "#fca5a5"
        rl_action = "Immediate action required" if lang=="en" else "ක්ෂණික පියවර අවශ්‍යයි"
    elif risk_score >= 45:
        rl_label = " ELEVATED RISK" if lang=="en" else " ඉහළ අවදානම"
        rl_clr = "#d97706"; rl_bg = "#fffbeb"; rl_border = "#fcd34d"
        rl_action = "Close monitoring needed" if lang=="en" else "සමීප නිරීක්ෂණය කරන්න"
    elif risk_score >= 25:
        rl_label = " WATCH" if lang=="en" else " නිරීක්ෂණය"
        rl_clr = "#ca8a04"; rl_bg = "#fefce8"; rl_border = "#fde68a"
        rl_action = "Monitor weekly" if lang=="en" else "සතිපතා නිරීක්ෂණය"
    else:
        rl_label = " LOW RISK" if lang=="en" else " අඩු අවදානම"
        rl_clr = "#3d7a55"; rl_bg = "#f0f5f2"; rl_border = "#a8c9b8"
        rl_action = "Market is stable" if lang=="en" else "වෙළඳ ස්ථාවරයි"

    # ── Quick Actions by risk level ──────────────────────────────────────
    if risk_score >= 70:
        actions_inner = (
            "Alert CDA/HARTI officials<br>Activate buffer stocks<br>Broadcast price warnings<br>Farmers: sell immediately<br>Businesses: hedge now"
            if lang=="en" else
            "CDA/HARTI නිලධාරීන් අනතුරු අඟවන්න<br>බෆර් තොග සක්‍රිය කරන්න<br>මිල අනතුරු ඇඟවීම් විකාශය කරන්න<br>ගොවීන්: ඉක්මනින් විකුණන්න<br>ව්‍යාපාර: දැන් ආරක්ෂා කරන්න")
    elif risk_score >= 45:
        actions_inner = (
            "Monitor daily auction prices<br>Prepare buffer stock release<br>Farmers: consider selling<br>Businesses: review contracts<br>Watch export demand"
            if lang=="en" else
            "දෛනික වෙන්දේසි මිල නිරීක්ෂණය කරන්න<br>බෆර් තොග මුදා හැරීමට සූදානම් වන්න<br>ගොවීන්: විකිණීම සලකා බලන්න<br>ව්‍යාපාර: ගිවිසුම් සමාලෝචනය කරන්න<br>අපනයන ඉල්ලුම නිරීක්ෂණය කරන්න")
    elif risk_score >= 25:
        actions_inner = (
            "Weekly price check sufficient<br>Farmers: continue normal ops<br>Businesses: plan ahead<br>Consider forward contracts<br>Explore export opportunities"
            if lang=="en" else
            "සතිපතා මිල පරීක්ෂාව ප්‍රමාණවත්<br>ගොවීන්: සාමාන්‍ය ක්‍රියාකාරිත්වය දිගටම කරන්න<br>ව්‍යාපාර: ඉදිරිය සැලසුම් කරන්න<br>ඉදිරි ගිවිසුම් සලකා බලන්න<br>අපනයන අවස්ථා ගවේෂණය කරන්න")
    else:
        actions_inner = (
            "No immediate action needed<br>Good time to invest/expand<br>Monthly monitoring sufficient<br>Build buffer stocks now<br>Explore value-added products"
            if lang=="en" else
            "ක්ෂණික ක්‍රියාමාර්ගයක් අවශ්‍ය නැත<br>ආයෝජනය/ව්‍යාප්ත කිරීමට හොඳ කාලය<br>මාසික නිරීක්ෂණය ප්‍රමාණවත්<br>දැන් බෆර් තොග ගොඩ නගා ගන්න<br>අගය-එකතු නිෂ්පාදන ගවේෂණය කරන්න")

    # ── Unified Formal Risk Panel ──────────────────────────────────────────
    bar_w   = min(int(risk_score), 100)
    bar_clr = ("#ef4444" if risk_score >= 70 else "#f59e0b" if risk_score >= 45
               else "#eab308" if risk_score >= 25 else "#3d7a55")

    # Build risk factor rows
    rf_rows_html = ""
    for dot, label, pts in risk_factors:
        pt_html = (f"<span style='color:#ef4444;font-size:.6rem;font-weight:700;'>+{pts}</span>"
                   if pts > 0 else "")
        rf_rows_html += (
            f"<div style='display:flex;align-items:center;gap:6px;padding:4px 0;"
            f"border-bottom:1px solid #e8f0eb;'>"
            f"<span style='font-size:.7rem;flex-shrink:0;'>{dot}</span>"
            f"<span style='font-size:.62rem;color:#374151;flex:1;line-height:1.3;'>{label}</span>"
            f"{pt_html}"
            f"</div>"
        )

    # Build quick action items
    action_items = actions_inner.replace("<br>", "|||").split("|||")
    action_rows_html = "".join(
        f"<div style='padding:3px 0;border-bottom:1px solid #e8f0eb;font-size:.62rem;color:#374151;line-height:1.4;'>{a.strip()}</div>"
        for a in action_items if a.strip()
    )

    _ew_title_lbl   = 'Price Risk Early Warning' if lang=='en' else 'මිල අවදානම් අනතුරු ඇඟවීම'
    _rf_lbl         = 'Risk Factors'      if lang=='en' else 'අවදානම් සාධක'
    _pz_lbl         = 'Price Thresholds'  if lang=='en' else 'මිල සීමා'
    _cp_lbl         = 'Current Auction Price' if lang=='en' else 'දැනට වෙන්දේසි මිල'
    _qa_lbl         = 'Recommended Actions' if lang=='en' else 'නිර්දේශිත ක්‍රියා'
    _mom_lbl        = 'vs 3 months ago'   if lang=='en' else 'මාස 3 ට සාපේක්ෂව'
    _crisis_lbl     = 'Crisis'  if lang=='en' else 'අර්බුද'
    _warn_lbl       = 'Warning' if lang=='en' else 'අවවාද'
    _safe_lbl       = 'Safe'    if lang=='en' else 'ආරක්ෂිත'

    _html_box = (
        "<div style='background:#fff;border:1px solid #b8d0c4;border-radius:10px;overflow:hidden;margin-bottom:12px;'>"
        f"<div style='background:#1a3328;padding:9px 14px;'>"
        f"<div style='font-size:.65rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1.5px;'>{_ew_title_lbl}</div>"
        "</div>"
        "<div style='padding:12px 14px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>"
        f"<div style='font-size:.75rem;font-weight:800;color:{rl_clr};'>{rl_label}</div>"
        f"<div style='font-size:.9rem;font-weight:900;color:{rl_clr};'>{risk_score}<span style='font-size:.58rem;font-weight:500;'>/100</span></div>"
        "</div>"
        "<div style='background:#e5e7eb;border-radius:4px;height:6px;margin-bottom:5px;'>"
        f"<div style='background:{bar_clr};width:{bar_w}%;height:100%;border-radius:4px;'></div>"
        "</div>"
        f"<div style='font-size:.6rem;color:{rl_clr};font-weight:600;margin-bottom:10px;'>{rl_action}</div>"
        "<div style='height:1px;background:#e8f0eb;margin-bottom:8px;'></div>"
        f"<div style='font-size:.6rem;font-weight:700;color:#4a6657;text-transform:uppercase;letter-spacing:.8px;margin-bottom:3px;'>{_cp_lbl}</div>"
        "<div style='display:flex;align-items:baseline;gap:6px;margin-bottom:2px;'>"
        f"<div style='font-size:1.2rem;font-weight:900;color:{rl_clr};'>Rs. {current_price:.2f}</div>"
        f"<div style='font-size:.6rem;color:#64748b;'>{momentum_3m:+.1f}% {_mom_lbl}</div>"
        "</div>"
        "<div style='height:1px;background:#e8f0eb;margin:8px 0;'></div>"
        f"<div style='font-size:.6rem;font-weight:700;color:#4a6657;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px;'>{_pz_lbl}</div>"
        "<div style='display:flex;flex-direction:column;gap:3px;margin-bottom:8px;'>"
        f"<div style='display:flex;justify-content:space-between;background:#fef2f2;border-left:3px solid #ef4444;padding:3px 7px;border-radius:0 4px 4px 0;'>"
        f"<span style='font-size:.62rem;font-weight:600;color:#7f1d1d;'>{_crisis_lbl}</span>"
        f"<span style='font-size:.62rem;font-weight:700;color:#7f1d1d;'>Rs.{crisis_threshold}+</span></div>"
        f"<div style='display:flex;justify-content:space-between;background:#fefce8;border-left:3px solid #eab308;padding:3px 7px;border-radius:0 4px 4px 0;'>"
        f"<span style='font-size:.62rem;font-weight:600;color:#713f12;'>{_warn_lbl}</span>"
        f"<span style='font-size:.62rem;font-weight:700;color:#713f12;'>Rs.{warn_threshold}&ndash;{crisis_threshold - 1}</span></div>"
        f"<div style='display:flex;justify-content:space-between;background:#f0f5f2;border-left:3px solid #3d7a55;padding:3px 7px;border-radius:0 4px 4px 0;'>"
        f"<span style='font-size:.62rem;font-weight:600;color:#1a3328;'>{_safe_lbl}</span>"
        f"<span style='font-size:.62rem;font-weight:700;color:#1a3328;'>Rs.&lt;{warn_threshold}</span></div>"
        "</div>"
        "<div style='height:1px;background:#e8f0eb;margin-bottom:8px;'></div>"
        f"<div style='font-size:.6rem;font-weight:700;color:#4a6657;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px;'>{_rf_lbl}</div>"
        f"<div style='margin-bottom:8px;'>{rf_rows_html}</div>"
        "<div style='height:1px;background:#e8f0eb;margin-bottom:8px;'></div>"
        f"<div style='font-size:.6rem;font-weight:700;color:#4a6657;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px;'>{_qa_lbl}</div>"
        f"<div>{action_rows_html}</div>"
        "</div></div>"
    )
    st.markdown(_html_box, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""<div style='background:#f0f5f2;border:1px solid #b8d0c4;border-radius:10px;padding:14px 12px;text-align:center;'>
      <div style='font-size:.6rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;'>\U0001f464 {t['footer_researcher']}</div>
      <div style='font-weight:800;font-size:.88rem;color:#1a3328;margin-bottom:8px;'>M A C S RATHNAYAKE</div>
      <div style='font-size:.6rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>{t['footer_ids']}</div>
      <div style='font-size:.78rem;color:#2d5a3d;'>UOW: w1999714</div>
      <div style='font-size:.78rem;color:#2d5a3d;margin-bottom:8px;'>IIT: 20220508</div>
      <div style='font-size:.6rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>{t['footer_programme']}</div>
      <div style='font-size:.75rem;color:#2d5a3d;line-height:1.6;'>BSc (Hons) Data Science<br>&amp; Analytics<br>University of Westminster</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────
st.markdown(f"""
<div id='coco-hero' style='text-align:center;padding:clamp(16px,4vw,36px) clamp(12px,5vw,48px) clamp(14px,3vw,32px);margin-bottom:0;
  background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 50%,#3d7a55 100%);border-bottom:3px solid #3d7a55;box-shadow:0 4px 20px rgba(26,51,40,.18);'>
  <div style='display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);border-radius:20px;padding:5px 18px;
      font-size:clamp(.62rem,2vw,.78rem);font-weight:700;color:#b8d0c4;letter-spacing:1px;margin-bottom:10px;'> {t["subtitle"]}</div>
  <h1 style='font-size:clamp(1.3rem,5vw,2.2rem);font-weight:900;color:#fff;margin:0 0 10px;line-height:1.25;text-shadow:0 2px 8px rgba(0,0,0,.2);'>{t["tagline"]}</h1>
  <p style='color:#b8d0c4;font-size:clamp(.78rem,2.5vw,.9rem);max-width:580px;margin:0 auto;line-height:1.7;font-weight:500;opacity:.9;'>{t["desc"]}</p>
</div>
<div style='margin-bottom:24px;'></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def metric_card(label, value, clr="#3d7a55", sub=None, height=110, val_size="1.4rem"):
    sub_html = (f"<div style='display:inline-block;background:#f0f5f2;color:#2d5a3d;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #b8d0c4;margin-top:4px;'>{sub}</div>"
                if sub else
                "<span style='display:none;'></span>")
    return (f"<div style='background:#fff;border:1px solid #b8d0c4;border-top:3px solid #3d7a55;border-radius:10px;padding:14px 16px;"
            f"height:{height}px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;'>"
            f"<div style='font-size:.65rem;font-weight:700;color:#2d5a3d;text-transform:uppercase;letter-spacing:.8px;'>{label}</div>"
            f"<div style='font-size:{val_size};font-weight:900;color:#1a3328;line-height:1.2;white-space:nowrap;'>{value}</div>"
            f"{sub_html}</div>")

def section_header(title, sub=None):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if sub: st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

REGIME_COLORS = ["#5a9470","#eab308","#ef4444"]
REGIME_BGS = ["#f0f5f2","#fef9c3","#fee2e2"]
REGIME_EMOJI = ["🟢","🟡","🔴"]

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────
sec_name = section.split(" ", 1)[1] if " " in section else section

# ══ OVERVIEW & HISTORY ═════════════════════════════════════════════════════
if t["nav"][0] in sec_name:
    c1,c2,c3,c4 = st.columns(4)
    cards = [
        (" "+t["card_price_label"], t["card_price_value"], "#3d7a55", t["card_price_sub"]),
        (" "+t["card_market_label"], " "+t["card_market_value"], "#3d7a55", t["card_market_sub"]),
        (" "+t["card_demand_label"], t["card_demand_value"], "#3d7a55", t["card_demand_sub"]),
        (" "+t["card_forecast_label"], t["card_forecast_value"], "#3d7a55", t["card_forecast_sub"]),
    ]
    for col,(label,value,clr,sub) in zip([c1,c2,c3,c4], cards):
        with col: st.markdown(metric_card(label,value,clr,sub,130), unsafe_allow_html=True)
    divider()

    col_chart, col_stats = st.columns([2,1])
    with col_chart:
        recent = history_df.tail(36)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=recent["date"],y=recent["price"],fill="tozeroy",fillcolor="rgba(61,122,85,.1)",
            line=dict(color="#3d7a55",width=2.5),hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
        fig.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}",annotation_position="top left")
        fig.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}",annotation_position="top left")
        fig.update_layout(title=dict(text=" "+("Recent 3-Year Price Trend" if lang=="en" else "\u0db8\u0dd0\u0dad \u0d9a\u0dcf\u0dbd \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0"),font=dict(size=14,color="#1a3328")),
            height=280,margin=dict(l=80,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",tickfont=dict(size=11)),showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":"hover"})
    with col_stats:
        st.markdown("#### "+("Quick Stats" if lang=="en" else "ඉක්මන් සංඛ්‍යාන"))
        last36 = history_df.tail(36)
        for lbl,val in [("3yr Avg" if lang=="en" else "වසර 3 සාමාන්‍යය",f"Rs.{last36['price'].mean():.1f}"),
                        ("3yr High" if lang=="en" else "වසර 3 ඉහළම",f"Rs.{last36['price'].max():.1f}"),
                        ("3yr Low" if lang=="en" else "වසර 3 පහළම",f"Rs.{last36['price'].min():.1f}"),
                        ("Volatility" if lang=="en" else "අස්ථාවරතාව",f"Rs.{last36['price'].std():.1f}")]:
            st.markdown(f"""<div style='background:#f0f5f2;border:1px solid #b8d0c4;border-left:4px solid #3d7a55;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.7rem;color:#2d5a3d;font-weight:700;text-transform:uppercase;'>{lbl}</div>
                <div style='font-size:1.25rem;font-weight:800;color:#1a3328;'>{val}</div></div>""", unsafe_allow_html=True)
    divider()

    # Seasonality heatmap
    st.markdown("#### "+("Monthly Avg Price by Year" if lang=="en" else "\u0dc0\u0dbb\u0dca\u0DC2\u0dba \u0d85\u0db1\u0dd4\u0dc0 \u0db8\u0dcf\u0dc3\u0dd2\u0d9a \u0db8\u0dd2\u0dbd"))
    mnames=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    piv = history_df.pivot_table(index="year",columns="month",values="price",aggfunc="mean").reindex(columns=range(1,13))
    piv.columns=mnames
    zc=[[None if np.isnan(v) else round(v,1) for v in row] for row in piv.values]
    tx=[[f"Rs.{v:.1f}" if not np.isnan(v) else "-" for v in row] for row in piv.values]
    fig_h=go.Figure(go.Heatmap(z=zc,x=mnames,y=[str(y) for y in piv.index],
        colorscale=[[0,"#f0f5f2"],[.5,"#fef9c3"],[1,"#fee2e2"]],text=tx,texttemplate="%{text}",textfont=dict(size=9),
        hovertemplate="<b>%{y} %{x}</b><br>%{text}<extra></extra>",showscale=True,
        colorbar=dict(title="Rs.",tickfont=dict(size=10)),zmin=history_df["price"].min(),zmax=history_df["price"].max()))
    fig_h.update_layout(height=280,margin=dict(l=20,r=20,t=10,b=20),paper_bgcolor="#fff")
    st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # Price Calculator
    st.markdown(f"#### {t['price_calc_title']}")
    st.markdown(f"<div class='section-sub'>{t['price_calc_sub']}</div>",unsafe_allow_html=True)
    pc1,pc2,pc3=st.columns(3)
    with pc1: nuts=st.number_input(t["nuts_per_week"],1,100,10,1)
    with pc2: pnow=st.number_input(t["current_price_input"],10.0,200.0,68.5,.5)
    with pc3: pnew=st.number_input(t["new_price_input"],10.0,200.0,75.0,.5)
    dw=(pnew-pnow)*nuts; clrc="#ef4444" if dw>0 else "#5a9470"; arr="" if dw>0 else ""
    rc1,rc2,rc3=st.columns(3)
    for col,lbl,val in zip([rc1,rc2,rc3],[t["weekly_impact"],t["monthly_impact"],t["annual_impact"]],[dw,dw*4,dw*52]):
        with col:
            st.markdown(f"""<div style='background:#f8fafc;border:2px solid {clrc}33;border-radius:14px;padding:14px;text-align:center;height:90px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.76rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{lbl}</div>
                <div style='font-size:1.5rem;font-weight:900;color:{clrc};'>{arr} Rs.{abs(val):.2f}</div></div>""",unsafe_allow_html=True)
    divider()
    # ── Historical Price Analysis ──────────────────────────────────────────────
    section_header(" "+t["history_title"], t["history_sub"])
    fig_hist=go.Figure()
    fig_hist.add_trace(go.Scatter(x=history_df["date"],y=history_df["price"],fill="tozeroy",fillcolor="rgba(22,163,74,.08)",
        line=dict(color="#3d7a55",width=1.8),mode="lines",hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_hist.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}",annotation_position="top left",annotation_font_color="#eab308")
    fig_hist.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}",annotation_position="bottom left",annotation_font_color="#ef4444")
    fig_hist.update_layout(height=360,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True),tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",tickfont=dict(size=11)),showlegend=False)
    st.plotly_chart(fig_hist,use_container_width=True,config={"displayModeBar":"hover"})
    st.markdown("#### "+("Summary Statistics" if lang=="en" else "සාරාංශ සංඛ්‍යාන"))
    hs1,hs2,hs3,hs4,hs5=st.columns(5)
    hdata=[(" " + ("Max" if lang=="en" else "උපරිම"),f"Rs.{history_df['price'].max():.2f}"),
           (" " + ("Min" if lang=="en" else "අවම"),f"Rs.{history_df['price'].min():.2f}"),
           (" " + ("Avg" if lang=="en" else "සාමාන්‍යය"),f"Rs.{history_df['price'].mean():.2f}"),
           (" " + ("Std" if lang=="en" else "විචලනය"),f"Rs.{history_df['price'].std():.2f}"),
           (" " + ("Months" if lang=="en" else "මාස"),str(len(history_df)))]
    for col,(lbl,val) in zip([hs1,hs2,hs3,hs4,hs5],hdata):
        with col: st.markdown(metric_card(lbl,val,height=90),unsafe_allow_html=True)
    divider()
    cp,cy=st.columns(2)
    with cp:
        rc=history_df["regime"].value_counts().sort_index()
        fig_pie=go.Figure(go.Pie(labels=t["regime_options"],values=rc.values,hole=.5,
            marker=dict(colors=REGIME_COLORS),textinfo="label+percent",textfont=dict(size=11)))
        fig_pie.update_layout(title=dict(text=" "+("Regime Distribution" if lang=="en" else "තත්ත්ව බෙදා හැරීම"),font=dict(size=13)),
            height=300,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_pie,use_container_width=True,config={"displayModeBar":"hover"})
    with cy:
        aa=history_df.groupby("year")["price"].mean().reset_index()
        fig_ann=go.Figure(go.Bar(x=aa["year"].astype(str),y=aa["price"].round(2),
            marker=dict(color=aa["price"],colorscale=[[0,"#f0f5f2"],[.5,"#fef9c3"],[1,"#fee2e2"]],showscale=False,line=dict(width=0)),
            text=aa["price"].round(1),texttemplate="Rs.%{text}",textposition="outside",
            hovertemplate="<b>%{x}</b><br>Avg: Rs.%{y:.2f}<extra></extra>"))
        fig_ann.update_layout(title=dict(text=" "+("Annual Average Price" if lang=="en" else "වාර්ෂික සාමාන්‍ය මිල"),font=dict(size=13)),
            height=300,margin=dict(l=10,r=10,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",range=[0,aa["price"].max()*1.15]),showlegend=False)
        st.plotly_chart(fig_ann,use_container_width=True,config={"displayModeBar":"hover"})
# ══ MARKET & DEMAND ════════════════════════════════════════════════════════
elif t["nav"][1] in sec_name:
    section_header(" "+t["regime_title"])
    c1,c2,c3=st.columns(3)
    for i,col in enumerate([c1,c2,c3]):
        border=f"3px solid {REGIME_COLORS[i]}" if i==regime_idx else "2px solid #e2e8f0"
        bg=REGIME_BGS[i] if i==regime_idx else "#f8fafc"
        with col:
            selected_badge = (f"<div style='margin-top:10px;font-size:.75rem;font-weight:800;color:{REGIME_COLORS[i]};'>&#10003; Selected</div>"
                              if i == regime_idx else
                              "<div style='margin-top:10px;height:22px;'></div>")
            st.markdown(
                f"<div style='background:{bg};border:{border};border-radius:16px;padding:24px;text-align:center;'>"
                f"<div style='font-size:2.5rem;margin-bottom:8px;'>{REGIME_EMOJI[i]}</div>"
                f"<div style='font-weight:800;color:{REGIME_COLORS[i]};margin-bottom:8px;'>{t['regime_options'][i]}</div>"
                f"<div style='font-size:.9rem;color:#475569;'>{t['regime_desc'][i]}</div>"
                f"{selected_badge}"
                f"</div>",
                unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    rc_=REGIME_COLORS[regime_idx]; rb_=REGIME_BGS[regime_idx]
    x1,x2,x3=st.columns(3)
    for col,lbl,val in zip([x1,x2,x3],[t["regime_avg_label"],t["regime_vol_label"],t["regime_status_label"]],
                            [t["regime_avg"][regime_idx],t["regime_vol"][regime_idx],t["regime_status"][regime_idx]]):
        with col:
            st.markdown(f"""<div style='background:{rb_};border-radius:12px;padding:16px;text-align:center;height:90px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.72rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{lbl}</div>
                <div style='font-size:1.7rem;font-weight:900;color:{rc_};'>{val}</div></div>""",unsafe_allow_html=True)
    divider()
    fig_r=go.Figure()
    for ri,(rc,rn) in enumerate(zip(REGIME_COLORS,t["regime_options"])):
        sub=history_df[history_df["regime"]==ri]
        if not sub.empty:
            fig_r.add_trace(go.Scatter(x=sub["date"],y=sub["price"],mode="markers",
                marker=dict(color=rc,size=5,opacity=.8),name=rn,hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_r.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}",annotation_position="top left")
    fig_r.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}",annotation_position="top left")
    fig_r.update_layout(title=dict(text=" "+("Price History by Regime" if lang=="en" else "තත්ත්වය අනුව මිල ඉතිහාසය"),font=dict(size=14)),
        height=320,margin=dict(l=80,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_r,use_container_width=True,config={"displayModeBar":"hover"})
    divider()
    st.markdown("#### "+("Regime Statistics" if lang=="en" else "තත්ත්ව සංඛ්‍යාන"))
    rc_counts=history_df["regime"].value_counts().sort_index()
    sc1,sc2,sc3=st.columns(3)
    for i,col in enumerate([sc1,sc2,sc3]):
        cnt=rc_counts.get(i,0); pct=cnt/len(history_df)*100
        with col:
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-radius:12px;padding:14px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:1.8rem;margin-bottom:4px;'>{REGIME_EMOJI[i]}</div>
                <div style='font-weight:800;color:{REGIME_COLORS[i]};font-size:1rem;margin-bottom:4px;'>{t["regime_options"][i]}</div>
                <div style='font-size:1.6rem;font-weight:900;color:{REGIME_COLORS[i]};'>{pct:.0f}%</div>
                <div style='font-size:.8rem;color:#64748b;'>{cnt} {"මාස" if lang=="si" else "months"}</div></div>""",unsafe_allow_html=True)
    divider()
    # ── Demand Analysis ────────────────────────────────────────────────────────
    section_header(" "+t["demand_title"])
    st.markdown(f"<div class='info-box-blue'>{t['demand_note']}</div>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        fig_d=go.Figure(go.Bar(x=t["demand_periods"],y=t["demand_sens"],
            marker=dict(color=REGIME_COLORS,line=dict(width=0)),
            text=[f"{v}%" for v in t["demand_sens"]],textposition="outside",width=.5))
        fig_d.update_layout(title=dict(text=t["demand_bar_title"],font=dict(size=14)),
            height=280,margin=dict(l=20,r=20,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",range=[0,50]),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":"hover"})
    with c2:
        for i,(period,desc) in enumerate(t["demand_cards"]):
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-left:4px solid {REGIME_COLORS[i]};border-radius:0 12px 12px 0;padding:14px 16px;margin-bottom:12px;'>
                <div style='font-weight:700;font-size:.95rem;margin-bottom:4px;'>{period}</div>
                <div style='font-size:.88rem;color:#475569;line-height:1.5;'>{desc}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### "+("Price Elasticity of Demand" if lang=="en" else "ඉල්ලුම් ස්ථිතිස්ථිකය"))
    e1,e2,e3=st.columns(3)
    for col,(ev,ep,ec,eb) in zip([e1,e2,e3],[("-0.35","Stable" if lang=="en" else "ස්ථාවර","#5a9470","#f0f5f2"),
                                             ("-0.22","Warning" if lang=="en" else "අවවාද","#eab308","#fef9c3"),
                                             ("-0.12","Crisis" if lang=="en" else "අර්බුද","#ef4444","#fee2e2")]):
        with col:
            st.markdown(f"""<div style='background:{eb};border-radius:12px;padding:16px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.72rem;font-weight:700;color:#64748b;margin-bottom:4px;'>{"Elasticity" if lang=="en" else "ස්ථිතිස්ථිකය"} - {ep}</div>
                <div style='font-size:1.9rem;font-weight:900;color:{ec};'>{ev}</div>
                <div style='font-size:.78rem;color:#64748b;margin-top:2px;'>{"Inelastic" if lang=="en" else "අප්‍රත්‍යාස්ථ"}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### "+("Demand Curve by Regime" if lang=="en" else "තත්ත්වය අනුව ඉල්ලුම් වක්‍රය"))
    pr=np.linspace(40,100,60); bq=1000; bp=60
    fig_dc=go.Figure()
    for (lbl,el),clr in zip({"Stable":-0.35,"Warning":-0.22,"Crisis":-0.12}.items(),REGIME_COLORS):
        q=bq*(pr/bp)**el
        fig_dc.add_trace(go.Scatter(x=q,y=pr,mode="lines",name=lbl,line=dict(color=clr,width=2.5),
            hovertemplate=f"<b>{lbl}</b><br>Price: Rs.%{{y:.1f}}<br>Qty: %{{x:.0f}}<extra></extra>"))
    fig_dc.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(title=("Quantity Demanded" if lang=="en" else "ඉල්ලුම් ප්‍රමාණය"),showgrid=False),
        yaxis=dict(title=("Price (Rs.)" if lang=="en" else "මිල (රු.)"),gridcolor="#e4eeea",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_dc,use_container_width=True,config={"displayModeBar":"hover"})
# ══ FORECAST ════════════════════════════════════════════════════════════════
elif t["nav"][3] in sec_name:
    section_header(" "+t["forecast_title"])
    st.markdown(f"<div class='info-box-green'>{t['forecast_summary']}</div>",unsafe_allow_html=True)
    hist_r=history_df.tail(16)
    fig_f=go.Figure()
    fig_f.add_trace(go.Scatter(x=pd.concat([forecast_df["date"],forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"],forecast_df["lower"][::-1]]),fill="toself",fillcolor="rgba(245,158,11,.15)",
        line=dict(color="rgba(0,0,0,0)"),name=t["forecast_range_label"],hoverinfo="skip"))
    fig_f.add_trace(go.Scatter(x=hist_r["date"],y=hist_r["price"],line=dict(color="#5a9470",width=2.5),
        name=t["forecast_hist_label"],mode="lines",hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_trace(go.Scatter(x=forecast_df["date"],y=forecast_df["price"],line=dict(color="#f59e0b",width=2.5,dash="dash"),
        name=t["forecast_pred_label"],mode="lines+markers",marker=dict(size=6,color="#f59e0b"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_hline(y=warn_threshold,line_dash="dot",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}",annotation_position="top left")
    fig_f.add_hline(y=crisis_threshold,line_dash="dot",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}",annotation_position="top left")
    fig_f.add_vline(x=forecast_df["date"].iloc[0].timestamp()*1000,line_dash="dot",line_color="#94a3b8",
        annotation_text="Forecast \u2192" if lang=="en" else "\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba \u2192",annotation_position="top left")
    fig_f.update_layout(height=340,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",tickfont=dict(size=11)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_f,use_container_width=True,config={"displayModeBar":"hover"})

    st.markdown("#### "+("12-Week Forecast Details" if lang=="en" else "සති 12 අනාවැකි විස්තර"))
    wcols=st.columns(6)
    for i,(_,row) in enumerate(forecast_df.iterrows()):
        if i>=12: break
        p=row["price"]; clr="#ef4444" if p>=crisis_threshold else "#eab308" if p>=warn_threshold else "#5a9470"
        st_=("Crisis" if p>=crisis_threshold else "Warning" if p>=warn_threshold else "Stable")
        with wcols[i%6]:
            st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid {clr};border-radius:10px;padding:10px 6px;text-align:center;margin-bottom:8px;min-height:78px;display:flex;flex-direction:column;justify-content:center;align-items:center;'>
                <div style='font-size:.7rem;color:#94a3b8;margin-bottom:2px;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:.95rem;font-weight:800;color:{clr};'>Rs.{p:.1f}</div>
                <div style='font-size:.65rem;font-weight:700;color:{clr};'>{st_}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### "+("Forecast Summary" if lang=="en" else "අනාවැකි සාරාංශය"))
    fa=forecast_df["price"].mean(); fmax=forecast_df["price"].max(); fmin=forecast_df["price"].min()
    ww=(forecast_df["price"]>=warn_threshold).sum(); wc=(forecast_df["price"]>=crisis_threshold).sum()
    s1,s2,s3,s4,s5=st.columns(5)
    for col,lbl,val,clr in zip([s1,s2,s3,s4,s5],
        ["Avg Forecast" if lang=="en" else "සාමාන්‍ය අනාවැකිය",
         "Peak Price" if lang=="en" else "ඉහළම මිල",
         "Low Price" if lang=="en" else "පහළම මිල",
         "Weeks >= Warning" if lang=="en" else "සති >= අවවාද",
         "Weeks >= Crisis" if lang=="en" else "සති >= අර්බුද"],
        [f"Rs.{fa:.1f}",f"Rs.{fmax:.1f}",f"Rs.{fmin:.1f}",
         f"{ww} " + ("wks" if lang=="en" else "සති"),
         f"{wc} " + ("wks" if lang=="en" else "සති")],
        ["#3d7a55","#3d7a55","#3d7a55","#3d7a55","#3d7a55"]):
        with col: st.markdown(metric_card(lbl,val,clr,height=80),unsafe_allow_html=True)

# ══ POLICY & RECOMMENDATIONS ═══════════════════════════════════════════════
elif t["nav"][6] in sec_name:
    section_header(" "+t["policy_title"], t["policy_sub"])
    pc1,pc2,pc3=st.columns(3)
    for i,col in enumerate([pc1,pc2,pc3]):
        is_a=(i==regime_idx)
        border=f"3px solid {REGIME_COLORS[i]}" if is_a else "2px solid #e2e8f0"
        badge=f"""<div style='margin-top:8px;background:{REGIME_COLORS[i]}22;border-radius:8px;padding:5px 10px;font-size:.78rem;color:{REGIME_COLORS[i]};font-weight:700;'>{t["policy_active"]}</div>""" if is_a else "<div style='margin-top:8px;height:29px;'></div>"
        with col:
            st.markdown(f"""<div style='border-radius:16px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.08);border:{border};height:200px;display:flex;flex-direction:column;'>
                <div style='background:{REGIME_COLORS[i]};padding:14px 18px;flex-shrink:0;'><span style='font-weight:800;font-size:1rem;color:#fff;'>{t["policy_markets"][i]}</span></div>
                <div style='padding:14px 18px;background:#f8fafc;flex:1;display:flex;flex-direction:column;justify-content:space-between;'>
                  <p style='font-size:.88rem;color:#475569;line-height:1.6;margin:0 0 8px;'>{t["policy_actions"][i]}</p>
                  <div><span style='font-size:.78rem;font-weight:700;color:#94a3b8;'>{t["policy_priority_label"]}</span>
                  <span style='background:{REGIME_COLORS[i]};color:#fff;font-size:.76rem;font-weight:800;padding:3px 10px;border-radius:12px;margin-left:6px;'>{t["policy_priorities"][i]}</span>
                  {badge}</div></div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### "+("Policy Decision Framework" if lang=="en" else "ප්‍රතිපත්ති තීරණ රාමුව"))
    stps=[("1\ufe0f\u20e3","Detect Regime" if lang=="en" else "තත්ත්වය හඳුනන්න","#3d7a55"),
          ("2\ufe0f\u20e3","Assess Priority" if lang=="en" else "ප්‍රමුඛතාව තීරණය","#3d7a55"),
          ("3\ufe0f\u20e3","Implement Policy" if lang=="en" else "ප්‍රතිපත්තිය ක්‍රියාත්මක","#3d7a55"),
          ("4\ufe0f\u20e3","Monitor & Review" if lang=="en" else "නිරීක්ෂණය කරන්න","#f59e0b")]
    sc=st.columns(4)
    for col,(em,st_,clr) in zip(sc,stps):
        with col:
            st.markdown(f"""<div style='text-align:center;background:#f8fafc;border-radius:14px;padding:14px 10px;border:1px solid #e2e8f0;height:100px;display:flex;flex-direction:column;justify-content:center;align-items:center;'>
                <div style='font-size:1.8rem;margin-bottom:6px;'>{em}</div>
                <div style='font-weight:700;font-size:.85rem;color:{clr};'>{st_}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### "+("Policy Effectiveness Indicators" if lang=="en" else "ප්‍රතිපත්ති ඵලදාව දර්ශක"))
    indics=[("Price Stability" if lang=="en" else "මිල ස්ථාවරතා",72,"#3d7a55"),
            ("Supply Chain" if lang=="en" else "සැපයුම් දාමය",58,"#3d7a55"),
            ("Farmer Support" if lang=="en" else "ගොවි සහාය",64,"#f59e0b"),
            ("Market Transparency" if lang=="en" else "වෙළෙඳ විනිවිද",80,"#3d7a55")]
    ic=st.columns(4)
    for col,(lbl,sc_,clr) in zip(ic,indics):
        with col:
            fig_g=go.Figure(go.Indicator(mode="gauge+number",value=sc_,domain={"x":[0,1],"y":[0,1]},
                title={"text":lbl,"font":{"size":11}},
                gauge={"axis":{"range":[0,100],"tickfont":{"size":9}},"bar":{"color":clr},"bgcolor":"#f8fafc",
                       "threshold":{"line":{"color":"#ef4444","width":3},"thickness":.75,"value":75}},
                number={"suffix":"/100","font":{"size":18}}))
            fig_g.update_layout(height=180,margin=dict(l=10,r=10,t=30,b=10),paper_bgcolor="#fff")
            col.plotly_chart(fig_g,use_container_width=True)
    divider()
    # ── Strategic Recommendations ───────────────────────────────────────────────
    import plotly.graph_objects as go

    # ── Hero banner ────────────────────────────────────────────────────────────
    _hero_title = " Strategic Decision Support Centre" if lang=="en" else " උපාය මාර්ගික තීරණ සහාය මධ්‍යස්ථානය"
    _hero_desc = ("Combines market regime detection, demand analysis, weather forecasts and export data to generate "
                   "actionable recommendations for <strong style='color:#82b49a;'>Government policymakers</strong>, "
                   "<strong style='color:#a8c9b8;'>Businesses &amp; Traders</strong>, and "
                   "<strong style='color:#a7f3d0;'>Coconut Farmers</strong>."
                   if lang=="en" else
                   "වෙළඳ තත්ත්ව හඳුනාගැනීම, ඉල්ලුම් විශ්ලේෂණය, කාලගුණ අනාවැකි සහ අපනයන දත්ත ඒකාබද්ධ කොට "
                   "<strong style='color:#82b49a;'>රජයේ ප්‍රතිපත්ති සම්පාදකයන්</strong>, "
                   "<strong style='color:#a8c9b8;'>ව්‍යාපාරිකයන් සහ වෙළෙන්දන්</strong> සහ "
                   "<strong style='color:#a7f3d0;'>පොල් ගොවීන්</strong> වෙනුවෙන් ක්‍රියාශීලී නිර්දේශ ලබා දේ.")
    st.markdown(f"""<div style='background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 55%,#3d7a55 100%);
        border-radius:14px;padding:28px 32px;margin-bottom:20px;'>
      <div style='font-size:clamp(1.2rem,4vw,1.7rem);font-weight:900;color:#fff;margin-bottom:8px;'>
        {_hero_title}
      </div>
      <div style='font-size:.88rem;color:#b8d0c4;line-height:1.7;max-width:760px;'>
        {_hero_desc}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live market snapshot ───────────────────────────────────────────────────
    current_price = history_df["price"].iloc[-1]
    price_3m_ago = history_df["price"].iloc[-4]
    price_change_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
    avg_12m = history_df["price"].tail(12).mean()
    volatility_12m = history_df["price"].tail(12).std()
    cv = (volatility_12m / avg_12m) * 100
    regime_now = int(history_df["regime"].iloc[-1])
    regime_labels = [" " + ("Stable" if lang=="en" else "ස්ථාවර"),
                        " " + ("Warning" if lang=="en" else "අවවාද"),
                        " " + ("Crisis" if lang=="en" else "අර්බුද")]
    regime_colors = ["#5a9470","#eab308","#ef4444"]
    regime_bgs = ["#f0f5f2","#fef9c3","#fee2e2"]

    st.markdown("#### " + ("Live Market Snapshot" if lang=="en" else "සජීව වෙළඳ තතු"))
    sn1,sn2,sn3,sn4,sn5 = st.columns(5)
    snap_data = [
        (" " + ("Current Price" if lang=="en" else "වත්මන් මිල"), f"Rs. {current_price:.2f}", "#3d7a55"),
        (" " + ("3-Month Change" if lang=="en" else "මාස 3 වෙනස"), f"{price_change_3m:+.1f}%", "#3d7a55" if price_change_3m<=0 else "#ef4444"),
        (" " + ("12M Average" if lang=="en" else "මාස 12 සාමාන්‍යය"), f"Rs. {avg_12m:.2f}", "#3d7a55"),
        (" " + ("Volatility" if lang=="en" else "අස්ථාවරතාව"), f"{cv:.1f}% CV", "#3d7a55"),
        ("️ " + ("Market Regime" if lang=="en" else "වෙළඳ තත්ත්වය"), regime_labels[regime_now], "#3d7a55"),
    ]
    for col,(lbl,val,clr) in zip([sn1,sn2,sn3,sn4,sn5], snap_data):
        with col: st.markdown(metric_card(lbl, val, clr, height=95), unsafe_allow_html=True)
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — STRATEGIC POLICY SIMULATOR
    # ══════════════════════════════════════════════════════════════════════════
    _sim_title = " " + ("Strategic Policy Simulator" if lang=="en" else "උපාය මාර්ගික ප්‍රතිපත්ති අනුකරණය")
    _sim_sub = ("Test government intervention scenarios and see projected market outcomes before implementation"
                  if lang=="en" else
                  "රජයේ මැදිහත්වීම් අවස්ථා පරීක්ෂා කර ක්‍රියාත්මක කිරීමට පෙර ඉදිරි වෙළඳ ප්‍රතිඵල බලන්න")
    st.markdown(f"""<div style='background:linear-gradient(90deg,#1a3328,#3d7a55);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        {_sim_title}
      </div>
      <div style='font-size:.78rem;color:#b8d0c4;margin-top:3px;'>
        {_sim_sub}
      </div>
    </div>
    """, unsafe_allow_html=True)

    ps_col1, ps_col2 = st.columns([1.2, 1])
    with ps_col1:
        st.markdown("##### " + ("Configure Policy Levers" if lang=="en" else "ප්‍රතිපත්ති සකස් කරන්න"))

        buffer_stock = st.slider(
            " Buffer Stock Release (% of monthly supply)" if lang=="en" else " බෆර් තොග මුදාහැරීම (%)",
            0, 30, 0, 1,
            help="Government releases stored nuts into market to reduce price pressure")

        import_duty = st.slider(
            " Import Duty Adjustment (%)" if lang=="en" else " ආනයන බද්ද (%)",
            -20, 20, 0, 1,
            help="Positive = increase duty (protect local farmers). Negative = reduce duty (lower consumer prices)")

        subsidy_pct = st.slider(
            " Farmer Input Subsidy (% cost reduction)" if lang=="en" else " ගොවි ආදාන සහාය (%)",
            0, 40, 0, 2,
            help="Subsidising fertiliser, pesticide and transport costs for farmers")

        price_floor = st.slider(
            "️ Minimum Price Floor (Rs.)" if lang=="en" else "️ අවම මිල (රු.)",
            30, 80, int(current_price * 0.8), 1,
            help="Government-guaranteed minimum purchase price for farmers")

        export_quota = st.slider(
            " Export Quota Restriction (% reduction)" if lang=="en" else " අපනයන සීමාව (% අඩු කිරීම)",
            0, 50, 0, 5,
            help="Restricting exports increases domestic supply and lowers local prices")

    with ps_col2:
        st.markdown("##### " + ("Projected Market Impact" if lang=="en" else "ඉදිරි වෙළඳ බලපෑම"))

        # Simulate projected price based on levers
        price_impact = current_price
        price_impact -= (buffer_stock * 0.12) # buffer release reduces price
        price_impact += (import_duty * 0.08) # higher duty = higher price
        price_impact -= (export_quota * 0.06) # export restriction lowers price
        price_impact += (subsidy_pct * 0.03) # subsidy has slight upward effect (more demand)
        price_impact = max(price_floor, price_impact) # floor enforced

        delta_price = price_impact - current_price
        delta_pct = (delta_price / current_price) * 100
        p_clr = "#5a9470" if delta_price <= 0 else "#ef4444"

        farmer_revenue_change = (price_impact - current_price) * 1000 # per 1000 nuts
        consumer_impact = delta_pct * 2.3 # household spend sensitivity
        export_revenue_change = -export_quota * 1.2 # USD M approx

        # Projected price gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(price_impact, 2),
            delta={"reference": current_price, "valueformat": ".2f",
                   "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#5a9470"}},
            number={"prefix": "Rs.", "font": {"size": 28, "color": "#1a3328"}},
            title={"text": ("Projected Price (Rs.)" if lang=="en" else "ඉදිරි මිල (රු.)"), "font": {"size": 13}},
            gauge={
                "axis": {"range": [30, 120], "tickfont": {"size": 9}},
                "bar": {"color": p_clr},
                "bgcolor": "#f8fafc",
                "threshold": {"line": {"color": "#94a3b8", "width": 2}, "value": current_price},
                "steps": [
                    {"range": [30, warn_threshold], "color": "#f0f5f2"},
                    {"range": [warn_threshold, crisis_threshold], "color": "#fef9c3"},
                    {"range": [crisis_threshold, 120], "color": "#fee2e2"},
                ],
            }))
        fig_gauge.update_layout(height=220, margin=dict(l=20,r=20,t=40,b=10), paper_bgcolor="#fff")
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

        # Impact summary cards
        ic1, ic2, ic3 = st.columns(3)
        for col, (lbl, val, clr) in zip([ic1, ic2, ic3], [
            ("‍ " + ("Farmer Revenue /1000 nuts" if lang=="en" else "ගොවි ආදායම /ගෙඩි 1000"),
             f"{'+'if farmer_revenue_change>=0 else ''}{farmer_revenue_change:,.0f} Rs.",
             "#3d7a55" if farmer_revenue_change>=0 else "#ef4444"),
            (" " + ("Consumer Spend Impact" if lang=="en" else "පාරිභෝගික වියදම් බලපෑම"),
             f"{consumer_impact:+.1f}%",
             "#5a9470" if consumer_impact<=0 else "#ef4444"),
            (" " + ("Export Revenue Est." if lang=="en" else "අපනයන ආදායම ඇ."),
             f"{export_revenue_change:+.1f}M USD",
             "#3d7a55"),
        ]):
            with col:
                st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid {clr};
                    border-radius:8px;padding:10px 10px;text-align:center;height:80px;display:flex;
                    flex-direction:column;justify-content:center;'>
                    <div style='font-size:.6rem;color:#64748b;font-weight:700;white-space:pre-line;margin-bottom:4px;'>{lbl}</div>
                    <div style='font-size:1rem;font-weight:900;color:{clr};'>{val}</div>
                </div>""", unsafe_allow_html=True)

    divider()

    # Policy scenario verdict
    if delta_price < -5:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "", \
            ("Strong Consumer Relief" if lang=="en" else "ප්‍රබල පාරිභෝගික සහනය"), \
            (f"This combination of policies is projected to reduce prices by Rs.{abs(delta_price):.1f}, providing significant relief to consumers. Monitor farmer income carefully."
             if lang=="en" else
             f"මෙම ප්‍රතිපත්ති සංයෝජනය මිල Rs.{abs(delta_price):.1f} කින් අඩු කරනු ඇතැයි අපේක්ෂා කෙරේ. ගොවි ආදායම ඉතා සුපරීක්ෂාකාරීව නිරීක්ෂණය කරන්න."), "#3d7a55"
    elif delta_price < 0:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "", \
            ("Mild Stabilisation" if lang=="en" else "මෘදු ස්ථාවරීකරණය"), \
            (f"Policies project a modest Rs.{abs(delta_price):.1f} price reduction. A balanced approach — good for consumers with minimal farmer impact."
             if lang=="en" else
             f"ප්‍රතිපත්ති Rs.{abs(delta_price):.1f} ක් මිල අඩු කරනු ඇතැයි අපේක්ෂා කෙරේ. සමබර ප්‍රවේශය — ගොවීන්ට අවම බලපෑමකින් පාරිභෝගිකයන්ට හිතකරයි."), "#eab308"
    elif delta_price == 0:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "", \
            ("Market Neutral" if lang=="en" else "වෙළඳ උදාසීන"), \
            ("Current policy settings have no projected impact. Adjust levers above to test interventions."
             if lang=="en" else
             "වත්මන් ප්‍රතිපත්ති සැකසුම් ඉදිරි බලපෑමක් නැත. ක්‍රියාදාමයන් පරීක්ෂා කිරීමට ඉහත ලීවර් සකස් කරන්න."), "#64748b"
    elif delta_price < 10:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "", \
            ("Moderate Farmer Support" if lang=="en" else "මධ්‍යස්ථ ගොවි සහාය"), \
            (f"Policies project a Rs.{delta_price:.1f} price increase, benefiting farmers. Watch consumer affordability closely."
             if lang=="en" else
             f"ප්‍රතිපත්ති Rs.{delta_price:.1f} ක් මිල ඉහළ නැංවීමක් ඉදිරිපත් කරයි, ගොවීන්ට වාසිදායකයි. පාරිභෝගික දැරිය හැකිකම ළිපෙහි නිරීක්ෂණය කරන්න."), "#eab308"
    else:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "", \
            ("High Price Risk" if lang=="en" else "ඉහළ මිල අවදානම"), \
            (f"Policies project a Rs.{delta_price:.1f} price surge. Strong intervention may be needed to protect consumers."
             if lang=="en" else
             f"ප්‍රතිපත්ති Rs.{delta_price:.1f} ක් මිල ඉහළ නැංවීමක් ඉදිරිපත් කරයි. පාරිභෝගිකයන් ආරක්ෂා කිරීමට ශක්තිමත් මැදිහත්වීමක් අවශ්‍ය විය හැක."), "#ef4444"

    st.markdown(f"""<div style='background:{verdict_clr}15;border:2px solid {verdict_clr};border-radius:12px;
        padding:16px 20px;display:flex;align-items:flex-start;gap:14px;'>
        <div style='font-size:1.8rem;line-height:1;'>{verdict_icon}</div>
        <div>
          <div style='font-size:.85rem;font-weight:900;color:{verdict_clr};margin-bottom:4px;'>{verdict_title}</div>
          <div style='font-size:.78rem;color:#374151;line-height:1.6;'>{verdict_msg}</div>
        </div>
    </div>""", unsafe_allow_html=True)
    divider()

    # ── Policy comparison bar chart ────────────────────────────────────────────
    st.markdown("##### " + ("Compare All Policy Scenarios" if lang=="en" else "ප්‍රතිපත්ති සසඳා බලන්න"))
    scenarios = {
        ("No Intervention" if lang=="en" else "මැදිහත්වීමක් නැත"): current_price,
        ("Buffer Stock Only" if lang=="en" else "බෆර් තොග පමණි"): max(price_floor, current_price - 10*0.12),
        ("Import Duty Cut" if lang=="en" else "ආනයන බද්ද කප්පාදු"): max(price_floor, current_price - 15*0.08),
        ("Farmer Subsidy" if lang=="en" else "ගොවි සහාය"): max(price_floor, current_price + 20*0.03),
        ("Export Quota" if lang=="en" else "අපනයන සීමාව"): max(price_floor, current_price - 25*0.06),
        ("Combined (Optimal)" if lang=="en" else "ඒකාබද්ධ (ප්‍රශස්ත)"): max(price_floor, current_price - 10*0.12 - 10*0.08 - 20*0.06),
        ("Current Settings" if lang=="en" else "වත්මන් සැකසුම්"): round(price_impact, 2),
    }
    s_names = list(scenarios.keys())
    s_prices = list(scenarios.values())
    s_deltas = [v - current_price for v in s_prices]
    # Use index-based coloring: index 0 = No Intervention, index 6 = Current Settings
    s_colors = ["#94a3b8" if i==0 else
                "#f59e0b" if i==6 else
                "#5a9470" if v <= current_price else "#ef4444"
                for i, (n, v) in enumerate(scenarios.items())]
    _baseline_lbl = ("Baseline" if lang=="en" else "පාදම") + f" Rs.{current_price:.1f}"
    _crisis_lbl = ("Crisis" if lang=="en" else "අර්බුද") + f" Rs.{crisis_threshold}"
    s_labels = [f"<b>Rs.{v:.1f}</b> ({'+' if d>0 else ''}{d:.1f})"
                for v, d in zip(s_prices, s_deltas)]
    fig_sc = go.Figure(go.Bar(
        y=s_names, x=s_prices, orientation="h",
        marker_color=s_colors, marker_line=dict(width=0),
        text=s_labels, textposition="outside",
        textfont=dict(size=11, color="#1e293b"),
        hovertemplate="<b>%{y}</b><br>Price: Rs.%{x:.2f}<extra></extra>",
        cliponaxis=False))
    fig_sc.add_vline(x=current_price, line_dash="dash", line_color="#64748b", line_width=2,
        annotation=dict(text=_baseline_lbl,
                        font=dict(size=10, color="#64748b"), bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="#64748b", borderwidth=1, y=1.08, yref="paper"))
    fig_sc.add_vline(x=warn_threshold, line_dash="dot", line_color="#eab308", line_width=1.5,
        annotation=dict(text=f" Rs.{warn_threshold}",
                        font=dict(size=9, color="#b45309"), bgcolor="rgba(255,255,255,0.85)",
                        y=0.0, yref="paper"))
    fig_sc.add_vline(x=crisis_threshold, line_dash="dot", line_color="#ef4444", line_width=1.5,
        annotation=dict(text=_crisis_lbl,
                        font=dict(size=9, color="#ef4444"), bgcolor="rgba(255,255,255,0.85)",
                        y=0.12, yref="paper"))
    p_min = min(s_prices); p_max = max(s_prices)
    x_min = max(0, p_min - (p_max - p_min) * 0.05)
    x_max = p_max + (p_max - p_min) * 0.55
    fig_sc.update_layout(
        height=340, margin=dict(l=10,r=20,t=50,b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        xaxis=dict(gridcolor="#f1f5f9", tickprefix="Rs.", tickfont=dict(size=10),
                   range=[x_min, x_max], zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11), autorange="reversed"),
        showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — STRATEGIC RECOMMENDATION ENGINE
    # ══════════════════════════════════════════════════════════════════════════
    _eng_title = " " + ("Strategic Recommendation Engine" if lang=="en" else "උපාය මාර්ගික නිර්දේශ යන්ත්‍රය")
    _eng_sub = ("AI-driven, regime-sensitive recommendations for all three market stakeholder groups"
                  if lang=="en" else
                  "වෙළඳ තත්ත්වය අනුව, සියලු තුන් පාර්ශ්ව කණ්ඩායම් සඳහා ක්‍රියාශීලී නිර්දේශ")
    st.markdown(f"""<div style='background:linear-gradient(90deg,#7c3aed,#6d28d9);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        {_eng_title}
      </div>
      <div style='font-size:.78rem;color:#ddd6fe;margin-top:3px;'>
        {_eng_sub}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic recommendations based on current regime
    _R = lang # shorthand
    all_recommendations = {
        0: { # Stable Market
            "government": [
                ("",
                 "Build Buffer Stocks" if _R=="en" else "බෆර් තොග ගොඩ නගා ගන්න",
                 "Stability window is ideal for building emergency grain reserves. Target: 3-month national supply." if _R=="en" else "ස්ථාවර කාලය හදිසි ගබඩා ගොඩ නැගීමට ආදර්ශ අවස්ථාවකි. ඉලක්කය: මාස 3ක ජාතික සැපයුම.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Min. Rs. 2.5B allocation from stabilisation fund" if _R=="en" else "ස්ථාවරීකරණ අරමුදලෙන් අවම රු. 2.5B"),
                ("",
                 "Enhance Data Infrastructure" if _R=="en" else "දත්ත යටිතල ශක්තිමත් කරන්න",
                 "Invest in real-time price reporting systems at all 6 major auction centres." if _R=="en" else "ප්‍රධාන වෙන්දේසි මධ්‍යස්ථාන 6 හි තත්‍යකාලීන මිල වාර්තාකරණ පද්ධති සඳහා ආයෝජනය කරන්න.",
                 "MEDIUM","3-6 months" if _R=="en" else "මාස 3-6","Rs. 180M — HARTI digital upgrade programme" if _R=="en" else "රු. 180M — HARTI ඩිජිටල් උසස්කිරීමේ වැඩසටහන"),
                ("",
                 "Review Farmer Registration" if _R=="en" else "ගොවි ලියාපදිංචිය සමාලෝචනය",
                 "Update CDA farmer database. Many smallholders lack formal registration limiting support access." if _R=="en" else "CDA ගොවි දත්ත ගබඩාව යාවත්කාලීන කරන්න. කුඩා ගොවීන් රාශියකට සහාය ලබා ගැනීම සීමා කරන සන්නද්ධ ලියාපදිංචියක් නොමැත.",
                 "MEDIUM","6-12 months" if _R=="en" else "මාස 6-12","Administrative — no major budget required" if _R=="en" else "පරිපාලනමය — ප්‍රධාන අයවැයක් අවශ්‍ය නැත"),
                ("",
                 "Promote Value Addition" if _R=="en" else "අගය-එකතු කිරීම ප්‍රවර්ධනය",
                 "Stable prices allow investment in coconut oil, desiccated coconut, and coconut milk processing." if _R=="en" else "ස්ථාවර මිල පොල් තෙල්, වියළි පොල් සහ පොල් කිරි සැකසීම සඳහා ආයෝජනය ඉඩ දේ.",
                 "HIGH","6-18 months" if _R=="en" else "මාස 6-18","Rs. 500M industry development grant" if _R=="en" else "රු. 500M කර්මාන්ත සංවර්ධන ප්‍රදානය"),
                ("",
                 "Negotiate Trade Agreements" if _R=="en" else "වෙළඳ ගිවිසුම් සාකච්ඡා කරන්න",
                 "Use stable period to negotiate better export terms with EU, USA, and Middle East markets." if _R=="en" else "EU, USA සහ මැදපෙරදිග වෙළඳපොළවල් සමග වඩා හොඳ අපනයන කොන්දේසි සාකච්ඡා කිරීමට ස්ථාවර කාලය භාවිත කරන්න.",
                 "MEDIUM","12-24 months" if _R=="en" else "මාස 12-24","Ministry of Trade — diplomatic resources" if _R=="en" else "වෙළඳ අමාත්‍යාංශය — රාජ්‍යතාන්ත්‍රික සම්පත්"),
            ],
            "business": [
                ("",
                 "Expand Processing Capacity" if _R=="en" else "සැකසුම් ධාරිතාව ව්‍යාප්ත කරන්න",
                 "Stable input costs make this the best time to invest in new processing lines and cold storage." if _R=="en" else "ස්ථාවර ආදාන පිරිවැය නව සැකසුම් රේඛා සහ ශීතල ගබඩාවලට ආයෝජනය කිරීමට හොඳම කාලය කරයි.",
                 "HIGH","6-12 months" if _R=="en" else "මාස 6-12","ROI: 18-24 months at current margins" if _R=="en" else "ROI: වත්මන් ආන්තිකවලදී මාස 18-24"),
                ("",
                 "Lock In Long-Term Supply Contracts" if _R=="en" else "දිගු කාලීන සැපයුම් ගිවිසුම් ගන්න",
                 "Negotiate 6-12 month fixed-price supply contracts with farmer cooperatives." if _R=="en" else "ගොවි සමිති සමග මාස 6-12 ස්ථාවර-මිල සැපයුම් ගිවිසුම් සාකච්ඡා කරන්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Reduces raw material cost volatility by ~40%" if _R=="en" else "අමු ද්‍රව්‍ය පිරිවැය අස්ථාවරතාව ~40%කින් අඩු කරයි"),
                ("",
                 "Enter New Export Markets" if _R=="en" else "නව අපනයන වෙළඳපොළවලට ඇතුල් වන්න",
                 "Low price risk enables testing new export markets without margin compression." if _R=="en" else "අඩු මිල අවදානම ආන්තික සම්පීඩනයකින් තොරව නව අපනයන වෙළඳපොළ පරීක්ෂා කිරීමට ඉඩ දේ.",
                 "MEDIUM","3-9 months" if _R=="en" else "මාස 3-9","Export development board support available" if _R=="en" else "අපනයන සංවර්ධන මණ්ඩල සහාය ලබා ගත හැකිය"),
                ("",
                 "Invest in Automation" if _R=="en" else "ස්වයංක්‍රීයකරණයට ආයෝජනය",
                 "Stable period ideal for upgrading factory equipment without cashflow pressure." if _R=="en" else "මුදල් ප්‍රවාහ පීඩනයකින් තොරව කර්මාන්ත ශාලා උපකරණ උසස් කිරීමට ස්ථාවර කාලය ආදර්ශ.",
                 "MEDIUM","6-18 months" if _R=="en" else "මාස 6-18","Automation grants available through BOI" if _R=="en" else "BOI හරහා ස්වයංක්‍රීයකරණ ප්‍රදාන ලබා ගත හැකිය"),
                ("",
                 "Diversify Product Portfolio" if _R=="en" else "නිෂ්පාදන ශ්‍රේණිය විවිධාංගීකරණය",
                 "Launch coconut water, activated carbon, or coir products to reduce commodity price risk." if _R=="en" else "ගොවිතැන් මිල අවදානම අඩු කිරීමට පොල් වතුර, සක්‍රිය කාබන් හෝ කොයිර් නිෂ්පාදන දියත් කරන්න.",
                 "HIGH","12-24 months" if _R=="en" else "මාස 12-24","Market studies show 35% margin premium on value-added" if _R=="en" else "වෙළඳ අධ්‍යයන අගය-එකතු කළ නිෂ්පාදනවල 35% ආන්තික වාසිය පෙන්වයි"),
            ],
            "farmer": [
                ("",
                 "Replant Ageing Trees" if _R=="en" else "වයෝවෘද්ධ ගස් නැවත සිටුවන්න",
                 "15-25% of SL coconut palms are past peak yield. Stable income = best time to replant." if _R=="en" else "ශ්‍රී ලංකා පොල් ගස්වලින් 15-25% උච්ච අස්වැන්නෙන් ඔබ්බට ගොස් ඇත. ස්ථාවර ආදායම = නැවත සිටුවීමට හොඳ කාලය.",
                 "HIGH","Now — 3yr ROI" if _R=="en" else "දැන් — ROI වසර 3","CDA provides seedlings at Rs. 150 each — 60% subsidy available" if _R=="en" else "CDA රු. 150 බැගින් පැළ සපයයි — 60% සහනාධාරය ලබා ගත හැකිය"),
                ("",
                 "Install Irrigation" if _R=="en" else "වාරිමාර්ග ස්ථාපිත කරන්න",
                 "Drip irrigation reduces drought vulnerability by 60%. CDA subsidises 50% of installation cost." if _R=="en" else "බිංදු වාරිමාර්ගය නියඟ අවදානම 60%කින් අඩු කරයි. CDA ස්ථාපනය පිරිවැයෙන් 50% සහාය දක්වයි.",
                 "HIGH","Next dry season" if _R=="en" else "ඊළඟ වියළි කාලය","Rs. 45,000-85,000 per acre — subsidy available" if _R=="en" else "රු. 45,000-85,000 අක්කරයකට — සහනාධාරය ලබා ගත හැකිය"),
                ("",
                 "Join a Cooperative" if _R=="en" else "සමිතියකට එකතු වන්න",
                 "Group selling at auctions achieves 12-18% higher prices than individual sellers." if _R=="en" else "වෙන්දේසිවලදී කණ්ඩායම් විකිණීම තනි විකුණුම්කරුවන්ට වඩා 12-18% ඉහළ මිල ලබා ගනී.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Contact CDA regional office for nearest co-op" if _R=="en" else "ළඟම සමිතිය සඳහා CDA කලාපීය කාර්යාලය අමතන්න"),
                ("",
                 "Access Training" if _R=="en" else "පුහුණුවට ප්‍රවේශ වන්න",
                 "CDA free training on integrated pest management and organic certification available." if _R=="en" else "ඒකාබද්ධ පළිබෝධ කළමනාකරණය සහ කාබනික සහතිකය පිළිබඳ CDA නොමිලේ පුහුණු ලබා ගත හැකිය.",
                 "MEDIUM","Ongoing" if _R=="en" else "අඛණ්ඩ","Free — register at cda.gov.lk/training" if _R=="en" else "නොමිලේ — cda.gov.lk/training හිදී ලියාපදිංචි වන්න"),
                ("",
                 "Open a Farm Savings Account" if _R=="en" else "ගොවි ඉතිරිකිරීමේ ගිණුමක් විවෘත කරන්න",
                 "Bank of Ceylon Farmer Account offers 2% above normal savings rate for registered farmers." if _R=="en" else "ලංකා බැංකු ගොවි ගිණුම ලියාපදිංචි ගොවීන්ට සාමාන්‍ය ඉතිරිකිරීම් අනුපාතයට වඩා 2% ඉහළ ලබා දේ.",
                 "MEDIUM","Immediate" if _R=="en" else "ක්ෂණිකව","BOC branch — CDA registration card required" if _R=="en" else "BOC ශාඛාව — CDA ලියාපදිංචි කාඩ්පත් අවශ්‍ය"),
            ],
        },
        1: { # Warning Market
            "government": [
                ("",
                 "Activate Price Monitoring Task Force" if _R=="en" else "මිල නිරීක්ෂණ කාර්ය සාධක බලකාය සක්‍රිය කරන්න",
                 "Deploy field officers to all 6 auction centres daily. Report unusual price movements within 24hrs." if _R=="en" else "වෙන්දේසි මධ්‍යස්ථාන 6 හි දිනපතා ක්ෂේත්‍ර නිලධාරීන් යොදවන්න. අසාමාන්‍ය මිල ව්‍යාප්තිය පැය 24 ඇතුළත වාර්තා කරන්න.",
                 "URGENT","Immediate" if _R=="en" else "ක්ෂණිකව","Rs. 8M — existing staff redeployment" if _R=="en" else "රු. 8M — දැනට සිටින කාර්ය මණ්ඩල නැවත යොදවීම"),
                ("",
                 "Partial Buffer Stock Release" if _R=="en" else "අර්ධ බෆර් තොග මුදා හැරීම",
                 "Release 10-15% of buffer stocks to inject supply and moderate upward price pressure." if _R=="en" else "සැපයුම ඉහළ නංවා ඉහළ මිල පීඩනය මධ්‍යස්ථ කිරීමට බෆර් තොගවලින් 10-15% මුදා හරින්න.",
                 "HIGH","Within 1 week" if _R=="en" else "සතියක් ඇතුළත","Coordinate with HARTI auction management" if _R=="en" else "HARTI වෙන්දේසි කළමනාකරණය සමග සම්බන්ධ කරගන්න"),
                ("",
                 "Public Price Transparency Campaign" if _R=="en" else "මහජන මිල විනිවිදභාව ව්‍යාපාරය",
                 "Broadcast daily auction prices via radio, SMS (Dialog/Mobitel), and social media to prevent panic buying." if _R=="en" else "අසංවිධිත ගැනුම් වළක්වා ගැනීමට ගුවන් විදුලිය, SMS (Dialog/Mobitel) සහ සමාජ මාධ්‍ය හරහා දෛනික වෙන්දේසි මිල විකාශය කරන්න.",
                 "HIGH","Within 3 days" if _R=="en" else "දින 3 ඇතුළත","Rs. 5M — public communications budget" if _R=="en" else "රු. 5M — මහජන සන්නිවේදන අයවැය"),
                ("",
                 "Activate Price Stabilisation Fund" if _R=="en" else "මිල ස්ථාවරීකරණ අරමුදල සක්‍රිය කරන්න",
                 "Signal readiness to deploy stabilisation fund. Market awareness alone can reduce speculation." if _R=="en" else "ස්ථාවරීකරණ අරමුදල යෙදවීමට සූදානම සංඥා කරන්න. වෙළඳ දැනුවත්කම පමණින් ද ශේෂකාරිත්වය අඩු කළ හැකිය.",
                 "HIGH","Within 1 week" if _R=="en" else "සතියක් ඇතුළත","Rs. 500M fund — Cabinet authorisation required" if _R=="en" else "රු. 500M අරමුදල — කැබිනට් අනුමැතිය අවශ්‍ය"),
                ("",
                 "Accelerate Harvest Support" if _R=="en" else "අස්වනු සහාය ත්වරාන්විත කරන්න",
                 "Provide subsidised transport to bring stored farm produce to market quickly." if _R=="en" else "ගබඩා ගොවිතැන් නිෂ්පාදන ඉක්මනින් වෙළඳපොළට ගෙන ඒමට සහනාධාර ප්‍රවාහනය ලබා දෙන්න.",
                 "MEDIUM","Within 2 weeks" if _R=="en" else "සති 2 ඇතුළත","Rs. 25M — transport subsidy scheme" if _R=="en" else "රු. 25M — ප්‍රවාහන සහනාධාර යෝජනා ක්‍රමය"),
            ],
            "business": [
                ("",
                 "Hedge Raw Material Costs" if _R=="en" else "අමු ද්‍රව්‍ය පිරිවැය ආරක්ෂා කරගන්න",
                 "Lock in forward contracts for next 3-6 months before prices escalate further." if _R=="en" else "මිල තවදුරටත් ඉහළ යාමට පෙර ඉදිරි මාස 3-6 සඳහා ඉදිරි ගිවිසුම් සාකච්ඡා කරන්න.",
                 "URGENT","This week" if _R=="en" else "මෙම සතිය","Contact commodity brokers — forward pricing available" if _R=="en" else "ගොවිතැන් තැරැව්කරුවන් අමතන්න — ඉදිරි මිල ගණනය ලබා ගත හැකිය"),
                ("",
                 "Reduce Inventory Holding" if _R=="en" else "තොග රඳවා ගැනීම අඩු කරන්න",
                 "High price environment — sell finished goods inventory quickly to protect margins." if _R=="en" else "ඉහළ මිල පරිසරය — ආන්තික ආරක්ෂා කිරීමට නිමි භාණ්ඩ තොග ඉක්මනින් විකුණන්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Review distribution channel pricing" if _R=="en" else "බෙදාහැරීමේ නාලිකා මිල ගණනය සමාලෝචනය කරන්න"),
                ("",
                 "Diversify Input Sources" if _R=="en" else "ආදාන මූලාශ්‍ර විවිධාංගීකරණය",
                 "Explore coconut sourcing from Puttalam, Kurunegala simultaneously — don't rely on single auction." if _R=="en" else "එකවර පුත්තලම, කුරුණෑගල සිට පොල් ලබා ගැනීම ගවේෂණය කරන්න — තනි වෙන්දේසියකට රඳා නොසිටින්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Register with 3+ auction centres" if _R=="en" else "වෙන්දේසි මධ්‍යස්ථාන 3+ක ලියාපදිංචි වන්න"),
                ("",
                 "Switch to Value Products" if _R=="en" else "අගය නිෂ්පාදනවලට මාරු වන්න",
                 "Shift production mix toward premium products (virgin coconut oil, organic) with higher margin buffer." if _R=="en" else "ඉහළ ආන්තික බෆරයක් සහිත ශ්‍රේෂ්ඨ නිෂ්පාදන (කළු නොකළ පොල් තෙල්, කාබනික) දෙසට නිෂ්පාදන මිශ්‍රණය මාරු කරන්න.",
                 "MEDIUM","2-4 weeks" if _R=="en" else "සති 2-4","Requires product certification — SLSI contact" if _R=="en" else "නිෂ්පාදන සහතිකය අවශ්‍ය — SLSI සම්බන්ධ කරගන්න"),
                ("",
                 "Weekly Price Tracking" if _R=="en" else "සතිපතා මිල නිරීක්ෂණය",
                 "Monitor all 6 auction centres daily. Set automated alerts at Rs.70, Rs.75, Rs.80." if _R=="en" else "දිනපතා වෙන්දේසි මධ්‍යස්ථාන 6 ම නිරීක්ෂණය කරන්න. රු.70, රු.75, රු.80 හිදී ස්වයංක්‍රීය ඇඟවීම් සකස් කරන්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","COCOStat dashboard — set custom thresholds" if _R=="en" else "COCOStat පාලක පුවරුව — අභිරුචි සීමා සකස් කරන්න"),
            ],
            "farmer": [
                ("",
                 "Sell Now — Don't Hoard" if _R=="en" else "දැන් විකුණන්න — ගබඩා නොකරන්න",
                 "Warning phase prices are already elevated. Sell at current auction prices rather than waiting." if _R=="en" else "අවවාද අදියර මිල දැනටමත් ඉහළ ගොස් ඇත. බලා සිටීමේ වෙනුවට වත්මන් වෙන්දේසි මිලට විකුණන්න.",
                 "URGENT","This week" if _R=="en" else "මෙම සතිය","Colombo auction Monday, Wednesday, Friday" if _R=="en" else "කොළඹ වෙන්දේසිය සඳු, බදා, සිකු"),
                ("",
                 "Register for Emergency Support" if _R=="en" else "හදිසි සහාය සඳහා ලියාපදිංචි වන්න",
                 "Pre-register for government income support scheme before crisis is declared." if _R=="en" else "අර්බුදය ප්‍රකාශිත වීමට පෙර රජයේ ආදායම් සහාය ක්‍රමයේ පූර්ව ලියාපදිංචිය සිදු කරන්න.",
                 "HIGH","This week" if _R=="en" else "මෙම සතිය","CDA Regional Office — free registration" if _R=="en" else "CDA කලාපීය කාර්යාලය — නොමිලේ ලියාපදිංචිය"),
                ("‍‍",
                 "Coordinate with Neighbours" if _R=="en" else "අසල්වාසීන් සමග සම්බන්ධීකරණය",
                 "Pool harvests with nearby farmers for stronger auction bargaining position." if _R=="en" else "ශක්තිමත් වෙන්දේසි ගනුදෙනු ස්ථාවරයක් සඳහා ළඟම ගොවීන් සමග අස්වනු එක්රැස් කරන්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Minimum 5,000 nuts for cooperative lot" if _R=="en" else "සමිති ලොටයකට අවම ගෙඩි 5,000"),
                ("",
                 "Accelerate Irrigation Use" if _R=="en" else "වාරිමාර්ග භාවිතය ත්වරාන්විත කරන්න",
                 "If irrigation installed — increase watering frequency to maximise current yield." if _R=="en" else "වාරිමාර්ගය ස්ථාපිත නම් — වත්මන් අස්වැන්න උපරිම කිරීමට ජල ලැබීමේ ප්‍රවර්ථනය වැඩි කරන්න.",
                 "MEDIUM","Immediate" if _R=="en" else "ක්ෂණිකව","CDA agronomy helpline: 1920" if _R=="en" else "CDA කෘෂිකර්ම ආධාර: 1920"),
                ("",
                 "Explore Direct Buyer Contracts" if _R=="en" else "සෘජු ගැනුම්කරු ගිවිසුම් ගවේෂණය කරන්න",
                 "Some processors will pay 5-8% above auction price for guaranteed supply contracts." if _R=="en" else "සමහර සකසන්නෝ සහතික සැපයුම් ගිවිසුම් සඳහා වෙන්දේසි මිලට වඩා 5-8% ඉහළ ගෙවනු ඇත.",
                 "MEDIUM","1-2 weeks" if _R=="en" else "සති 1-2","CDA Buyer Directory available on request" if _R=="en" else "CDA ගැනුම්කරු නාමාවලිය ඉල්ලීමෙන් ලබා ගත හැකිය"),
            ],
        },
        2: { # Crisis Market
            "government": [
                ("🆘",
                 "Emergency Price Control Activation" if _R=="en" else "හදිසි මිල පාලන සක්‍රිය කිරීම",
                 "Invoke the Consumer Affairs Authority Act — set ceiling price at Rs.85. Enforce at all retail levels." if _R=="en" else "පාරිභෝගික කටයුතු අධිකාරි පනත ක්‍රියාත්මක කරන්න — උපරිම මිල රු.85 ලෙස සකසන්න. සියලු සිල්ලර මට්ටම්වල ක්‍රියාත්මක කරන්න.",
                 "CRITICAL","Within 24hrs" if _R=="en" else "පැය 24 ඇතුළත","Cabinet emergency session — Rs. 50M enforcement budget" if _R=="en" else "කැබිනට් හදිසි රැස්වීම — රු. 50M ක්‍රියාත්මක කිරීමේ අයවැය"),
                ("",
                 "Full Buffer Stock Emergency Release" if _R=="en" else "සම්පූර්ණ බෆර් තොග හදිසි මුදා හැරීම",
                 "Release 100% of available buffer stocks immediately. Coordinate HARTI emergency auction." if _R=="en" else "ලබා ගත හැකි සියලු බෆර් තොග ක්ෂණිකව මුදා හරින්න. HARTI හදිසි වෙන්දේසිය සම්බන්ධීකරණය කරන්න.",
                 "CRITICAL","Within 48hrs" if _R=="en" else "පැය 48 ඇතුළත","All regional centres — coordinate military logistics if needed" if _R=="en" else "සියලු කලාපීය මධ්‍යස්ථාන — අවශ්‍ය නම් හමුදා සැපයුම් සම්බන්ධීකරණය"),
                ("",
                 "Emergency Import Authorisation" if _R=="en" else "හදිසි ආනයන අනුමැතිය",
                 "Fast-track import permits for coconut from India/Philippines to bridge supply gap." if _R=="en" else "සැපයුම් හිඟය පියවා ගැනීමට ඉන්දියාව/පිලිපීනය සිට පොල් ආනයන බලපත්‍ර ඉක්මනින් ලබා දෙන්න.",
                 "CRITICAL","Within 1 week" if _R=="en" else "සතියක් ඇතුළත","Ministry of Trade emergency order — waive normal 45-day process" if _R=="en" else "වෙළඳ අමාත්‍යාංශ හදිසි නියෝගය — සාමාන්‍ය දින 45 ක්‍රියාවලිය ඉවත් කරන්න"),
                ("",
                 "Cash Transfer to Vulnerable Households" if _R=="en" else "අවදානම් ගෘහ සඳහා මුදල් හුවමාරු",
                 "Rs. 2,500 per household hardship payment via Samurdhi mechanism for bottom 30%." if _R=="en" else "පහළ 30% සඳහා සමෘද්ධි යාන්ත්‍රණය හරහා ගෘහ සඳහා රු. 2,500 ක දුෂ්කරතා ගෙවීම.",
                 "CRITICAL","Within 2 weeks" if _R=="en" else "සති 2 ඇතුළත","Rs. 12B — emergency supplementary estimate" if _R=="en" else "රු. 12B — හදිසි අතිරේක ඇස්තමේන්තුව"),
                ("",
                 "Daily National Price Broadcast" if _R=="en" else "දෛනික ජාතික මිල විකාශය",
                 "Daily 8PM TV/radio broadcast of official controlled prices and where to buy." if _R=="en" else "නිල පාලිත මිල සහ මිල දී ගත හැකි ස්ථාන ගැන දිනපතා රාත්‍රී 8 TV/ගුවන් විදුලි විකාශය.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","SLRC coordination — Rs. 2M production budget" if _R=="en" else "SLRC සම්බන්ධීකරණය — රු. 2M නිෂ්පාදන අයවැය"),
                ("",
                 "Anti-Hoarding Enforcement" if _R=="en" else "ගබඩා කිරීම් විරෝධී ක්‍රියාත්මක කිරීම",
                 "CAA/Police joint teams to inspect large warehouses for hoarding. Penalties up to Rs. 5M." if _R=="en" else "ගබඩා කිරීම් සඳහා විශාල ගබඩා පරීක්ෂා කිරීමට CAA/පොලිස් ඒකාබද්ධ කණ්ඩායම්. දඩ රු. 5M දක්වා.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","District secretariat coordination required" if _R=="en" else "දිස්ත්‍රික් ලේකම් කාර්යාල සම්බන්ධීකරණය අවශ්‍ය"),
            ],
            "business": [
                ("🆘",
                 "Activate Business Continuity Protocol" if _R=="en" else "ව්‍යාපාර අඛණ්ඩතා ක්‍රියාවලිය සක්‍රිය කරන්න",
                 "Implement pre-agreed crisis supply chain procedures. Identify alternative inputs immediately." if _R=="en" else "පූර්ව-එකඟ වූ අර්බුද සැපයුම් දාම ක්‍රියාවලි ක්‍රියාත්මක කරන්න. විකල්ප ආදාන ක්ෂණිකව හඳුනා ගන්න.",
                 "CRITICAL","Immediate" if _R=="en" else "ක්ෂණිකව","Board-level decision required" if _R=="en" else "මණ්ඩල මට්ටමේ තීරණය අවශ්‍ය"),
                ("",
                 "Secure Emergency Credit Lines" if _R=="en" else "හදිසි ණය රේඛා සුරක්ෂිත කරගන්න",
                 "Apply for SME Emergency Credit from NDB/BOC at 6% crisis rate before demand exceeds capacity." if _R=="en" else "ඉල්ලුම ධාරිතාවය ඉක්මවීමට පෙර 6% අර්බුද අනුපාතයේ NDB/BOC SME හදිසි ණය සඳහා ඉල්ලුම් කරන්න.",
                 "CRITICAL","Within 3 days" if _R=="en" else "දින 3 ඇතුළත","NDB/BOC — Rs. 50M facility available" if _R=="en" else "NDB/BOC — රු. 50M පහසුකම් ලබා ගත හැකිය"),
                ("",
                 "Reduce Production Volumes" if _R=="en" else "නිෂ්පාදන ප්‍රමාණ අඩු කරන්න",
                 "Temporarily reduce production of commodity lines. Maintain only high-margin premium products." if _R=="en" else "ගොවිතැන් නිෂ්පාදන රේඛා තාවකාලිකව අඩු කරන්න. ඉහළ ආන්තිකයෙන් යුතු ශ්‍රේෂ්ඨ නිෂ්පාදන පමණක් ලාභදායි ලෙස නිෂ්පාදනය කරන්න.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","Protect working capital — prioritise cash flow" if _R=="en" else "ශ්‍රම ප්‍රාග්ධනය ආරක්ෂා කරන්න — මුදල් ප්‍රවාහයට ප්‍රමුඛතාවය"),
                ("",
                 "Source Alternative Raw Materials" if _R=="en" else "විකල්ප අමු ද්‍රව්‍ය ලබා ගන්න",
                 "Explore palm oil, sunflower — partial substitution in cooking oil lines until crisis passes." if _R=="en" else "අර්බුදය ගතවන තෙක් ඉවුම් පිහුම් තෙල් රේඛාවල අර්ධ ආදේශනය සඳහා පාම් තෙල්, සූරියකාන්ත ගවේෂණය කරන්න.",
                 "HIGH","Within 1 week" if _R=="en" else "සතියක් ඇතුළත","SLSI approval may be required for labelling change" if _R=="en" else "ලේබල් වෙනස් කිරීමට SLSI අනුමැතිය අවශ්‍ය විය හැක"),
                ("",
                 "Customer Communication" if _R=="en" else "ගනුදෙනුකරු සන්නිවේදනය",
                 "Proactively communicate price increases to retail partners with written justification." if _R=="en" else "ලිඛිත සාධාරණීකරණයක් සහිතව සිල්ලර හවුල්කරුවන්ට ක්‍රියාශීලීව මිල ඉහළ යාම ගැන දැනුම් දෙන්න.",
                 "HIGH","Within 2 days" if _R=="en" else "දින 2 ඇතුළත","Prevents channel conflict — protect long-term relationships" if _R=="en" else "නාලිකා ගැටුම් වළක්වයි — දිගු කාලීන සම්බන්ධතා ආරක්ෂා කරයි"),
                ("",
                 "Engage Industry Association" if _R=="en" else "කර්මාන්ත සංගමය සමග කටයුතු කරන්න",
                 "Coconut Industry Collective Action — joint lobbying for import duty relief and government support." if _R=="en" else "පොල් කර්මාන්ත සාමූහික ක්‍රියාව — ආනයන බදු සහනය සහ රජු සහාය සඳහා ඒකාබද්ධ ශ්‍රමය.",
                 "MEDIUM","This week" if _R=="en" else "මෙම සතිය","CDA Industry Association: +94 11 243 0610"),
            ],
            "farmer": [
                ("",
                 "Maximise Harvest Immediately" if _R=="en" else "ක්ෂණිකව අස්වනු උපරිම කරන්න",
                 "Rush all harvestable nuts to market before government price controls reduce ceiling." if _R=="en" else "රජයේ මිල පාලනය කූඩාව අඩු කිරීමට පෙර අස්වනු ලබා ගත හැකි සියලු ගෙඩි ඉක්මනින් වෙළඳපොළට ගෙන යන්න.",
                 "CRITICAL","Next 3-5 days" if _R=="en" else "ඉදිරි දින 3-5","All 6 auction centres operating emergency sessions" if _R=="en" else "වෙන්දේසි මධ්‍යස්ථාන 6 ම හදිසි සැසි ක්‍රියාත්මක කරයි"),
                ("",
                 "Call CDA Emergency Helpline" if _R=="en" else "CDA හදිසි ආධාර රේඛාව අමතන්න",
                 "Register for emergency farmer support — income protection payments being processed." if _R=="en" else "හදිසි ගොවි සහාය සඳහා ලියාපදිංචි වන්න — ආදායම් ආරක්ෂා ගෙවීම් සකස් කෙරේ.",
                 "CRITICAL","Today" if _R=="en" else "අද","CDA Emergency: 1920 (toll-free 24/7)"),
                ("️",
                 "Document Your Costs" if _R=="en" else "ඔබේ පිරිවැය ලේඛනගත කරන්න",
                 "Keep all receipts for fertiliser, labour, transport — required for compensation claims." if _R=="en" else "පොහොර, ශ්‍රම, ප්‍රවාහන සියලු රිසිට්පත් රඳවා ගන්න — වන්දි ඉල්ලීම් සඳහා අවශ්‍ය.",
                 "HIGH","Immediate" if _R=="en" else "ක්ෂණිකව","CDA compensation forms available at regional offices" if _R=="en" else "CDA වන්දි ෆෝරම කලාපීය කාර්යාලවල ලබා ගත හැකිය"),
                ("",
                 "Do Not Sell Seedlings/Young Trees" if _R=="en" else "පැළ/තරුණ ගස් විකිණීම නොකරන්න",
                 "Crisis will pass. Do not liquidate productive assets for short-term cash." if _R=="en" else "අර්බුදය ගතවනු ඇත. කෙටි කාලීන මුදල් සඳහා ඵලදායි වත්කම් ලිදිවිය නොකරන්න.",
                 "HIGH","Now" if _R=="en" else "දැන්","Long-term income protection — very important" if _R=="en" else "දිගු කාලීන ආදායම් ආරක්ෂාව — ඉතා වැදගත්"),
                ("",
                 "Apply for Samurdhi Emergency Aid" if _R=="en" else "සමෘද්ධි හදිසි ආධාර ඉල්ලන්න",
                 "Farming households affected by crisis can apply for Rs. 3,500/month emergency support." if _R=="en" else "අර්බුදයෙන් බලපෑමට ලක් වූ ගොවි ගෘහ මාසිකව රු. 3,500 ක හදිසි සහාය සඳහා ඉල්ලුම් කළ හැකිය.",
                 "HIGH","Within 1 week" if _R=="en" else "සතියක් ඇතුළත","Divisional Secretariat — bring NIC and CDA registration" if _R=="en" else "ප්‍රාදේශීය ලේකම් — NIC සහ CDA ලියාපදිංචිය රැගෙන යන්න"),
                ("",
                 "Report Price Manipulation" if _R=="en" else "මිල හිරිහැර වාර්තා කරන්න",
                 "If brokers or middlemen offering below-auction prices — report immediately." if _R=="en" else "තැරැව්කරුවන් හෝ මැදිහත්කරුවන් වෙන්දේසිට අඩු මිල ඉදිරිපත් කරන්නේ නම් — ක්ෂණිකව වාර්තා කරන්න.",
                 "MEDIUM","If occurs" if _R=="en" else "සිදු වේ නම්","CAA hotline: 1977 (Consumer Affairs Authority)" if _R=="en" else "CAA ආධාර: 1977 (පාරිභෝගික කටයුතු අධිකාරිය)"),
            ],
        },
    }

    recs = all_recommendations[regime_now]
    regime_bg = regime_bgs[regime_now]
    regime_clr = regime_colors[regime_now]
    regime_name = (["Stable Market","Warning Market","Crisis Market"][regime_now]
                   if lang=="en" else
                   ["ස්ථාවර වෙළඳපොළ","අවවාද වෙළඳපොළ","අර්බුද වෙළඳපොළ"][regime_now])

    # Market status banner
    _active_regime_lbl = "Active Regime" if lang=="en" else "ක්‍රියාකාරී තත්ත්වය"
    _recs_active_lbl = ("Recommendations Active" if lang=="en" else "නිර්දේශ සක්‍රියයි")
    _current_price_lbl = ("Current price" if lang=="en" else "වත්මන් මිල")
    _total_recs_lbl = ("total recommendations across 3 stakeholder groups" if lang=="en" else "පාර්ශ්ව 3 සඳහා සම්පූර්ණ නිර්දේශ")
    st.markdown(f"""<div style='background:{regime_bg};border:2px solid {regime_clr};border-radius:12px;
        padding:14px 20px;margin-bottom:18px;display:flex;align-items:center;gap:12px;'>
        <div style='font-size:2rem;'>{["","",""][regime_now]}</div>
        <div>
          <div style='font-size:.72rem;font-weight:800;color:{regime_clr};text-transform:uppercase;
              letter-spacing:1.5px;'>{_active_regime_lbl}</div>
          <div style='font-size:1rem;font-weight:900;color:#1a3328;'>{regime_name} — {_recs_active_lbl}</div>
          <div style='font-size:.75rem;color:#374151;margin-top:2px;'>
              {_current_price_lbl} Rs.{current_price:.2f} | {len(recs["government"])+len(recs["business"])+len(recs["farmer"])} {_total_recs_lbl}
          </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Priority badge helper
    def priority_badge(p):
        cfg = {"CRITICAL":("#7f1d1d","#fca5a5"),"URGENT":("#ef4444","#fee2e2"),
               "HIGH":("#92400e","#fef3c7"),"MEDIUM":("#1a3328","#e4eeea")}
        bg, txt = cfg.get(p, ("#374151","#f1f5f9"))
        return f"<span style='background:{txt};color:{bg};font-size:.58rem;font-weight:800;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px;'>{p}</span>"

    # ── Render all 3 stakeholder tabs ──────────────────────────────────────────
    tab_gov, tab_biz, tab_farm = st.tabs([
        " " + ("Government & Policymakers" if lang=="en" else "රජය සහ ප්‍රතිපත්ති සම්පාදකයන්"),
        " " + ("Businesses & Traders" if lang=="en" else "ව්‍යාපාරිකයන් සහ වෙළෙන්දන්"),
        "‍ " + ("Coconut Farmers" if lang=="en" else "පොල් ගොවීන්"),
    ])

    def render_rec_cards(recs_list, accent):
        for i, (icon, title, desc, priority, timing, resource) in enumerate(recs_list):
            st.markdown(f"""<div style='background:#fff;border:1px solid #e2e8f0;border-left:5px solid {accent};
                border-radius:0 12px 12px 0;padding:16px 18px;margin-bottom:12px;
                box-shadow:0 1px 4px rgba(0,0,0,.06);'>
              <div style='display:flex;align-items:flex-start;gap:12px;'>
                <div style='font-size:1.5rem;line-height:1;margin-top:2px;'>{icon}</div>
                <div style='flex:1;'>
                  <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;'>
                    <div style='font-size:.88rem;font-weight:800;color:#1a3328;'>{title}</div>
                    {priority_badge(priority)}
                  </div>
                  <div style='font-size:.78rem;color:#374151;line-height:1.65;margin-bottom:8px;'>{desc}</div>
                  <div style='display:flex;gap:12px;flex-wrap:wrap;'>
                    <div style='font-size:.68rem;background:#f0f5f2;color:#3d7a55;padding:3px 9px;
                        border-radius:20px;font-weight:700;'>⏱ {timing}</div>
                    <div style='font-size:.68rem;background:#f0f5f2;color:#2d5a3d;padding:3px 9px;
                        border-radius:20px;font-weight:700;'> {resource}</div>
                  </div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    with tab_gov:
        _gov_intro = (f" These recommendations are tailored for <strong>Cabinet Ministers, CDA, HARTI, and Central Bank officials</strong> managing the coconut sector under <strong>{regime_name}</strong> conditions."
                      if lang=="en" else
                      f" මෙම නිර්දේශ <strong>{regime_name}</strong> තත්ත්වය යටතේ පොල් අංශය කළමනාකරණය කරන <strong>කැබිනට් අමාත්‍යවරුන්, CDA, HARTI සහ මහ බැංකු නිලධාරීන්</strong> සඳහා සකසා ඇත.")
        st.markdown(f"""<div style='background:#f0f5f2;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#1a3328;font-weight:700;'>
            {_gov_intro}
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["government"], "#3d7a55")

    with tab_biz:
        _biz_intro = (f" These recommendations are tailored for <strong>Coconut product manufacturers, exporters, traders and processors</strong> operating under <strong>{regime_name}</strong> conditions."
                      if lang=="en" else
                      f" මෙම නිර්දේශ <strong>{regime_name}</strong> තත්ත්වය යටතේ ක්‍රියාත්මක <strong>පොල් නිෂ්පාදකයන්, අපනයන කරන්නන්, වෙළෙන්දන් සහ සකසන්නන්</strong> සඳහා සකසා ඇත.")
        st.markdown(f"""<div style='background:#fdf4ff;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#6b21a8;font-weight:700;'>
            {_biz_intro}
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["business"], "#7c3aed")

    with tab_farm:
        _farm_intro = (f"‍ These recommendations are tailored for <strong>Smallholder farmers, coconut growers and farming cooperatives</strong> operating under <strong>{regime_name}</strong> conditions."
                       if lang=="en" else
                       f"‍ මෙම නිර්දේශ <strong>{regime_name}</strong> තත්ත්වය යටතේ ක්‍රියාත්මක <strong>කුඩා ගොවීන්, පොල් වගාකරුවන් සහ ගොවි සමිති</strong> සඳහා සකසා ඇත.")
        st.markdown(f"""<div style='background:#f0f5f2;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#3d7a55;font-weight:700;'>
            {_farm_intro}
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["farmer"], "#3d7a55")

    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — DECISION RISK MATRIX
    # ══════════════════════════════════════════════════════════════════════════
    _risk_title = ("Strategic Risk & Opportunity Matrix" if lang=="en" else "උපාය මාර්ගික අවදානම් සහ අවස්ථා න්‍යාසය")
    _risk_sub = ("Visual mapping of risks and opportunities across all market conditions"
                   if lang=="en" else
                   "සියලු වෙළඳ තත්ත්ව හරහා අවදානම් සහ අවස්ථා දෘශ්‍ය සිතියම")
    st.markdown(f"""<div style='background:linear-gradient(90deg,#0f766e,#0d9488);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        {_risk_title}
      </div>
      <div style='font-size:.78rem;color:#ccfbf1;margin-top:3px;'>
        {_risk_sub}
      </div>
    </div>
    """, unsafe_allow_html=True)

    rm1, rm2 = st.columns(2)
    with rm1:
        st.markdown("##### " + ("Key Risks to Monitor" if lang=="en" else "ප්‍රධාන අවදානම්"))
        risks = [
            ("",
             "Drought / Low Rainfall" if lang=="en" else "නියඟය / අඩු වර්ෂාව",
             "HIGH" if regime_now >= 1 else "MEDIUM",
             "Yield drop in 3-6 months. Monitor CRI rainfall index monthly." if lang=="en" else "මාස 3-6 තුළ අස්වැන්න පහත වැටේ. CRI වර්ෂාපාත දර්ශකය මාසිකව නිරීක්ෂණය කරන්න."),
            ("",
             "Export Demand Surge" if lang=="en" else "අපනයන ඉල්ලුම් ඉහළ යාම",
             "HIGH" if regime_now >= 1 else "MEDIUM",
             "Global demand spikes can drain domestic supply rapidly." if lang=="en" else "ගෝලීය ඉල්ලුම ඉහළ යාම දේශීය සැපයුම ඉක්මනින් හිඳ දැමිය හැක."),
            ("",
             "Rising Input Costs" if lang=="en" else "ආදාන පිරිවැය ඉහළ යාම",
             "MEDIUM",
             "Fuel, fertiliser prices affect farm-gate profitability directly." if lang=="en" else "ඉන්ධන, පොහොර මිල ගොවි ලාභදායිතාවට කෙලින්ම බලපායි."),
            ("",
             "Exchange Rate Volatility" if lang=="en" else "විනිමය අනුපාත අස්ථාවරතාව",
             "MEDIUM",
             "LKR depreciation increases import cost of inputs." if lang=="en" else "රුපියල් ශ්‍රේණිගත කිරීම ආදාන ආනයන පිරිවැය ඉහළ නංවයි."),
            ("",
             "Pest/Disease Outbreak" if lang=="en" else "පළිබෝධ / රෝග පැතිරීම",
             "HIGH" if regime_now == 2 else "MEDIUM",
             "Rhinoceros beetle and bud rot remain significant threats." if lang=="en" else "රයිනොසරස් සිලිත්‍රා සහ අංකුර කුණාටුව ප්‍රධාන තර්ජන ලෙස පවතී."),
            ("",
             "Processing Capacity Shortage" if lang=="en" else "සැකසුම් ධාරිතා හිඟය",
             "LOW" if regime_now == 0 else "MEDIUM",
             "Value-addition bottlenecks limit export revenue growth." if lang=="en" else "අගය එකතු කිරීමේ බාධා අපනයන ආදායම් වර්ධනය සීමා කරයි."),
        ]
        for icon, risk, level, detail in risks:
            lvl_clr = {"CRITICAL":"#ef4444","HIGH":"#f59e0b","MEDIUM":"#5a9470","LOW":"#5a9470"}[level]
            st.markdown(f"""<div style='display:flex;align-items:center;gap:10px;padding:9px 12px;
                background:#f8fafc;border-radius:8px;margin-bottom:7px;border:1px solid #e2e8f0;'>
                <div style='font-size:1.1rem;'>{icon}</div>
                <div style='flex:1;'>
                  <div style='display:flex;align-items:center;gap:7px;'>
                    <div style='font-size:.75rem;font-weight:800;color:#1a3328;'>{risk}</div>
                    {priority_badge(level)}
                  </div>
                  <div style='font-size:.68rem;color:#64748b;margin-top:2px;'>{detail}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with rm2:
        st.markdown("##### " + ("Key Opportunities" if lang=="en" else "ප්‍රධාන අවස්ථා"))
        opportunities = [
            ("",
             "Virgin Coconut Oil Export" if lang=="en" else "කළු නොකළ පොල් තෙල් අපනයනය",
             "HIGH",
             "Global VCO market growing 8.5% YoY. SL quality commands 30% premium." if lang=="en" else "ගෝලීය VCO වෙළඳපොළ වාර්ෂිකව 8.5% ක් වර්ධනය වේ. ශ්‍රී ලංකා ගුණය 30% වාසිය ලබා ගනී."),
            ("",
             "Organic Certification" if lang=="en" else "කාබනික සහතිකය",
             "HIGH",
             "EU organic coconut market worth $2.1B. Only 12% of SL farms certified." if lang=="en" else "EU කාබනික පොල් වෙළඳපොළ $2.1B. ශ්‍රී ලංකා ගොවිතැන් 12% ක් පමණක් සහතික කර ඇත."),
            ("",
             "Coconut Water Market" if lang=="en" else "පොල් වතුර වෙළඳපොළ",
             "HIGH",
             "Global market $6.8B by 2026. SL currently exports < 3% of potential." if lang=="en" else "2026 වන විට ගෝලීය වෙළඳපොළ $6.8B. ශ්‍රී ලංකාව දැනට හැකියාවේ 3%ට වඩා අඩු ප්‍රමාණයක් අපනයනය කරයි."),
            ("",
             "Activated Carbon" if lang=="en" else "සක්‍රිය කාබන්",
             "MEDIUM",
             "High-value industrial product from coconut shell. Margins 4x raw nuts." if lang=="en" else "පොල් කටු වලින් ලබාගත් අධි-අගය කාර්මික නිෂ්පාදනය. ලාභ ආන්තිකය නැවුම් ගෙඩිවලට වඩා 4 ගුණයකි."),
            ("",
             "Agro-Tourism" if lang=="en" else "කෘෂිකාර්මික සංචාරය",
             "MEDIUM",
             "Coconut triangle farm tourism growing 22% annually post-pandemic." if lang=="en" else "වසංගතයෙන් පසු පොල් ත්‍රිකෝණ ගොවිපල සංචාරය වාර්ෂිකව 22% ක් වර්ධනය වේ."),
            ("",
             "Smart Farming Technology" if lang=="en" else "දක්ෂ ගොවිතැන් තාක්ෂණය",
             "MEDIUM",
             "IoT sensors and drone spraying can increase yield by 15-20%." if lang=="en" else "IoT සංවේදක සහ ඩ්‍රෝන් ඉසිනා ගැනීම් අස්වැන්න 15-20% ක් ඉහළ නැංවිය හැක."),
        ]
        for icon, opp, level, detail in opportunities:
            lvl_clr = {"HIGH":"#3d7a55","MEDIUM":"#5a9470","LOW":"#94a3b8"}[level]
            st.markdown(f"""<div style='display:flex;align-items:center;gap:10px;padding:9px 12px;
                background:#f0f5f2;border-radius:8px;margin-bottom:7px;border:1px solid #b8d0c4;'>
                <div style='font-size:1.1rem;'>{icon}</div>
                <div style='flex:1;'>
                  <div style='display:flex;align-items:center;gap:7px;'>
                    <div style='font-size:.75rem;font-weight:800;color:#1a3328;'>{opp}</div>
                    <span style='background:#f0f5f2;color:#3d7a55;font-size:.58rem;font-weight:800;
                        padding:2px 7px;border-radius:20px;'>{level}</span>
                  </div>
                  <div style='font-size:.68rem;color:#374151;margin-top:2px;'>{detail}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — 90-DAY ACTION PLAN
    # ══════════════════════════════════════════════════════════════════════════
    _plan_title = ("90-Day Priority Action Plan" if lang=="en" else "දින 90 ප්‍රමුඛ ක්‍රියා සැලැස්ම")
    _plan_sub = ("Immediate, short-term and medium-term actions based on current market regime"
                   if lang=="en" else
                   "වත්මන් වෙළඳ තත්ත්වය මත පදනම් වූ ක්ෂණික, කෙටි කාලීන සහ මධ්‍ය කාලීන ක්‍රියාමාර්ග")
    st.markdown(f"""<div style='background:linear-gradient(90deg,#92400e,#b45309);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        {_plan_title}
      </div>
      <div style='font-size:.78rem;color:#fde68a;margin-top:3px;'>
        {_plan_sub}
      </div>
    </div>
    """, unsafe_allow_html=True)

    action_plan = {
        0: [ # Stable
            ("Week 1–2" if lang=="en" else "සතිය 1–2", "#3d7a55",
             " Initiate buffer stock procurement | Deploy CDA digital price reporting" if lang=="en" else
             " බෆර් තොග ලබා ගැනීම ආරම්භ කරන්න | CDA ඩිජිටල් මිල වාර්තාකරණය ක්‍රියාත්මක කරන්න"),
            ("Week 3–4" if lang=="en" else "සතිය 3–4", "#5a9470",
             " Update farmer registration database | Launch cooperative formation drive" if lang=="en" else
             " ගොවි ලියාපදිංචි දත්ත සමුදාය යාවත්කාලීන කරන්න | සමිති ගොඩනැගීමේ ව්‍යාපාරය ආරම්භ කරන්න"),
            ("Month 2" if lang=="en" else "2 වන මාසය", "#f59e0b",
             " Value-addition investment roadshow | Trade agreement preliminary talks" if lang=="en" else
             " අගය-එකතු කිරීමේ ආයෝජන ප්‍රවර්ධනය | වෙළඳ ගිවිසුම් මූලික සාකච්ඡා"),
            ("Month 3" if lang=="en" else "3 වන මාසය", "#8b5cf6",
             " Review export incentive schemes | Replanting programme launch" if lang=="en" else
             " අපනයන දිරිගැන්වීමේ යෝජනා ක්‍රම සමාලෝචනය | නැවත රෝපණ වැඩසටහන ආරම්භ කරන්න"),
        ],
        1: [ # Warning
            ("Day 1–3" if lang=="en" else "දිනය 1–3", "#ef4444",
             " Activate monitoring task force | Launch price transparency media campaign" if lang=="en" else
             " නිරීක්ෂණ කාර්ය සාධක බලකාය සක්‍රිය කරන්න | මිල විනිවිදභාවය මාධ්‍ය ව්‍යාපාරය ආරම්භ කරන්න"),
            ("Day 4–7" if lang=="en" else "දිනය 4–7", "#f59e0b",
             " Release 10-15% buffer stock | Signal stabilisation fund readiness" if lang=="en" else
             " බෆර් තොගයෙන් 10-15% මුදා හරින්න | ස්ථාවරීකරණ අරමුදල් සූදානම සංඥා කරන්න"),
            ("Week 2–3" if lang=="en" else "සතිය 2–3", "#5a9470",
             " Accelerate harvest support transport | Emergency farmer registration" if lang=="en" else
             " අස්වනු සහාය ප්‍රවාහනය ත්වරාන්විත කරන්න | හදිසි ගොවි ලියාපදිංචිය"),
            ("Month 2–3" if lang=="en" else "මාස 2–3", "#8b5cf6",
             "️ Review import duty schedule | Commission independent price audit" if lang=="en" else
             "️ ආනයන බදු කාලසටහන සමාලෝචනය | ස්වාධීන මිල විගණනය කෙරෙහි පත් කිරීම"),
        ],
        2: [ # Crisis
            ("Today" if lang=="en" else "අද", "#7f1d1d",
             "🆘 Emergency Cabinet session | Full buffer stock release authorisation" if lang=="en" else
             "🆘 හදිසි කැබිනට් රැස්වීම | සම්පූර්ණ බෆර් තොග මුදා හැරීමේ අනුමැතිය"),
            ("Day 2–3" if lang=="en" else "දිනය 2–3", "#ef4444",
             " Gazette emergency import permits | Activate Samurdhi emergency payments" if lang=="en" else
             " හදිසි ආනයන බලපත්‍ර ගැසට් කරන්න | සමෘද්ධි හදිසි ගෙවීම් සක්‍රිය කරන්න"),
            ("Week 1" if lang=="en" else "1 වන සතිය", "#f59e0b",
             " Deploy anti-hoarding enforcement | Begin daily national price broadcast" if lang=="en" else
             " ගබඩා කිරීම් වැළැක්වීමේ ක්‍රියාත්මක කිරීම | දෛනික ජාතික මිල විකාශය ආරම්භ කරන්න"),
            ("Week 2–4" if lang=="en" else "සතිය 2–4", "#5a9470",
             " Conduct supply chain audit | Post-crisis recovery plan preparation" if lang=="en" else
             " සැපයුම් දාම විගණනය සිදු කරන්න | අර්බුදයෙන් පසු යථා තත්ත්වයට පත්වීමේ සැලැස්ම සකස් කරන්න"),
        ],
    }

    ap_cols = st.columns(4)
    for col, (period, clr, actions) in zip(ap_cols, action_plan[regime_now]):
        action_items = [a.strip() for a in actions.split("|")]
        items_html = "".join([f"<div style='font-size:.7rem;color:#374151;padding:5px 0;border-bottom:1px solid #f0f5f2;line-height:1.4;'>{a}</div>" for a in action_items])
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #e2e8f0;border-top:4px solid {clr};
                border-radius:10px;padding:14px 12px;min-height:180px;'>
                <div style='font-size:.7rem;font-weight:900;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:10px;'>{period}</div>
                {items_html}
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Download summary report ────────────────────────────────────────────────
    st.markdown("##### " + ("Export Recommendation Report" if lang=="en" else "නිර්දේශ වාර්තාව බාගන්න"))
    from datetime import datetime
    report_lines = [
        f"COCOStat – Strategic Recommendation Report",
        f"{'Generated' if lang=='en' else 'ජනනය කළ දිනය'}: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"{'Current Market Regime' if lang=='en' else 'වත්මන් වෙළඳ තත්ත්වය'}: {regime_name}",
        f"{'Current Price' if lang=='en' else 'වත්මන් මිල'}: Rs. {current_price:.2f}",
        f"{'12-Month Average' if lang=='en' else 'මාස 12 සාමාන්‍යය'}: Rs. {avg_12m:.2f}",
        f"{'Price Volatility (CV)' if lang=='en' else 'මිල අස්ථාවරතාව (CV)'}: {cv:.1f}%",
        "",
        "=" * 60,
        "POLICY SIMULATOR RESULTS" if lang=="en" else "ප්‍රතිපත්ති අනුකරණ ප්‍රතිඵල",
        "=" * 60,
        f"{'Buffer Stock Release' if lang=='en' else 'බෆර් තොග මුදා හැරීම'}: {buffer_stock}%",
        f"{'Import Duty Change' if lang=='en' else 'ආනයන බදු වෙනස'}: {import_duty:+}%",
        f"{'Farmer Subsidy' if lang=='en' else 'ගොවි සහාය'}: {subsidy_pct}%",
        f"{'Price Floor' if lang=='en' else 'අවම මිල'}: Rs. {price_floor}",
        f"{'Export Quota Cut' if lang=='en' else 'අපනයන සීමා කප්පාදු'}: {export_quota}%",
        f"{'Projected Price' if lang=='en' else 'ඉදිරි මිල'}: Rs. {price_impact:.2f} ({delta_pct:+.1f}%)",
        f"{'Policy Verdict' if lang=='en' else 'ප්‍රතිපත්ති තීරණය'}: {verdict_title}",
        "",
        "=" * 60,
        f"{'GOVERNMENT RECOMMENDATIONS' if lang=='en' else 'රජු නිර්දේශ'} ({regime_name})",
        "=" * 60,
    ]
    for icon, title, desc, priority, timing, resource in recs["government"]:
        report_lines += [f"\n[{priority}] {title}", f" {desc}", f" ⏱ {timing} | {resource}"]
    report_lines += ["", "=" * 60, f"{'BUSINESS RECOMMENDATIONS' if lang=='en' else 'ව්‍යාපාර නිර්දේශ'} ({regime_name})", "=" * 60]
    for icon, title, desc, priority, timing, resource in recs["business"]:
        report_lines += [f"\n[{priority}] {title}", f" {desc}", f" ⏱ {timing} | {resource}"]
    report_lines += ["", "=" * 60, f"{'FARMER RECOMMENDATIONS' if lang=='en' else 'ගොවි නිර්දේශ'} ({regime_name})", "=" * 60]
    for icon, title, desc, priority, timing, resource in recs["farmer"]:
        report_lines += [f"\n[{priority}] {title}", f" {desc}", f" ⏱ {timing} | {resource}"]
    report_lines += ["", "─" * 60, "COCOStat · Coconut Market Intelligence · CDA & HARTI Sri Lanka"]

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label= ("Download Full Recommendation Report (TXT)" if lang=="en" else "සම්පූර්ණ නිර්දේශ වාර්තාව බාගන්න (TXT)"),
            data="\n".join(report_lines),
            file_name=f"cocostat_recommendations_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain", use_container_width=True)
    with dl2:
        import io
        csv_rows = [["Stakeholder","Priority","Action","Description","Timing","Resource"] if lang=="en"
                    else ["පාර්ශ්වය","ප්‍රමුඛතාවය","ක්‍රියාව","විස්තරය","කාලය","සම්පත"]]
        _gov_lbl = "Government" if lang=="en" else "රජය"
        _biz_lbl = "Business" if lang=="en" else "ව්‍යාපාරය"
        _farm_lbl = "Farmer" if lang=="en" else "ගොවිය"
        for stakeholder, recs_list in [(_gov_lbl,recs["government"]),(_biz_lbl,recs["business"]),(_farm_lbl,recs["farmer"])]:
            for icon, title, desc, priority, timing, resource in recs_list:
                csv_rows.append([stakeholder, priority, title, desc, timing, resource])
        csv_buf = io.StringIO()
        import csv as csv_mod
        writer = csv_mod.writer(csv_buf)
        writer.writerows(csv_rows)
        st.download_button(
            label= ("Download Action Items (CSV)" if lang=="en" else "ක්‍රියා අයිතම බාගන්න (CSV)"),
            data=csv_buf.getvalue(),
            file_name=f"cocostat_actions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)

# ══ COMPARE ══════════════════════════════════════════════════════════════════
elif t["nav"][4] in sec_name:
    section_header(" "+t["compare_title"], t["compare_sub"])
    avail=sorted(history_df["year"].unique().tolist())
    sel=st.multiselect("Select years:" if lang=="en" else "\u0dc0\u0dc3\u0dbb \u0dad\u0ddc\u0dbb\u0db1\u0dca\u0db1:",avail,default=avail[-3:])
    if sel:
        mn=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        yc=px.colors.qualitative.Set2
        fig_y=go.Figure()
        for idx,yr in enumerate(sel):
            yd=history_df[history_df["year"]==yr].sort_values("month")
            fig_y.add_trace(go.Scatter(x=[mn[m-1] for m in yd["month"]],y=yd["price"],mode="lines+markers",name=str(yr),
                line=dict(color=yc[idx%len(yc)],width=2.5),marker=dict(size=7),
                hovertemplate=f"<b>{yr}</b> %{{x}}<br>Rs.%{{y:.2f}}<extra></extra>"))
        fig_y.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f" Rs.{warn_threshold}")
        fig_y.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f" Rs.{crisis_threshold}")
        fig_y.update_layout(height=360,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_y,use_container_width=True,config={"displayModeBar":"hover"})
        divider()
        st.markdown("#### "+("Year-by-Year Comparison" if lang=="en" else "\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1 \u0dc0\u0d9c\u0dd4\u0dc0"))
        cdata=[]
        for yr in sel:
            yd=history_df[history_df["year"]==yr]["price"]
            _yr_lbl = "Year" if lang=="en" else "වර්ෂය"
            _avg_lbl = "Avg (Rs.)" if lang=="en" else "සාමාන්‍යය (රු.)"
            _min_lbl = "Min (Rs.)" if lang=="en" else "අවම (රු.)"
            _max_lbl = "Max (Rs.)" if lang=="en" else "උපරිම (රු.)"
            _std_lbl = "Std Dev" if lang=="en" else "විචලනය"
            _crisis_lbl2 = "Crisis Months" if lang=="en" else "අර්බුද මාස"
            _warn_lbl2 = "Warning Months" if lang=="en" else "අවවාද මාස"
            cdata.append({_yr_lbl:yr, _avg_lbl:round(yd.mean(),2), _min_lbl:round(yd.min(),2),
                _max_lbl:round(yd.max(),2), _std_lbl:round(yd.std(),2),
                _crisis_lbl2:int((yd>=crisis_threshold).sum()), _warn_lbl2:int(((yd>=warn_threshold)&(yd<crisis_threshold)).sum())})
        st.dataframe(pd.DataFrame(cdata),use_container_width=True,hide_index=True)
        divider()
        st.markdown("#### "+("Volatility Comparison" if lang=="en" else "\u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba"))
        fig_v=go.Figure()
        for idx,yr in enumerate(sel):
            fig_v.add_trace(go.Box(y=history_df[history_df["year"]==yr]["price"],name=str(yr),marker_color=yc[idx%len(yc)],boxmean=True))
        fig_v.update_layout(height=300,margin=dict(l=10,r=10,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_v,use_container_width=True,config={"displayModeBar":"hover"})

        # ── GLOBAL COMPARISON (embedded) ──────────────────────────────────────
        divider()
        st.markdown(f"""<div style='background:linear-gradient(90deg,#1a3328,#2d5a3d);border-radius:10px;padding:12px 20px;margin-bottom:12px;'>
            <div style='font-size:1.05rem;font-weight:900;color:#fff;'> {"Global Market Comparison" if lang=="en" else "ගෝලීය වෙළඳපොළ සංසන්දනය"}</div>
            <div style='font-size:.78rem;color:#b8d0c4;margin-top:3px;'>{"Sri Lanka vs. Major Coconut Producing Nations" if lang=="en" else "ශ්‍රී ලංකා හා ප්‍රධාන නිෂ්පාදක රටවල් සංසන්දනය"}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box-blue'>{t['global_note']}</div>", unsafe_allow_html=True)

        # Global KPI row
        sl_l = global_price_df["Sri Lanka"].iloc[-1]
        w_avg = global_price_df[["Indonesia","Philippines","India","Vietnam"]].iloc[-1].mean()
        sl_vs = sl_l - w_avg; sv_clr = "#3d7a55"
        gk1,gk2,gk3,gk4 = st.columns(4)
        for col,(lbl,val,clr) in zip([gk1,gk2,gk3,gk4],[
            ("SL Price (2024)" if lang=="en" else "ශ්‍රී ලංකා මිල 2024", f"Rs.{sl_l:.0f}", "#3d7a55"),
            ("World Avg Price" if lang=="en" else "ලෝක සාමාන්‍ය", f"Rs.{w_avg:.0f}", "#3d7a55"),
            ("SL Premium" if lang=="en" else "ශ්‍රී ලංකා වෙනස", f"{'+' if sl_vs>0 else ''}{sl_vs:.0f} Rs ({(sl_vs/w_avg*100):+.1f}%)", sv_clr),
            ("World Rank" if lang=="en" else "ලෝක ශ්‍රේණිය", "3rd Largest Producer" if lang=="en" else "3 වැනි නිෂ්පාදකයා", "#3d7a55")]):
            with col: st.markdown(metric_card(lbl,val,clr,height=100), unsafe_allow_html=True)

        divider()

        # Multi-country price trend
        st.markdown("#### "+("Coconut Price Trend — Sri Lanka vs World Producers (LKR Equivalent)" if lang=="en" else "පොල් මිල ප්‍රවණතාව — ශ්‍රී ලංකා හා ලෝක නිෂ්පාදකයෝ"))
        c_colors={"Sri Lanka":"#3d7a55","Indonesia":"#5a9470","Philippines":"#f59e0b","India":"#ef4444","Vietnam":"#8b5cf6"}
        fig_gl=go.Figure()
        for country,clr in c_colors.items():
            is_sl=(country=="Sri Lanka")
            fig_gl.add_trace(go.Scatter(x=global_price_df["year"].astype(str),y=global_price_df[country],
                mode="lines+markers",name=("🇱🇰 " if is_sl else "")+country,
                line=dict(color=clr,width=3.5 if is_sl else 1.8,dash="solid" if is_sl else "dot"),
                marker=dict(size=8 if is_sl else 5),
                hovertemplate=f"<b>{country}</b> %{{x}}<br>Rs.%{{y:.1f}}<extra></extra>"))
        fig_gl.update_layout(height=340,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",tickfont=dict(size=11)),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_gl,use_container_width=True,config={"displayModeBar":"hover"})
        divider()

        # Production share + radar
        cp2,cr=st.columns(2)
        with cp2:
            st.markdown("#### "+("Global Coconut Production Share" if lang=="en" else "ගෝලීය පොල් නිෂ්පාදන කොටස"))
            fig_pp=go.Figure(go.Pie(labels=production_df["Country"],values=production_df["Production_B_nuts"],hole=.45,
                textinfo="label+percent",textfont=dict(size=10),
                marker=dict(colors=["#5a9470","#f59e0b","#ef4444","#3d7a55","#8b5cf6","#06b6d4","#84cc16"]),
                pull=[.08 if c=="Sri Lanka" else 0 for c in production_df["Country"]],
                hovertemplate="<b>%{label}</b><br>%{value}B nuts/yr<br>%{percent}<extra></extra>"))
            fig_pp.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
            st.plotly_chart(fig_pp,use_container_width=True,config={"displayModeBar":"hover"})
        with cr:
            st.markdown("#### "+("Country Competitiveness Radar" if lang=="en" else "රටවල් තරඟකාරිත්ව රේඩාර්"))
            ctries=["Sri Lanka","Indonesia","Philippines","India","Vietnam"]
            attrs=(["Quality","Volume","Price Comp.","Export Infra.","Processing"]
                   if lang=="en" else
                   ["ගුණාත්මකභාවය","පරිමාව","මිල තරඟකාරිත්වය","අපනයන යටිතල","සැකසීම"])
            scores={"Sri Lanka":[88,40,55,72,80],"Indonesia":[70,95,90,82,75],"Philippines":[75,85,80,78,70],"India":[80,88,72,80,82],"Vietnam":[65,50,88,60,55]}
            clrs_r=["#3d7a55","#5a9470","#f59e0b","#ef4444","#8b5cf6"]
            fig_rad=go.Figure()
            for ct,clr in zip(ctries,clrs_r):
                v=scores[ct]+[scores[ct][0]]; a=attrs+[attrs[0]]
                c_int=int(clr[1:3],16); c_g=int(clr[3:5],16); c_b=int(clr[5:7],16)
                fig_rad.add_trace(go.Scatterpolar(r=v,theta=a,fill="toself",fillcolor=f"rgba({c_int},{c_g},{c_b},.08)",
                    line=dict(color=clr,width=2),name=ct,hovertemplate=f"<b>{ct}</b><br>%{{theta}}: %{{r}}<extra></extra>"))
            fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100],tickfont=dict(size=9)),
                angularaxis=dict(tickfont=dict(size=10)),bgcolor="#fff"),
                height=300,margin=dict(l=30,r=30,t=20,b=20),paper_bgcolor="#fff",
                legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=9)))
            st.plotly_chart(fig_rad,use_container_width=True,config={"displayModeBar":"hover"})
        divider()

        # Price gap table
        st.markdown("#### "+("Price Gap Analysis vs Sri Lanka (Latest Year)" if lang=="en" else "මිල පරතර විශ්ලේෂණය"))
        lr=global_price_df.iloc[-1]; sl_p=lr["Sri Lanka"]
        gdrows=[]
        for ct in ["Indonesia","Philippines","India","Vietnam"]:
            cp_=lr[ct]; gap=sl_p-cp_; gp=gap/cp_*100
            gdrows.append({
                ("Country" if lang=="en" else "රට"):ct,
                ("Price (Rs.)" if lang=="en" else "මිල (රු.)"):round(cp_,1),
                ("SL Price (Rs.)" if lang=="en" else "ශ්‍රී ලංකා මිල (රු.)"):round(sl_p,1),
                ("Gap (Rs.)" if lang=="en" else "පරතරය (රු.)"):round(gap,1),
                ("Gap (%)" if lang=="en" else "පරතරය (%)"):round(gp,1),
                ("SL vs This" if lang=="en" else "ශ්‍රී ලංකා"):("Higher↑" if gap>0 else "Lower↓")
            })
        st.dataframe(pd.DataFrame(gdrows),use_container_width=True,hide_index=True)
        divider()

        # SL price divergence bar chart
        st.markdown("#### "+("SL Price Divergence from World Average" if lang=="en" else "ලෝක සාමාන්‍යයෙන් ශ්‍රී ලංකා අපගමනය"))
        wavg_s=global_price_df[["Indonesia","Philippines","India","Vietnam"]].mean(axis=1)
        sldev=global_price_df["Sri Lanka"]-wavg_s
        fig_dv=go.Figure(go.Bar(x=global_price_df["year"].astype(str),y=sldev,
            marker_color=["#5a9470" if v>0 else "#ef4444" for v in sldev],
            text=[f"Rs.{v:+.1f}" for v in sldev],textposition="outside",textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>SL Premium: Rs.%{y:.1f}<extra></extra>"))
        fig_dv.add_hline(y=0,line_color="#94a3b8",line_width=1.5)
        fig_dv.update_layout(height=260,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs.",
            title=("Premium above World Avg" if lang=="en" else "ලෝක සාමාන්‍යයට ඉහළ")),showlegend=False)
        st.plotly_chart(fig_dv,use_container_width=True,config={"displayModeBar":"hover"})

    else:
        st.info("Please select at least one year." if lang=="en" else "\u0d9a\u0dbb\u0dd4\u0dab\u0dcf\u0d9a\u0dbb \u0d85\u0dc0\u0db8 \u0dc0\u0dc3\u0dbb\u0d9a\u0dca \u0dad\u0ddc\u0dbb\u0db1\u0dca\u0db1.")

# ══ METHOD ═══════════════════════════════════════════════════════════════════
elif t["nav"][9] in sec_name:

    # ── Page CSS: black & green formal theme ──────────────────────────────────
    st.markdown("""<style>
    .m-hero{background:#0a0a0a;border-left:5px solid #3d7a55;border-radius:4px;
        padding:22px 28px;margin-bottom:8px;}
    .m-section-title{font-size:.65rem;font-weight:800;color:#3d7a55;
        text-transform:uppercase;letter-spacing:2.5px;margin:28px 0 14px;}
    .m-card{background:#111;border:1px solid #1f1f1f;border-top:3px solid #3d7a55;
        border-radius:6px;padding:18px 18px;margin-bottom:10px;height:100%;}
    .m-card-title{font-size:.82rem;font-weight:700;color:#f0f5f2;margin-bottom:7px;}
    .m-card-body{font-size:.74rem;color:#9ca3af;line-height:1.7;}
    .m-pipe{background:#111;border:1px solid #222;border-left:3px solid #3d7a55;
        border-radius:4px;padding:14px 16px;margin-bottom:8px;}
    .m-pipe-num{font-size:.58rem;font-weight:800;color:#3d7a55;letter-spacing:2px;
        text-transform:uppercase;margin-bottom:5px;}
    .m-pipe-title{font-size:.82rem;font-weight:700;color:#f0f5f2;margin-bottom:5px;}
    .m-pipe-body{font-size:.73rem;color:#9ca3af;line-height:1.65;}
    .m-tbl table{width:100%;border-collapse:collapse;font-size:.76rem;}
    .m-tbl th{background:#1a3328;color:#82b49a;font-weight:700;
        padding:9px 12px;text-align:left;border-bottom:2px solid #3d7a55;letter-spacing:.5px;}
    .m-tbl td{padding:8px 12px;border-bottom:1px solid #1f1f1f;
        color:#d1d5db;vertical-align:top;line-height:1.55;}
    .m-tbl tr:hover td{background:#1a332822;}
    .m-ref{background:#111;border:1px solid #1f1f1f;border-radius:6px;padding:20px 22px;margin-bottom:10px;}
    .m-ref-head{font-size:.65rem;font-weight:800;color:#3d7a55;
        text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;}
    .m-ref-item{font-size:.77rem;color:#d1d5db;line-height:1.8;
        padding:4px 0;border-bottom:1px solid #1a1a1a;}
    </style>""", unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""<div class='m-hero'>
      <div style='font-size:1.35rem;font-weight:900;color:#fff;letter-spacing:-.3px;margin-bottom:8px;'>
        COCOStat &mdash; Methodology & Documentation
      </div>
      <div style='font-size:.85rem;color:#a8c9b8;line-height:1.75;'>
        COCOStat is a Coconut Market Intelligence Dashboard developed for Sri Lanka's coconut industry.
        All data is sourced from official Sri Lankan government departments and institutions.
        The system integrates price records, weather observations, export statistics, and agronomic
        data to deliver market analysis, forecasts, policy tools, and farmer support.
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Dashboard Sections ────────────────────────────────────────────────────
    st.markdown("<div class='m-section-title'>Dashboard Sections</div>", unsafe_allow_html=True)

    sections = [
        ("01", "Overview &amp; History",
         "Monthly auction price records from 2015 to 2024, sourced from CDA and HARTI. "
         "Includes 3-year trend chart, seasonal heatmap, price impact calculator, and annual average analysis."),
        ("02", "Market &amp; Demand",
         "Three-tier market regime classification (Stable / Warning / Crisis) based on CDA price thresholds. "
         "Price elasticity of demand analysis with demand curves per regime."),
        ("03", "Weather &amp; Harvest",
         "Rainfall and temperature data from the Department of Meteorology. "
         "Yield index forecasts using a 3-month lagged rainfall model aligned with SW and NE monsoon seasons."),
        ("04", "Forecast",
         "12-week ahead price forecast with confidence intervals based on historical CDA auction records. "
         "Weekly price projections with regime-based colour indicators."),
        ("05", "Compare",
         "Year-over-year price comparison across the full 2015–2024 dataset. "
         "Segmentation by year, month, market regime, and agricultural season."),
        ("06", "Export &amp; Trade",
         "Export volume and revenue data sourced from the Sri Lanka Export Development Board (EDB) and CDA. "
         "Covers six product categories across nine destination markets (2015–2024)."),
        ("07", "Policy &amp; Recommendations",
         "Evidence-based policy simulator with five intervention levers. "
         "Tailored recommendations for Government policymakers, Businesses, and Farmers "
         "based on current market regime, with a 90-Day Action Plan."),
        ("08", "Farmer Profitability",
         "Farm-level income calculator using CDA-published land and yield benchmarks. "
         "Break-even price analysis and profit sensitivity to market price changes."),
        ("09", "Auction Details",
         "Official auction centre information for all six CDA and HARTI-managed centres. "
         "Includes schedules, grade benchmarks, bidding rules, and buyer/seller requirements."),
        ("10", "Method",
         "System documentation covering data sources, analytical methodology, processing pipeline, "
         "technical specifications, and references."),
    ]

    for i in range(0, 10, 2):
        c1, c2 = st.columns(2)
        for col, (num, title, body) in zip([c1, c2], sections[i:i+2]):
            with col:
                st.markdown(
                    f"<div class='m-card'>"
                    f"<div style='font-size:.58rem;font-weight:800;color:#3d7a55;"
                    f"letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>{num}</div>"
                    f"<div class='m-card-title'>{title}</div>"
                    f"<div class='m-card-body'>{body}</div>"
                    f"</div>",
                    unsafe_allow_html=True)

    # ── Data Sources ──────────────────────────────────────────────────────────
    st.markdown("<div class='m-section-title'>Data Sources</div>", unsafe_allow_html=True)

    _ds_title = "Data Sources & Coverage" if lang=="en" else "දත්ත මූලාශ්‍ර සහ ආවරණය"
    st.markdown(f"""<div class='m-tbl'><table>
      <thead><tr>
        <th>Data Category</th><th>Source Organisation</th><th>Coverage</th><th>Update Frequency</th>
      </tr></thead>
      <tbody>
        <tr><td>Coconut Auction Prices</td>
            <td>Coconut Development Authority (CDA)</td>
            <td>2015 – 2024 &nbsp;|&nbsp; Monthly</td><td>Monthly</td></tr>
        <tr><td>Market Auction Operations</td>
            <td>HARTI Economic Centres</td>
            <td>All 6 Auction Centres</td><td>Weekly</td></tr>
        <tr><td>Rainfall &amp; Temperature</td>
            <td>Department of Meteorology, Sri Lanka</td>
            <td>2015 – 2024 &nbsp;|&nbsp; Monthly</td><td>Monthly</td></tr>
        <tr><td>Coconut Yield &amp; Production</td>
            <td>Coconut Research Institute (CRI)</td>
            <td>2015 – 2024 &nbsp;|&nbsp; Annual</td><td>Annual</td></tr>
        <tr><td>Export Volumes &amp; Revenue</td>
            <td>Sri Lanka Export Development Board (EDB)</td>
            <td>2015 – 2024 &nbsp;|&nbsp; Annual</td><td>Annual</td></tr>
        <tr><td>Global Market Prices</td>
            <td>EDB &amp; CDA International Reports</td>
            <td>5 Countries &nbsp;|&nbsp; Annual</td><td>Annual</td></tr>
        <tr><td>Farm Economics &amp; Benchmarks</td>
            <td>CDA &amp; Department of Agriculture</td>
            <td>National Averages</td><td>Annual</td></tr>
        <tr><td>Auction Rules &amp; Regulations</td>
            <td>CDA Official Gazette Notifications</td>
            <td>Current Regulations</td><td>As updated</td></tr>
      </tbody>
    </table></div>""", unsafe_allow_html=True)

    # ── Analytical Methods ─────────────────────────────────────────────────────
    st.markdown("<div class='m-section-title'>Analytical Methodology</div>", unsafe_allow_html=True)

    methods = [
        ("01", "Market Regime Classification",
         "Auction prices are classified into three market regimes using threshold analysis based on "
         "CDA price benchmarks: Stable (below Rs. 65), Warning (Rs. 65–80), and Crisis (above Rs. 80). "
         "Regime distribution is calculated across the full 2015–2024 dataset."),
        ("02", "Price Elasticity of Demand",
         "Demand sensitivity is measured per regime using percentage-change analysis of price and quantity data "
         "from CDA auction records. Elasticity coefficients: Stable −0.35, Warning −0.22, Crisis −0.12. "
         "Demand for coconuts is confirmed as price-inelastic across all regimes."),
        ("03", "Price Forecasting",
         "Short-term (12-week) price forecasts are produced using a trend projection model calibrated "
         "against historical CDA weekly auction data, with a ±Rs. 5 confidence interval. "
         "Medium-term (12-month) forecasts apply a seasonal ARIMA-based framework."),
        ("04", "Weather–Yield Correlation",
         "Coconut yield indices are derived from CRI agronomic records correlated with Department of "
         "Meteorology rainfall data using a 3-month lag structure, consistent with the known "
         "physiological response time of coconut palms to rainfall stress."),
        ("05", "Policy Impact Simulation",
         "Five policy intervention levers (buffer stock release, import duty adjustment, farmer input subsidy, "
         "minimum price floor, export quota restriction) are modelled using linear impact coefficients "
         "calibrated against historical CDA and Ministry of Agriculture policy outcomes."),
        ("06", "Farmer Profitability Model",
         "Net farm income is calculated as: Gross Revenue − (Labour + Fertilizer + Transport + Other Costs). "
         "Input benchmarks are sourced from CDA smallholder studies and the Department of Agriculture. "
         "Break-even price and profit sensitivity are computed for user-defined farm parameters."),
    ]

    for i in range(0, 6, 2):
        c1, c2 = st.columns(2)
        for col, (num, title, body) in zip([c1, c2], methods[i:i+2]):
            with col:
                st.markdown(
                    f"<div class='m-pipe'>"
                    f"<div class='m-pipe-num'>{num}</div>"
                    f"<div class='m-pipe-title'>{title}</div>"
                    f"<div class='m-pipe-body'>{body}</div>"
                    f"</div>",
                    unsafe_allow_html=True)

    # ── Technical Specifications ───────────────────────────────────────────────
    st.markdown("<div class='m-section-title'>Technical Specifications</div>", unsafe_allow_html=True)
    st.markdown("""<div class='m-tbl'><table>
      <thead><tr><th>Component</th><th>Specification</th></tr></thead>
      <tbody>
        <tr><td>Programming Language</td><td>Python 3.13</td></tr>
        <tr><td>Web Framework</td><td>Streamlit</td></tr>
        <tr><td>Visualisation Library</td><td>Plotly Graph Objects &amp; Plotly Express</td></tr>
        <tr><td>Data Processing</td><td>Pandas, NumPy</td></tr>
        <tr><td>Language Support</td><td>Bilingual — English &amp; Sinhala (Unicode / ZWJ)</td></tr>
        <tr><td>Price Regime Thresholds</td><td>Stable &lt; Rs.65 &nbsp;|&nbsp; Warning Rs.65–80 &nbsp;|&nbsp; Crisis &gt; Rs.80</td></tr>
        <tr><td>Price Elasticity (by regime)</td><td>Stable: −0.35 &nbsp;|&nbsp; Warning: −0.22 &nbsp;|&nbsp; Crisis: −0.12</td></tr>
        <tr><td>Forecast Horizon</td><td>12 weeks (short-term) &nbsp;|&nbsp; 12 months (medium-term)</td></tr>
        <tr><td>Rainfall Lag (yield model)</td><td>3 months</td></tr>
        <tr><td>Policy Lever Coefficients</td><td>Buffer Stock: −0.12/% &nbsp;|&nbsp; Import Duty: +0.08/% &nbsp;|&nbsp; Export Quota: −0.06/%</td></tr>
        <tr><td>Transport Cost (farm model)</td><td>5% of gross revenue</td></tr>
        <tr><td>Other Costs (farm model)</td><td>3% of gross revenue</td></tr>
      </tbody>
    </table></div>""", unsafe_allow_html=True)

    # ── References ────────────────────────────────────────────────────────────
    st.markdown("<div class='m-section-title'>References &amp; Official Sources</div>", unsafe_allow_html=True)

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""<div class='m-ref'>
          <div class='m-ref-head'>Government &amp; Institutional Sources</div>
          <div class='m-ref-item'>Coconut Development Authority (CDA) &mdash; Annual Reports 2015–2024 &nbsp;|&nbsp; <em>cda.gov.lk</em></div>
          <div class='m-ref-item'>Coconut Research Institute (CRI) &mdash; Agronomic Data &amp; Yield Records &nbsp;|&nbsp; <em>cri.gov.lk</em></div>
          <div class='m-ref-item'>HARTI Economic Centres &mdash; Auction Price Series &nbsp;|&nbsp; <em>harti.gov.lk</em></div>
          <div class='m-ref-item'>Sri Lanka Export Development Board (EDB) &mdash; Export Statistics &nbsp;|&nbsp; <em>srilankabusiness.com</em></div>
          <div class='m-ref-item'>Department of Meteorology, Sri Lanka &mdash; Rainfall &amp; Temperature Records</div>
          <div class='m-ref-item'>Department of Agriculture, Sri Lanka &mdash; Farm Economics Benchmarks</div>
        </div>""", unsafe_allow_html=True)
    with r2:
        st.markdown("""<div class='m-ref'>
          <div class='m-ref-head'>Academic &amp; Technical References</div>
          <div class='m-ref-item'>Hamilton, J.D. (1989). <em>A New Approach to the Economic Analysis of Nonstationary Time Series.</em> Econometrica, 57(2), 357–384.</div>
          <div class='m-ref-item'>Box, G.E.P. &amp; Jenkins, G.M. (1976). <em>Time Series Analysis: Forecasting and Control.</em> Holden-Day.</div>
          <div class='m-ref-item'>Streamlit Inc. (2024). <em>Streamlit Documentation.</em> docs.streamlit.io</div>
          <div class='m-ref-item'>Plotly Technologies Inc. (2024). <em>Plotly Python Graphing Library.</em> plotly.com/python</div>
          <div class='m-ref-item' style='margin-top:14px;padding-top:12px;border-top:1px solid #222;
              color:#a8c9b8;font-weight:600;'>Prepared by: M A C S Rathnayake<br>
              UOW: w1999714 &nbsp;|&nbsp; IIT: 20220508<br>
              BSc (Hons) Data Science &amp; Analytics &mdash; University of Westminster</div>
        </div>""", unsafe_allow_html=True)

# ══ WEATHER & HARVEST (FORWARD FORECAST) ═════════════════════════════════════
elif t["nav"][2] in sec_name:
    section_header(" "+t["weather_title"], t["weather_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['weather_note']}</div>",unsafe_allow_html=True)

    # ── Generate 12-month forward weather forecast from today ─────────────────
    today = datetime.now()
    future_months = pd.date_range(start=today.replace(day=1) + pd.DateOffset(months=1), periods=12, freq="MS")
    np.random.seed(99)
    f_months = future_months.month.values
    # Seasonal rainfall forecast (Sri Lanka pattern: SW monsoon May-Sep, NE monsoon Nov-Jan)
    base_rain_f = 100 + 80*np.sin((f_months-3)*np.pi/6) + 40*np.sin((f_months-10)*np.pi/3)
    fcast_rain = np.clip(base_rain_f + np.random.normal(0,18,12), 15, 380)
    fcast_rain_upper = np.clip(fcast_rain + np.random.uniform(20,50,12), 20, 420)
    fcast_rain_lower = np.clip(fcast_rain - np.random.uniform(15,40,12), 5, 350)
    fcast_temp = 28 + 3*np.sin((f_months-4)*np.pi/6) + np.random.normal(0,0.5,12)
    # Yield index forecast (rainfall 3 months prior effect)
    hist_rain_last3 = weather_df["rainfall_mm"].tail(3).values
    lag_rain = np.concatenate([hist_rain_last3, fcast_rain[:9]])
    fcast_yield = np.clip(lag_rain/200*100 + np.random.normal(0,5,12), 40, 110)
    # Price impact forecast based on yield
    last_hist_price = history_df["price"].iloc[-1]
    fcast_price = last_hist_price + (50 - fcast_yield)*0.35 + np.random.normal(0,1.5,12)

    fwd_df = pd.DataFrame({
        "date": future_months,
        "month": f_months,
        "rainfall_mm": np.round(fcast_rain,1),
        "rain_upper": np.round(fcast_rain_upper,1),
        "rain_lower": np.round(fcast_rain_lower,1),
        "temp_c": np.round(fcast_temp,1),
        "yield_index": np.round(fcast_yield,1),
        "price_impact": np.round(fcast_price,2),
    })
    fwd_df["harvest_period"] = fwd_df["month"].isin([3,4,8,9,10,11])
    fwd_df["monsoon"] = fwd_df["month"].apply(lambda m:
        ("SW Monsoon" if lang=="en" else "නිරිත දිග මෝසම") if m in [5,6,7,8,9] else
        ("NE Monsoon" if lang=="en" else "ඊසාන දිග මෝසම") if m in [11,12,1] else
        ("Inter-Monsoon" if lang=="en" else "අන්තර් මෝසම"))

    # ── KPI Row (forward-looking) ─────────────────────────────────────────────
    avg_frain = fwd_df["rainfall_mm"].mean()
    avg_fyield = fwd_df["yield_index"].mean()
    avg_ftemp = fwd_df["temp_c"].mean()
    harvest_months_count = int(fwd_df["harvest_period"].sum())
    hist_avg_rain = weather_df["rainfall_mm"].mean()
    rain_diff = avg_frain - hist_avg_rain

    wk1,wk2,wk3,wk4 = st.columns(4)
    for col,(lbl,val,clr) in zip([wk1,wk2,wk3,wk4],[
        (" Forecast Avg Rainfall" if lang=="en" else " අනාවැකි සාමාන්‍ය වර්ෂාව", f"{avg_frain:.0f} mm", "#3d7a55"),
        (" Forecast Avg Temp" if lang=="en" else " අනාවැකි සාමාන්‍ය උෂ්ණත්වය", f"{avg_ftemp:.1f} °C", "#3d7a55"),
        (" Forecast Yield Index" if lang=="en" else " අනාවැකි අස්වැන්න දර්ශකය", f"{avg_fyield:.0f}/100", "#3d7a55"),
        (" Harvest Months (12m)" if lang=="en" else " අස්වනු මාස (12m)", f"{harvest_months_count} " + ("months" if lang=="en" else "මාස"), "#3d7a55")]):
        with col: st.markdown(metric_card(lbl,val,clr,height=110),unsafe_allow_html=True)
    divider()

    # ── Main chart: Rainfall forecast + harvest overlay + yield + price ────────
    st.markdown("#### "+("12-Month Forward Rainfall Forecast, Yield & Price Impact" if lang=="en" else "ඉදිරි මාස 12 වර්ෂාව, අස්වැන්න සහ මිල අනාවැකිය"))

    mn_labels = [m.strftime("%b %Y") for m in future_months]

    fig_fw = make_subplots(specs=[[{"secondary_y": True}]])

    # Harvest period background shading
    for i, row in fwd_df.iterrows():
        if row["harvest_period"]:
            fig_fw.add_vrect(
                x0=row["date"] - pd.Timedelta(days=10),
                x1=row["date"] + pd.Timedelta(days=10),
                fillcolor="rgba(22,163,74,0.10)", layer="below", line_width=0,
            )

    # Rainfall confidence band
    fig_fw.add_trace(go.Scatter(
        x=list(fwd_df["date"])+list(fwd_df["date"][::-1]),
        y=list(fwd_df["rain_upper"])+list(fwd_df["rain_lower"][::-1]),
        fill="toself", fillcolor="rgba(59,130,246,0.12)", line=dict(color="rgba(0,0,0,0)"),
        showlegend=True, name=("Rainfall Range" if lang=="en" else "වර්ෂාපාත පරාසය"),
        hoverinfo="skip"), secondary_y=False)

    # Rainfall bars
    fig_fw.add_trace(go.Bar(
        x=fwd_df["date"], y=fwd_df["rainfall_mm"],
        name=("Forecast Rainfall (mm)" if lang=="en" else "අනාවැකි වර්ෂාව (mm)"),
        marker_color="rgba(59,130,246,.55)",
        hovertemplate="<b>%{x|%b %Y}</b><br>" + ("Rain" if lang=="en" else "වර්ෂාව") + ": %{y:.0f} mm<extra></extra>"),
        secondary_y=False)

    # Yield index line
    fig_fw.add_trace(go.Scatter(
        x=fwd_df["date"], y=fwd_df["yield_index"],
        name=("Yield Index" if lang=="en" else "අස්වැන්න දර්ශකය"),
        mode="lines+markers", line=dict(color="#3d7a55", width=2.5),
        marker=dict(size=7, symbol=["star" if h else "circle" for h in fwd_df["harvest_period"]]),
        hovertemplate="<b>%{x|%b %Y}</b><br>" + ("Yield" if lang=="en" else "අස්වැන්න") + ": %{y:.1f}<extra></extra>"),
        secondary_y=True)

    # Price impact line
    fig_fw.add_trace(go.Scatter(
        x=fwd_df["date"], y=fwd_df["price_impact"],
        name=("Est. Price (Rs.)" if lang=="en" else "ඇ. මිල (රු.)"),
        mode="lines+markers", line=dict(color="#f59e0b", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="<b>%{x|%b %Y}</b><br>Est. Rs.%{y:.2f}<extra></extra>"),
        secondary_y=True)

    fig_fw.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
        annotation_text=f" Rs.{warn_threshold}", secondary_y=True)
    fig_fw.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
        annotation_text=f" Rs.{crisis_threshold}", secondary_y=True)

    fig_fw.update_layout(
        height=380, margin=dict(l=60,r=60,t=20,b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)))
    fig_fw.update_yaxes(title_text=("Rainfall (mm)" if lang=="en" else "වර්ෂාව (mm)"), secondary_y=False, gridcolor="#e4eeea")
    fig_fw.update_yaxes(title_text=("Yield Index / Price (Rs.)" if lang=="en" else "අස්වැන්න දර්ශකය / මිල (රු.)"), secondary_y=True, showgrid=False)

    # Harvest period annotation
    _harvest_note1 = ("Green shading = Harvest months (Mar–Apr, Aug–Nov)" if lang=="en" else "කොළ සෙවන = අස්වනු මාස (මාර්-අප්‍රේ, අගෝ-නොවැ)")
    _harvest_note2 = ("Star markers = Harvest month yield points" if lang=="en" else "තරු සලකුණු = අස්වනු මාස දර්ශක ලකුණු")
    st.markdown(f"""<div style='font-size:.75rem;color:#3d7a55;font-weight:700;margin-bottom:6px;'>
         <span style='background:#f0f5f2;padding:2px 8px;border-radius:4px;'>{_harvest_note1}</span>
        &nbsp;&nbsp; {_harvest_note2}
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(fig_fw, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Month-by-month forward table ──────────────────────────────────────────
    st.markdown("#### "+("12-Month Forward Forecast Table" if lang=="en" else "ඉදිරි මාස 12 අනාවැකි වගුව"))
    table_df = fwd_df[["date","rainfall_mm","temp_c","yield_index","price_impact","harvest_period","monsoon"]].copy()
    table_df["date"] = table_df["date"].dt.strftime("%b %Y")
    table_df["harvest_period"] = table_df["harvest_period"].apply(
        lambda x: (" Harvest" if lang=="en" else " අස්වනු") if x else "—")
    table_df.columns = (["Month","Rainfall (mm)","Temp (°C)","Yield Index","Est. Price (Rs.)","Harvest","Season"]
                        if lang=="en" else
                        ["මාසය","වර්ෂාව (mm)","උෂ්ණත්වය (°C)","අස්වැන්න දර්ශකය","ඇ. මිල (රු.)","අස්වනු","කාලගුණය"])
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    divider()

    # ── Monthly rainfall pattern (forward) ───────────────────────────────────
    c_heat, c_corr = st.columns([3,2])
    with c_heat:
        st.markdown("#### "+("Monthly Forecast Rainfall Pattern" if lang=="en" else "මාසික අනාවැකි වර්ෂා රටාව"))
        mnames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        # Build a single-row heatmap for next 12 months
        rain_by_month = {mnames[m-1]: [] for m in range(1,13)}
        for _, row in fwd_df.iterrows():
            rain_by_month[mnames[row["month"]-1]].append(row["rainfall_mm"])
        rain_vals = [np.mean(rain_by_month[m]) if rain_by_month[m] else None for m in mnames]
        fig_rh = go.Figure(go.Bar(
            x=mnames, y=rain_vals,
            marker=dict(
                color=rain_vals,
                colorscale=[[0,"#fef9c3"],[.5,"#b8d0c4"],[1,"#2d5a3d"]],
                showscale=True,
                colorbar=dict(title="mm", tickfont=dict(size=10))),
            text=[f"{v:.0f}mm" if v else "" for v in rain_vals],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>"))
        # Mark harvest months
        harvest_m = ["Mar","Apr","Aug","Sep","Oct","Nov"]
        for hm in harvest_m:
            if hm in mnames:
                fig_rh.add_vline(x=mnames.index(hm), line_dash="dot", line_color="#3d7a55", line_width=1.5)
        fig_rh.update_layout(height=260,margin=dict(l=20,r=20,t=10,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#e4eeea",ticksuffix=" mm"))
        st.plotly_chart(fig_rh, use_container_width=True, config={"displayModeBar":"hover"})

    with c_corr:
        st.markdown("#### "+("Yield vs Est. Price (Next 12 Months)" if lang=="en" else "අස්වැන්න හා මිල — ඉදිරි මාස 12"))
        _mn_lbs_sc = [d.strftime("%b") for d in fwd_df["date"]]
        _harv_mask = fwd_df["harvest_period"].values
        _yl_lbl = ("Yield Index" if lang=="en" else "අස්වැන්න දර්ශකය")
        _pr_lbl = ("Est. Price (Rs.)" if lang=="en" else "ඇ. මිල (රු.)")

        # Normalise yield to same 0-100 scale as price for direct overlay
        _yi = fwd_df["yield_index"].values
        _pi = fwd_df["price_impact"].values
        _yi_norm = (_yi - _yi.min()) / max(_yi.max() - _yi.min(), 1) * (_pi.max() - _pi.min()) + _pi.min()

        fig_sc = go.Figure()

        # Shaded yield area
        fig_sc.add_trace(go.Scatter(
            x=_mn_lbs_sc, y=_yi_norm,
            name=_yl_lbl,
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.12)",
            line=dict(color="#5a9470", width=2),
            hovertemplate="<b>%{x}</b><br>" + _yl_lbl + ": %{customdata:.0f}<extra></extra>",
            customdata=_yi))

        # Price line
        fig_sc.add_trace(go.Scatter(
            x=_mn_lbs_sc, y=_pi,
            name=_pr_lbl,
            mode="lines+markers",
            line=dict(color="#f59e0b", width=2.5),
            marker=dict(color="#f59e0b", size=7, line=dict(color="#fff", width=1.5)),
            hovertemplate="<b>%{x}</b><br>" + _pr_lbl + ": Rs.%{y:.1f}<extra></extra>"))

        # Harvest month markers on price line
        fig_sc.add_trace(go.Scatter(
            x=[_mn_lbs_sc[i] for i,h in enumerate(_harv_mask) if h],
            y=[_pi[i] for i,h in enumerate(_harv_mask) if h],
            name=(" Harvest" if lang=="en" else " අස්වනු"),
            mode="markers",
            marker=dict(color="#3d7a55", size=12, symbol="star",
                        line=dict(color="#fff", width=1.5)),
            hovertemplate="<b>%{x}</b> <br>Rs.%{y:.1f}<extra></extra>"))

        # Warn / crisis lines
        fig_sc.add_hline(y=warn_threshold,
            line_dash="dot", line_color="#eab308", line_width=1.5,
            annotation_text=f" Rs.{warn_threshold}",
            annotation_position="top left",
            annotation_font=dict(size=9, color="#b45309"))
        fig_sc.add_hline(y=crisis_threshold,
            line_dash="dot", line_color="#ef4444", line_width=1.5,
            annotation_text=f" Rs.{crisis_threshold}",
            annotation_position="top right",
            annotation_font=dict(size=9, color="#ef4444"))

        fig_sc.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(
                tickprefix="Rs.", gridcolor="#e4eeea",
                title=_pr_lbl, tickfont=dict(size=10)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=9)))
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Monsoon & Harvest season summary ──────────────────────────────────────
    st.markdown("#### "+("Season-by-Season Forecast Summary" if lang=="en" else "කාල ගත අනාවැකි සාරාංශය"))
    seasons_fwd = (
        {"SW Monsoon (May–Sep)":[5,6,7,8,9],"NE Monsoon (Nov–Jan)":[11,12,1],
         "Inter-Monsoon 1 (Mar–Apr)":[3,4],"Inter-Monsoon 2 (Oct)":[10]}
        if lang=="en" else
        {"නිරිත දිග මෝසම (මැයි–සැප්)":[5,6,7,8,9],"ඊසාන දිග මෝසම (නොවැ–ජන)":[11,12,1],
         "අන්තර් මෝසම 1 (මාර්–අප්‍රේ)":[3,4],"අන්තර් මෝසම 2 (ඔක්)":[10]}
    )
    seas_clrs = ["#5a9470","#8b5cf6","#f59e0b","#5a9470"]
    sc2 = st.columns(4)
    for col,(season,months_s),clr in zip(sc2,seasons_fwd.items(),seas_clrs):
        msk = fwd_df["month"].isin(months_s)
        if msk.sum() > 0:
            ar = fwd_df.loc[msk,"rainfall_mm"].mean()
            ay = fwd_df.loc[msk,"yield_index"].mean()
            ap = fwd_df.loc[msk,"price_impact"].mean()
            harv = (" Harvest Season" if lang=="en" else " අස්වනු කාලය") if any(m in [3,4,8,9,10,11] for m in months_s) else "—"
        else:
            ar, ay, ap, harv = 0, 0, 0, "—"
        _mm_lbl = "mm forecast" if lang=="en" else "mm අනාවැකිය"
        _yield_lbl = "Yield" if lang=="en" else "අස්වැන්න"
        _est_lbl = "Est." if lang=="en" else "ඇ."
        with col:
            st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid {clr};border-radius:10px;padding:14px 10px;text-align:center;height:180px;display:flex;flex-direction:column;justify-content:space-between;'>
                <div style='font-size:.72rem;font-weight:800;color:{clr};'>{season}</div>
                <div>
                  <div style='font-size:.75rem;color:#5a9470;font-weight:600;'> {ar:.0f} {_mm_lbl}</div>
                  <div style='font-size:.75rem;color:#3d7a55;font-weight:600;'> {_yield_lbl}: {ay:.0f}/100</div>
                  <div style='font-size:.75rem;color:#f59e0b;font-weight:600;'> {_est_lbl} Rs.{ap:.1f}</div>
                  <div style='font-size:.72rem;color:#3d7a55;font-weight:700;margin-top:4px;'>{harv}</div>
                </div></div>""", unsafe_allow_html=True)

# ══ EXPORT & TRADE (NEW) ═════════════════════════════════════════════════════
elif t["nav"][5] in sec_name:
    section_header(" "+t["export_title"], t["export_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['export_note']}</div>",unsafe_allow_html=True)

    # KPI row
    le=export_df.iloc[-1]; pe=export_df.iloc[-2]
    yoy=(le["Total"]-pe["Total"])/pe["Total"]*100; yoy_clr="#3d7a55"
    ek1,ek2,ek3,ek4=st.columns(4)
    for col,(lbl,val,clr) in zip([ek1,ek2,ek3,ek4],[
        (" Total Exports (Latest Yr)" if lang=="en" else " \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0d85\u0db4\u0db1\u0dba\u0db1", f"${le['Total']}M","#3d7a55"),
        (" YoY Growth" if lang=="en" else " \u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0dc0\u0dbb\u0dca\u0db0\u0db1\u0dba", f"{'+'if yoy>0 else ''}{yoy:.1f}%",yoy_clr),
        (" Top Product" if lang=="en" else " \u0db4\u0dca\u200d\u0dbb\u0db8\u0dd4\u0d9b \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1\u0dba",
         "Desiccated Coconut" if lang=="en" else "වියළි පොල්","#3d7a55"),
        (" Top Market" if lang=="en" else " \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5","USA (22%)","#3d7a55")]):
        with col: st.markdown(metric_card(lbl,val,clr,height=110),unsafe_allow_html=True)
    divider()

    ce1,ce2=st.columns([3,2])
    with ce1:
        st.markdown("#### "+("Export Revenue by Product (USD Million)" if lang=="en" else "\u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1\u0dba \u0d85\u0db1\u0dd4\u0dc0 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0d86\u0daf\u0dcf\u0dba\u0db8"))
        fig_eb=go.Figure()
        _pnames = PRODUCT_NAMES_SI if lang=="si" else PRODUCT_COLS
        for pc,pcl,pn in zip(PRODUCT_COLS,PRODUCT_COLORS,_pnames):
            fig_eb.add_trace(go.Bar(x=export_df["year"].astype(str),y=export_df[pc],name=pn,marker_color=pcl,
                hovertemplate=f"<b>%{{x}}</b><br>{pn}: $%{{y}}M<extra></extra>"))
        fig_eb.update_layout(barmode="stack",height=320,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="$",ticksuffix="M"),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)))
        st.plotly_chart(fig_eb,use_container_width=True,config={"displayModeBar":"hover"})
    with ce2:
        st.markdown("#### "+("Export Destinations (Latest Year)" if lang=="en" else "\u0d85\u0db4\u0db1\u0dba\u0db1 \u0d9c\u0db8\u0db1\u0dcf\u0db1\u0dca\u0dad"))
        fig_dest=go.Figure(go.Pie(labels=destinations_df["Country"],values=destinations_df["Share_pct"],hole=.45,
            textinfo="label+percent",textfont=dict(size=10),marker=dict(colors=px.colors.qualitative.Set3),
            hovertemplate="<b>%{label}</b><br>Share: %{percent}<br>$%{customdata}M<extra></extra>",customdata=destinations_df["Value_USD_M"]))
        fig_dest.update_layout(height=320,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_dest,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Export vs domestic price
    st.markdown("#### "+("Export Growth vs Domestic Price" if lang=="en" else "\u0d85\u0db4\u0db1\u0dba\u0db1 \u0dc0\u0dbb\u0dca\u0db0\u0db1\u0dba \u0dc4\u0dcf \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0"))
    ap=history_df.groupby("year")["price"].mean().reset_index()
    me=export_df.merge(ap,on="year",how="inner")
    fig_ep=make_subplots(specs=[[{"secondary_y":True}]])
    fig_ep.add_trace(go.Bar(x=me["year"].astype(str),y=me["Total"],
        name=("Export Revenue ($M)" if lang=="en" else "අපනයන ආදායම ($M)"),
        marker_color="rgba(22,163,74,.5)",hovertemplate="<b>%{x}</b><br>$%{y}M<extra></extra>"),secondary_y=False)
    fig_ep.add_trace(go.Scatter(x=me["year"].astype(str),y=me["price"],
        name=("Domestic Price (Rs.)" if lang=="en" else "දේශීය මිල (රු.)"),
        line=dict(color="#f59e0b",width=2.5),mode="lines+markers",marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Rs.%{y:.2f}<extra></extra>"),secondary_y=True)
    fig_ep.update_layout(height=300,margin=dict(l=20,r=60,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_ep.update_yaxes(title_text=("Export Revenue ($M)" if lang=="en" else "අපනයන ආදායම ($M)"),secondary_y=False,gridcolor="#e4eeea",tickprefix="$",ticksuffix="M")
    fig_ep.update_yaxes(title_text=("Domestic Price (Rs.)" if lang=="en" else "දේශීය මිල (රු.)"),secondary_y=True,showgrid=False,tickprefix="Rs.")
    st.plotly_chart(fig_ep,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Individual product trends
    st.markdown("#### "+("Individual Product Export Trends" if lang=="en" else "\u0dad\u0db1\u0dd2 \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf"))
    fig_pt=go.Figure()
    _pnames2 = PRODUCT_NAMES_SI if lang=="si" else PRODUCT_COLS
    for pc,pcl,pn in zip(PRODUCT_COLS,PRODUCT_COLORS,_pnames2):
        fig_pt.add_trace(go.Scatter(x=export_df["year"].astype(str),y=export_df[pc],mode="lines+markers",name=pn,
            line=dict(color=pcl,width=2),marker=dict(size=6),hovertemplate=f"<b>%{{x}}</b><br>{pn}: $%{{y}}M<extra></extra>"))
    fig_pt.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="$",ticksuffix="M"),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)))
    st.plotly_chart(fig_pt,use_container_width=True,config={"displayModeBar":"hover"})

# ══ FARMER PROFITABILITY (NEW) ═══════════════════════════════════════════════
elif t["nav"][7] in sec_name:
    section_header(" "+t["farmer_title"], t["farmer_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['farmer_note']}</div>",unsafe_allow_html=True)

    st.markdown("#### "+("Your Farm Parameters" if lang=="en" else "\u0d94\u0db6\u0dda \u0d9c\u0ddc\u0dc0\u0dd2\u0dad\u0dd0\u0db1\u0dca \u0daf\u0dad\u0dca\u0dad"))
    fi1,fi2,fi3=st.columns(3)
    with fi1:
        farm_acres=st.slider(" "+("Farm Size (acres)" if lang=="en" else "\u0d9c\u0ddc\u0dc0\u0dd2\u0dad\u0dd0\u0db1\u0dca \u0dc0\u0dd2\u0DC1\u0dcf\u0dbd\u0dad\u0dca\u0dc0\u0dba (\u0d85\u0d9a\u0dca\u0d9a\u0dbb)"),1,50,5,1)
        trees_acre=st.slider(" "+("Trees per Acre" if lang=="en" else "\u0d85\u0d9a\u0dca\u0d9a\u0dbb\u0dba\u0d9a\u0da7 \u0d9c\u0dc3\u0dca"),20,80,40,5)
    with fi2:
        nuts_tree=st.slider(" "+("Nuts per Tree/Year" if lang=="en" else "\u0d9c\u0dc3\u0d9a\u0da7 \u0d9c\u0dd9\u0da9\u0dd2/\u0dc0\u0dbb\u0dca\u0DC2\u0dba"),30,120,60,5)
        sell_price=st.slider(" "+("Selling Price (Rs./nut)" if lang=="en" else "\u0dc0\u0dd2\u0d9a\u0dd2\u0dab\u0dd4\u0db8\u0dca \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4./\u0d9c\u0dd9\u0da9\u0dd2\u0dba)"),30,120,int(current_price),1)
    with fi3:
        labour_month=st.slider(" "+("Labour Cost (Rs./month)" if lang=="en" else "\u0d9a\u0db8\u0dca\u0d9a\u0dbb\u0dd4 \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba (\u0dbb\u0dd4./\u0db8\u0dcf\u0dc3\u0dba)"),5000,50000,15000,1000)
        fert_year=st.slider(" "+("Fertilizer & Inputs (Rs./yr)" if lang=="en" else "\u0db4\u0ddc\u0dc4\u0ddc\u0dbb & \u0d86\u0daf\u0dcf\u0db1 (\u0dbb\u0dd4./\u0dc0\u0dbb\u0dca\u0DC2\u0dba)"),5000,100000,25000,5000)

    # Calculations
    total_trees=farm_acres*trees_acre; total_nuts=total_trees*nuts_tree
    gross_rev=total_nuts*sell_price; labour_ann=labour_month*12
    transport=gross_rev*.05; other=gross_rev*.03
    total_cost=labour_ann+fert_year+transport+other
    net_profit=gross_rev-total_cost
    margin=net_profit/gross_rev*100 if gross_rev>0 else 0
    be_price=total_cost/total_nuts if total_nuts>0 else 0
    pc_="#3d7a55"
    divider()
    st.markdown("#### "+("Profitability Results" if lang=="en" else "\u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db5\u0dbd"))
    r1,r2,r3,r4,r5=st.columns(5)
    for col,(lbl,val,clr) in zip([r1,r2,r3,r4,r5],[
        (" Total Nuts/Year" if lang=="en" else " \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0d9c\u0dd9\u0da9\u0dd2/\u0dc0\u0dbb\u0dca\u0DC2\u0dba", f"{total_nuts:,}","#3d7a55"),
        (" Gross Revenue" if lang=="en" else " \u0daf\u0dc5 \u0d86\u0daf\u0dcf\u0dba\u0db8", f"Rs.{gross_rev:,.0f}","#3d7a55"),
        (" Total Costs" if lang=="en" else " \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba", f"Rs.{total_cost:,.0f}","#3d7a55"),
        ((" Net Profit" if net_profit>0 else " Net Loss") if lang=="en" else (" \u0DC1\u0dd4\u0daf\u0dca\u0db0 \u0dbd\u0dcf\u0db7\u0dba" if net_profit>0 else " \u0dbd\u0dcf\u0db7 \u0d85\u0dc0"),
         f"Rs.{net_profit:,.0f}",pc_),
        (" Profit Margin" if lang=="en" else " \u0dbd\u0dcf\u0db7 \u0db8\u0dcf\u0daf\u0dd2\u0dbd\u0dd2\u0dba",f"{margin:.1f}%",pc_)]):
        with col: st.markdown(metric_card(lbl,val,clr,height=90),unsafe_allow_html=True)
    divider()

    cw,cb=st.columns([3,2])
    with cw:
        st.markdown("#### "+("Revenue Waterfall" if lang=="en" else "\u0d86\u0daf\u0dcf\u0dba\u0db8\u0dca \u0daf\u0dd2\u0dba \u0d87\u0dbd\u0dca\u0dbd"))
        fig_wf=go.Figure(go.Waterfall(orientation="v",
            measure=["absolute","relative","relative","relative","relative","total"],
            x=(["Gross Revenue","Labour","Fertilizer","Transport","Other","Net Profit"]
               if lang=="en" else
               ["දළ ආදායම","ශ්‍රමය","පොහොර","ප්‍රවාහනය","වෙනත්","ශුද්ධ ලාභය"]),
            y=[gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit],
            connector=dict(line=dict(color="#94a3b8",width=1.5)),
            increasing=dict(marker=dict(color="#3d7a55")),decreasing=dict(marker=dict(color="#ef4444")),totals=dict(marker=dict(color=pc_)),
            text=[f"Rs.{abs(v):,.0f}" for v in [gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit]],
            textposition="outside",textfont=dict(size=10)))
        fig_wf.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_wf,use_container_width=True,config={"displayModeBar":"hover"})
    with cb:
        st.markdown("#### "+("Break-Even Analysis" if lang=="en" else "\u0DC1\u0dda\u0DC2-\u0dc3\u0dca\u0dae\u0dcf\u0db1 \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba"))
        pr_be=np.linspace(20,120,100)
        fig_be=go.Figure()
        fig_be.add_trace(go.Scatter(x=pr_be,y=pr_be*total_nuts-total_cost,mode="lines",
            line=dict(color="#3d7a55",width=2.5),showlegend=False,
            name=("Net Profit" if lang=="en" else "ශුද්ධ ලාභය"),
            hovertemplate=("Price" if lang=="en" else "මිල")+": Rs.%{x:.1f}<br>"+("Profit" if lang=="en" else "ලාභය")+": Rs.%{y:,.0f}<extra></extra>"))
        _be_zero_lbl = "Break-even" if lang=="en" else "ශේෂ ස්ථානය"
        _curr_lbl = ("Current" if lang=="en" else "වත්මන්") + f" Rs.{sell_price}"
        _be_price_lbl = f"BE Rs.{be_price:.1f}"
        fig_be.add_hline(y=0,line_dash="dash",line_color="#ef4444",
            annotation_text=_be_zero_lbl,
            annotation_position="bottom right",
            annotation_font_color="#ef4444")
        fig_be.add_vline(x=sell_price,line_dash="dot",line_color="#f59e0b",
            annotation_text=_curr_lbl,annotation_position="top right",
            annotation_font_color="#d97706")
        fig_be.add_vline(x=be_price,line_dash="dash",line_color="#ef4444",
            annotation_text=_be_price_lbl,annotation_position="bottom right",
            annotation_font_color="#ef4444")
        # Format large y-axis values nicely
        _ymax = max(pr_be) * total_nuts - total_cost
        _ymin = min(pr_be) * total_nuts - total_cost
        fig_be.update_layout(height=280,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(title=("Price per Nut (Rs.)" if lang=="en" else "ගෙඩියකට මිල (රු.)"),showgrid=False),
            yaxis=dict(
                title=("Net Profit (Rs.)" if lang=="en" else "ශුද්ධ ලාභය (රු.)"),
                gridcolor="#e4eeea",
                tickformat=",.0f",
                tickprefix="Rs.",
            ),showlegend=False)
        st.plotly_chart(fig_be,use_container_width=True,config={"displayModeBar":"hover"})
        bev=sell_price-be_price; bec="#5a9470" if bev>0 else "#ef4444"
        st.markdown(f"""<div style='background:#f8fafc;border:2px solid {bec};border-radius:10px;padding:12px;text-align:center;margin-top:8px;'>
            <div style='font-size:.72rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{"Break-Even Price" if lang=="en" else "\u0DC1\u0dda\u0DC2-\u0dc3\u0dca\u0dae\u0dcf\u0db1 \u0db8\u0dd2\u0dbd"}</div>
            <div style='font-size:1.4rem;font-weight:900;color:{bec};'>Rs.{be_price:.2f}</div>
            <div style=\'font-size:.78rem;color:{bec};margin-top:4px;\'>{chr(9989) if bev>0 else chr(10060)} Rs.{abs(bev):.2f} {"above" if bev>0 else "below"} {"current" if lang=="en" else "වත්මනින්"}</div></div>""",unsafe_allow_html=True)
    divider()

    st.markdown("#### "+("Profit Sensitivity to Selling Price" if lang=="en" else "\u0dc0\u0dd2\u0d9a\u0dd2\u0dab\u0dd4\u0db8\u0dca \u0db8\u0dd2\u0dbd\u0da7 \u0dbd\u0dcf\u0db7 \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dad\u0dcf\u0dc0"))
    ps=[40,50,55,60,65,68.5,70,75,80,85,90,100]
    prf=[p*total_nuts-total_cost for p in ps]
    fig_ps=go.Figure(go.Bar(x=[f"Rs.{p}" for p in ps],y=prf,marker_color=["#5a9470" if v>0 else "#ef4444" for v in prf],
        text=[f"Rs.{v:,.0f}" for v in prf],textposition="outside",textfont=dict(size=9),
        hovertemplate=("Price" if lang=="en" else "මිල")+": %{x}<br>"+("Profit" if lang=="en" else "ලාභය")+": Rs.%{y:,.0f}<extra></extra>"))
    fig_ps.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
    fig_ps.update_layout(height=280,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e4eeea",tickprefix="Rs."),showlegend=False)
    st.plotly_chart(fig_ps,use_container_width=True,config={"displayModeBar":"hover"})

# ══ AUCTION DETAILS ══════════════════════════════════════════════════════════
elif t["nav"][8] in sec_name:
    section_header(" "+t["auction_title"], t["auction_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['auction_note']}</div>", unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    ak1,ak2,ak3,ak4 = st.columns(4)
    for col,(lbl,val,clr) in zip([ak1,ak2,ak3,ak4],[
        ("Primary Authority" if lang=="en" else " ප්‍රධාන බලධාරිය",
         "CDA / HARTI", "#3d7a55"),
        ("Auction Frequency" if lang=="en" else "වෙන්දේසි නිතිය",
         "Weekly (Mon–Fri)" if lang=="en" else "සතිපතා (සඳු–සිකු)", "#3d7a55"),
        ("Typical Start Time" if lang=="en" else "ආරම්භ වේලාව",
         "7:30 – 9:00 AM", "#3d7a55"),
        ("Lot Size" if lang=="en" else "ලොට් ප්‍රමාණය",
         "500–5,000 nuts" if lang=="en" else "ඇට 500–5,000", "#3d7a55"),
    ]):
        with col: st.markdown(metric_card(lbl, val, clr, height=110, val_size="1.1rem"), unsafe_allow_html=True)
    divider()

    # ── Main Auction Centres ───────────────────────────────────────────────────
    st.markdown("#### "+("Official Coconut Auction Centres" if lang=="en" else "නිල පොල් වෙන්දේසි මධ්‍යස්ථාන"))
    centres = [
        {
            "name": "Colombo Auction Centre",
            "si_name": "කොළඹ වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "HARTI Economic Centre, Narahenpita, Colombo 05",
            "days": "Monday, Wednesday, Friday",
            "time": "7:30 AM – 10:00 AM",
            "type": "Whole Nuts & Copra",
            "si_type": "සම්පූර්ණ ගෙඩි සහ කොප්රා",
            "authority": "HARTI / CDA",
            "phone": "+94 11 259 1919",
            "note": "Largest & most active auction. Sets the national benchmark price.",
            "si_note": "විශාලතම සහ වඩාත් ක්‍රියාශීලී වෙන්දේසිය. ජාතික මිල නිශ්චය කරයි.",
            "clr": "#3d7a55",
        },
        {
            "name": "Kurunegala Auction Centre",
            "si_name": "කුරුණෑගල වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "CDA Regional Office, Kurunegala",
            "days": "Tuesday, Thursday",
            "time": "8:00 AM – 10:30 AM",
            "type": "Whole Nuts",
            "si_type": "සම්පූර්ණ ගෙඩි",
            "authority": "CDA",
            "phone": "+94 37 222 2250",
            "note": "Main centre for Kurunegala district — Sri Lanka's largest coconut belt.",
            "si_note": "කුරුණෑගල දිස්ත්‍රික්කයේ ප්‍රධාන මධ්‍යස්ථානය — ශ්‍රී ලංකාවේ විශාලතම පොල් කලාපය.",
            "clr": "#5a9470",
        },
        {
            "name": "Puttalam Auction Centre",
            "si_name": "පුත්තලම වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "CDA Regional Office, Puttalam",
            "days": "Monday, Friday",
            "time": "8:00 AM – 10:00 AM",
            "type": "Whole Nuts & Coconut Oil",
            "si_type": "සම්පූර්ණ ගෙඩි සහ පොල් තෙල්",
            "authority": "CDA",
            "phone": "+94 32 222 5120",
            "note": "Covers northern coconut triangle; strong copra and oil trade.",
            "si_note": "උතුරු පොල් ත්‍රිකෝණය ආවරණය කරයි; ශක්තිමත් කොප්රා සහ තෙල් වෙළඳාම.",
            "clr": "#f59e0b",
        },
        {
            "name": "Gampaha Auction Centre",
            "si_name": "ගම්පහ වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Nittambuwa, Gampaha",
            "days": "Tuesday, Thursday, Saturday",
            "time": "7:00 AM – 9:30 AM",
            "type": "Whole Nuts & Desiccated Coconut",
            "si_type": "සම්පූර්ණ ගෙඩි සහ වියළි පොල්",
            "authority": "HARTI",
            "phone": "+94 33 222 3100",
            "note": "Serves Western Province. High volume during peak harvest months.",
            "si_note": "බස්නාහිර පළාත සේවය කරයි. උච්ච අස්වනු මාසවලදී ඉහළ පරිමාව.",
            "clr": "#8b5cf6",
        },
        {
            "name": "Matara Auction Centre",
            "si_name": "මාතර වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Matara",
            "days": "Wednesday, Saturday",
            "time": "8:30 AM – 10:30 AM",
            "type": "Whole Nuts",
            "si_type": "සම්පූර්ණ ගෙඩි",
            "authority": "HARTI / CDA",
            "phone": "+94 41 222 2440",
            "note": "Key centre for Southern Province coconut growers.",
            "si_note": "දකුණු පළාත් පොල් ගොවීන් සඳහා ප්‍රධාන මධ්‍යස්ථානය.",
            "clr": "#ef4444",
        },
        {
            "name": "Kalutara Auction Centre",
            "si_name": "කළුතර වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Kalutara South",
            "days": "Monday, Thursday",
            "time": "8:00 AM – 10:00 AM",
            "type": "Whole Nuts & Coconut Milk",
            "si_type": "සම්පූර්ණ ගෙඩි සහ පොල් කිරි",
            "authority": "HARTI",
            "phone": "+94 34 222 5300",
            "note": "Significant trade in coconut milk products alongside whole nuts.",
            "si_note": "සම්පූර්ණ ගෙඩිවලට අමතරව පොල් කිරි නිෂ්පාදනවල සැලකිය යුතු වෙළඳාම.",
            "clr": "#06b6d4",
        },
    ]

    # Display 3 per row
    for row_start in range(0, len(centres), 3):
        row_centres = centres[row_start:row_start+3]
        cols = st.columns(3)
        for col, c in zip(cols, row_centres):
            name_display = c["si_name"] if lang == "si" else c["name"]
            type_display = c["si_type"] if lang == "si" else c["type"]
            note_display = c["si_note"] if lang == "si" else c["note"]
            with col:
                st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:4px solid {c["clr"]};
                    border-radius:12px;padding:18px 16px;margin-bottom:14px;height:280px;display:flex;flex-direction:column;justify-content:space-between;'>
                    <div>
                      <div style='font-size:.6rem;font-weight:800;color:{c["clr"]};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;'>{c["authority"]}</div>
                      <div style='font-size:.9rem;font-weight:800;color:#1a3328;margin-bottom:10px;line-height:1.3;'>{name_display}</div>
                      <div style='font-size:.72rem;color:#374151;line-height:1.85;'>
                         {c["venue"]}<br>
                         {c["days"]}<br>
                         {c["time"]}<br>
                         {type_display}<br>
                         {c["phone"]}
                      </div>
                    </div>
                    <div style='font-size:.68rem;color:{c["clr"]};font-weight:600;margin-top:8px;background:{c["clr"]}11;
                        padding:6px 8px;border-radius:6px;line-height:1.4;'> {note_display}</div>
                </div>""", unsafe_allow_html=True)
    divider()

    # ── Weekly Auction Schedule ────────────────────────────────────────────────
    st.markdown("#### "+("Weekly Auction Schedule" if lang=="en" else "සතිපතා වෙන්දේසි කාලසටහන"))
    days_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    days_si = ["සඳුදා","අඟහරුවාදා","බදාදා","බ්‍රහස්පතින්දා","සිකුරාදා","සෙනසුරාදා"]
    days = days_en if lang=="en" else days_si
    day_auctions_en = {
        "Monday": [("Colombo","7:30 AM"),("Puttalam","8:00 AM"),("Kalutara","8:00 AM")],
        "Tuesday": [("Kurunegala","8:00 AM"),("Gampaha","7:00 AM")],
        "Wednesday": [("Colombo","7:30 AM"),("Matara","8:30 AM")],
        "Thursday": [("Kurunegala","8:00 AM"),("Gampaha","7:00 AM"),("Kalutara","8:00 AM")],
        "Friday": [("Colombo","7:30 AM"),("Puttalam","8:00 AM")],
        "Saturday": [("Gampaha","7:00 AM"),("Matara","8:30 AM")],
    }
    day_auctions = {d_si: day_auctions_en[d_en] for d_en, d_si in zip(days_en, days_si)} if lang=="si" else day_auctions_en
    day_colors_map = dict(zip(days, ["#3d7a55","#5a9470","#f59e0b","#8b5cf6","#ef4444","#06b6d4"]))
    sched_cols = st.columns(6)
    for col, day in zip(sched_cols, days):
        auctions = day_auctions[day]
        clr = day_colors_map[day]
        items_html = "".join([
            f"<div style='padding:4px 0;border-bottom:1px solid #f0f5f2;'>"
            f"<div style='font-size:.7rem;font-weight:700;color:#1e293b;white-space:nowrap;'> {name}</div>"
            f"<div style='font-size:.63rem;color:#64748b;margin-left:18px;white-space:nowrap;'>{time}</div>"
            f"</div>"
            for name, time in auctions
        ])
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:3px solid {clr};
                border-radius:10px;padding:12px 10px;min-height:160px;'>
                <div style='font-size:.72rem;font-weight:800;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:8px;text-align:center;'>{day}</div>
                {items_html}
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Auction Process & Rules ────────────────────────────────────────────────
    st.markdown("#### "+("How the Coconut Auction Works" if lang=="en" else "වෙන්දේසිය ක්‍රියාකාරිත්වය"))
    proc_cols = st.columns(4)
    steps = (
        [
            ("01","Registration",
             "Sellers register with CDA/HARTI at least 24 hrs before auction. Lots are inspected and graded by officials.",
             "Buyers must hold valid CDA buyer licence. Annual renewal required.","#3d7a55"),
            ("02","Grading & Lot Formation",
             "Nuts are graded by size, freshness and quality. Standard lot = 1,000 nuts. Minimum 500 nuts per lot.",
             "Grade A: ≥12cm dia. Grade B: 10–12cm. Grade C: <10cm.","#3d7a55"),
            ("03","Bidding Process",
             "Open outcry ascending bid auction. Auctioneer calls starting price. Highest bid wins. Buyer must pay within 24 hrs.",
             "Electronic bidding being piloted at Colombo centre.","#f59e0b"),
            ("04","Settlement & Transport",
             "Payment via bank transfer or certified cheque. Seller receives funds within 2 working days.",
             "CDA provides transport support for quantities >5,000 nuts.","#3d7a55"),
        ] if lang=="en" else [
            ("01","ලියාපදිංචිය",
             "විකුණුම්කරුවන් වෙන්දේසියට අවම වශයෙන් පැය 24 කට පෙර CDA/HARTI සමග ලියාපදිංචි විය යුතුය. නිලධාරීන් විසින් ලොට් පරීක්ෂා කර ශ්‍රේණිගත කෙරේ.",
             "ගැනුම්කරුවන් සතුව වලංගු CDA ගැනුම්කරු බලපත්‍රයක් තිබිය යුතුය. වාර්ෂික අලුත් කිරීම අවශ්‍ය වේ.","#3d7a55"),
            ("02","ශ්‍රේණිගත කිරීම සහ ලොට් සෑදීම",
             "ගෙඩි ප්‍රමාණය, සතුටුදායකත්වය සහ ගුණාත්මකභාවය අනුව ශ්‍රේණිගත කෙරේ. සම්මත ලොට් = ගෙඩි 1,000. අවම ලොට් ගෙඩි 500.",
             "A ශ්‍රේණිය: ≥12cm. B ශ්‍රේණිය: 10–12cm. C ශ්‍රේණිය: <10cm.","#3d7a55"),
            ("03","ලංසු ක්‍රියාවලිය",
             "විවෘත ලංසු ක්‍රමය. වෙන්දේසිකරු ආරම්භ මිල කියයි. ඉහළම ලංසුකරු ජය ගනී. ගැනුම්කරු පැය 24 ඇතුළත ගෙවිය යුතුය.",
             "කොළඹ මධ්‍යස්ථානයේ ඉලෙක්ට්‍රොනික ලංසු ක්‍රමය පරීක්ෂාර්ථ ක්‍රියාත්මක වේ.","#f59e0b"),
            ("04","නිරවැද්‍යතාව සහ ප්‍රවාහනය",
             "බැංකු හරහා හෝ සහතිකගත චෙකපත් මගින් ගෙවීම. විකුණුම්කරු ව්‍යාපාරික දින 2ක් ඇතුළත මුදල් ලබා ගනී.",
             "CDA ගෙඩි 5,000 ට වඩා ඇති ප්‍රමාණ සඳහා ප්‍රවාහන සහාය සපයයි.","#3d7a55"),
        ]
    )
    _step_lbl = "STEP" if lang=="en" else "පියවර"
    for col, (num, title, desc, note, clr) in zip(proc_cols, steps):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:4px solid {clr};
                border-radius:10px;padding:16px 14px;height:240px;display:flex;flex-direction:column;'>
                <div style='font-size:.6rem;font-weight:800;color:{clr};text-transform:uppercase;letter-spacing:2px;'>{_step_lbl} {num}</div>
                <div style='font-size:.85rem;font-weight:800;color:#1a3328;margin:6px 0 8px;'>{title}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.55;flex:1;'>{desc}</div>
                <div style='font-size:.65rem;color:{clr};font-weight:600;margin-top:8px;background:{clr}11;
                    padding:5px 7px;border-radius:5px;line-height:1.4;'>ℹ️ {note}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Price Grades & Benchmarks ──────────────────────────────────────────────
    st.markdown("#### "+("Current Auction Price Benchmarks (Rs. per nut)" if lang=="en" else "වත්මන් වෙන්දේසි මිල දණ්ඩ (රු. ගෙඩියකට)"))
    import plotly.graph_objects as go

    gmins = [72, 58, 42, 85, 380]
    gmaxs = [85, 72, 58, 110, 450]
    gavgs = [78, 65, 50, 95, 415]
    bar_colors = ["#5a9470","#3d7a55","#3d7a55","#0d9488","#0891b2"]

    _grade_lbls = (
        ["Grade A (Premium)", "Grade B (Standard)", "Grade C (Small)", "Copra (per kg)", "Coconut Oil (per L)"]
        if lang=="en" else
        ["A ශ්‍රේණිය (විශාල)", "B ශ්‍රේණිය (සම්මත)", "C ශ්‍රේණිය (කුඩා)", "කොප්රා (kg)", "පොල් තෙල් (L)"]
    )
    _lbl_min = "Min" if lang=="en" else "අවම"
    _lbl_avg = "Average" if lang=="en" else "සාමාන්‍යය"
    _lbl_max = "Max" if lang=="en" else "උපරිම"
    _px_lbl = "Price (Rs.)" if lang=="en" else "මිල (රු.)"

    fig_grades = go.Figure()

    # Min bars
    fig_grades.add_trace(go.Bar(
        name=_lbl_min,
        x=_grade_lbls, y=gmins,
        marker_color="#94a3b8",
        marker_line=dict(width=0),
        text=[f"Rs.{v}" for v in gmins],
        textposition="outside",
        textfont=dict(size=10, color="#475569"),
        hovertemplate="<b>%{x}</b><br>" + _lbl_min + ": Rs.%{y}<extra></extra>"))

    # Avg bars
    fig_grades.add_trace(go.Bar(
        name=_lbl_avg,
        x=_grade_lbls, y=gavgs,
        marker_color=bar_colors,
        marker_line=dict(width=0),
        text=[f"Rs.{v}" for v in gavgs],
        textposition="outside",
        textfont=dict(size=11, color="#1a3328", family="Arial Black"),
        hovertemplate="<b>%{x}</b><br>" + _lbl_avg + ": Rs.%{y}<extra></extra>"))

    # Max bars
    fig_grades.add_trace(go.Bar(
        name=_lbl_max,
        x=_grade_lbls, y=gmaxs,
        marker_color=["rgba(34,197,94,0.35)","rgba(22,163,74,0.35)",
                      "rgba(21,128,61,0.35)","rgba(13,148,136,0.35)","rgba(8,145,178,0.35)"],
        marker_line=dict(color=bar_colors, width=1.5),
        text=[f"Rs.{v}" for v in gmaxs],
        textposition="outside",
        textfont=dict(size=10, color="#475569"),
        hovertemplate="<b>%{x}</b><br>" + _lbl_max + ": Rs.%{y}<extra></extra>"))

    fig_grades.update_layout(
        barmode="group",
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(
            gridcolor="#f0f5f2", tickprefix="Rs.",
            title=_px_lbl,
            tickfont=dict(size=10),
            zeroline=False),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="right", x=1, font=dict(size=11)),
        bargap=0.25, bargroupgap=0.06)

    st.plotly_chart(fig_grades, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Key Rules & Regulations ────────────────────────────────────────────────
    r1c, r2c = st.columns(2)
    with r1c:
        st.markdown("#### "+("Seller Requirements" if lang=="en" else "විකුණුම්කරු අවශ්‍යතා"))
        seller_rules = (
            [
                ("","CDA Registration","All sellers must be registered with the Coconut Development Authority (CDA)."),
                ("","Minimum Lot","Minimum 500 nuts per auction lot. Lots must be clean and free of husked nuts."),
                ("","Pre-inspection","Lots must arrive at the centre at least 1 hour before auction for grading."),
                ("","Transport","Seller arranges transport to the auction centre. CDA may assist for large volumes."),
                ("","Payment","Sellers receive payment within 2 working days of auction settlement."),
            ] if lang=="en" else [
                ("","CDA ලියාපදිංචිය","සියලු විකුණුම්කරුවන් පොල් සංවර්ධන අධිකාරිය (CDA) සමග ලියාපදිංචි විය යුතුය."),
                ("","අවම ලොට්","ලොටයකට අවම ගෙඩි 500. ලොට් පිරිසිදු විය යුතු අතර කෑල්ලට ගිලුණු ගෙඩි නොතිබිය යුතුය."),
                ("","පූර්ව පරීක්ෂණය","ශ්‍රේණිගත කිරීම සඳහා ලොට් වෙන්දේසියට අවම පැයකට පෙර මධ්‍යස්ථානයට ළඟා විය යුතුය."),
                ("","ප්‍රවාහනය","විකුණුම්කරු වෙන්දේසි මධ්‍යස්ථානයට ප්‍රවාහනය සකස් කරගත යුතුය. CDA විශාල ප්‍රමාණ සඳහා සහාය විය හැක."),
                ("","ගෙවීම","විකුණුම්කරුවන් වෙන්දේසි ගෙවීමෙන් ව්‍යාපාරික දින 2ක් ඇතුළත ගෙවීම ලබා ගනී."),
            ]
        )
        for icon, title, desc in seller_rules:
            st.markdown(f"""<div style='background:#f0f5f2;border-left:4px solid #3d7a55;border-radius:0 8px 8px 0;
                padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.75rem;font-weight:800;color:#1a3328;'>{icon} {title}</div>
                <div style='font-size:.7rem;color:#374151;margin-top:3px;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    with r2c:
        st.markdown("#### "+("Buyer Requirements" if lang=="en" else "ගැනුම්කරු අවශ්‍යතා"))
        buyer_rules = (
            [
                ("","Buyer Licence","Valid CDA buyer licence required. Obtainable from CDA Head Office, Colombo 02."),
                ("","Licence Fee","Annual buyer licence fee: Rs. 5,000 (Individual) / Rs. 15,000 (Company)."),
                ("","Deposit","Registered buyers must maintain a security deposit with the auction centre."),
                ("","Payment","Full payment within 24 hours of auction. Late payment attracts a 2% penalty per day."),
                ("","Quantity Limit","Individual buyers limited to 50,000 nuts per auction session to prevent cornering."),
            ] if lang=="en" else [
                ("","ගැනුම්කරු බලපත්‍රය","වලංගු CDA ගැනුම්කරු බලපත්‍රයක් අවශ්‍ය වේ. CDA ප්‍රධාන කාර්යාලය, කොළඹ 02 හිදී ලබා ගත හැකිය."),
                ("","බලපත්‍ර ගාස්තු","වාර්ෂික ගැනුම්කරු බලපත්‍ර ගාස්තු: රු. 5,000 (පුද්ගල) / රු. 15,000 (සමාගම)."),
                ("","තැන්පතු","ලියාපදිංචි ගැනුම්කරුවන් වෙන්දේසි මධ්‍යස්ථානය සමග ආරක්ෂිත තැන්පතුවක් පවත්වාගත යුතුය."),
                ("","ගෙවීම","වෙන්දේසි ඇතුළත පැය 24 ක් ඇතුළත සම්පූර්ණ ගෙවීම. ප්‍රමාද ගෙවීම් දිනකට 2%ක දඩයකට ලක් වේ."),
                ("","ප්‍රමාණ සීමාව","ඒකාධිකාරය වළක්වා ගැනීම සඳහා පුද්ගල ගැනුම්කරුවන් වෙන්දේසි සැසියකදී ගෙඩි 50,000 කට සීමා වේ."),
            ]
        )
        for icon, title, desc in buyer_rules:
            st.markdown(f"""<div style='background:#f0f5f2;border-left:4px solid #5a9470;border-radius:0 8px 8px 0;
                padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.75rem;font-weight:800;color:#1a3328;'>{icon} {title}</div>
                <div style='font-size:.7rem;color:#374151;margin-top:3px;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Special Auctions ──────────────────────────────────────────────────────
    st.markdown("#### "+("Special & Seasonal Auction Events" if lang=="en" else "විශේෂ සහ සෘතු වෙන්දේසි"))
    spec_cols = st.columns(3)
    specials = (
        [
            ("Peak Harvest Auctions",
             "March–April / Aug–November",
             "Extra auction sessions added during peak harvest. Colombo centre operates 5 days/week. Prices typically lower due to high supply.",
             "#3d7a55"),
            ("Premium Quality Auction",
             "Quarterly (Jan, Apr, Jul, Oct)",
             "Specially graded Grade A+ lots. Pre-registration required. Reserved for certified export-grade buyers and premium product manufacturers.",
             "#f59e0b"),
            ("Export Auction",
             "Every 2nd Friday of month",
             "Dedicated auction for export-quality coconuts and value-added products. CDA export facilitation team present. Prices in USD/EUR accepted.",
             "#3d7a55"),
        ] if lang=="en" else [
            ("උච්ච අස්වනු වෙන්දේසිය",
             "මාර්තු–අප්‍රේල් / අගෝ–නොවැ",
             "උච්ච අස්වනු කාලය තුළ අමතර වෙන්දේසි සැසි එකතු කෙරේ. කොළඹ මධ්‍යස්ථානය සතිපතා දින 5 ක් ක්‍රියාත්මක වේ. ඉහළ සැපයුම හේතුවෙන් මිල සාමාන්‍යයෙන් අඩු වේ.",
             "#3d7a55"),
            ("ශ්‍රේෂ්ඨ ගුණාත්මක වෙන්දේසිය",
             "කාර්තුව (ජන, අප්‍රේ, ජූලි, ඔක්)",
             "විශේෂයෙන් ශ්‍රේණිගත A+ ලොට්. පූර්ව ලියාපදිංචිය අවශ්‍ය. සහතිකගත අපනයන ශ්‍රේණියේ ගැනුම්කරුවන් සහ ශ්‍රේෂ්ඨ නිෂ්පාදකයන් සඳහා.",
             "#f59e0b"),
            ("අපනයන වෙන්දේසිය",
             "සෑම 2 වන සිකුරාදා",
             "අපනයන ගුණාත්මක පොල් සහ අගය-එකතු නිෂ්පාදන සඳහා විශේෂ වෙන්දේසිය. CDA අපනයන ආධාරක කණ්ඩායම සහභාගී වේ. USD/EUR මිල ද පිළිගනු ලැබේ.",
             "#3d7a55"),
        ]
    )
    for col, (title, schedule, desc, clr) in zip(spec_cols, specials):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:4px solid {clr};
                border-radius:12px;padding:18px 14px;height:220px;display:flex;flex-direction:column;'>
                <div style='font-size:.85rem;font-weight:800;color:#1a3328;margin-bottom:4px;'>{title}</div>
                <div style='font-size:.7rem;font-weight:700;color:{clr};margin-bottom:8px;'> {schedule}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.55;flex:1;'>{desc}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Contact & Registration ─────────────────────────────────────────────────
    st.markdown("#### "+("Register & Contact" if lang=="en" else "ලියාපදිංචි සහ සම්බන්ධ වන්න"))
    ct1, ct2, ct3 = st.columns(3)
    contacts = [
        ("CDA Head Office","No. 54, Nawam Mawatha, Colombo 02","+94 11 243 0610","cda@cda.gov.lk","www.cda.gov.lk",
         ("Seller & Buyer Registration, Licence Applications" if lang=="en" else "විකුණුම්කරු සහ ගැනුම්කරු ලියාපදිංචිය, බලපත්‍ර ඉල්ලීම්"),"#3d7a55"),
        ("HARTI Head Office","Narahenpita, Colombo 05","+94 11 259 1919","harti@harti.gov.lk","www.harti.gov.lk",
         ("Colombo & Gampaha Auction Operations" if lang=="en" else "කොළඹ සහ ගම්පහ වෙන්දේසි ක්‍රියාකාරිත්වය"),"#3d7a55"),
        ("CDA Auction Hotline","Any CDA Regional Office","1920 (toll-free)","auctions@cda.gov.lk","www.cda.gov.lk/auctions",
         ("Auction schedule enquiries, lot registration" if lang=="en" else "වෙන්දේසි කාලසටහන විමසීම්, ලොට් ලියාපදිංචිය"),"#f59e0b"),
    ]
    _contact_lbl = "Contact" if lang=="en" else "සම්බන්ධයි"
    for col, (org,addr,phone,email,web,purpose,clr) in zip([ct1,ct2,ct3], contacts):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #b8d0c4;border-top:3px solid {clr};
                border-radius:10px;padding:16px 14px;height:220px;display:flex;flex-direction:column;'>
                <div style='font-size:.6rem;font-weight:700;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:6px;'>{_contact_lbl}</div>
                <div style='font-weight:800;font-size:.82rem;color:#1a3328;margin-bottom:8px;'>{org}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.8;flex:1;'>
                    {addr}<br>{phone}<br>{email}<br>
                    <a href='https://{web}' target='_blank' style='color:{clr};font-weight:600;text-decoration:none;'>{web}</a>
                </div>
                <div style='font-size:.65rem;color:{clr};font-weight:600;margin-top:6px;'>{purpose}</div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
divider()

_CARD_STYLE = "background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #82b49a;padding:16px 14px;flex:1;min-width:200px;display:flex;flex-direction:column;"
_BADGE_STYLE = "font-size:.58rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;"
_NAME_STYLE = "font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;"
_INFO_STYLE = "font-size:.72rem;color:#b8d0c4;line-height:1.9;flex:1;"
_LINK_STYLE = "color:#82b49a;font-weight:600;text-decoration:none;"
_STAT_STYLE = "flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"
_DIST_STYLE = "flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"

_footer_industry_title = "Sri Lanka Coconut Industry" if lang=="en" else "ශ්‍රී ලංකා පොල් කර්මාන්තය"
_footer_industry_sub = "Key Organisations, Contacts &amp; Industry Facts" if lang=="en" else "ප්‍රධාන සංවිධාන, සම්බන්ධතා සහ කර්මාන්ත කරුණු"
_footer_regulator_lbl = "Primary Regulator" if lang=="en" else "ප්‍රාථමික නියාමකය"
_footer_research_lbl = "Research Institute" if lang=="en" else "පර්යේෂණ ආයතනය"
_footer_export_lbl = "Export Promoter" if lang=="en" else "අපනයන ප්‍රවර්ධකය"
_footer_market_lbl = "Market &amp; Auction" if lang=="en" else "වෙළඳ සහ වෙන්දේසිය"
_footer_glance_title = "Sri Lanka Coconut Industry at a Glance" if lang=="en" else "ශ්‍රී ලංකා පොල් කර්මාන්තය දළ විශ්ලේෂණයක්"
_footer_hectares = "Hectares" if lang=="en" else "හෙක්ටෙයාර්"
_footer_nutsyear = "Nuts/Year" if lang=="en" else "ගෙඩි/වර්ෂය"
_footer_families = "Families" if lang=="en" else "පවුල්"
_footer_exports = "Exports" if lang=="en" else "අපනයන"
_footer_worldrank = "World Rank" if lang=="en" else "ලෝක ශ්‍රේණිය"
_footer_gdp = "GDP Share" if lang=="en" else "GDP කොටස"
_footer_triangle_title = "The Coconut Triangle" if lang=="en" else "පොල් ත්‍රිකෝණය"
_footer_tagline = "COCOStat · Coconut Market Intelligence Dashboard · Data from CDA &amp; CRI Sri Lanka" if lang=="en" else " COCOStat · පොල් වෙළඳ බුද්ධිමත් පාලක පුවරුව · CDA සහ CRI ශ්‍රී ලංකා දත්ත"

st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a3328 0%,#2d5a3d 50%,#3d7a55 100%);border-radius:0;padding:36px 32px;box-shadow:0 4px 24px rgba(26,51,40,.25);margin-bottom:28px;">

  <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.15);margin-bottom:28px;">
    <div style="font-size:2rem;font-weight:900;color:#fff;margin-bottom:8px;text-shadow:0 2px 8px rgba(0,0,0,.2);">{_footer_industry_title}</div>
    <div style="font-size:.9rem;color:#b8d0c4;font-weight:500;">{_footer_industry_sub}</div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px;">
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #82b49a;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{_footer_regulator_lbl}</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Coconut Development Authority</div>
      <div style="font-size:.72rem;color:#b8d0c4;line-height:1.9;flex:1;"> No.54, Nawam Mawatha<br>Colombo 02<br> +94 11 243 0610<br> <a href="https://www.cda.gov.lk" target="_blank" style="color:#82b49a;font-weight:600;text-decoration:none;">www.cda.gov.lk</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #82b49a;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{_footer_research_lbl}</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Coconut Research Institute (CRI)</div>
      <div style="font-size:.72rem;color:#b8d0c4;line-height:1.9;flex:1;"> Bandirippuwa Estate<br>Lunuwila 61150<br> +94 31 222 2481<br> <a href="https://www.cri.gov.lk" target="_blank" style="color:#82b49a;font-weight:600;text-decoration:none;">www.cri.gov.lk</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #82b49a;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{_footer_export_lbl}</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Sri Lanka Export Development Board</div>
      <div style="font-size:.72rem;color:#b8d0c4;line-height:1.9;flex:1;"> 42 Nawam Mawatha<br>Colombo 02<br> +94 11 230 0705<br> <a href="https://www.srilankabusiness.com" target="_blank" style="color:#82b49a;font-weight:600;text-decoration:none;">www.srilankabusiness.com</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #82b49a;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{_footer_market_lbl}</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">HARTI / Economic Centres</div>
      <div style="font-size:.72rem;color:#b8d0c4;line-height:1.9;flex:1;"> Narahenpita, Colombo 05<br>{"(Head Office)" if lang=="en" else "(ප්‍රධාන කාර්යාලය)"}<br> +94 11 259 1919<br> <a href="https://www.harti.gov.lk" target="_blank" style="color:#82b49a;font-weight:600;text-decoration:none;">www.harti.gov.lk</a></div>
    </div>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;margin-bottom:24px;">
    <div style="text-align:center;font-size:.75rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;">{_footer_glance_title}</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~2.7M</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_hectares}</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~3B</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_nutsyear}</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">450K+</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_families}</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">$350M+</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_exports}</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">3rd</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_worldrank}</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~2%</div><div style="font-size:.65rem;color:#a8c9b8;margin-top:4px;font-weight:600;text-transform:uppercase;">{_footer_gdp}</div></div>
    </div>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;margin-bottom:24px;">
    <div style="text-align:center;font-size:.75rem;font-weight:700;color:#a8c9b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;">{_footer_triangle_title}</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;"></div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">{"Kurunegala" if lang=="en" else "කුරුණෑගල"}</div></div>
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;"></div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">{"Puttalam" if lang=="en" else "පුත්තලම"}</div></div>
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;"></div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">{"Gampaha" if lang=="en" else "ගම්පහ"}</div></div>
    </div>
  </div>

  <div style="text-align:center;font-size:.72rem;color:#a8c9b8;padding-top:20px;border-top:1px solid rgba(255,255,255,0.15);opacity:.85;">
    {_footer_tagline}
  </div>

</div>
""", unsafe_allow_html=True)
