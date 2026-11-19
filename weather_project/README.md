# Weather Dashboard

A local Flask web app that looks up a location and displays its current
conditions and five-day forecast using the free Open-Meteo geocoding and weather
APIs. Expand any forecast day to see hourly temperature, feels-like temperature,
rain chance, precipitation, and wind. Weather icons and colors change with the
conditions for each hour. The dashboard also suggests weather-appropriate
clothing and two activities. No API key is required.

The app starts with **Luton** and saves the most recently searched location in
`config.json` in this folder. That file is generated locally and excluded from
version control.

## Requirements

- Python 3.10 or later
- Internet access to reach `geocoding-api.open-meteo.com` and
  `api.open-meteo.com`

## Setup

From the repository root, activate the shared virtual environment and enter
this project:

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location weather_project
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

Open <http://127.0.0.1:8001> if the browser does not open automatically. Stop
the server with `Ctrl+C`. Optional settings:

```powershell
python main.py --host 127.0.0.1 --port 8002 --no-browser
```

Search for another town or city in the form. A successful search becomes the
saved location and is shown the next time the app starts. If the weather
service is unavailable, the dashboard displays an error and keeps the saved
location. Forecast dates use `DD/MM/YYYY`, and local weather time uses the
24-hour `HH:MM` format.

## Project structure

```text
weather_project/
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── weather_app/
│   ├── __init__.py
│   ├── app.py          # Flask routes and application factory
│   ├── cli.py          # Server command-line options
│   ├── config.py       # Last-location persistence
│   ├── weather.py      # Open-Meteo API client and forecast formatting
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── index.html
└── tests/
    ├── test_app.py
    └── test_weather.py
```

## Tests

The tests mock external weather API responses, so they do not require internet
access:

```powershell
python -m unittest discover -s tests -v
```

## Data source

Weather and geocoding data are provided by
[Open-Meteo](https://open-meteo.com/). Its APIs are intended for non-commercial
use without an API key; consult the provider's terms for other use.
