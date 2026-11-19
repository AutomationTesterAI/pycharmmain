"""Read and save the last location used by the dashboard."""

import json
from pathlib import Path
from typing import Any


DEFAULT_LOCATION = "Luton"


class ConfigurationError(Exception):
    """Raised when the saved application configuration cannot be used."""


def load_last_location(config_path: Path) -> str:
    """Read the saved location, creating a default config file on first run."""
    if not config_path.exists():
        save_last_location(config_path, DEFAULT_LOCATION)
        return DEFAULT_LOCATION

    try:
        config: Any = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"Could not read the location settings at {config_path}: {error}"
        ) from error

    location = config.get("last_location") if isinstance(config, dict) else None
    if not isinstance(location, str) or not location.strip():
        raise ConfigurationError(
            f"The config file {config_path} must contain a non-empty "
            "'last_location' value."
        )
    return location.strip()


def save_last_location(config_path: Path, location: str) -> None:
    """Persist the last searched location in a small JSON config file."""
    normalized_location = location.strip()
    if not normalized_location:
        raise ValueError("A location is required.")

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = config_path.with_suffix(config_path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps({"last_location": normalized_location}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(config_path)
    except OSError as error:
        raise ConfigurationError(
            f"Could not save the location settings at {config_path}: {error}"
        ) from error
