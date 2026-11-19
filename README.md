# Sales Explorer

A small local web application for exploring the records in `messy_sales.csv`.
It provides a searchable sales table and record counts by region and product.

## Requirements

- Python 3.10 or later
- The `messy_sales.csv` file in the project root

## Setup

From the project directory, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the application dependency:

```powershell
python -m pip install -r requirements.txt
```

## Run

Start the app and open its local address in your browser:

```powershell
python main.py
```

The default address is <http://127.0.0.1:8000>. Stop the server with `Ctrl+C`.
To choose a different port or skip opening a browser:

```powershell
python main.py --port 8080 --no-browser
```

The CSV file is loaded when the app starts. Restart the app after changing the
file. Region names are normalized for filtering (for example, ` Glasgow ` and
`GLASGOW` are treated as the same region).

## Project structure

```text
.
├── main.py                   # Backward-compatible script entry point
├── messy_sales.csv           # Input data
├── requirements.txt          # Python dependencies
└── sales_explorer/
    ├── __init__.py
    ├── cli.py                 # Command-line options and server startup
    ├── data.py                # CSV loading, filtering, and summary functions
    ├── web.py                 # Flask application factory and route
    ├── static/
    │   └── style.css          # Dashboard styles
    └── templates/
        └── index.html         # Dashboard template
```

## Tests

Run the test suite from the project directory:

```powershell
python -m unittest discover -s tests -v
```

## Notes

The built-in Flask development server is intended for local use and development,
not public production hosting. For production deployment, use a production WSGI
server and configure the host and port for the target environment.
