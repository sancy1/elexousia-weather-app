"""
FILE: backend/app/agent/tools/city_resolver.py
City resolution with database lookup, vector search, and API fallback
"""

import re
import json
from typing import Optional, Dict, Any

from app.infrastructure.database.session import get_db_connection
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Region detection for hybrid vector search
REGION_MAP = {
    "west_africa_coastal": ["NG", "GH", "SN", "CI", "BJ", "TG", "LR", "SL", "GN", "GM", "CV", "GW"],
    "west_africa": ["NG", "GH", "SN", "CI", "BJ", "TG", "LR", "SL", "GN", "GM", "CV", "GW", "ML", "BF", "NE", "MR"],
    "east_africa": ["KE", "TZ", "ET", "UG", "RW", "BI", "ER", "DJ", "SO", "MG"],
    "north_africa": ["EG", "LY", "TN", "DZ", "MA", "SD"],
    "middle_east": ["AE", "SA", "IQ", "IR", "IL", "JO", "LB", "KW", "QA", "BH", "OM", "YE", "SY", "TR"],
    "south_asia": ["IN", "PK", "BD", "LK", "NP", "AF"],
    "east_asia": ["CN", "JP", "KR", "TW", "HK", "MN"],
    "southeast_asia": ["SG", "TH", "ID", "MY", "VN", "PH", "MM", "KH", "LA"],
    "western_europe": ["GB", "FR", "DE", "IT", "ES", "NL", "BE", "PT", "AT", "CH", "IE"],
    "north_america": ["US", "CA", "MX"],
    "south_america": ["BR", "AR", "CO", "PE", "VE", "CL", "EC", "BO", "PY", "UY"],
    "scandinavia": ["SE", "NO", "DK", "FI", "IS"],
    "oceania": ["AU", "NZ", "PG", "FJ"],
}

QUERY_KEYWORDS = {
    "west africa": "west_africa",
    "west african": "west_africa",
    "coastal west africa": "west_africa_coastal",
    "east africa": "east_africa",
    "north africa": "north_africa",
    "middle east": "middle_east",
    "south asia": "south_asia",
    "east asia": "east_asia",
    "southeast asia": "southeast_asia",
    "western europe": "western_europe",
    "north america": "north_america",
    "south america": "south_america",
    "scandinavia": "scandinavia",
    "nordic": "scandinavia",
    "oceania": "oceania",
    "nigeria": ["NG"],
    "ghana": ["GH"],
    "japan": ["JP"],
    "france": ["FR"],
    "germany": ["DE"],
    "india": ["IN"],
    "china": ["CN"],
    "brazil": ["BR"],
    "australia": ["AU"],
}

EMBED_MODEL = settings.EMBED_MODEL if hasattr(settings, 'EMBED_MODEL') else "mxbai-embed-large"
QUERY_PREFIX = "search_query: "


