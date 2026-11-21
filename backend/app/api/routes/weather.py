"""
FILE: backend/app/api/routes/weather.py
Weather endpoints - Auto-detect, current, forecast, compare
"""

from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
import httpx

from app.agent.tools.city_resolver import resolve_city
from app.infrastructure.external.weather_api import fetch_current, fetch_forecast
from app.infrastructure.external.geocoding import reverse_geocode
from app.infrastructure.repositories.weather_repository import save_cache, get_cache
from app.core.config import settings
from app.core.logging_config import get_logger
from app.middleware.rate_limit import get_client_ip
from app.services.clothing_advice import generate_clothing_advice

logger = get_logger(__name__)

router = APIRouter(prefix="/weather", tags=["Weather"])


async def _resolve_coords(city: Optional[str], lat: Optional[float], lon: Optional[float]):
    """
    Resolve request coordinates.

    If explicit lat/lon are supplied they are used directly (browser
    geolocation) — no city-name round-trip, preserving precision.
    Otherwise the city name is resolved through the normal chain.

    Returns (lat, lon, loc_dict_or_None).
    Raises HTTPException 404 when a city name is required but not found.
    """
    if lat is not None and lon is not None:
        return float(lat), float(lon), None

    if not city:
        raise HTTPException(status_code=400, detail="Provide either 'city' or 'lat'+'lon'")

    loc = await resolve_city(city)
    if not loc:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    return float(loc["latitude"]), float(loc["longitude"]), loc


