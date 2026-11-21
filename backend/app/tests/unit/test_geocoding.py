"""
FILE: backend/app/tests/unit/test_geocoding.py
Unit tests for reverse geocoding and the /weather/nearby endpoint.
All external HTTP calls are mocked — no live API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.external import geocoding
from app.infrastructure.external.geocoding import reverse_geocode


# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_httpx_json(payload, status=200):
    """Return a mock httpx.AsyncClient whose .get() yields payload."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload

    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture(autouse=True)
def clear_geocode_cache():
    geocoding._cache.clear()
    yield
    geocoding._cache.clear()


NOMINATIM_NEIGHBOURHOOD = {
    "address": {
        "neighbourhood": "Magodo",
        "suburb": "Magodo",
        "city": "Lagos",
        "state": "Lagos",
        "country": "Nigeria",
        "country_code": "ng",
    }
}

NOMINATIM_CITY_ONLY = {
    "address": {
        "city": "Lagos",
        "state": "Lagos",
        "country": "Nigeria",
        "country_code": "ng",
    }
}

WEATHERAPI_SEARCH = [
    {
        "name": "Lagos",
        "region": "Lagos",
        "country": "Nigeria",
        "country_code": "NG",
        "lat": 6.5244,
        "lon": 3.3792,
    }
]


# ── reverse_geocode ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_geocode_neighbourhood_precision():
    """Nominatim suburb-level result -> neighbourhood precision + specific label."""
    client = _mock_httpx_json(NOMINATIM_NEIGHBOURHOOD)
    with patch("app.infrastructure.external.geocoding.httpx.AsyncClient", return_value=client):
        result = await reverse_geocode(6.60, 3.35)

    assert result is not None
    assert result["precision"] == "neighbourhood"
    assert result["area"] == "Magodo"
    assert result["city"] == "Lagos"
    assert result["country"] == "Nigeria"
    assert "Magodo" in result["label"]
    assert "Lagos" in result["label"]
    assert result["source"] == "nominatim"


@pytest.mark.asyncio
async def test_reverse_geocode_city_fallback_precision():
    """City-only Nominatim result -> city precision, no false neighbourhood claim."""
    client = _mock_httpx_json(NOMINATIM_CITY_ONLY)
    with patch("app.infrastructure.external.geocoding.httpx.AsyncClient", return_value=client):
        result = await reverse_geocode(6.60, 3.35)

    assert result["precision"] == "city"
    assert result["area"] is None
    assert result["label"] == "Lagos, Nigeria"  # duplicate city/region deduplicated


@pytest.mark.asyncio
async def test_reverse_geocode_nominatim_fails_uses_weatherapi():
    """Nominatim failure falls back to WeatherAPI city-level geocoding."""
    # First client (Nominatim) raises, second (WeatherAPI) returns results
    bad_client = MagicMock()
    bad_client.get = AsyncMock(side_effect=Exception("nominatim down"))
    bad_client.__aenter__ = AsyncMock(return_value=bad_client)
    bad_client.__aexit__ = AsyncMock(return_value=False)

    good_client = _mock_httpx_json(WEATHERAPI_SEARCH)

    with patch(
        "app.infrastructure.external.geocoding.httpx.AsyncClient",
        side_effect=[bad_client, good_client],
    ):
        result = await reverse_geocode(6.60, 3.35)

    assert result is not None
    assert result["precision"] == "city"
    assert result["city"] == "Lagos"
    assert result["source"] == "weatherapi"


@pytest.mark.asyncio
async def test_reverse_geocode_all_fail_returns_none():
    """Total geocoding failure returns None (endpoint falls back to weather location)."""
    bad_client = MagicMock()
    bad_client.get = AsyncMock(side_effect=Exception("all down"))
    bad_client.__aenter__ = AsyncMock(return_value=bad_client)
    bad_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.infrastructure.external.geocoding.httpx.AsyncClient", return_value=bad_client):
        result = await reverse_geocode(6.60, 3.35)

    assert result is None


@pytest.mark.asyncio
async def test_reverse_geocode_uses_cache():
    """Second call for same ~100m cell does not re-hit Nominatim."""
    client = _mock_httpx_json(NOMINATIM_NEIGHBOURHOOD)
    with patch(
        "app.infrastructure.external.geocoding.httpx.AsyncClient", return_value=client
    ) as mock_cls:
        await reverse_geocode(6.6011, 3.3511)
        await reverse_geocode(6.6012, 3.3512)  # same ~100m rounded cell

    # AsyncClient instantiated once (first call only)
    assert mock_cls.call_count == 1


# ── /weather/nearby endpoint ──────────────────────────────────────────────────


