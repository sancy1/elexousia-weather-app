"""
FILE: backend/app/infrastructure/database/models.py
Python dataclasses for all 13 PostgreSQL tables (based on actual database schema)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal


# ─────────────────────────────────────────────────────────────
# CORE TABLES
# ─────────────────────────────────────────────────────────────

@dataclass
class City:
    """cities table - 31,561 world cities"""
    id: int
    city_name: str
    ascii_name: str
    country_name: str
    country_code: str
    latitude: Decimal
    longitude: Decimal
    timezone: str
    state_province: Optional[str] = None
    population: Optional[int] = None
    elevation_m: Optional[int] = None
    is_capital: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CityAlias:
    """city_aliases table - 122 nicknames and abbreviations"""
    id: int
    alias: str
    city_id: int
    alias_type: str  # abbreviation, nickname, typo, local_name, etc.
    language: str = 'en'
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CityEmbedding:
    """city_embeddings table - 1024-dim vectors for semantic search"""
    id: int
    city_id: int
    content: str
    embedding: Optional[List[float]] = None  # vector(1024)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherCache:
    """weather_cache table - cached WeatherAPI responses"""
    id: int
    city_id: int
    cache_type: str  # 'current' or 'forecast'
    raw_json: Dict[str, Any]
    forecast_days: Optional[int] = 1
    temperature_c: Optional[Decimal] = None
    condition: Optional[str] = None
    rain_chance: Optional[int] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class SearchLog:
    """search_log table - every city resolution attempt"""
    id: int
    raw_input: str
    normalised_input: Optional[str] = None
    resolved_city_id: Optional[int] = None
    resolution_method: Optional[str] = None  # exact_match, alias_match, vector_match, etc.
    response_status: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    duration_ms: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


# ─────────────────────────────────────────────────────────────
# AUTHENTICATION TABLES
# ─────────────────────────────────────────────────────────────

@dataclass
class WeatherUser:
    """weather_users table - OAuth users"""
    id: int
    provider: str  # 'google' or 'github'
    provider_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    initials: Optional[str] = None
    unit_preference: str = 'C'  # 'C' or 'F'
    theme: str = 'system'  # 'light', 'dark', 'system'
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherSession:
    """weather_sessions table - auth tokens"""
    id: int
    user_id: int
    session_token: str  # hashed
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


# ─────────────────────────────────────────────────────────────
# CONVERSATION TABLES
# ─────────────────────────────────────────────────────────────

@dataclass
class WeatherConversation:
    """weather_conversations table - chat sessions"""
    id: int
    session_id: str  # UUID
    user_id: Optional[int] = None
    title: Optional[str] = None
    city_name: Optional[str] = None
    country_code: Optional[str] = None
    message_count: int = 0
    is_archived: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherMessage:
    """weather_messages table - individual messages with tool trace"""
    id: int
    session_id: str
    user_message: str
    bot_response: str
    city_resolved: Optional[str] = None
    user_id: Optional[int] = None
    role: str = 'user'
    tools_used: Optional[List[Dict[str, Any]]] = None
    response_ms: Optional[int] = None
    temperature_c: Optional[Decimal] = None
    condition: Optional[str] = None
    country_code: Optional[str] = None
    conversation_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


# ─────────────────────────────────────────────────────────────
# PERSONALIZATION TABLES
# ─────────────────────────────────────────────────────────────

@dataclass
class WeatherSavedLocation:
    """weather_saved_locations table - user-pinned cities"""
    id: int
    user_id: int
    city_name: str
    country_name: str
    country_code: str
    latitude: Decimal
    longitude: Decimal
    city_id: Optional[int] = None
    timezone: Optional[str] = None
    label: Optional[str] = None  # 'Home', 'Work', 'Travel'
    display_order: int = 0
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherQuickChip:
    """weather_quick_chips table - pre-built prompt buttons (7 rows)"""
    id: int
    label: str
    prompt_text: str
    icon: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    requires_city: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherNotification:
    """weather_notifications table - rain alerts and heat warnings"""
    id: int
    user_id: int
    city_name: str
    type: str  # 'rain_alert', 'heat_warning', 'storm_alert'
    title: str
    message: str
    country_code: Optional[str] = None
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class WeatherSearchIndex:
    """weather_search_index table - full-text search across content"""
    id: int
    record_type: str  # 'conversation', 'saved_location'
    record_id: int
    display_text: str
    user_id: Optional[int] = None
    secondary_text: Optional[str] = None
    search_vector: Optional[str] = None  # tsvector
    relevance_boost: Decimal = Decimal('1.0')
    updated_at: datetime = field(default_factory=datetime.now)


# ─────────────────────────────────────────────────────────────
# FACTORY FUNCTIONS FOR CREATING MODELS FROM DB ROWS
# ─────────────────────────────────────────────────────────────

def city_from_row(row: Dict[str, Any]) -> City:
    """Create City dataclass from database row."""
    return City(
        id=row['id'],
        city_name=row['city_name'],
        ascii_name=row['ascii_name'],
        country_name=row['country_name'],
        country_code=row['country_code'],
        latitude=row['latitude'],
        longitude=row['longitude'],
        timezone=row['timezone'],
        state_province=row.get('state_province'),
        population=row.get('population'),
        elevation_m=row.get('elevation_m'),
        is_capital=row.get('is_capital', False),
        is_active=row.get('is_active', True),
        created_at=row.get('created_at', datetime.now()),
        updated_at=row.get('updated_at', datetime.now())
    )


def weather_user_from_row(row: Dict[str, Any]) -> WeatherUser:
    """Create WeatherUser dataclass from database row."""
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


def weather_conversation_from_row(row: Dict[str, Any]) -> WeatherConversation:
    """Create WeatherConversation dataclass from database row."""
    return WeatherConversation(
        id=row['id'],
        session_id=row['session_id'],
        user_id=row.get('user_id'),
        title=row.get('title'),
        city_name=row.get('city_name'),
        country_code=row.get('country_code'),
        message_count=row.get('message_count', 0),
        is_archived=row.get('is_archived', False),
        created_at=row.get('created_at', datetime.now()),
        last_active_at=row.get('last_active_at', datetime.now())
    )


def weather_message_from_row(row: Dict[str, Any]) -> WeatherMessage:
    """Create WeatherMessage dataclass from database row."""
    return WeatherMessage(
        id=row['id'],
        session_id=row['session_id'],
        user_message=row['user_message'],
        bot_response=row['bot_response'],
        city_resolved=row.get('city_resolved'),
        user_id=row.get('user_id'),
        role=row.get('role', 'user'),
        tools_used=row.get('tools_used'),
        response_ms=row.get('response_ms'),
        temperature_c=row.get('temperature_c'),
        condition=row.get('condition'),
        country_code=row.get('country_code'),
        conversation_id=row.get('conversation_id'),
        created_at=row.get('created_at', datetime.now())
    )