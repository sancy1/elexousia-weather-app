"""
FILE: backend/app/infrastructure/repositories/location_repository.py
Repository for saved locations operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def add_saved_location(
    user_id: int,
    city_name: str,
    country_code: str,
    label: str,
    latitude: float,
    longitude: float,
    timezone: str
) -> Optional[Dict[str, Any]]:
    """
    Add a new saved location for a user
    
    Args:
        user_id: User ID
        city_name: City name
        country_code: Country code (e.g., NG, US)
        label: User-defined label (e.g., "Home", "Work")
        latitude: Latitude
        longitude: Longitude
        timezone: Timezone
        
    Returns:
        Saved location dict or None if failed
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get max display_order for this user
            cursor.execute(
                "SELECT COALESCE(MAX(display_order), 0) FROM weather_saved_locations WHERE user_id = %s",
                (user_id,)
            )
            max_order = cursor.fetchone()[0]
            new_order = max_order + 1
            
            # Insert new location
            cursor.execute("""
                INSERT INTO weather_saved_locations 
                (user_id, city_name, country_name, country_code, label, latitude, longitude, timezone, display_order, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                RETURNING id, user_id, city_name, country_code, label, latitude, longitude, 
                          timezone, display_order, is_default, created_at
            """, (user_id, city_name, country_code, country_code, label, latitude, longitude, timezone, new_order))
            
            row = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "city_name": row[2],
                    "country_code": row[3],
                    "label": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "timezone": row[7],
                    "display_order": row[8],
                    "is_default": row[9],
                    "created_at": row[10].isoformat() if row[10] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to add saved location: {e}")
        return None


async def get_saved_locations(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all saved locations for a user ordered by display_order
    
    Args:
        user_id: User ID
        
    Returns:
        List of saved location dicts
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, city_name, country_code, label, latitude, longitude, 
                       timezone, display_order, is_default, created_at
                FROM weather_saved_locations
                WHERE user_id = %s
                ORDER BY display_order ASC, created_at ASC
            """, (user_id,))
            
            locations = []
            for row in cursor.fetchall():
                locations.append({
                    "id": row[0],
                    "user_id": row[1],
                    "city_name": row[2],
                    "country_code": row[3],
                    "label": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "timezone": row[7],
                    "display_order": row[8],
                    "is_default": row[9],
                    "created_at": row[10].isoformat() if row[10] else None
                })
            
            cursor.close()
            return locations
    except Exception as e:
        logger.error(f"Failed to get saved locations: {e}")
        return []


async def update_saved_location(
    location_id: int,
    user_id: int,
    label: Optional[str] = None,
    display_order: Optional[int] = None
) -> bool:
    """
    Update a saved location's label or display_order
    
    Args:
        location_id: Location ID
        user_id: User ID (for ownership check)
        label: New label (optional)
        display_order: New display order (optional)
        
    Returns:
        True if updated, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            updates = []
            params = []
            
            if label is not None:
                updates.append("label = %s")
                params.append(label)
            
            if display_order is not None:
                updates.append("display_order = %s")
                params.append(display_order)
            
            if not updates:
                return False
            
            params.extend([location_id, user_id])
            
            query = f"""
                UPDATE weather_saved_locations
                SET {', '.join(updates)}
                WHERE id = %s AND user_id = %s
            """
            
            cursor.execute(query, params)
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to update saved location: {e}")
        return False


async def set_default_location(location_id: int, user_id: int) -> bool:
    """
    Set a location as the default (only one default per user)
    
    Args:
        location_id: Location ID
        user_id: User ID
        
    Returns:
        True if set as default, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Remove default from all user's locations
            cursor.execute(
                "UPDATE weather_saved_locations SET is_default = FALSE WHERE user_id = %s",
                (user_id,)
            )
            
            # Set new default
            cursor.execute(
                "UPDATE weather_saved_locations SET is_default = TRUE WHERE id = %s AND user_id = %s",
                (location_id, user_id)
            )
            
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to set default location: {e}")
        return False


async def delete_saved_location(location_id: int, user_id: int) -> bool:
    """
    Delete a saved location
    
    Args:
        location_id: Location ID
        user_id: User ID (for ownership check)
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM weather_saved_locations WHERE id = %s AND user_id = %s",
                (location_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to delete saved location: {e}")
        return False


async def get_default_location(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user's default saved location
    
    Args:
        user_id: User ID
        
    Returns:
        Default location dict or None
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, city_name, country_code, label, latitude, longitude, 
                       timezone, display_order, is_default, created_at
                FROM weather_saved_locations
                WHERE user_id = %s AND is_default = TRUE
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "city_name": row[2],
                    "country_code": row[3],
                    "label": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "timezone": row[7],
                    "display_order": row[8],
                    "is_default": row[9],
                    "created_at": row[10].isoformat() if row[10] else None
                }
            return None
    except Exception as e:
        logger.error(f"Failed to get default location: {e}")
        return None