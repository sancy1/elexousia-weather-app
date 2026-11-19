# """
# FILE: backend/app/core/config.py
# Application configuration using pydantic-settings
# """

# from typing import Optional, Literal, List, Any
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field, field_validator
# import json
# import os


# class Settings(BaseSettings):
#     """Application settings loaded from environment variables."""

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore"
#     )

#     # ── Application ──────────────────────────────────────────
#     APP_NAME: str = "Elexousia Weather API"
#     APP_VERSION: str = "1.0.0"
#     DEBUG: bool = False
#     ENVIRONMENT: Literal["development", "staging", "production"] = "development"

#     # ── Server ───────────────────────────────────────────────
#     HOST: str = "0.0.0.0"
#     PORT: int = 8000
#     API_PREFIX: str = "/api"

#     # ── CORS ─────────────────────────────────────────────────
#     # Use a simple string that will be split - no complex parsing
#     ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

#     @field_validator("ALLOWED_ORIGINS", mode="before")
#     @classmethod
#     def parse_allowed_origins(cls, v: Any) -> List[str]:
#         """Parse ALLOWED_ORIGINS safely from string or list"""
#         # If it's already a list, return it
#         if isinstance(v, list):
#             return v

#         # If it's None or empty, return default
#         if v is None or v == "":
#             return ["http://localhost:5173", "http://localhost:3000"]

#         # If it's a string
#         if isinstance(v, str):
#             # Try to parse as JSON first
#             v = v.strip()
#             if v.startswith('['):
#                 try:
#                     parsed = json.loads(v)
#                     if isinstance(parsed, list):
#                         return parsed
#                 except json.JSONDecodeError:
#                     pass

#             # Otherwise split by comma
#             return [origin.strip() for origin in v.split(",") if origin.strip()]

#         # Fallback to default
#         return ["http://localhost:5173", "http://localhost:3000"]

#     # ── Database ─────────────────────────────────────────────
#     DATABASE_URL: str = ""

#     # ── LLM Configuration ────────────────────────────────────
#     LLM_PROVIDER: Literal["ollama", "groq", "gemini"] = "ollama"

#     # Ollama
#     OLLAMA_BASE_URL: str = "http://localhost:11434"
#     OLLAMA_MODEL: str = "llama3.2"

#     # Groq
#     GROQ_API_KEY: Optional[str] = None
#     GROQ_MODEL: str = "mixtral-8x7b-32768"

#     # Gemini
#     GOOGLE_API_KEY: Optional[str] = None
#     GEMINI_MODEL: str = "gemini-1.5-flash"

#     # ── Embeddings ───────────────────────────────────────────
#     EMBED_MODEL: str = "mxbai-embed-large"
#     EMBED_DIM: int = 1024

#     # ── Weather API ──────────────────────────────────────────
#     WEATHER_API_KEY: str = ""
#     WEATHER_API_BASE: str = "https://api.weatherapi.com/v1"

#     # ── OAuth ────────────────────────────────────────────────
#     GOOGLE_CLIENT_ID: Optional[str] = None
#     GOOGLE_CLIENT_SECRET: Optional[str] = None
#     GITHUB_CLIENT_ID: Optional[str] = None
#     GITHUB_CLIENT_SECRET: Optional[str] = None

#     # ── Security ─────────────────────────────────────────────
#     SECRET_KEY: str = "change_this_in_production"
#     SESSION_EXPIRY_DAYS: int = 1

#     # ── Rate Limiting ────────────────────────────────────────
#     RATE_LIMIT_CHAT: int = 30
#     RATE_LIMIT_WEATHER: int = 100
#     RATE_LIMIT_AUTH: int = 10
#     RATE_LIMIT_DEFAULT: int = 200

#     # ── Observability ────────────────────────────────────────
#     SENTRY_DSN: Optional[str] = None
#     LANGCHAIN_TRACING_V2: bool = False
#     LANGCHAIN_API_KEY: Optional[str] = None
#     LANGCHAIN_PROJECT: Optional[str] = None

