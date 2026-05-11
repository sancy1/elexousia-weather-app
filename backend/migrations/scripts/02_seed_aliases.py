"""
╔══════════════════════════════════════════════════════════════╗
║   SCRIPT 2 — City Alias Seeder                              ║
║   Populates city_aliases with abbreviations, nicknames,     ║
║   local names, and common typos for all major cities        ║
║                                                              ║
║   Run after 01_load_cities.py:  python 02_seed_aliases.py  ║
╚══════════════════════════════════════════════════════════════╝

This script also sets up the resolve_city() PostgreSQL function
that the weather agent calls to dynamically resolve any city
string a user types — replacing ALL hardcoded CITY_ALIASES.
"""

import os
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise EnvironmentError("DATABASE_URL not set in .env")
    return psycopg2.connect(DATABASE_URL)


def log(msg: str):
    print(f"  {msg}", flush=True)


# ─────────────────────────────────────────────────────────────
# ALIAS DATA
# Format: (alias, city_name_to_match, country_code, alias_type)
# city_name_to_match must match ascii_name in your cities table
# ─────────────────────────────────────────────────────────────

ALIASES = [
    # ── United States ────────────────────────────────────────
    ("nyc",              "New York City",   "US", "abbreviation"),
    ("new york city",    "New York City",   "US", "full_name"),
    ("ny",               "New York City",   "US", "abbreviation"),
    ("the big apple",    "New York City",   "US", "nickname"),
    ("manhattan",        "New York City",   "US", "district"),
    ("sf",               "San Francisco",   "US", "abbreviation"),
    ("san fran",         "San Francisco",   "US", "nickname"),
    ("la",               "Los Angeles",     "US", "abbreviation"),
    ("los angeles",      "Los Angeles",     "US", "full_name"),
    ("lax",              "Los Angeles",     "US", "airport_code"),
    ("chi",              "Chicago",         "US", "abbreviation"),
    ("the windy city",   "Chicago",         "US", "nickname"),
    ("chi-town",         "Chicago",         "US", "nickname"),
    ("dc",               "Washington",      "US", "abbreviation"),
    ("washington dc",    "Washington",      "US", "full_name"),
    ("miami fl",         "Miami",           "US", "full_name"),
    ("houston tx",       "Houston",         "US", "full_name"),
    ("philly",           "Philadelphia",    "US", "nickname"),
    ("las vegas nv",     "Las Vegas",       "US", "full_name"),
    ("sin city",         "Las Vegas",       "US", "nickname"),
    ("boston ma",        "Boston",          "US", "full_name"),
    ("seattle wa",       "Seattle",         "US", "full_name"),
    ("the emerald city", "Seattle",         "US", "nickname"),
    ("denver co",        "Denver",          "US", "full_name"),
    ("atl",              "Atlanta",         "US", "abbreviation"),
    ("hotlanta",         "Atlanta",         "US", "nickname"),

    # ── United Kingdom ────────────────────────────────────────
    ("london uk",        "London",          "GB", "full_name"),
    ("london england",   "London",          "GB", "full_name"),
    ("the city",         "London",          "GB", "nickname"),
    ("manchester uk",    "Manchester",      "GB", "full_name"),
    ("edinburgh scotland","Edinburgh",      "GB", "full_name"),
    ("cardiff wales",    "Cardiff",         "GB", "full_name"),

    # ── Nigeria ───────────────────────────────────────────────
    ("lagos nigeria",    "Lagos",           "NG", "full_name"),
    ("eko",              "Lagos",           "NG", "local_name"),
    ("abuja nigeria",    "Abuja",           "NG", "full_name"),
    ("fct",              "Abuja",           "NG", "abbreviation"),
    ("ph",               "Port Harcourt",   "NG", "abbreviation"),
    ("port harcourt",    "Port Harcourt",   "NG", "full_name"),
    ("kano nigeria",     "Kano",            "NG", "full_name"),
    ("ibadan nigeria",   "Ibadan",          "NG", "full_name"),

    # ── France ────────────────────────────────────────────────
    ("paris france",     "Paris",           "FR", "full_name"),
    ("pris",             "Paris",           "FR", "typo"),
    ("pare",             "Paris",           "FR", "typo"),
    ("city of light",    "Paris",           "FR", "nickname"),
    ("lyon france",      "Lyon",            "FR", "full_name"),
    ("marseille france", "Marseille",       "FR", "full_name"),

    # ── Germany ───────────────────────────────────────────────
    ("berlin germany",   "Berlin",          "DE", "full_name"),
    ("munich",           "Munich",          "DE", "english_name"),
    ("munchen",          "Munich",          "DE", "local_name"),
    ("frankfurt germany","Frankfurt",       "DE", "full_name"),

    # ── UAE ───────────────────────────────────────────────────
    ("dubai uae",        "Dubai",           "AE", "full_name"),
    ("uae",              "Dubai",           "AE", "country_alias"),
    ("abu dhabi uae",    "Abu Dhabi",       "AE", "full_name"),

    # ── Japan ─────────────────────────────────────────────────
    ("tokyo japan",      "Tokyo",           "JP", "full_name"),
    ("japan",            "Tokyo",           "JP", "country_alias"),
    ("osaka japan",      "Osaka",           "JP", "full_name"),
    ("kyoto japan",      "Kyoto",           "JP", "full_name"),

    # ── China ─────────────────────────────────────────────────
    ("beijing china",    "Beijing",         "CN", "full_name"),
    ("peking",           "Beijing",         "CN", "former_name"),
    ("shanghai china",   "Shanghai",        "CN", "full_name"),
    ("hong kong",        "Hong Kong",       "HK", "full_name"),
    ("hk",               "Hong Kong",       "HK", "abbreviation"),

    # ── India ─────────────────────────────────────────────────
    ("mumbai india",     "Mumbai",          "IN", "full_name"),
    ("bombay",           "Mumbai",          "IN", "former_name"),
    ("delhi india",      "Delhi",           "IN", "full_name"),
    ("new delhi",        "New Delhi",       "IN", "full_name"),
    ("bangalore",        "Bengaluru",       "IN", "former_name"),
    ("bengaluru india",  "Bengaluru",       "IN", "full_name"),
    ("chennai india",    "Chennai",         "IN", "full_name"),
    ("madras",           "Chennai",         "IN", "former_name"),

    # ── Brazil ────────────────────────────────────────────────
    ("sao paulo brazil", "São Paulo",       "BR", "full_name"),
    ("sao paulo",        "São Paulo",       "BR", "ascii_variant"),
    ("rio",              "Rio de Janeiro",  "BR", "nickname"),
    ("rio brazil",       "Rio de Janeiro",  "BR", "full_name"),
    ("rio de janeiro",   "Rio de Janeiro",  "BR", "full_name"),

    # ── South Africa ─────────────────────────────────────────
    ("cape town sa",     "Cape Town",       "ZA", "full_name"),
    ("johannesburg",     "Johannesburg",    "ZA", "full_name"),
    ("joburg",           "Johannesburg",    "ZA", "nickname"),
    ("jozi",             "Johannesburg",    "ZA", "nickname"),
    ("jhb",              "Johannesburg",    "ZA", "abbreviation"),
    ("durban sa",        "Durban",          "ZA", "full_name"),
    ("pretoria sa",      "Pretoria",        "ZA", "full_name"),

    # ── Kenya ─────────────────────────────────────────────────
    ("nairobi kenya",    "Nairobi",         "KE", "full_name"),

    # ── Ghana ─────────────────────────────────────────────────
    ("accra ghana",      "Accra",           "GH", "full_name"),

    # ── Egypt ─────────────────────────────────────────────────
    ("cairo egypt",      "Cairo",           "EG", "full_name"),
    ("al qahira",        "Cairo",           "EG", "local_name"),

    # ── Australia ─────────────────────────────────────────────
    ("sydney australia", "Sydney",          "AU", "full_name"),
    ("melbourne australia","Melbourne",     "AU", "full_name"),
    ("australia",        "Sydney",          "AU", "country_alias"),

    # ── Canada ────────────────────────────────────────────────
    ("toronto canada",   "Toronto",         "CA", "full_name"),
    ("the 6",            "Toronto",         "CA", "nickname"),
    ("t dot",            "Toronto",         "CA", "nickname"),
    ("vancouver canada", "Vancouver",       "CA", "full_name"),
    ("montreal canada",  "Montreal",        "CA", "full_name"),

    # ── Singapore ─────────────────────────────────────────────
    ("sg",               "Singapore",       "SG", "abbreviation"),
    ("singapore city",   "Singapore",       "SG", "full_name"),

    # ── Pakistan ─────────────────────────────────────────────
    ("karachi pakistan", "Karachi",         "PK", "full_name"),
    ("lahore pakistan",  "Lahore",          "PK", "full_name"),

    # ── Russia ───────────────────────────────────────────────
    ("moscow russia",    "Moscow",          "RU", "full_name"),
    ("saint petersburg", "Saint Petersburg","RU", "full_name"),
    ("st petersburg",    "Saint Petersburg","RU", "abbreviation"),
    ("spb",              "Saint Petersburg","RU", "abbreviation"),

    # ── Mexico ───────────────────────────────────────────────
    ("mexico city",      "Mexico City",     "MX", "full_name"),
    ("cdmx",             "Mexico City",     "MX", "abbreviation"),
    ("df",               "Mexico City",     "MX", "abbreviation"),

    # ── Argentina ────────────────────────────────────────────
    ("buenos aires",     "Buenos Aires",    "AR", "full_name"),
    ("ba argentina",     "Buenos Aires",    "AR", "abbreviation"),

    # ── South Korea ──────────────────────────────────────────
    ("seoul south korea","Seoul",           "KR", "full_name"),
    ("korea",            "Seoul",           "KR", "country_alias"),

    # ── Turkey ───────────────────────────────────────────────
    ("istanbul turkey",  "Istanbul",        "TR", "full_name"),
    ("ankara turkey",    "Ankara",          "TR", "full_name"),

    # ── Indonesia ────────────────────────────────────────────
    ("jakarta indonesia","Jakarta",         "ID", "full_name"),
    ("jakarta",          "Jakarta",         "ID", "full_name"),

    # ── Thailand ─────────────────────────────────────────────
    ("bangkok thailand", "Bangkok",         "TH", "full_name"),
    ("bkk",              "Bangkok",         "TH", "airport_code"),

    # ── Netherlands ──────────────────────────────────────────
    ("amsterdam netherlands","Amsterdam",   "NL", "full_name"),
    ("amsterdam holland","Amsterdam",       "NL", "full_name"),

    # ── Spain ────────────────────────────────────────────────
    ("madrid spain",     "Madrid",          "ES", "full_name"),
    ("barcelona spain",  "Barcelona",       "ES", "full_name"),

    # ── Italy ────────────────────────────────────────────────
    ("rome italy",       "Rome",            "IT", "full_name"),
    ("roma",             "Rome",            "IT", "local_name"),
    ("milan italy",      "Milan",           "IT", "full_name"),
    ("milano",           "Milan",           "IT", "local_name"),
]