async def detect_location_from_ip(ip: str) -> Optional[dict]:
    """
    Detect city from IP address using multiple free geolocation APIs

    Args:
        ip: IP address

    Returns:
        City information dict or None if all services fail
    """
    # Handle localhost/private IPs - can't geocode these directly.
    # Outside production (local dev), fall back to WeatherAPI's auto:ip,
    # which geolocates the backend's own outbound IP — on a dev machine
    # that is the developer's real public IP.
    is_private = (
        ip in ["127.0.0.1", "localhost", "::1"]
        or ip.startswith("192.168.")
        or ip.startswith("10.")
        or ip.startswith("172.")
    )
    if is_private:
        if settings.ENVIRONMENT == "production":
            logger.info(f"Local/private IP detected: {ip}, cannot auto-detect location")
            return None
        logger.info(
            f"Private IP {ip} in {settings.ENVIRONMENT} — trying WeatherAPI auto:ip fallback"
        )
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"{settings.WEATHER_API_BASE}/current.json",
                    params={"key": settings.WEATHER_API_KEY, "q": "auto:ip"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    loc = data.get("location", {})
                    if (
                        loc.get("name")
                        and loc.get("lat") is not None
                        and loc.get("lon") is not None
                    ):
                        result = {
                            "city": loc.get("name"),
                            "country": loc.get("country"),
                            "country_code": loc.get("country_code"),
                            "lat": loc.get("lat"),
                            "lon": loc.get("lon"),
                            "timezone": loc.get("tz_id"),
                        }
                        logger.info(
                            f"Location detected via WeatherAPI auto:ip fallback: {result['city']}, {result['country']}"
                        )
                        return result
        except Exception as e:
            logger.warning(f"WeatherAPI auto:ip fallback failed: {e}")
        logger.info(f"Local/private IP detected: {ip}, cannot auto-detect location")
        return None

    # Try multiple geolocation services in order
    services = [
        {
            "name": "ip-api.com",
            "url": f"http://ip-api.com/json/{ip}",
            "parser": lambda data: (
                {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "timezone": data.get("timezone"),
                }
                if data.get("status") == "success"
                else None
            ),
        },
        {
            "name": "ip-api.co",
            "url": f"https://ipapi.co/{ip}/json/",
            "parser": lambda data: (
                {
                    "city": data.get("city"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "lat": data.get("latitude"),
                    "lon": data.get("longitude"),
                    "timezone": data.get("timezone"),
                }
                if data.get("error") is False
                else None
            ),
        },
        {
            "name": "ipwho.is",
            "url": f"https://ipwho.is/{ip}",
            "parser": lambda data: (
                {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "country_code": data.get("country_code"),
                    "lat": data.get("latitude"),
                    "lon": data.get("longitude"),
                    "timezone": data.get("timezone", {}).get("id")
                    if isinstance(data.get("timezone"), dict)
                    else data.get("timezone"),
                }
                if data.get("success")
                else None
            ),
        },
    ]

    for service in services:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(service["url"])
                if response.status_code == 200:
                    data = response.json()
                    result = service["parser"](data)
                    if result and result.get("city") and result.get("lat") and result.get("lon"):
                        logger.info(
                            f"Location detected using {service['name']}: {result['city']}, {result['country']}"
                        )
                        return result
        except Exception as e:
            logger.warning(f"{service['name']} failed: {e}")
            continue

    logger.warning(f"All geolocation services failed for IP: {ip}")
    return None


@router.get("/auto")
async def get_auto_weather(request: Request):
    """
    Auto-detect location from IP and return current weather + 7-day forecast
    """
    # Get client IP - behind Render/Cloudflare the direct peer is the proxy,
    # so resolve the real client IP from proxy headers
    ip = get_client_ip(request)
    if not ip or ip == "unknown":
        raise HTTPException(status_code=400, detail="Could not determine IP address")

    # Detect location from IP (with fallback for local development)
    location = await detect_location_from_ip(ip)
    if not location:
        raise HTTPException(status_code=404, detail="Could not detect location from IP")

    city = location.get("city")
    lat = location.get("lat")
    lon = location.get("lon")

    if not city or not lat or not lon:
        raise HTTPException(status_code=404, detail="Incomplete location data")

    # Get current weather
    try:
        current_data = await fetch_current(lat, lon)
    except Exception as e:
        logger.error(f"Failed to fetch current weather: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    # Get 7-day forecast
    try:
        forecast_data = await fetch_forecast(lat, lon, days=7)
    except Exception as e:
        logger.error(f"Failed to fetch forecast: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch forecast data")

    # Build response
    cur = current_data["current"]
    loc = current_data["location"]

    # Build forecast array
    forecast_days = []
    for day in forecast_data["forecast"]["forecastday"]:
        d = day["day"]
        forecast_days.append(
            {
                "date": day["date"],
                "high_c": d["maxtemp_c"],
                "low_c": d["mintemp_c"],
                "high_f": d["maxtemp_f"],
                "low_f": d["mintemp_f"],
                "condition": d["condition"]["text"],
                "rain_chance_pct": d["daily_chance_of_rain"],
                "humidity_pct": d["avghumidity"],
                "uv_index": d["uv"],
                "sunrise": day["astro"]["sunrise"],
                "sunset": day["astro"]["sunset"],
            }
        )

    # Build advice
    advice = []
    if cur.get("precip_mm", 0) > 1 or cur.get("humidity", 0) > 80:
        advice.append("Carry an umbrella.")
    t = cur.get("temp_c", 20)
    if t > 35:
        advice.append("Extreme heat — stay hydrated.")
    elif t > 28:
        advice.append("Wear light clothing.")
    elif t < 15:
        advice.append("Bring a jacket.")

    return {
        "city": city,
        "country": location.get("country"),
        "country_code": location.get("country_code"),
        "local_time": loc.get("localtime"),
        "temperature_c": cur["temp_c"],
        "temperature_f": cur["temp_f"],
        "feels_like_c": cur["feelslike_c"],
        "feels_like_f": cur["feelslike_f"],
        "condition": cur["condition"]["text"],
        "humidity_pct": cur["humidity"],
        "wind_kph": cur["wind_kph"],
        "wind_direction": cur["wind_dir"],
        "uv_index": cur.get("uv", 0),
        "visibility_km": cur.get("vis_km", 0),
        "cloud_cover_pct": cur.get("cloud", 0),
        "pressure_hpa": cur.get("pressure_mb"),
        "sunrise": cur.get("sunrise", ""),
        "sunset": cur.get("sunset", ""),
        "forecast": forecast_days,
        "advice": " ".join(advice) or "Pleasant conditions.",
    }


@router.get("/current")
async def get_current_weather_endpoint(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude (coordinate weather)"),
    lon: Optional[float] = Query(None, description="Longitude (coordinate weather)"),
):
    """
    Get current weather for a named city or exact coordinates
    """
    lat, lon, loc = await _resolve_coords(city, lat, lon)

    # Check cache (only for city-resolved requests — coord cache lookup is
    # not coordinate-aware and could return another location's data)
    if loc:
        cached = await get_cache(loc.get("city_id"), lat, lon, "current", days=1)
        if cached:
            return cached

    # Fetch live data
    try:
        data = await fetch_current(lat, lon)
    except Exception as e:
        logger.error(f"Failed to fetch current weather: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    # Build response
    cur = data["current"]
    loc_data = data["location"]

    result = {
        "city": loc_data["name"],
        "country": loc_data["country"],
        "country_code": loc_data.get("country_code", ""),
        "local_time": loc_data.get("localtime"),
        "temperature_c": cur["temp_c"],
        "temperature_f": cur["temp_f"],
        "feels_like_c": cur["feelslike_c"],
        "feels_like_f": cur["feelslike_f"],
        "condition": cur["condition"]["text"],
        "humidity_pct": cur["humidity"],
        "wind_kph": cur["wind_kph"],
        "wind_direction": cur["wind_dir"],
        "uv_index": cur.get("uv", 0),
        "visibility_km": cur.get("vis_km", 0),
        "cloud_cover_pct": cur.get("cloud", 0),
        "pressure_hpa": cur.get("pressure_mb"),
    }

    # Save to cache (city-resolved requests only)
    if loc:
        await save_cache(
            loc.get("city_id"), "current", 1, result, cur["temp_c"], cur["condition"]["text"]
        )

    return result


@router.get("/forecast")
async def get_forecast_endpoint(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude (coordinate weather)"),
    lon: Optional[float] = Query(None, description="Longitude (coordinate weather)"),
    days: int = Query(7, ge=1, le=7, description="Number of days (1-7)"),
):
    """
    Get weather forecast for a city or exact coordinates
    """
    lat, lon, loc = await _resolve_coords(city, lat, lon)

    # Check cache (city-resolved requests only)
    if loc:
        cached = await get_cache(loc.get("city_id"), lat, lon, "forecast", days=days)
        if cached:
            return cached

    # Fetch live data
    try:
        data = await fetch_forecast(lat, lon, days)
    except Exception as e:
        logger.error(f"Failed to fetch forecast: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch forecast data")

    # Build response
    loc_data = data["location"]
    forecast_days = []

    for day in data["forecast"]["forecastday"]:
        d = day["day"]
        forecast_days.append(
            {
                "date": day["date"],
                "day_name": day.get("date", ""),
                "high_c": d["maxtemp_c"],
                "low_c": d["mintemp_c"],
                "high_f": d["maxtemp_f"],
                "low_f": d["mintemp_f"],
                "condition": d["condition"]["text"],
                "rain_chance_pct": d["daily_chance_of_rain"],
                "total_rain_mm": d["totalprecip_mm"],
                "humidity_pct": d["avghumidity"],
                "uv_index": d["uv"],
                "sunrise": day["astro"]["sunrise"],
                "sunset": day["astro"]["sunset"],
            }
        )

    result = {
        "city": loc_data["name"],
        "country": loc_data["country"],
        "days_requested": days,
        "forecast": forecast_days,
    }

    # Save to cache (city-resolved requests only)
    if loc:
        await save_cache(loc.get("city_id"), "forecast", days, result)

    return result


@router.get("/compare")
async def compare_weather_endpoint(
    city1: str = Query(..., description="First city"),
    city2: str = Query(..., description="Second city"),
):
    """
    Compare current weather between two cities
    """
    # Resolve both cities
    loc1 = await resolve_city(city1)
    loc2 = await resolve_city(city2)

    errors = []
    if not loc1:
        errors.append(f"City '{city1}' not found")
    if not loc2:
        errors.append(f"City '{city2}' not found")

    if errors:
        raise HTTPException(status_code=404, detail=" | ".join(errors))

    # Fetch weather for both cities
    try:
        data1 = await fetch_current(float(loc1["latitude"]), float(loc1["longitude"]))
        data2 = await fetch_current(float(loc2["latitude"]), float(loc2["longitude"]))
    except Exception as e:
        logger.error(f"Failed to fetch comparison data: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    # Build response
    def extract_city_data(data):
        cur = data["current"]
        loc = data["location"]
        return {
            "city": loc["name"],
            "country": loc["country"],
            "temperature_c": cur["temp_c"],
            "temperature_f": cur["temp_f"],
            "feels_like_c": cur["feelslike_c"],
            "condition": cur["condition"]["text"],
            "humidity_pct": cur["humidity"],
            "wind_kph": cur["wind_kph"],
            "uv_index": cur.get("uv", 0),
        }

    city1_data = extract_city_data(data1)
    city2_data = extract_city_data(data2)

    return {
        "city_1": city1_data,
        "city_2": city2_data,
        "comparison": {
            "warmer_city": city1_data["city"]
            if city1_data["temperature_c"] >= city2_data["temperature_c"]
            else city2_data["city"],
            "cooler_city": city2_data["city"]
            if city1_data["temperature_c"] >= city2_data["temperature_c"]
            else city1_data["city"],
            "temp_difference_c": abs(city1_data["temperature_c"] - city2_data["temperature_c"]),
            "temp_difference_f": abs(city1_data["temperature_f"] - city2_data["temperature_f"]),
        },
    }


@router.get("/hourly")
async def get_hourly_forecast(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude (coordinate weather)"),
    lon: Optional[float] = Query(None, description="Longitude (coordinate weather)"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get 24-hour breakdown for a specific date
    """
    lat, lon, loc = await _resolve_coords(city, lat, lon)

    # Fetch forecast data
    try:
        data = await fetch_forecast(
            lat, lon, days=3
        )  # Get 3 days to ensure we have the target date
    except Exception as e:
        logger.error(f"Failed to fetch hourly forecast: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch forecast data")

    # Find the target date in forecast
    target_hourly = None
    for day in data["forecast"]["forecastday"]:
        if day["date"] == date:
            target_hourly = day.get("hour", [])
            break

    if not target_hourly:
        raise HTTPException(status_code=404, detail=f"No hourly data available for date {date}")

    # Build hourly response
    hourly_data = []
    for hour in target_hourly:
        hourly_data.append(
            {
                "time": hour["time"],
                "temperature_c": hour["temp_c"],
                "temperature_f": hour["temp_f"],
                "condition": hour["condition"]["text"],
                "humidity_pct": hour["humidity"],
                "wind_kph": hour["wind_kph"],
                "wind_direction": hour["wind_dir"],
                "rain_chance_pct": hour["chance_of_rain"],
                "uv_index": hour.get("uv", 0),
            }
        )

    return {
        "city": (loc or {}).get("city_name") or data["location"]["name"],
        "date": date,
        "hourly": hourly_data,
    }


@router.get("/detail")
async def get_weather_detail(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude (coordinate weather)"),
    lon: Optional[float] = Query(None, description="Longitude (coordinate weather)"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get detailed weather for a specific day (rain, pressure, UV)
    """
    lat, lon, loc = await _resolve_coords(city, lat, lon)

    # Fetch forecast data
    try:
        data = await fetch_forecast(lat, lon, days=3)
    except Exception as e:
        logger.error(f"Failed to fetch weather detail: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch forecast data")

    # Find the target date in forecast
    target_day = None
    for day in data["forecast"]["forecastday"]:
        if day["date"] == date:
            target_day = day
            break

    if not target_day:
        raise HTTPException(status_code=404, detail=f"No data available for date {date}")

    d = target_day["day"]
    astro = target_day["astro"]

    return {
        "city": (loc or {}).get("city_name") or data["location"]["name"],
        "date": date,
        "rain": {
            "chance_pct": d["daily_chance_of_rain"],
            "total_mm": d["totalprecip_mm"],
            "will_it_rain": d["daily_will_it_rain"],
        },
        "pressure": {
            "hpa": d.get(
                "avgvis_km", 0
            )  # Using visibility as proxy, WeatherAPI doesn't provide pressure in day data
        },
        "uv": {
            "index": d["uv"],
            "level": "Extreme"
            if d["uv"] >= 11
            else "Very High"
            if d["uv"] >= 8
            else "High"
            if d["uv"] >= 6
            else "Moderate"
            if d["uv"] >= 3
            else "Low",
        },
        "sun": {
            "sunrise": astro["sunrise"],
            "sunset": astro["sunset"],
            "moonrise": astro["moonrise"],
            "moonset": astro["moonset"],
            "moon_phase": astro["moon_phase"],
        },
        "condition": {"text": d["condition"]["text"], "icon": d["condition"]["icon"]},
    }


@router.get("/wear")
async def get_clothing_advice(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude (coordinate weather)"),
    lon: Optional[float] = Query(None, description="Longitude (coordinate weather)"),
    unit: str = Query("C", regex="^[CF]$"),
):
    """
    Get AI-powered clothing recommendations for current conditions
    """
    lat, lon, loc = await _resolve_coords(city, lat, lon)

    # Fetch current weather
    try:
        data = await fetch_current(lat, lon)
    except Exception as e:
        logger.error(f"Failed to fetch current weather for clothing advice: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    cur = data["current"]
    loc_data = data["location"]

    # Generate clothing advice
    advice = generate_clothing_advice(
        temp_c=cur["temp_c"],
        condition=cur["condition"]["text"],
        rain_chance=cur.get("daily_chance_of_rain", 0),
        uv_index=cur.get("uv", 0),
    )

    return {
        "city": loc_data["name"],
        "country": loc_data["country"],
        "temperature_c": cur["temp_c"],
        "temperature_f": cur["temp_f"],
        "condition": cur["condition"]["text"],
        **advice,
    }


@router.get("/nearby")
async def get_nearby_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """
    Weather for exact browser coordinates + reverse-geocoded location label.

    Weather is fetched by coordinates (no city-name round-trip). The label is
    the most specific readable name available — neighbourhood when the
    geocoder provides one, otherwise city/region/country.
    """
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    # Reverse geocode (cached; falls back to WeatherAPI city-level)
    geo = await reverse_geocode(lat, lon)

    # Fetch live weather by coordinates
    try:
        current_data = await fetch_current(lat, lon)
        forecast_data = await fetch_forecast(lat, lon, days=7)
    except Exception as e:
        logger.error(f"Failed to fetch nearby weather: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    cur = current_data["current"]
    loc_data = current_data["location"]

    # Location label: geocoder result, else WeatherAPI's own location name
    if geo and geo.get("label"):
        location_label = geo["label"]
        precision = geo.get("precision", "city")
        country = geo.get("country") or loc_data.get("country")
        country_code = geo.get("country_code") or loc_data.get("country_code", "")
    else:
        location_label = f"{loc_data['name']}, {loc_data['country']}"
        precision = "city"
        country = loc_data.get("country")
        country_code = loc_data.get("country_code", "")

    # Build forecast array (same shape as /auto)
    forecast_days = []
    for day in forecast_data["forecast"]["forecastday"]:
        d = day["day"]
        forecast_days.append(
            {
                "date": day["date"],
                "high_c": d["maxtemp_c"],
                "low_c": d["mintemp_c"],
                "high_f": d["maxtemp_f"],
                "low_f": d["mintemp_f"],
                "condition": d["condition"]["text"],
                "rain_chance_pct": d["daily_chance_of_rain"],
                "humidity_pct": d["avghumidity"],
                "uv_index": d["uv"],
                "sunrise": day["astro"]["sunrise"],
                "sunset": day["astro"]["sunset"],
            }
        )

    advice = []
    if cur.get("precip_mm", 0) > 1 or cur.get("humidity", 0) > 80:
        advice.append("Carry an umbrella.")
    t = cur.get("temp_c", 20)
    if t > 35:
        advice.append("Extreme heat — stay hydrated.")
    elif t > 28:
        advice.append("Wear light clothing.")
    elif t < 15:
        advice.append("Bring a jacket.")

    return {
        "location_label": location_label,
        "location_precision": precision,
        "city": loc_data["name"],
        "country": country,
        "country_code": country_code,
        "local_time": loc_data.get("localtime"),
        "temperature_c": cur["temp_c"],
        "temperature_f": cur["temp_f"],
        "feels_like_c": cur["feelslike_c"],
        "feels_like_f": cur["feelslike_f"],
        "condition": cur["condition"]["text"],
        "humidity_pct": cur["humidity"],
        "wind_kph": cur["wind_kph"],
        "wind_direction": cur["wind_dir"],
        "uv_index": cur.get("uv", 0),
        "visibility_km": cur.get("vis_km", 0),
        "cloud_cover_pct": cur.get("cloud", 0),
        "pressure_hpa": cur.get("pressure_mb"),
        "sunrise": cur.get("sunrise", ""),
        "sunset": cur.get("sunset", ""),
        "forecast": forecast_days,
        "advice": " ".join(advice) or "Pleasant conditions.",
    }


@router.post("/wear")
async def get_clothing_advice_post(request: dict):
    """
    Get clothing advice for specific date or occasion
    """
    city = request.get("city")
    date = request.get("date")  # Optional: YYYY-MM-DD
    occasion = request.get("occasion", "general")  # Optional: work, casual, formal, outdoor

    if not city:
        raise HTTPException(status_code=400, detail="City is required")

    # Resolve city
    loc = await resolve_city(city)
    if not loc:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    lat = float(loc["latitude"])
    lon = float(loc["longitude"])

    # Fetch weather data
    try:
        if date:
            data = await fetch_forecast(lat, lon, days=3)
            # Find target date
            target_day = None
            for day in data["forecast"]["forecastday"]:
                if day["date"] == date:
                    target_day = day
                    break
            if not target_day:
                raise HTTPException(status_code=404, detail=f"No data available for date {date}")
            cur = target_day["day"]
            condition = cur["condition"]["text"]
            rain_chance = cur["daily_chance_of_rain"]
            uv_index = cur["uv"]
        else:
            data = await fetch_current(lat, lon)
            cur = data["current"]
            condition = cur["condition"]["text"]
            rain_chance = cur.get("daily_chance_of_rain", 0)
            uv_index = cur.get("uv", 0)
            cur["temp_c"] = cur["temp_c"]  # Ensure temp_c exists
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch weather for clothing advice: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    # Generate clothing advice
    advice = generate_clothing_advice(
        temp_c=cur["temp_c"],
        condition=condition,
        rain_chance=rain_chance,
        uv_index=uv_index,
        occasion=occasion,
    )

    return {
        "city": loc.get("city_name"),
        "date": date or "today",
        "occasion": occasion,
        "temperature_c": cur["temp_c"],
        "temperature_f": cur.get("temp_f", cur["temp_c"] * 9 / 5 + 32),
        "condition": condition,
        **advice,
    }