#     # ── Cache ────────────────────────────────────────────────
#     WEATHER_CACHE_TTL_SECONDS: int = 600
#     MEMORY_CACHE_MAX_SIZE: int = 1000

#     # ── Session Cookie ───────────────────────────────────────
#     COOKIE_NAME: str = "elexousia_session"
#     COOKIE_SECURE: bool = False
#     COOKIE_HTTPONLY: bool = True
#     COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


# # Global settings instance
# settings = Settings()


# ==========================================================================================


# """
# FILE: backend/app/core/config.py
# Application configuration using pydantic-settings
# """

# from typing import Optional, Literal, List, Any
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field, field_validator
# import json
# import os


# class Settings(BaseSettings):
#     """Application settings loaded from environment variables."""

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore"
#     )

#     # ── Application ──────────────────────────────────────────
#     APP_NAME: str = "Elexousia Weather API"
#     APP_VERSION: str = "1.0.0"
#     DEBUG: bool = False
#     ENVIRONMENT: Literal["development", "staging", "production"] = "development"

#     # ── Server ───────────────────────────────────────────────
#     HOST: str = "0.0.0.0"
#     PORT: int = 8000
#     API_PREFIX: str = "/api"

#     # ── CORS ─────────────────────────────────────────────────
#     # Use a simple string that will be split - no complex parsing
#     # ── CORS ─────────────────────────────────────────────────
#     ALLOWED_ORIGINS: List[str] = [
#         "http://localhost:5173",
#         "http://localhost:3000",
#         "https://elexousia-weatherforecast-lovat.vercel.app"
#     ]

#     @field_validator("ALLOWED_ORIGINS", mode="before")
#     @classmethod
#     def parse_allowed_origins(cls, v: Any) -> List[str]:
#         """Parse ALLOWED_ORIGINS safely from string or list"""
#         # If it's already a list, return it
#         if isinstance(v, list):
#             return v

#         # If it's None or empty, return default with Vercel URL
#         if v is None or v == "":
#             return [
#                 "http://localhost:5173",
#                 "http://localhost:3000",
#                 "https://elexousia-weatherforecast-lovat.vercel.app"
#             ]

#         # If it's a string
#         if isinstance(v, str):
#             # Try to parse as JSON first
#             v = v.strip()
#             if v.startswith('['):
#                 try:
#                     parsed = json.loads(v)
#                     if isinstance(parsed, list):
#                         return parsed
#                 except json.JSONDecodeError:
#                     pass

#             # Otherwise split by comma
#             return [origin.strip() for origin in v.split(",") if origin.strip()]

#         # Fallback to default
#         return [
#             "http://localhost:5173",
#             "http://localhost:3000",
#             "https://elexousia-weatherforecast-lovat.vercel.app"
#         ]

#     # ── Database ─────────────────────────────────────────────
#     DATABASE_URL: str = ""

#     # ── LLM Configuration ────────────────────────────────────
#     LLM_PROVIDER: Literal["ollama", "groq", "gemini"] = "ollama"

#     # Ollama
#     OLLAMA_BASE_URL: str = "http://localhost:11434"
#     OLLAMA_MODEL: str = "llama3.2"

#     # Groq
#     GROQ_API_KEY: Optional[str] = None
#     GROQ_MODEL: str = "mixtral-8x7b-32768"

#     # Gemini
#     GOOGLE_API_KEY: Optional[str] = None
#     GEMINI_MODEL: str = "gemini-1.5-flash"

#     # ── Embeddings ───────────────────────────────────────────
#     EMBED_MODEL: str = "mxbai-embed-large"
#     EMBED_DIM: int = 1024

#     # ── Weather API ──────────────────────────────────────────
#     WEATHER_API_KEY: str = ""
#     WEATHER_API_BASE: str = "https://api.weatherapi.com/v1"

