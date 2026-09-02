"""Thin client around the local air-quality sensor's HTTP API."""
import logging

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import SensorReadingRaw

logger = logging.getLogger("airquality.sensor")


class SensorUnavailableError(Exception):
    """Raised when the sensor cannot be reached or returns invalid data."""


def fetch_current_reading() -> SensorReadingRaw:
    """GET the sensor's /measures/current endpoint and validate the payload.

    Raises SensorUnavailableError on any network error, non-2xx response,
    or malformed JSON. Callers (the collector) are expected to catch this
    and log + retry on the next scheduled tick rather than crashing.
    """
    settings = get_settings()
    try:
        response = httpx.get(
            settings.sensor_url, timeout=settings.sensor_request_timeout_seconds
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        raise SensorUnavailableError(f"Sensor request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise SensorUnavailableError(
            f"Sensor returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        raise SensorUnavailableError(f"Could not reach sensor: {exc}") from exc
    except ValueError as exc:  # invalid JSON
        raise SensorUnavailableError(f"Sensor returned invalid JSON: {exc}") from exc

    try:
        return SensorReadingRaw.model_validate(payload)
    except ValidationError as exc:
        raise SensorUnavailableError(f"Sensor payload failed validation: {exc}") from exc
