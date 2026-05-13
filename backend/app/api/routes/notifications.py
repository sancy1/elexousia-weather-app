"""
FILE: backend/app/api/routes/notifications.py
Notifications endpoints
"""

from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Optional

from app.infrastructure.database.session import get_db_connection
from app.api.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(user = Depends(get_current_user)):
    """
    Returns unread notifications count + list for bell icon
    """
    user_id = user.id
    
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get unread count
            cursor.execute(
                "SELECT COUNT(*) FROM weather_notifications WHERE user_id = %s AND is_read = FALSE",
                (user_id,)
            )
            unread_count = cursor.fetchone()[0]
            
            # Get all notifications
            cursor.execute("""
                SELECT id, user_id, type, city_name, title, message, is_read, created_at
                FROM weather_notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    "id": row[0],
                    "user_id": row[1],
                    "type": row[2],
                    "city_name": row[3],
                    "title": row[4],
                    "message": row[5],
                    "is_read": row[6],
                    "created_at": row[7].isoformat() if row[7] else None
                })
            
            cursor.close()
            
            return {
                "unread_count": unread_count,
                "notifications": notifications
            }
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int = Path(..., description="Notification ID"),
    user = Depends(get_current_user)
):
    """
    Marks a notification as read
    """
    user_id = user.id
    
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE weather_notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
                (notification_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            if affected > 0:
                return {"message": "Notification marked as read"}
            else:
                raise HTTPException(status_code=404, detail="Notification not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


@router.patch("/read-all")
async def mark_all_as_read(user = Depends(get_current_user)):
    """
    Marks all notifications as read
    """
    user_id = user.id
    
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE weather_notifications SET is_read = TRUE WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            
            cursor.close()
            
            return {"message": "All notifications marked as read"}
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int = Path(..., description="Notification ID"),
    user = Depends(get_current_user)
):
    """
    Deletes a notification
    """
    user_id = user.id
    
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM weather_notifications WHERE id = %s AND user_id = %s",
                (notification_id, user_id)
            )
            conn.commit()
            
            affected = cursor.rowcount
            cursor.close()
            
            if affected > 0:
                return {"message": "Notification deleted"}
            else:
                raise HTTPException(status_code=404, detail="Notification not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.post("/check")
async def check_notifications(request):
    """
    Internal/cron endpoint: Checks saved locations and creates alerts if needed
    This should be called periodically (e.g., every hour) to check weather conditions
    """
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Same source as notification_checker_task in app.main (weather_saved_locations)
            cursor.execute("""
                SELECT id, user_id, city_name, latitude, longitude
                FROM weather_saved_locations
            """)
            
            locations = cursor.fetchall()
            
            from app.infrastructure.external.weather_api import fetch_forecast
            
            notifications_created = 0
            
            for loc in locations:
                location_id, user_id, city_name, lat, lon = loc
                
                try:
                    # Get forecast for today
                    forecast = await fetch_forecast(lat, lon, days=1)
                    today = forecast["forecast"]["forecastday"][0]["day"]
                    
                    # Check for rain alert (>70% chance)
                    if today["daily_chance_of_rain"] > 70:
                        cursor.execute("""
                            INSERT INTO weather_notifications 
                            (user_id, type, city_name, title, message, is_read)
                            VALUES (%s, %s, %s, %s, %s, FALSE)
                            ON CONFLICT DO NOTHING
                        """, (
                            user_id,
                            "rain_alert",
                            city_name,
                            "Rain expected today",
                            f"{today['daily_chance_of_rain']}% chance of rain in {city_name}. Pack an umbrella."
                        ))
                        notifications_created += cursor.rowcount
                    
                    # Check for extreme heat (>35°C)
                    if today["maxtemp_c"] > 35:
                        cursor.execute("""
                            INSERT INTO weather_notifications 
                            (user_id, type, city_name, title, message, is_read)
                            VALUES (%s, %s, %s, %s, %s, FALSE)
                            ON CONFLICT DO NOTHING
                        """, (
                            user_id,
                            "heat_alert",
                            city_name,
                            "Extreme heat warning",
                            f"Temperature in {city_name} will reach {today['maxtemp_c']}°C. Stay hydrated."
                        ))
                        notifications_created += cursor.rowcount
                    
                    # Check for extreme cold (<0°C)
                    if today["mintemp_c"] < 0:
                        cursor.execute("""
                            INSERT INTO weather_notifications 
                            (user_id, type, city_name, title, message, is_read)
                            VALUES (%s, %s, %s, %s, %s, FALSE)
                            ON CONFLICT DO NOTHING
                        """, (
                            user_id,
                            "cold_alert",
                            city_name,
                            "Freezing warning",
                            f"Temperature in {city_name} will drop to {today['mintemp_c']}°C. Dress warmly."
                        ))
                        notifications_created += cursor.rowcount
                    
                except Exception as e:
                    logger.error(f"Failed to check weather for {city_name}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            
            return {
                "message": "Weather check completed",
                "notifications_created": notifications_created
            }
    except Exception as e:
        logger.error(f"Failed to check notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to check notifications")