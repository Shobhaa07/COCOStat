"""
COCOStat JSON Data Extractor
============================
Run this script in the same directory as your Jupyter notebook
(COCOStat_Analysis__1_.ipynb) and the source dataset (Dataset.xlsx).

It re-executes the notebook's data loading and analysis logic, then
exports ALL required data for the COCOStat Streamlit app into a single
file:  cocostat_data.json

Usage:
    pip install pandas openpyxl statsmodels scikit-learn scipy numpy
    python generate_cocostat_json.py

The script expects Dataset.xlsx (the original data source used in the
notebook) to be present in the working directory.
"""

import warnings
warnings.filterwarnings("ignore")

import json
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DATA_PATH   = "Dataset.xlsx"       # source workbook used by the notebook
OUTPUT_FILE = "cocostat_data.json" # output JSON consumed by the Streamlit app

# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_sheet(target):
    xls = pd.ExcelFile(DATA_PATH)
    for sheet in xls.sheet_names:
        if target.lower() in sheet.lower():
            return sheet
    raise ValueError(f"No matching sheet for '{target}'. Available: {xls.sheet_names}")


def _load(sheet_key, cols):
    sheet = get_sheet(sheet_key)
    df    = pd.read_excel(DATA_PATH, sheet_name=sheet, header=0)
    df    = df.iloc[:, :len(cols)]
    df.columns = cols
    df    = df[pd.to_numeric(df["Year"], errors="coerce").notna()].copy()
    df["Year"] = df["Year"].astype(int)
    return df


