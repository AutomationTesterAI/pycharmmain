"""Tests for weather API response parsing and error handling."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from weather_app.weather import (
    FORECAST_DAYS,
    FORECAST_URL,
    GEOCODING_URL,
    WeatherServiceError,
    get_weather,
    get_recommendations,
    weather_description,
    weather_visual,
)


class WeatherServiceTests(unittest.TestCase):
    def setUp(self):
        self.geocoding_response = {
            "results": [
                {
                    "name": "Luton",
                    "country": "United Kingdom",
                    "latitude": 51.88,
                    "longitude": -0.42,
                }
            ]
        }
        self.forecast_response = {
            "timezone": "Europe/London",
            "current": {
                "time": "2026-06-01T14:35",
                "temperature_2m": 14.2,
                "apparent_temperature": 13.1,
                "relative_humidity_2m": 68,
                "weather_code": 2,
                "wind_speed_10m": 10.4,
            },
            "daily": {
                "time": [f"2026-06-{day:02}" for day in range(1, 6)],
                "weather_code": [0, 1, 2, 3, 61],
                "temperature_2m_max": [20, 21, 19, 18, 16],
                "temperature_2m_min": [11, 12, 10, 9, 8],
                "precipitation_sum": [0, 0, 0.1, 1.2, 4.0],
            },
            "hourly": {
                "time": [
                    (datetime(2026, 6, 1) + timedelta(hours=hour)).isoformat(
                        timespec="minutes"
                    )
                    for hour in range(FORECAST_DAYS * 24)
                ],
                "temperature_2m": [15] * (FORECAST_DAYS * 24),
                "apparent_temperature": [14] * (FORECAST_DAYS * 24),
                "precipitation_probability": [0] * (FORECAST_DAYS * 24),
                "precipitation": [0] * (FORECAST_DAYS * 24),
                "weather_code": [0] * (FORECAST_DAYS * 24),
                "wind_speed_10m": [10] * (FORECAST_DAYS * 24),
            },
        }
        self.forecast_response["hourly"]["weather_code"][1] = 61

    @patch("weather_app.weather._request_json")
    def test_returns_current_conditions_and_five_day_forecast(self, request_json):
        request_json.side_effect = [
            self.geocoding_response,
            self.forecast_response,
        ]

        result = get_weather(" Luton ")

        self.assertEqual(result["name"], "Luton")
        self.assertEqual(result["current"]["description"], "Partly cloudy")
        self.assertEqual(result["current"]["theme"], "partly-cloudy")
        self.assertEqual(
            result["current"]["visual_label"],
            "A mix of sun and clouds",
        )
        self.assertEqual(result["current"]["time"], "14:35")
        self.assertIn("jacket", result["recommendations"]["clothing"])
        self.assertEqual(len(result["recommendations"]["activities"]), 2)
        self.assertEqual(result["daily"][0]["date"], "01/06/2026")
        self.assertEqual(len(result["daily"][0]["hours"]), 24)
        self.assertEqual(result["daily"][0]["hours"][1]["time"], "01:00")
        self.assertEqual(result["daily"][0]["hours"][1]["theme"], "rainy")
        self.assertEqual(len(result["daily"]), FORECAST_DAYS)
        self.assertEqual(request_json.call_args_list[0].args[0], GEOCODING_URL)
        self.assertEqual(request_json.call_args_list[1].args[0], FORECAST_URL)
        self.assertEqual(
            request_json.call_args_list[1].args[1]["forecast_days"],
            FORECAST_DAYS,
        )
        self.assertIn("precipitation_probability", request_json.call_args_list[1].args[1]["hourly"])

    @patch("weather_app.weather._request_json")
    def test_reports_location_not_found(self, request_json):
        request_json.return_value = {"results": []}

        with self.assertRaisesRegex(WeatherServiceError, "No location was found"):
            get_weather("Unknown Place")

    def test_rejects_empty_location(self):
        with self.assertRaisesRegex(WeatherServiceError, "Enter a town or city"):
            get_weather(" ")

    def test_unknown_weather_code_has_fallback_description(self):
        self.assertEqual(weather_description(999), "Unknown conditions")

    def test_selects_sunny_rainy_and_stormy_illustrations(self):
        self.assertEqual(weather_visual(0)["theme"], "sunny")
        self.assertEqual(weather_visual(61)["theme"], "rainy")
        self.assertEqual(weather_visual(61)["icon"], "☂️")
        self.assertEqual(weather_visual(61)["visual_label"], "Bring an umbrella")
        self.assertEqual(weather_visual(95)["theme"], "stormy")

    def test_recommendations_match_weather_and_temperature(self):
        rainy = get_recommendations(18, 61)
        self.assertIn("umbrella", rainy["clothing"])
        self.assertEqual(len(rainy["activities"]), 2)

        hot_and_sunny = get_recommendations(28, 0)
        self.assertIn("breathable", hot_and_sunny["clothing"])
        self.assertEqual(len(hot_and_sunny["activities"]), 2)

    @patch("weather_app.weather._request_json")
    def test_rejects_forecast_with_missing_days(self, request_json):
        response = dict(self.forecast_response)
        response["daily"] = dict(self.forecast_response["daily"])
        response["daily"]["time"] = response["daily"]["time"][:4]
        request_json.side_effect = [self.geocoding_response, response]

        with self.assertRaisesRegex(WeatherServiceError, "all 5 forecast days"):
            get_weather("Luton")


if __name__ == "__main__":
    unittest.main()
