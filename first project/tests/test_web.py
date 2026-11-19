"""Request-level tests for the Sales Explorer dashboard."""

import unittest

from sales_explorer.web import create_app


class SalesDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app().test_client()

    def test_dashboard_shows_summary_and_all_sales(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sales Explorer", response.data)
        self.assertIn(b"22 total records", response.data)
        self.assertIn(b"ORD1001", response.data)

    def test_region_and_search_filters_are_applied(self):
        response = self.app.get("/", query_string={"region": "Glasgow", "q": "mouse"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ORD1007", response.data)
        self.assertNotIn(b"ORD1001", response.data)

    def test_no_match_has_empty_state(self):
        response = self.app.get("/", query_string={"q": "no-such-product"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No matching sales records.", response.data)


if __name__ == "__main__":
    unittest.main()
