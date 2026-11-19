"""Flask application factory and dashboard routes."""

from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from weather_app.config import (
    DEFAULT_LOCATION,
    ConfigurationError,
    load_last_location,
    save_last_location,
)
from weather_app.weather import WeatherServiceError, get_weather


def create_app(config_path: Path | None = None) -> Flask:
    """Create the dashboard app using a local last-location settings file."""
    app = Flask(__name__)
    settings_path = config_path or Path(__file__).resolve().parent.parent / "config.json"
    app.config["WEATHER_CONFIG_PATH"] = settings_path
    app.config["LAST_LOCATION"] = load_last_location(settings_path)

    @app.route("/", methods=["GET", "POST"])
    def index():
        """Display current conditions and forecast for the last-used location."""
        message = None

        if request.method == "POST":
            location = request.form.get("location", "").strip()
            if not location:
                message = "Enter a town or city before searching."
            elif len(location) > 100:
                message = "Location names must be 100 characters or fewer."
            else:
                try:
                    save_last_location(settings_path, location)
                except ConfigurationError as error:
                    message = str(error)
                else:
                    app.config["LAST_LOCATION"] = location
                    return redirect(url_for("index"))

        location = app.config["LAST_LOCATION"]
        weather = None
        try:
            weather = get_weather(location)
        except WeatherServiceError as error:
            message = str(error)

        return render_template(
            "index.html",
            location=location,
            weather=weather,
            message=message,
            forecast_days=5,
            default_location=DEFAULT_LOCATION,
        )

    return app
