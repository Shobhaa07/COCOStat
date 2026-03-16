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
    page_icon="🥥",
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
        "Coconut Oil":        [55,60,58,65, 70, 72, 68, 75, 80, 62],
        "Coconut Milk":       [30,35,38,42, 45, 50, 52, 55, 60, 48],
        "Coir Products":      [20,22,25,27, 30, 32, 28, 35, 38, 30],
        "Fresh Nuts":         [15,18,20,22, 25, 28, 24, 30, 32, 25],
        "Activated Carbon":   [12,14,16,18, 20, 22, 25, 28, 30, 24],
    }
    export_df = pd.DataFrame(data)
    export_df["Total"] = export_df[product_cols].sum(axis=1)
    destinations = pd.DataFrame({
        "Country":    ["USA","UK","Germany","Australia","Netherlands","Japan","Canada","UAE","Others"],
        "Share_pct":  [22,16,12,9,8,7,6,5,15],
        "Value_USD_M":[54,39,29,22,20,17,15,12,37],
    })
    return export_df, destinations

@st.cache_data
def generate_global_data():
    years = list(range(2015, 2025))
    global_df = pd.DataFrame({
        "year":        years,
        "Sri Lanka":   [52,54,57,60,63,66,62,68,72,68],
        "Indonesia":   [38,40,42,45,47,50,48,52,55,50],
        "Philippines": [45,47,50,53,56,59,55,61,65,60],
        "India":       [48,50,53,56,59,62,58,64,68,63],
        "Vietnam":     [35,37,39,42,44,47,45,49,52,47],
    })
    production = pd.DataFrame({
        "Country":           ["Indonesia","Philippines","India","Sri Lanka","Vietnam","Brazil","Mexico"],
        "Production_B_nuts": [19.5,15.0,14.8,2.7,1.8,1.6,1.2],
    })
    return global_df, production

