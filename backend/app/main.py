"""
FILE: backend/app/main.py
Elexousia Weather API - Main Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
import time
import asyncio
import psycopg2
from dotenv import load_dotenv

from starlette.middleware.sessions import SessionMiddleware

# Import routers
from app.api.routes import auth, weather, chat, chips, saved_locations, conversations, search, notifications, search_history
from app.middleware.rate_limit import rate_limit_middleware
from app.core.config import settings

load_dotenv()

# Application start time
START_TIME = datetime.now()


async def notification_checker_task():
    """Background task that checks for weather notifications every hour"""
    from app.infrastructure.database.session import get_db_connection
    from app.infrastructure.external.weather_api import fetch_forecast
    from app.core.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    while True:
        try:
            logger.info("Running notification check task...")
            
            async with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all saved locations from weather_saved_locations
                cursor.execute("""
                    SELECT id, user_id, city_name, latitude, longitude
                    FROM weather_saved_locations
                """)
                
                locations = cursor.fetchall()
                
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
                
                if notifications_created > 0:
                    logger.info(f"Notification check completed: {notifications_created} notifications created")
                else:
                    logger.info("Notification check completed: no new notifications")
                
        except Exception as e:
            logger.error(f"Notification check task failed: {e}")
        
        # Wait for 1 hour before running again
        await asyncio.sleep(3600)  # 1 hour in seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("\n" + "="*60)
    print("🚀 Starting Elexousia Weather API")
    print("="*60)
    print(f"📍 Server: http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', 8000)}")
    print(f"📚 Docs: http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', 8000)}/docs")

    # Check database connection status
    print("\n🔍 Checking database connection...")
    try:
        import psycopg2
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            print("✅ Database connected")
            conn.close()
        else:
            print("⚠️  DATABASE_URL not configured")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)[:50]}...")

    # Start background notification checker task
    print("🔔 Starting notification checker (runs every hour)...")
    notification_task = asyncio.create_task(notification_checker_task())
    print("✅ Notification checker started")

    print("="*60 + "\n")

    yield

    print("\n👋 Shutting down...")
    print("🔔 Stopping notification checker...")
    notification_task.cancel()
    try:
        await notification_task
    except asyncio.CancelledError:
        pass
    print("✅ Notification checker stopped")
    print("\n")


# Create FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "Elexousia Weather API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Intelligent weather forecasting with AI agent",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Add SessionMiddleware after CORS
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change_this_in_production"),
    session_cookie="elexousia_oauth_state"
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(chips.router, prefix="/api")
app.include_router(saved_locations.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(search_history.router, prefix="/api")

# ─────────────────────────────────────────────────────────────
# HEALTH ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/")
@app.get("/api/health")
async def health_check():
    """Basic health check"""
    uptime = (datetime.now() - START_TIME).total_seconds()
    
    return {
        "status": "healthy",
        "service": os.getenv("APP_NAME", "Elexousia Weather API"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "uptime_seconds": int(uptime),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health/db")
async def db_health_check():
    """Database health check with retry"""
    start = time.time()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            DATABASE_URL = os.getenv("DATABASE_URL")
            if not DATABASE_URL:
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": "DATABASE_URL not configured",
                        "latency_ms": None
                    }
                )
            
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test, NOW() as server_time, current_database()")
            test, server_time, db_name = cursor.fetchone()
            cursor.close()
            conn.close()
            
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": "connected",
                "database": db_name,
                "latency_ms": round(latency_ms, 2),
                "server_time": server_time.isoformat(),
                "attempt": attempt + 1
            }
            
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            
            if attempt == max_retries - 1:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "disconnected",
                        "error": str(e),
                        "latency_ms": round(latency_ms, 2),
                        "attempts": max_retries
                    }
                )
            
            # Wait before retry
            import asyncio
            await asyncio.sleep(1 * (attempt + 1))
    
    return {
        "status": "disconnected",
        "latency_ms": None
    }


@app.get("/api/health/agent")
async def agent_health_check():
    """Agent/AI health check"""
    import httpx
    
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Check if our model is available
                model_available = any(ollama_model in name for name in model_names)
                
                return {
                    "status": "healthy" if model_available else "degraded",
                    "ollama": {
                        "status": "connected",
                        "url": ollama_url,
                        "models_available": len(models),
                        "default_model": ollama_model,
                        "model_available": model_available
                    }
                }
    except Exception as e:
        return {
            "status": "degraded",
            "ollama": {
                "status": "unavailable",
                "error": str(e),
                "url": ollama_url
            }
        }


# ─────────────────────────────────────────────────────────────
# WEATHER ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/api/weather/current")
async def get_current_weather(city: str = "Lagos"):
    """Get current weather for any city"""
    import httpx
    
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    if not WEATHER_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "WEATHER_API_KEY not configured"}
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.weatherapi.com/v1/current.json",
                params={"key": WEATHER_API_KEY, "q": city},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "city": data["location"]["name"],
                    "country": data["location"]["country"],
                    "temperature_c": data["current"]["temp_c"],
                    "temperature_f": data["current"]["temp_f"],
                    "feels_like_c": data["current"]["feelslike_c"],
                    "feels_like_f": data["current"]["feelslike_f"],
                    "condition": data["current"]["condition"]["text"],
                    "humidity": data["current"]["humidity"],
                    "wind_kph": data["current"]["wind_kph"],
                    "uv_index": data["current"].get("uv", 0)
                }
            else:
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": f"Weather API error: {response.status_code}"}
                )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/weather/forecast")
async def get_weather_forecast(city: str = "Lagos", days: int = 3):
    """Get weather forecast for a city"""
    import httpx
    
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    days = min(max(days, 1), 7)  # Limit to 1-7 days
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.weatherapi.com/v1/forecast.json",
                params={"key": WEATHER_API_KEY, "q": city, "days": days},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                forecast = []
                
                for day in data["forecast"]["forecastday"]:
                    forecast.append({
                        "date": day["date"],
                        "max_temp_c": day["day"]["maxtemp_c"],
                        "min_temp_c": day["day"]["mintemp_c"],
                        "condition": day["day"]["condition"]["text"],
                        "rain_chance": day["day"]["daily_chance_of_rain"],
                        "uv_index": day["day"]["uv"]
                    })
                
                return {
                    "success": True,
                    "city": data["location"]["name"],
                    "country": data["location"]["country"],
                    "forecast": forecast
                }
            else:
                return {"error": f"Weather API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────
# SEARCH ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/api/search/cities")
async def search_cities(q: str, limit: int = 5):
    """Search for cities in the database"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT city_name, country_name, country_code, population
            FROM cities
            WHERE city_name ILIKE %s OR ascii_name ILIKE %s
            ORDER BY population DESC NULLS LAST
            LIMIT %s
        """, (f"{q}%", f"{q}%", limit))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "query": q,
            "results": [
                {
                    "city": r[0],
                    "country": r[1],
                    "country_code": r[2],
                    "population": r[3]
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e), "query": q, "results": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )