
"""
test_vector.py — Full end-to-end vector search test
Tests city resolution using mxbai-embed-large (1024-dim)
Run after 03e_fast_embed.py completes successfully.
"""

import os
import json
import psycopg2
import psycopg2.extras
import ollama
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
EMBED_MODEL  = "mxbai-embed-large"   # ← CORRECT MODEL (1024-dim, 4/4 accuracy)
EMBED_DIM    = 1024
QUERY_PREFIX = "search_query: "

# ── REGION MAP ────────────────────────────────────────────────
REGION_MAP = {
    "west_africa_coastal": ["NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM","CV","GW"],
    "west_africa":   ["NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM","CV","GW","ML","BF","NE","MR"],
    "east_africa":   ["KE","TZ","ET","UG","RW","BI","ER","DJ","SO","MG"],
    "north_africa":  ["EG","LY","TN","DZ","MA","SD"],
    "middle_east":   ["AE","SA","IQ","IR","IL","JO","LB","KW","QA","BH","OM","YE","SY","TR"],
    "south_asia":    ["IN","PK","BD","LK","NP","AF"],
    "east_asia":     ["CN","JP","KR","TW","HK","MN"],
    "southeast_asia":["SG","TH","ID","MY","VN","PH","MM","KH","LA"],
    "western_europe":["GB","FR","DE","IT","ES","NL","BE","PT","AT","CH","IE"],
    "north_america": ["US","CA","MX"],
    "south_america": ["BR","AR","CO","PE","VE","CL","EC","BO","PY","UY"],
    "scandinavia":   ["SE","NO","DK","FI","IS"],
    "oceania":       ["AU","NZ","PG","FJ"],
}

QUERY_KEYWORDS = {
    "west africa":         "west_africa",
    "west african":        "west_africa",
    "coastal west africa": "west_africa_coastal",
    "east africa":         "east_africa",
    "north africa":        "north_africa",
    "middle east":         "middle_east",
    "south asia":          "south_asia",
    "east asia":           "east_asia",
    "southeast asia":      "southeast_asia",
    "western europe":      "western_europe",
    "north america":       "north_america",
    "south america":       "south_america",
    "latin america":       "south_america",
    "scandinavia":         "scandinavia",
    "nordic":              "scandinavia",
    "oceania":             "oceania",
    "australia":           "oceania",
    "nigeria":   ["NG"],
    "ghana":     ["GH"],
    "japan":     ["JP"],
    "france":    ["FR"],
    "germany":   ["DE"],
    "india":     ["IN"],
    "china":     ["CN"],
    "brazil":    ["BR"],
}


def get_db():
    return psycopg2.connect(DATABASE_URL)


def embed(text: str) -> list:
    """Embed a query using mxbai-embed-large."""
    r = ollama.embed(model=EMBED_MODEL, input=f"{QUERY_PREFIX}{text}")
    return r["embeddings"][0]


def detect_region(query: str) -> list:
    """Extract region country codes from query text."""
    q = query.lower()
    for kw, region in QUERY_KEYWORDS.items():
        if kw in q:
            return region if isinstance(region, list) else REGION_MAP.get(region, [])
    return []


# ─────────────────────────────────────────────────────────────
# DB STATE CHECK
# ─────────────────────────────────────────────────────────────

