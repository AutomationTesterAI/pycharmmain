"""Tests for the Weather Dashboard routes and saved-location behavior."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from weather_app.app import create_app
from weather_app.config import DEFAULT_LOCATION
from weather_app.weather import WeatherServiceError


class WeatherDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temporary_directory.name) / "config.json"
        self.app = create_app(self.config_path)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    @patch("weather_app.app.get_weather")
    def test_first_run_uses_and_saves_default_location(self, get_weather):
        get_weather.return_value = None
        self.assertEqual(self.app.config["LAST_LOCATION"], DEFAULT_LOCATION)
        self.assertEqual(
            json.loads(self.config_path.read_text(encoding="utf-8")),
            {"last_location": DEFAULT_LOCATION},
        )

    @patch("weather_app.app.get_weather")
    def test_dashboard_displays_weather(self, get_weather):
        get_weather.return_value = {
            "name": "Luton",
            "country": "United Kingdom",
            "timezone": "Europe/London",
            "current": {
                "time": "14:35",
                "temperature": 14.2,
                "feels_like": 13.1,
                "humidity": 68,
                "wind_speed": 10.4,
                "description": "Partly cloudy",
                "theme": "partly-cloudy",
                "icon": "🌤️",
                "visual_label": "A mix of sun and clouds",
            },
            "recommendations": {
                "clothing": "Wear comfortable layers and bring a light jacket.",
                "activities": ["Take a park walk", "Visit a local café"],
            },
            "daily": [
                {
                    "date": f"{day:02}/06/2026",
                    "description": "Clear sky",
                    "theme": "sunny",
                    "icon": "☀️",
                    "high": 20,
                    "low": 10,
                    "precipitation": 0,
                    "hours": [
                        {
                            "time": "14:00",
                            "temperature": 18,
                            "feels_like": 18,
                            "rain_chance": 0,
                            "precipitation": 0,
                            "wind_speed": 5,
                            "description": "Clear sky",
                            "theme": "sunny",
                            "icon": "☀️",
                            "visual_label": "Bright and sunny",
                        },
                        {
                            "time": "15:00",
                            "temperature": 17,
                            "feels_like": 17,
                            "rain_chance": 70,
                            "precipitation": 1.2,
                            "wind_speed": 12,
                            "description": "Slight rain",
                            "theme": "rainy",
                            "icon": "☂️",
                            "visual_label": "Bring an umbrella",
                        },
                    ],
                }
                for day in range(1, 6)
            ],
        }

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Luton, United Kingdom", response.data)
        self.assertIn(b"14.2", response.data)
        self.assertIn(b"Local time: 14:35", response.data)
        self.assertIn(b"01/06/2026", response.data)
        self.assertIn(b"5-day forecast", response.data)
        self.assertIn(b"weather-illustration--partly-cloudy", response.data)
        self.assertIn(b"A mix of sun and clouds", response.data)
        self.assertIn(b"Click to view hourly details", response.data)
        self.assertIn(b"hour-card--sunny", response.data)
        self.assertIn(b"hour-card--rainy", response.data)
        self.assertIn(b"Rain chance", response.data)
        self.assertIn(b"What to wear &amp; do", response.data)
        self.assertIn(b"Wear comfortable layers", response.data)
        self.assertIn(b"Take a park walk", response.data)
        self.assertIn(b"Visit a local caf", response.data)

    @patch("weather_app.app.get_weather")
    def test_search_saves_location_and_redirects(self, get_weather):
        get_weather.return_value = None

        response = self.client.post(
            "/",
            data={"location": "  Cambridge  "},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.app.config["LAST_LOCATION"], "Cambridge")
        self.assertEqual(
            json.loads(self.config_path.read_text(encoding="utf-8")),
            {"last_location": "Cambridge"},
        )
        get_weather.assert_called_with("Cambridge")

    @patch("weather_app.app.get_weather")
    def test_empty_search_does_not_replace_saved_location(self, get_weather):
        get_weather.return_value = None

        response = self.client.post("/", data={"location": "  "})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Enter a town or city before searching.", response.data)
        self.assertEqual(self.app.config["LAST_LOCATION"], DEFAULT_LOCATION)

    @patch("weather_app.app.get_weather")
    def test_weather_error_is_shown_on_dashboard(self, get_weather):
        get_weather.side_effect = WeatherServiceError("Weather service unavailable.")

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Weather service unavailable.", response.data)
        self.assertIn(b"Weather is not available right now", response.data)


if __name__ == "__main__":
    unittest.main()
