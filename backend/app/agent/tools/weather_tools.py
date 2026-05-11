"""
FILE: backend/app/agent/tools/weather_tools.py
LangChain tools for weather data fetching
"""

from typing import Dict, Any
import json
from langchain_core.tools import tool

from app.agent.tools.city_resolver import resolve_city
from app.infrastructure.external.weather_api import fetch_current, fetch_forecast
from app.infrastructure.repositories.weather_repository import get_cache, save_cache
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def build_advice(cur: Dict[str, Any]) -> str:
    """Generate weather advice based on current conditions"""
    tips = []
    if cur.get("precip_mm", 0) > 1 or cur.get("humidity", 0) > 80:
        tips.append("Carry an umbrella.")
    
    t = cur.get("temp_c", 20)
    if t > 35:
        tips.append("Extreme heat — stay hydrated.")
    elif t > 28:
        tips.append("Wear light, breathable clothing.")
    elif t < 5:
        tips.append("Very cold — heavy coat essential.")
    elif t < 15:
        tips.append("Cool — bring a jacket.")
    
    if cur.get("uv", 0) >= 8:
        tips.append("Very high UV — SPF 50+ required.")
    elif cur.get("uv", 0) >= 5:
        tips.append("Moderate UV — apply sunscreen.")
    
    if cur.get("wind_kph", 0) > 40:
        tips.append("Strong winds — secure loose items.")
    
    return " ".join(tips) or "Pleasant conditions — enjoy your day!"


def build_travel_advice(daily: list) -> str:
    """Generate travel advice based on forecast"""
    if not daily:
        return "No forecast data."
    
    mr = max(d.get("rain_chance_pct", 0) for d in daily)
    ah = sum(d.get("high_c", 20) for d in daily) / len(daily)
    tips = []
    
    if mr > 60:
        tips.append("Pack a rain jacket — wet days expected.")
    if ah > 32:
        tips.append("Hot destination — light clothing and SPF 50+ essential.")
    elif ah < 8:
        tips.append("Cold — pack heavy winter layers.")
    
    return " ".join(tips) or "Good conditions expected."


@tool
async def get_current_weather(city: str) -> str:
    """
    Gets live current weather for any city in the world.
    Handles abbreviations (NYC), typos (pris), nicknames (city of light).
    Use for: right now, today, current conditions.
    
    Args:
        city: any city name, abbreviation, or nickname.
        
    Returns:
        JSON with temperature C/F, conditions, humidity, wind, UV, advice.
    """
    loc = await resolve_city(city)
    if not loc:
        return json.dumps({
            "status": "error",
            "query": city,
            "message": f"Cannot resolve '{city}'. Try 'City, Country' format."
        })
    
    city_id = loc.get("city_id")
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    
    # Check cache
    cached = await get_cache(city_id, lat, lon, "current", days=1)
    if cached:
        return json.dumps({
            "status": "success",
            "data": cached,
            "source": "cache",
            "resolution": loc.get("resolution", "db")
        })
    
    # Fetch live data
    try:
        raw = await fetch_current(lat, lon)
    except Exception as e:
        logger.error(f"Failed to fetch current weather: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    
    cur, location = raw["current"], raw["location"]
    result = {
        "city": location["name"],
        "country": location["country"],
        "local_time": location["localtime"],
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
        "advice": build_advice(cur),
        "resolved_city": location["name"],  # For auto-updating UI
    }
    
    await save_cache(city_id, "current", 1, result, cur["temp_c"], cur["condition"]["text"])
    
    return json.dumps({
        "status": "success",
        "data": result,
        "source": "live",
        "resolution": loc.get("resolution", "db")
    })


@tool
async def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    Gets multi-day weather forecast for any city in the world.
    Use for: tomorrow, this week, will it rain, travel planning.
    
    Args:
        city: any city name.
        days: 1 to 7 (default 3).
        
    Returns:
        JSON with daily high/low, conditions, rain chance, travel advice.
    """
    days = max(1, min(7, int(days)))
    
    loc = await resolve_city(city)
    if not loc:
        return json.dumps({
            "status": "error",
            "message": f"Cannot resolve '{city}'."
        })
    
    city_id = loc.get("city_id")
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    
    # Check cache
    cached = await get_cache(city_id, lat, lon, "forecast", days=days)
    if cached:
        return json.dumps({
            "status": "success",
            "data": cached,
            "source": "cache"
        })
    
    # Fetch live data
    try:
        raw = await fetch_forecast(lat, lon, days)
    except Exception as e:
        logger.error(f"Failed to fetch forecast: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    
    location = raw["location"]
    daily = []
    
    for day in raw["forecast"]["forecastday"]:
        d = day["day"]
        daily.append({
            "date": day["date"],
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
        })
    
    result = {
        "city": location["name"],
        "country": location["country"],
        "days_requested": days,
        "forecast": daily,
        "travel_advice": build_travel_advice(daily),
        "resolved_city": location["name"],  # For auto-updating UI
    }
    
    await save_cache(city_id, "forecast", days, result)
    
    return json.dumps({
        "status": "success",
        "data": result,
        "source": "live"
    })


@tool
async def compare_weather(city1: str, city2: str) -> str:
    """
    Compares current weather between two cities side by side.
    Use when user mentions two cities or asks which is better for travel.
    
    Args:
        city1, city2: any city names or descriptions.
        
    Returns:
        JSON with side-by-side comparison and recommendation.
    """
    loc1, loc2 = await resolve_city(city1), await resolve_city(city2)
    errors = []
    
    if not loc1:
        errors.append(f"Cannot resolve '{city1}'")
    if not loc2:
        errors.append(f"Cannot resolve '{city2}'")
    
    if errors:
        return json.dumps({
            "status": "error",
            "message": " | ".join(errors)
        })
    
    try:
        r1 = await fetch_current(float(loc1["latitude"]), float(loc1["longitude"]))
        r2 = await fetch_current(float(loc2["latitude"]), float(loc2["longitude"]))
    except Exception as e:
        logger.error(f"Failed to fetch comparison data: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    
    def extract(r):
        c = r["current"]
        return {
            "city": r["location"]["name"],
            "country": r["location"]["country"],
            "temp_c": c["temp_c"],
            "temp_f": c["temp_f"],
            "feels_like_c": c["feelslike_c"],
            "condition": c["condition"]["text"],
            "humidity": c["humidity"],
            "wind_kph": c["wind_kph"],
            "uv_index": c.get("uv", 0)
        }
    
    c1, c2 = extract(r1), extract(r2)
    
    return json.dumps({
        "status": "success",
        "city_1": c1,
        "city_2": c2,
        "comparison": {
            "warmer_city": c1["city"] if c1["temp_c"] >= c2["temp_c"] else c2["city"],
            "windier_city": c1["city"] if c1["wind_kph"] >= c2["wind_kph"] else c2["city"],
            "temp_difference_c": abs(c1["temp_c"] - c2["temp_c"]),
            "temp_difference_f": abs(c1["temp_f"] - c2["temp_f"]),
        },
        "resolved_city": c1["city"],  # Default to first city for UI
    })