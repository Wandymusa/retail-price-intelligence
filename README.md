# Retail Price Intelligence

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://retail-price-intelligence-myj9qtfqw72ga5yzsycxl2.streamlit.app)

🔗 **Live Production Dashboard:** [retail-price-intelligence.streamlit.app](https://retail-price-intelligence-myj9qtfqw72ga5yzsycxl2.streamlit.app)

Automated category monitoring, discount spread analysis, and stockout risk dashboard powered by DuckDB and Streamlit.
# 🏷️ Automated Retail Price Intelligence & Markdown Analytics Engine

An end-to-end data pipeline extracting retail catalog APIs, modeling product elasticity in DuckDB via analytical window functions, and serving operational inventory risk signals via an interactive Streamlit dashboard.

![Project Roadmap](roadmap.svg)

## 💼 Business Problem & Impact
Retailers routinely experience margin leakage through uncalibrated discounting or tie up working capital in slow-moving stock. This system ingests product catalog metrics from live REST APIs to automate catalog auditing and surface critical inventory risks in real-time:

*   **⚠️ Critical Stockout Risk:** High-performing SKUs with fewer than 10 units remaining.
*   **💸 Margin Drain:** Heavily discounted items (>20% markdown) paired with low customer sentiment (<3.5 rating), indicating inefficient promotion spend.
*   **🧊 Overstocked / Stagnant:** High inventory held (>100 units) with negligible discount (<5%), highlighting capital allocation bottlenecks.

## 🛠️ Architecture & Stack
```text
[REST API] ──(Requests/Pandas ETL)──> [DuckDB Warehouse] ──(SQL CTEs & Windowing)──> [Streamlit BI Dashboard]