# Common city name normalizations
CITY_NORMALIZATIONS = {
    "newyork": "New York",
    "newyorkcity": "New York",
    "nyc": "New York",
    "losangeles": "Los Angeles",
    "la": "Los Angeles",
    "sanfrancisco": "San Francisco",
    "sf": "San Francisco",
    "washingtondc": "Washington, D.C.",
    "washington": "Washington, D.C.",
    "philadelphia": "Philadelphia",
    "philly": "Philadelphia",
    "houston": "Houston",
    "chicago": "Chicago",
    "dallas": "Dallas",
    "miami": "Miami",
    "atlanta": "Atlanta",
    "boston": "Boston",
    "seattle": "Seattle",
    "denver": "Denver",
    "lasvegas": "Las Vegas",
    "portland": "Portland",
    "austin": "Austin",
    "sanantonio": "San Antonio",
    "sandiego": "San Diego",
    "phoenix": "Phoenix",
    "tampa": "Tampa",
    "orlando": "Toronto",  # Common confusion
    "toronto": "Toronto",
    "vancouver": "Vancouver",
    "montreal": "Montreal",
    "calgary": "Calgary",
    "edmonton": "Edmonton",
    "ottawa": "Ottawa",
    "london": "London",
    "manchester": "Manchester",
    "birmingham": "Birmingham",
    "liverpool": "Liverpool",
    "leeds": "Leeds",
    "glasgow": "Glasgow",
    "edinburgh": "Edinburgh",
    "paris": "Paris",
    "berlin": "Berlin",
    "rome": "Rome",
    "madrid": "Madrid",
    "amsterdam": "Amsterdam",
    "vienna": "Vienna",
    "prague": "Prague",
    "budapest": "Budapest",
    "warsaw": "Warsaw",
    "bucharest": "Bucharest",
    "sofia": "Sofia",
    "athens": "Athens",
    "lisbon": "Lisbon",
    "dublin": "Dublin",
    "stockholm": "Stockholm",
    "oslo": "Oslo",
    "copenhagen": "Copenhagen",
    "helsinki": "Helsinki",
    "reykjavik": "Reykjavik",
    "moscow": "Moscow",
    "stpetersburg": "Saint Petersburg",
    "kiev": "Kyiv",
    "minsk": "Minsk",
    "riga": "Riga",
    "vilnius": "Vilnius",
    "tallinn": "Tallinn",
    "beijing": "Beijing",
    "shanghai": "Shanghai",
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "seoul": "Seoul",
    "busan": "Busan",
    "bangkok": "Bangkok",
    "singapore": "Singapore",
    "jakarta": "Jakarta",
    "manila": "Manila",
    "ho chi minh": "Ho Chi Minh City",
    "hanoi": "Hanoi",
    "kuala lumpur": "Kuala Lumpur",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "bangalore": "Bangalore",
    "chennai": "Chennai",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "karachi": "Karachi",
    "lahore": "Lahore",
    "dhaka": "Dhaka",
    "colombo": "Colombo",
    "kathmandu": "Kathmandu",
    "yangon": "Yangon",
    "cairo": "Cairo",
    "lagos": "Lagos",
    "abuja": "Abuja",
    "kano": "Kano",
    "ibadan": "Ibadan",
    "accra": "Accra",
    "kumasi": "Kumasi",
    "nairobi": "Nairobi",
    "mombasa": "Mombasa",
    "kampala": "Kampala",
    "dar es salaam": "Dar es Salaam",
    "addis ababa": "Addis Ababa",
    "johannesburg": "Johannesburg",
    "cape town": "Cape Town",
    "durban": "Durban",
    "pretoria": "Pretoria",
    "casablanca": "Casablanca",
    "rabat": "Rabat",
    "tunis": "Tunis",
    "algiers": "Algiers",
    "tripoli": "Tripoli",
    "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "riyadh": "Riyadh",
    "jeddah": "Jeddah",
    "doha": "Doha",
    "kuwait city": "Kuwait City",
    "manama": "Manama",
    "muscat": "Muscat",
    "tehran": "Tehran",
    "baghdad": "Baghdad",
    "amman": "Amman",
    "beirut": "Beirut",
    "tel aviv": "Tel Aviv-Yafo",
    "jerusalem": "Jerusalem",
    "istanbul": "Istanbul",
    "ankara": "Ankara",
    "izmir": "Izmir",
    "sydney": "Sydney",
    "melbourne": "Melbourne",
    "brisbane": "Brisbane",
    "perth": "Perth",
    "adelaide": "Adelaide",
    "auckland": "Auckland",
    "wellington": "Wellington",
    "christchurch": "Christchurch",
    "sao paulo": "São Paulo",
    "rio de janeiro": "Rio de Janeiro",
    "buenos aires": "Buenos Aires",
    "cordoba": "Córdoba",
    "mexico city": "Mexico City",
    "guadalajara": "Guadalajara",
    "monterrey": "Monterrey",
    "santiago": "Santiago",
    "lima": "Lima",
    "bogota": "Bogotá",
    "medellin": "Medellín",
    "caracas": "Caracas",
}


def normalize_city_name(city_text: str) -> str:
    """
    Normalize city name to handle common variations
    """
    cleaned = city_text.lower().strip()
    
    # Check for exact match in normalizations
    if cleaned in CITY_NORMALIZATIONS:
        return CITY_NORMALIZATIONS[cleaned]
    
    # Check for partial matches (e.g., "newyorkcity")
    for key, value in CITY_NORMALIZATIONS.items():
        if cleaned.replace(" ", "") == key.replace(" ", ""):
            return value
    
    # Add spaces between camelCase words (NewYork -> New York)
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', city_text)
    
    # Remove extra spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Capitalize properly
    result = ' '.join(word.capitalize() for word in result.split())
    
    return result


def detect_region_from_query(query: str) -> list:
    """Detect region from query text for hybrid filtering"""
    q = query.lower()
    for kw, region in QUERY_KEYWORDS.items():
        if kw in q:
            return region if isinstance(region, list) else REGION_MAP.get(region, [])
    return []


