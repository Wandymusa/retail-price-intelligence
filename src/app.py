import os
import subprocess
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="Retail Price Intelligence",
    page_icon="🏷️",
    layout="wide"
)

# 2. Ensure data directory & database exist
DB_PATH = "data/retail_warehouse.duckdb"
os.makedirs("data", exist_ok=True)

if not os.path.exists(DB_PATH):
    subprocess.run(["python3", "src/pipeline.py"], check=True)

# 3. Connect to DuckDB and load data safely
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=False)

conn = get_connection()

# Execute query using an isolated cursor to avoid unclosed query lockups
cur = conn.cursor()
try:
    df = cur.execute("""
        SELECT 
            id,
            title,
            category,
            brand,
            price,
            discountPercentage AS discount_pct,
            rating,
            stock,
            effective_price,
            inventory_value,
            CASE 
                WHEN stock < 10 THEN 'Critical Stock'
                WHEN discountPercentage > 25 THEN 'Deep Discount Risk'
                ELSE 'Healthy'
            END AS inventory_health_status
        FROM raw_products
    """).df()
except Exception as e:
    # Fallback if raw_products does not exist yet
    cur.close()
    subprocess.run(["python3", "src/pipeline.py"], check=True)
    cur = conn.cursor()
    df = cur.execute("""
        SELECT 
            id,
            title,
            category,
            brand,
            price,
            discountPercentage AS discount_pct,
            rating,
            stock,
            effective_price,
            inventory_value,
            CASE 
                WHEN stock < 10 THEN 'Critical Stock'
                WHEN discountPercentage > 25 THEN 'Deep Discount Risk'
                ELSE 'Healthy'
            END AS inventory_health_status
        FROM raw_products
    """).df()
finally:
    cur.close()

# 4. Streamlit Dashboard Layout
st.title("🏷️ Retail Price Intelligence")
st.caption("Automated category monitoring, discount spread analysis, and stockout risk mitigation")

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monitored SKUs", f"{len(df):,}")
col2.metric("Total Portfolio Value", f"${df['inventory_value'].sum():,.2f}")
col3.metric("Average Discount Depth", f"{df['discount_pct'].mean():.1f}%")
risk_count = len(df[df["inventory_health_status"] != "Healthy"])
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
        title="Effective Price vs Discount Depth by Inventory Status",
        labels={"effective_price": "Effective Price ($)", "discount_pct": "Discount (%)"}
    )
    fig_scatter.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

with row1_col2:
    fig_cat = px.bar(
        df.groupby("category")["inventory_value"].sum().reset_index().sort_values(by="inventory_value", ascending=False),
        x="category",
        y="inventory_value",
        title="Total Inventory Exposure by Category",
        labels={"inventory_value": "Inventory Value ($)", "category": "Category"}
    )
    fig_cat.update_layout(margin=dict(l=20, r=20, t=40, b=20), xaxis_tickangle=-45)
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()

# Detailed SKU Table with Filters
st.subheader("SKU Inventory Health Table")
selected_category = st.multiselect("Filter by Category", options=df["category"].unique(), default=df["category"].unique())
filtered_df = df[df["category"].isin(selected_category)]

st.dataframe(
    filtered_df[["title", "category", "brand", "price", "effective_price", "discount_pct", "stock", "inventory_health_status"]],
    use_container_width=True,
    hide_index=True
)