"""
FILE: backend/app/api/routes/chips.py
Quick chips endpoint for prompt suggestions
"""

from fastapi import APIRouter

from app.infrastructure.database.session import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chips", tags=["Chips"])


@router.get("")
async def get_chips():
    """
    Returns all active quick chips ordered by display_order
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, prompt_text, icon, requires_city
                FROM weather_quick_chips
                WHERE is_active = true
                ORDER BY display_order ASC;
            """)
            
            chips = []
            for row in cursor.fetchall():
                chips.append({
                    "id": row[0],
                    "label": row[1],
                    "prompt_text": row[2],
                    "icon": row[3],
                    "requires_city": row[4]
                })
            
            cursor.close()
            
            return {"chips": chips}
            
    except Exception as e:
        logger.error(f"Failed to fetch chips: {e}")
        # Return default chips if database query fails
        return {
            "chips": [
                {"id": 1, "label": "3-day forecast", "prompt_text": "Give me a detailed 3-day weather forecast for", "icon": "📅", "requires_city": True},
                {"id": 2, "label": "Current weather", "prompt_text": "What's the current weather in", "icon": "🌤️", "requires_city": True},
                {"id": 3, "label": "Will it rain?", "prompt_text": "Will it rain today in", "icon": "🌧️", "requires_city": True},
                {"id": 4, "label": "Travel advice", "prompt_text": "I'm travelling to", "icon": "✈️", "requires_city": True},
                {"id": 5, "label": "What to wear", "prompt_text": "What should I wear today in", "icon": "👕", "requires_city": True},
                {"id": 6, "label": "UV index", "prompt_text": "What's the UV index in", "icon": "☀️", "requires_city": True},
                {"id": 7, "label": "Weekend forecast", "prompt_text": "What's the weekend forecast for", "icon": "📆", "requires_city": True},
            ]
        }