# ─────────────────────────────────────────────────────────────
# INSTALL resolve_city() DATABASE FUNCTION
# This replaces ALL hardcoded city lookup in the agent code
# ─────────────────────────────────────────────────────────────

RESOLVE_CITY_FUNCTION = """
CREATE OR REPLACE FUNCTION resolve_city(input_text TEXT, query_vector vector(768) DEFAULT NULL)
RETURNS TABLE (
    city_id       INTEGER,
    city_name     VARCHAR,
    country_name  VARCHAR,
    country_code  CHAR(2),
    latitude      DECIMAL,
    longitude     DECIMAL,
    timezone      VARCHAR,
    resolution    TEXT
) AS $$
DECLARE
    clean_input TEXT := LOWER(TRIM(input_text));
BEGIN
    -- Step 1: Exact match on ascii_name or city_name
    RETURN QUERY
        SELECT c.id, c.city_name, c.country_name, c.country_code,
               c.latitude, c.longitude, c.timezone,
               'exact_match'::TEXT
        FROM cities c
        WHERE LOWER(c.ascii_name) = clean_input
           OR LOWER(c.city_name)  = clean_input
        ORDER BY c.population DESC NULLS LAST
        LIMIT 1;

    IF FOUND THEN RETURN; END IF;

    -- Step 2: Alias lookup (NYC, Eko, etc.)
    RETURN QUERY
        SELECT c.id, c.city_name, c.country_name, c.country_code,
               c.latitude, c.longitude, c.timezone,
               'alias_match'::TEXT
        FROM city_aliases a
        JOIN cities c ON c.id = a.city_id
        WHERE LOWER(a.alias) = clean_input
        ORDER BY c.population DESC NULLS LAST
        LIMIT 1;

    IF FOUND THEN RETURN; END IF;

    -- Step 3: Vector Semantic Match (The new "Brain")
    -- This only runs if we pass a vector from Ollama
    IF query_vector IS NOT NULL THEN
        RETURN QUERY
            SELECT c.id, c.city_name, c.country_name, c.country_code,
                   c.latitude, c.longitude, c.timezone,
                   'vector_match'::TEXT
            FROM city_embeddings e
            JOIN cities c ON c.id = e.city_id
            ORDER BY e.embedding <=> query_vector
            LIMIT 1;
            
        IF FOUND THEN RETURN; END IF;
    END IF;

    -- Step 4: Fallback to ILIKE (Last resort for partial text matches)
    RETURN QUERY
        SELECT c.id, c.city_name, c.country_name, c.country_code,
               c.latitude, c.longitude, c.timezone,
               'partial_match'::TEXT
        FROM cities c
        WHERE LOWER(c.ascii_name) LIKE '%' || clean_input || '%'
           OR LOWER(c.city_name)  LIKE '%' || clean_input || '%'
        ORDER BY c.population DESC NULLS LAST
        LIMIT 1;

END;
$$ LANGUAGE plpgsql;
"""


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def seed_aliases(conn):
    cursor = conn.cursor()
    inserted = 0
    skipped  = 0
    failed   = 0

    log(f"Seeding {len(ALIASES):,} aliases...")

    for alias_text, city_match, country_code, alias_type in ALIASES:
        # Find the city_id by matching ascii_name or city_name
        cursor.execute("""
            SELECT id FROM cities
            WHERE (LOWER(ascii_name) = LOWER(%s) OR LOWER(city_name) = LOWER(%s))
              AND LOWER(country_code) = LOWER(%s)
            ORDER BY population DESC NULLS LAST
            LIMIT 1;
        """, (city_match, city_match, country_code))

        row = cursor.fetchone()
        if not row:
            log(f"  [SKIP] '{city_match}' ({country_code}) not found in cities table")
            failed += 1
            continue

        city_id = row[0]

        cursor.execute("""
            INSERT INTO city_aliases (alias, city_id, alias_type)
            VALUES (LOWER(%s), %s, %s)
            ON CONFLICT (LOWER(alias)) DO UPDATE
                SET city_id    = EXCLUDED.city_id,
                    alias_type = EXCLUDED.alias_type;
        """, (alias_text, city_id, alias_type))

        inserted += 1

    conn.commit()
    cursor.close()
    return inserted, skipped, failed


