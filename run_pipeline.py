"""Run the sales ETL, SQL reporting layer, and static dashboard build."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from generate_data import write_synthetic_sales


ROOT = Path(__file__).resolve().parent
RAW_DATA = ROOT / "data" / "raw_sales_data.csv"
OUTPUT_DIR = ROOT / "outputs"


def clean_transform_sales(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Validate, clean, and enrich raw transactions."""
    required = {
        "Transaction_ID", "Date", "Customer_ID", "Region", "Product",
        "Quantity", "Unit_Price", "Unit_Cost",
    }
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    sales = raw.copy()
    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")
    duplicate_rows = int(sales.duplicated("Transaction_ID").sum())
    missing_regions = int(sales["Region"].isna().sum())
    invalid_quantity = int((sales["Quantity"] <= 0).sum())
    invalid_price = int((sales["Unit_Price"] <= 0).sum())

    sales = sales.drop_duplicates("Transaction_ID", keep="first")
    sales = sales.loc[
        sales["Date"].notna()
        & sales["Customer_ID"].notna()
        & (sales["Quantity"] > 0)
        & (sales["Unit_Price"] > 0)
        & (sales["Unit_Cost"] >= 0)
    ].copy()
    sales["Region"] = sales["Region"].fillna("Unknown")
    sales["Revenue"] = sales["Quantity"] * sales["Unit_Price"]
    sales["Cost"] = sales["Quantity"] * sales["Unit_Cost"]
    sales["Profit"] = sales["Revenue"] - sales["Cost"]
    sales["Month"] = sales["Date"].dt.strftime("%Y-%m")
    sales = sales.sort_values(["Date", "Transaction_ID"]).reset_index(drop=True)

    report = {
        "raw_rows": len(raw),
        "duplicate_transaction_ids": duplicate_rows,
        "missing_regions_imputed": missing_regions,
        "invalid_quantity_rows": invalid_quantity,
        "invalid_price_rows": invalid_price,
        "clean_rows": len(sales),
        "rows_removed": len(raw) - len(sales),
    }
    return sales, report


def execute_sql_reports(sales: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Load the clean fact table into SQLite and execute versioned SQL reports."""
    with sqlite3.connect(":memory:") as connection:
        sales.to_sql("sales", connection, index=False, if_exists="replace")
        return {
            name: pd.read_sql_query((ROOT / "sql" / filename).read_text(), connection)
            for name, filename in {
                "monthly_financials": "monthly_financials.sql",
                "customer_churn": "customer_churn.sql",
                "dimension_summary": "dimension_summary.sql",
            }.items()
        }


def create_summary(
    sales: pd.DataFrame, reports: dict[str, pd.DataFrame]
) -> dict[str, object]:
    monthly = reports["monthly_financials"]
    churn = reports["customer_churn"]
    dimension = reports["dimension_summary"]
    total_revenue = float(sales["Revenue"].sum())
    total_profit = float(sales["Profit"].sum())
    weighted_churn = 100 * churn["Churned_Users"].sum() / churn["Previous_Users"].sum()
    region_summary = sales.groupby("Region", as_index=False)["Revenue"].sum()
    product_summary = sales.groupby("Product", as_index=False)["Profit"].sum()

    return {
        "months": int(sales["Month"].nunique()),
        "unique_customers": int(sales["Customer_ID"].nunique()),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin_pct": round(100 * total_profit / total_revenue, 2),
        "weighted_churn_rate_pct": round(float(weighted_churn), 2),
        "peak_revenue_month": str(monthly.loc[monthly["Revenue"].idxmax(), "Month"]),
        "highest_churn_month": str(churn.loc[churn["Churn_Rate_Pct"].idxmax(), "Month"]),
        "top_region_by_revenue": str(region_summary.loc[region_summary["Revenue"].idxmax(), "Region"]),
        "top_product_by_profit": str(product_summary.loc[product_summary["Profit"].idxmax(), "Product"]),
        "dimension_rows": len(dimension),
    }


def save_dashboard(
    sales: pd.DataFrame, reports: dict[str, pd.DataFrame], output_path: Path
) -> None:
    """Create a reproducible executive dashboard image."""
    monthly = reports["monthly_financials"]
    churn = reports["customer_churn"]
    by_region = sales.groupby("Region")["Revenue"].sum().sort_values()
    by_product = sales.groupby("Product")["Profit"].sum().sort_values()

    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(14, 9))
    figure.suptitle("Sales Performance Executive Dashboard", fontsize=20, weight="bold")

    axes[0, 0].plot(monthly["Month"], monthly["Revenue"], marker="o", color="#2563eb")
    axes[0, 0].set_title("Monthly Revenue")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].set_ylabel("Revenue")

    axes[0, 1].plot(churn["Month"], churn["Churn_Rate_Pct"], marker="o", color="#dc2626")
    axes[0, 1].set_title("Customer Churn (previous-month base)")
    axes[0, 1].tick_params(axis="x", rotation=45)
    axes[0, 1].set_ylabel("Churn rate (%)")

    by_region.plot.barh(ax=axes[1, 0], color="#0f766e")
    axes[1, 0].set_title("Revenue by Region")
    axes[1, 0].set_xlabel("Revenue")
    axes[1, 0].set_ylabel("")

    by_product.plot.barh(ax=axes[1, 1], color="#7c3aed")
    axes[1, 1].set_title("Profit by Product")
    axes[1, 1].set_xlabel("Profit")
    axes[1, 1].set_ylabel("")

    figure.tight_layout(rect=(0, 0, 1, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def main() -> dict[str, object]:
    raw = write_synthetic_sales(RAW_DATA)
    sales, validation = clean_transform_sales(raw)
    reports = execute_sql_reports(sales)
    summary = create_summary(sales, reports)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sales.to_csv(OUTPUT_DIR / "clean_sales.csv", index=False)
    for name, report in reports.items():
        report.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    (OUTPUT_DIR / "validation_report.json").write_text(
        json.dumps(validation, indent=2) + "\n"
    )
    (OUTPUT_DIR / "executive_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    dashboard_path = OUTPUT_DIR / "executive_dashboard.png"
    save_dashboard(sales, reports, dashboard_path)
    save_dashboard(sales, reports, ROOT / "tableau_dashboard.png")

    print(json.dumps({"validation": validation, "summary": summary}, indent=2))
    return summary


if __name__ == "__main__":
    main()
