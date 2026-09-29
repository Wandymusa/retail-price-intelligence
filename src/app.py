import streamlit as st
import duckdb
import plotly.express as px

st.set_page_config(page_title="Retail Markdown & Price Intelligence", layout="wide")
st.title("🏷️ Retail Price Intelligence & Markdown Dashboard")
st.markdown("Automated category monitoring, discount spread analysis, and stockout risk mitigation.")

# Load transformed data directly from DuckDB using the SQL logic
conn = duckdb.connect("data/retail_warehouse.duckdb", read_only=False)

# Execute the view creation script to guarantee fresh transformations
with open("src/transform.sql", "r") as f:
    conn.execute(f.read())

df = conn.execute("SELECT * FROM v_category_pricing_intelligence").df()
conn.close()

# Sidebar: Category & Risk Filtering
categories = ["All"] + sorted(df["category"].unique().tolist())
selected_category = st.sidebar.selectbox("Filter Category:", categories)

filtered_df = df if selected_category == "All" else df[df["category"] == selected_category]

# KPI Summary Cards
col1, col2, col3, col4 = st.columns(4)
total_inventory = filtered_df["inventory_value"].sum()
avg_discount = filtered_df["discount_pct"].mean()
high_risk_count = len(filtered_df[filtered_df["inventory_health_status"] != "Healthy"])

col1.metric("Monitored SKUs", len(filtered_df))
col2.metric("Total Portfolio Value", f"${total_inventory:,.2f}")
col3.metric("Average Discount Depth", f"{avg_discount:.1f}%")
col4.metric("Flagged SKU Risks", high_risk_count, delta_color="inverse")

st.divider()

# Charts
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    fig_scatter = px.scatter(
        filtered_df,
        x="effective_price",
        y="discount_pct",
        size="stock",
        color="inventory_health_status",
        hover_data=["title", "brand", "rating"],
        title="Price vs. Discount Depth (Bubble Size = Stock Units)",
        labels={"effective_price": "Effective Selling Price ($)", "discount_pct": "Discount %"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with row1_col2:
    fig_bar = px.histogram(
        filtered_df,
        x="inventory_health_status",
        color="inventory_health_status",
        title="Inventory Operational Health Distribution"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Data Drill-Down Table
st.subheader("High-Risk / Actionable SKUs")
st.dataframe(
    filtered_df[filtered_df["inventory_health_status"] != "Healthy"]
    [["title", "category", "brand", "msrp", "discount_pct", "stock", "rating", "inventory_health_status"]],
    use_container_width=True
)