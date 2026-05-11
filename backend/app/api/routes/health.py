"""
FILE: backend/app/api/routes/health.py
Health check endpoints with DB and Ollama status
"""

from fastapi import APIRouter, Request
from datetime import datetime
import time
import httpx

from app.core.config import settings
from app.core.logging_config import get_logger
from app.infrastructure.database.session import check_db_health

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)

START_TIME = datetime.now()


async def check_ollama_status() -> dict:
    """Check Ollama status and return available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Check if our required models are available
                chat_model_available = settings.OLLAMA_MODEL in models
                embed_model_available = settings.EMBED_MODEL in models
                
                return {
                    "status": "running" if chat_model_available else "model_missing",
                    "models": models[:10],  # Limit to first 10
                    "chat_model": settings.OLLAMA_MODEL,
                    "chat_model_available": chat_model_available,
                    "embed_model": settings.EMBED_MODEL,
                    "embed_model_available": embed_model_available
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "status": "unreachable",
            "error": "Cannot connect to Ollama. Run: ollama serve"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def full_health_check():
    """
    Comprehensive health check including DB status, Ollama status, app version, uptime.
    """
    uptime_seconds = (datetime.now() - START_TIME).total_seconds()
    
    # Check database health
    db_status = await check_db_health()
    
    # Check Ollama status
    ollama_status = await check_ollama_status()
    
    is_healthy = (
        db_status.get("status") == "connected" and
        ollama_status.get("status") in ["running", "model_missing"]
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": int(uptime_seconds),
        "database": db_status,
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health/db")
async def database_health():
    """
    Pings Neon DB — returns latency in ms.
    """
    return await check_db_health()


@router.get("/health/agent")
async def agent_health():
    """
    Pings Ollama — returns model list and status.
    """
    return await check_ollama_status()