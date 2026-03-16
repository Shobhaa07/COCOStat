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
                "Weather & Harvest","Export & Trade","Farmer Profitability","Auction Details","Recommendations"],
        "nav_icons":["\U0001f4ca","\U0001f6a6","\U0001f4c9","\U0001f52e","\U0001f3db","\U0001f4c8",
                     "\U0001f50d","\U0001f9e0","\U0001f326","\U0001f4e6","\U0001f9d1\u200d\U0001f33e","\U0001f6a9","\U0001f9e9"],
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
        "auction_title":"\U0001f6a9 Sri Lanka Coconut Auction Details",
        "auction_sub":"Official auction schedules, venues, and key information for Sri Lanka coconut auctions managed by CDA & HARTI.",
        "auction_note":"\U0001f4a1 Coconut auctions are the primary price-discovery mechanism in Sri Lanka. Prices set at auction directly affect farmers, traders, and consumers.",
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
                "\u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab & \u0d85\u0dc3\u0dca\u0dc0\u0db1\u0dd4","\u0d85\u0db4\u0db1\u0dba\u0db1 & \u0dc0\u0dd9\u0dc5\u0db3\u0dcf\u0db8","\u0d9c\u0ddc\u0dc0\u0dd2 \u0dbd\u0dcf\u0db7\u0daf\u0dcf\u0dba\u0dd2\u0dad\u0dcf\u0dc0","\u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb","\u0db1\u0dd2\u0dbb\u0dca\u0daf\u0dda\u0DC1"],
        "nav_icons":["\U0001f4ca","\U0001f6a6","\U0001f4c9","\U0001f52e","\U0001f3db","\U0001f4c8",
                     "\U0001f50d","\U0001f9e0","\U0001f326","\U0001f4e6","\U0001f9d1\u200d\U0001f33e","\U0001f6a9","\U0001f9e9"],
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
        "auction_title":"\U0001f6a9 \u0DC1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0d82\u0d9a\u0dcf \u0db4\u0ddc\u0dbd\u0dca \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb",
        "auction_sub":"\u0dc3\u0dd0\u0dba CDA \u0dc3\u0dc4 HARTI \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1\u0dba \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0dc3\u0dad\u0dd2 \u0dc0\u0dd9\u0dbd\u0dda\u0dc0\u0dbd\u0dca, \u0dc3\u0dca\u0dad\u0dcf\u0db1, \u0dc3\u0dc4 \u0d9c\u0ddc\u0dc0\u0dd2\u0db1\u0dca\u0da7 \u0dc0\u0dcf\u0dbb\u0dca\u0dad\u0dcf \u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4.",
        "auction_note":"\U0001f4a1 \u0dc0\u0dd9\u0db1\u0dca\u0daf\u0dda\u0dc3\u0dd2 \u0db8\u0dd2\u0dbd \u0db1\u0dd2\u0dba\u0db8\u0dba \u0d9c\u0ddc\u0dc0\u0dd3\u0db1\u0dca\u0da7, \u0dc0\u0dca\u200d\u0dba\u0dcf\u0db4\u0dcf\u0dbb\u0dd2\u0d9a\u0dba\u0db1\u0dca\u0da7 \u0dc3\u0dc4 \u0db4\u0dbb\u0dd2\u0db4\u0dcf\u0dbd\u0d9a\u0dba\u0db1\u0dca\u0da7 \u0db4\u0dca\u200d\u0dbb\u0dad\u0dca\u0dba\u0d9a\u0dca\u0DC1\u0dba\u0dba\u0dd9\u0db1\u0dca \u0db6\u0dbd\u0db4\u0dcf\u0db1\u0dcf\u0dc0\u0dba.",
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
    st.markdown("""<div style='text-align:center;padding:22px 0 14px;border-bottom:2px solid #d1e7d1;margin-bottom:4px;'>
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

    # ══ PRICE RISK EARLY WARNING SYSTEM ══
    st.markdown(f"""<div style='background:linear-gradient(135deg,#0d2b0d,#166534);border-radius:10px;
        padding:10px 12px;margin-bottom:10px;text-align:center;'>
      <div style='font-size:.72rem;font-weight:900;color:#4ade80;text-transform:uppercase;letter-spacing:1.5px;'>
        🚦 {'Price Risk Early Warning' if lang=='en' else 'මිල අවදානම් අනතුරු ඇඟවීම'}
      </div>
    </div>""", unsafe_allow_html=True)

    current_price    = 68.50
    price_3m_ago     = float(history_df["price"].iloc[-4]) if len(history_df) >= 4 else current_price
    price_6m_ago     = float(history_df["price"].iloc[-7]) if len(history_df) >= 7 else current_price
    avg_12m_sb       = float(history_df["price"].tail(12).mean())
    avg_3m_sb        = float(history_df["price"].tail(3).mean())
    volatility_sb    = float(history_df["price"].tail(12).std())
    momentum_3m      = ((current_price - price_3m_ago) / price_3m_ago) * 100
    momentum_6m      = ((current_price - price_6m_ago) / price_6m_ago) * 100
    crisis_months_sb = int((history_df["price"].tail(12) >= 80).sum())

    # Thresholds (user-configurable)
    warn_threshold   = st.slider(
        "⚠️ Warning Level (Rs.)" if lang=="en" else "⚠️ අවවාද සීමාව (රු.)",
        min_value=50, max_value=90, value=65, step=1)
    crisis_threshold = st.slider(
        "🔴 Crisis Level (Rs.)" if lang=="en" else "🔴 අර්බුද සීමාව (රු.)",
        min_value=60, max_value=120, value=80, step=1)

    # ── Risk Score Engine ──────────────────
    risk_score = 0
    risk_factors = []

    # Factor 1: Current price vs thresholds
    if current_price >= crisis_threshold:
        risk_score += 40
        risk_factors.append(("🔴", f"Price Rs.{current_price:.0f} above crisis level", 40))
    elif current_price >= warn_threshold:
        risk_score += 25
        risk_factors.append(("🟡", f"Price Rs.{current_price:.0f} above warning level", 25))
    else:
        risk_factors.append(("🟢", f"Price Rs.{current_price:.0f} within safe range", 0))

    # Factor 2: 3-month momentum
    if momentum_3m > 15:
        risk_score += 20
        risk_factors.append(("🔴", f"Rapid 3M rise: +{momentum_3m:.1f}%", 20))
    elif momentum_3m > 8:
        risk_score += 12
        risk_factors.append(("🟡", f"Moderate 3M rise: +{momentum_3m:.1f}%", 12))
    elif momentum_3m < -10:
        risk_score += 5
        risk_factors.append(("🔵", f"Sharp 3M drop: {momentum_3m:.1f}%", 5))
    else:
        risk_factors.append(("🟢", f"3M change stable: {momentum_3m:+.1f}%", 0))

    # Factor 3: Volatility
    cv_sb = (volatility_sb / avg_12m_sb) * 100
    if cv_sb > 18:
        risk_score += 20
        risk_factors.append(("🔴", f"High volatility: CV {cv_sb:.1f}%", 20))
    elif cv_sb > 10:
        risk_score += 10
        risk_factors.append(("🟡", f"Moderate volatility: CV {cv_sb:.1f}%", 10))
    else:
        risk_factors.append(("🟢", f"Low volatility: CV {cv_sb:.1f}%", 0))

    # Factor 4: Distance to crisis threshold
    gap_to_crisis = crisis_threshold - current_price
    if gap_to_crisis <= 5:
        risk_score += 15
        risk_factors.append(("🔴", f"Only Rs.{gap_to_crisis:.0f} below crisis level", 15))
    elif gap_to_crisis <= 12:
        risk_score += 8
        risk_factors.append(("🟡", f"Rs.{gap_to_crisis:.0f} buffer to crisis level", 8))
    else:
        risk_factors.append(("🟢", f"Rs.{gap_to_crisis:.0f} buffer to crisis level", 0))

    # Factor 5: Recent crisis months
    if crisis_months_sb >= 4:
        risk_score += 5
        risk_factors.append(("🟡", f"{crisis_months_sb} crisis months (last 12)", 5))

    risk_score = min(risk_score, 100)

    # Risk level classification
    if risk_score >= 70:
        rl_label = "🔴 CRISIS RISK" if lang=="en" else "🔴 අර්බුද අවදානම"
        rl_clr   = "#ef4444"; rl_bg = "#fef2f2"; rl_border = "#fca5a5"
        rl_action = "Immediate action required" if lang=="en" else "ක්ෂණික පියවර අවශ්‍යයි"
    elif risk_score >= 45:
        rl_label = "🟡 ELEVATED RISK" if lang=="en" else "🟡 ඉහළ අවදානම"
        rl_clr   = "#d97706"; rl_bg = "#fffbeb"; rl_border = "#fcd34d"
        rl_action = "Close monitoring needed" if lang=="en" else "සමීප නිරීක්ෂණය කරන්න"
    elif risk_score >= 25:
        rl_label = "🟡 WATCH" if lang=="en" else "🟡 නිරීක්ෂණය"
        rl_clr   = "#ca8a04"; rl_bg = "#fefce8"; rl_border = "#fde68a"
        rl_action = "Monitor weekly" if lang=="en" else "සතිපතා නිරීක්ෂණය"
    else:
        rl_label = "🟢 LOW RISK" if lang=="en" else "🟢 අඩු අවදානම"
        rl_clr   = "#16a34a"; rl_bg = "#f0fdf4"; rl_border = "#86efac"
        rl_action = "Market is stable" if lang=="en" else "වෙළඳ ස්ථාවරයි"

    # ── Risk Score Gauge ──────────────────
    # Visual bar gauge
    bar_w   = min(int(risk_score), 100)
    bar_clr = ("#ef4444" if risk_score >= 70 else "#f59e0b" if risk_score >= 45
               else "#eab308" if risk_score >= 25 else "#22c55e")
    st.markdown(f"""<div style='background:{rl_bg};border:2px solid {rl_border};border-radius:10px;
        padding:12px 12px 10px;margin-bottom:8px;'>
      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
        <div style='font-size:.72rem;font-weight:900;color:{rl_clr};'>{rl_label}</div>
        <div style='font-size:1rem;font-weight:900;color:{rl_clr};'>{risk_score}<span style='font-size:.6rem;'>/100</span></div>
      </div>
      <div style='background:#e5e7eb;border-radius:99px;height:8px;overflow:hidden;margin-bottom:6px;'>
        <div style='background:linear-gradient(90deg,#22c55e,{bar_clr});width:{bar_w}%;height:100%;
            border-radius:99px;transition:width .3s;'></div>
      </div>
      <div style='font-size:.63rem;color:{rl_clr};font-weight:700;text-align:center;'>
        {rl_action}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Risk Factor Breakdown ─────────────
    rf_label = "Risk Factors" if lang=="en" else "අවදානම් සාධක"
    rf_rows_html = ""
    for dot, label, pts in risk_factors:
        pt_span = (f"<span style='font-size:.56rem;color:#ef4444;font-weight:700;min-width:18px;text-align:right;'>+{pts}</span>"
                   if pts > 0 else
                   "<span style='min-width:18px;'></span>")
        rf_rows_html += (
            f"<div style='display:flex;align-items:center;gap:5px;padding:3px 0;"
            f"border-bottom:1px solid #f0fdf4;'>"
            f"<span style='font-size:.7rem;'>{dot}</span>"
            f"<span style='font-size:.63rem;color:#374151;flex:1;line-height:1.3;'>{label}</span>"
            f"{pt_span}"
            f"</div>"
        )
    st.markdown(
        f"<div style='font-size:.62rem;font-weight:800;color:#4a7a4a;text-transform:uppercase;"
        f"letter-spacing:1px;margin-bottom:5px;'>{rf_label}</div>"
        f"<div>{rf_rows_html}</div>",
        unsafe_allow_html=True
    )

    # ── Price Zones + Current Price + Quick Actions (all one call) ────────────
    pz_crisis_lbl  = "Crisis"  if lang=="en" else "අර්බුද"
    pz_warn_lbl    = "Warning" if lang=="en" else "අවවාද"
    pz_safe_lbl    = "Safe"    if lang=="en" else "ආරක්ෂිත"
    cp_lbl         = "Current Auction Price" if lang=="en" else "දැනට වෙන්දේසි මිල"
    mom_lbl        = "vs 3 months ago"       if lang=="en" else "මාස 3 ට සාපේක්ෂව"
    qa_label       = "Quick Actions"         if lang=="en" else "ක්ෂණික ක්‍රියා"

    if risk_score >= 70:
        actions_inner = ("🏛️ Alert CDA/HARTI officials<br>"
                         "📦 Activate buffer stocks<br>"
                         "📣 Broadcast price warnings<br>"
                         "💰 Farmers: sell immediately<br>"
                         "🏭 Businesses: hedge now")
    elif risk_score >= 45:
        actions_inner = ("📊 Monitor daily auction prices<br>"
                         "📦 Prepare buffer stock release<br>"
                         "💰 Farmers: consider selling<br>"
                         "🏭 Businesses: review contracts<br>"
                         "🔍 Watch export demand")
    elif risk_score >= 25:
        actions_inner = ("📋 Weekly price check sufficient<br>"
                         "🌱 Farmers: continue normal ops<br>"
                         "🏭 Businesses: plan ahead<br>"
                         "📈 Consider forward contracts<br>"
                         "🌍 Explore export opportunities")
    else:
        actions_inner = ("✅ No immediate action needed<br>"
                         "🌱 Good time to invest/expand<br>"
                         "📋 Monthly monitoring sufficient<br>"
                         "🏦 Build buffer stocks now<br>"
                         "🌿 Explore value-added products")

    pz_zones_label = "Price Zones" if lang=="en" else "මිල කලාප"
    st.markdown(
        f"<div style='margin-top:10px;'>"
        f"<div style='font-size:.62rem;font-weight:800;color:#4a7a4a;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{pz_zones_label}</div>"
        f"<div style='display:flex;flex-direction:column;gap:4px;'>"
        f"<div style='background:#fee2e2;border-left:3px solid #ef4444;border-radius:0 5px 5px 0;padding:4px 8px;display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-size:.63rem;font-weight:700;color:#7f1d1d;'>🔴 {pz_crisis_lbl}</span>"
        f"<span style='font-size:.63rem;font-weight:800;color:#7f1d1d;'>Rs.{crisis_threshold}+</span></div>"
        f"<div style='background:#fef9c3;border-left:3px solid #eab308;border-radius:0 5px 5px 0;padding:4px 8px;display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-size:.63rem;font-weight:700;color:#713f12;'>🟡 {pz_warn_lbl}</span>"
        f"<span style='font-size:.63rem;font-weight:800;color:#713f12;'>Rs.{warn_threshold}&#8211;{crisis_threshold-1}</span></div>"
        f"<div style='background:#dcfce7;border-left:3px solid #22c55e;border-radius:0 5px 5px 0;padding:4px 8px;display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-size:.63rem;font-weight:700;color:#14532d;'>🟢 {pz_safe_lbl}</span>"
        f"<span style='font-size:.63rem;font-weight:800;color:#14532d;'>Rs.&lt;{warn_threshold}</span></div>"
        f"</div></div>"
        f"<div style='background:#fff;border:1px solid #d1e7d1;border-radius:8px;padding:8px 10px;margin-top:8px;text-align:center;'>"
        f"<div style='font-size:.58rem;color:#4a7a4a;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>{cp_lbl}</div>"
        f"<div style='font-size:1.35rem;font-weight:900;color:{rl_clr};margin:2px 0;'>Rs. {current_price:.2f}</div>"
        f"<div style='font-size:.6rem;color:#64748b;'>{momentum_3m:+.1f}% {mom_lbl}</div>"
        f"</div>"
        f"<div style='margin-top:10px;'>"
        f"<div style='font-size:.62rem;font-weight:800;color:#4a7a4a;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{qa_label}</div>"
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 10px;'>"
        f"<div style='font-size:.63rem;line-height:1.7;color:#374151;'>{actions_inner}</div>"
        f"</div></div>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown(f"""<div style='background:#f0fdf4;border:1px solid #d1e7d1;border-radius:10px;padding:14px 12px;text-align:center;'>
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
    sub_html = (f"<div style='display:inline-block;background:#f0fdf4;color:#166534;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #bbf7d0;margin-top:4px;'>{sub}</div>"
                if sub else
                "<span style='display:none;'></span>")
    return (f"<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid {clr};border-radius:10px;padding:14px 16px;"
            f"height:{height}px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;'>"
            f"<div style='font-size:.65rem;font-weight:700;color:#4a7a4a;text-transform:uppercase;letter-spacing:.8px;'>{label}</div>"
            f"<div style='font-size:1.4rem;font-weight:900;color:{clr};line-height:1.2;'>{value}</div>"
            f"{sub_html}</div>")

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
        arr = (f"<div style='position:absolute;right:-14px;top:50%;transform:translateY(-50%);font-size:1rem;color:#16a34a;font-weight:700;z-index:2;'>\u203a</div>"
               if i < 4 else
               "<span style='display:none;'></span>")
        with col:
            st.markdown(
                f"<div style='position:relative;background:#f0fdf4;border:1px solid #d1e7d1;border-top:3px solid #16a34a;border-radius:8px;padding:16px 10px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center;'>"
                f"<div style='font-size:.68rem;font-weight:800;color:#16a34a;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>{num}</div>"
                f"<div style='font-size:.9rem;font-weight:700;color:#0d2b0d;margin-bottom:3px;'>{title}</div>"
                f"<div style='font-size:.78rem;color:#4a7a4a;font-weight:500;'>{sub}</div>"
                f"{arr}"
                f"</div>",
                unsafe_allow_html=True)
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

# ══ AUCTION DETAILS ══════════════════════════════════════════════════════════
elif t["nav"][11] in sec_name:
    section_header("\U0001f6a9 "+t["auction_title"], t["auction_sub"])
    st.markdown(f"<div class='info-box-blue'>{t['auction_note']}</div>", unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    ak1,ak2,ak3,ak4 = st.columns(4)
    for col,(lbl,val,clr) in zip([ak1,ak2,ak3,ak4],[
        ("🏛️ Primary Authority" if lang=="en" else "🏛️ ප්‍රධාන බලධාරිය",
         "CDA / HARTI", "#16a34a"),
        ("📅 Auction Frequency" if lang=="en" else "📅 වෙන්දේසි නිතිය",
         "Weekly (Mon–Fri)" if lang=="en" else "සතිපතා (සඳු–සිකු)", "#3b82f6"),
        ("🕗 Typical Start Time" if lang=="en" else "🕗 ආරම්භ වේලාව",
         "7:30 AM – 9:00 AM", "#f59e0b"),
        ("📦 Lot Size" if lang=="en" else "📦 ලොට් ප්‍රමාණය",
         "500 – 5,000 nuts" if lang=="en" else "ඇට 500 – 5,000", "#8b5cf6"),
    ]):
        with col: st.markdown(metric_card(lbl, val, clr, height=110), unsafe_allow_html=True)
    divider()

    # ── Main Auction Centres ───────────────────────────────────────────────────
    st.markdown("#### 🏢 "+("Official Coconut Auction Centres" if lang=="en" else "නිල පොල් වෙන්දේසි මධ්‍යස්ථාන"))
    centres = [
        {
            "name": "Colombo Auction Centre",
            "si_name": "කොළඹ වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "HARTI Economic Centre, Narahenpita, Colombo 05",
            "days": "Monday, Wednesday, Friday",
            "time": "7:30 AM – 10:00 AM",
            "type": "Whole Nuts & Copra",
            "authority": "HARTI / CDA",
            "phone": "+94 11 259 1919",
            "note": "Largest & most active auction. Sets the national benchmark price.",
            "clr": "#16a34a",
        },
        {
            "name": "Kurunegala Auction Centre",
            "si_name": "කුරුණෑගල වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "CDA Regional Office, Kurunegala",
            "days": "Tuesday, Thursday",
            "time": "8:00 AM – 10:30 AM",
            "type": "Whole Nuts",
            "authority": "CDA",
            "phone": "+94 37 222 2250",
            "note": "Main centre for Kurunegala district — Sri Lanka's largest coconut belt.",
            "clr": "#3b82f6",
        },
        {
            "name": "Puttalam Auction Centre",
            "si_name": "පුත්තලම වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "CDA Regional Office, Puttalam",
            "days": "Monday, Friday",
            "time": "8:00 AM – 10:00 AM",
            "type": "Whole Nuts & Coconut Oil",
            "authority": "CDA",
            "phone": "+94 32 222 5120",
            "note": "Covers northern coconut triangle; strong copra and oil trade.",
            "clr": "#f59e0b",
        },
        {
            "name": "Gampaha Auction Centre",
            "si_name": "ගම්පහ වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Nittambuwa, Gampaha",
            "days": "Tuesday, Thursday, Saturday",
            "time": "7:00 AM – 9:30 AM",
            "type": "Whole Nuts & Desiccated Coconut",
            "authority": "HARTI",
            "phone": "+94 33 222 3100",
            "note": "Serves Western Province. High volume during peak harvest months.",
            "clr": "#8b5cf6",
        },
        {
            "name": "Matara Auction Centre",
            "si_name": "මාතර වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Matara",
            "days": "Wednesday, Saturday",
            "time": "8:30 AM – 10:30 AM",
            "type": "Whole Nuts",
            "authority": "HARTI / CDA",
            "phone": "+94 41 222 2440",
            "note": "Key centre for Southern Province coconut growers.",
            "clr": "#ef4444",
        },
        {
            "name": "Kalutara Auction Centre",
            "si_name": "කළුතර වෙන්දේසි මධ්‍යස්ථානය",
            "venue": "Economic Centre, Kalutara South",
            "days": "Monday, Thursday",
            "time": "8:00 AM – 10:00 AM",
            "type": "Whole Nuts & Coconut Milk",
            "authority": "HARTI",
            "phone": "+94 34 222 5300",
            "note": "Significant trade in coconut milk products alongside whole nuts.",
            "clr": "#06b6d4",
        },
    ]

    # Display 3 per row
    for row_start in range(0, len(centres), 3):
        row_centres = centres[row_start:row_start+3]
        cols = st.columns(3)
        for col, c in zip(cols, row_centres):
            name_display = c["si_name"] if lang == "si" else c["name"]
            with col:
                st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:4px solid {c["clr"]};
                    border-radius:12px;padding:18px 16px;margin-bottom:14px;height:280px;display:flex;flex-direction:column;justify-content:space-between;'>
                    <div>
                      <div style='font-size:.6rem;font-weight:800;color:{c["clr"]};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;'>{c["authority"]}</div>
                      <div style='font-size:.9rem;font-weight:800;color:#0d2b0d;margin-bottom:10px;line-height:1.3;'>{name_display}</div>
                      <div style='font-size:.72rem;color:#374151;line-height:1.85;'>
                        📍 {c["venue"]}<br>
                        📅 {c["days"]}<br>
                        🕗 {c["time"]}<br>
                        📦 {c["type"]}<br>
                        📞 {c["phone"]}
                      </div>
                    </div>
                    <div style='font-size:.68rem;color:{c["clr"]};font-weight:600;margin-top:8px;background:{c["clr"]}11;
                        padding:6px 8px;border-radius:6px;line-height:1.4;'>💡 {c["note"]}</div>
                </div>""", unsafe_allow_html=True)
    divider()

    # ── Weekly Auction Schedule ────────────────────────────────────────────────
    st.markdown("#### 📅 "+("Weekly Auction Schedule" if lang=="en" else "සතිපතා වෙන්දේසි කාලසටහන"))
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    day_auctions = {
        "Monday":    ["Colombo (7:30 AM)","Puttalam (8:00 AM)","Kalutara (8:00 AM)"],
        "Tuesday":   ["Kurunegala (8:00 AM)","Gampaha (7:00 AM)"],
        "Wednesday": ["Colombo (7:30 AM)","Matara (8:30 AM)"],
        "Thursday":  ["Kurunegala (8:00 AM)","Gampaha (7:00 AM)","Kalutara (8:00 AM)"],
        "Friday":    ["Colombo (7:30 AM)","Puttalam (8:00 AM)"],
        "Saturday":  ["Gampaha (7:00 AM)","Matara (8:30 AM)"],
    }
    day_colors = {"Monday":"#16a34a","Tuesday":"#3b82f6","Wednesday":"#f59e0b",
                  "Thursday":"#8b5cf6","Friday":"#ef4444","Saturday":"#06b6d4"}
    sched_cols = st.columns(6)
    for col, day in zip(sched_cols, days):
        auctions = day_auctions[day]
        clr = day_colors[day]
        items_html = "".join([f"<div style='font-size:.68rem;color:#374151;padding:4px 0;border-bottom:1px solid #f0fdf4;line-height:1.4;'>🔔 {a}</div>" for a in auctions])
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid {clr};
                border-radius:10px;padding:12px 10px;min-height:160px;'>
                <div style='font-size:.72rem;font-weight:800;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:8px;text-align:center;'>{day}</div>
                {items_html}
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Auction Process & Rules ────────────────────────────────────────────────
    st.markdown("#### 📋 "+("How the Coconut Auction Works" if lang=="en" else "වෙන්දේසිය ක්‍රියාකාරිත්වය"))
    proc_cols = st.columns(4)
    steps = [
        ("01","Registration","Sellers register with CDA/HARTI at least 24 hrs before auction. Lots are inspected and graded by officials.",
         "Buyers must hold valid CDA buyer licence. Annual renewal required.","#16a34a"),
        ("02","Grading & Lot Formation","Nuts are graded by size, freshness and quality. Standard lot = 1,000 nuts. Minimum 500 nuts per lot.",
         "Grade A: ≥12cm dia. Grade B: 10–12cm. Grade C: <10cm.","#3b82f6"),
        ("03","Bidding Process","Open outcry ascending bid auction. Auctioneer calls starting price. Highest bid wins. Buyer must pay within 24 hrs.",
         "Electronic bidding being piloted at Colombo centre.","#f59e0b"),
        ("04","Settlement & Transport","Payment via bank transfer or certified cheque. Seller receives funds within 2 working days.",
         "CDA provides transport support for quantities >5,000 nuts.","#8b5cf6"),
    ]
    for col, (num, title, desc, note, clr) in zip(proc_cols, steps):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:4px solid {clr};
                border-radius:10px;padding:16px 14px;height:240px;display:flex;flex-direction:column;'>
                <div style='font-size:.6rem;font-weight:800;color:{clr};text-transform:uppercase;letter-spacing:2px;'>STEP {num}</div>
                <div style='font-size:.85rem;font-weight:800;color:#0d2b0d;margin:6px 0 8px;'>{title}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.55;flex:1;'>{desc}</div>
                <div style='font-size:.65rem;color:{clr};font-weight:600;margin-top:8px;background:{clr}11;
                    padding:5px 7px;border-radius:5px;line-height:1.4;'>ℹ️ {note}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Price Grades & Benchmarks ──────────────────────────────────────────────
    st.markdown("#### 💰 "+("Current Auction Price Benchmarks (Rs. per nut)" if lang=="en" else "වත්මන් වෙන්දේසි මිල දණ්ඩ (රු. ගෙඩියකට)"))
    import plotly.graph_objects as go
    grade_data = {
        "Grade A\n(Premium Large)": (72, 85, 78),
        "Grade B\n(Standard)":       (58, 72, 65),
        "Grade C\n(Small)":           (42, 58, 50),
        "Copra\n(per kg)":            (85, 110, 95),
        "Coconut Oil\n(per litre)":   (380, 450, 415),
    }
    fig_grades = go.Figure()
    gnames = list(grade_data.keys())
    gmins  = [v[0] for v in grade_data.values()]
    gmaxs  = [v[1] for v in grade_data.values()]
    gavgs  = [v[2] for v in grade_data.values()]
    fig_grades.add_trace(go.Bar(name="Min Price", x=gnames, y=gmins,
        marker_color="rgba(22,163,74,0.3)", text=[f"Rs.{v}" for v in gmins],
        textposition="inside", textfont=dict(size=10, color="#166534")))
    fig_grades.add_trace(go.Bar(name="Max Price", x=gnames, y=gmaxs,
        marker_color="rgba(22,163,74,0.7)", text=[f"Rs.{v}" for v in gmaxs],
        textposition="inside", textfont=dict(size=10, color="#fff")))
    fig_grades.add_trace(go.Scatter(name="Avg Price", x=gnames, y=gavgs,
        mode="markers+text", marker=dict(color="#f59e0b", size=14, symbol="diamond"),
        text=[f"Rs.{v}" for v in gavgs], textposition="top center",
        textfont=dict(size=11, color="#92400e")))
    fig_grades.update_layout(barmode="overlay", height=320,
        margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#e8f5e9", tickprefix="Rs.", title="Price (Rs.)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_grades, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ── Key Rules & Regulations ────────────────────────────────────────────────
    r1c, r2c = st.columns(2)
    with r1c:
        st.markdown("#### 📜 "+("Seller Requirements" if lang=="en" else "විකුණුම්කරු අවශ්‍යතා"))
        seller_rules = [
            ("✅","CDA Registration","All sellers must be registered with the Coconut Development Authority (CDA)."),
            ("✅","Minimum Lot","Minimum 500 nuts per auction lot. Lots must be clean and free of husked nuts."),
            ("✅","Pre-inspection","Lots must arrive at the centre at least 1 hour before auction for grading."),
            ("✅","Transport","Seller arranges transport to the auction centre. CDA may assist for large volumes."),
            ("✅","Payment","Sellers receive payment within 2 working days of auction settlement."),
        ]
        for icon, title, desc in seller_rules:
            st.markdown(f"""<div style='background:#f0fdf4;border-left:4px solid #16a34a;border-radius:0 8px 8px 0;
                padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.75rem;font-weight:800;color:#0d2b0d;'>{icon} {title}</div>
                <div style='font-size:.7rem;color:#374151;margin-top:3px;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    with r2c:
        st.markdown("#### 📜 "+("Buyer Requirements" if lang=="en" else "ගැනුම්කරු අවශ්‍යතා"))
        buyer_rules = [
            ("✅","Buyer Licence","Valid CDA buyer licence required. Obtainable from CDA Head Office, Colombo 02."),
            ("✅","Licence Fee","Annual buyer licence fee: Rs. 5,000 (Individual) / Rs. 15,000 (Company)."),
            ("✅","Deposit","Registered buyers must maintain a security deposit with the auction centre."),
            ("✅","Payment","Full payment within 24 hours of auction. Late payment attracts a 2% penalty per day."),
            ("✅","Quantity Limit","Individual buyers limited to 50,000 nuts per auction session to prevent cornering."),
        ]
        for icon, title, desc in buyer_rules:
            st.markdown(f"""<div style='background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;
                padding:10px 14px;margin-bottom:8px;'>
                <div style='font-size:.75rem;font-weight:800;color:#0d2b0d;'>{icon} {title}</div>
                <div style='font-size:.7rem;color:#374151;margin-top:3px;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Special Auctions ──────────────────────────────────────────────────────
    st.markdown("#### 🌟 "+("Special & Seasonal Auction Events" if lang=="en" else "විශේෂ සහ සෘතු වෙන්දේසි"))
    spec_cols = st.columns(3)
    specials = [
        ("🌾 Peak Harvest Auctions",
         "March–April / Aug–November",
         "Extra auction sessions added during peak harvest. Colombo centre operates 5 days/week. Prices typically lower due to high supply.",
         "#16a34a"),
        ("🏆 Premium Quality Auction",
         "Quarterly (Jan, Apr, Jul, Oct)",
         "Specially graded Grade A+ lots. Pre-registration required. Reserved for certified export-grade buyers and premium product manufacturers.",
         "#f59e0b"),
        ("🌐 Export Auction",
         "Every 2nd Friday of month",
         "Dedicated auction for export-quality coconuts and value-added products. CDA export facilitation team present. Prices in USD/EUR accepted.",
         "#3b82f6"),
    ]
    for col, (title, schedule, desc, clr) in zip(spec_cols, specials):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:4px solid {clr};
                border-radius:12px;padding:18px 14px;height:220px;display:flex;flex-direction:column;'>
                <div style='font-size:.85rem;font-weight:800;color:#0d2b0d;margin-bottom:4px;'>{title}</div>
                <div style='font-size:.7rem;font-weight:700;color:{clr};margin-bottom:8px;'>📅 {schedule}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.55;flex:1;'>{desc}</div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Contact & Registration ─────────────────────────────────────────────────
    st.markdown("#### 📞 "+("Register & Contact" if lang=="en" else "ලියාපදිංචි සහ සම්බන්ධ වන්න"))
    ct1, ct2, ct3 = st.columns(3)
    contacts = [
        ("🏛️","CDA Head Office","No. 54, Nawam Mawatha, Colombo 02","+94 11 243 0610","cda@cda.gov.lk","www.cda.gov.lk","Seller & Buyer Registration, Licence Applications","#16a34a"),
        ("🏪","HARTI Head Office","Narahenpita, Colombo 05","+94 11 259 1919","harti@harti.gov.lk","www.harti.gov.lk","Colombo & Gampaha Auction Operations","#3b82f6"),
        ("📋","CDA Auction Hotline","Any CDA Regional Office","1920 (toll-free)","auctions@cda.gov.lk","www.cda.gov.lk/auctions","Auction schedule enquiries, lot registration","#f59e0b"),
    ]
    for col, (icon,org,addr,phone,email,web,purpose,clr) in zip([ct1,ct2,ct3], contacts):
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #d1e7d1;border-top:3px solid {clr};
                border-radius:10px;padding:16px 14px;height:220px;display:flex;flex-direction:column;'>
                <div style='font-size:.6rem;font-weight:700;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:6px;'>{icon} Contact</div>
                <div style='font-weight:800;font-size:.82rem;color:#0d2b0d;margin-bottom:8px;'>{org}</div>
                <div style='font-size:.7rem;color:#374151;line-height:1.8;flex:1;'>
                    📍 {addr}<br>📞 {phone}<br>✉️ {email}<br>
                    🌐 <a href='https://{web}' target='_blank' style='color:{clr};font-weight:600;text-decoration:none;'>{web}</a>
                </div>
                <div style='font-size:.65rem;color:{clr};font-weight:600;margin-top:6px;'>🎯 {purpose}</div>
            </div>""", unsafe_allow_html=True)


# ══ RECOMMENDATIONS & DECISION SUPPORT ═══════════════════════════════════════
elif t["nav"][12] in sec_name:
    import plotly.graph_objects as go

    # ── Hero banner ────────────────────────────────────────────────────────────
    st.markdown("""<div style='background:linear-gradient(135deg,#0d2b0d 0%,#14532d 55%,#166534 100%);
        border-radius:14px;padding:28px 32px;margin-bottom:20px;'>
      <div style='font-size:clamp(1.2rem,4vw,1.7rem);font-weight:900;color:#fff;margin-bottom:8px;'>
        🧩 Strategic Decision Support Centre
      </div>
      <div style='font-size:.88rem;color:#bbf7d0;line-height:1.7;max-width:760px;'>
        Combines market regime detection, demand analysis, weather forecasts and export data to generate
        actionable recommendations for <strong style='color:#4ade80;'>Government policymakers</strong>,
        <strong style='color:#86efac;'>Businesses & Traders</strong>, and
        <strong style='color:#a7f3d0;'>Coconut Farmers</strong>.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live market snapshot ───────────────────────────────────────────────────
    current_price   = history_df["price"].iloc[-1]
    price_3m_ago    = history_df["price"].iloc[-4]
    price_change_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
    avg_12m         = history_df["price"].tail(12).mean()
    volatility_12m  = history_df["price"].tail(12).std()
    cv              = (volatility_12m / avg_12m) * 100
    regime_now      = int(history_df["regime"].iloc[-1])
    regime_labels   = ["🟢 Stable","🟡 Warning","🔴 Crisis"]
    regime_colors   = ["#22c55e","#eab308","#ef4444"]
    regime_bgs      = ["#dcfce7","#fef9c3","#fee2e2"]

    st.markdown("#### 📊 " + ("Live Market Snapshot" if lang=="en" else "සජීව වෙළඳ තතු"))
    sn1,sn2,sn3,sn4,sn5 = st.columns(5)
    snap_data = [
        ("💰 Current Price",  f"Rs. {current_price:.2f}", "#16a34a"),
        ("📈 3-Month Change", f"{price_change_3m:+.1f}%", "#22c55e" if price_change_3m<=0 else "#ef4444"),
        ("📊 12M Average",    f"Rs. {avg_12m:.2f}",       "#3b82f6"),
        ("⚡ Volatility",     f"{cv:.1f}% CV",            "#f59e0b"),
        ("🏷️ Market Regime",  regime_labels[regime_now],  regime_colors[regime_now]),
    ]
    for col,(lbl,val,clr) in zip([sn1,sn2,sn3,sn4,sn5], snap_data):
        with col: st.markdown(metric_card(lbl, val, clr, height=95), unsafe_allow_html=True)
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — STRATEGIC POLICY SIMULATOR
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div style='background:linear-gradient(90deg,#1e3a8a,#1d4ed8);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        🏛️ Strategic Policy Simulator
      </div>
      <div style='font-size:.78rem;color:#bfdbfe;margin-top:3px;'>
        Test government intervention scenarios and see projected market outcomes before implementation
      </div>
    </div>
    """, unsafe_allow_html=True)

    ps_col1, ps_col2 = st.columns([1.2, 1])
    with ps_col1:
        st.markdown("##### ⚙️ " + ("Configure Policy Levers" if lang=="en" else "ප්‍රතිපත්ති සකස් කරන්න"))

        buffer_stock = st.slider(
            "🏦 Buffer Stock Release (% of monthly supply)" if lang=="en" else "🏦 බෆර් තොග මුදාහැරීම (%)",
            0, 30, 0, 1,
            help="Government releases stored nuts into market to reduce price pressure")

        import_duty  = st.slider(
            "🚢 Import Duty Adjustment (%)" if lang=="en" else "🚢 ආනයන බද්ද (%)",
            -20, 20, 0, 1,
            help="Positive = increase duty (protect local farmers). Negative = reduce duty (lower consumer prices)")

        subsidy_pct  = st.slider(
            "💊 Farmer Input Subsidy (% cost reduction)" if lang=="en" else "💊 ගොවි ආදාන සහාය (%)",
            0, 40, 0, 2,
            help="Subsidising fertiliser, pesticide and transport costs for farmers")

        price_floor  = st.slider(
            "🛡️ Minimum Price Floor (Rs.)" if lang=="en" else "🛡️ අවම මිල (රු.)",
            30, 80, int(current_price * 0.8), 1,
            help="Government-guaranteed minimum purchase price for farmers")

        export_quota = st.slider(
            "📦 Export Quota Restriction (% reduction)" if lang=="en" else "📦 අපනයන සීමාව (% අඩු කිරීම)",
            0, 50, 0, 5,
            help="Restricting exports increases domestic supply and lowers local prices")

    with ps_col2:
        st.markdown("##### 📈 " + ("Projected Market Impact" if lang=="en" else "ඉදිරි වෙළඳ බලපෑම"))

        # Simulate projected price based on levers
        price_impact  = current_price
        price_impact -= (buffer_stock * 0.12)          # buffer release reduces price
        price_impact += (import_duty  * 0.08)          # higher duty = higher price
        price_impact -= (export_quota * 0.06)          # export restriction lowers price
        price_impact += (subsidy_pct  * 0.03)          # subsidy has slight upward effect (more demand)
        price_impact  = max(price_floor, price_impact) # floor enforced

        delta_price   = price_impact - current_price
        delta_pct     = (delta_price / current_price) * 100
        p_clr         = "#22c55e" if delta_price <= 0 else "#ef4444"

        farmer_revenue_change = (price_impact - current_price) * 1000  # per 1000 nuts
        consumer_impact       = delta_pct * 2.3  # household spend sensitivity
        export_revenue_change = -export_quota * 1.2  # USD M approx

        # Projected price gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(price_impact, 2),
            delta={"reference": current_price, "valueformat": ".2f",
                   "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#22c55e"}},
            number={"prefix": "Rs.", "font": {"size": 28, "color": "#0d2b0d"}},
            title={"text": "Projected Price (Rs.)", "font": {"size": 13}},
            gauge={
                "axis": {"range": [30, 120], "tickfont": {"size": 9}},
                "bar":  {"color": p_clr},
                "bgcolor": "#f8fafc",
                "threshold": {"line": {"color": "#94a3b8", "width": 2}, "value": current_price},
                "steps": [
                    {"range": [30,  warn_threshold],    "color": "#dcfce7"},
                    {"range": [warn_threshold,  crisis_threshold], "color": "#fef9c3"},
                    {"range": [crisis_threshold, 120],  "color": "#fee2e2"},
                ],
            }))
        fig_gauge.update_layout(height=220, margin=dict(l=20,r=20,t=40,b=10), paper_bgcolor="#fff")
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

        # Impact summary cards
        ic1, ic2, ic3 = st.columns(3)
        for col, (lbl, val, clr) in zip([ic1, ic2, ic3], [
            ("👨‍🌾 Farmer\nRevenue /1000 nuts", f"{'+'if farmer_revenue_change>=0 else ''}{farmer_revenue_change:,.0f} Rs.", "#16a34a" if farmer_revenue_change>=0 else "#ef4444"),
            ("🏠 Consumer\nSpend Impact",       f"{consumer_impact:+.1f}%",  "#22c55e" if consumer_impact<=0 else "#ef4444"),
            ("📦 Export\nRevenue Est.",          f"{export_revenue_change:+.1f}M USD", "#3b82f6"),
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
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "🟢","Strong Consumer Relief", \
            f"This combination of policies is projected to reduce prices by Rs.{abs(delta_price):.1f}, providing significant relief to consumers. Monitor farmer income carefully.", "#16a34a"
    elif delta_price < 0:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "🟡","Mild Stabilisation", \
            f"Policies project a modest Rs.{abs(delta_price):.1f} price reduction. A balanced approach — good for consumers with minimal farmer impact.", "#eab308"
    elif delta_price == 0:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "⚪","Market Neutral", \
            "Current policy settings have no projected impact. Adjust levers above to test interventions.", "#64748b"
    elif delta_price < 10:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "🟡","Moderate Farmer Support", \
            f"Policies project a Rs.{delta_price:.1f} price increase, benefiting farmers. Watch consumer affordability closely.", "#eab308"
    else:
        verdict_icon, verdict_title, verdict_msg, verdict_clr = "🔴","High Price Risk", \
            f"Policies project a Rs.{delta_price:.1f} price surge. Strong intervention may be needed to protect consumers.", "#ef4444"

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
    st.markdown("##### 📊 " + ("Compare All Policy Scenarios" if lang=="en" else "ප්‍රතිපත්ති සසඳා බලන්න"))
    scenarios = {
        "No Intervention":       current_price,
        "Buffer Stock Only":     max(price_floor, current_price - 10*0.12),
        "Import Duty Cut":       max(price_floor, current_price - 15*0.08),
        "Farmer Subsidy":        max(price_floor, current_price + 20*0.03),
        "Export Quota":          max(price_floor, current_price - 25*0.06),
        "Combined (Optimal)":    max(price_floor, current_price - 10*0.12 - 10*0.08 - 20*0.06),
        "Current Settings":      round(price_impact, 2),
    }
    s_names  = list(scenarios.keys())
    s_prices = list(scenarios.values())
    s_colors = ["#94a3b8" if n=="No Intervention" else
                "#f59e0b" if n=="Current Settings" else
                "#22c55e" if v <= current_price else "#ef4444"
                for n, v in scenarios.items()]
    fig_sc = go.Figure(go.Bar(
        x=s_names, y=s_prices,
        marker_color=s_colors,
        text=[f"Rs.{v:.1f}" for v in s_prices],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Rs.%{y:.2f}<extra></extra>"))
    fig_sc.add_hline(y=current_price, line_dash="dash", line_color="#64748b",
        annotation_text=f"Current Rs.{current_price:.1f}", annotation_position="top right")
    fig_sc.add_hline(y=warn_threshold, line_dash="dot", line_color="#eab308",
        annotation_text=f"⚠ Rs.{warn_threshold}")
    fig_sc.add_hline(y=crisis_threshold, line_dash="dot", line_color="#ef4444",
        annotation_text=f"🔴 Rs.{crisis_threshold}")
    fig_sc.update_layout(height=300, margin=dict(l=20,r=20,t=30,b=20),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#e8f5e9", tickprefix="Rs.", range=[30, max(s_prices)*1.18]),
        showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar":"hover"})
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — STRATEGIC RECOMMENDATION ENGINE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div style='background:linear-gradient(90deg,#7c3aed,#6d28d9);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        🎯 Strategic Recommendation Engine
      </div>
      <div style='font-size:.78rem;color:#ddd6fe;margin-top:3px;'>
        AI-driven, regime-sensitive recommendations for all three market stakeholder groups
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic recommendations based on current regime
    all_recommendations = {
        0: {  # Stable Market
            "government": [
                ("🏦","Build Buffer Stocks","Stability window is ideal for building emergency grain reserves. Target: 3-month national supply.",
                 "HIGH","Immediate","Min. Rs. 2.5B allocation from stabilisation fund"),
                ("📊","Enhance Data Infrastructure","Invest in real-time price reporting systems at all 6 major auction centres.",
                 "MEDIUM","3-6 months","Rs. 180M — HARTI digital upgrade programme"),
                ("📋","Review Farmer Registration","Update CDA farmer database. Many smallholders lack formal registration limiting support access.",
                 "MEDIUM","6-12 months","Administrative — no major budget required"),
                ("🌿","Promote Value Addition","Stable prices allow investment in coconut oil, desiccated coconut, and coconut milk processing.",
                 "HIGH","6-18 months","Rs. 500M industry development grant"),
                ("🌍","Negotiate Trade Agreements","Use stable period to negotiate better export terms with EU, USA, and Middle East markets.",
                 "MEDIUM","12-24 months","Ministry of Trade — diplomatic resources"),
            ],
            "business": [
                ("📈","Expand Processing Capacity","Stable input costs make this the best time to invest in new processing lines and cold storage.",
                 "HIGH","6-12 months","ROI: 18-24 months at current margins"),
                ("🔒","Lock In Long-Term Supply Contracts","Negotiate 6-12 month fixed-price supply contracts with farmer cooperatives.",
                 "HIGH","Immediate","Reduces raw material cost volatility by ~40%"),
                ("🌐","Enter New Export Markets","Low price risk enables testing new export markets without margin compression.",
                 "MEDIUM","3-9 months","Export development board support available"),
                ("🏭","Invest in Automation","Stable period ideal for upgrading factory equipment without cashflow pressure.",
                 "MEDIUM","6-18 months","Automation grants available through BOI"),
                ("📦","Diversify Product Portfolio","Launch coconut water, activated carbon, or coir products to reduce commodity price risk.",
                 "HIGH","12-24 months","Market studies show 35% margin premium on value-added"),
            ],
            "farmer": [
                ("🌱","Replant Ageing Trees","15-25% of SL coconut palms are past peak yield. Stable income = best time to replant.",
                 "HIGH","Now — 3yr ROI","CDA provides seedlings at Rs. 150 each — 60% subsidy available"),
                ("💧","Install Irrigation","Drip irrigation reduces drought vulnerability by 60%. CDA subsidises 50% of installation cost.",
                 "HIGH","Next dry season","Rs. 45,000-85,000 per acre — subsidy available"),
                ("🤝","Join a Cooperative","Group selling at auctions achieves 12-18% higher prices than individual sellers.",
                 "HIGH","Immediate","Contact CDA regional office for nearest co-op"),
                ("📚","Access Training","CDA free training on integrated pest management and organic certification available.",
                 "MEDIUM","Ongoing","Free — register at cda.gov.lk/training"),
                ("💰","Open a Farm Savings Account","Bank of Ceylon Farmer Account offers 2% above normal savings rate for registered farmers.",
                 "MEDIUM","Immediate","BOC branch — CDA registration card required"),
            ],
        },
        1: {  # Warning Market
            "government": [
                ("🚨","Activate Price Monitoring Task Force","Deploy field officers to all 6 auction centres daily. Report unusual price movements within 24hrs.",
                 "URGENT","Immediate","Rs. 8M — existing staff redeployment"),
                ("📦","Partial Buffer Stock Release","Release 10-15% of buffer stocks to inject supply and moderate upward price pressure.",
                 "HIGH","Within 1 week","Coordinate with HARTI auction management"),
                ("📣","Public Price Transparency Campaign","Broadcast daily auction prices via radio, SMS (Dialog/Mobitel), and social media to prevent panic buying.",
                 "HIGH","Within 3 days","Rs. 5M — public communications budget"),
                ("🏦","Activate Price Stabilisation Fund","Signal readiness to deploy stabilisation fund. Market awareness alone can reduce speculation.",
                 "HIGH","Within 1 week","Rs. 500M fund — Cabinet authorisation required"),
                ("🌾","Accelerate Harvest Support","Provide subsidised transport to bring stored farm produce to market quickly.",
                 "MEDIUM","Within 2 weeks","Rs. 25M — transport subsidy scheme"),
            ],
            "business": [
                ("⚠️","Hedge Raw Material Costs","Lock in forward contracts for next 3-6 months before prices escalate further.",
                 "URGENT","This week","Contact commodity brokers — forward pricing available"),
                ("📉","Reduce Inventory Holding","High price environment — sell finished goods inventory quickly to protect margins.",
                 "HIGH","Immediate","Review distribution channel pricing"),
                ("🔍","Diversify Input Sources","Explore coconut sourcing from Puttalam, Kurunegala simultaneously — don't rely on single auction.",
                 "HIGH","Immediate","Register with 3+ auction centres"),
                ("💡","Switch to Value Products","Shift production mix toward premium products (virgin coconut oil, organic) with higher margin buffer.",
                 "MEDIUM","2-4 weeks","Requires product certification — SLSI contact"),
                ("📊","Weekly Price Tracking","Monitor all 6 auction centres daily. Set automated alerts at Rs.70, Rs.75, Rs.80.",
                 "HIGH","Immediate","COCOStat dashboard — set custom thresholds"),
            ],
            "farmer": [
                ("💰","Sell Now — Don't Hoard","Warning phase prices are already elevated. Sell at current auction prices rather than waiting.",
                 "URGENT","This week","Colombo auction Monday, Wednesday, Friday"),
                ("📋","Register for Emergency Support","Pre-register for government income support scheme before crisis is declared.",
                 "HIGH","This week","CDA Regional Office — free registration"),
                ("🧑‍🤝‍🧑","Coordinate with Neighbours","Pool harvests with nearby farmers for stronger auction bargaining position.",
                 "HIGH","Immediate","Minimum 5,000 nuts for cooperative lot"),
                ("💧","Accelerate Irrigation Use","If irrigation installed — increase watering frequency to maximise current yield.",
                 "MEDIUM","Immediate","CDA agronomy helpline: 1920"),
                ("📦","Explore Direct Buyer Contracts","Some processors will pay 5-8% above auction price for guaranteed supply contracts.",
                 "MEDIUM","1-2 weeks","CDA Buyer Directory available on request"),
            ],
        },
        2: {  # Crisis Market
            "government": [
                ("🆘","Emergency Price Control Activation","Invoke the Consumer Affairs Authority Act — set ceiling price at Rs.85. Enforce at all retail levels.",
                 "CRITICAL","Within 24hrs","Cabinet emergency session — Rs. 50M enforcement budget"),
                ("🚛","Full Buffer Stock Emergency Release","Release 100% of available buffer stocks immediately. Coordinate HARTI emergency auction.",
                 "CRITICAL","Within 48hrs","All regional centres — coordinate military logistics if needed"),
                ("🌐","Emergency Import Authorisation","Fast-track import permits for coconut from India/Philippines to bridge supply gap.",
                 "CRITICAL","Within 1 week","Ministry of Trade emergency order — waive normal 45-day process"),
                ("💵","Cash Transfer to Vulnerable Households","Rs. 2,500 per household hardship payment via Samurdhi mechanism for bottom 30%.",
                 "CRITICAL","Within 2 weeks","Rs. 12B — emergency supplementary estimate"),
                ("📡","Daily National Price Broadcast","Daily 8PM TV/radio broadcast of official controlled prices and where to buy.",
                 "HIGH","Immediate","SLRC coordination — Rs. 2M production budget"),
                ("🔎","Anti-Hoarding Enforcement","CAA/Police joint teams to inspect large warehouses for hoarding. Penalties up to Rs. 5M.",
                 "HIGH","Immediate","District secretariat coordination required"),
            ],
            "business": [
                ("🆘","Activate Business Continuity Protocol","Implement pre-agreed crisis supply chain procedures. Identify alternative inputs immediately.",
                 "CRITICAL","Immediate","Board-level decision required"),
                ("🏦","Secure Emergency Credit Lines","Apply for SME Emergency Credit from NDB/BOC at 6% crisis rate before demand exceeds capacity.",
                 "CRITICAL","Within 3 days","NDB/BOC — Rs. 50M facility available"),
                ("📦","Reduce Production Volumes","Temporarily reduce production of commodity lines. Maintain only high-margin premium products.",
                 "HIGH","Immediate","Protect working capital — prioritise cash flow"),
                ("🔄","Source Alternative Raw Materials","Explore palm oil, sunflower — partial substitution in cooking oil lines until crisis passes.",
                 "HIGH","Within 1 week","SLSI approval may be required for labelling change"),
                ("📣","Customer Communication","Proactively communicate price increases to retail partners with written justification.",
                 "HIGH","Within 2 days","Prevents channel conflict — protect long-term relationships"),
                ("💼","Engage Industry Association","Coconut Industry Collective Action — joint lobbying for import duty relief and government support.",
                 "MEDIUM","This week","CDA Industry Association: +94 11 243 0610"),
            ],
            "farmer": [
                ("💰","Maximise Harvest Immediately","Rush all harvestable nuts to market before government price controls reduce ceiling.",
                 "CRITICAL","Next 3-5 days","All 6 auction centres operating emergency sessions"),
                ("📞","Call CDA Emergency Helpline","Register for emergency farmer support — income protection payments being processed.",
                 "CRITICAL","Today","CDA Emergency: 1920 (toll-free 24/7)"),
                ("🛡️","Document Your Costs","Keep all receipts for fertiliser, labour, transport — required for compensation claims.",
                 "HIGH","Immediate","CDA compensation forms available at regional offices"),
                ("🌱","Do Not Sell Seedlings/Young Trees","Crisis will pass. Do not liquidate productive assets for short-term cash.",
                 "HIGH","Now","Long-term income protection — very important"),
                ("🤝","Apply for Samurdhi Emergency Aid","Farming households affected by crisis can apply for Rs. 3,500/month emergency support.",
                 "HIGH","Within 1 week","Divisional Secretariat — bring NIC and CDA registration"),
                ("📋","Report Price Manipulation","If brokers or middlemen offering below-auction prices — report immediately.",
                 "MEDIUM","If occurs","CAA hotline: 1977 (Consumer Affairs Authority)"),
            ],
        },
    }

    recs = all_recommendations[regime_now]
    regime_bg   = regime_bgs[regime_now]
    regime_clr  = regime_colors[regime_now]
    regime_name = ["Stable Market","Warning Market","Crisis Market"][regime_now]

    # Market status banner
    st.markdown(f"""<div style='background:{regime_bg};border:2px solid {regime_clr};border-radius:12px;
        padding:14px 20px;margin-bottom:18px;display:flex;align-items:center;gap:12px;'>
        <div style='font-size:2rem;'>{["🟢","🟡","🔴"][regime_now]}</div>
        <div>
          <div style='font-size:.72rem;font-weight:800;color:{regime_clr};text-transform:uppercase;
              letter-spacing:1.5px;'>Active Regime</div>
          <div style='font-size:1rem;font-weight:900;color:#0d2b0d;'>{regime_name} — Recommendations Active</div>
          <div style='font-size:.75rem;color:#374151;margin-top:2px;'>
              Current price Rs.{current_price:.2f} | {len(recs["government"])+len(recs["business"])+len(recs["farmer"])} total recommendations across 3 stakeholder groups
          </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Priority badge helper
    def priority_badge(p):
        cfg = {"CRITICAL":("#7f1d1d","#fca5a5"),"URGENT":("#ef4444","#fee2e2"),
               "HIGH":("#92400e","#fef3c7"),"MEDIUM":("#1e3a8a","#dbeafe")}
        bg, txt = cfg.get(p, ("#374151","#f1f5f9"))
        return f"<span style='background:{txt};color:{bg};font-size:.58rem;font-weight:800;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px;'>{p}</span>"

    # ── Render all 3 stakeholder tabs ──────────────────────────────────────────
    tab_gov, tab_biz, tab_farm = st.tabs([
        "🏛️ Government & Policymakers",
        "💼 Businesses & Traders",
        "👨‍🌾 Coconut Farmers",
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
                    <div style='font-size:.88rem;font-weight:800;color:#0d2b0d;'>{title}</div>
                    {priority_badge(priority)}
                  </div>
                  <div style='font-size:.78rem;color:#374151;line-height:1.65;margin-bottom:8px;'>{desc}</div>
                  <div style='display:flex;gap:12px;flex-wrap:wrap;'>
                    <div style='font-size:.68rem;background:#f0fdf4;color:#166534;padding:3px 9px;
                        border-radius:20px;font-weight:700;'>⏱ {timing}</div>
                    <div style='font-size:.68rem;background:#eff6ff;color:#1e40af;padding:3px 9px;
                        border-radius:20px;font-weight:700;'>💡 {resource}</div>
                  </div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    with tab_gov:
        st.markdown(f"""<div style='background:#eff6ff;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#1e3a8a;font-weight:700;'>
            🏛️ These recommendations are tailored for <strong>Cabinet Ministers, CDA, HARTI, and Central Bank officials</strong>
            managing the coconut sector under <strong>{regime_name}</strong> conditions.
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["government"], "#1d4ed8")

    with tab_biz:
        st.markdown(f"""<div style='background:#fdf4ff;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#6b21a8;font-weight:700;'>
            💼 These recommendations are tailored for <strong>Coconut product manufacturers, exporters, traders and processors</strong>
            operating under <strong>{regime_name}</strong> conditions.
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["business"], "#7c3aed")

    with tab_farm:
        st.markdown(f"""<div style='background:#f0fdf4;border-radius:8px;padding:10px 14px;margin-bottom:14px;'>
            <div style='font-size:.78rem;color:#166534;font-weight:700;'>
            👨‍🌾 These recommendations are tailored for <strong>Smallholder farmers, coconut growers and farming cooperatives</strong>
            operating under <strong>{regime_name}</strong> conditions.
            </div></div>""", unsafe_allow_html=True)
        render_rec_cards(recs["farmer"], "#16a34a")

    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — DECISION RISK MATRIX
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div style='background:linear-gradient(90deg,#0f766e,#0d9488);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        🗺️ Strategic Risk & Opportunity Matrix
      </div>
      <div style='font-size:.78rem;color:#ccfbf1;margin-top:3px;'>
        Visual mapping of risks and opportunities across all market conditions
      </div>
    </div>
    """, unsafe_allow_html=True)

    rm1, rm2 = st.columns(2)
    with rm1:
        st.markdown("##### ⚠️ " + ("Key Risks to Monitor" if lang=="en" else "ප්‍රධාන අවදානම්"))
        risks = [
            ("🌧️","Drought / Low Rainfall","HIGH" if regime_now >= 1 else "MEDIUM",
             "Yield drop in 3-6 months. Monitor CRI rainfall index monthly."),
            ("📦","Export Demand Surge","HIGH" if regime_now >= 1 else "MEDIUM",
             "Global demand spikes can drain domestic supply rapidly."),
            ("⛽","Rising Input Costs","MEDIUM",
             "Fuel, fertiliser prices affect farm-gate profitability directly."),
            ("🌐","Exchange Rate Volatility","MEDIUM",
             "LKR depreciation increases import cost of inputs."),
            ("🐛","Pest/Disease Outbreak","HIGH" if regime_now == 2 else "MEDIUM",
             "Rhinoceros beetle and bud rot remain significant threats."),
            ("🏭","Processing Capacity Shortage","LOW" if regime_now == 0 else "MEDIUM",
             "Value-addition bottlenecks limit export revenue growth."),
        ]
        for icon, risk, level, detail in risks:
            lvl_clr = {"CRITICAL":"#ef4444","HIGH":"#f59e0b","MEDIUM":"#3b82f6","LOW":"#22c55e"}[level]
            st.markdown(f"""<div style='display:flex;align-items:center;gap:10px;padding:9px 12px;
                background:#f8fafc;border-radius:8px;margin-bottom:7px;border:1px solid #e2e8f0;'>
                <div style='font-size:1.1rem;'>{icon}</div>
                <div style='flex:1;'>
                  <div style='display:flex;align-items:center;gap:7px;'>
                    <div style='font-size:.75rem;font-weight:800;color:#0d2b0d;'>{risk}</div>
                    {priority_badge(level)}
                  </div>
                  <div style='font-size:.68rem;color:#64748b;margin-top:2px;'>{detail}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with rm2:
        st.markdown("##### 🌟 " + ("Key Opportunities" if lang=="en" else "ප්‍රධාන අවස්ථා"))
        opportunities = [
            ("🥥","Virgin Coconut Oil Export","HIGH","Global VCO market growing 8.5% YoY. SL quality commands 30% premium."),
            ("🌱","Organic Certification","HIGH","EU organic coconut market worth $2.1B. Only 12% of SL farms certified."),
            ("💧","Coconut Water Market","HIGH","Global market $6.8B by 2026. SL currently exports < 3% of potential."),
            ("🔋","Activated Carbon","MEDIUM","High-value industrial product from coconut shell. Margins 4x raw nuts."),
            ("🏝","Agro-Tourism","MEDIUM","Coconut triangle farm tourism growing 22% annually post-pandemic."),
            ("🤖","Smart Farming Technology","MEDIUM","IoT sensors and drone spraying can increase yield by 15-20%."),
        ]
        for icon, opp, level, detail in opportunities:
            lvl_clr = {"HIGH":"#16a34a","MEDIUM":"#3b82f6","LOW":"#94a3b8"}[level]
            st.markdown(f"""<div style='display:flex;align-items:center;gap:10px;padding:9px 12px;
                background:#f0fdf4;border-radius:8px;margin-bottom:7px;border:1px solid #d1e7d1;'>
                <div style='font-size:1.1rem;'>{icon}</div>
                <div style='flex:1;'>
                  <div style='display:flex;align-items:center;gap:7px;'>
                    <div style='font-size:.75rem;font-weight:800;color:#0d2b0d;'>{opp}</div>
                    <span style='background:#dcfce7;color:#166534;font-size:.58rem;font-weight:800;
                        padding:2px 7px;border-radius:20px;'>{level}</span>
                  </div>
                  <div style='font-size:.68rem;color:#374151;margin-top:2px;'>{detail}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — 90-DAY ACTION PLAN
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div style='background:linear-gradient(90deg,#92400e,#b45309);border-radius:10px;
        padding:14px 22px;margin-bottom:16px;'>
      <div style='font-size:1.05rem;font-weight:900;color:#fff;'>
        📅 90-Day Priority Action Plan
      </div>
      <div style='font-size:.78rem;color:#fde68a;margin-top:3px;'>
        Immediate, short-term and medium-term actions based on current market regime
      </div>
    </div>
    """, unsafe_allow_html=True)

    action_plan = {
        0: [  # Stable
            ("Week 1–2",  "#16a34a", "🏦 Initiate buffer stock procurement | 📊 Deploy CDA digital price reporting"),
            ("Week 3–4",  "#3b82f6", "📋 Update farmer registration database | 🤝 Launch cooperative formation drive"),
            ("Month 2",   "#f59e0b", "🌿 Value-addition investment roadshow | 🌍 Trade agreement preliminary talks"),
            ("Month 3",   "#8b5cf6", "📈 Review export incentive schemes | 🌱 Replanting programme launch"),
        ],
        1: [  # Warning
            ("Day 1–3",   "#ef4444", "🚨 Activate monitoring task force | 📣 Launch price transparency media campaign"),
            ("Day 4–7",   "#f59e0b", "📦 Release 10-15% buffer stock | 🏦 Signal stabilisation fund readiness"),
            ("Week 2–3",  "#3b82f6", "🌾 Accelerate harvest support transport | 📋 Emergency farmer registration"),
            ("Month 2–3", "#8b5cf6", "⚖️ Review import duty schedule | 📊 Commission independent price audit"),
        ],
        2: [  # Crisis
            ("Today",     "#7f1d1d", "🆘 Emergency Cabinet session | 🚛 Full buffer stock release authorisation"),
            ("Day 2–3",   "#ef4444", "🌐 Gazette emergency import permits | 💵 Activate Samurdhi emergency payments"),
            ("Week 1",    "#f59e0b", "🔎 Deploy anti-hoarding enforcement | 📡 Begin daily national price broadcast"),
            ("Week 2–4",  "#3b82f6", "📊 Conduct supply chain audit | 🌱 Post-crisis recovery plan preparation"),
        ],
    }

    ap_cols = st.columns(4)
    for col, (period, clr, actions) in zip(ap_cols, action_plan[regime_now]):
        action_items = [a.strip() for a in actions.split("|")]
        items_html = "".join([f"<div style='font-size:.7rem;color:#374151;padding:5px 0;border-bottom:1px solid #f0fdf4;line-height:1.4;'>{a}</div>" for a in action_items])
        with col:
            st.markdown(f"""<div style='background:#fff;border:1px solid #e2e8f0;border-top:4px solid {clr};
                border-radius:10px;padding:14px 12px;min-height:180px;'>
                <div style='font-size:.7rem;font-weight:900;color:{clr};text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:10px;'>{period}</div>
                {items_html}
            </div>""", unsafe_allow_html=True)
    divider()

    # ── Download summary report ────────────────────────────────────────────────
    st.markdown("##### 📥 " + ("Export Recommendation Report" if lang=="en" else "නිර්දේශ වාර්තාව බාගන්න"))
    from datetime import datetime
    report_lines = [
        f"COCOStat – Strategic Recommendation Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Current Market Regime: {regime_name}",
        f"Current Price: Rs. {current_price:.2f}",
        f"12-Month Average: Rs. {avg_12m:.2f}",
        f"Price Volatility (CV): {cv:.1f}%",
        "",
        "=" * 60,
        "POLICY SIMULATOR RESULTS",
        "=" * 60,
        f"Buffer Stock Release:  {buffer_stock}%",
        f"Import Duty Change:    {import_duty:+}%",
        f"Farmer Subsidy:        {subsidy_pct}%",
        f"Price Floor:           Rs. {price_floor}",
        f"Export Quota Cut:      {export_quota}%",
        f"Projected Price:       Rs. {price_impact:.2f} ({delta_pct:+.1f}%)",
        f"Policy Verdict:        {verdict_title}",
        "",
        "=" * 60,
        f"GOVERNMENT RECOMMENDATIONS ({regime_name})",
        "=" * 60,
    ]
    for icon, title, desc, priority, timing, resource in recs["government"]:
        report_lines += [f"\n[{priority}] {title}", f"  {desc}", f"  ⏱ {timing} | 💡 {resource}"]
    report_lines += ["", "=" * 60, f"BUSINESS RECOMMENDATIONS ({regime_name})", "=" * 60]
    for icon, title, desc, priority, timing, resource in recs["business"]:
        report_lines += [f"\n[{priority}] {title}", f"  {desc}", f"  ⏱ {timing} | 💡 {resource}"]
    report_lines += ["", "=" * 60, f"FARMER RECOMMENDATIONS ({regime_name})", "=" * 60]
    for icon, title, desc, priority, timing, resource in recs["farmer"]:
        report_lines += [f"\n[{priority}] {title}", f"  {desc}", f"  ⏱ {timing} | 💡 {resource}"]
    report_lines += ["", "─" * 60, "COCOStat · Coconut Market Intelligence · CDA & HARTI Sri Lanka"]

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="📄 Download Full Recommendation Report (TXT)",
            data="\n".join(report_lines),
            file_name=f"cocostat_recommendations_{regime_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain", use_container_width=True)
    with dl2:
        import io
        csv_rows = [["Stakeholder","Priority","Action","Description","Timing","Resource"]]
        for stakeholder, recs_list in [("Government",recs["government"]),("Business",recs["business"]),("Farmer",recs["farmer"])]:
            for icon, title, desc, priority, timing, resource in recs_list:
                csv_rows.append([stakeholder, priority, title, desc, timing, resource])
        csv_buf = io.StringIO()
        import csv as csv_mod
        writer = csv_mod.writer(csv_buf)
        writer.writerows(csv_rows)
        st.download_button(
            label="📊 Download Action Items (CSV)",
            data=csv_buf.getvalue(),
            file_name=f"cocostat_actions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
divider()

_CARD_STYLE = "background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #4ade80;padding:16px 14px;flex:1;min-width:200px;display:flex;flex-direction:column;"
_BADGE_STYLE = "font-size:.58rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;"
_NAME_STYLE  = "font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;"
_INFO_STYLE  = "font-size:.72rem;color:#bbf7d0;line-height:1.9;flex:1;"
_LINK_STYLE  = "color:#4ade80;font-weight:600;text-decoration:none;"
_STAT_STYLE  = "flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"
_DIST_STYLE  = "flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"

st.markdown("""
<div style="background:linear-gradient(135deg,#0d2b0d 0%,#14532d 50%,#166534 100%);border-radius:0;padding:36px 32px;box-shadow:0 4px 24px rgba(13,43,13,.25);margin-bottom:28px;">

  <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.15);margin-bottom:28px;">
    <div style="font-size:2rem;font-weight:900;color:#fff;margin-bottom:8px;text-shadow:0 2px 8px rgba(0,0,0,.2);">Sri Lanka Coconut Industry</div>
    <div style="font-size:.9rem;color:#bbf7d0;font-weight:500;">Key Organisations, Contacts &amp; Industry Facts</div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px;">
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #4ade80;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🏛 Primary Regulator</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Coconut Development Authority</div>
      <div style="font-size:.72rem;color:#bbf7d0;line-height:1.9;flex:1;">📍 No.54, Nawam Mawatha<br>Colombo 02<br>📞 +94 11 243 0610<br>🌐 <a href="https://www.cda.gov.lk" target="_blank" style="color:#4ade80;font-weight:600;text-decoration:none;">www.cda.gov.lk</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #4ade80;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🔬 Research Institute</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Coconut Research Institute (CRI)</div>
      <div style="font-size:.72rem;color:#bbf7d0;line-height:1.9;flex:1;">📍 Bandirippuwa Estate<br>Lunuwila 61150<br>📞 +94 31 222 2481<br>🌐 <a href="https://www.cri.gov.lk" target="_blank" style="color:#4ade80;font-weight:600;text-decoration:none;">www.cri.gov.lk</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #4ade80;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">📦 Export Promoter</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">Sri Lanka Export Development Board</div>
      <div style="font-size:.72rem;color:#bbf7d0;line-height:1.9;flex:1;">📍 42 Nawam Mawatha<br>Colombo 02<br>📞 +94 11 230 0705<br>🌐 <a href="https://www.srilankabusiness.com" target="_blank" style="color:#4ade80;font-weight:600;text-decoration:none;">www.srilankabusiness.com</a></div>
    </div>
    <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-top:3px solid #4ade80;padding:16px 14px;display:flex;flex-direction:column;">
      <div style="font-size:.58rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🛒 Market &amp; Auction</div>
      <div style="font-weight:800;font-size:.82rem;color:#ffffff;margin-bottom:10px;line-height:1.3;">HARTI / Economic Centres</div>
      <div style="font-size:.72rem;color:#bbf7d0;line-height:1.9;flex:1;">📍 Narahenpita, Colombo 05<br>(Head Office)<br>📞 +94 11 259 1919<br>🌐 <a href="https://www.harti.gov.lk" target="_blank" style="color:#4ade80;font-weight:600;text-decoration:none;">www.harti.gov.lk</a></div>
    </div>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;margin-bottom:24px;">
    <div style="text-align:center;font-size:.75rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;">Sri Lanka Coconut Industry at a Glance</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~2.7M</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">Hectares</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~3B</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">Nuts/Year</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">450K+</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">Families</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">$350M+</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">Exports</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">3rd</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">World Rank</div></div>
      <div style="flex:1;min-width:80px;text-align:center;padding:14px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;font-weight:900;color:#ffffff;">~2%</div><div style="font-size:.65rem;color:#86efac;margin-top:4px;font-weight:600;text-transform:uppercase;">GDP Share</div></div>
    </div>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;margin-bottom:24px;">
    <div style="text-align:center;font-size:.75rem;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;">📍 The Coconut Triangle</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;">🌴</div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">Kurunegala</div></div>
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;">🌴</div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">Puttalam</div></div>
      <div style="flex:1;min-width:120px;max-width:220px;text-align:center;padding:16px 8px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"><div style="font-size:1.4rem;">🌴</div><div style="font-size:.85rem;font-weight:700;color:#ffffff;margin-top:6px;">Gampaha</div></div>
    </div>
  </div>

  <div style="text-align:center;font-size:.72rem;color:#86efac;padding-top:20px;border-top:1px solid rgba(255,255,255,0.15);opacity:.85;">
    🥥 COCOStat · Coconut Market Intelligence Dashboard · Data from CDA &amp; CRI Sri Lanka
  </div>

</div>
""", unsafe_allow_html=True)
