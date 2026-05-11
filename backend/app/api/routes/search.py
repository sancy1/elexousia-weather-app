"""
FILE: backend/app/api/routes/search.py
Search endpoint - searches across conversations, saved locations, and cities
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.infrastructure.database.session import get_db_connection
from app.api.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search_all(q: str = Query(..., description="Search query"), limit: int = Query(20, ge=1, le=100), user = Depends(get_current_user)):
    """
    Searches all indexed content for user (conversations, saved locations)
    Uses the weather_search_index table and search_weather_app() PostgreSQL function
    """
    user_id = user.id
    
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Call the search function
            cursor.execute(
                "SELECT * FROM search_weather_app(%s, %s, %s)",
                (q, user_id, limit)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "type": row[0],  # saved_location, conversation, etc.
                    "id": row[1],
                    "display": row[2],
                    "secondary": row[3],
                    "rank": row[4]
                })
            
            cursor.close()
            
            return {
                "results": results,
                "total": len(results),
                "query": q
            }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/cities")
async def search_cities(q: str = Query(..., description="Search query"), limit: int = Query(10, ge=1, le=50)):
    """
    Searches global cities table for city picker (no auth required)
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Search cities by name
            cursor.execute("""
                SELECT id, city_name, country_name, country_code, latitude, longitude, timezone
                FROM cities
                WHERE city_name ILIKE %s OR country_name ILIKE %s
                ORDER BY 
                    CASE WHEN city_name ILIKE %s THEN 1 ELSE 2 END,
                    city_name
                LIMIT %s
            """, (f"%{q}%", f"%{q}%", f"{q}%", limit))
            
            cities = []
            for row in cursor.fetchall():
                cities.append({
                    "id": row[0],
                    "city_name": row[1],
                    "country_name": row[2],
                    "country_code": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "timezone": row[6]
                })
            
            cursor.close()
            
            return {
                "cities": cities,
                "total": len(cities),
                "query": q
            }
    except Exception as e:
        logger.error(f"City search failed: {e}")
        raise HTTPException(status_code=500, detail="City search failed")