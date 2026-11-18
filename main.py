import csv
import html
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import webbrowser


HOST = "127.0.0.1"
PORT = 8000


def read_sales_file():
    """Load the sales records from the CSV file next to this program."""
    csv_path = Path(__file__).with_name("messy_sales.csv")
    with csv_path.open(mode="r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def clean_text(value):
    """Remove extra spaces around a value and make missing values safe to display."""
    return (value or "").strip()


def get_region(sale):
    """Normalize region names so spacing and capitalization don't split a region."""
    region = clean_text(sale.get("Region"))
    return region.title() if region else "Unknown region"


def escape(value):
    """Escape CSV or user-provided text before placing it in HTML."""
    return html.escape(str(value), quote=True)


def render_page(sales, selected_region="", search_term=""):
    """Build the page, summary, filter controls, and table of matching records."""
    regions = sorted({get_region(sale) for sale in sales})
    search_key = search_term.casefold()

    # Apply both filters to the records shown in the table and summary.
    matching_sales = [
        sale
        for sale in sales
        if (not selected_region or get_region(sale) == selected_region)
        and (
            not search_key
            or any(
                search_key in clean_text(sale.get(field)).casefold()
                for field in ("Product", "Salesperson", "Order_ID", "Category")
            )
        )
    ]

    region_counts = Counter(get_region(sale) for sale in matching_sales)
    product_counts = Counter(
        clean_text(sale.get("Product")).title() or "Unknown product"
        for sale in matching_sales
    )

    # Build option and summary markup from the CSV values using HTML escaping.
    region_options = ['<option value="">All regions</option>']
    for region in regions:
        selected = " selected" if region == selected_region else ""
        region_options.append(
            f'<option value="{escape(region)}"{selected}>{escape(region)}</option>'
        )

    region_summary = "".join(
        f"<li><span>{escape(region)}</span><strong>{count}</strong></li>"
        for region, count in sorted(region_counts.items())
    ) or "<li>No matching records</li>"
    product_summary = "".join(
        f"<li><span>{escape(product)}</span><strong>{count}</strong></li>"
        for product, count in sorted(product_counts.items())
    ) or "<li>No matching records</li>"

    headers = list(sales[0].keys()) if sales else []
    table_header = "".join(f"<th>{escape(field)}</th>" for field in headers)
    table_rows = []
    for sale in matching_sales:
        cells = "".join(
            f"<td>{escape(clean_text(sale.get(field)) or '—')}</td>"
            for field in headers
        )
        table_rows.append(f"<tr>{cells}</tr>")
    table_body = "".join(table_rows) or (
        f'<tr><td class="empty" colspan="{max(len(headers), 1)}">'
        "No matching sales records.</td></tr>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sales Explorer</title>
  <style>
    :root {{ color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; }}
    body {{ margin: 0; background: #f3f6fb; color: #172033; }}
    header {{ padding: 28px max(24px, calc((100% - 1180px) / 2)); background: #173b67; color: white; }}
    header h1 {{ margin: 0 0 6px; font-size: 1.8rem; }}
    header p {{ margin: 0; color: #d7e5f5; }}
    main {{ max-width: 1180px; margin: 24px auto; padding: 0 20px; }}
    .filters, .card {{ background: white; border: 1px solid #e0e6ef; border-radius: 10px; }}
    .filters {{ display: flex; flex-wrap: wrap; align-items: end; gap: 14px; padding: 18px; }}
    label {{ display: grid; gap: 6px; font-weight: 600; }}
    input, select, button {{ box-sizing: border-box; min-height: 40px; padding: 8px 11px; border: 1px solid #bbc6d5; border-radius: 6px; font: inherit; }}
    input {{ min-width: 240px; }}
    button {{ border-color: #1d5e9e; background: #1d5e9e; color: white; font-weight: 600; cursor: pointer; }}
    button:hover {{ background: #174b7f; }}
    .reset {{ padding-bottom: 10px; color: #1d5e9e; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 20px 0; }}
    .card {{ padding: 18px; }}
    .card h2 {{ margin: 0 0 12px; font-size: 1.05rem; }}
    .total {{ color: #1d5e9e; font-size: 2rem; font-weight: 700; }}
    ul {{ margin: 0; padding: 0; list-style: none; }}
    li {{ display: flex; justify-content: space-between; gap: 12px; padding: 7px 0; border-top: 1px solid #edf0f5; }}
    .table-wrap {{ overflow-x: auto; background: white; border: 1px solid #e0e6ef; border-radius: 10px; }}
    table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
    th, td {{ padding: 11px 13px; border-bottom: 1px solid #edf0f5; text-align: left; }}
    th {{ background: #eaf0f7; color: #253c59; }}
    tbody tr:hover {{ background: #f7faff; }}
    .empty {{ padding: 24px; color: #59677a; text-align: center; }}
    .result-count {{ color: #59677a; }}
    @media (max-width: 600px) {{ main {{ margin-top: 16px; }} input {{ min-width: 0; width: 100%; }} .filters label {{ width: 100%; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Sales Explorer</h1>
    <p>Explore sales records from messy_sales.csv</p>
  </header>
  <main>
    <form class="filters" method="get" action="/">
      <label>Region
        <select name="region">{"".join(region_options)}</select>
      </label>
      <label>Search records
        <input type="search" name="q" value="{escape(search_term)}"
          placeholder="Product, salesperson, order ID, or category">
      </label>
      <button type="submit">Apply filters</button>
      <a class="reset" href="/">Clear filters</a>
    </form>

    <section class="cards" aria-label="Sales summary">
      <article class="card">
        <h2>Matching records</h2>
        <div class="total">{len(matching_sales)}</div>
        <div class="result-count">of {len(sales)} total records</div>
      </article>
      <article class="card">
        <h2>Records by region</h2>
        <ul>{region_summary}</ul>
      </article>
      <article class="card">
        <h2>Records by product</h2>
        <ul>{product_summary}</ul>
      </article>
    </section>

    <h2>Sales records</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>{table_header}</tr></thead>
        <tbody>{"".join(table_rows) if table_rows else table_body}</tbody>
      </table>
    </div>
  </main>
</body>
</html>"""


class SalesRequestHandler(BaseHTTPRequestHandler):
    """Serve the sales dashboard and its region/search filters."""

    def do_GET(self):
        """Render the dashboard using filters from the URL query string."""
        request = urlsplit(self.path)
        if request.path != "/":
            self.send_error(404, "Page not found")
            return

        query = parse_qs(request.query, keep_blank_values=True)
        region = query.get("region", [""])[0].strip()
        search_term = query.get("q", [""])[0].strip()
        page = render_page(self.server.sales, region, search_term)
        body = page.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        """Keep the local server console readable by hiding routine page requests."""


def main():
    """Start the local web server and open the dashboard in the browser."""
    sales = read_sales_file()
    server = ThreadingHTTPServer((HOST, PORT), SalesRequestHandler)
    server.sales = sales
    url = f"http://{HOST}:{PORT}"
    print(f"Loaded {len(sales)} sales records.")
    print(f"Sales Explorer is running at {url}")
    print("Press Ctrl+C to stop the server.")
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSales Explorer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
