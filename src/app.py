import os
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px
import requests

st.set_page_config(
    page_title="Retail Price Intelligence",
    page_icon="🏷️",
    layout="wide"
)

# 1. Ensure storage directory exists
os.makedirs("data", exist_ok=True)
db_path = "data/retail_warehouse.duckdb"

conn = duckdb.connect(db_path, read_only=False)

# 2. Check if raw_products exists; if not, fetch and load data
table_check = conn.execute(
    "SELECT count(*) FROM information_schema.tables WHERE table_name = 'raw_products'"
).fetchone()[0]

if table_check == 0:
    with st.spinner("Fetching catalog data and building warehouse..."):
        url = "https://dummyjson.com/products?limit=100"
        response = requests.get(url, timeout=15)
        raw_items = response.json().get("products", [])

        records = []
        for item in raw_items:
            records.append({
                "product_id": int(item.get("id")),
                "title": str(item.get("title")),
                "category": str(item.get("category")),
                "brand": str(item.get("brand") or "Generic"),
                "msrp": float(item.get("price")),
                "discount_pct": float(item.get("discountPercentage", 0.0)),
                "stock": int(item.get("stock", 0)),
                "rating": float(item.get("rating", 0.0))
            })

        init_df = pd.DataFrame(records)
        conn.register("temp_df", init_df)
        conn.execute("CREATE TABLE raw_products AS SELECT * FROM temp_df")

# 3. Read and execute the analytical transformation SQL
try:
    with open("src/transform.sql", "r") as f:
        sql_script = f.read()
    conn.execute(sql_script)
    df = conn.execute("SELECT * FROM v_category_pricing_intelligence").df()
except Exception:
    # Resilient fallback: compute metrics directly if SQL script view has syntax/file mismatches
    df = conn.execute("""
        SELECT 
            product_id,
            title,
            category,
            brand,
            msrp,
            discount_pct,
            stock,
            rating,
            ROUND(msrp * (1 - (discount_pct / 100.0)), 2) AS effective_price,
            ROUND(stock * msrp * (1 - (discount_pct / 100.0)), 2) AS inventory_value,
            CASE 
                WHEN stock < 10 THEN 'Stockout Risk'
                WHEN discount_pct > 20 AND rating < 3.5 THEN 'Margin Drain'
                WHEN stock > 100 AND discount_pct < 5 THEN 'Overstocked'
                ELSE 'Healthy'
            END AS inventory_health_status
        FROM raw_products
    """).df()

# 4. Streamlit Dashboard Layout
st.title("🏷️ Retail Price Intelligence & Markdown Dashboard")
st.caption("Automated category monitoring, discount spread analysis, and stockout risk mitigation.")

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monitored SKUs", f"{len(df):,}")
col2.metric("Total Portfolio Value", f"${df['inventory_value'].sum():,.2f}")
col3.metric("Average Discount Depth", f"{df['discount_pct'].mean():.1f}%")
risk_count = len(df[df['inventory_health_status'] != 'Healthy'])
col4.metric("Flagged SKU Risks", f"{risk_count:,}")

st.divider()

# Visualizations
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    fig_scatter = px.scatter(
        df,
        x="effective_price",
        y="discount_pct",
        size="stock",
        color="inventory_health_status",
        hover_name="title",
        title="Price vs. Discount Depth (Bubble Size = Stock Units)",
        labels={"effective_price": "Effective Selling Price ($)", "discount_pct": "Discount %"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with row1_col2:
    fig_bar = px.histogram(
        df,
        x="inventory_health_status",
        color="inventory_health_status",
        title="Inventory Operational Health Distribution"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Data Drilldown Table
st.subheader("High-Risk / Actionable SKUs")
actionable_df = df[df['inventory_health_status'] != 'Healthy'][[
    "title", "category", "brand", "msrp", "discount_pct", "stock", "rating", "inventory_health_status"
]]
st.dataframe(actionable_df, use_container_width=True)
