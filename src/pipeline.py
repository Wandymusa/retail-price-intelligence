import os
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests


API_URL = "https://dummyjson.com/products?limit=0"
DB_PATH = "data/retail_warehouse.duckdb"


def fetch_catalog_data():
    """Extract product catalog from REST API with error handling."""
    print("Fetching retail catalog data from API...")
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])
    except requests.exceptions.RequestException as error:
        print(f"API extraction failed: {error}")
        raise


def clean_and_normalize(products):
    """Normalize product JSON into a DataFrame with a consistent schema."""
    required_cols = [
        "id",
        "title",
        "category",
        "price",
        "discountPercentage",
        "rating",
        "stock",
        "brand",
        "weight",
    ]
    df = pd.DataFrame(products).reindex(columns=required_cols)

    df["brand"] = df["brand"].fillna("Generic/Store Brand")
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0).astype(int)
    for column in ("price", "discountPercentage", "rating"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["effective_price"] = (
        df["price"] * (1 - df["discountPercentage"] / 100.0)
    ).round(2)
    df["inventory_value"] = (df["effective_price"] * df["stock"]).round(2)
    df["ingested_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return df


def load_to_duckdb(df):
    """Load normalized data into a persistent DuckDB warehouse."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    try:
        conn.register("df_view", df)
        conn.execute("CREATE OR REPLACE TABLE raw_products AS SELECT * FROM df_view")
        row_count = conn.execute("SELECT COUNT(*) FROM raw_products").fetchone()[0]
        print(f"Successfully loaded {row_count} SKUs into {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    raw_data = fetch_catalog_data()
    cleaned_df = clean_and_normalize(raw_data)
    load_to_duckdb(cleaned_df)