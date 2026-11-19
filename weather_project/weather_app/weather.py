"""Open-Meteo geocoding and five-day forecast client."""

import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 5
REQUEST_TIMEOUT_SECONDS = 10


class WeatherServiceError(Exception):
    """Raised when a location or weather forecast cannot be retrieved."""


WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

WEATHER_VISUALS = {
    "sunny": {"icon": "☀️", "visual_label": "Bright and sunny"},
    "partly-cloudy": {"icon": "🌤️", "visual_label": "A mix of sun and clouds"},
    "cloudy": {"icon": "☁️", "visual_label": "Cloudy skies"},
    "foggy": {"icon": "🌫️", "visual_label": "Misty and foggy"},
    "rainy": {"icon": "☂️", "visual_label": "Bring an umbrella"},
    "snowy": {"icon": "❄️", "visual_label": "Snowy weather"},
    "stormy": {"icon": "⛈️", "visual_label": "Stormy skies"},
    "unknown": {"icon": "🌡️", "visual_label": "Current weather"},
}


def _request_json(url: str, parameters: dict[str, str | int]) -> dict[str, Any]:
    """Request and decode one JSON response from Open-Meteo."""
    request_url = f"{url}?{urlencode(parameters)}"
    try:
        with urlopen(request_url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data: Any = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise WeatherServiceError(
            f"The weather service returned HTTP {error.code}."
        ) from error
    except (URLError, TimeoutError) as error:
        raise WeatherServiceError(
            "Could not connect to the weather service. Check your internet "
            "connection and try again."
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WeatherServiceError(
            "The weather service returned an unreadable response."
        ) from error

    if not isinstance(data, dict):
        raise WeatherServiceError("The weather service returned invalid data.")
    if data.get("error"):
        raise WeatherServiceError(
            str(data.get("reason", "The weather service could not process the request."))
        )
    return data


def weather_description(code: int) -> str:
    """Translate a WMO weather code into a short human-readable description."""
    return WEATHER_DESCRIPTIONS.get(code, "Unknown conditions")


def weather_visual(code: int) -> dict[str, str]:
    """Choose a dashboard theme and illustration for a WMO weather code."""
    if code in {0, 1}:
        theme = "sunny"
    elif code == 2:
        theme = "partly-cloudy"
    elif code == 3:
        theme = "cloudy"
    elif code in {45, 48}:
        theme = "foggy"
    elif code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        theme = "rainy"
    elif code in {71, 73, 75, 77, 85, 86}:
        theme = "snowy"
    elif code in {95, 96, 99}:
        theme = "stormy"
    else:
        theme = "unknown"
    return {"theme": theme, **WEATHER_VISUALS[theme]}


def get_recommendations(temperature: float, code: int) -> dict[str, Any]:
    """Suggest practical clothing and two activities for the current weather."""
    theme = weather_visual(code)["theme"]
    if theme == "stormy":
        clothing = "Stay indoors during thunderstorms; keep a waterproof layer nearby."
        activities = ["Enjoy a film or a favourite book indoors", "Try a café, museum, or indoor class"]
    elif theme == "snowy":
        clothing = "Wear a warm insulated coat, gloves, a hat, and shoes with good grip."
        activities = ["Take a careful walk to enjoy the snowy scenery", "Relax with a warm drink at a cosy café"]
    elif theme == "rainy":
        clothing = "Take a waterproof jacket and umbrella; choose shoes that handle wet paths."
        activities = ["Visit a museum, gallery, or cinema", "Enjoy a relaxed café or indoor hobby"]
    elif theme == "foggy":
        clothing = "Wear a light jacket and something reflective if you will be outdoors."
        activities = ["Choose a familiar, well-lit walking route", "Spend time at a café or local gallery"]
    elif temperature <= 8:
        clothing = "Layer up with a warm coat, and consider a scarf and gloves."
        activities = ["Take a brisk walk somewhere sheltered", "Enjoy a warm drink or an indoor activity"]
    elif temperature <= 15:
        clothing = "Wear a light-to-medium jacket over comfortable layers."
        activities = ["Go for a comfortable walk in a nearby park", "Explore a local market or café"]
    elif temperature >= 25:
        clothing = "Choose light, breathable clothing, sunglasses, and sun protection."
        activities = ["Enjoy an early or late-day outdoor walk", "Relax in a shaded park or outdoor café"]
    elif theme == "sunny":
        clothing = "Wear comfortable light layers and bring sunglasses."
        activities = ["Enjoy a walk or picnic in a local park", "Explore the town or an outdoor market"]
    else:
        clothing = "Wear comfortable layers and bring a light jacket in case it cools down."
        activities = ["Take a walk in a local park", "Explore a nearby market, garden, or café"]

    return {"clothing": clothing, "activities": activities}


def get_weather(location: str) -> dict[str, Any]:
    """Find a location and return its current conditions and five-day forecast."""
    normalized_location = location.strip()
    if not normalized_location:
        raise WeatherServiceError("Enter a town or city to see its weather.")

    geocoding_data = _request_json(
        GEOCODING_URL,
        {"name": normalized_location, "count": 1, "language": "en", "format": "json"},
    )
    results = geocoding_data.get("results")
    if not isinstance(results, list) or not results:
        raise WeatherServiceError(
            f"No location was found for “{normalized_location}”. Try another name."
        )

    place = results[0]
    if not isinstance(place, dict):
        raise WeatherServiceError("The location service returned invalid data.")

    try:
        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
        place_name = str(place["name"])
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherServiceError(
            "The location service returned incomplete location details."
        ) from error

    forecast_data = _request_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "weather_code,wind_speed_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum"
            ),
            "hourly": (
                "temperature_2m,apparent_temperature,precipitation_probability,"
                "precipitation,weather_code,wind_speed_10m"
            ),
            "forecast_days": FORECAST_DAYS,
            "timezone": "auto",
        },
    )

    current = forecast_data.get("current")
    daily = forecast_data.get("daily")
    hourly = forecast_data.get("hourly")
    if (
        not isinstance(current, dict)
        or not isinstance(daily, dict)
        or not isinstance(hourly, dict)
    ):
        raise WeatherServiceError("The weather service returned incomplete forecast data.")

    try:
        hourly_by_date: dict[str, list[dict[str, Any]]] = {}
        hourly_values = zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["apparent_temperature"],
            hourly["precipitation_probability"],
            hourly["precipitation"],
            hourly["weather_code"],
            hourly["wind_speed_10m"],
            strict=True,
        )
        for (
            timestamp,
            temperature,
            feels_like,
            rain_chance,
            precipitation,
            code,
            wind,
        ) in hourly_values:
            hour_datetime = datetime.fromisoformat(timestamp)
            weather_code = int(code)
            hourly_by_date.setdefault(hour_datetime.date().isoformat(), []).append(
                {
                    "time": hour_datetime.strftime("%H:%M"),
                    "temperature": temperature,
                    "feels_like": feels_like,
                    "rain_chance": rain_chance,
                    "precipitation": precipitation,
                    "wind_speed": wind,
                    "description": weather_description(weather_code),
                    **weather_visual(weather_code),
                }
            )

        daily_forecast = [
            {
                "iso_date": date,
                "date": datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y"),
                "description": weather_description(int(code)),
                **weather_visual(int(code)),
                "high": high,
                "low": low,
                "precipitation": precipitation,
                "hours": hourly_by_date.get(date, []),
            }
            for date, code, high, low, precipitation in zip(
                daily["time"],
                daily["weather_code"],
                daily["temperature_2m_max"],
                daily["temperature_2m_min"],
                daily["precipitation_sum"],
                strict=True,
            )
        ]
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherServiceError(
            f"The weather service returned incomplete daily or hourly forecast data; "
            f"expected all {FORECAST_DAYS} forecast days."
        ) from error

    if len(daily_forecast) != FORECAST_DAYS:
        raise WeatherServiceError(
            f"The weather service did not return all {FORECAST_DAYS} forecast days."
        )
    if any(not day["hours"] for day in daily_forecast):
        raise WeatherServiceError(
            "The weather service returned no hourly forecast for one or more days."
        )

    try:
        weather_code = int(current["weather_code"])
        current_conditions = {
            "time": datetime.fromisoformat(str(current["time"])).strftime("%H:%M"),
            "temperature": current["temperature_2m"],
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "description": weather_description(weather_code),
            **weather_visual(weather_code),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherServiceError(
            "The weather service returned incomplete current conditions."
        ) from error

    return {
        "name": place_name,
        "country": str(place.get("country", "")),
        "timezone": str(forecast_data.get("timezone", "")),
        "current": current_conditions,
        "recommendations": get_recommendations(
            float(current_conditions["temperature"]),
            weather_code,
        ),
        "daily": daily_forecast,
    }
