"""
FILE: backend/app/infrastructure/repositories/user_repository.py
User database operations for authentication and session management
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

from app.infrastructure.database.session import get_db_connection
from app.infrastructure.database.models import WeatherUser, WeatherSession
from app.core.security import hash_session_token, get_session_expiry, generate_user_initials
from app.core.exceptions import DatabaseError, AuthError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for user and session database operations."""
    
    @staticmethod
    async def upsert_user(
        provider: str,
        provider_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> WeatherUser:
        """
        Create a new user or update existing user on login.
        Returns WeatherUser dataclass.
        """
        initials = generate_user_initials(name, email)
        
        query = """
            INSERT INTO weather_users (
                provider, provider_id, email, name, avatar_url, initials, 
                unit_preference, theme, is_active, last_login_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (provider, provider_id) 
            DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                avatar_url = EXCLUDED.avatar_url,
                initials = EXCLUDED.initials,
                last_login_at = NOW(),
                is_active = TRUE
            RETURNING *
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (
                        provider, provider_id, email, name, avatar_url, initials,
                        'C', 'system', True
                    ))
                    row = cursor.fetchone()
                    conn.commit()
                    
                    if not row:
                        raise DatabaseError("Failed to upsert user")
                    
                    logger.info(f"User upserted", provider=provider, email=email)
                    return _row_to_weather_user(row)
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to upsert user: {e}")
                raise DatabaseError(f"User upsert failed: {e}", e)
    
    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[WeatherUser]:
        """Get user by ID, returns WeatherUser or None."""
        query = """
            SELECT * FROM weather_users 
            WHERE id = %s AND is_active = TRUE
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (user_id,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    return _row_to_weather_user(row)
                    
            except Exception as e:
                logger.error(f"Failed to get user {user_id}: {e}")
                raise DatabaseError(f"Failed to get user: {e}", e)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[WeatherUser]:
        """Get user by email, returns WeatherUser or None."""
        query = """
            SELECT * FROM weather_users 
            WHERE email = %s AND is_active = TRUE
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (email,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    return _row_to_weather_user(row)
                    
            except Exception as e:
                logger.error(f"Failed to get user by email {email}: {e}")
                raise DatabaseError(f"Failed to get user: {e}", e)
    
    @staticmethod
    async def create_session(
        user_id: int,
        session_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> WeatherSession:
        """
        Create a new session for a user.
        Stores hashed session token, returns WeatherSession.
        """
        hashed_token = hash_session_token(session_token)
        expires_at = get_session_expiry()
        
        query = """
            INSERT INTO weather_sessions (
                user_id, session_token, expires_at, ip_address, user_agent
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (
                        user_id, hashed_token, expires_at, ip_address, user_agent
                    ))
                    row = cursor.fetchone()
                    conn.commit()
                    
                    if not row:
                        raise DatabaseError("Failed to create session")
                    
                    logger.info(f"Session created for user {user_id}")
                    return _row_to_weather_session(row)
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to create session: {e}")
                raise DatabaseError(f"Session creation failed: {e}", e)
    
    @staticmethod
    async def get_session(session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session with associated user by raw token.
        Returns dict with 'session' and 'user' or None if expired/invalid.
        """
        hashed_token = hash_session_token(session_token)
        
        query = """
            SELECT 
                s.*,
                u.id as user_id,
                u.email,
                u.name,
                u.avatar_url,
                u.initials,
                u.unit_preference,
                u.theme,
                u.provider
            FROM weather_sessions s
            JOIN weather_users u ON s.user_id = u.id
            WHERE s.session_token = %s
              AND s.expires_at > NOW()
              AND u.is_active = TRUE
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (hashed_token,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    return {
                        'session': _row_to_weather_session(row),
                        'user': _row_to_weather_user_from_session(row)
                    }
                    
            except Exception as e:
                logger.error(f"Failed to get session: {e}")
                raise DatabaseError(f"Session lookup failed: {e}", e)
    
    @staticmethod
    async def delete_session(session_token: str) -> bool:
        """
        Delete a session (logout).
        Returns True if session was deleted.
        """
        hashed_token = hash_session_token(session_token)
        
        query = "DELETE FROM weather_sessions WHERE session_token = %s"
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (hashed_token,))
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        logger.info(f"Session deleted")
                    
                    return deleted
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to delete session: {e}")
                raise DatabaseError(f"Session deletion failed: {e}", e)
    
    @staticmethod
    async def delete_expired_sessions() -> int:
        """
        Delete all expired sessions.
        Returns number of sessions deleted.
        """
        query = "DELETE FROM weather_sessions WHERE expires_at <= NOW()"
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    deleted = cursor.rowcount
                    conn.commit()
                    
                    if deleted > 0:
                        logger.info(f"Deleted {deleted} expired sessions")
                    
                    return deleted
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to delete expired sessions: {e}")
                raise DatabaseError(f"Cleanup failed: {e}", e)
    
    @staticmethod
    async def update_preferences(
        user_id: int,
        unit_preference: Optional[str] = None,
        theme: Optional[str] = None
    ) -> WeatherUser:
        """
        Update user preferences (unit and theme).
        """
        updates = []
        params = []
        
        if unit_preference is not None:
            updates.append("unit_preference = %s")
            params.append(unit_preference)
        
        if theme is not None:
            updates.append("theme = %s")
            params.append(theme)
        
        if not updates:
            raise ValueError("No preferences to update")
        
        params.append(user_id)
        query = f"""
            UPDATE weather_users 
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """
        
        async with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    conn.commit()
                    
                    if not row:
                        raise AuthError("User not found")
                    
                    logger.info(f"Preferences updated for user {user_id}")
                    return _row_to_weather_user(row)
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to update preferences: {e}")
                raise DatabaseError(f"Update failed: {e}", e)


# ── Helper functions for converting DB rows to dataclasses ──

def _row_to_weather_user(row: Dict[str, Any]) -> WeatherUser:
    """Convert database row to WeatherUser dataclass."""
    return WeatherUser(
        id=row['id'],
        provider=row['provider'],
        provider_id=row['provider_id'],
        email=row['email'],
        name=row.get('name'),
        avatar_url=row.get('avatar_url'),
        initials=row.get('initials'),
        unit_preference=row.get('unit_preference', 'C'),
        theme=row.get('theme', 'system'),
        is_active=row.get('is_active', True),
        created_at=row.get('created_at', datetime.now()),
        last_login_at=row.get('last_login_at', datetime.now())
    )


def _row_to_weather_user_from_session(row: Dict[str, Any]) -> WeatherUser:
    """Convert session query row to WeatherUser dataclass."""
    return WeatherUser(
        id=row['user_id'],
        provider=row['provider'],
        provider_id='',  # Not needed for profile
        email=row['email'],
        name=row.get('name'),
        avatar_url=row.get('avatar_url'),
        initials=row.get('initials'),
        unit_preference=row.get('unit_preference', 'C'),
        theme=row.get('theme', 'system'),
        is_active=True,
        created_at=datetime.now(),
        last_login_at=datetime.now()
    )


def _row_to_weather_session(row: Dict[str, Any]) -> WeatherSession:
    """Convert database row to WeatherSession dataclass."""
    return WeatherSession(
        id=row['id'],
        user_id=row['user_id'],
        session_token=row['session_token'],
        expires_at=row['expires_at'],
        ip_address=row.get('ip_address'),
        user_agent=row.get('user_agent'),
        created_at=row.get('created_at', datetime.now())
    )