"""
FILE: backend/app/infrastructure/cache/memory_cache.py
In-process LRU cache for repeated queries
"""

from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import Lock
import time

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 600):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple] = OrderedDict()
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, timestamp = self.cache[key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            # Remove if already exists
            if key in self.cache:
                del self.cache[key]
            
            # Add to end
            self.cache[key] = (value, time.time())
            
            # Evict oldest if over capacity
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.ttl_seconds
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)


# Global cache instances
_weather_cache: Optional[LRUCache] = None
_city_cache: Optional[LRUCache] = None


def get_weather_cache() -> LRUCache:
    """Get or create weather cache singleton"""
    global _weather_cache
    if _weather_cache is None:
        max_size = getattr(settings, 'MEMORY_CACHE_MAX_SIZE', 1000)
        ttl = getattr(settings, 'WEATHER_CACHE_TTL_SECONDS', 600)
        _weather_cache = LRUCache(max_size=max_size, ttl_seconds=ttl)
        logger.info(f"Initialized weather cache: max_size={max_size}, ttl={ttl}s")
    return _weather_cache


def get_city_cache() -> LRUCache:
    """Get or create city cache singleton"""
    global _city_cache
    if _city_cache is None:
        _city_cache = LRUCache(max_size=500, ttl_seconds=3600)  # 1 hour for city data
        logger.info("Initialized city cache: max_size=500, ttl=3600s")
    return _city_cache


def cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a cache key from parameters
    
    Args:
        prefix: Key prefix
        **kwargs: Parameters to include in key
        
    Returns:
        Cache key string
    """
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}={value}")
    return ":".join(parts)