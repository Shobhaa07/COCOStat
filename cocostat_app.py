
import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------------
# CONFIG
# -------------------------
DATA_PATH = Path("data.xlsx")

# -------------------------
# CACHING FIXES
# -------------------------

@st.cache_resource
def _get_sheet_map():
    # Cached once (resource-level)
    xl = pd.ExcelFile(DATA_PATH)
    return {name: xl.parse(name) for name in xl.sheet_names}

def _sheet(name):
    sheets = _get_sheet_map()
    return sheets.get(name)

@st.cache_data(ttl=3600)
def load_prices():
    df = _sheet("prices")
    return df.copy()

# -------------------------
# VALIDATION BLOCK (NEW)
# -------------------------
def validate_data(df):
    required_cols = {"date", "price"}

    assert df is not None, "Dataset is None"
    assert not df.empty, "Dataset is empty"
    assert required_cols.issubset(df.columns), f"Missing columns: {required_cols - set(df.columns)}"

    # Basic sanity checks
    assert df["price"].notna().any(), "All prices are NaN"
    assert df["price"].between(0, 1e7).all(), "Price values out of plausible range"

# -------------------------
# PROCESSING
# -------------------------
def classify_regime(df):
    df = df.copy()

    # Null guard
    df = df[df["price"].notna()]

    df["regime"] = pd.cut(
        df["price"],
        bins=[0, 65, 80, 999],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )
    return df

# -------------------------
# APP
# -------------------------
def main():
    st.title("Price Dashboard")

    df = load_prices()

    # Validation BEFORE rendering
    validate_data(df)

    df = classify_regime(df)

    st.write("Preview", df.head())
    st.bar_chart(df.set_index("date")["price"])

if __name__ == "__main__":
    main()
