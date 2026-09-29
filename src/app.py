import os
import subprocess
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. Ensure the data directory exists
os.makedirs("data", exist_ok=True)
db_path = "data/retail_warehouse.duckdb"

# 2. Run the extraction pipeline if the database is missing
if not os.path.exists(db_path):
    subprocess.run(["python3", "src/pipeline.py"], check=True)

# Streamlit Page Config
st.set_page_config(
    page_title="Retail Price Intelligence",
    page_icon="🏷️",
    layout="wide"
)

# 3. Connect to DuckDB and create the analytical view
conn = duckdb.connect(db_path, read_only=False)

with open("src/transform.sql", "r") as f:
    sql_script = f.read()

conn.execute(sql_script)

df = conn.execute("SELECT * FROM v_category_pricing_intelligence").df()

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

# Charts
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

# Data Table Drill-Down
st.subheader("High-Risk / Actionable SKUs")
actionable_df = df[df['inventory_health_status'] != 'Healthy'][[
    "title", "category", "brand", "msrp", "discount_pct", "stock", "rating", "inventory_health_status"
]]
st.dataframe(actionable_df, use_container_width=True)
