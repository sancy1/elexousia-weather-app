"""
╔══════════════════════════════════════════════════════════════╗
║   SCRIPT 1 — GeoNames City Loader                           ║
║   Downloads cities15000.txt from GeoNames (free, no key)    ║
║   Inserts all 25,000+ cities into your Neon PostgreSQL DB   ║
║                                                              ║
║   Run once:  python 01_load_cities.py                       ║
║   Duration:  ~3–8 minutes depending on internet speed       ║
╚══════════════════════════════════════════════════════════════╝

GeoNames columns in cities15000.txt (tab-separated):
  0  geonameid       1  name            2  asciiname
  3  alternatenames  4  latitude        5  longitude
  6  feature_class   7  feature_code    8  country_code
  9  cc2            10  admin1_code    11  admin2_code
 12  admin3_code    13  admin4_code    14  population
 15  elevation      16  dem            17  timezone
 18  modification_date
"""

import os
import io
import csv
import sys
import time
import zipfile
import requests
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

DATABASE_URL  = os.getenv("DATABASE_URL")
GEONAMES_URL  = "https://download.geonames.org/export/dump/cities15000.zip"
COUNTRY_URL   = "https://download.geonames.org/export/dump/countryInfo.txt"
BATCH_SIZE    = 500     # rows per INSERT batch
MIN_POP       = 0       # set to 50000 to load only large cities

# GeoNames feature codes to include (P = populated place)
INCLUDE_CODES = {
    "PPL",   # populated place
    "PPLA",  # seat of a first-order admin division
    "PPLA2", # seat of a second-order admin division
    "PPLA3", # seat of a third-order admin division
    "PPLC",  # capital of a political entity
    "PPLG",  # seat of government of a political entity
    "PPLX",  # section of populated place
    "PPLS",  # populated places
}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"  {msg}", flush=True)


def progress(current: int, total: int, label: str = ""):
    pct   = int(current / total * 100)
    bar   = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\r  [{bar}] {pct:3d}%  {current:,}/{total:,}  {label}", end="", flush=True)


def get_connection():
    if not DATABASE_URL:
        raise EnvironmentError(
            "\n[ERROR] DATABASE_URL not set.\n"
            "Add this to your .env file:\n"
            "  DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD"
            "@ep-curly-mode-amz3qy3g-pooler.c-5.us-east-1.aws.neon.tech"
            "/neondb?sslmode=require&channel_binding=require\n"
        )
    return psycopg2.connect(DATABASE_URL)


# ─────────────────────────────────────────────────────────────
# STEP 1 — Load country name lookup
# ─────────────────────────────────────────────────────────────

def fetch_country_names() -> dict:
    """
    Downloads GeoNames country info and returns a dict:
    { "NG": "Nigeria", "GB": "United Kingdom", "US": "United States", ... }
    """
    log("Fetching country names from GeoNames...")
    resp = requests.get(COUNTRY_URL, timeout=30)
    resp.raise_for_status()

    countries = {}
    for line in resp.text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 5:
            iso   = parts[0].strip()   # ISO 3166-1 alpha-2
            name  = parts[4].strip()   # country name
            if iso and name:
                countries[iso] = name

    log(f"Loaded {len(countries):,} country names.")
    return countries


# ─────────────────────────────────────────────────────────────
# STEP 2 — Download and parse GeoNames cities15000.zip
# ─────────────────────────────────────────────────────────────

def download_geonames() -> list[dict]:
    """
    Downloads cities15000.zip from GeoNames, unzips in memory,
    and returns a list of city dicts ready for database insertion.
    """
    log(f"Downloading {GEONAMES_URL} ...")
    log("(This file is ~5MB — takes 10–60 seconds depending on speed)")

    resp = requests.get(GEONAMES_URL, timeout=120, stream=True)
    resp.raise_for_status()

    # Download with progress
    total_size = int(resp.headers.get("content-length", 0))
    downloaded = 0
    chunks     = []

    for chunk in resp.iter_content(chunk_size=8192):
        chunks.append(chunk)
        downloaded += len(chunk)
        if total_size:
            progress(downloaded, total_size, "downloading")

    print()  # newline after progress bar
    raw_bytes = b"".join(chunks)
    log(f"Downloaded {len(raw_bytes)/1024/1024:.1f} MB")

    # Unzip in memory
    log("Unzipping in memory...")
    zf        = zipfile.ZipFile(io.BytesIO(raw_bytes))
    txt_file  = [n for n in zf.namelist() if n.endswith(".txt")][0]
    content   = zf.read(txt_file).decode("utf-8")
    log(f"Unzipped: {txt_file}")

    return content.splitlines()


# ─────────────────────────────────────────────────────────────
# STEP 3 — Parse rows into city dicts
# ─────────────────────────────────────────────────────────────