#     # ── OAuth ────────────────────────────────────────────────
#     GOOGLE_CLIENT_ID: Optional[str] = None
#     GOOGLE_CLIENT_SECRET: Optional[str] = None
#     GITHUB_CLIENT_ID: Optional[str] = None
#     GITHUB_CLIENT_SECRET: Optional[str] = None

#     # ── Security ─────────────────────────────────────────────
#     SECRET_KEY: str = "change_this_in_production"
#     SESSION_EXPIRY_DAYS: int = 1

#     # ── Rate Limiting ────────────────────────────────────────
#     RATE_LIMIT_CHAT: int = 30
#     RATE_LIMIT_WEATHER: int = 100
#     RATE_LIMIT_AUTH: int = 10
#     RATE_LIMIT_DEFAULT: int = 200

#     # ── Observability ────────────────────────────────────────
#     SENTRY_DSN: Optional[str] = None
#     LANGCHAIN_TRACING_V2: bool = False
#     LANGCHAIN_API_KEY: Optional[str] = None
#     LANGCHAIN_PROJECT: Optional[str] = None

#     # ── Cache ────────────────────────────────────────────────
#     WEATHER_CACHE_TTL_SECONDS: int = 600
#     MEMORY_CACHE_MAX_SIZE: int = 1000

#     # ── Session Cookie ───────────────────────────────────────
#     COOKIE_NAME: str = "elexousia_session"
#     COOKIE_SECURE: bool = False
#     COOKIE_HTTPONLY: bool = True
#     COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


# # Global settings instance
# settings = Settings()


"""
FILE: backend/app/core/config.py
Application configuration using pydantic-settings
"""

from typing import Optional, Literal, List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "Elexousia Weather API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api"

    # ── CORS ─────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://elexousia-weatherforecast-lovat.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        """Parse ALLOWED_ORIGINS safely from string or list"""
        if isinstance(v, list):
            return v

        if v is None or v == "":
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "https://elexousia-weatherforecast-lovat.vercel.app",
            ]

        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

            return [origin.strip() for origin in v.split(",") if origin.strip()]

        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://elexousia-weatherforecast-lovat.vercel.app",
        ]

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = ""

    # ── LLM Configuration ────────────────────────────────────
    LLM_PROVIDER: Literal["ollama", "groq", "gemini"] = "ollama"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com"
    # Primary model for agent calls. Falls back to GROQ_MODEL when unset.
    GROQ_PRIMARY_MODEL: Optional[str] = None
    # Comma-separated fallback models tried in order on HTTP 429/503/404.
    GROQ_FALLBACK_MODELS: str = "openai/gpt-oss-20b,qwen/qwen3.8-27b"
    # Optional JSON map of per-model extra request params, e.g.
    # {"openai/gpt-oss-120b": {"reasoning_effort": "low"}}
    GROQ_MODEL_KWARGS_JSON: str = ""
    # Seconds a rate-limited Groq model sits out before being retried.
    GROQ_MODEL_COOLDOWN_SECONDS: float = 60.0

    # Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Embeddings ───────────────────────────────────────────
    EMBED_MODEL: str = "mxbai-embed-large"
    EMBED_DIM: int = 1024

    # ── Weather API ──────────────────────────────────────────
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE: str = "https://api.weatherapi.com/v1"

    # ── OAuth ────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # ── Security ─────────────────────────────────────────────
    # No default: main.py fails fast in production if this is unset/weak.
    SECRET_KEY: str = ""
    SESSION_EXPIRY_DAYS: int = 1

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_CHAT: int = 30
    RATE_LIMIT_WEATHER: int = 100
    RATE_LIMIT_AUTH: int = 10
    RATE_LIMIT_DEFAULT: int = 200

    # ── Observability ────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None

    # ── Cache ────────────────────────────────────────────────
    WEATHER_CACHE_TTL_SECONDS: int = 600
    MEMORY_CACHE_MAX_SIZE: int = 1000

    # ── Session Cookie ───────────────────────────────────────
    COOKIE_NAME: str = "elexousia_session"
    COOKIE_SECURE: bool = False
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


# Global settings instance
settings = Settings()
