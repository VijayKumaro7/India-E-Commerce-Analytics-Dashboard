"""
Smoke tests for the India E-Commerce dashboard data assets.

These deliberately mirror the exact paths and columns that app.py depends on,
so a broken data path or a renamed column fails CI instead of only surfacing
when someone runs `streamlit run app.py`.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "india_ecommerce_orders.csv"
GEOJSON_PATH = ROOT / "data" / "india_states.geojson"

# Columns app.py reads directly.
REQUIRED_COLUMNS = {
    "Order ID",
    "Order Date",
    "CustomerName",
    "State",
    "City",
    "Amount",
    "Profit",
    "Category",
    "Sub-Category",
}


def test_data_files_exist():
    assert CSV_PATH.exists(), f"missing data file: {CSV_PATH}"
    assert GEOJSON_PATH.exists(), f"missing data file: {GEOJSON_PATH}"


def test_csv_loads_with_required_columns():
    df = pd.read_csv(CSV_PATH, parse_dates=["Order Date"])
    assert not df.empty
    missing = REQUIRED_COLUMNS - set(df.columns)
    assert not missing, f"CSV missing required columns: {missing}"
    assert pd.api.types.is_datetime64_any_dtype(df["Order Date"])
    # Core KPI math must be computable.
    assert df["Amount"].sum() > 0
    assert pd.api.types.is_numeric_dtype(df["Profit"])


def test_state_names_match_geojson():
    df = pd.read_csv(CSV_PATH)
    with open(GEOJSON_PATH) as f:
        geo = json.load(f)
    geo_states = {feat["properties"]["State"] for feat in geo["features"]}
    # Every state in the data must resolve on the choropleth, or the map
    # silently drops it.
    unmatched = set(df["State"].str.strip().unique()) - geo_states
    assert not unmatched, f"states in data not present in geojson: {unmatched}"