def safe(val):
    """Convert numpy scalars / NaN to plain Python types for JSON."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return None if np.isnan(val) else float(val)
    if isinstance(val, float):
        return None if (val != val) else val
    return val


def df_to_records(df):
    """Convert a DataFrame to a list of dicts with JSON-safe values."""
    records = []
    for row in df.to_dict(orient="records"):
        records.append({k: safe(v) for k, v in row.items()})
    return records

# ─────────────────────────────────────────────────────────────────────────────
# 3. LOAD RAW SHEETS
# ─────────────────────────────────────────────────────────────────────────────
print("Loading sheets from", DATA_PATH, "…")

df_weekly = _load("weekly", [
    "Year", "Month", "Week_Date", "Offered_Nuts", "Sold_Nuts",
    "Avg_Price", "Palm_Oil_Price", "Inflation", "CSE"
])
df_prod   = _load("production", [
    "Year", "Total_Production", "Copra", "VCO", "DC",
    "Coconut_Milk", "CMP", "Fresh_Nuts_Local", "Seed_Coconut"
])
df_export = _load("export_products", [
    "Year", "DC_MT", "CocoOil_MT", "CMP_MT", "Coir_MT",
    "FreshNuts_1000", "Copra_MT", "CocoMilk_MT",
    "CocoCream_MT", "Total_Export_MT"
])
df_global = _load("global_benchmarks", [
    "Year", "World_CocoOil_USD", "SL_Yield", "Land_Ha",
    "Land_Ac", "SL_Avg_Price", "YoY_Price_Change"
])
df_weather = _load("weather", [
    "Year", "Month", "Rainfall", "Temperature",
    "Yield_Index", "Drought_Flag", "Lag3_Rain"
])
df_gcmp = _load("global_comparison", [
    "Year", "SL", "Indonesia", "Philippines",
    "India", "Vietnam", "SL_vs_World_Avg"
])
df_dest = _load("destinations", [
    "Year", "USA", "UK", "Germany", "Australia",
    "Netherlands", "Japan", "Canada", "UAE", "Others", "Total"
])

# Fix weekly dates
df_weekly["Date"] = pd.to_datetime(df_weekly["Week_Date"], errors="coerce")
df_weekly = df_weekly.sort_values("Date").reset_index(drop=True)
df_weekly["Sell_Through_Rate"] = df_weekly["Sold_Nuts"] / df_weekly["Offered_Nuts"]

print("  Sheets loaded. Weekly obs:", len(df_weekly))

# ─────────────────────────────────────────────────────────────────────────────
# 4. MARKET REGIME CLASSIFICATION  (GMM K=3, matching notebook Cell 10)
# ─────────────────────────────────────────────────────────────────────────────
print("Running GMM regime classification …")

clust_df = df_weekly[["Date", "Year", "Month", "Avg_Price",
                       "Sell_Through_Rate", "Palm_Oil_Price", "Inflation"]].copy()
clust_df["Sell_Through_Rate"] = clust_df["Sell_Through_Rate"].clip(upper=1.0)

# Feature engineering
clust_df["Price_Volatility"]  = (clust_df["Avg_Price"]
                                  .rolling(4, min_periods=1).std()
                                  .fillna(clust_df["Avg_Price"].std()))
clust_df["Price_MoM"]         = clust_df["Avg_Price"].pct_change(4).fillna(0)
clust_df["Palm_Normalised"]   = clust_df["Palm_Oil_Price"] / 1000
clust_df["Inflation_Clean"]   = clust_df["Inflation"].fillna(clust_df["Inflation"].median())

features = ["Avg_Price", "Price_Volatility", "Price_MoM",
            "Sell_Through_Rate", "Inflation_Clean"]
X = clust_df[features].fillna(0).values
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

# Fit GMM with same seed as notebook
gmm = GaussianMixture(n_components=3, covariance_type="full",
                      random_state=42, n_init=5)
gmm.fit(Xs)
labels = gmm.predict(Xs)

# Map cluster indices to Stable / Warning / Crisis by mean price
cluster_means = {i: X[labels == i, 0].mean() for i in range(3)}
sorted_clusters = sorted(cluster_means, key=lambda x: cluster_means[x])
label_map = {sorted_clusters[0]: "Stable",
             sorted_clusters[1]: "Warning",
             sorted_clusters[2]: "Crisis"}
clust_df["Regime"] = [label_map[l] for l in labels]

# Monthly mode regime
clust_df["Month_Date"] = clust_df["Date"].dt.to_period("M").dt.start_time
monthly_regimes = (clust_df.groupby("Month_Date")["Regime"]
                   .agg(lambda x: x.mode()[0])
                   .reset_index()
                   .rename(columns={"Month_Date": "Date", "Regime": "Monthly_Regime"}))

print("  Regimes assigned.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. MONTHLY PRICE HISTORY  (matching app's load_data → history_df)
# ─────────────────────────────────────────────────────────────────────────────
print("Building monthly price history …")

month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
             "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

df_weekly["Date"] = pd.to_datetime(df_weekly["Week_Date"], errors="coerce")
df_weekly["Month_Num"] = df_weekly["Month"].map(month_map)

monthly_agg = df_weekly.groupby(["Year", "Month_Num"]).agg(
    Avg_Price=("Avg_Price", "mean"),
    Offered_Nuts=("Offered_Nuts", "sum"),
    Sold_Nuts=("Sold_Nuts", "sum"),
    Palm_Oil_Price=("Palm_Oil_Price", "mean"),
    Inflation=("Inflation", "mean")
).reset_index()

monthly_agg["date"] = pd.to_datetime(
    monthly_agg["Year"].astype(str) + "-" +
    monthly_agg["Month_Num"].astype(str).str.zfill(2) + "-01"
)
monthly_agg = monthly_agg.sort_values("date").reset_index(drop=True)

# Merge regime
monthly_agg = monthly_agg.merge(monthly_regimes, left_on="date", right_on="Date", how="left")

# Price per nut (Rs.)
monthly_agg["price"] = (monthly_agg["Avg_Price"] / 1000).round(2)
monthly_agg["price"] = monthly_agg["price"].where(monthly_agg["price"] > 0)

# Regime numeric (0=Stable,1=Warning,2=Crisis) – matches app logic
regime_num = {"Stable": 0, "Warning": 1, "Crisis": 2}
monthly_agg["regime"] = monthly_agg["Monthly_Regime"].map(regime_num).fillna(0).astype(int)

# Calculate YoY change
monthly_agg["year"]  = monthly_agg["Year"]
monthly_agg["month"] = monthly_agg["Month_Num"]
monthly_agg["YoY_Change"] = monthly_agg["price"].pct_change(12).mul(100).round(2)

history_records = []
for _, row in monthly_agg.iterrows():
    history_records.append({
        "date":   row["date"].strftime("%Y-%m-%d"),
        "price":  safe(row["price"]),
        "regime": int(row["regime"]),
        "year":   int(row["year"]),
        "month":  int(row["month"]),
    })

print(f"  Monthly history: {len(history_records)} records.")

# ─────────────────────────────────────────────────────────────────────────────
# 6. WEEKLY AUCTION DATA  (app's load_data → weekly_df)
# ─────────────────────────────────────────────────────────────────────────────
print("Building weekly data …")

weekly_records = []
for _, row in df_weekly.iterrows():
    if pd.isna(row["Date"]):
        continue
    weekly_records.append({
        "date":  row["Date"].strftime("%Y-%m-%d"),
        "price": safe(row["Avg_Price"] / 1000),
    })

print(f"  Weekly records: {len(weekly_records)}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. PRICE FORECAST  (matching notebook Cell 22 output / app's load_data → forecast_df)
# ─────────────────────────────────────────────────────────────────────────────
print("Building price forecast records …")

# These values come directly from the notebook Cell 22 output
# (DETAILED 12-MONTH PRICE FORECAST table).
forecast_raw = [
    ("2025-12-01", 123.01, 128.01, 118.01),
    ("2026-01-01", 132.89, 137.89, 127.89),
    ("2026-02-01", 132.84, 137.84, 127.84),
    ("2026-03-01", 128.17, 133.17, 123.17),
    ("2026-04-01", 137.23, 142.23, 132.23),
    ("2026-05-01", 132.75, 137.75, 127.75),
    ("2026-06-01", 131.92, 136.92, 126.92),
    ("2026-07-01", 140.33, 145.33, 135.33),
    ("2026-08-01", 133.36, 138.36, 128.36),
    ("2026-09-01", 138.84, 143.84, 133.84),
    ("2026-10-01", 141.53, 146.53, 136.53),
    ("2026-11-01", 135.07, 140.07, 130.07),
    ("2026-12-01", 142.96, 147.96, 137.96),
]
forecast_records = [
    {"date": d, "price": p, "upper": u, "lower": l}
    for d, p, u, l in forecast_raw
]

# Alternatively, re-run the SARIMA model if the above should be live:
try:
    price_series_weekly = (
        df_weekly
        .assign(Date=pd.to_datetime(df_weekly["Week_Date"], errors="coerce"))
        .dropna(subset=["Date"])
        .sort_values("Date")
        .drop_duplicates(subset="Date")
        .set_index("Date")["Avg_Price"]
    )
    train_series = price_series_weekly[price_series_weekly.index <= "2024-12-31"]

    # Exogenous vars (monthly → weekly forward-fill)
    monthly_exog = monthly_agg.set_index("date")[["Palm_Oil_Price", "Inflation"]].copy()
    monthly_exog.index = pd.to_datetime(monthly_exog.index)
    exog_weekly = monthly_exog.reindex(price_series_weekly.index).ffill().bfill()
    train_exog  = exog_weekly[exog_weekly.index <= "2024-12-31"]

    model = sm.tsa.SARIMAX(
        train_series,
        order=(1, 1, 2),
        seasonal_order=(1, 1, 1, 12),
        exog=train_exog,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fit = model.fit(disp=False, maxiter=200)

    # Build 52-week exog for forecast (use last known values forward-filled)
    last_exog_val = exog_weekly.iloc[-1].values
    fc_exog = pd.DataFrame(
        [last_exog_val] * 56,
        index=pd.date_range(start=price_series_weekly.index[-1] + pd.Timedelta(weeks=1), periods=56, freq="W"),
        columns=["Palm_Oil_Price", "Inflation"]
    )
    fc = fit.get_forecast(steps=56, exog=fc_exog)
    fc_mean = fc.predicted_mean
    fc_ci   = fc.conf_int(alpha=0.05)

    fcast_tbl = pd.DataFrame({
        "date":  fc_mean.index.strftime("%Y-%m-%d"),
        "price": (fc_mean.values / 1000).round(2),
        "upper": ((fc_mean.values + 5000) / 1000).round(2),
        "lower": ((fc_mean.values - 5000) / 1000).round(2),
    })

    # Aggregate to monthly (mean per calendar month)
    fcast_tbl["month_key"] = fc_mean.index.to_period("M").astype(str)
    monthly_fc = fcast_tbl.groupby("month_key").agg(
        price=("price", "mean"),
        upper=("upper", "mean"),
        lower=("lower", "mean"),
    ).reset_index()
    monthly_fc["date"] = pd.to_datetime(monthly_fc["month_key"] + "-01").dt.strftime("%Y-%m-%d")

    forecast_records = [
        {"date": row["date"], "price": round(row["price"], 2),
         "upper": round(row["upper"], 2), "lower": round(row["lower"], 2)}
        for _, row in monthly_fc.iterrows()
    ]
    print(f"  SARIMA forecast recomputed: {len(forecast_records)} months.")
except Exception as e:
    print(f"  SARIMA recompute skipped ({e}). Using notebook output values.")

# ─────────────────────────────────────────────────────────────────────────────
# 8. WEATHER DATA  (app's load_weather_data → weather_df)
# ─────────────────────────────────────────────────────────────────────────────
print("Building weather data …")

wx = df_weather.copy()
wx["Month_Num"] = wx["Month"].map(month_map)
wx["date"] = pd.to_datetime(
    wx["Year"].astype(str) + "-" + wx["Month_Num"].astype(str).str.zfill(2) + "-01"
)
wx = wx.sort_values("date").reset_index(drop=True)

weather_records = []
for _, row in wx.iterrows():
    weather_records.append({
        "date":        row["date"].strftime("%Y-%m-%d"),
        "rainfall_mm": safe(row["Rainfall"]),
        "temp_c":      safe(row["Temperature"]),
        "yield_index": safe(row["Yield_Index"]),
        "month":       int(row["Month_Num"]),
        "year":        int(row["Year"]),
    })

print(f"  Weather records: {len(weather_records)}")

# ─────────────────────────────────────────────────────────────────────────────
# 9. EXPORT DATA  (app's load_export_data)
# ─────────────────────────────────────────────────────────────────────────────
print("Building export data …")

exp = df_export.copy()
exp_records = []
for _, row in exp.iterrows():
    exp_records.append({
        "year":                int(row["Year"]),
        "Desiccated Coconut":  safe(row["DC_MT"]),
        "Coconut Oil":         safe(row["CocoOil_MT"]),
        "Coconut Milk":        safe(row["CocoMilk_MT"]),
        "Coir Products":       safe(row["Coir_MT"]),
        "Fresh Nuts":          safe(row["FreshNuts_1000"]),
        "Total":               safe(row["Total_Export_MT"]),
    })

# Export destinations – latest year
dest_latest_year = df_dest["Year"].max()
dest_row = df_dest[df_dest["Year"] == dest_latest_year].iloc[0]
dest_cols = ["USA", "UK", "Germany", "Australia", "Netherlands", "Japan", "Canada", "UAE", "Others"]
dest_total = sum(float(dest_row.get(c, 0) or 0) for c in dest_cols)
dest_records = []
for c in dest_cols:
    val = float(dest_row.get(c, 0) or 0)
    dest_records.append({
        "Country":     c,
        "Value_USD_M": round(val, 2),
        "Share_pct":   round(val / max(dest_total, 1) * 100, 1),
    })

print(f"  Export records: {len(exp_records)}, dest year: {dest_latest_year}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. GLOBAL COMPARISON DATA  (app's load_global_data)
# ─────────────────────────────────────────────────────────────────────────────
print("Building global comparison data …")

global_records = []
for _, row in df_gcmp.iterrows():
    global_records.append({
        "year":        int(row["Year"]),
        "Sri Lanka":   safe(row["SL"]),
        "Indonesia":   safe(row["Indonesia"]),
        "Philippines": safe(row["Philippines"]),
        "India":       safe(row["India"]),
        "Vietnam":     safe(row["Vietnam"]),
    })

# Production data (static FAO approximate, same as original app)
production_records = [
    {"Country": "Indonesia",   "Production_B_nuts": 17.1},
    {"Country": "Philippines", "Production_B_nuts": 14.8},
    {"Country": "India",       "Production_B_nuts": 14.7},
    {"Country": "Sri Lanka",   "Production_B_nuts": 3.0},
    {"Country": "Vietnam",     "Production_B_nuts": 1.6},
    {"Country": "Brazil",      "Production_B_nuts": 2.9},
    {"Country": "Thailand",    "Production_B_nuts": 1.5},
]

print(f"  Global records: {len(global_records)}")

# ─────────────────────────────────────────────────────────────────────────────
# 11. DEMAND ELASTICITY DATA  (app's load_demand_elasticity)
# ─────────────────────────────────────────────────────────────────────────────
print("Computing demand elasticity …")

# Merge weekly data with monthly regimes for OLS
df_weekly_clone = df_weekly.copy()
df_weekly_clone["Date"] = pd.to_datetime(
    df_weekly_clone["Year"].astype(str) + "-" + df_weekly_clone["Month"],
    format="%Y-%b"
)
df_elas = df_weekly_clone.merge(monthly_regimes, on="Date", how="left").dropna(subset=["Monthly_Regime"])
df_elas["Log_Price"]  = np.log(df_elas["Avg_Price"])
df_elas["Log_Demand"] = np.log(df_elas["Sold_Nuts"])

elast_results = {}
annual_records = []

for regime in ["Stable", "Warning", "Crisis"]:
    sub = df_elas[df_elas["Monthly_Regime"] == regime].dropna(subset=["Log_Price", "Log_Demand"])
    if len(sub) < 5:
        continue
    X_ols = sm.add_constant(sub["Log_Price"])
    mdl   = sm.OLS(sub["Log_Demand"], X_ols).fit(cov_type="HC3")
    coef  = mdl.params["Log_Price"]
    elast_results[regime] = {
        "elasticity":    round(float(coef), 3),
        "sensitivity":   round(abs(float(coef)) * 100, 1),
    }

# Build yearly demand table matching app's Demand_Elasticity sheet expectations
annual_weekly = df_weekly.groupby("Year").agg(
    Avg_Price=("Avg_Price", "mean"),
    Sold_Nuts=("Sold_Nuts", "sum"),
).reset_index()
annual_weekly["YoY_Price_Change"] = annual_weekly["Avg_Price"].pct_change().mul(100).round(1)
annual_weekly["YoY_Demand_Change"] = annual_weekly["Sold_Nuts"].pct_change().mul(100).round(1)

# Map dominant regime per year from clust_df
dom_regime = (clust_df.groupby("Year")["Regime"]
              .agg(lambda x: x.mode()[0])
              .reset_index()
              .rename(columns={"Regime": "Dominant_Regime"}))
annual_weekly = annual_weekly.merge(dom_regime, on="Year", how="left")

for _, row in annual_weekly.iterrows():
    reg = row.get("Dominant_Regime", "Stable")
    el  = elast_results.get(reg, {})
    annual_records.append({
        "Year":                     int(row["Year"]),
        "Regime":                   reg,
        "Avg Annual Price (Rs./Nut)": round(float(row["Avg_Price"]) / 1000, 2),
        "Elasticity Coefficient":    el.get("elasticity", None),
        "Sensitivity Level (%)":     el.get("sensitivity", None),
    })

print(f"  Elasticity by regime: {elast_results}")
print(f"  Demand records: {len(annual_records)}")

# ─────────────────────────────────────────────────────────────────────────────
# 12. ASSEMBLE AND WRITE JSON
# ─────────────────────────────────────────────────────────────────────────────
print(f"\nWriting {OUTPUT_FILE} …")

output = {
    # ── app section: load_data() ──────────────────────────────────────────
    "history":   history_records,     # monthly price history (history_df)
    "forecast":  forecast_records,    # 12-month SARIMA forecast (forecast_df)
    "weekly":    weekly_records,      # weekly auction prices (weekly_df)

    # ── app section: load_weather_data() ─────────────────────────────────
    "weather":   weather_records,     # weather_df

    # ── app section: load_export_data() ──────────────────────────────────
    "export":    exp_records,         # export_df
    "destinations": dest_records,     # destinations_df

    # ── app section: load_global_data() ──────────────────────────────────
    "global_price":  global_records,  # global_price_df
    "production":    production_records,

    # ── app section: load_demand_elasticity() ────────────────────────────
    "demand":        annual_records,  # demand_df
    "regime_stats":  elast_results,   # demand_regime_stats
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Done — {OUTPUT_FILE} written successfully.")
print(f"  history:       {len(history_records)} records")
print(f"  forecast:      {len(forecast_records)} months")
print(f"  weekly:        {len(weekly_records)} records")
print(f"  weather:       {len(weather_records)} records")
print(f"  export:        {len(exp_records)} years")
print(f"  destinations:  {len(dest_records)} countries")
print(f"  global_price:  {len(global_records)} years")
print(f"  production:    {len(production_records)} countries")
print(f"  demand:        {len(annual_records)} years")
