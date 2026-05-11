"""
FILE: backend/app/middleware/rate_limit.py
Rate limiting middleware for API endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict
from time import time
from typing import Dict
import asyncio

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        # Store request counts: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    def _get_key(self, request: Request, limit_type: str) -> str:
        """Generate a unique key for rate limiting based on type."""
        if limit_type == "user":
            # For user-based limiting, use user_id if authenticated, else IP
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                return f"user:{token}"
            return f"ip:{request.client.host}"
        elif limit_type == "ip":
            # For IP-based limiting
            return f"ip:{request.client.host}"
        else:
            return f"ip:{request.client.host}"
    
    def _clean_old_requests(self, key: str, window_seconds: int):
        """Remove requests older than the time window."""
        now = time()
        self.requests[key] = [
            (timestamp, count) for timestamp, count in self.requests[key]
            if now - timestamp < window_seconds
        ]
    
    async def check_rate_limit(
        self,
        request: Request,
        limit: int,
        window_seconds: int,
        limit_type: str = "user"
    ) -> bool:
        """
        Check if the request should be rate limited.
        
        Args:
            request: FastAPI request object
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            limit_type: "user" or "ip"
        
        Returns:
            True if allowed, False if rate limited
        """
        async with self.lock:
            key = self._get_key(request, limit_type)
            now = time()
            
            # Clean old requests
            self._clean_old_requests(key, window_seconds)
            
            # Count requests in window
            request_count = sum(count for _, count in self.requests[key])
            
            if request_count >= limit:
                logger.warning(f"Rate limit exceeded for {key}: {request_count}/{limit}")
                return False
            
            # Add this request
            self.requests[key].append((now, 1))
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configuration per endpoint
RATE_LIMITS = {
    # Chat endpoint - 30 req/min (Ollama is slow)
    "/api/chat": {"limit": 30, "window": 60, "type": "user"},
    "/api/chat/stop": {"limit": 30, "window": 60, "type": "user"},
    
    # Weather endpoints - 100 req/min (WeatherAPI limits)
    "/api/weather/auto": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/current": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/forecast": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/hourly": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/detail": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/compare": {"limit": 100, "window": 60, "type": "ip"},
    "/api/weather/wear": {"limit": 100, "window": 60, "type": "ip"},
    
    # Auth endpoints - 10 req/min (prevent brute force)
    "/api/auth/google": {"limit": 10, "window": 60, "type": "ip"},
    "/api/auth/google/callback": {"limit": 10, "window": 60, "type": "ip"},
    "/api/auth/github": {"limit": 10, "window": 60, "type": "ip"},
    "/api/auth/github/callback": {"limit": 10, "window": 60, "type": "ip"},
    
    # Default - 200 req/min for all other routes
    "default": {"limit": 200, "window": 60, "type": "user"}
}


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.
    """
    path = request.url.path
    
    # Get rate limit config for this path
    config = RATE_LIMITS.get(path, RATE_LIMITS["default"])
    
    # Check rate limit
    allowed = await rate_limiter.check_rate_limit(
        request,
        limit=config["limit"],
        window_seconds=config["window"],
        limit_type=config["type"]
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded: {config['limit']} requests per {config['window']} seconds",
                "limit": config["limit"],
                "window": config["window"]
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(config["limit"])
    response.headers["X-RateLimit-Window"] = str(config["window"])
    
    return response