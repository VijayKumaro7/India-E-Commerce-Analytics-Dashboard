# India E-Commerce Analytics Dashboard

A story-driven analytics dashboard built with **Streamlit + Plotly** on real
Indian e-commerce order data — not synthetic data, not Brazil/Olist. Covers
560 real orders (1,500 order line items) across 19 Indian states for FY
Apr 2018 – Mar 2019.

**Live focus:** this isn't a "here's 6 charts" dashboard. Every section leads
with a plain-English insight computed live from the filtered data, because
that's what separates an analyst's dashboard from a BI-tool default export —
and it's what a recruiter or interviewer will actually remember.

## The story this dashboard tells

- Revenue and profit don't move together — some of the biggest revenue
  categories are actively losing money (~33% of all order line items are
  loss-making).
- State-level revenue leaders are not always the healthiest states on margin
  — a state generating high revenue on deep discounts can be worse for the
  business than a smaller, well-margined one.
- Sub-category granularity matters: "Furniture" as a category looks fine,
  but "Tables" and "Bookcases" inside it are actively bleeding money while
  other sub-categories carry the segment.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Project structure

```
india-dashboard/
├── app.py                          # Streamlit dashboard (single-file app)
├── data/
│   ├── india_ecommerce_orders.csv  # cleaned, feature-engineered dataset
│   └── india_states.geojson        # simplified India state boundaries
├── requirements.txt
└── README.md
```

## Data

**Source:** Indian E-Commerce Sales dataset (Kaggle), originally three raw
files (`List of Orders.csv`, `Order Details.csv`, `Sales target.csv`) merged
and cleaned into a single order-line-item table.

**Cleaning applied:**
- Trimmed whitespace in `State`/`City`/`CustomerName` (e.g. `"Kerala "` →
  `"Kerala"` — a real data quality issue in the raw file that would silently
  split state-level aggregates in two if left unfixed)
- Parsed `Order Date` to proper datetime
- Added `Profit Margin %` per line item

**Known limitation (stated honestly, not hidden):** customers are identified
by first name only — there's no unique customer ID in the source data. The
"repeat customer" metric in the dashboard is therefore directional, not
exact, and the dashboard says so explicitly in the UI rather than presenting
it as more precise than it is. A production version would resolve this with
a proper `customer_id` join key.

**Geographic data:** `india_states.geojson` is sourced from
[geohacker/india](https://github.com/geohacker/india) (state-level
boundaries), simplified with Shapely (Douglas-Peucker, tolerance 0.01°) to
cut file size from ~23 MB to ~0.77 MB — small enough to commit to the repo
and load fast in the browser, without visibly degrading the map at this
zoom level. All 19 state names in the order data match the geojson's
`NAME_1` property exactly, so there's no silent state-name mismatch
(a common bug in India choropleths — e.g. "Orissa" vs "Odisha").

## Dashboard sections

1. **KPI row** — revenue, profit, margin, orders, AOV, loss-making item share
2. **Revenue & profit trend** — monthly, with auto-generated callout on
   best/worst months
3. **Category & sub-category performance** — margin-colored bars, sorted
   worst-to-best profit
4. **State-wise performance** — bar chart + interactive choropleth map
   (toggle between Revenue / Profit / Margin % / Orders), adjustable top-N
5. **City-level drill-down** — click a state on the map (or use the
   dropdown) to see its city-level revenue/profit breakdown, revenue
   concentration risk, and best/worst-margin city within that state
6. **Customer analysis** — top customers, repeat vs one-time split
7. **Raw data explorer** — filtered table + CSV export

## Tech notes

- All filters (date range, state, category) recompute every chart and every
  insight sentence live — nothing is hardcoded from a one-time analysis.
- `@st.cache_data` used on the data load so filtering stays fast.
- Color scale on bar charts is margin-driven (red → white → green), not
  decorative, so profitability is visible at a glance without reading axis
  labels.

## Possible extensions

- Swap the CSV for a Postgres connection and add a scheduled refresh
- Add a proper `customer_id` and rebuild the repeat-customer metric on real
  identity resolution
- Add a discount/promotion table if available, to explain *why* certain
  sub-categories run at a loss (currently the data shows the loss but not
  the driver — a natural "what I'd ask for next" talking point in interviews)
