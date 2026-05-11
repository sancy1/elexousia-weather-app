"""
FILE: backend/app/infrastructure/external/weather_api.py
HTTP client for WeatherAPI.com
"""

import httpx
from typing import Dict, Any

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def fetch_current(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch current weather from WeatherAPI.com
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Raw JSON response from WeatherAPI
    """
    url = f"{settings.WEATHER_API_BASE}/current.json"
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": f"{lat},{lon}",
        "aqi": "no"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"WeatherAPI HTTP error: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        logger.error(f"WeatherAPI request error: {e}")
        raise


async def fetch_forecast(lat: float, lon: float, days: int = 3) -> Dict[str, Any]:
    """
    Fetch weather forecast from WeatherAPI.com
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of days (1-10)
        
    Returns:
        Raw JSON response from WeatherAPI
    """
    days = max(1, min(10, int(days)))
    url = f"{settings.WEATHER_API_BASE}/forecast.json"
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": f"{lat},{lon}",
        "days": days,
        "aqi": "no",
        "alerts": "no"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"WeatherAPI HTTP error: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        logger.error(f"WeatherAPI request error: {e}")
        raise


async def search_city(query: str) -> list:
    """
    Search for cities using WeatherAPI geocoding
    
    Args:
        query: City name or query string
        
    Returns:
        List of matching cities
    """
    url = f"{settings.WEATHER_API_BASE}/search.json"
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": query
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"WeatherAPI search HTTP error: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        logger.error(f"WeatherAPI search request error: {e}")
        return []