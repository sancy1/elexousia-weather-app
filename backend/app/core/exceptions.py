"""
FILE: backend/app/core/exceptions.py
Custom exceptions for Elexousia Weather API
"""

from typing import Optional, Any


class WeatherAgentError(Exception):
    """Base exception for all weather agent errors."""
    
    def __init__(self, message: str, code: str = "AGENT_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class CityNotFoundError(WeatherAgentError):
    """Raised when a city cannot be resolved."""
    
    def __init__(self, query: str):
        super().__init__(
            message=f"Cannot resolve city: '{query}'. Please try a different name.",
            code="CITY_NOT_FOUND",
            status_code=404
        )
        self.query = query


class AuthError(WeatherAgentError):
    """Raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication required", status_code: int = 401):
        super().__init__(
            message=message,
            code="AUTH_REQUIRED",
            status_code=status_code
        )


class InvalidTokenError(AuthError):
    """Raised when a session token is invalid or expired."""
    
    def __init__(self):
        super().__init__(
            message="Invalid or expired session token. Please log in again.",
            status_code=401
        )


class DatabaseError(WeatherAgentError):
    """Raised for database connection or query errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"Database error: {message}",
            code="DATABASE_ERROR",
            status_code=500
        )
        self.original_error = original_error


class RateLimitError(WeatherAgentError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
        self.retry_after = retry_after


class WeatherAPIError(WeatherAgentError):
    """Raised when WeatherAPI.com request fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"Weather API error: {message}",
            code="WEATHER_API_ERROR",
            status_code=503
        )
        self.original_error = original_error


class LLMProviderError(WeatherAgentError):
    """Raised when LLM provider fails."""
    
    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"LLM provider '{provider}' error: {message}",
            code="LLM_ERROR",
            status_code=503
        )