def parse_cities(lines: list[str], country_names: dict) -> list[dict]:
    """
    Parses GeoNames tab-separated lines into city dicts.
    Filters to populated places only.
    """
    log(f"Parsing {len(lines):,} raw lines...")

    cities    = []
    skipped   = 0
    total     = len(lines)

    for i, line in enumerate(lines):
        if i % 5000 == 0:
            progress(i, total, "parsing")

        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < 19:
            skipped += 1
            continue

        feature_code = parts[7].strip()
        if feature_code not in INCLUDE_CODES:
            skipped += 1
            continue

        try:
            population = int(parts[14]) if parts[14].strip() else 0
        except ValueError:
            population = 0

        if population < MIN_POP and MIN_POP > 0:
            skipped += 1
            continue

        try:
            lat = float(parts[4])
            lon = float(parts[5])
        except ValueError:
            skipped += 1
            continue

        country_code = parts[8].strip().upper()
        is_capital   = feature_code in ("PPLC", "PPLG")

        try:
            elevation = int(parts[15]) if parts[15].strip() else None
        except ValueError:
            elevation = None

        cities.append({
            "city_name":      parts[1].strip(),
            "ascii_name":     parts[2].strip().lower(),
            "country_name":   country_names.get(country_code, "Unknown"),
            "country_code":   country_code,
            "state_province": parts[10].strip() or None,
            "latitude":       lat,
            "longitude":      lon,
            "timezone":       parts[17].strip() or "UTC",
            "population":     population,
            "elevation_m":    elevation,
            "is_capital":     is_capital,
        })

    print()  # newline after progress bar
    log(f"Parsed {len(cities):,} valid cities  |  skipped {skipped:,} rows")
    return cities


# ─────────────────────────────────────────────────────────────
# STEP 4 — Insert into PostgreSQL in batches
# ─────────────────────────────────────────────────────────────

def insert_cities(conn, cities: list[dict]) -> int:
    """
    Bulk insert cities into PostgreSQL.

    Removes duplicates before insertion to prevent:
    ON CONFLICT DO UPDATE command cannot affect row a second time
    """
    log("Removing duplicate cities...")

    # Deduplicate using (ascii_name, country_code)
    unique = {}
    for city in cities:
        key = (
            city["ascii_name"].lower().strip(),
            city["country_code"].upper().strip()
        )

        # Keep the city with the largest population
        existing = unique.get(key)
        if existing is None or city["population"] > existing["population"]:
            unique[key] = city

    cities = list(unique.values())

    log(f"After deduplication: {len(cities):,} unique cities")

    cursor = conn.cursor()

    # Create unique index
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cities_name_country
        ON cities (LOWER(ascii_name), LOWER(country_code));
    """)
    conn.commit()

    total = len(cities)
    inserted = 0

    log(f"Inserting {total:,} cities into PostgreSQL...")

    for i in range(0, total, BATCH_SIZE):
        batch = cities[i:i + BATCH_SIZE]

        values = [
            (
                c["city_name"],
                c["ascii_name"],
                c["country_name"],
                c["country_code"],
                c["state_province"],
                c["latitude"],
                c["longitude"],
                c["timezone"],
                c["population"],
                c["elevation_m"],
                c["is_capital"],
            )
            for c in batch
        ]

        psycopg2.extras.execute_values(
            cursor,
            """
            INSERT INTO cities (
                city_name,
                ascii_name,
                country_name,
                country_code,
                state_province,
                latitude,
                longitude,
                timezone,
                population,
                elevation_m,
                is_capital
            )
            VALUES %s
            ON CONFLICT (LOWER(ascii_name), LOWER(country_code))
            DO UPDATE SET
                city_name = EXCLUDED.city_name,
                country_name = EXCLUDED.country_name,
                state_province = EXCLUDED.state_province,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                timezone = EXCLUDED.timezone,
                population = EXCLUDED.population,
                elevation_m = EXCLUDED.elevation_m,
                is_capital = EXCLUDED.is_capital,
                updated_at = NOW();
            """,
            values,
            page_size=BATCH_SIZE
        )

        conn.commit()
        inserted += len(batch)
        progress(inserted, total, "inserting")

    print()
    cursor.close()
    return inserted


# ─────────────────────────────────────────────────────────────
# STEP 5 — Verify insertion
# ─────────────────────────────────────────────────────────────

def verify(conn):
    """Prints a summary of what was loaded."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cities;")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cities WHERE is_capital = TRUE;")
    capitals = cursor.fetchone()[0]

    cursor.execute("""
        SELECT country_name, COUNT(*) as cnt
        FROM cities
        GROUP BY country_name
        ORDER BY cnt DESC
        LIMIT 10;
    """)
    top_countries = cursor.fetchall()

    cursor.execute("""
        SELECT city_name, country_name, population
        FROM cities
        ORDER BY population DESC
        LIMIT 5;
    """)
    top_cities = cursor.fetchall()

    cursor.close()

    print()
    print("  ─" * 31)
    print("  LOAD COMPLETE — VERIFICATION SUMMARY")
    print("  ─" * 31)
    print(f"  Total cities loaded : {total:,}")
    print(f"  Capital cities      : {capitals:,}")
    print()
    print("  Top 10 countries by city count:")
    for country, count in top_countries:
        print(f"    {country:<30} {count:>5,} cities")
    print()
    print("  Top 5 cities by population:")
    for city, country, pop in top_cities:
        print(f"    {city}, {country:<25} pop: {pop:>12,}")
    print("  ─" * 31)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print()
    print("═" * 62)
    print("  AXIOQUAN — GeoNames City Loader")
    print("  Loading 25,000+ world cities into Neon PostgreSQL")
    print("═" * 62)

    start = time.time()

    # Connect
    log("Connecting to Neon PostgreSQL...")
    conn = get_connection()
    log("Connected successfully.")

    # Run pipeline
    country_names = fetch_country_names()
    raw_lines     = download_geonames()
    cities        = parse_cities(raw_lines, country_names)
    inserted      = insert_cities(conn, cities)

    elapsed = time.time() - start
    log(f"Total time: {elapsed:.1f} seconds")

    verify(conn)
    conn.close()


if __name__ == "__main__":
    main()