async def resolve_city_from_db(city_text: str) -> Optional[Dict[str, Any]]:
    """Resolve city using database resolve_city function"""
    try:
        async with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resolve_city(%s) LIMIT 1;", (city_text,))
            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    "city_id": row[0],
                    "city_name": row[1],
                    "country_name": row[2],
                    "country_code": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "timezone": row[6],
                    "resolution": "db"
                }
            return None
    except Exception as e:
        logger.error(f"DB city resolution error: {e}")
        return None


async def resolve_city_by_vector(query_text: str) -> Optional[Dict[str, Any]]:
    """Resolve city using vector search with pgvector"""
    try:
        import ollama as ollama_client
        
        response = ollama_client.embed(
            model=EMBED_MODEL,
            input=f"{QUERY_PREFIX}{query_text}"
        )
        query_vec = response["embeddings"][0]
        
        # Detect region from query for hybrid filtering
        region_codes = detect_region_from_query(query_text)

        async with get_db_connection() as conn:
            cursor = conn.cursor()

            if region_codes:
                cursor.execute("""
                    SELECT c.id as city_id, c.city_name, c.country_name, c.country_code,
                           c.latitude, c.longitude, c.timezone,
                           1 - (e.embedding <=> %s::vector) AS similarity
                    FROM city_embeddings e JOIN cities c ON c.id = e.city_id
                    WHERE e.embedding IS NOT NULL
                      AND c.country_code = ANY(%s)
                    ORDER BY e.embedding <=> %s::vector LIMIT 1;
                """, (json.dumps(query_vec), region_codes, json.dumps(query_vec)))
            else:
                cursor.execute("""
                    SELECT c.id as city_id, c.city_name, c.country_name, c.country_code,
                           c.latitude, c.longitude, c.timezone,
                           1 - (e.embedding <=> %s::vector) AS similarity
                    FROM city_embeddings e JOIN cities c ON c.id = e.city_id
                    WHERE e.embedding IS NOT NULL
                    ORDER BY e.embedding <=> %s::vector LIMIT 1;
                """, (json.dumps(query_vec), json.dumps(query_vec)))

            row = cursor.fetchone()
            cursor.close()

            if row and float(row[7]) > 0.55:
                return {
                    "city_id": row[0],
                    "city_name": row[1],
                    "country_name": row[2],
                    "country_code": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "timezone": row[6],
                    "resolution": "vector_search"
                }
            return None
    except ImportError:
        logger.warning("Ollama not installed, skipping vector search")
        return None
    except Exception as e:
        logger.error(f"Vector city resolution error: {e}")
        return None


async def resolve_city_via_api(city_text: str) -> Optional[Dict[str, Any]]:
    """Resolve city using WeatherAPI geocoding"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.WEATHER_API_BASE}/search.json",
                params={"key": settings.WEATHER_API_KEY, "q": city_text},
                timeout=10
            )
            
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    loc = results[0]
                    return {
                        "city_name": loc["name"],
                        "country_name": loc["country"],
                        "country_code": loc.get("country_code", ""),
                        "latitude": loc["lat"],
                        "longitude": loc["lon"],
                        "timezone": loc.get("tz_id", "UTC"),
                        "resolution": "api_geocode"
                    }
            return None
    except Exception as e:
        logger.error(f"API city resolution error: {e}")
        return None


async def resolve_city(city_text: str) -> Optional[Dict[str, Any]]:
    """
    Main city resolution function with fallback chain:
    1. Normalize city name (handle common variations)
    2. Database lookup (exact match, aliases)
    3. Vector search (semantic similarity)
    4. WeatherAPI geocoding (fallback)
    """
    # Normalize city name first
    normalized = normalize_city_name(city_text)
    
    # Clean the query (remove weather-related words)
    clean = re.sub(
        r'\b(weather|forecast|temperature|rain|sunny|cloudy|today|tomorrow|'
        r'this week|in|at|for|the|whats|what is|tell me|is it|will it|'
        r'should i|i am going to|travelling to)\b',
        '', normalized.lower()
    ).strip() or normalized.lower().strip()
    
    # Try database first with normalized name
    result = await resolve_city_from_db(normalized)
    if result:
        return result
    
    # Try database with cleaned name
    result = await resolve_city_from_db(clean)
    if result:
        return result
    
    # Try vector search with original text
    result = await resolve_city_by_vector(city_text)
    if result:
        return result
    
    # Try vector search with normalized name
    result = await resolve_city_by_vector(normalized)
    if result:
        return result
    
    # Try API as fallback with normalized name
    result = await resolve_city_via_api(normalized)
    if result:
        return result
    
    return None