"""Flask application factory and dashboard route."""

from pathlib import Path

from flask import Flask, render_template, request

from sales_explorer.data import filter_sales, get_regions, load_sales, summarize_sales


def create_app(csv_path: Path | None = None) -> Flask:
    """Create the web application, optionally using a custom sales CSV path."""
    app = Flask(__name__)
    source_path = csv_path or Path(__file__).resolve().parent.parent / "messy_sales.csv"
    sales = load_sales(source_path)
    headers = list(sales[0].keys()) if sales else []

    @app.get("/")
    def index():
        """Render the dashboard with optional region and text filters."""
        selected_region = request.args.get("region", "").strip()
        search_query = request.args.get("q", "").strip()
        matching_sales = filter_sales(sales, selected_region, search_query)

        return render_template(
            "index.html",
            headers=headers,
            sales=matching_sales,
            regions=get_regions(sales),
            selected_region=selected_region,
            search_query=search_query,
            summary=summarize_sales(matching_sales),
            total_records=len(sales),
        )

    return app
