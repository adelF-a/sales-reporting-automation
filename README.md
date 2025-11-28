# 📈 Automated Sales Reporting & BI Pipeline

![Python](https://img.shields.io/badge/Python-ETL%20Automation-blue?style=for-the-badge&logo=python)
![SQL](https://img.shields.io/badge/SQL-Advanced%20Logic-orange?style=for-the-badge&logo=sqlite)
![Tableau](https://img.shields.io/badge/Tableau-Dashboarding-E97627?style=for-the-badge&logo=tableau)

## 📋 Project Overview
This project mimics a real-world **Business Intelligence (BI) Pipeline** designed to automate monthly financial reporting. It replaces manual spreadsheet work with a scalable Python/SQL architecture and a professional Tableau Dashboard.

**Workflow:**
1.  **Python (ETL):** Ingests raw transaction logs and cleans "dirty" data (imputing missing values).
2.  **Advanced SQL:** Calculates complex KPIs like **Month-over-Month Growth** and **Churn Rate** using Window Functions.
3.  **Tableau:** Visualizes the results in an interactive Executive Dashboard with drill-down capabilities.

## 📊 Executive Tableau Dashboard
*Connected directly to the processed data pipeline. Features **Drill-Down** capabilities by Region and Product.*

![Tableau Dashboard](tableau_dashboard.png)

## 🛠 Technical Implementation

### 1. Data Engineering (Python)
* **Synthetic Data Generator:** A custom script (`generate_data.py`) creates realistic transaction logs (5,000+ rows) with intentional "dirty" data to simulate real-world cleaning scenarios.
* **Automation:** The pipeline automatically handles missing regional tags (`NaN`) before analysis.

### 2. SQL Business Logic (Window Functions)
I utilized SQL **Window Functions** (`LAG`, `OVER`) to calculate time-series metrics directly in the database layer.

**Example: Month-over-Month (MoM) Revenue Growth**
```sql
SELECT 
    Month,
    Revenue,
    -- Compare current month to previous month using LAG()
    LAG(Revenue, 1) OVER (ORDER BY Month) as Prev_Month_Rev,
    -- Calculate Growth %
    ROUND((Revenue - LAG(Revenue, 1) OVER (ORDER BY Month)) / 
           LAG(Revenue, 1) OVER (ORDER BY Month) * 100, 2) as Growth_Pct
FROM MonthlyStats