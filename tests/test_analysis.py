"""Independent reconciliation checks against the prepared synthetic database."""
import csv
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AnalysisChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = sqlite3.connect(ROOT / "data" / "retail.sqlite")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_sales_counts_and_keys(self):
        with (ROOT / "data/raw/sales.csv").open(newline="", encoding="utf-8") as handle:
            raw_count = sum(1 for _ in csv.DictReader(handle))
        clean_count = self.con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        self.assertEqual(raw_count - clean_count, 5)
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_monthly_reconciles_to_detail(self):
        detail = self.con.execute("SELECT SUM(quantity * unit_price), SUM(quantity * (unit_price-unit_cost)) FROM sales").fetchone()
        grouped = self.con.execute((ROOT / "sql/01_monthly_store_category.sql").read_text(encoding="utf-8")).fetchall()
        # Group values are rounded to cents, so allow one cent per group.
        self.assertAlmostEqual(sum(row[4] for row in grouped), detail[0], delta=len(grouped) * .01)
        self.assertAlmostEqual(sum(row[5] for row in grouped), detail[1], delta=len(grouped) * .01)
        self.assertEqual(len(grouped), 12 * 3 * 5)

    def test_replenishment_math(self):
        rows = self.con.execute((ROOT / "sql/04_replenishment.sql").read_text(encoding="utf-8")).fetchall()
        self.assertGreater(len(rows), 0)
        for row in rows:
            on_hand, units_28d, reorder, shortfall = row[5], row[6], row[8], row[9]
            self.assertEqual(reorder, units_28d)  # 28-day demand and 28-day cover
            self.assertEqual(shortfall, reorder - on_hand)
            self.assertGreater(shortfall, 0)


if __name__ == "__main__":
    unittest.main()
