# 🏷️ Automated Retail Price Intelligence & Markdown Analytics Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://retail-price-intelligence-myj9qtfqw72ga5yzsycxl2.streamlit.app/)

An end-to-end data pipeline that ingests live retail catalog REST APIs, models inventory risk and price elasticity in DuckDB via analytical SQL logic, and surfaces actionable operational signals through an interactive Streamlit dashboard hosted 24/7.

🔗 **Live Public Dashboard:** [View Deployed App](https://retail-price-intelligence-myj9qtfqw72ga5yzsycxl2.streamlit.app/)

---

## 💼 Business Problem & Impact

Retail operators face margin loss through misaligned discount strategies and capital lockup in stagnant inventory. This intelligence engine automates catalog analysis to monitor inventory distributions and surface commercial operational risks:

* **⚠️ Stockout Risk:** High-demand or core SKUs with fewer than 10 units remaining.
* **💸 Margin Drain:** Items discounted by more than 20% with customer review scores below 3.5, signaling inefficient discount spend.
* **🧊 Overstocked:** Excess inventory (>100 units held) coupled with minimal discount depth (<5%), identifying slow-moving capital.
* **✅ Healthy:** Inventory operating within expected turnover and margin thresholds.

---

## 🛠️ Architecture & Tech Stack

```text
[REST API] ──(Requests & Pandas ETL)──> [DuckDB Warehouse] ──(SQL Transformation Engine)──> [Streamlit BI Dashboard]
