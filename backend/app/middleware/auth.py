"""
FILE: backend/app/middleware/auth.py
Custom authentication middleware for session-based auth
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.dependencies import get_optional_user


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that adds user to request.state.
    Skips auth check for public routes.
    """
    
    # Routes that skip authentication
    PUBLIC_ROUTES = {
        "/",
        "/api/health",
        "/api/health/db",
        "/api/health/agent",
        "/api/weather/current",
        "/api/weather/forecast",
        "/api/search/cities",
        "/api/auth/google",
        "/api/auth/github",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    # Route prefixes that skip authentication
    PUBLIC_PREFIXES = {
        "/api/auth/google/callback",
        "/api/auth/github/callback",
        "/static",
        "/favicon"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add user to request.state if authenticated.
        """
        # Check if route should skip authentication
        path = request.url.path
        
        if self._is_public_route(path):
            # Skip auth, proceed to next middleware
            return await call_next(request)
        
        # Try to get user (returns None if not authenticated)
        user = await get_optional_user(request)
        request.state.user = user
        
        # Proceed to next middleware
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """
        Check if a path is a public route that should skip authentication.
        """
        # Check exact matches
        if path in self.PUBLIC_ROUTES:
            return True
        
        # Check prefix matches
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False