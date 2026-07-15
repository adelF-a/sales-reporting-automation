"""Generate a deterministic, imperfect sales dataset for the reporting pipeline."""

from pathlib import Path

import numpy as np
import pandas as pd


PRODUCTS = {
    "Enterprise License": (1200.0, 350.0),
    "Consulting Service": (180.0, 105.0),
    "Basic Support": (300.0, 70.0),
    "Premium Maintenance": (650.0, 220.0),
}
REGIONS = ["North America", "Europe", "Asia-Pacific", "Latin America"]


def generate_synthetic_sales(seed: int = 42) -> pd.DataFrame:
    """Return 18 months of sales with a realistic customer lifecycle.

    The generated defects are deliberate and deterministic: 120 missing regions,
    10 zero quantities, 10 negative prices, and 15 duplicate transaction IDs.
    """
    rng = np.random.default_rng(seed)
    months = pd.period_range("2023-01", periods=18, freq="M")
    customer_pool = np.array([f"CUST-{i:04d}" for i in range(1, 801)])

    active = set(rng.choice(customer_pool, size=220, replace=False))
    unseen = set(customer_pool) - active
    rows: list[dict[str, object]] = []
    transaction_number = 1

    for month_number, month in enumerate(months):
        if month_number:
            retention_probability = 0.86 + 0.03 * np.cos(month_number / 2)
            active = {
                customer
                for customer in sorted(active)
                if rng.random() < retention_probability
            }
            acquisition_count = min(
                len(unseen), max(5, int(rng.normal(loc=26, scale=5)))
            )
            acquired = set(
                rng.choice(sorted(unseen), size=acquisition_count, replace=False)
            )
            active.update(acquired)
            unseen.difference_update(acquired)

        month_start = month.to_timestamp()
        days_in_month = month.days_in_month
        for customer in sorted(active):
            transaction_count = int(rng.choice([1, 2, 3], p=[0.68, 0.25, 0.07]))
            region = str(rng.choice(REGIONS))
            for _ in range(transaction_count):
                product = str(rng.choice(list(PRODUCTS)))
                list_price, unit_cost = PRODUCTS[product]
                unit_price = round(list_price * rng.uniform(0.90, 1.08), 2)
                rows.append(
                    {
                        "Transaction_ID": f"TRX-{transaction_number:06d}",
                        "Date": month_start
                        + pd.Timedelta(days=int(rng.integers(0, days_in_month))),
                        "Customer_ID": customer,
                        "Region": region,
                        "Product": product,
                        "Quantity": int(rng.integers(1, 8)),
                        "Unit_Price": unit_price,
                        "Unit_Cost": unit_cost,
                    }
                )
                transaction_number += 1

    sales = pd.DataFrame(rows)

    missing_region_rows = rng.choice(sales.index, size=120, replace=False)
    remaining = sales.index.difference(missing_region_rows)
    zero_quantity_rows = rng.choice(remaining, size=10, replace=False)
    remaining = remaining.difference(zero_quantity_rows)
    negative_price_rows = rng.choice(remaining, size=10, replace=False)

    sales.loc[missing_region_rows, "Region"] = np.nan
    sales.loc[zero_quantity_rows, "Quantity"] = 0
    sales.loc[negative_price_rows, "Unit_Price"] *= -1

    duplicates = sales.sample(n=15, random_state=seed)
    return pd.concat([sales, duplicates], ignore_index=True)


def write_synthetic_sales(
    output_path: str | Path = "data/raw_sales_data.csv", seed: int = 42
) -> pd.DataFrame:
    """Generate the dataset and write it to ``output_path``."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sales = generate_synthetic_sales(seed=seed)
    sales.to_csv(output_path, index=False)
    return sales


if __name__ == "__main__":
    generated = write_synthetic_sales()
    print(f"Generated {len(generated):,} rows in data/raw_sales_data.csv")
