import tempfile
import unittest
from pathlib import Path

import pandas as pd

from generate_data import generate_synthetic_sales
from run_pipeline import clean_transform_sales, execute_sql_reports


class SalesPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = generate_synthetic_sales(seed=42)
        cls.sales, cls.validation = clean_transform_sales(cls.raw)
        cls.reports = execute_sql_reports(cls.sales)

    def test_generator_is_deterministic_and_defects_are_cleaned(self):
        second = generate_synthetic_sales(seed=42)
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "first.csv"
            second_path = Path(directory) / "second.csv"
            self.raw.to_csv(first_path, index=False)
            second.to_csv(second_path, index=False)
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

        self.assertEqual(self.validation["duplicate_transaction_ids"], 15)
        self.assertEqual(self.validation["missing_regions_imputed"], 120)
        self.assertEqual(self.validation["invalid_quantity_rows"], 10)
        self.assertEqual(self.validation["invalid_price_rows"], 10)
        self.assertEqual(self.validation["rows_removed"], 35)
        self.assertFalse(self.sales["Region"].isna().any())
        self.assertTrue((self.sales["Quantity"] > 0).all())
        self.assertTrue((self.sales["Unit_Price"] > 0).all())

    def test_sql_churn_matches_customer_set_arithmetic(self):
        monthly_sets = {
            month: set(group["Customer_ID"])
            for month, group in self.sales.groupby("Month")
        }
        churn = self.reports["customer_churn"].set_index("Month")
        months = sorted(monthly_sets)
        self.assertEqual(list(churn.index), months[1:])

        for previous_month, current_month in zip(months, months[1:]):
            previous = monthly_sets[previous_month]
            current = monthly_sets[current_month]
            row = churn.loc[current_month]
            self.assertEqual(int(row["Previous_Users"]), len(previous))
            self.assertEqual(int(row["Retained_Users"]), len(previous & current))
            self.assertEqual(int(row["Churned_Users"]), len(previous - current))
            self.assertEqual(int(row["New_Users"]), len(current - previous))

        self.assertTrue(churn["Churn_Rate_Pct"].between(0, 100).all())
        self.assertGreater(churn["Churn_Rate_Pct"].max(), 0)

    def test_sql_financial_totals_match_clean_fact_table(self):
        monthly = self.reports["monthly_financials"]
        self.assertAlmostEqual(monthly["Revenue"].sum(), self.sales["Revenue"].sum(), places=2)
        self.assertAlmostEqual(monthly["Cost"].sum(), self.sales["Cost"].sum(), places=2)
        self.assertAlmostEqual(monthly["Profit"].sum(), self.sales["Profit"].sum(), places=2)
        self.assertTrue(pd.isna(monthly.iloc[0]["Revenue_Growth_Pct"]))


if __name__ == "__main__":
    unittest.main()
