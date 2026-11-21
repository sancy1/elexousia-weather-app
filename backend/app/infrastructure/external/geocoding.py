"""
FILE: backend/app/infrastructure/external/geocoding.py
Reverse geocoding: coordinates -> most specific readable location label.

Strategy:
  1. Nominatim (OpenStreetMap) reverse geocode — can resolve neighbourhood /
     suburb / district level names. Cached briefly to respect usage policy.
  2. WeatherAPI search (lat,lon) — city-level fallback, reuses existing key.

Never claims neighbourhood precision the data does not support: the returned
`precision` field is "neighbourhood" | "city" | "region".
"""

import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "Elexousia-Weather/1.0 (weather app; contact: admin@elexousia)"

# In-memory TTL cache: ~100 m grid cells -> (timestamp, result)
_CACHE_TTL_SECONDS = 24 * 60 * 60
_cache: Dict[tuple, tuple] = {}

# Address keys ordered from most to least specific (Nominatim address object)
_AREA_KEYS = ("neighbourhood", "suburb", "city_district", "quarter", "borough", "hamlet")
_CITY_KEYS = ("city", "town", "village", "municipality", "county")
_REGION_KEYS = ("state", "state_district", "region", "province")


def _cache_key(lat: float, lon: float) -> tuple:
    # ~100 m precision is plenty for a weather label
    return (round(lat, 3), round(lon, 3))


def _pick(address: Dict[str, Any], keys) -> Optional[str]:
    for k in keys:
        v = address.get(k)
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    return None


async def _nominatim_reverse(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Reverse geocode via Nominatim. Returns label parts or None."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                NOMINATIM_REVERSE_URL,
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "jsonv2",
                    "zoom": 18,  # neighbourhood-level detail
                    "addressdetails": 1,
                },
                headers={"User-Agent": NOMINATIM_USER_AGENT},
            )
            if resp.status_code != 200:
                logger.warning(f"Nominatim reverse failed: HTTP {resp.status_code}")
                return None
            data = resp.json()
    except Exception as e:
        logger.warning(f"Nominatim reverse error: {e}")
        return None

    address = data.get("address") or {}
    if not address:
        return None

    area = _pick(address, _AREA_KEYS)
    city = _pick(address, _CITY_KEYS)
    region = _pick(address, _REGION_KEYS)
    country = _pick(address, ("country",)) or ""
    country_code = (address.get("country_code") or "").upper() or None

    if not (area or city or region or country):
        return None

    # Build label: most specific parts first, deduplicated, no raw coords
    parts = []
    for p in (area, city, region, country):
        if p and p not in parts:
            parts.append(p)
    label = ", ".join(parts)

    if area:
        precision = "neighbourhood"
    elif city:
        precision = "city"
    else:
        precision = "region"

    return {
        "label": label,
        "area": area,
        "city": city,
        "region": region,
        "country": country,
        "country_code": country_code,
        "precision": precision,
        "source": "nominatim",
    }


async def _weatherapi_reverse(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """City-level fallback via WeatherAPI search (lat,lon query)."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{settings.WEATHER_API_BASE}/search.json",
                params={"key": settings.WEATHER_API_KEY, "q": f"{lat},{lon}"},
            )
            if resp.status_code != 200:
                return None
            results = resp.json()
    except Exception as e:
        logger.warning(f"WeatherAPI reverse geocode error: {e}")
        return None

    if not results:
        return None
    loc = results[0]
    name = loc.get("name")
    region = loc.get("region")
    country = loc.get("country", "")
    if not name:
        return None

    parts = [p for p in (name, region, country) if p]
    return {
        "label": ", ".join(parts),
        "area": None,
        "city": name,
        "region": region,
        "country": country,
        "country_code": loc.get("country_code"),
        "precision": "city",
        "source": "weatherapi",
    }


async def reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Resolve coordinates to the most specific readable label available.

    Returns dict with label/area/city/region/country/country_code/precision
    or None if every provider fails. Results are cached ~24h per ~100 m cell.
    """
    key = _cache_key(lat, lon)
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < _CACHE_TTL_SECONDS:
        return hit[1]

    result = await _nominatim_reverse(lat, lon)
    if result is None:
        result = await _weatherapi_reverse(lat, lon)

    if result is not None:
        _cache[key] = (now, result)
    return result
