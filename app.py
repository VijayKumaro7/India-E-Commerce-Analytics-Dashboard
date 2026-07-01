"""
India E-Commerce Analytics Dashboard
--------------------------------------
A story-driven Streamlit dashboard on real Indian e-commerce order data
(FY 2018-19, 560 orders / 1,500 line items across 19 states).

Run:
    streamlit run app.py
"""

import json

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# Page config & light styling
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="India E-Commerce Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = {
    "primary": "#1F4E79",     # deep blue — trust, corporate
    "accent": "#E8871E",      # amber — India-market warmth without being flag-cliché
    "positive": "#2E7D32",
    "negative": "#C62828",
    "neutral": "#6B7280",
    "bg_card": "#F8FAFC",
}

st.markdown(f"""
<style>
    .block-container {{ padding-top: 1.5rem; }}
    div[data-testid="stMetric"] {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 14px 16px 8px 16px;
    }}
    div[data-testid="stMetricValue"] {{ font-size: 1.6rem; }}
    .story-box {{
        background-color: #FFF7ED;
        border-left: 4px solid {PALETTE['accent']};
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 14px;
        font-size: 0.95rem;
    }}
    h1, h2, h3 {{ color: {PALETTE['primary']}; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path="data/india_ecommerce_orders.csv"):
    df = pd.read_csv(path, parse_dates=["Order Date"])
    return df


@st.cache_data
def load_geojson(path="data/india_states.geojson"):
    with open(path) as f:
        return json.load(f)


df = load_data()
india_geojson = load_geojson()

# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.title("📦 Filters")
st.sidebar.caption("India E-Commerce · FY 2018-19")

min_date, max_date = df["Order Date"].min(), df["Order Date"].max()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)

states = sorted(df["State"].unique())
sel_states = st.sidebar.multiselect("State", states, default=states)

categories = sorted(df["Category"].unique())
sel_categories = st.sidebar.multiselect("Category", categories, default=categories)

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start_date, end_date = min_date, max_date

mask = (
    (df["Order Date"] >= start_date) & (df["Order Date"] <= end_date)
    & (df["State"].isin(sel_states))
    & (df["Category"].isin(sel_categories))
)
fdf = df.loc[mask].copy()

st.sidebar.markdown("---")
st.sidebar.metric("Rows in current view", f"{len(fdf):,}")
st.sidebar.caption(
    "Data: Indian E-Commerce Sales dataset (Kaggle) — 560 orders, "
    "1,500 order line items, 19 states, FY Apr 2018 – Mar 2019."
)

if fdf.empty:
    st.warning("No data for the current filter selection. Widen your filters.")
    st.stop()

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("India E-Commerce Analytics")
st.caption(
    "Where the revenue comes from, where the profit leaks out, and which "
    "states and categories actually deserve the marketing budget."
)

# ----------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------
total_revenue = fdf["Amount"].sum()
total_profit = fdf["Profit"].sum()
margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0
n_orders = fdf["Order ID"].nunique()
aov = total_revenue / n_orders if n_orders else 0
loss_share = (fdf["Profit"] < 0).mean() * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
c2.metric("Total Profit", f"₹{total_profit:,.0f}",
          delta=f"{margin_pct:.1f}% margin")
c3.metric("Orders", f"{n_orders:,}")
c4.metric("Avg Order Value", f"₹{aov:,.0f}")
c5.metric("Loss-making line items", f"{loss_share:.0f}%",
          delta="of all items", delta_color="off")

st.markdown("---")

# ----------------------------------------------------------------------
# SECTION 1 — Trend over time
# ----------------------------------------------------------------------
st.subheader("1. Revenue & Profit Trend")

monthly = (
    fdf.groupby(pd.Grouper(key="Order Date", freq="MS"))
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    .reset_index()
)

best_month = monthly.loc[monthly["Revenue"].idxmax(), "Order Date"].strftime("%B %Y") if not monthly.empty else "N/A"
worst_profit_month = monthly.loc[monthly["Profit"].idxmin(), "Order Date"].strftime("%B %Y") if not monthly.empty else "N/A"

st.markdown(f"""
<div class="story-box">
📈 <b>{best_month}</b> was the strongest revenue month in the current view, while
<b>{worst_profit_month}</b> had the weakest profit — worth checking what discounting or
category mix drove that gap.
</div>
""", unsafe_allow_html=True)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=monthly["Order Date"], y=monthly["Revenue"], name="Revenue",
    line=dict(color=PALETTE["primary"], width=3), mode="lines+markers"
))
fig_trend.add_trace(go.Scatter(
    x=monthly["Order Date"], y=monthly["Profit"], name="Profit",
    line=dict(color=PALETTE["accent"], width=3), mode="lines+markers"
))
fig_trend.update_layout(
    height=380, hovermode="x unified",
    yaxis_title="₹", legend=dict(orientation="h", y=1.1),
    margin=dict(t=20, b=0, l=0, r=0),
)
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------------------------------------------------
# SECTION 2 — Category & Sub-category performance
# ----------------------------------------------------------------------
st.subheader("2. Category & Sub-Category Performance")

cat_col, sub_col = st.columns([1, 1.4])

cat_perf = (
    fdf.groupby("Category")
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"))
    .reset_index()
)
cat_perf["Margin %"] = (cat_perf["Profit"] / cat_perf["Revenue"] * 100).round(1)

with cat_col:
    fig_cat = px.bar(
        cat_perf.sort_values("Revenue"), x="Revenue", y="Category", orientation="h",
        color="Margin %", color_continuous_scale=["#C62828", "#F8FAFC", "#2E7D32"],
        color_continuous_midpoint=0, text="Revenue",
        title="Revenue by Category (colored by margin)"
    )
    fig_cat.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_cat.update_layout(height=340, margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig_cat, use_container_width=True)

sub_perf = (
    fdf.groupby(["Category", "Sub-Category"])
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"))
    .reset_index()
    .sort_values("Profit")
)

with sub_col:
    fig_sub = px.bar(
        sub_perf, x="Profit", y="Sub-Category", orientation="h", color="Category",
        title="Profit by Sub-Category (worst → best)",
        color_discrete_map={
            "Furniture": PALETTE["primary"], "Clothing": PALETTE["accent"], "Electronics": "#6B7280"
        }
    )
    fig_sub.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.4)
    fig_sub.update_layout(height=340, margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig_sub, use_container_width=True)

worst_subcat = sub_perf.iloc[0]
best_subcat = sub_perf.iloc[-1]
st.markdown(f"""
<div class="story-box">
🪑 <b>{worst_subcat['Sub-Category']}</b> ({worst_subcat['Category']}) is the biggest profit
drain in the current view, losing <b>₹{abs(worst_subcat['Profit']):,.0f}</b> — while
<b>{best_subcat['Sub-Category']}</b> ({best_subcat['Category']}) is the strongest performer at
<b>₹{best_subcat['Profit']:,.0f}</b> profit. Same "revenue" line on a P&L can hide very
different stories — this is why sub-category-level analysis matters more than category-level.
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SECTION 3 — State-wise performance
# ----------------------------------------------------------------------
st.subheader("3. State-Wise Performance")

state_perf = (
    fdf.groupby("State")
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)
state_perf["Margin %"] = (state_perf["Profit"] / state_perf["Revenue"] * 100).round(1)

top_n = st.slider("Show top N states by revenue", 5, len(state_perf), min(10, len(state_perf)))
state_view = state_perf.head(top_n)

fig_state = px.bar(
    state_view, x="State", y="Revenue", color="Margin %",
    color_continuous_scale=["#C62828", "#F8FAFC", "#2E7D32"], color_continuous_midpoint=0,
    hover_data=["Profit", "Orders"], title=f"Top {top_n} States by Revenue"
)
fig_state.update_layout(height=380, margin=dict(t=40, b=0, l=0, r=0))

map_metric = st.radio(
    "Map metric", ["Revenue", "Profit", "Margin %", "Orders"],
    horizontal=True, key="map_metric"
)

color_scale = (
    "Blues" if map_metric in ("Revenue", "Orders")
    else ["#C62828", "#F8FAFC", "#2E7D32"]
)
midpoint = 0 if map_metric in ("Profit", "Margin %") else None

fig_map = px.choropleth(
    state_perf, geojson=india_geojson, locations="State",
    featureidkey="properties.State", color=map_metric,
    color_continuous_scale=color_scale,
    color_continuous_midpoint=midpoint,
    hover_data={"Revenue": ":,.0f", "Profit": ":,.0f", "Margin %": ":.1f", "Orders": True, "State": False},
    title=f"{map_metric} by State"
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(height=520, margin=dict(t=40, b=0, l=0, r=0))

bar_tab, map_tab = st.tabs(["📊 Bar chart", "🗺️ Choropleth map"])
with bar_tab:
    st.plotly_chart(fig_state, use_container_width=True)
with map_tab:
    map_event = st.plotly_chart(
        fig_map, use_container_width=True,
        on_select="rerun", selection_mode="points", key="choropleth_map"
    )
    zero_rev_states = sorted(set(f["properties"]["State"] for f in india_geojson["features"]) - set(state_perf["State"]))
    if zero_rev_states:
        st.caption(
            f"Grey states have no orders in the current filtered view "
            f"({len(zero_rev_states)} states/UTs, e.g. {', '.join(zero_rev_states[:5])}...) "
            f"— the dataset only covers 19 of India's states/UTs. "
            f"💡 Click any colored state to drill into its cities below."
        )

# Capture a clicked state from the map (if any) so the drill-down section
# below can default to it. Falls back to the top-revenue state otherwise.
clicked_state = None
if map_event and map_event.get("selection", {}).get("points"):
    clicked_state = map_event["selection"]["points"][0].get("location")
if clicked_state:
    st.session_state["drill_state"] = clicked_state

top_state = state_perf.iloc[0]
lowest_margin_state = state_perf.sort_values("Margin %").iloc[0]
st.markdown(f"""
<div class="story-box">
📍 <b>{top_state['State']}</b> leads on revenue (₹{top_state['Revenue']:,.0f}), but
<b>{lowest_margin_state['State']}</b> has the weakest margin in the current view at
<b>{lowest_margin_state['Margin %']:.1f}%</b> — high revenue doesn't always mean a healthy
state. Worth a pricing/discount review before scaling ad spend there.
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SECTION 4 — City-level drill-down
# ----------------------------------------------------------------------
st.subheader("4. City-Level Drill-Down")

state_options = sorted(state_perf["State"])
default_state = st.session_state.get("drill_state", top_state["State"])
if default_state not in state_options:
    default_state = top_state["State"]

drill_state = st.selectbox(
    "Drill into a state (or click a state on the map above)",
    state_options, index=state_options.index(default_state), key="drill_selectbox"
)

city_df = fdf[fdf["State"] == drill_state]
city_perf = (
    city_df.groupby("City")
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)
city_perf["Margin %"] = (city_perf["Profit"] / city_perf["Revenue"] * 100).round(1)

if city_perf.empty:
    st.info(f"No orders for {drill_state} in the current filtered view.")
else:
    drill_col1, drill_col2 = st.columns([1.5, 1])

    with drill_col1:
        fig_city = px.bar(
            city_perf.sort_values("Revenue"), x="Revenue", y="City", orientation="h",
            color="Margin %", color_continuous_scale=["#C62828", "#F8FAFC", "#2E7D32"],
            color_continuous_midpoint=0, hover_data=["Profit", "Orders"],
            title=f"Cities in {drill_state} by Revenue"
        )
        fig_city.update_layout(height=max(260, 40 * len(city_perf)), margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_city, use_container_width=True)

    with drill_col2:
        state_revenue = city_perf["Revenue"].sum()
        state_profit = city_perf["Profit"].sum()
        state_margin = (state_profit / state_revenue * 100) if state_revenue else 0
        top_city = city_perf.iloc[0]
        concentration = (top_city["Revenue"] / state_revenue * 100) if state_revenue else 0

        st.metric(f"{drill_state} revenue", f"₹{state_revenue:,.0f}")
        st.metric(f"{drill_state} margin", f"{state_margin:.1f}%")
        st.metric("Cities with orders", f"{len(city_perf)}")
        st.metric(
            f"Top city concentration",
            f"{concentration:.0f}%",
            delta=f"{top_city['City']} of state revenue", delta_color="off"
        )

    worst_city = city_perf.sort_values("Margin %").iloc[0]
    best_city = city_perf.sort_values("Margin %").iloc[-1]
    concentration_note = (
        f"<b>{top_city['City']}</b> alone drives <b>{concentration:.0f}%</b> of {drill_state}'s revenue"
        f" — a concentration risk if that one city slows down. "
        if len(city_perf) > 1 else
        f"All of {drill_state}'s revenue in this view comes from a single city, {top_city['City']}. "
    )
    st.markdown(f"""
<div class="story-box">
🏙️ {concentration_note}
{"Within the state, " + f"<b>{worst_city['City']}</b> runs the weakest margin ({worst_city['Margin %']:.1f}%) while <b>{best_city['City']}</b> runs the strongest ({best_city['Margin %']:.1f}%)." if len(city_perf) > 1 else ""}
</div>
""", unsafe_allow_html=True)

    with st.expander(f"View raw city-level table for {drill_state}"):
        st.dataframe(city_perf, use_container_width=True)

# ----------------------------------------------------------------------
# SECTION 5 — Customers
# ----------------------------------------------------------------------
st.subheader("5. Customer Analysis")

cust_col1, cust_col2 = st.columns([1.3, 1])

cust_perf = (
    fdf.groupby("CustomerName")
    .agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

with cust_col1:
    top15 = cust_perf.head(15)
    fig_cust = px.bar(
        top15, x="Revenue", y="CustomerName", orientation="h",
        color="Profit", color_continuous_scale=["#C62828", "#F8FAFC", "#2E7D32"],
        color_continuous_midpoint=0, title="Top 15 Customers by Revenue"
    )
    fig_cust.update_layout(height=420, yaxis=dict(categoryorder="total ascending"),
                            margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig_cust, use_container_width=True)

with cust_col2:
    repeat_customers = (cust_perf["Orders"] > 1).sum()
    total_customers = len(cust_perf)
    repeat_rate = repeat_customers / total_customers * 100 if total_customers else 0

    st.metric("Unique customers", f"{total_customers:,}")
    st.metric("Repeat customers (2+ orders)", f"{repeat_customers:,}",
              delta=f"{repeat_rate:.0f}% repeat rate")

    fig_pie = px.pie(
        values=[repeat_customers, total_customers - repeat_customers],
        names=["Repeat", "One-time"],
        color_discrete_sequence=[PALETTE["primary"], PALETTE["neutral"]],
        hole=0.55, title="Repeat vs One-Time Customers"
    )
    fig_pie.update_layout(height=280, margin=dict(t=40, b=0, l=0, r=0), showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.caption(
        "⚠️ Note: customers are identified by first name only in this dataset "
        "(no unique customer ID), so this repeat-rate is directional, not exact — "
        "some 'repeat customers' may be different people sharing a common name. "
        "A production version of this dashboard would key off a proper customer_id."
    )

st.markdown("---")

# ----------------------------------------------------------------------
# SECTION 6 — Raw data / export
# ----------------------------------------------------------------------
with st.expander("🔍 View filtered raw data"):
    st.dataframe(fdf.sort_values("Order Date", ascending=False), use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_india_ecommerce.csv",
        mime="text/csv",
    )

st.caption(
    "Built with Streamlit + Plotly · Data: Indian E-Commerce Sales dataset (Kaggle), "
    "cleaned and feature-engineered · FY Apr 2018 – Mar 2019."
)
