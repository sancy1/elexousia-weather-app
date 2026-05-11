"""
FILE: backend/app/infrastructure/repositories/search_history_repository.py
Repository for search history operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def add_search_history(
    user_id: int,
    city_name: str,
    country_code: str,
    temperature: Optional[float] = None,
    condition: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Add a new search history entry for a user
    
    Args:
        user_id: User ID
        city_name: City name
        country_code: Country code (e.g., NG, US)
        temperature: Temperature in Celsius (optional)
        condition: Weather condition (optional)
        
    Returns:
        Search history dict or None if failed
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if this city already exists in history for this user
            cursor.execute(
                "SELECT id FROM search_history WHERE user_id = %s AND city_name = %s",
                (user_id, city_name)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                cursor.execute("""
                    UPDATE search_history
                    SET searched_at = NOW(), temperature = %s, condition = %s
                    WHERE id = %s
                    RETURNING id, user_id, city_name, country_code, searched_at, temperature, condition
                """, (temperature, condition, existing[0]))
            else:
                # Insert new entry
                cursor.execute("""
                    INSERT INTO search_history 
                    (user_id, city_name, country_code, temperature, condition)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, user_id, city_name, country_code, searched_at, temperature, condition
                """, (user_id, city_name, country_code, temperature, condition))
            
            row = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "city_name": row[2],
                    "country_code": row[3],
                    "searched_at": row[4].isoformat() if row[4] else None,
                    "temperature": row[5],
                    "condition": row[6]
                }
            return None
    except Exception as e:
        logger.error(f"Failed to add search history: {e}")
        return None


async def get_search_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get search history for a user ordered by searched_at DESC
    
    Args:
        user_id: User ID
        limit: Maximum number of entries to return
        
    Returns:
        List of search history dicts
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, city_name, country_code, searched_at, temperature, condition
                FROM search_history
                WHERE user_id = %s
                ORDER BY searched_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "user_id": row[1],
                    "city_name": row[2],
                    "country_code": row[3],
                    "searched_at": row[4].isoformat() if row[4] else None,
                    "temperature": row[5],
                    "condition": row[6]
                })
            
            cursor.close()
            return history
    except Exception as e:
        logger.error(f"Failed to get search history: {e}")
        return []


async def delete_search_history(history_id: int, user_id: int) -> bool:
    """
    Delete a search history entry
    
    Args:
        history_id: History entry ID
        user_id: User ID (for ownership check)
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM search_history WHERE id = %s AND user_id = %s",
                (history_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
    except Exception as e:
        logger.error(f"Failed to delete search history: {e}")
        return False


async def clear_search_history(user_id: int) -> bool:
    """
    Clear all search history for a user
    
    Args:
        user_id: User ID
        
    Returns:
        True if cleared, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM search_history WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Failed to clear search history: {e}")
        return False


async def cleanup_old_search_history(user_id: int, keep_count: int = 50) -> int:
    """
    Delete old search history entries, keeping only the most recent ones
    
    Args:
        user_id: User ID
        keep_count: Number of entries to keep
        
    Returns:
        Number of entries deleted
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM search_history
                WHERE id IN (
                    SELECT id FROM search_history
                    WHERE user_id = %s
                    ORDER BY searched_at DESC
                    OFFSET %s
                )
            """, (user_id, keep_count))
            
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            
            return deleted
    except Exception as e:
        logger.error(f"Failed to cleanup old search history: {e}")
        return 0
