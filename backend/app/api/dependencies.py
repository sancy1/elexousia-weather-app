"""
FILE: backend/app/api/dependencies.py
FastAPI dependencies for authentication and session management
"""

from typing import Optional
from fastapi import Request, HTTPException, Depends
from starlette.responses import JSONResponse

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.database.models import WeatherUser
from app.core.exceptions import AuthError


async def get_current_user(request: Request) -> WeatherUser:
    """
    Extract session token from cookie or Authorization header and verify it.
    Returns WeatherUser if valid, raises HTTPException if invalid.
    
    Priority:
    1. Authorization header (Bearer token)
    2. session_cookie
    """
    # Try Authorization header first
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    else:
        # Fall back to cookie
        token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid session token."
        )
    
    # Verify session
    session_data = await UserRepository.get_session(token)
    
    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please login again."
        )
    
    return session_data['user']


async def get_optional_user(request: Request) -> Optional[WeatherUser]:
    """
    Same as get_current_user but returns None for anonymous users.
    Used on public routes where authentication is optional.
    """
    # Try Authorization header first
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    else:
        # Fall back to cookie
        token = request.cookies.get("session_token")
    
    if not token:
        return None
    
    # Verify session
    session_data = await UserRepository.get_session(token)
    
    if not session_data:
        return None
    
    return session_data['user']


async def verify_session(token: str) -> WeatherUser:
    """
    Verify a session token and return the associated user.
    Used by middleware and auth endpoints.
    
    Args:
        token: Raw session token (not hashed)
    
    Returns:
        WeatherUser if token is valid
    
    Raises:
        AuthError if token is invalid or expired
    """
    session_data = await UserRepository.get_session(token)
    
    if not session_data:
        raise AuthError("Invalid or expired session")
    
    return session_data['user']