"""
FILE: backend/app/infrastructure/database/session.py
Database connection management with auto-retry logic
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from functools import wraps
import psycopg2
from psycopg2 import pool, OperationalError
from psycopg2.extras import RealDictCursor

from ...core.config import settings
from ...core.exceptions import DatabaseError
from ...core.logging_config import get_logger

logger = get_logger(__name__)

# Global connection pool
_pool: Optional[pool.SimpleConnectionPool] = None

# Retry configuration
MAX_RETRIES = 5
INITIAL_DELAY = 1  # seconds
MAX_DELAY = 30  # seconds
BACKOFF_FACTOR = 2


def retry_on_db_failure(max_retries: int = MAX_RETRIES, initial_delay: float = INITIAL_DELAY):
    """
    Decorator to retry database operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (OperationalError, psycopg2.OperationalError, DatabaseError) as e:
                    last_exception = e
                    
                    # Check if this is a connection issue
                    error_msg = str(e).lower()
                    is_connection_error = any(phrase in error_msg for phrase in [
                        'could not connect', 'connection refused', 'timeout',
                        'network is unreachable', 'name resolution'
                    ])
                    
                    if not is_connection_error or attempt == max_retries:
                        logger.error(
                            f"Database operation failed after {attempt} retries",
                            error=str(e),
                            attempt=attempt,
                            max_retries=max_retries
                        )
                        raise DatabaseError(f"Database operation failed: {e}", e)
                    
                    logger.warning(
                        f"Database connection error, retrying in {delay}s",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e)
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * BACKOFF_FACTOR, MAX_DELAY)
                    
                    # Attempt to reconnect
                    await reconnect_pool()
                    
            raise DatabaseError(f"Failed after {max_retries} retries: {last_exception}", last_exception)
        return wrapper
    return decorator


async def reconnect_pool():
    """
    Reconnect the database pool if it's broken.
    """
    global _pool
    
    logger.info("Attempting to reconnect database pool...")
    
    # Close existing pool if it exists
    if _pool:
        try:
            _pool.closeall()
            logger.debug("Closed existing connection pool")
        except Exception as e:
            logger.warning(f"Error closing existing pool: {e}")
    
    # Create new pool
    try:
        await init_db_pool()
        logger.info("Database pool reconnected successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reconnect database pool: {e}")
        return False


async def init_db_pool():
    """
    Initialize the database connection pool with retry logic.
    """
    global _pool
    
    logger.info(f"Initializing database connection pool (max_retries={MAX_RETRIES})...")
    
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES + 1):
        try:
            _pool = pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=settings.DATABASE_URL,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=10
            )
            
            # Test the connection
            with _pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 as test, NOW() as server_time")
                    result = cur.fetchone()
                    logger.info(f"Database connection verified", test=result[0])
                _pool.putconn(conn)
            
            logger.info(
                "Database connection pool initialized",
                min_connections=2,
                max_connections=10,
                host=settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'
            )
            return True
            
        except Exception as e:
            logger.warning(
                f"Database connection attempt {attempt + 1} failed",
                error=str(e),
                attempt=attempt + 1,
                max_retries=MAX_RETRIES
            )
            
            if attempt == MAX_RETRIES:
                logger.error("Failed to initialize database pool after all retries")
                raise DatabaseError(f"Could not connect to database after {MAX_RETRIES} attempts: {e}", e)
            
            logger.info(f"Retrying connection in {delay} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * BACKOFF_FACTOR, MAX_DELAY)
    
    return False


async def close_db_pool():
    """
    Close the database connection pool.
    """
    global _pool
    if _pool:
        try:
            _pool.closeall()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.warning(f"Error closing database pool: {e}")
        finally:
            _pool = None


@asynccontextmanager
async def get_db_connection_with_retry(max_retries: int = 3, lazy_init: bool = True):
    """
    Get a database connection from the pool with retry logic.

    Args:
        max_retries: Maximum number of retry attempts for this specific connection
        lazy_init: If True, initialize pool on first use; if False, require pool to be ready

    Yields:
        Database connection
    """
    if not _pool:
        if lazy_init:
            logger.warning("Database pool not initialized, attempting to initialize...")
            try:
                await init_db_pool()
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise DatabaseError("Database not available")

        if not _pool:
            raise DatabaseError("Database pool not available")

    last_exception = None
    delay = INITIAL_DELAY

    for attempt in range(max_retries + 1):
        try:
            conn = _pool.getconn()
            # Test connection is alive
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            yield conn
            return
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Failed to get database connection (attempt {attempt + 1})",
                error=str(e)
            )

            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay = min(delay * BACKOFF_FACTOR, MAX_DELAY)
            else:
                logger.error("Failed to get database connection after all retries")
                raise DatabaseError(f"Database connection failed: {e}", e)
        finally:
            if 'conn' in locals() and conn:
                _pool.putconn(conn)


# Original function for backward compatibility
@asynccontextmanager
async def get_db_connection():
    """
    Get a database connection from the pool (with default retries).
    """
    async with get_db_connection_with_retry(max_retries=3) as conn:
        yield conn


async def check_db_health() -> dict:
    """
    Check database health with connection retry.
    """
    start_time = time.time()
    
    for attempt in range(MAX_RETRIES):
        try:
            async with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 as healthy, NOW() as server_time")
                    result = cur.fetchone()
                    
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "connected",
                "latency_ms": round(latency_ms, 2),
                "server_time": result[1].isoformat() if result else None,
                "attempt": attempt + 1,
                "retry_count": attempt
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Health check failed after {MAX_RETRIES} attempts", error=str(e))
                return {
                    "status": "disconnected",
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                    "attempt": attempt + 1,
                    "retry_count": attempt
                }
            
            logger.warning(f"Health check attempt {attempt + 1} failed, retrying...", error=str(e))
            await asyncio.sleep(INITIAL_DELAY * (attempt + 1))
    
    return {
        "status": "disconnected",
        "latency_ms": None,
        "error": "Maximum retries exceeded"
    }


# Health check for application startup
async def wait_for_db(max_wait_seconds: int = 30):
    """
    Wait for database to become available on startup.
    
    Args:
        max_wait_seconds: Maximum time to wait for database connection
    
    Returns:
        bool: True if database connected, False otherwise
    """
    logger.info(f"Waiting for database to become available (max {max_wait_seconds}s)...")
    
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait_seconds:
        attempt += 1
        try:
            async with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    
            logger.info(f"Database is ready! (took {time.time() - start_time:.1f}s)")
            return True
            
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= max_wait_seconds:
                logger.error(f"Database not available after {max_wait_seconds}s: {e}")
                return False
            
            logger.debug(f"Database not ready yet (attempt {attempt}), waiting...")
            await asyncio.sleep(2)
    
    return False