import httpx
import pytest
import respx

from app.config import get_settings
from app.sensor import SensorUnavailableError, fetch_current_reading

SAMPLE_PAYLOAD = {
    "pm01": 3.73,
    "pm02": 4.2,
    "pm10": 4.2,
    "pm003Count": 847,
    "pm02Compensated": 4.18,
    "atmp": 27.98,
    "atmpCompensated": 27.98,
    "rhum": 43.74,
    "rhumCompensated": 43.74,
    "rco2": 494.43,
    "boot": 2854,
    "bootCount": 2854,
    "wifi": -64,
    "serialno": "f4cfa276b187",
    "firmware": "3.6.5-snap",
    "model": "DIY-BASIC-I-4.0PS",
}


@respx.mock
def test_fetch_current_reading_parses_valid_payload():
    settings = get_settings()
    respx.get(settings.sensor_url).mock(return_value=httpx.Response(200, json=SAMPLE_PAYLOAD))

    reading = fetch_current_reading()

    assert reading.pm02 == 4.2
    assert reading.rco2 == 494.43
    assert reading.serialno == "f4cfa276b187"


@respx.mock
def test_fetch_current_reading_ignores_unknown_extra_fields():
    settings = get_settings()
    payload = {**SAMPLE_PAYLOAD, "someFutureField": "unexpected"}
    respx.get(settings.sensor_url).mock(return_value=httpx.Response(200, json=payload))

    reading = fetch_current_reading()

    assert reading.pm02 == 4.2


@respx.mock
def test_fetch_current_reading_raises_on_http_error():
    settings = get_settings()
    respx.get(settings.sensor_url).mock(return_value=httpx.Response(500))

    with pytest.raises(SensorUnavailableError):
        fetch_current_reading()


@respx.mock
def test_fetch_current_reading_raises_on_timeout():
    settings = get_settings()
    respx.get(settings.sensor_url).mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(SensorUnavailableError):
        fetch_current_reading()


@respx.mock
def test_fetch_current_reading_raises_on_malformed_json():
    settings = get_settings()
    respx.get(settings.sensor_url).mock(
        return_value=httpx.Response(200, content=b"not json")
    )

    with pytest.raises(SensorUnavailableError):
        fetch_current_reading()


@respx.mock
def test_fetch_current_reading_handles_missing_optional_fields():
    settings = get_settings()
    respx.get(settings.sensor_url).mock(return_value=httpx.Response(200, json={"pm02": 5.0}))

    reading = fetch_current_reading()

    assert reading.pm02 == 5.0
    assert reading.rco2 is None
