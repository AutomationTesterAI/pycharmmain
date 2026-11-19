"""Tests for sales CSV loading, normalization, filtering, and summaries."""

import tempfile
import unittest
from pathlib import Path

from sales_explorer.data import (
    filter_sales,
    get_region,
    get_regions,
    load_sales,
    summarize_sales,
)


class SalesDataTests(unittest.TestCase):
    def setUp(self):
        self.sales = [
            {
                "Region": " Glasgow ",
                "Product": "Wireless Mouse",
                "Salesperson": "Aisha Khan",
                "Order_ID": "ORD1001",
                "Category": "Accessories",
            },
            {
                "Region": "GLASGOW",
                "Product": "Laptop Stand",
                "Salesperson": "Ben Fraser",
                "Order_ID": "ORD1002",
                "Category": "Accessories",
            },
            {
                "Region": "Edinburgh",
                "Product": "Wireless Mouse",
                "Salesperson": "Cara Reid",
                "Order_ID": "ORD1003",
                "Category": "Hardware",
            },
        ]

    def test_normalizes_region_names(self):
        self.assertEqual(get_region(self.sales[0]), "Glasgow")
        self.assertEqual(get_regions(self.sales), ["Edinburgh", "Glasgow"])
        self.assertEqual(get_region({"Region": "  "}), "Unknown region")

    def test_filters_by_region_and_case_insensitive_query(self):
        matches = filter_sales(self.sales, region="Glasgow", query="mouse")
        self.assertEqual([sale["Order_ID"] for sale in matches], ["ORD1001"])

    def test_searches_supported_fields(self):
        matches = filter_sales(self.sales, query="ord1002")
        self.assertEqual([sale["Product"] for sale in matches], ["Laptop Stand"])

    def test_summarizes_matching_records(self):
        summary = summarize_sales(self.sales[:2])
        self.assertEqual(summary["record_count"], 2)
        self.assertEqual(summary["region_counts"], {"Glasgow": 2})
        self.assertEqual(summary["product_counts"], {
            "Laptop Stand": 1,
            "Wireless Mouse": 1,
        })

    def test_loads_csv_with_utf8_bom(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "sales.csv"
            csv_path.write_text(
                "\ufeffRegion,Product\nGlasgow,Mouse\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_sales(csv_path),
                [{"Region": "Glasgow", "Product": "Mouse"}],
            )

    def test_rejects_csv_without_header(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "empty.csv"
            csv_path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no header row"):
                load_sales(csv_path)


if __name__ == "__main__":
    unittest.main()