def check_db():
    print("\n" + "="*55)
    print("  DATABASE STATE")
    print("="*55)

    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cities;")
    print(f"  Total cities          : {cursor.fetchone()[0]:,}")

    cursor.execute("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
    total = cursor.fetchone()[0]
    print(f"  Valid embeddings      : {total:,}")

    # Fast diversity check — compare cities 50 apart
    cursor.execute("""
        SELECT AVG(1-(e1.embedding<=>e2.embedding)) as avg_sim
        FROM city_embeddings e1
        JOIN city_embeddings e2 ON e2.city_id = e1.city_id + 50
        WHERE e1.embedding IS NOT NULL
          AND e2.embedding IS NOT NULL
        LIMIT 20;
    """)
    row = cursor.fetchone()
    avg_sim = float(row[0]) if row and row[0] else 1.0
    ok = "✅ DIVERSE" if avg_sim < 0.85 else "❌ TOO SIMILAR — possible duplicates"
    print(f"  Avg similarity (50-gap): {avg_sim:.6f}  {ok}")

    # Lagos vs Tokyo — should be clearly different
    cursor.execute("""
        SELECT 1-(
            (SELECT e.embedding FROM city_embeddings e
             JOIN cities c ON c.id=e.city_id
             WHERE c.city_name='Lagos' AND c.country_code='NG'
             LIMIT 1)
            <=>
            (SELECT e.embedding FROM city_embeddings e
             JOIN cities c ON c.id=e.city_id
             WHERE c.city_name='Tokyo'
             LIMIT 1)
        ) as sim;
    """)
    row = cursor.fetchone()
    if row and row[0]:
        sim = float(row[0])
        ok  = "✅ GOOD" if sim < 0.75 else "⚠️  CLOSE — check embeddings"
        print(f"  Lagos vs Tokyo sim    : {sim:.6f}  {ok}")

    cursor.execute("SELECT COUNT(*) FROM city_aliases;")
    print(f"  City aliases          : {cursor.fetchone()[0]:,}")

    # Check vector column dimension
    cursor.execute("""
        SELECT pg_catalog.format_type(a.atttypid, a.atttypmod)
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        WHERE c.relname = 'city_embeddings'
          AND a.attname = 'embedding'
          AND a.attnum  > 0;
    """)
    row = cursor.fetchone()
    if row:
        dim_ok = "✅" if "1024" in str(row[0]) else "❌ WRONG — should be vector(1024)"
        print(f"  Embedding column type : {row[0]}  {dim_ok}")

    cursor.close()
    conn.close()
    print("="*55)


# ─────────────────────────────────────────────────────────────
# TEXT RESOLUTION TEST
# ─────────────────────────────────────────────────────────────

def test_resolve(query: str):
    print(f"\n  Query: '{query}'")
    conn   = get_db()
    cursor = conn.cursor()

    vec   = embed(query)
    codes = detect_region(query)

    try:
        cursor.execute("""
            SELECT city_id, city_name, country_name, country_code,
                   latitude, longitude, resolution
            FROM resolve_city(%s, %s::vector(1024), %s)
            LIMIT 1;
        """, (query, json.dumps(vec), codes if codes else None))

        row = cursor.fetchone()
        if row:
            _, name, country, cc, lat, lon, method = row
            region_note = f"region: {codes[:3]}..." if codes else "no region filter"
            print(f"  ✅ {name}, {country} ({cc})  [{method}]  {region_note}")
            print(f"     coords: {lat}, {lon}")
        else:
            print(f"  ❌ Not found — no result from any resolution method")

    except Exception as e:
        print(f"  ⚠️  SQL Error: {e}")

    cursor.close()
    conn.close()


# ─────────────────────────────────────────────────────────────
# RAW VECTOR SEARCH TEST
# ─────────────────────────────────────────────────────────────

def test_raw_vector(query: str, region_key: str = None, top_k: int = 5):
    codes = REGION_MAP.get(region_key, []) if region_key else []
    label = f"region={region_key}" if region_key else "GLOBAL (no filter)"
    print(f"\n  Raw vector: '{query}'  [{label}]")

    vec    = embed(query)
    conn   = get_db()
    cursor = conn.cursor()

    try:
        if codes:
            cursor.execute("""
                SELECT c.city_name, c.country_name, c.country_code,
                       1-(e.embedding<=>%s::vector(1024)) as sim
                FROM city_embeddings e
                JOIN cities c ON c.id = e.city_id
                WHERE e.embedding IS NOT NULL
                  AND c.country_code = ANY(%s)
                ORDER BY e.embedding <=> %s::vector(1024)
                LIMIT %s;
            """, (json.dumps(vec), codes, json.dumps(vec), top_k))
        else:
            cursor.execute("""
                SELECT c.city_name, c.country_name, c.country_code,
                       1-(e.embedding<=>%s::vector(1024)) as sim
                FROM city_embeddings e
                JOIN cities c ON c.id = e.city_id
                WHERE e.embedding IS NOT NULL
                ORDER BY e.embedding <=> %s::vector(1024)
                LIMIT %s;
            """, (json.dumps(vec), json.dumps(vec), top_k))

        rows = cursor.fetchall()
        if rows:
            for city, country, cc, sim in rows:
                bar = "█" * int(sim * 20)
                print(f"    {city:<22} {country:<18} ({cc})  {sim:.4f}  {bar}")
        else:
            print("    No results — city_embeddings may be empty")

    except Exception as e:
        print(f"  ⚠️  SQL Error: {e}")

    cursor.close()
    conn.close()


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # 1. Database state
    check_db()

    # 2. Text resolution tests (exact / alias / fulltext — no vector needed)
    print("\n" + "="*55)
    print("  TEXT RESOLUTION TESTS (exact / alias / fulltext)")
    print("="*55)
    test_resolve("Paris")
    test_resolve("Toronto")
    test_resolve("NYC")
    test_resolve("the big apple")
    test_resolve("Lagos")
    test_resolve("pris")
    test_resolve("city of light")

    # 3. Hybrid semantic tests (vector + region filter)
    print("\n\n" + "="*55)
    print("  HYBRID SEMANTIC TESTS (vector + region filter)")
    print("="*55)
    test_resolve("a coastal city in West Africa")
    test_resolve("biggest city in Japan")
    test_resolve("cold Nordic capital")
    test_resolve("desert city in the Middle East")
    test_resolve("major city in South America")

    # 4. Raw vector scores — WITH region filter vs WITHOUT
    print("\n\n" + "="*55)
    print("  RAW VECTOR — WITH vs WITHOUT REGION FILTER")
    print("="*55)
    test_raw_vector("coastal city in West Africa",  "west_africa_coastal")
    test_raw_vector("coastal city in West Africa",  None)
    test_raw_vector("cold Nordic capital",           "scandinavia")
    test_raw_vector("desert city Arabian Peninsula", "middle_east")
    test_raw_vector("biggest city in Japan",         "east_asia")

