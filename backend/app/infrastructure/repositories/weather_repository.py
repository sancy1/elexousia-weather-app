"""
FILE: backend/app/infrastructure/repositories/weather_repository.py
Weather cache repository for database operations
"""

import json
from typing import Optional, Dict, Any

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def save_cache(
    city_id: Optional[int],
    cache_type: str,
    days: int,
    data: Dict[str, Any],
    temp_c: Optional[float] = None,
    condition: Optional[str] = None
) -> bool:
    """
    Save weather data to cache
    
    Args:
        city_id: Database city ID
        cache_type: Type of cache (current, forecast, etc.)
        days: Number of forecast days
        data: Weather data to cache
        temp_c: Current temperature for indexing
        condition: Weather condition for indexing
        
    Returns:
        True if saved successfully
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather_cache (city_id, cache_type, forecast_days, raw_json, temperature_c, condition)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (city_id, cache_type, days, json.dumps(data), temp_c, condition))
            conn.commit()
            cursor.close()
            logger.debug(f"Saved cache: {cache_type} for city_id={city_id}")
            return True
    except Exception as e:
        # If insert fails (duplicate), try update
        try:
            async with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE weather_cache
                    SET raw_json = %s, temperature_c = %s, condition = %s, fetched_at = NOW()
                    WHERE city_id = %s AND cache_type = %s AND forecast_days = %s
                """, (json.dumps(data), temp_c, condition, city_id, cache_type, days))
                conn.commit()
                cursor.close()
                logger.debug(f"Updated cache: {cache_type} for city_id={city_id}")
                return True
        except Exception as e2:
            logger.error(f"Failed to save/update cache: {e2}")
            return False


async def get_cache(
    city_id: Optional[int],
    lat: float,
    lon: float,
    cache_type: str,
    days: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Get cached weather data
    
    Args:
        city_id: Database city ID
        lat: Latitude (for coordinate-based cache lookup if city_id not available)
        lon: Longitude
        cache_type: Type of cache
        days: Number of forecast days
        
    Returns:
        Cached data if valid, None otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if city_id:
                cursor.execute("""
                    SELECT raw_json FROM weather_cache
                    WHERE city_id = %s AND cache_type = %s AND forecast_days = %s AND expires_at > NOW()
                    ORDER BY fetched_at DESC LIMIT 1;
                """, (city_id, cache_type, days))
            else:
                # Fallback: try to find by coordinates
                cursor.execute("""
                    SELECT raw_json FROM weather_cache
                    WHERE cache_type = %s AND forecast_days = %s AND expires_at > NOW()
                    ORDER BY fetched_at DESC LIMIT 1;
                """, (cache_type, days))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return json.loads(row[0])
            return None
    except Exception as e:
        logger.error(f"Failed to get cache: {e}")
        return None


async def delete_expired_cache() -> int:
    """
    Delete expired cache entries (cleanup job)
    
    Returns:
        Number of deleted rows
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM weather_cache WHERE expires_at < NOW();
            """)
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            logger.info(f"Deleted {deleted} expired cache entries")
            return deleted
    except Exception as e:
        logger.error(f"Failed to delete expired cache: {e}")
        return 0


async def get_cached_weather_by_city(city_name: str, cache_type: str = "current") -> Optional[Dict[str, Any]]:
    """
    Get cached weather by city name (joins with cities table)
    
    Args:
        city_name: City name
        cache_type: Type of cache
        
    Returns:
        Cached data if found
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wc.raw_json 
                FROM weather_cache wc
                JOIN cities c ON wc.city_id = c.id
                WHERE c.city_name ILIKE %s AND wc.cache_type = %s AND wc.expires_at > NOW()
                ORDER BY wc.fetched_at DESC
                LIMIT 1;
            """, (city_name, cache_type))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return json.loads(row[0])
            return None
    except Exception as e:
        logger.error(f"Failed to get cached weather by city: {e}")
        return None