def _weather_payloads():
    current = {
        "location": {
            "name": "Lagos",
            "country": "Nigeria",
            "country_code": "NG",
            "localtime": "2026-11-21 14:00",
        },
        "current": {
            "temp_c": 31.0,
            "temp_f": 87.8,
            "feelslike_c": 34.0,
            "feelslike_f": 93.2,
            "condition": {"text": "Partly cloudy", "icon": "//icon"},
            "humidity": 72,
            "wind_kph": 12.0,
            "wind_dir": "SW",
            "uv": 6,
            "vis_km": 10,
            "cloud": 45,
            "pressure_mb": 1012,
            "precip_mm": 0.0,
            "sunrise": "06:30 AM",
            "sunset": "06:10 PM",
        },
    }
    forecast = {
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-11-21",
                    "day": {
                        "maxtemp_c": 33,
                        "mintemp_c": 24,
                        "maxtemp_f": 91,
                        "mintemp_f": 75,
                        "condition": {"text": "Sunny"},
                        "daily_chance_of_rain": 10,
                        "avghumidity": 70,
                        "uv": 7,
                        "totalprecip_mm": 0,
                    },
                    "astro": {"sunrise": "06:30 AM", "sunset": "06:10 PM"},
                }
            ]
        }
    }
    return current, forecast


@pytest.mark.asyncio
async def test_nearby_endpoint_returns_label_and_weather():
    """Nearby endpoint combines reverse-geocoded label with coordinate weather."""
    from app.api.routes.weather import get_nearby_weather

    current, forecast = _weather_payloads()
    geo = {
        "label": "Magodo, Lagos, Nigeria",
        "area": "Magodo",
        "city": "Lagos",
        "region": "Lagos",
        "country": "Nigeria",
        "country_code": "NG",
        "precision": "neighbourhood",
        "source": "nominatim",
    }

    with (
        patch("app.api.routes.weather.reverse_geocode", new=AsyncMock(return_value=geo)),
        patch("app.api.routes.weather.fetch_current", new=AsyncMock(return_value=current)),
        patch("app.api.routes.weather.fetch_forecast", new=AsyncMock(return_value=forecast)),
    ):
        result = await get_nearby_weather(lat=6.60, lon=3.35)

    assert result["location_label"] == "Magodo, Lagos, Nigeria"
    assert result["location_precision"] == "neighbourhood"
    assert result["temperature_c"] == 31.0
    assert result["city"] == "Lagos"
    assert len(result["forecast"]) == 1
    # Raw coordinates are NOT exposed in the response
    assert "lat" not in result and "lon" not in result and "latitude" not in result


@pytest.mark.asyncio
async def test_nearby_endpoint_geocode_failure_falls_back_to_weather_location():
    """When geocoding fails entirely, label falls back to WeatherAPI location."""
    from app.api.routes.weather import get_nearby_weather

    current, forecast = _weather_payloads()

    with (
        patch("app.api.routes.weather.reverse_geocode", new=AsyncMock(return_value=None)),
        patch("app.api.routes.weather.fetch_current", new=AsyncMock(return_value=current)),
        patch("app.api.routes.weather.fetch_forecast", new=AsyncMock(return_value=forecast)),
    ):
        result = await get_nearby_weather(lat=6.60, lon=3.35)

    assert result["location_label"] == "Lagos, Nigeria"
    assert result["location_precision"] == "city"


@pytest.mark.asyncio
async def test_nearby_endpoint_rejects_invalid_coords():
    """Out-of-range coordinates are rejected with 400."""
    from fastapi import HTTPException
    from app.api.routes.weather import get_nearby_weather

    with pytest.raises(HTTPException) as exc:
        await get_nearby_weather(lat=999.0, lon=3.35)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_current_endpoint_accepts_coordinates():
    """GET /current?lat&lon bypasses city resolution and uses coords directly."""
    from app.api.routes.weather import get_current_weather_endpoint

    current, _ = _weather_payloads()

    with (
        patch(
            "app.api.routes.weather.fetch_current", new=AsyncMock(return_value=current)
        ) as mock_fetch,
        patch("app.api.routes.weather.get_cache", new=AsyncMock(return_value=None)),
        patch("app.api.routes.weather.save_cache", new=AsyncMock(return_value=True)),
        patch("app.api.routes.weather.resolve_city", new=AsyncMock()) as mock_resolve,
    ):
        result = await get_current_weather_endpoint(city=None, lat=6.60, lon=3.35)

    # City resolution must NOT be called when coords are provided
    mock_resolve.assert_not_awaited()
    # fetch_current received the exact coordinates
    args = mock_fetch.await_args.args
    assert args == (6.60, 3.35)
    assert result["temperature_c"] == 31.0