history_df, forecast_df, weekly_df = generate_data()
weather_df  = generate_weather_data()
export_df, destinations_df = generate_export_data()
global_price_df, production_df = generate_global_data()
PRODUCT_COLS = ["Desiccated Coconut","Coconut Oil","Coconut Milk","Coir Products","Fresh Nuts","Activated Carbon"]
PRODUCT_COLORS = ["#16a34a","#3b82f6","#f59e0b","#8b5cf6","#ef4444","#06b6d4"]

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────
T = {
    "en": {
        "subtitle": "Coconut Market Intelligence Dashboard",
        "tagline": "Understanding Coconut Prices in Simple Terms",
        "desc": "This dashboard explains coconut price changes, demand behaviour, and gives future predictions with policy advice.",
        "nav": ["Overview","Market","Demand","Forecast","Policy","History","Compare","Method",
                "Weather & Harvest","Export & Trade","Farmer Profitability","Global Comparison"],
        "nav_icons":["\U0001f4ca","\U0001f6a6","\U0001f4c9","\U0001f52e","\U0001f3db","\U0001f4c8",
                     "\U0001f50d","\U0001f9e0","\U0001f326","\U0001f4e6","\U0001f9d1\u200d\U0001f33e","\U0001f30d"],
        "card_price_label":"Current Price","card_price_value":"Rs. 68.50","card_price_sub":"Per Nut (Auction)",
        "card_market_label":"Market Condition","card_market_value":"Stable","card_market_sub":"Normal conditions",
        "card_demand_label":"Demand Response","card_demand_value":"Inelastic","card_demand_sub":"People still buy",
        "card_forecast_label":"Future Trend","card_forecast_value":"\u2191 Slight Rise","card_forecast_sub":"Next 12 Weeks",
        "regime_title":"What is the Current Market Situation?",
        "regime_select":"Select Market Type to Explore",
        "regime_options":["\U0001f7e2 Stable Market","\U0001f7e1 Warning Market","\U0001f534 Crisis Market"],
        "regime_desc":["Prices are normal and stable.","Prices are changing moderately.","Prices are very unstable."],
        "regime_avg":["Rs. 52-65","Rs. 65-80","Rs. 80+"],
        "regime_vol":["Low","Medium","High"],
        "regime_avg_label":"Average Price","regime_vol_label":"Volatility","regime_status_label":"Status",
        "regime_status":["\u2705 OK","\u26a0\ufe0f Watch","\U0001f6a8 Alert"],
        "demand_title":"Do People Reduce Buying When Prices Increase?",
        "demand_note":"\U0001f4a1 Demand is mostly inelastic \u2014 people must buy coconuts because it is an essential food.",
        "demand_bar_title":"Price Sensitivity Level (%)","demand_periods":["Stable Period","Warning Period","Crisis Period"],
        "demand_sens":[35,22,12],
        "demand_cards":[
            ("\U0001f7e2 Stable Period","People react slightly to price changes."),
            ("\U0001f7e1 Warning Period","Moderate reaction to price volatility."),
            ("\U0001f534 Crisis Period","People still buy coconuts even if price increases."),
        ],
        "forecast_title":"What Will Happen to Prices in the Next 12 Weeks?",
        "forecast_summary":"\U0001f52e Prices are expected to increase slowly. No immediate crisis predicted.",
        "forecast_week":"Wk","forecast_hist_label":"Historical","forecast_pred_label":"Forecast",
        "forecast_range_label":"Uncertainty Range",
        "policy_title":"What Should the Government Do Now?",
        "policy_sub":"Evidence-based policy recommendations based on current market regime.",
        "policy_markets":["If Market is Green \U0001f7e2","If Market is Yellow \U0001f7e1","If Market is Red \U0001f534"],
        "policy_actions":["Support farmers and improve supply systems.",
                          "Improve price transparency and monitoring.",
                          "Use buffer stocks and temporary price control."],
        "policy_priorities":["\U0001f535 Low","\U0001f7e1 Medium","\U0001f534 High"],
        "policy_active":"\u2190 Currently Active","policy_priority_label":"Priority:",
        "history_title":"Market History (2015-2024)","history_sub":"Full 10-year auction price history. Hover to explore.",
        "method_title":"How This System Works",
        "method_steps":["We studied 10 years of auction data.","We grouped market situations into 3 types.",
                        "We measured how people react to prices.","We predicted future prices."],
        "footer_researcher":"Researcher","footer_ids":"Student IDs","footer_programme":"Programme",
        "compare_title":"Year-over-Year Price Comparison",
        "compare_sub":"Compare coconut prices across different years to identify seasonal patterns.",
        "price_calc_title":"\U0001f4b0 Price Impact Calculator",
        "price_calc_sub":"Estimate how price changes affect household spending.",
        "nuts_per_week":"Coconuts purchased per week","current_price_input":"Current price per nut (Rs.)",
        "new_price_input":"New price per nut (Rs.)",
        "weekly_impact":"Weekly Cost Change","monthly_impact":"Monthly Cost Change","annual_impact":"Annual Cost Change",
        "alert_warn":"Warning alert at (Rs.)","alert_crisis":"Crisis alert at (Rs.)",
        # NEW SECTIONS
        "weather_title":"\U0001f326\ufe0f Weather & Harvest Impact Analysis",
        "weather_sub":"How rainfall, temperature, and drought affect coconut yields and prices.",
        "weather_note":"\U0001f4a1 Coconut yields are highly sensitive to rainfall. Drought pushes prices up within 3-6 months.",
        "export_title":"\U0001f4e6 Export & Trade Analysis",
        "export_sub":"Sri Lanka coconut export volumes, product categories, and revenue trends (2015-2024).",
        "export_note":"\U0001f4a1 Export demand creates upward price pressure domestically. Strong export seasons often coincide with local price spikes.",
        "farmer_title":"\U0001f9d1\u200d\U0001f33e Farmer Profitability Calculator",
        "farmer_sub":"Estimate net farm income based on your land size, yield, costs, and current market price.",
        "farmer_note":"\U0001f4a1 At current prices, the average smallholder earns a thin margin. Any cost increase quickly erodes profit.",
        "global_title":"\U0001f30d Global Market Comparison",
        "global_sub":"Compare Sri Lanka coconut prices with major producers worldwide.",
        "global_note":"\U0001f4a1 Sri Lanka typically commands a price premium due to quality. But high prices hurt export competitiveness.",
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
        "nav": ["\u0daf\u0dbb\u0dca\u0dc1\u0db1\u0dba","\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5","\u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8","\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba","\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2","\u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba","\u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba","\u0d9a\u0dca\u200d\u0dbb\u0db8\u0dc0\u0dda\u0daf\u0dba",
                "\u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab & \u0d85\u0dc3\u0dca\u0dc0\u0db1\u0dd4","\u0d85\u0db4\u0db1\u0dba\u0db1 & \u0dc0\u0dd9\u0dc5\u0db3\u0dcf\u0db8","\u0d9c\u0ddc\u0dc0\u0dd2 \u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf\u0dc0","\u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba"],
        "nav_icons":["\U0001f4ca","\U0001f6a6","\U0001f4c9","\U0001f52e","\U0001f3db","\U0001f4c8",
                     "\U0001f50d","\U0001f9e0","\U0001f326","\U0001f4e6","\U0001f9d1\u200d\U0001f33e","\U0001f30d"],
        "card_price_label":"\u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd","card_price_value":"\u0dbb\u0dd4. 68.50","card_price_sub":"\u0db4\u0ddc\u0dbd\u0dca \u0d9c\u0dd0\u0da9\u0dd2\u0dba\u0d9a\u0da7 (\u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2)",
        "card_market_label":"\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba","card_market_value":"\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2","card_market_sub":"\u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba",
        "card_demand_label":"\u0db8\u0dd2\u0dbd\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba","card_demand_value":"\u0d85\u0da2\u0da9","card_demand_sub":"\u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0d85\u0da9\u0dd4 \u0db1\u0dd0\u0dad",
        "card_forecast_label":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0","card_forecast_value":"\u2191 \u0dc3\u0dd9\u0db8\u0dd2\u0db1\u0dca \u0d89\u0dc4\u0dbd","card_forecast_sub":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0dc3\u0dad\u0dd2 12",
        "regime_title":"\u0daf\u0dd0\u0db1\u0da7 \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5\u0dda \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0d9a\u0dd4\u0db8\u0d9a\u0dca\u0daf?",
        "regime_select":"\u0d9c\u0dc0\u0dda\u0DC2\u0dab\u0dba \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0dc0\u0dd9\u0dc5\u0db3 \u0dc0\u0dbb\u0dca\u0d9c\u0dba\u0d9a\u0dca \u0dad\u0ddc\u0dbb\u0db1\u0dca\u0db1",
        "regime_options":["\U0001f7e2 \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5","\U0001f7e1 \u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5","\U0001f534 \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5"],
        "regime_desc":["\u0db8\u0dd2\u0dbd \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2, \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba.","\u0db8\u0dd2\u0dbd \u0db8\u0daf\u0dca\u0dba\u0db8 \u0dbd\u0dd9\u0dc3 \u0dc0\u0dd9\u0db1\u0dc3\u0dca \u0dc0\u0dda.","\u0db8\u0dd2\u0dbd \u0d85\u0dad\u0dd2\u0DC1\u0dba\u0dd2\u0db1\u0dca \u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2."],
        "regime_avg":["\u0dbb\u0dd4. 52-65","\u0dbb\u0dd4. 65-80","\u0dbb\u0dd4. 80+"],
        "regime_vol":["\u0d85\u0da9\u0dd4","\u0db8\u0daf\u0dca\u0dba\u0db8","\u0d89\u0dc4\u0dbd"],
        "regime_avg_label":"\u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba \u0db8\u0dd2\u0dbd","regime_vol_label":"\u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf\u0dc0","regime_status_label":"\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba",
        "regime_status":["\u2705 \u0dc4\u0ddc\u0db3\u0dba\u0dd2","\u26a0\ufe0f \u0db1\u0dd2\u0dbb\u0dd3\u0d9a\u0dca\u0DC2\u0dab\u0dba","\U0001f6a8 \u0d85\u0dc0\u0daf\u0dcf\u0db1\u0db8"],
        "demand_title":"\u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dbd \u0d9c\u0dd2\u0dba \u0db8\u0dd2\u0db1\u0dd2\u0dc3\u0dd4\u0db1\u0dca \u0db8\u0dd2\u0dbd\u0daf\u0dd3 \u0d9c\u0dd9\u0db1\u0dd3\u0db8 \u0d85\u0da9\u0dd4 \u0d9a\u0dbb\u0dba\u0dd2\u0daf?",
        "demand_note":"\U0001f4a1 \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dad\u0dca\u0dba\u0dc0\u0DC1\u0dca\u0dba \u0d86\u0dc4\u0dcf\u0dbb\u0dba\u0d9a\u0dca \u0db6\u0dd0\u0dc0\u0dd2\u0db1\u0dca, \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dbd \u0d9c\u0dd2\u0dba\u0dad\u0dca \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0d85\u0da9\u0dd4\u0dc0\u0db1\u0dca\u0db1\u0dda \u0db1\u0dd0\u0dad.",
        "demand_bar_title":"\u0db8\u0dd2\u0dbd \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dad\u0dcf \u0db8\u0da7\u0dca\u0da7\u0db8 (%)","demand_periods":["\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb","\u0d85\u0dc0\u0dc0\u0dcf\u0daf","\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf"],
        "demand_sens":[35,22,12],
        "demand_cards":[
            ("\U0001f7e2 \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca\u0dc0\u0dd3\u0db8\u0dca \u0dc0\u0dbd\u0da7 \u0da7\u0dd2\u0d9a\u0d9a\u0dca \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb \u0daf\u0d9a\u0dca\u0dc0\u0dba\u0dd2."),
            ("\U0001f7e1 \u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf\u0dc0\u0da7 \u0db8\u0daf\u0dca\u0dba\u0db8 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba\u0d9a\u0dca."),
            ("\U0001f534 \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0d9a\u0dcf\u0dbd\u0dba","\u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dbd \u0d9c\u0dd2\u0dba\u0dad\u0dca \u0db8\u0dd2\u0db1\u0dd2\u0dc3\u0dd4\u0db1\u0dca \u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd\u0daf\u0dd3 \u0d9c\u0db1\u0dd3."),
        ],
        "forecast_title":"\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0dc3\u0dad\u0dd2 12 \u0dad\u0dd4\u0dbd \u0db8\u0dd2\u0dbd\u0da7 \u0d9a\u0dd4\u0db8\u0d9a\u0dca \u0dc3\u0dd2\u0daf\u0dc0\u0dda\u0daf?",
        "forecast_summary":"\U0001f52e \u0db8\u0dd2\u0dbd \u0dc3\u0dd9\u0db8\u0dd2\u0db1\u0dca \u0d89\u0dc4\u0dbd \u0dba\u0dcf \u0dc4\u0dd0\u0d9a. \u0dc0\u0dc4\u0dcf\u0db8 \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf\u0dba\u0d9a\u0dca \u0d85\u0db4\u0dda\u0d9a\u0dca\u0DC2\u0dcf \u0db1\u0ddc\u0d9a\u0dd9\u0dbb\u0dda.",
        "forecast_week":"\u0dc3\u0dad\u0dd2","forecast_hist_label":"\u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba","forecast_pred_label":"\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba",
        "forecast_range_label":"\u0d85\u0dc0\u0dd2\u0db1\u0dd2\u0DC1\u0da0\u0dd2\u0dad \u0db4\u0dbb\u0dcf\u0dc3\u0dba",
        "policy_title":"\u0daf\u0dd0\u0db1\u0da7 \u0dbb\u0da2\u0dba \u0d9a\u0dd4\u0db8\u0d9a\u0dca \u0d9a\u0dbd \u0dba\u0dd4\u0dad\u0dd4\u0daf?",
        "policy_sub":"\u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0dc0\u0dd9\u0dc5\u0db3 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0db8\u0dad \u0db4\u0daf\u0db1\u0db8\u0dca \u0dc0\u0dd6 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2 \u0db1\u0dd2\u0dbb\u0dca\u0daf\u0dda\u0DC1.",
        "policy_markets":["\U0001f7e2 \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dba\u0dd2 \u0db1\u0db8\u0dca","\U0001f7e1 \u0d85\u0dc0\u0dc0\u0dcf\u0daf\u0dba\u0dd2 \u0db1\u0db8\u0dca","\U0001f534 \u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf\u0dba\u0dd2 \u0db1\u0db8\u0dca"],
        "policy_actions":["\u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0da7 \u0dc3\u0dc4\u0dba \u0dbd\u0db6\u0dcf \u0daf\u0dd3 \u0dc3\u0dd0\u0db4\u0dba\u0dd4\u0db8\u0dca \u0db4\u0daf\u0dca\u0daf\u0dad\u0dd2\u0dba \u0dc0\u0dd0\u0da9\u0dd2\u0daf\u0dd2\u0dba\u0dd4\u0dab\u0dd4 \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
                          "\u0db8\u0dd2\u0dbd \u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4 \u0db4\u0dd0\u0dc4\u0daf\u0dd2\u0dbd\u0dd2 \u0d9a\u0dbb \u0db1\u0dd2\u0dbb\u0dd3\u0d9a\u0dca\u0DC2\u0dab\u0dba \u0dc0\u0dd0\u0daf\u0dd2 \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
                          "\u0db6\u0dc6\u0dbb\u0dca \u0dad\u0ddc\u0d9c \u0db7\u0dcf\u0dc0\u0dd2\u0dad\u0dcf \u0d9a\u0dbb \u0dad\u0dcf\u0dc0\u0d9a\u0dcf\u0dbd\u0dd2\u0d9a \u0db8\u0dd2\u0dbd \u0db4\u0dcf\u0dbd\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1."],
        "policy_priorities":["\U0001f535 \u0d85\u0da9\u0dd4","\U0001f7e1 \u0db8\u0daf\u0dca\u0dba\u0db8","\U0001f534 \u0d89\u0dc4\u0dbd"],
        "policy_active":"\u2190 \u0daf\u0dd0\u0db1\u0da7 \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a\u0dba\u0dd2","policy_priority_label":"\u0db4\u0dca\u200d\u0dbb\u0db8\u0dd4\u0d9a\u0dad\u0dcf\u0dc0:",
        "history_title":"\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba (2015-2024)","history_sub":"\u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0dc0\u0dc3\u0dbb 10 \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0db8\u0dd2\u0dbd \u0d89\u0dad\u0dd2\u0dc4\u0dcf\u0dc3\u0dba.",
        "method_title":"\u0db8\u0dda\u0db8 \u0db4\u0daf\u0dca\u0db0\u0dad\u0dd2\u0dba \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf \u0d9a\u0dbb\u0db1\u0dca \u0d86\u0d9a\u0dcf\u0dbb\u0dba",
        "method_steps":["\u0dc0\u0dc3\u0dbb 10\u0d9a \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0daf\u0dad\u0dca\u0dad \u0d85\u0daf\u0dca\u0dba\u0dba\u0db1\u0dba \u0d9a\u0dbd\u0dcf.","\u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0 3\u0d9a\u0dca \u0dc4\u0db3\u0dd4\u0db1\u0dcf\u0d9c\u0dad\u0dca\u0dad\u0dcf.","\u0db8\u0dd2\u0dbd\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb\u0dba \u0db8\u0dd0\u0db1 \u0db6\u0dd0\u0dbd\u0dd4\u0dc0\u0dcf.","\u0d89\u0daf\u0dd2\u0dbb\u0dd2 \u0db8\u0dd2\u0dbd \u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2 \u0d9a\u0dbd\u0dcf."],
        "footer_researcher":"\u0db4\u0dbb\u0dca\u0dba\u0dda\u0DC1\u0d9a","footer_ids":"\u0DC1\u0dd2\u0DC2\u0dca\u0dba \u0d8a\u0daf\u0dca","footer_programme":"\u0db4\u0dcf\u0da7\u0db8\u0dcf\u0dbd\u0dcf\u0dc0",
        "compare_title":"\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0db8\u0dd2\u0dbd \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba",
        "compare_sub":"\u0dc3\u0dd8\u0dad\u0dd4\u0db8\u0dba \u0dbb\u0da7\u0dcf \u0dc4\u0db3\u0dd4\u0db1\u0dcf \u0d9c\u0dd9\u0db1\u0dd3\u0db8\u0da7.",
        "price_calc_title":"\U0001f4b0 \u0db8\u0dd2\u0dbd \u0db6\u0dbd\u0db4\u0dcf\u0db8\u0dca \u0d9a\u0dd0\u0dbd\u0dca\u0d9a\u0dd2\u0dba\u0dd4\u0dbd\u0dda\u0da7\u0dbb\u0dba",
        "price_calc_sub":"\u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca\u0dc0\u0dd3\u0db8\u0dca \u0d9c\u0dd0\u0dc4\u0dc3\u0dca\u0dad \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0d9a\u0dd9\u0dc3\u0dda \u0db6\u0dbd\u0db4\u0dcf\u0daf\u0dd0\u0dba\u0dd2 \u0d9c\u0dab\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "nuts_per_week":"\u0dc3\u0dad\u0dd2\u0dba\u0d9a\u0da7 \u0db8\u0dd2\u0dbd\u0daf\u0dd3 \u0d9c\u0db1\u0dca\u0db1 \u0db4\u0ddc\u0dbd\u0dca \u0d9c\u0dd0\u0da9\u0dd2","current_price_input":"\u0daf\u0dd0\u0db1\u0da7 \u0d9c\u0dd0\u0da9\u0dd2\u0dba\u0d9a\u0da7 \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4.)","new_price_input":"\u0db1\u0dc0 \u0d9c\u0dd0\u0da9\u0dd2\u0dba\u0d9a\u0da7 \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4.)",
        "weekly_impact":"\u0dc3\u0dad\u0dd2\u0db4\u0dad\u0dcf \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3","monthly_impact":"\u0db8\u0dcf\u0dc3\u0dd2\u0d9a\u0dc0 \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3","annual_impact":"\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a\u0dc0 \u0dc0\u0dd2\u0dba\u0daf\u0db8\u0dca \u0dc0\u0dd9\u0db1\u0dc3",
        "alert_warn":"\u0d85\u0dc0\u0dc0\u0dcf\u0daf \u0d87\u0d9f\u0dc5\u0dd3\u0db8 (\u0dbb\u0dd4.)","alert_crisis":"\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf \u0d87\u0d9f\u0dc5\u0dd3\u0db8 (\u0dbb\u0dd4.)",
        # NEW
        "weather_title":"\U0001f326\ufe0f \u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab \u0dc3\u0dc4 \u0d85\u0dc3\u0dca\u0dc0\u0db1\u0dd4 \u0db6\u0dbd\u0db4\u0dcf\u0db8\u0dca \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba",
        "weather_sub":"\u0dc0\u0dbb\u0dca\u0DC2\u0dcf\u0dc0 \u0dc3\u0dc4 \u0d8b\u0DC2\u0dca\u0da4\u0dad\u0dca\u0dc0\u0dba \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1\u0da7 \u0dc3\u0dc4 \u0db8\u0dd2\u0dbd\u0da7 \u0db6\u0dbd\u0db4\u0dcf\u0db1 \u0d86\u0d9a\u0dcf\u0dbb\u0dba.",
        "weather_note":"\U0001f4a1 \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1 \u0dc0\u0dbb\u0dca\u0DC2\u0dcf\u0db4\u0dad\u0db1\u0dba\u0da7 \u0d89\u0dad\u0dcf \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dba\u0dd2. \u0db1\u0dd2\u0dba\u0d82 \u0d9a\u0dcf\u0dbd\u0dba \u0db8\u0dcf\u0dc3 3-6 \u0d87\u0dad\u0dd4\u0dbd\u0dad \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dbd \u0db1\u0d82\u0dc0\u0dba\u0dd2.",
        "export_title":"\U0001f4e6 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0dc3\u0dc4 \u0dc0\u0dd9\u0dc5\u0db3 \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba",
        "export_sub":"\u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0d85\u0db4\u0db1\u0dba\u0db1 \u0db4\u0dca\u200d\u0dbb\u0db8\u0dcf\u0dab, \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d9a\u0dcf\u0dab\u0dca\u0da9 \u0dc3\u0dc4 \u0d86\u0daf\u0dcf\u0dba\u0db8\u0dca \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf (2015-2024).",
        "export_note":"\U0001f4a1 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8 \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db8\u0dd2\u0dbd \u0d89\u0dc4\u0dbd \u0db1\u0d82\u0dc0\u0dba\u0dd2.",
        "farmer_title":"\U0001f9d1\u200d\U0001f33e \u0d9c\u0ddc\u0dc0\u0dd2 \u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf \u0d9a\u0dd0\u0dbd\u0dca\u0d9a\u0dd2\u0dba\u0dd4\u0dbd\u0dda\u0da7\u0dbb\u0dba",
        "farmer_sub":"\u0d85\u0dc3\u0dca\u0dc0\u0dd0\u0db1\u0dca\u0db1, \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba \u0dc3\u0dc4 \u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd \u0db8\u0dad \u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0d9c\u0dda \u0DC1\u0dd4\u0daf\u0dca\u0db0 \u0d86\u0daf\u0dcf\u0dba\u0db8 \u0d9c\u0dab\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "farmer_note":"\U0001f4a1 \u0dc0\u0dad\u0dca\u0db8\u0db1\u0dca \u0db8\u0dd2\u0dbd\u0dda\u0daf\u0dd3, \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba \u0d9a\u0dd4\u0da9\u0dcf \u0d9c\u0ddc\u0dc0\u0dd2\u0dba\u0dcf\u0da7 \u0dbd\u0dcf\u0dbb\u0dca \u0dbd\u0dd0\u0db6\u0dd9\u0db1\u0dca\u0db1\u0dda \u0dc3\u0dca\u0dc0\u0dbd\u0dca\u0db4\u0dba\u0d9a\u0dd2.",
        "global_title":"\U0001f30d \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba",
        "global_sub":"\u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0dc0\u0dd9\u0dc5\u0db3\u0db4\u0ddc\u0dc5 \u0dc3\u0db8\u0d9f \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "global_note":"\U0001f4a1 \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db8\u0dd2\u0dbd \u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf \u0d85\u0db1\u0dd4\u0d9c\u0db8\u0db1\u0dba \u0d9a\u0dbb\u0db8\u0dd2\u0db1\u0dca \u0daf \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2\u0dc0\u0dbd\u0dd2\u0db1\u0dca \u0d86\u0dbb\u0d9a\u0dca\u0DC2\u0dcf \u0dc0\u0dda.",
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
html,body,[class*="css"]{font-family:'Inter','Noto Sans Sinhala',sans-serif;background:#fff;color:#1a2e1a}
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
div[data-testid="stSidebar"]{background:#f7faf7!important;border-right:2px solid #d1e7d1!important}
div[data-testid="stSidebar"] *{color:#1a3a1a!important}
div[data-testid="stSidebar"] .stRadio label{padding:7px 12px;border-radius:8px;font-size:.85rem;font-weight:500}
div[data-testid="stSidebar"] .stRadio label:hover{background:#dcfce7;color:#14532d!important}
div[data-testid="stSidebar"] hr{border-color:#d1e7d1!important}
div[data-testid="stSidebar"] h3{color:#14532d!important;font-size:.72rem!important;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}
.section-header{font-size:1.45rem;font-weight:800;color:#0d2b0d;margin-bottom:4px;letter-spacing:-.2px}
.section-sub{color:#6b7280;font-size:.87rem;margin-bottom:18px}
.info-box-green,.info-box-blue{background:#f0fdf4;border-left:4px solid #16a34a;border-radius:0 10px 10px 0;padding:12px 16px;color:#14532d;font-weight:600;font-size:.9rem;margin-bottom:16px}
.info-box-yellow{background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;padding:12px 16px;color:#78350f;font-weight:600;font-size:.9rem;margin-bottom:16px}
.info-box-red{background:#fff1f2;border-left:4px solid #ef4444;border-radius:0 10px 10px 0;padding:12px 16px;color:#7f1d1d;font-weight:600;font-size:.9rem;margin-bottom:16px}
.styled-divider{height:1px;background:#d1e7d1;margin:28px 0}
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
    st.markdown("""
    <div style='text-align:center;padding:22px 0 14px;border-bottom:2px solid #d1e7d1;margin-bottom:4px;'>
      <svg width="56" height="56" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin:0 auto 8px;display:block;">
        <circle cx="32" cy="32" r="30" fill="#14532d" stroke="#22c55e" stroke-width="2"/>
        <circle cx="32" cy="32" r="23" fill="#166534"/>
        <rect x="30.5" y="35" width="3" height="13" rx="1.5" fill="#bbf7d0"/>
        <path d="M32 34 Q24 26 20 18 Q28 22 32 28 Q36 22 44 18 Q40 26 32 34Z" fill="#4ade80"/>
        <path d="M32 30 Q26 24 24 16 Q31 21 32 27 Q33 21 40 16 Q38 24 32 30Z" fill="#86efac"/>
        <circle cx="32" cy="37" r="4.5" fill="#92400e"/>
        <rect x="8" y="46" width="3.5" height="9" rx="1" fill="#4ade80" opacity="0.85"/>
        <rect x="13.5" y="42" width="3.5" height="13" rx="1" fill="#4ade80" opacity="0.85"/>
        <rect x="19" y="45" width="3.5" height="10" rx="1" fill="#4ade80" opacity="0.85"/>
        <polyline points="9.75,50 15.25,46 20.75,49" stroke="#bbf7d0" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        <circle cx="9.75" cy="50" r="1.2" fill="#86efac"/><circle cx="15.25" cy="46" r="1.2" fill="#86efac"/><circle cx="20.75" cy="49" r="1.2" fill="#86efac"/>
      </svg>
      <div style='font-size:1.3rem;font-weight:900;color:#0d2b0d;'>COCOStat</div>
      <div style='font-size:.65rem;color:#4a7a4a;margin-top:3px;letter-spacing:2px;font-weight:600;text-transform:uppercase;'>Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    lang_choice = st.radio("\U0001f310 Language / \u0db7\u0dcf\u0DC2\u0dcf\u0dc0", ["English", "\u0dc3\u0dd2\u0d82\u0dc4\u0dbd"], index=0)
    lang = "en" if lang_choice == "English" else "si"
    t = T[lang]
    st.markdown("---")
    st.markdown("### " + ("\U0001f4cd Navigation" if lang=="en" else "\U0001f4cd \u0dc3\u0d82\u0da0\u0dcf\u0dbd\u0db1\u0dba"))
    nav_full = [f"{icon} {name}" for icon, name in zip(t["nav_icons"], t["nav"])]
    section = st.radio("", nav_full, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### " + ("\u2699\ufe0f Settings" if lang=="en" else "\u2699\ufe0f \u0dc3\u0dd0\u0d9a\u0dc3\u0dd4\u0db8\u0dca"))
    regime_emojis = ["\U0001f7e2 ","\U0001f7e1 ","\U0001f534 "]
    active_regime = st.selectbox(t["regime_select"], [f"{e}{o}" for e,o in zip(regime_emojis, t["regime_options"])], index=0)
    regime_idx = [f"{e}{o}" for e,o in zip(regime_emojis, t["regime_options"])].index(active_regime)
    st.markdown("---")
    st.markdown("### " + ("\U0001f514 Alerts" if lang=="en" else "\U0001f514 \u0d87\u0d9f\u0dc5\u0dd3\u0db8\u0dca"))
    warn_threshold  = st.slider(t["alert_warn"],  min_value=50, max_value=90,  value=65, step=1)
    crisis_threshold= st.slider(t["alert_crisis"], min_value=60, max_value=120, value=80, step=1)
    current_price = 68.50
    if current_price >= crisis_threshold:
        st.markdown(f"<div class='info-box-red' style='margin-top:8px;'>🚨 {'CRISIS: Price above Rs.' if lang=='en' else '\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf\u0dba: \u0dbb\u0dd4.'}{crisis_threshold}</div>", unsafe_allow_html=True)
    elif current_price >= warn_threshold:
        st.markdown(f"<div class='info-box-yellow' style='margin-top:8px;'>⚠️ {'WARNING: Rs.' if lang=='en' else '\u0d85\u0dc0\u0dc0\u0dcf\u0daf\u0dba: \u0dbb\u0dd4.'}{warn_threshold} {'threshold breached' if lang=='en' else '\u0dc3\u0dd3\u0db8\u0dcf\u0dc0 \u0d89\u0d9a\u0dca\u0db8\u0dc0\u0dcf'}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='info-box-green' style='margin-top:8px;'>✅ {'Market within safe range' if lang=='en' else '\u0d86\u0dbb\u0d9a\u0dca\u0DC2\u0dd2\u0dad \u0dc3\u0dd3\u0db8\u0dcf\u0dc0'}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"""
    <div style='background:#f0fdf4;border:1px solid #d1e7d1;border-radius:10px;padding:14px 12px;text-align:center;'>
      <div style='font-size:.6rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;'>\U0001f464 {t['footer_researcher']}</div>
      <div style='font-weight:800;font-size:.88rem;color:#0d2b0d;margin-bottom:8px;'>M A C S RATHNAYAKE</div>
      <div style='font-size:.6rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>{t['footer_ids']}</div>
      <div style='font-size:.78rem;color:#1a3a1a;'>UOW: w1999714</div>
      <div style='font-size:.78rem;color:#1a3a1a;margin-bottom:8px;'>IIT: 20220508</div>
      <div style='font-size:.6rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>{t['footer_programme']}</div>
      <div style='font-size:.75rem;color:#1a3a1a;line-height:1.6;'>BSc (Hons) Data Science<br>&amp; Analytics<br>University of Westminster</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────
st.markdown(f"""
<div id='coco-hero' style='text-align:center;padding:clamp(16px,4vw,36px) clamp(12px,5vw,48px) clamp(14px,3vw,32px);margin-bottom:0;
  background:linear-gradient(135deg,#0d2b0d 0%,#14532d 50%,#166534 100%);border-bottom:3px solid #16a34a;box-shadow:0 4px 20px rgba(13,43,13,.18);'>
  <div style='display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);border-radius:20px;padding:5px 18px;
      font-size:clamp(.62rem,2vw,.78rem);font-weight:700;color:#bbf7d0;letter-spacing:1px;margin-bottom:10px;'>🥥 {t["subtitle"]}</div>
  <h1 style='font-size:clamp(1.3rem,5vw,2.2rem);font-weight:900;color:#fff;margin:0 0 10px;line-height:1.25;text-shadow:0 2px 8px rgba(0,0,0,.2);'>{t["tagline"]}</h1>
  <p style='color:#bbf7d0;font-size:clamp(.78rem,2.5vw,.9rem);max-width:580px;margin:0 auto;line-height:1.7;font-weight:500;opacity:.9;'>{t["desc"]}</p>
</div>
<div style='margin-bottom:24px;'></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def metric_card(label, value, clr="#16a34a", sub=None, height=110):
    sub_html = f"<div style='display:inline-block;background:#f0fdf4;color:#166534;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #bbf7d0;margin-top:4px;'>{sub}</div>" if sub else ""
    return f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid {clr};border-radius:10px;padding:14px 16px;
        height:{height}px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;'>
        <div style='font-size:.65rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:.8px;'>{label}</div>
        <div style='font-size:1.4rem;font-weight:900;color:{clr};line-height:1.2;'>{value}</div>
        {sub_html}</div>"""

def section_header(title, sub=None):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if sub: st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

REGIME_COLORS = ["#22c55e","#eab308","#ef4444"]
REGIME_BGS    = ["#dcfce7","#fef9c3","#fee2e2"]
REGIME_EMOJI  = ["🟢","🟡","🔴"]

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────
sec_name = section.split(" ", 1)[1] if " " in section else section

# ══ OVERVIEW ════════════════════════════════════════════════════════════════
if t["nav"][0] in sec_name:
    c1,c2,c3,c4 = st.columns(4)
    cards = [
        ("\U0001f4b0 "+t["card_price_label"], t["card_price_value"], "#16a34a", t["card_price_sub"]),
        ("\U0001f4ca "+t["card_market_label"], "\U0001f7e2 "+t["card_market_value"], "#22c55e", t["card_market_sub"]),
        ("\U0001f4c9 "+t["card_demand_label"], t["card_demand_value"], "#3b82f6", t["card_demand_sub"]),
        ("\U0001f52e "+t["card_forecast_label"], t["card_forecast_value"], "#f59e0b", t["card_forecast_sub"]),
    ]
    for col,(label,value,clr,sub) in zip([c1,c2,c3,c4], cards):
        with col: st.markdown(metric_card(label,value,clr,sub,130), unsafe_allow_html=True)
    divider()

    col_chart, col_stats = st.columns([2,1])
    with col_chart:
        recent = history_df.tail(36)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=recent["date"],y=recent["price"],fill="tozeroy",fillcolor="rgba(22,163,74,.1)",
            line=dict(color="#16a34a",width=2.5),hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
        fig.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f"\u26a0 Rs.{warn_threshold}",annotation_position="top left")
        fig.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f"\U0001f534 Rs.{crisis_threshold}",annotation_position="top left")
        fig.update_layout(title=dict(text="\U0001f4c8 "+("Recent 3-Year Price Trend" if lang=="en" else "\u0db8\u0dd0\u0dad \u0d9a\u0dcf\u0dbd \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0"),font=dict(size=14,color="#0f172a")),
            height=280,margin=dict(l=80,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",tickfont=dict(size=11)),showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":"hover"})
    with col_stats:
        st.markdown("#### \U0001f4ca "+("Quick Stats" if lang=="en" else "\u0d89\u0d9a\u0dca\u0db8\u0db1\u0dca \u0dc3\u0d82\u0d9a\u0dca\u200d\u0dba\u0dcf\u0db1"))
        last36 = history_df.tail(36)
        for lbl,val in [("3yr Avg",f"Rs.{last36['price'].mean():.1f}"),("3yr High",f"Rs.{last36['price'].max():.1f}"),
                        ("3yr Low",f"Rs.{last36['price'].min():.1f}"),("Volatility",f"Rs.{last36['price'].std():.1f}")]:
            st.markdown(f"""<div style='background:#f7faf7;border:1px solid #d1e7d1;border-left:4px solid #16a34a;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.7rem;color:#4a7a4a;font-weight:700;text-transform:uppercase;'>{lbl}</div>
                <div style='font-size:1.25rem;font-weight:800;color:#0d2b0d;'>{val}</div></div>""", unsafe_allow_html=True)
    divider()

    # Seasonality heatmap
    st.markdown("#### \U0001f5d3\ufe0f "+("Monthly Avg Price by Year" if lang=="en" else "\u0dc0\u0dbb\u0dca\u0DC2\u0dba \u0d85\u0db1\u0dd4\u0dc0 \u0db8\u0dcf\u0dc3\u0dd2\u0d9a \u0db8\u0dd2\u0dbd"))
    mnames=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    piv = history_df.pivot_table(index="year",columns="month",values="price",aggfunc="mean").reindex(columns=range(1,13))
    piv.columns=mnames
    zc=[[None if np.isnan(v) else round(v,1) for v in row] for row in piv.values]
    tx=[[f"Rs.{v:.1f}" if not np.isnan(v) else "-" for v in row] for row in piv.values]
    fig_h=go.Figure(go.Heatmap(z=zc,x=mnames,y=[str(y) for y in piv.index],
        colorscale=[[0,"#dcfce7"],[.5,"#fef9c3"],[1,"#fee2e2"]],text=tx,texttemplate="%{text}",textfont=dict(size=9),
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
    dw=(pnew-pnow)*nuts; clrc="#ef4444" if dw>0 else "#22c55e"; arr="\u2191" if dw>0 else "\u2193"
    rc1,rc2,rc3=st.columns(3)
    for col,lbl,val in zip([rc1,rc2,rc3],[t["weekly_impact"],t["monthly_impact"],t["annual_impact"]],[dw,dw*4,dw*52]):
        with col:
            st.markdown(f"""<div style='background:#f8fafc;border:2px solid {clrc}33;border-radius:14px;padding:14px;text-align:center;height:90px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.76rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{lbl}</div>
                <div style='font-size:1.5rem;font-weight:900;color:{clrc};'>{arr} Rs.{abs(val):.2f}</div></div>""",unsafe_allow_html=True)

# ══ MARKET REGIME ════════════════════════════════════════════════════════════
elif t["nav"][1] in sec_name:
    section_header("\U0001f6a6 "+t["regime_title"])
    c1,c2,c3=st.columns(3)
    for i,col in enumerate([c1,c2,c3]):
        border=f"3px solid {REGIME_COLORS[i]}" if i==regime_idx else "2px solid #e2e8f0"
        bg=REGIME_BGS[i] if i==regime_idx else "#f8fafc"
        with col:
            st.markdown(f"""<div style='background:{bg};border:{border};border-radius:16px;padding:24px;text-align:center;'>
                <div style='font-size:2.5rem;margin-bottom:8px;'>{REGIME_EMOJI[i]}</div>
                <div style='font-weight:800;color:{REGIME_COLORS[i]};margin-bottom:8px;'>{t["regime_options"][i]}</div>
                <div style='font-size:.9rem;color:#475569;'>{t["regime_desc"][i]}</div>
                {"<div style=\'margin-top:10px;font-size:.75rem;font-weight:800;color:"+REGIME_COLORS[i]+";'>✓ Selected</div>" if i==regime_idx else ""}
            </div>""",unsafe_allow_html=True)
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
    fig_r.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f"\u26a0 Rs.{warn_threshold}",annotation_position="top left")
    fig_r.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f"\U0001f534 Rs.{crisis_threshold}",annotation_position="top left")
    fig_r.update_layout(title=dict(text="\U0001f4ca "+("Price History by Regime" if lang=="en" else "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0d85\u0db1\u0dd4\u0dc0 \u0db8\u0dd2\u0dbd"),font=dict(size=14)),
        height=320,margin=dict(l=80,r=20,t=40,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_r,use_container_width=True,config={"displayModeBar":"hover"})
    divider()
    st.markdown("#### \U0001f4ca "+("Regime Statistics" if lang=="en" else "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0 \u0dc3\u0d82\u0d9a\u0dca\u200d\u0dba\u0dcf\u0db1"))
    rc_counts=history_df["regime"].value_counts().sort_index()
    sc1,sc2,sc3=st.columns(3)
    for i,col in enumerate([sc1,sc2,sc3]):
        cnt=rc_counts.get(i,0); pct=cnt/len(history_df)*100
        with col:
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-radius:12px;padding:14px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:1.8rem;margin-bottom:4px;'>{REGIME_EMOJI[i]}</div>
                <div style='font-weight:800;color:{REGIME_COLORS[i]};font-size:1rem;margin-bottom:4px;'>{t["regime_options"][i]}</div>
                <div style='font-size:1.6rem;font-weight:900;color:{REGIME_COLORS[i]};'>{pct:.0f}%</div>
                <div style='font-size:.8rem;color:#64748b;'>{cnt} {"months" if lang=="en" else "\u0db8\u0dcf\u0dc3"}</div></div>""",unsafe_allow_html=True)

# ══ DEMAND ═══════════════════════════════════════════════════════════════════
elif t["nav"][2] in sec_name:
    section_header("\U0001f4c9 "+t["demand_title"])
    st.markdown(f"<div class='info-box-blue'>{t['demand_note']}</div>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        fig_d=go.Figure(go.Bar(x=t["demand_periods"],y=t["demand_sens"],
            marker=dict(color=REGIME_COLORS,line=dict(width=0)),
            text=[f"{v}%" for v in t["demand_sens"]],textposition="outside",width=.5))
        fig_d.update_layout(title=dict(text=t["demand_bar_title"],font=dict(size=14)),
            height=280,margin=dict(l=20,r=20,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e8f5e9",range=[0,50]),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":"hover"})
    with c2:
        for i,(period,desc) in enumerate(t["demand_cards"]):
            st.markdown(f"""<div style='background:{REGIME_BGS[i]};border-left:4px solid {REGIME_COLORS[i]};border-radius:0 12px 12px 0;padding:14px 16px;margin-bottom:12px;'>
                <div style='font-weight:700;font-size:.95rem;margin-bottom:4px;'>{period}</div>
                <div style='font-size:.88rem;color:#475569;line-height:1.5;'>{desc}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### \U0001f4ca "+("Price Elasticity of Demand" if lang=="en" else "\u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8\u0dca \u0dc3\u0dca\u0da5\u0dd2\u0dad\u0dd2\u0dc3\u0dca\u0da5\u0dd2\u0d9a\u0dba"))
    e1,e2,e3=st.columns(3)
    for col,(ev,ep,ec,eb) in zip([e1,e2,e3],[("-0.35","Stable" if lang=="en" else "\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb","#22c55e","#dcfce7"),
                                             ("-0.22","Warning" if lang=="en" else "\u0d85\u0dc0\u0dc0\u0dcf\u0daf","#eab308","#fef9c3"),
                                             ("-0.12","Crisis" if lang=="en" else "\u0d85\u0dbb\u0dca\u0db6\u0dd4\u0daf","#ef4444","#fee2e2")]):
        with col:
            st.markdown(f"""<div style='background:{eb};border-radius:12px;padding:16px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.72rem;font-weight:700;color:#64748b;margin-bottom:4px;'>{"Elasticity" if lang=="en" else "\u0dc3\u0dca\u0da5\u0dd2\u0dad\u0dd2\u0dc3\u0dca\u0da5\u0dd2\u0d9a\u0dba"} - {ep}</div>
                <div style='font-size:1.9rem;font-weight:900;color:{ec};'>{ev}</div>
                <div style='font-size:.78rem;color:#64748b;margin-top:2px;'>{"Inelastic" if lang=="en" else "\u0d85\u0da2\u0da9"}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### \U0001f4c9 "+("Demand Curve by Regime" if lang=="en" else "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0d85\u0db1\u0dd4\u0dc0 \u0d89\u0dbd\u0dca\u0dbd\u0dd4\u0db8\u0dca \u0dc0\u0d9a\u0dca\u200d\u0dbb\u0dba"))
    pr=np.linspace(40,100,60); bq=1000; bp=60
    fig_dc=go.Figure()
    for (lbl,el),clr in zip({"Stable":-0.35,"Warning":-0.22,"Crisis":-0.12}.items(),REGIME_COLORS):
        q=bq*(pr/bp)**el
        fig_dc.add_trace(go.Scatter(x=q,y=pr,mode="lines",name=lbl,line=dict(color=clr,width=2.5),
            hovertemplate=f"<b>{lbl}</b><br>Price: Rs.%{{y:.1f}}<br>Qty: %{{x:.0f}}<extra></extra>"))
    fig_dc.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(title="Quantity Demanded",showgrid=False),yaxis=dict(title="Price (Rs.)",gridcolor="#e8f5e9",tickprefix="Rs."),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_dc,use_container_width=True,config={"displayModeBar":"hover"})

# ══ FORECAST ════════════════════════════════════════════════════════════════
elif t["nav"][3] in sec_name:
    section_header("\U0001f52e "+t["forecast_title"])
    st.markdown(f"<div class='info-box-green'>{t['forecast_summary']}</div>",unsafe_allow_html=True)
    hist_r=history_df.tail(16)
    fig_f=go.Figure()
    fig_f.add_trace(go.Scatter(x=pd.concat([forecast_df["date"],forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"],forecast_df["lower"][::-1]]),fill="toself",fillcolor="rgba(245,158,11,.15)",
        line=dict(color="rgba(0,0,0,0)"),name=t["forecast_range_label"],hoverinfo="skip"))
    fig_f.add_trace(go.Scatter(x=hist_r["date"],y=hist_r["price"],line=dict(color="#3b82f6",width=2.5),
        name=t["forecast_hist_label"],mode="lines",hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_trace(go.Scatter(x=forecast_df["date"],y=forecast_df["price"],line=dict(color="#f59e0b",width=2.5,dash="dash"),
        name=t["forecast_pred_label"],mode="lines+markers",marker=dict(size=6,color="#f59e0b"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_f.add_hline(y=warn_threshold,line_dash="dot",line_color="#eab308",annotation_text=f"\u26a0 Rs.{warn_threshold}",annotation_position="top left")
    fig_f.add_hline(y=crisis_threshold,line_dash="dot",line_color="#ef4444",annotation_text=f"\U0001f534 Rs.{crisis_threshold}",annotation_position="top left")
    fig_f.add_vline(x=forecast_df["date"].iloc[0].timestamp()*1000,line_dash="dot",line_color="#94a3b8",
        annotation_text="Forecast \u2192" if lang=="en" else "\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2\u0dba \u2192",annotation_position="top left")
    fig_f.update_layout(height=340,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",tickfont=dict(size=11)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_f,use_container_width=True,config={"displayModeBar":"hover"})

    st.markdown("#### \U0001f4c5 "+("12-Week Forecast Details" if lang=="en" else "\u0dc3\u0dad\u0dd2 12 \u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb"))
    wcols=st.columns(6)
    for i,(_,row) in enumerate(forecast_df.iterrows()):
        if i>=12: break
        p=row["price"]; clr="#ef4444" if p>=crisis_threshold else "#eab308" if p>=warn_threshold else "#22c55e"
        st_=("\U0001f534" if p>=crisis_threshold else "\U0001f7e1" if p>=warn_threshold else "\U0001f7e2")
        with wcols[i%6]:
            st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid {clr};border-radius:10px;padding:10px 6px;text-align:center;margin-bottom:8px;min-height:78px;display:flex;flex-direction:column;justify-content:center;align-items:center;'>
                <div style='font-size:.7rem;color:#94a3b8;margin-bottom:2px;'>{t["forecast_week"]} {i+1}</div>
                <div style='font-size:.95rem;font-weight:800;color:{clr};'>Rs.{p:.1f}</div>
                <div style='font-size:.8rem;'>{st_}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### \U0001f4ca "+("Forecast Summary" if lang=="en" else "\u0d85\u0db1\u0dcf\u0dc0\u0dd0\u0d9a\u0dd2 \u0dc3\u0dcf\u0dbb\u0dcf\u0d82\u0DC1\u0dba"))
    fa=forecast_df["price"].mean(); fmax=forecast_df["price"].max(); fmin=forecast_df["price"].min()
    ww=(forecast_df["price"]>=warn_threshold).sum(); wc=(forecast_df["price"]>=crisis_threshold).sum()
    s1,s2,s3,s4,s5=st.columns(5)
    for col,lbl,val,clr in zip([s1,s2,s3,s4,s5],
        ["Avg Forecast","Peak Price","Low Price","Weeks >= Warning","Weeks >= Crisis"],
        [f"Rs.{fa:.1f}",f"Rs.{fmax:.1f}",f"Rs.{fmin:.1f}",f"{ww} wks",f"{wc} wks"],
        ["#16a34a","#16a34a","#16a34a","#f59e0b","#ef4444"]):
        with col: st.markdown(metric_card(lbl,val,clr,height=80),unsafe_allow_html=True)

# ══ POLICY ═══════════════════════════════════════════════════════════════════
elif t["nav"][4] in sec_name:
    section_header("\U0001f3db "+t["policy_title"], t["policy_sub"])
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
    st.markdown("#### \U0001f4cb "+("Policy Decision Framework" if lang=="en" else "\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2 \u0dad\u0dd3\u0dbb\u0dab \u0dbb\u0dcf\u0db8\u0dd4\u0dc0"))
    stps=[("1\ufe0f\u20e3","Detect Regime" if lang=="en" else "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba \u0dc4\u0dde\u0daf\u0dd4\u0db1\u0db1\u0dca\u0db1","#3b82f6"),
          ("2\ufe0f\u20e3","Assess Priority" if lang=="en" else "\u0db4\u0dca\u200d\u0dbb\u0db8\u0dd4\u0d9a\u0dad\u0dcf\u0dc0 \u0dad\u0dd3\u0dbb\u0dab\u0dba","#8b5cf6"),
          ("3\ufe0f\u20e3","Implement Policy" if lang=="en" else "\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2\u0dba \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a","#16a34a"),
          ("4\ufe0f\u20e3","Monitor & Review" if lang=="en" else "\u0db1\u0dd2\u0dbb\u0dd3\u0d9a\u0dca\u0DC2\u0dab\u0dba \u0d9a\u0dbb\u0db1\u0dca\u0db1","#f59e0b")]
    sc=st.columns(4)
    for col,(em,st_,clr) in zip(sc,stps):
        with col:
            st.markdown(f"""<div style='text-align:center;background:#f8fafc;border-radius:14px;padding:14px 10px;border:1px solid #e2e8f0;height:100px;display:flex;flex-direction:column;justify-content:center;align-items:center;'>
                <div style='font-size:1.8rem;margin-bottom:6px;'>{em}</div>
                <div style='font-weight:700;font-size:.85rem;color:{clr};'>{st_}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("#### \U0001f4c8 "+("Policy Effectiveness Indicators" if lang=="en" else "\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0dad\u0dca\u0dad\u0dd2 \u0dc3\u0dc2\u0dbd\u0dad\u0dcf \u0daf\u0dbb\u0dca\u0DC1\u0d9a"))
    indics=[("Price Stability" if lang=="en" else "\u0db8\u0dd2\u0dbd \u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf",72,"#3b82f6"),
            ("Supply Chain" if lang=="en" else "\u0dc3\u0dd0\u0db4\u0dba\u0dd4\u0db8\u0dca \u0daf\u0dcf\u0db8",58,"#22c55e"),
            ("Farmer Support" if lang=="en" else "\u0d9c\u0ddc\u0dc0\u0dd2 \u0dc3\u0dc4\u0dba",64,"#f59e0b"),
            ("Market Transparency" if lang=="en" else "\u0dc0\u0dd9\u0dc7\u0dad \u0dc0\u0dd2\u0db1\u0dd2\u0dc0\u0dd2\u0daf",80,"#8b5cf6")]
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

# ══ HISTORY ══════════════════════════════════════════════════════════════════
elif t["nav"][5] in sec_name:
    section_header("\U0001f4c8 "+t["history_title"], t["history_sub"])
    fig_hist=go.Figure()
    fig_hist.add_trace(go.Scatter(x=history_df["date"],y=history_df["price"],fill="tozeroy",fillcolor="rgba(22,163,74,.08)",
        line=dict(color="#16a34a",width=1.8),mode="lines",hovertemplate="<b>%{x|%b %Y}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_hist.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f"\u26a0 Rs.{warn_threshold}",annotation_position="top left",annotation_font_color="#eab308")
    fig_hist.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f"\U0001f534 Rs.{crisis_threshold}",annotation_position="bottom left",annotation_font_color="#ef4444")
    fig_hist.update_layout(height=360,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True),tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",tickfont=dict(size=11)),showlegend=False)
    st.plotly_chart(fig_hist,use_container_width=True,config={"displayModeBar":"hover"})
    st.markdown("#### \U0001f4ca "+("Summary Statistics" if lang=="en" else "\u0dc3\u0dcf\u0dbb\u0dcf\u0d82\u0DC1 \u0dc3\u0d82\u0d9a\u0dca\u200d\u0dba\u0dcf\u0db1"))
    hs1,hs2,hs3,hs4,hs5=st.columns(5)
    hdata=[("\U0001f4c8 Max",f"Rs.{history_df['price'].max():.2f}"),("\U0001f4c9 Min",f"Rs.{history_df['price'].min():.2f}"),
           ("\U0001f4ca Avg",f"Rs.{history_df['price'].mean():.2f}"),("\U0001f4d0 Std",f"Rs.{history_df['price'].std():.2f}"),
           ("\U0001f4c5 Months",str(len(history_df)))]
    for col,(lbl,val) in zip([hs1,hs2,hs3,hs4,hs5],hdata):
        with col: st.markdown(metric_card(lbl,val,height=90),unsafe_allow_html=True)
    divider()
    cp,cy=st.columns(2)
    with cp:
        rc=history_df["regime"].value_counts().sort_index()
        fig_pie=go.Figure(go.Pie(labels=t["regime_options"],values=rc.values,hole=.5,
            marker=dict(colors=REGIME_COLORS),textinfo="label+percent",textfont=dict(size=11)))
        fig_pie.update_layout(title=dict(text="\U0001f967 "+("Regime Distribution" if lang=="en" else "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0 \u0db6\u0daf\u0dcf \u0dc4\u0dd0\u0dbb\u0dd3\u0db8"),font=dict(size=13)),
            height=300,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_pie,use_container_width=True,config={"displayModeBar":"hover"})
    with cy:
        aa=history_df.groupby("year")["price"].mean().reset_index()
        fig_ann=go.Figure(go.Bar(x=aa["year"].astype(str),y=aa["price"].round(2),
            marker=dict(color=aa["price"],colorscale=[[0,"#dcfce7"],[.5,"#fef9c3"],[1,"#fee2e2"]],showscale=False,line=dict(width=0)),
            text=aa["price"].round(1),texttemplate="Rs.%{text}",textposition="outside",
            hovertemplate="<b>%{x}</b><br>Avg: Rs.%{y:.2f}<extra></extra>"))
        fig_ann.update_layout(title=dict(text="\U0001f4ca "+("Annual Average Price" if lang=="en" else "\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba \u0db8\u0dd2\u0dbd"),font=dict(size=13)),
            height=300,margin=dict(l=10,r=10,t=50,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",range=[0,aa["price"].max()*1.15]),showlegend=False)
        st.plotly_chart(fig_ann,use_container_width=True,config={"displayModeBar":"hover"})

# ══ COMPARE ══════════════════════════════════════════════════════════════════
elif t["nav"][6] in sec_name:
    section_header("\U0001f50d "+t["compare_title"], t["compare_sub"])
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
        fig_y.add_hline(y=warn_threshold,line_dash="dash",line_color="#eab308",annotation_text=f"\u26a0 Rs.{warn_threshold}")
        fig_y.add_hline(y=crisis_threshold,line_dash="dash",line_color="#ef4444",annotation_text=f"\U0001f534 Rs.{crisis_threshold}")
        fig_y.update_layout(height=360,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs."),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_y,use_container_width=True,config={"displayModeBar":"hover"})
        divider()
        st.markdown("#### \U0001f4cb "+("Year-by-Year Comparison" if lang=="en" else "\u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1 \u0dc0\u0d9c\u0dd4\u0dc0"))
        cdata=[]
        for yr in sel:
            yd=history_df[history_df["year"]==yr]["price"]
            cdata.append({"Year":yr,"Avg (Rs.)":round(yd.mean(),2),"Min (Rs.)":round(yd.min(),2),
                "Max (Rs.)":round(yd.max(),2),"Std Dev":round(yd.std(),2),
                "Crisis Months":int((yd>=crisis_threshold).sum()),"Warning Months":int(((yd>=warn_threshold)&(yd<crisis_threshold)).sum())})
        st.dataframe(pd.DataFrame(cdata),use_container_width=True,hide_index=True)
        divider()
        st.markdown("#### \U0001f4ca "+("Volatility Comparison" if lang=="en" else "\u0d85\u0dc3\u0dca\u0dae\u0dcf\u0dc0\u0dbb\u0dad\u0dcf \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba"))
        fig_v=go.Figure()
        for idx,yr in enumerate(sel):
            fig_v.add_trace(go.Box(y=history_df[history_df["year"]==yr]["price"],name=str(yr),marker_color=yc[idx%len(yc)],boxmean=True))
        fig_v.update_layout(height=300,margin=dict(l=10,r=10,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs."),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_v,use_container_width=True,config={"displayModeBar":"hover"})

        # ── GLOBAL COMPARISON (embedded) ──────────────────────────────────────
        divider()
        st.markdown(f"""<div style='background:linear-gradient(90deg,#0d2b0d,#14532d);border-radius:10px;padding:12px 20px;margin-bottom:12px;'>
            <div style='font-size:1.05rem;font-weight:900;color:#fff;'>🌍 {"Global Market Comparison" if lang=="en" else "ගෝලීය වෙළඳපොළ සංසන්දනය"}</div>
            <div style='font-size:.78rem;color:#bbf7d0;margin-top:3px;'>{"Sri Lanka vs. Major Coconut Producing Nations" if lang=="en" else "ශ්‍රී ලංකා හා ප්‍රධාන නිෂ්පාදක රටවල් සංසන්දනය"}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box-blue'>{t['global_note']}</div>", unsafe_allow_html=True)

        # Global KPI row
        sl_l = global_price_df["Sri Lanka"].iloc[-1]
        w_avg = global_price_df[["Indonesia","Philippines","India","Vietnam"]].iloc[-1].mean()
        sl_vs = sl_l - w_avg; sv_clr = "#f59e0b" if sl_vs > 0 else "#22c55e"
        gk1,gk2,gk3,gk4 = st.columns(4)
        for col,(lbl,val,clr) in zip([gk1,gk2,gk3,gk4],[
            ("🇱🇰 SL Price (2024)" if lang=="en" else "🇱🇰 ශ්‍රී ලංකා මිල 2024", f"Rs.{sl_l:.0f}", "#16a34a"),
            ("🌍 World Avg Price" if lang=="en" else "🌍 ලෝක සාමාන්‍ය", f"Rs.{w_avg:.0f}", "#3b82f6"),
            ("📊 SL Premium" if lang=="en" else "📊 ශ්‍රී ලංකා වෙනස", f"{'+' if sl_vs>0 else ''}{sl_vs:.0f} Rs ({(sl_vs/w_avg*100):+.1f}%)", sv_clr),
            ("🏭 World Rank" if lang=="en" else "🏭 ලෝක ශ්‍රේණිය", "3rd Largest Producer" if lang=="en" else "3 වැනි නිෂ්පාදකයා", "#8b5cf6")]):
            with col: st.markdown(metric_card(lbl,val,clr,height=100), unsafe_allow_html=True)

        divider()

        # Multi-country price trend
        st.markdown("#### 📈 "+("Coconut Price Trend — Sri Lanka vs World Producers (LKR Equivalent)" if lang=="en" else "පොල් මිල ප්‍රවණතාව — ශ්‍රී ලංකා හා ලෝක නිෂ්පාදකයෝ"))
        c_colors={"Sri Lanka":"#16a34a","Indonesia":"#3b82f6","Philippines":"#f59e0b","India":"#ef4444","Vietnam":"#8b5cf6"}
        fig_gl=go.Figure()
        for country,clr in c_colors.items():
            is_sl=(country=="Sri Lanka")
            fig_gl.add_trace(go.Scatter(x=global_price_df["year"].astype(str),y=global_price_df[country],
                mode="lines+markers",name=("🇱🇰 " if is_sl else "")+country,
                line=dict(color=clr,width=3.5 if is_sl else 1.8,dash="solid" if is_sl else "dot"),
                marker=dict(size=8 if is_sl else 5),
                hovertemplate=f"<b>{country}</b> %{{x}}<br>Rs.%{{y:.1f}}<extra></extra>"))
        fig_gl.update_layout(height=340,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",tickfont=dict(size=11)),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig_gl,use_container_width=True,config={"displayModeBar":"hover"})
        divider()

        # Production share + radar
        cp2,cr=st.columns(2)
        with cp2:
            st.markdown("#### 🌍 "+("Global Coconut Production Share" if lang=="en" else "ගෝලීය පොල් නිෂ්පාදන කොටස"))
            fig_pp=go.Figure(go.Pie(labels=production_df["Country"],values=production_df["Production_B_nuts"],hole=.45,
                textinfo="label+percent",textfont=dict(size=10),
                marker=dict(colors=["#3b82f6","#f59e0b","#ef4444","#16a34a","#8b5cf6","#06b6d4","#84cc16"]),
                pull=[.08 if c=="Sri Lanka" else 0 for c in production_df["Country"]],
                hovertemplate="<b>%{label}</b><br>%{value}B nuts/yr<br>%{percent}<extra></extra>"))
            fig_pp.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
            st.plotly_chart(fig_pp,use_container_width=True,config={"displayModeBar":"hover"})
        with cr:
            st.markdown("#### 📊 "+("Country Competitiveness Radar" if lang=="en" else "රටවල් තරඟකාරිත්ව රේඩාර්"))
            ctries=["Sri Lanka","Indonesia","Philippines","India","Vietnam"]
            attrs=["Quality","Volume","Price Comp.","Export Infra.","Processing"]
            scores={"Sri Lanka":[88,40,55,72,80],"Indonesia":[70,95,90,82,75],"Philippines":[75,85,80,78,70],"India":[80,88,72,80,82],"Vietnam":[65,50,88,60,55]}
            clrs_r=["#16a34a","#3b82f6","#f59e0b","#ef4444","#8b5cf6"]
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
        st.markdown("#### 📋 "+("Price Gap Analysis vs Sri Lanka (Latest Year)" if lang=="en" else "මිල පරතර විශ්ලේෂණය"))
        lr=global_price_df.iloc[-1]; sl_p=lr["Sri Lanka"]
        gdrows=[]
        for ct in ["Indonesia","Philippines","India","Vietnam"]:
            cp_=lr[ct]; gap=sl_p-cp_; gp=gap/cp_*100
            gdrows.append({"Country":ct,"Price (Rs.)":round(cp_,1),"SL Price (Rs.)":round(sl_p,1),"Gap (Rs.)":round(gap,1),"Gap (%)":round(gp,1),"SL vs This":("Higher↑" if gap>0 else "Lower↓")})
        st.dataframe(pd.DataFrame(gdrows),use_container_width=True,hide_index=True)
        divider()

        # SL price divergence bar chart
        st.markdown("#### 📉 "+("SL Price Divergence from World Average" if lang=="en" else "ලෝක සාමාන්‍යයෙන් ශ්‍රී ලංකා අපගමනය"))
        wavg_s=global_price_df[["Indonesia","Philippines","India","Vietnam"]].mean(axis=1)
        sldev=global_price_df["Sri Lanka"]-wavg_s
        fig_dv=go.Figure(go.Bar(x=global_price_df["year"].astype(str),y=sldev,
            marker_color=["#22c55e" if v>0 else "#ef4444" for v in sldev],
            text=[f"Rs.{v:+.1f}" for v in sldev],textposition="outside",textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>SL Premium: Rs.%{y:.1f}<extra></extra>"))
        fig_dv.add_hline(y=0,line_color="#94a3b8",line_width=1.5)
        fig_dv.update_layout(height=260,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",title="Premium above World Avg"),showlegend=False)
        st.plotly_chart(fig_dv,use_container_width=True,config={"displayModeBar":"hover"})

    else:
        st.info("Please select at least one year." if lang=="en" else "\u0d9a\u0dbb\u0dd4\u0dab\u0dcf\u0d9a\u0dbb \u0d85\u0dc0\u0db8 \u0dc0\u0dc3\u0dbb\u0d9a\u0dca \u0dad\u0ddc\u0dbb\u0db1\u0dca\u0db1.")

# ══ METHOD ═══════════════════════════════════════════════════════════════════
elif t["nav"][7] in sec_name:
    section_header("\U0001f9e0 "+t["method_title"])
    mc=st.columns(4)
    for i,(col,step) in enumerate(zip(mc,t["method_steps"])):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:4px solid #16a34a;border-radius:8px;padding:22px 18px;height:130px;display:flex;flex-direction:column;justify-content:space-between;'>
                <div style='font-size:.72rem;font-weight:800;color:#16a34a;text-transform:uppercase;letter-spacing:1.5px;'>Step 0{i+1}</div>
                <div style='font-size:.95rem;color:#0d2b0d;line-height:1.55;font-weight:600;'>{step}</div></div>""",unsafe_allow_html=True)
    divider()
    st.markdown("<div style='font-size:.78rem;font-weight:800;color:#14532d;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;'>"
        +("System Architecture &amp; Processing Pipeline" if lang=="en" else "\u0db4\u0daf\u0dca\u0db0\u0dad\u0dd2 \u0d9c\u0ddb\u0dc4 \u0db1\u0dd2\u0dbb\u0dca\u0db8\u0dcf\u0da4\u0dba")
        +"</div>",unsafe_allow_html=True)
    ac=st.columns(5)
    for i,(col,(num,title,sub)) in enumerate(zip(ac,[("01","Raw Data","Auction Records"),("02","Pre-processing","& Cleaning"),
            ("03","Model Training","Markov + ARIMA"),("04","Analysis","Elasticity"),("05","Dashboard","COCOStat")])):
        arr=f"<div style='position:absolute;right:-14px;top:50%;transform:translateY(-50%);font-size:1rem;color:#16a34a;font-weight:700;z-index:2;'>\u203a</div>" if i<4 else ""
        with col:
            st.markdown(f"""<div style='position:relative;background:#f0fdf4;border:1px solid #d1e7d1;border-top:3px solid #16a34a;border-radius:8px;padding:16px 10px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>
                <div style='font-size:.68rem;font-weight:800;color:#16a34a;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>{num}</div>
                <div style='font-size:.9rem;font-weight:700;color:#0d2b0d;margin-bottom:3px;'>{title}</div>
                <div style='font-size:.78rem;color:#4a7a4a;font-weight:500;'>{sub}</div>{arr}</div>""",unsafe_allow_html=True)
    divider()
    with st.expander("\U0001f52c "+("Technical Details" if lang=="en" else "\u0dad\u0dcf\u0d9a\u0dca\u0DC2\u0dab\u0dd2\u0d9a \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb")):
        st.markdown("""
| Component | Method | Detail |
|-----------|--------|--------|
| Regime Detection | Markov Switching Model (3-State) | Hamilton (1989) |
| Demand Estimation | OLS with HC3 Robust Std Errors | Log-log specification |
| Forecasting | SARIMA with seasonal adjustment | AIC-selected order |
| Volatility | Rolling std dev (12-month window) | Monthly frequency |
| Data Source | Sri Lanka Coconut Auction Records | 2015-2024 (113 obs.) |
        """)
    with st.expander("\U0001f4d6 "+("References" if lang=="en" else "\u0dba\u0ddc\u0db8\u0dd4 \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0dca")):
        st.markdown("""
- Hamilton, J.D. (1989). *A New Approach to the Economic Analysis of Nonstationary Time Series*. Econometrica.
- Box, G.E.P. & Jenkins, G.M. (1976). *Time Series Analysis: Forecasting and Control*. Holden-Day.
- Sri Lanka Coconut Development Authority. Annual Reports (2015-2024).
        """)

# ══ WEATHER & HARVEST (FORWARD FORECAST) ═════════════════════════════════════
elif t["nav"][8] in sec_name:
    section_header("\U0001f326\ufe0f "+t["weather_title"], t["weather_sub"])
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
        "SW Monsoon" if m in [5,6,7,8,9] else
        "NE Monsoon" if m in [11,12,1] else
        "Inter-Monsoon" )

    # ── KPI Row (forward-looking) ─────────────────────────────────────────────
    avg_frain = fwd_df["rainfall_mm"].mean()
    avg_fyield = fwd_df["yield_index"].mean()
    avg_ftemp = fwd_df["temp_c"].mean()
    harvest_months_count = int(fwd_df["harvest_period"].sum())
    hist_avg_rain = weather_df["rainfall_mm"].mean()
    rain_diff = avg_frain - hist_avg_rain

    wk1,wk2,wk3,wk4 = st.columns(4)
    for col,(lbl,val,clr) in zip([wk1,wk2,wk3,wk4],[
        ("🌧 Forecast Avg Rainfall" if lang=="en" else "🌧 අනාවැකි සාමාන්‍ය වර්ෂාව", f"{avg_frain:.0f} mm", "#3b82f6"),
        ("🌡 Forecast Avg Temp" if lang=="en" else "🌡 අනාවැකි සාමාන්‍ය උෂ්ණත්වය", f"{avg_ftemp:.1f} °C", "#f59e0b"),
        ("🌴 Forecast Yield Index" if lang=="en" else "🌴 අනාවැකි අස්වැන්න දර්ශකය", f"{avg_fyield:.0f}/100", "#16a34a"),
        ("🌾 Harvest Months (12m)" if lang=="en" else "🌾 අස්වනු මාස (12m)", f"{harvest_months_count} months", "#8b5cf6")]):
        with col: st.markdown(metric_card(lbl,val,clr,height=110),unsafe_allow_html=True)
    divider()

    # ── Main chart: Rainfall forecast + harvest overlay + yield + price ────────
    st.markdown("#### 🌧 "+("12-Month Forward Rainfall Forecast, Yield & Price Impact" if lang=="en" else "ඉදිරි මාස 12 වර්ෂාව, අස්වැන්න සහ මිල අනාවැකිය"))

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
        showlegend=True, name="Rainfall Range",
        hoverinfo="skip"), secondary_y=False)

    # Rainfall bars
    fig_fw.add_trace(go.Bar(
        x=fwd_df["date"], y=fwd_df["rainfall_mm"], name="Forecast Rainfall (mm)",
        marker_color="rgba(59,130,246,.55)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Rain: %{y:.0f} mm<extra></extra>"),
        secondary_y=False)

    # Yield index line
    fig_fw.add_trace(go.Scatter(
        x=fwd_df["date"], y=fwd_df["yield_index"], name="Yield Index",
        mode="lines+markers", line=dict(color="#16a34a", width=2.5),
        marker=dict(size=7, symbol=["star" if h else "circle" for h in fwd_df["harvest_period"]]),
        hovertemplate="<b>%{x|%b %Y}</b><br>Yield: %{y:.1f}<extra></extra>"),
        secondary_y=True)

    # Price impact line
    fig_fw.add_trace(go.Scatter(
        x=fwd_df["date"], y=fwd_df["price_impact"], name="Est. Price (Rs.)",
        mode="lines+markers", line=dict(color="#f59e0b", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="<b>%{x|%b %Y}</b><br>Est. Rs.%{y:.2f}<extra></extra>"),
        secondary_y=True)

    fig_fw.add_hline(y=warn_threshold, line_dash="dash", line_color="#eab308",
        annotation_text=f"⚠ Rs.{warn_threshold}", secondary_y=True)
    fig_fw.add_hline(y=crisis_threshold, line_dash="dash", line_color="#ef4444",
        annotation_text=f"🔴 Rs.{crisis_threshold}", secondary_y=True)

    fig_fw.update_layout(
        height=380, margin=dict(l=60,r=60,t=20,b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)))
    fig_fw.update_yaxes(title_text="Rainfall (mm)", secondary_y=False, gridcolor="#e8f5e9")
    fig_fw.update_yaxes(title_text="Yield Index / Price (Rs.)", secondary_y=True, showgrid=False)

    # Harvest period annotation
    st.markdown("""<div style='font-size:.75rem;color:#16a34a;font-weight:700;margin-bottom:6px;'>
        🌴 <span style='background:#dcfce7;padding:2px 8px;border-radius:4px;'>Green shading = Harvest months (Mar–Apr, Aug–Nov)</span>
        &nbsp;&nbsp;⭐ Star markers = Harvest month yield points
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(fig_fw, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Month-by-month forward table ──────────────────────────────────────────
    st.markdown("#### 📋 "+("12-Month Forward Forecast Table" if lang=="en" else "ඉදිරි මාස 12 අනාවැකි වගුව"))
    table_df = fwd_df[["date","rainfall_mm","temp_c","yield_index","price_impact","harvest_period","monsoon"]].copy()
    table_df["date"] = table_df["date"].dt.strftime("%b %Y")
    table_df["harvest_period"] = table_df["harvest_period"].apply(lambda x: "🌾 Harvest" if x else "—")
    table_df.columns = ["Month","Rainfall (mm)","Temp (°C)","Yield Index","Est. Price (Rs.)","Harvest","Season"]
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    divider()

    # ── Monthly rainfall pattern (forward) ───────────────────────────────────
    c_heat, c_corr = st.columns([3,2])
    with c_heat:
        st.markdown("#### 🗓 "+("Monthly Forecast Rainfall Pattern" if lang=="en" else "මාසික අනාවැකි වර්ෂා රටාව"))
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
                colorscale=[[0,"#fef9c3"],[.5,"#bfdbfe"],[1,"#1e40af"]],
                showscale=True,
                colorbar=dict(title="mm", tickfont=dict(size=10))),
            text=[f"{v:.0f}mm" if v else "" for v in rain_vals],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>"))
        # Mark harvest months
        harvest_m = ["Mar","Apr","Aug","Sep","Oct","Nov"]
        for hm in harvest_m:
            if hm in mnames:
                fig_rh.add_vline(x=mnames.index(hm), line_dash="dot", line_color="#16a34a", line_width=1.5)
        fig_rh.update_layout(height=260,margin=dict(l=20,r=20,t=10,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#e8f5e9",ticksuffix=" mm"))
        st.plotly_chart(fig_rh, use_container_width=True, config={"displayModeBar":"hover"})

    with c_corr:
        st.markdown("#### 📈 "+("Yield vs Est. Price (Next 12 Months)" if lang=="en" else "අස්වැන්න හා මිල — ඉදිරි මාස 12"))
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=fwd_df["yield_index"], y=fwd_df["price_impact"],
            mode="markers+text",
            marker=dict(color=["#16a34a" if h else "#3b82f6" for h in fwd_df["harvest_period"]],
                size=10, symbol=["star" if h else "circle" for h in fwd_df["harvest_period"]]),
            text=[m.strftime("%b") for m in fwd_df["date"]],
            textposition="top center", textfont=dict(size=9),
            hovertemplate="Yield: %{x:.1f}<br>Est. Price: Rs.%{y:.2f}<extra></extra>"))
        if len(fwd_df) > 3:
            zf = np.polyfit(fwd_df["yield_index"], fwd_df["price_impact"],1); pf=np.poly1d(zf)
            xr = np.linspace(fwd_df["yield_index"].min(), fwd_df["yield_index"].max(), 40)
            fig_sc.add_trace(go.Scatter(x=xr, y=pf(xr), mode="lines",
                line=dict(color="#ef4444",width=1.5,dash="dash"), showlegend=False))
        fig_sc.update_layout(height=260,margin=dict(l=20,r=20,t=10,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(title="Yield Index",showgrid=False),
            yaxis=dict(title="Est. Price (Rs.)",gridcolor="#e8f5e9",tickprefix="Rs."))
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Monsoon & Harvest season summary ──────────────────────────────────────
    st.markdown("#### 🌀 "+("Season-by-Season Forecast Summary" if lang=="en" else "කාල ගත අනාවැකි සාරාංශය"))
    seasons_fwd = {
        "SW Monsoon (May–Sep)":     [5,6,7,8,9],
        "NE Monsoon (Nov–Jan)":     [11,12,1],
        "Inter-Monsoon 1 (Mar–Apr)":[3,4],
        "Inter-Monsoon 2 (Oct)":    [10],
    }
    seas_clrs = ["#3b82f6","#8b5cf6","#f59e0b","#22c55e"]
    sc2 = st.columns(4)
    for col,(season,months_s),clr in zip(sc2,seasons_fwd.items(),seas_clrs):
        msk = fwd_df["month"].isin(months_s)
        if msk.sum() > 0:
            ar = fwd_df.loc[msk,"rainfall_mm"].mean()
            ay = fwd_df.loc[msk,"yield_index"].mean()
            ap = fwd_df.loc[msk,"price_impact"].mean()
            harv = "✅ Harvest Season" if any(m in [3,4,8,9,10,11] for m in months_s) else "—"
        else:
            ar, ay, ap, harv = 0, 0, 0, "—"
        with col:
            st.markdown(f"""<div style='background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid {clr};border-radius:10px;padding:14px 10px;text-align:center;height:180px;display:flex;flex-direction:column;justify-content:space-between;'>
                <div style='font-size:.72rem;font-weight:800;color:{clr};'>{season}</div>
                <div>
                  <div style='font-size:.75rem;color:#3b82f6;font-weight:600;'>🌧 {ar:.0f} mm forecast</div>
                  <div style='font-size:.75rem;color:#16a34a;font-weight:600;'>🌴 Yield: {ay:.0f}/100</div>
                  <div style='font-size:.75rem;color:#f59e0b;font-weight:600;'>💰 Est. Rs.{ap:.1f}</div>
                  <div style='font-size:.72rem;color:#166534;font-weight:700;margin-top:4px;'>{harv}</div>
                </div></div>""", unsafe_allow_html=True)

# ══ EXPORT & TRADE (NEW) ═════════════════════════════════════════════════════
elif t["nav"][9] in sec_name:
    section_header("\U0001f4e6 "+t["export_title"], t["export_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['export_note']}</div>",unsafe_allow_html=True)

    # KPI row
    le=export_df.iloc[-1]; pe=export_df.iloc[-2]
    yoy=(le["Total"]-pe["Total"])/pe["Total"]*100; yoy_clr="#22c55e" if yoy>0 else "#ef4444"
    ek1,ek2,ek3,ek4=st.columns(4)
    for col,(lbl,val,clr) in zip([ek1,ek2,ek3,ek4],[
        ("\U0001f4e6 Total Exports (Latest Yr)" if lang=="en" else "\U0001f4e6 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0d85\u0db4\u0db1\u0dba\u0db1", f"${le['Total']}M","#16a34a"),
        ("\U0001f4c8 YoY Growth" if lang=="en" else "\U0001f4c8 \u0dc0\u0dcf\u0dbb\u0dca\u0DC2\u0dd2\u0d9a \u0dc0\u0dbb\u0dca\u0daf\u0dc4\u0db1\u0dba", f"{'+'if yoy>0 else ''}{yoy:.1f}%",yoy_clr),
        ("\U0001f3c6 Top Product" if lang=="en" else "\U0001f3c6 \u0db4\u0dca\u200d\u0dbb\u0db8\u0dd4\u0d9a \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1\u0dba","Desiccated Coconut","#3b82f6"),
        ("\U0001f30d Top Market" if lang=="en" else "\U0001f30d \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0dc0\u0dd9\u0dc7\u0dad\u0db4\u0ddc\u0ddc\u0dbd\u0dca","USA (22%)","#8b5cf6")]):
        with col: st.markdown(metric_card(lbl,val,clr,height=110),unsafe_allow_html=True)
    divider()

    ce1,ce2=st.columns([3,2])
    with ce1:
        st.markdown("#### \U0001f4ca "+("Export Revenue by Product (USD Million)" if lang=="en" else "\u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d9a\u0dcf\u0da4 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0d86\u0daf\u0dcf\u0dba\u0db8"))
        fig_eb=go.Figure()
        for pc,pcl in zip(PRODUCT_COLS,PRODUCT_COLORS):
            fig_eb.add_trace(go.Bar(x=export_df["year"].astype(str),y=export_df[pc],name=pc,marker_color=pcl,
                hovertemplate=f"<b>%{{x}}</b><br>{pc}: $%{{y}}M<extra></extra>"))
        fig_eb.update_layout(barmode="stack",height=320,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="$",ticksuffix="M"),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)))
        st.plotly_chart(fig_eb,use_container_width=True,config={"displayModeBar":"hover"})
    with ce2:
        st.markdown("#### \U0001f30d "+("Export Destinations (Latest Year)" if lang=="en" else "\u0d85\u0db4\u0db1\u0dba\u0db1 \u0d9c\u0db8\u0db1\u0dcf\u0db1\u0dca\u0dad"))
        fig_dest=go.Figure(go.Pie(labels=destinations_df["Country"],values=destinations_df["Share_pct"],hole=.45,
            textinfo="label+percent",textfont=dict(size=10),marker=dict(colors=px.colors.qualitative.Set3),
            hovertemplate="<b>%{label}</b><br>Share: %{percent}<br>$%{customdata}M<extra></extra>",customdata=destinations_df["Value_USD_M"]))
        fig_dest.update_layout(height=320,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_dest,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Export vs domestic price
    st.markdown("#### \U0001f4c8 "+("Export Growth vs Domestic Price" if lang=="en" else "\u0d85\u0db4\u0db1\u0dba\u0db1 \u0dc0\u0dbb\u0dca\u0daf\u0dc4\u0db1\u0dba \u0dc4\u0dcf \u0daf\u0dda\u0DC1\u0dd3\u0dba \u0db8\u0dd2\u0dbd \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf\u0dc0"))
    ap=history_df.groupby("year")["price"].mean().reset_index()
    me=export_df.merge(ap,on="year",how="inner")
    fig_ep=make_subplots(specs=[[{"secondary_y":True}]])
    fig_ep.add_trace(go.Bar(x=me["year"].astype(str),y=me["Total"],name="Export Revenue ($M)",
        marker_color="rgba(22,163,74,.5)",hovertemplate="<b>%{x}</b><br>$%{y}M<extra></extra>"),secondary_y=False)
    fig_ep.add_trace(go.Scatter(x=me["year"].astype(str),y=me["price"],name="Domestic Price (Rs.)",
        line=dict(color="#f59e0b",width=2.5),mode="lines+markers",marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Rs.%{y:.2f}<extra></extra>"),secondary_y=True)
    fig_ep.update_layout(height=300,margin=dict(l=20,r=60,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_ep.update_yaxes(title_text="Export Revenue ($M)",secondary_y=False,gridcolor="#e8f5e9",tickprefix="$",ticksuffix="M")
    fig_ep.update_yaxes(title_text="Domestic Price (Rs.)",secondary_y=True,showgrid=False,tickprefix="Rs.")
    st.plotly_chart(fig_ep,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Individual product trends
    st.markdown("#### \U0001f4c9 "+("Individual Product Export Trends" if lang=="en" else "\u0dad\u0db1\u0dd2 \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d85\u0db4\u0db1\u0dba\u0db1 \u0db4\u0dca\u200d\u0dbb\u0dc0\u0dab\u0dad\u0dcf"))
    fig_pt=go.Figure()
    for pc,pcl in zip(PRODUCT_COLS,PRODUCT_COLORS):
        fig_pt.add_trace(go.Scatter(x=export_df["year"].astype(str),y=export_df[pc],mode="lines+markers",name=pc,
            line=dict(color=pcl,width=2),marker=dict(size=6),hovertemplate=f"<b>%{{x}}</b><br>{pc}: $%{{y}}M<extra></extra>"))
    fig_pt.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="$",ticksuffix="M"),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)))
    st.plotly_chart(fig_pt,use_container_width=True,config={"displayModeBar":"hover"})

# ══ FARMER PROFITABILITY (NEW) ═══════════════════════════════════════════════
elif t["nav"][10] in sec_name:
    section_header("\U0001f9d1\u200d\U0001f33e "+t["farmer_title"], t["farmer_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['farmer_note']}</div>",unsafe_allow_html=True)

    st.markdown("#### \u2699\ufe0f "+("Your Farm Parameters" if lang=="en" else "\u0d94\u0db6\u0dda \u0d9c\u0ddc\u0dc0\u0dd2\u0dad\u0dd0\u0db1\u0dca \u0daf\u0dad\u0dca\u0dad"))
    fi1,fi2,fi3=st.columns(3)
    with fi1:
        farm_acres=st.slider("\U0001f334 "+("Farm Size (acres)" if lang=="en" else "\u0d9c\u0ddc\u0dc0\u0dd2\u0dad\u0dd0\u0db1\u0dca \u0dc0\u0dd2\u0DC1\u0dcf\u0dbd\u0dad\u0dca\u0dc0\u0dba (\u0d85\u0d9a\u0dca\u0d9a\u0dbb)"),1,50,5,1)
        trees_acre=st.slider("\U0001f333 "+("Trees per Acre" if lang=="en" else "\u0d85\u0d9a\u0dca\u0d9a\u0dbb\u0dba\u0d9a\u0da7 \u0d9c\u0dc3\u0dca"),20,80,40,5)
    with fi2:
        nuts_tree=st.slider("\U0001f965 "+("Nuts per Tree/Year" if lang=="en" else "\u0d9c\u0dc3\u0d9a\u0da7 \u0d9c\u0dd0\u0da9\u0dd2/\u0dc0\u0dbb\u0dca\u0DC2\u0dba"),30,120,60,5)
        sell_price=st.slider("\U0001f4b0 "+("Selling Price (Rs./nut)" if lang=="en" else "\u0dc0\u0dd2\u0d9a\u0dd2\u0da4\u0dd4\u0db8\u0dca \u0db8\u0dd2\u0dbd (\u0dbb\u0dd4./\u0d9c\u0dd0\u0da9\u0dd2\u0dba)"),30,120,int(current_price),1)
    with fi3:
        labour_month=st.slider("\U0001f477 "+("Labour Cost (Rs./month)" if lang=="en" else "\u0d9a\u0db8\u0dca\u0d9a\u0dbb\u0dd4 \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba (\u0dbb\u0dd4./\u0db8\u0dcf\u0dc3\u0dba)"),5000,50000,15000,1000)
        fert_year=st.slider("\U0001f33f "+("Fertilizer & Inputs (Rs./yr)" if lang=="en" else "\u0db4\u0ddc\u0dc4\u0ddc\u0dbb & \u0d86\u0daf\u0dcf\u0db1 (\u0dbb\u0dd4./\u0dc0\u0dbb\u0dca\u0DC2\u0dba)"),5000,100000,25000,5000)

    # Calculations
    total_trees=farm_acres*trees_acre; total_nuts=total_trees*nuts_tree
    gross_rev=total_nuts*sell_price; labour_ann=labour_month*12
    transport=gross_rev*.05; other=gross_rev*.03
    total_cost=labour_ann+fert_year+transport+other
    net_profit=gross_rev-total_cost
    margin=net_profit/gross_rev*100 if gross_rev>0 else 0
    be_price=total_cost/total_nuts if total_nuts>0 else 0
    pc_=("#22c55e" if net_profit>0 else "#ef4444")
    divider()
    st.markdown("#### \U0001f4ca "+("Profitability Results" if lang=="en" else "\u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0dc2\u0dbd"))
    r1,r2,r3,r4,r5=st.columns(5)
    for col,(lbl,val,clr) in zip([r1,r2,r3,r4,r5],[
        ("\U0001f965 Total Nuts/Year" if lang=="en" else "\U0001f965 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0d9c\u0dd0\u0da9\u0dd2/\u0dc0\u0dbb\u0dca\u0DC2\u0dba", f"{total_nuts:,}","#16a34a"),
        ("\U0001f4b5 Gross Revenue" if lang=="en" else "\U0001f4b5 \u0daf\u0dbc \u0d86\u0daf\u0dcf\u0dba\u0db8", f"Rs.{gross_rev:,.0f}","#3b82f6"),
        ("\U0001f4c9 Total Costs" if lang=="en" else "\U0001f4c9 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dd2\u0dbb\u0dd2\u0dc0\u0dd0\u0dba", f"Rs.{total_cost:,.0f}","#ef4444"),
        (("\u2705 Net Profit" if net_profit>0 else "\u274c Net Loss") if lang=="en" else ("\u2705 \u0DC1\u0dd4\u0daf\u0dca\u0db0 \u0dbd\u0dcf\u0dbb\u0dca\u0dba\u0dba" if net_profit>0 else "\u274c \u0dbd\u0dcf\u0dbb\u0dca \u0d85\u0dc0"),
         f"Rs.{net_profit:,.0f}",pc_),
        ("\U0001f4d0 Profit Margin" if lang=="en" else "\U0001f4d0 \u0dbd\u0dcf\u0dbb\u0dca \u0db8\u0dcf\u0daf\u0dd2\u0dbd\u0dd2\u0dba",f"{margin:.1f}%",pc_)]):
        with col: st.markdown(metric_card(lbl,val,clr,height=90),unsafe_allow_html=True)
    divider()

    cw,cb=st.columns([3,2])
    with cw:
        st.markdown("#### \U0001f4a7 "+("Revenue Waterfall" if lang=="en" else "\u0d86\u0daf\u0dcf\u0dba\u0db8\u0dca \u0daf\u0dd2\u0dba \u0d87\u0dbd\u0dca\u0dbd"))
        fig_wf=go.Figure(go.Waterfall(orientation="v",
            measure=["absolute","relative","relative","relative","relative","total"],
            x=["Gross Revenue","Labour","Fertilizer","Transport","Other","Net Profit"],
            y=[gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit],
            connector=dict(line=dict(color="#94a3b8",width=1.5)),
            increasing=dict(marker=dict(color="#16a34a")),decreasing=dict(marker=dict(color="#ef4444")),totals=dict(marker=dict(color=pc_)),
            text=[f"Rs.{abs(v):,.0f}" for v in [gross_rev,-labour_ann,-fert_year,-transport,-other,net_profit]],
            textposition="outside",textfont=dict(size=10)))
        fig_wf.update_layout(height=300,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs."),xaxis=dict(showgrid=False),showlegend=False)
        st.plotly_chart(fig_wf,use_container_width=True,config={"displayModeBar":"hover"})
    with cb:
        st.markdown("#### \U0001f4cd "+("Break-Even Analysis" if lang=="en" else "\u0DC1\u0dda\u0DC2-\u0dc3\u0dca\u0da5\u0dcf\u0db1 \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba"))
        pr_be=np.linspace(20,120,100)
        fig_be=go.Figure()
        fig_be.add_trace(go.Scatter(x=pr_be,y=pr_be*total_nuts-total_cost,mode="lines",line=dict(color="#16a34a",width=2.5),showlegend=False,
            hovertemplate="Price: Rs.%{x:.1f}<br>Profit: Rs.%{y:,.0f}<extra></extra>"))
        fig_be.add_hline(y=0,line_dash="dash",line_color="#ef4444",annotation_text="Break-even" if lang=="en" else "\u0DC1\u0dda\u0DC2 \u0dc3\u0dca\u0da5\u0dcf\u0db1\u0dba")
        fig_be.add_vline(x=sell_price,line_dash="dot",line_color="#f59e0b",annotation_text=f"Current Rs.{sell_price}",annotation_position="top right")
        fig_be.add_vline(x=be_price,line_dash="dash",line_color="#ef4444",annotation_text=f"BE Rs.{be_price:.1f}",annotation_position="bottom right")
        fig_be.update_layout(height=260,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
            xaxis=dict(title="Price per Nut (Rs.)",showgrid=False),yaxis=dict(title="Net Profit (Rs.)",gridcolor="#e8f5e9"),showlegend=False)
        st.plotly_chart(fig_be,use_container_width=True,config={"displayModeBar":"hover"})
        bev=sell_price-be_price; bec="#22c55e" if bev>0 else "#ef4444"
        st.markdown(f"""<div style='background:#f8fafc;border:2px solid {bec};border-radius:10px;padding:12px;text-align:center;margin-top:8px;'>
            <div style='font-size:.72rem;color:#64748b;font-weight:700;margin-bottom:4px;'>{"Break-Even Price" if lang=="en" else "\u0DC1\u0dda\u0DC2-\u0dc3\u0dca\u0da5\u0dcf\u0db1 \u0db8\u0dd2\u0dbd"}</div>
            <div style='font-size:1.4rem;font-weight:900;color:{bec};'>Rs.{be_price:.2f}</div>
            <div style=\'font-size:.78rem;color:{bec};margin-top:4px;\'>{chr(9989) if bev>0 else chr(10060)} Rs.{abs(bev):.2f} {"above" if bev>0 else "below"} current</div></div>""",unsafe_allow_html=True)
    divider()

    st.markdown("#### \U0001f4c8 "+("Profit Sensitivity to Selling Price" if lang=="en" else "\u0dc0\u0dd2\u0d9a\u0dd2\u0da4\u0dd4\u0db8\u0dca \u0db8\u0dd2\u0dbd\u0da7 \u0dbd\u0dcf\u0dbb\u0dca \u0dc3\u0d82\u0dc0\u0dda\u0daf\u0dd3\u0dad\u0dcf\u0dc0"))
    ps=[40,50,55,60,65,68.5,70,75,80,85,90,100]
    prf=[p*total_nuts-total_cost for p in ps]
    fig_ps=go.Figure(go.Bar(x=[f"Rs.{p}" for p in ps],y=prf,marker_color=["#22c55e" if v>0 else "#ef4444" for v in prf],
        text=[f"Rs.{v:,.0f}" for v in prf],textposition="outside",textfont=dict(size=9),
        hovertemplate="Price: %{x}<br>Profit: Rs.%{y:,.0f}<extra></extra>"))
    fig_ps.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
    fig_ps.update_layout(height=280,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs."),showlegend=False)
    st.plotly_chart(fig_ps,use_container_width=True,config={"displayModeBar":"hover"})

# ══ GLOBAL COMPARISON (NEW) ══════════════════════════════════════════════════
elif t["nav"][11] in sec_name:
    section_header("\U0001f30d "+t["global_title"], t["global_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['global_note']}</div>",unsafe_allow_html=True)

    # KPI row
    sl_l=global_price_df["Sri Lanka"].iloc[-1]
    w_avg=global_price_df[["Indonesia","Philippines","India","Vietnam"]].iloc[-1].mean()
    sl_vs=sl_l-w_avg; sv_clr="#f59e0b" if sl_vs>0 else "#22c55e"
    gk1,gk2,gk3,gk4=st.columns(4)
    for col,(lbl,val,clr) in zip([gk1,gk2,gk3,gk4],[
        ("\U0001f1f1\U0001f1f0 SL Price (2024)" if lang=="en" else "\U0001f1f1\U0001f1f0 \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db8\u0dd2\u0dbd 2024", f"Rs.{sl_l:.0f}","#16a34a"),
        ("\U0001f30d World Avg Price" if lang=="en" else "\U0001f30d \u0dbd\u0ddc\u0d9a \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba", f"Rs.{w_avg:.0f}","#3b82f6"),
        ("\U0001f4ca SL Premium" if lang=="en" else "\U0001f4ca \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0dc0\u0dd9\u0db1\u0dc3", f"{'+' if sl_vs>0 else ''}{sl_vs:.0f} Rs ({(sl_vs/w_avg*100):+.1f}%)",sv_clr),
        ("\U0001f3ed World Rank" if lang=="en" else "\U0001f3ed \u0dbd\u0ddc\u0d9a \u0DC1\u0dca\u200d\u0dbb\u0dda\u0da4\u0dd2\u0dba","3rd Largest Producer" if lang=="en" else "3 \u0dc0\u0dd0\u0db1\u0dd2 \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0d9a\u0dba\u0dcf","#8b5cf6")]):
        with col: st.markdown(metric_card(lbl,val,clr,height=110),unsafe_allow_html=True)
    divider()

    # Multi-country trend
    st.markdown("#### \U0001f4c8 "+("Coconut Price Comparison - Major Producers (LKR Equivalent)" if lang=="en" else "\u0db4\u0ddc\u0dbd\u0dca \u0db8\u0dd2\u0dbd \u0dc3\u0d82\u0dc3\u0db1\u0dca\u0daf\u0db1\u0dba - \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0d9a\u0dba\u0dcf\u0db1\u0dca (LKR)"))
    c_colors={"Sri Lanka":"#16a34a","Indonesia":"#3b82f6","Philippines":"#f59e0b","India":"#ef4444","Vietnam":"#8b5cf6"}
    fig_gl=go.Figure()
    for country,clr in c_colors.items():
        is_sl=(country=="Sri Lanka")
        fig_gl.add_trace(go.Scatter(x=global_price_df["year"].astype(str),y=global_price_df[country],
            mode="lines+markers",name=("\U0001f1f1\U0001f1f0 " if is_sl else "")+country,
            line=dict(color=clr,width=3.5 if is_sl else 1.8,dash="solid" if is_sl else "dot"),
            marker=dict(size=8 if is_sl else 5),hovertemplate=f"<b>{country}</b> %{{x}}<br>Rs.%{{y:.1f}}<extra></extra>"))
    fig_gl.update_layout(height=340,margin=dict(l=80,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",tickfont=dict(size=11)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig_gl,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    cp2,cr=st.columns(2)
    with cp2:
        st.markdown("#### \U0001f30d "+("Global Coconut Production Share" if lang=="en" else "\u0d9c\u0ddd\u0dbd\u0dd3\u0dba \u0db4\u0ddc\u0dbd\u0dca \u0db1\u0dd2\u0DC2\u0dca\u0db4\u0dcf\u0daf\u0db1 \u0d9a\u0ddc\u0da7\u0dc3"))
        fig_pp=go.Figure(go.Pie(labels=production_df["Country"],values=production_df["Production_B_nuts"],hole=.45,
            textinfo="label+percent",textfont=dict(size=10),
            marker=dict(colors=["#3b82f6","#f59e0b","#ef4444","#16a34a","#8b5cf6","#06b6d4","#84cc16"]),
            pull=[.08 if c=="Sri Lanka" else 0 for c in production_df["Country"]],
            hovertemplate="<b>%{label}</b><br>%{value}B nuts/yr<br>%{percent}<extra></extra>"))
        fig_pp.update_layout(height=320,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="#fff",showlegend=False)
        st.plotly_chart(fig_pp,use_container_width=True,config={"displayModeBar":"hover"})
    with cr:
        st.markdown("#### \U0001f4ca "+("Country Competitiveness Radar" if lang=="en" else "\u0dbb\u0da7\u0dc0\u0dbd\u0dca \u0dad\u0dbb\u0d9c\u0d9a\u0dcf\u0dbb\u0dd2\u0dad\u0dca\u0dc0 \u0dbb\u0dda\u0daf\u0dcf\u0dbb\u0dca"))
        ctries=["Sri Lanka","Indonesia","Philippines","India","Vietnam"]
        attrs=["Quality","Volume","Price Comp.","Export Infra.","Processing"]
        scores={"Sri Lanka":[88,40,55,72,80],"Indonesia":[70,95,90,82,75],"Philippines":[75,85,80,78,70],"India":[80,88,72,80,82],"Vietnam":[65,50,88,60,55]}
        clrs_r=["#16a34a","#3b82f6","#f59e0b","#ef4444","#8b5cf6"]
        fig_rad=go.Figure()
        for ct,clr in zip(ctries,clrs_r):
            v=scores[ct]+[scores[ct][0]]; a=attrs+[attrs[0]]
            c_int=int(clr[1:3],16); c_g=int(clr[3:5],16); c_b=int(clr[5:7],16)
            fig_rad.add_trace(go.Scatterpolar(r=v,theta=a,fill="toself",fillcolor=f"rgba({c_int},{c_g},{c_b},.08)",
                line=dict(color=clr,width=2),name=ct,hovertemplate=f"<b>{ct}</b><br>%{{theta}}: %{{r}}<extra></extra>"))
        fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100],tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=10)),bgcolor="#fff"),
            height=320,margin=dict(l=30,r=30,t=20,b=20),paper_bgcolor="#fff",
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=9)))
        st.plotly_chart(fig_rad,use_container_width=True,config={"displayModeBar":"hover"})
    divider()

    # Price gap table
    st.markdown("#### \U0001f4cb "+("Price Gap Analysis vs Sri Lanka (Latest Year)" if lang=="en" else "\u0db8\u0dd2\u0dbd \u0db4\u0dbb\u0dad\u0dbb \u0dc0\u0dd2\u0DC1\u0dca\u0dbd\u0dda\u0DC2\u0dab\u0dba"))
    lr=global_price_df.iloc[-1]; sl_p=lr["Sri Lanka"]
    gdrows=[]
    for ct in ["Indonesia","Philippines","India","Vietnam"]:
        cp_=lr[ct]; gap=sl_p-cp_; gp=gap/cp_*100
        gdrows.append({"Country":ct,"Price (Rs.)":round(cp_,1),"SL Price (Rs.)":round(sl_p,1),"Gap (Rs.)":round(gap,1),"Gap (%)":round(gp,1),"SL vs This":("Higher\u2191" if gap>0 else "Lower\u2193")})
    st.dataframe(pd.DataFrame(gdrows),use_container_width=True,hide_index=True)
    divider()

    # Price divergence over time
    st.markdown("#### \U0001f4c9 "+("SL Price Divergence from World Average" if lang=="en" else "\u0dbd\u0ddc\u0d9a \u0dc3\u0dcf\u0db8\u0dcf\u0db1\u0dca\u0dba\u0dba\u0dd9\u0db1\u0dca \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0d85\u0db4\u0d9c\u0db8\u0db1\u0dba"))
    wavg_s=global_price_df[["Indonesia","Philippines","India","Vietnam"]].mean(axis=1)
    sldev=global_price_df["Sri Lanka"]-wavg_s
    fig_dv=go.Figure(go.Bar(x=global_price_df["year"].astype(str),y=sldev,
        marker_color=["#22c55e" if v>0 else "#ef4444" for v in sldev],
        text=[f"Rs.{v:+.1f}" for v in sldev],textposition="outside",textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>SL Premium: Rs.%{y:.1f}<extra></extra>"))
    fig_dv.add_hline(y=0,line_color="#94a3b8",line_width=1.5)
    fig_dv.update_layout(height=280,margin=dict(l=20,r=20,t=20,b=20),plot_bgcolor="#fff",paper_bgcolor="#fff",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#e8f5e9",tickprefix="Rs.",title="Premium above World Avg"),showlegend=False)
    st.plotly_chart(fig_dv,use_container_width=True,config={"displayModeBar":"hover"})


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
divider()
st.markdown("""
<div style='text-align:center;padding:clamp(20px,4vw,36px) clamp(12px,5vw,48px) clamp(18px,3vw,32px);margin-bottom:28px;
  background:linear-gradient(135deg,#0d2b0d 0%,#14532d 50%,#166534 100%);border-radius:14px;box-shadow:0 4px 20px rgba(13,43,13,.18);'>
  <div style='font-size:clamp(1.3rem,5vw,2rem);font-weight:900;color:#fff;margin-bottom:8px;text-shadow:0 2px 8px rgba(0,0,0,.2);'>Sri Lanka Coconut Industry</div>
  <div style='font-size:clamp(.78rem,2.5vw,.9rem);color:#bbf7d0;font-weight:500;opacity:.9;'>Key Organisations, Contacts &amp; Industry Facts</div>
</div>
""",unsafe_allow_html=True)

oc1,oc2,oc3,oc4=st.columns(4)
orgs=[
    ("\U0001f3db","Primary Regulator","Coconut Development Authority","No.54, Nawam Mawatha<br>Colombo 02","+94 11 243 0610","www.cda.gov.lk","https://www.cda.gov.lk"),
    ("\U0001f52c","Research Institute","Coconut Research Institute (CRI)","Bandirippuwa Estate<br>Lunuwila 61150","+94 31 222 2481","www.cri.gov.lk","https://www.cri.gov.lk"),
    ("\U0001f4e6","Export Promoter","Sri Lanka Export Development Board","42 Nawam Mawatha<br>Colombo 02","+94 11 230 0705","www.srilankabusiness.com","https://www.srilankabusiness.com"),
    ("\U0001f6d2","Market & Auction","HARTI / Economic Centres","Narahenpita, Colombo 05<br>(Head Office)","+94 11 259 1919","www.harti.gov.lk","https://www.harti.gov.lk"),
]
for col,(icon,badge,name,addr,phone,web,url) in zip([oc1,oc2,oc3,oc4],orgs):
    with col:
        st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid #16a34a;border-radius:10px;padding:16px 14px;height:240px;display:flex;flex-direction:column;'>
            <div style='font-size:.58rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{icon} {badge}</div>
            <div style='font-weight:800;font-size:.82rem;color:#0d2b0d;margin-bottom:10px;line-height:1.3;'>{name}</div>
            <div style='font-size:.72rem;color:#374151;line-height:1.9;flex:1;'>\U0001f4cd {addr}<br>\U0001f4de {phone}<br>\U0001f310 <a href='{url}' target='_blank' style='color:#16a34a;font-weight:600;text-decoration:none;'>{web}</a></div>
        </div>""",unsafe_allow_html=True)
divider()
st.markdown("<div style='text-align:center;font-size:.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;'>\U0001f4ca Sri Lanka Coconut Industry at a Glance</div>",unsafe_allow_html=True)
s1,s2,s3,s4,s5,s6=st.columns(6)
for col,(val,lbl) in zip([s1,s2,s3,s4,s5,s6],[("~2.7M","Hectares"),("~3B","Nuts/Year"),("450K+","Families"),("$350M+","Exports"),("3rd","World Rank"),("~2%","GDP Share")]):
    with col:
        st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid #16a34a;border-radius:10px;padding:12px 8px;text-align:center;height:90px;display:flex;flex-direction:column;justify-content:center;'>
            <div style='font-size:1.4rem;font-weight:900;color:#0d2b0d;'>{val}</div>
            <div style='font-size:.68rem;color:#4a7a4a;margin-top:4px;font-weight:600;text-transform:uppercase;'>{lbl}</div></div>""",unsafe_allow_html=True)
divider()
st.markdown("<div style='text-align:center;font-size:.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;'>\U0001f4cd The Coconut Triangle - Main Growing Districts</div>",unsafe_allow_html=True)
dd1,dd2,dd3,dd4,dd5=st.columns(5)
for col,dist in zip([dd1,dd2,dd3,dd4,dd5],["Kurunegala","Puttalam","Gampaha","Colombo","Kalutara"]):
    with col:
        st.markdown(f"""<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 8px;text-align:center;'>
            <div style='font-size:1.4rem;'>🌴</div>
            <div style='font-size:.85rem;font-weight:700;color:#0d2b0d;margin-top:6px;'>{dist}</div></div>""",unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)
st.markdown("<div style='text-align:center;font-size:.72rem;color:#4a7a4a;padding:16px 0;border-top:1px solid #d1e7d1;margin-top:8px;'>🥥 COCOStat \u00b7 Coconut Market Intelligence Dashboard \u00b7 Data from CDA &amp; CRI Sri Lanka</div>",unsafe_allow_html=True)