def install_function(conn):
    log("Installing resolve_city() PostgreSQL function...")
    cursor = conn.cursor()
    cursor.execute(RESOLVE_CITY_FUNCTION)
    conn.commit()
    cursor.close()
    log("resolve_city() installed successfully.")


def verify(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM city_aliases;")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT alias_type, COUNT(*) FROM city_aliases
        GROUP BY alias_type ORDER BY COUNT(*) DESC;
    """)
    by_type = cursor.fetchall()

    cursor.execute("""
        SELECT a.alias, c.city_name, c.country_name
        FROM city_aliases a
        JOIN cities c ON c.id = a.city_id
        ORDER BY a.id DESC LIMIT 5;
    """)
    samples = cursor.fetchall()

    cursor.close()

    print()
    print("  ─" * 31)
    print("  ALIAS SEED COMPLETE")
    print("  ─" * 31)
    print(f"  Total aliases: {total:,}")
    print()
    print("  By type:")
    for t, c in by_type:
        print(f"    {t:<20} {c:>4}")
    print()
    print("  Sample aliases:")
    for alias, city, country in samples:
        print(f"    '{alias}' → {city}, {country}")

    # Test resolve_city function
    print()
    log("Testing resolve_city() function...")
    cursor = conn.cursor()
    for test in ["nyc", "pris", "lagos", "the big apple", "uae"]:
        cursor.execute("SELECT city_name, country_name, resolution FROM resolve_city(%s);", (test,))
        result = cursor.fetchone()
        if result:
            print(f"    resolve_city('{test}') → {result[0]}, {result[1]}  [{result[2]}]")
        else:
            print(f"    resolve_city('{test}') → NOT FOUND")
    cursor.close()
    print("  ─" * 31)


def main():
    print()
    print("═" * 62)
    print("  AXIOQUAN — City Alias Seeder")
    print("═" * 62)

    conn              = get_connection()
    log("Connected to Neon PostgreSQL.")

    install_function(conn)
    inserted, skipped, failed = seed_aliases(conn)

    log(f"Inserted: {inserted:,}  |  Skipped: {skipped:,}  |  Not found: {failed:,}")
    verify(conn)
    conn.close()


if __name__ == "__main__":
    main()
