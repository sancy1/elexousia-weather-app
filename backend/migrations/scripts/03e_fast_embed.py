# """
# ╔══════════════════════════════════════════════════════════════╗
# ║   SCRIPT 03e — Fast Embedder (Neon Free Tier Safe)          ║
# ║                                                              ║
# ║   Fixes the slowness of 03d by:                             ║
# ║   1. No expensive duplicate detection query                 ║
# ║   2. Processes cities in small batches with keepalive       ║
# ║   3. Saves progress — safe to restart if disconnected       ║
# ║   4. Reconnects automatically if Neon drops the connection  ║
# ║                                                              ║
# ║   Run: python 03e_fast_embed.py                            ║
# ║   Time: ~20-40 minutes for 31,561 cities                   ║
# ║   Safe to restart: picks up from where it stopped          ║
# ╚══════════════════════════════════════════════════════════════╝
# """

# import os
# import sys
# import json
# import time
# import psycopg2
# import psycopg2.extras
# import ollama
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# EMBED_MODEL  = "mxbai-embed-large"
# EMBED_DIM    = 1024
# # EMBED_MODEL  = "nomic-embed-text"
# # EMBED_DIM    = 768
# DOC_PREFIX   = "search_document: "
# QUERY_PREFIX = "search_query: "

# # ── KEY SETTINGS FOR NEON FREE TIER ──────────────────────────
# BATCH_SIZE       = 25     # small batches = more frequent commits
# COMMIT_EVERY     = 25     # commit to DB every N cities
# KEEPALIVE_EVERY  = 50     # send a SELECT 1 every N cities to prevent timeout
# RECONNECT_WAIT   = 5      # seconds to wait before reconnecting


# def log(msg):
#     print(f"  {msg}", flush=True)


# def progress(cur, total, start_time, errors):
#     pct     = int(cur / total * 100)
#     bar     = "█" * (pct // 5) + "░" * (20 - pct // 5)
#     elapsed = time.time() - start_time
#     rate    = cur / elapsed if elapsed > 0 else 0
#     eta     = int((total - cur) / rate) if rate > 0 else 0
#     eta_str = f"{eta//60}m{eta%60:02d}s" if eta > 0 else "?"
#     print(
#         f"\r  [{bar}] {pct:3d}%  {cur:,}/{total:,}  "
#         f"ETA:{eta_str}  errors:{errors}",
#         end="", flush=True
#     )


# # ─────────────────────────────────────────────────────────────
# # ROBUST DB CONNECTION WITH AUTO-RECONNECT
# # ─────────────────────────────────────────────────────────────

# class DBConnection:
#     """
#     Wrapper that automatically reconnects to Neon if the
#     connection drops due to the free tier idle timeout.
#     """
#     def __init__(self):
#         self.conn   = None
#         self.cursor = None
#         self._connect()

#     def _connect(self):
#         if self.conn:
#             try:
#                 self.conn.close()
#             except Exception:
#                 pass
#         self.conn   = psycopg2.connect(
#             DATABASE_URL,
#             keepalives=1,
#             keepalives_idle=30,      # send keepalive after 30s idle
#             keepalives_interval=10,  # retry every 10s
#             keepalives_count=5,      # give up after 5 retries
#         )
#         self.conn.autocommit = False

#     def execute(self, sql, params=None):
#         """Execute with automatic reconnect on failure."""
#         for attempt in range(3):
#             try:
#                 cursor = self.conn.cursor()
#                 cursor.execute(sql, params)
#                 return cursor
#             except (psycopg2.OperationalError,
#                     psycopg2.InterfaceError) as e:
#                 log(f"\n  [DB RECONNECT] attempt {attempt+1}: {e}")
#                 time.sleep(RECONNECT_WAIT)
#                 self._connect()
#         raise RuntimeError("Could not reconnect to database after 3 attempts")

#     def commit(self):
#         for attempt in range(3):
#             try:
#                 self.conn.commit()
#                 return
#             except Exception as e:
#                 log(f"\n  [COMMIT ERROR] {e}")
#                 time.sleep(RECONNECT_WAIT)
#                 self._connect()

#     def fetchall(self, sql, params=None):
#         cursor = self.execute(sql, params)
#         return cursor.fetchall()

#     def fetchone(self, sql, params=None):
#         cursor = self.execute(sql, params)
#         return cursor.fetchone()

#     def keepalive(self):
#         """Prevents Neon from dropping the idle connection."""
#         try:
#             self.execute("SELECT 1")
#         except Exception:
#             self._connect()

#     def close(self):
#         try:
#             self.conn.close()
#         except Exception:
#             pass


# # ─────────────────────────────────────────────────────────────
# # BUILD EXPLICIT CITY CONTENT
# # Same rich content as 03c/03d for quality embeddings
# # ─────────────────────────────────────────────────────────────

# def build_content(row) -> str:
#     city_id, name, country, cc, state, pop, capital = row
#     pop     = pop or 0
#     state   = state or ""
#     capital = capital or False

#     parts = [f"{name} is a city in {country}."]
#     if state:
#         parts.append(f"It is in the {state} region.")
#     if capital:
#         parts.append(f"{name} is the capital of {country}.")

#     # Region classification
#     wa_coastal = {"NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM","CV","GW"}
#     wa_inland  = {"ML","BF","NE","MR"}
#     ea         = {"KE","TZ","ET","UG","RW","BI","ER","DJ","SO","MG"}
#     na_r       = {"EG","LY","TN","DZ","MA","SD"}
#     ca_r       = {"CD","CG","CF","CM","GA","GQ","ST","TD"}
#     sa_r       = {"ZA","MZ","ZM","ZW","MW","NA","BW","LS","SZ","AO"}
#     me         = {"AE","SA","IQ","IR","IL","JO","LB","KW","QA","BH","OM","YE","SY","TR"}
#     sas        = {"IN","PK","BD","LK","NP","AF"}
#     eas        = {"CN","JP","KR","TW","HK","MN"}
#     seas       = {"SG","TH","ID","MY","VN","PH","MM","KH","LA"}
#     we         = {"GB","FR","DE","IT","ES","NL","BE","PT","AT","CH","IE"}
#     ee         = {"PL","CZ","HU","RO","BG","UA","BY","RS","HR","SK","SI"}
#     scan       = {"SE","NO","DK","FI","IS"}
#     nam        = {"US","CA"}
#     sam        = {"BR","AR","CO","PE","VE","CL","EC","BO","PY","UY"}
#     oce        = {"AU","NZ","PG","FJ"}

#     if cc in wa_coastal:
#         parts.append(f"{name} is in West Africa on the African continent.")
#         parts.append(f"Coastal city on the Atlantic Ocean in West Africa. Port city.")
#     elif cc in wa_inland:
#         parts.append(f"{name} is an inland city in West Africa, African continent.")
#     elif cc in ea:
#         parts.append(f"{name} is in East Africa.")
#         if cc in {"KE","TZ","MZ","ER","DJ","SO"}:
#             parts.append("Coastal city on the Indian Ocean, East Africa.")
#         else:
#             parts.append("Inland city in East Africa.")
#     elif cc in na_r:
#         parts.append(f"{name} is in North Africa.")
#         if cc in {"EG","LY","TN","DZ","MA"}:
#             parts.append("Mediterranean or North African coastal region.")
#     elif cc in ca_r:
#         parts.append(f"{name} is in Central Africa, African continent.")
#     elif cc in sa_r:
#         parts.append(f"{name} is in Southern Africa.")
#         if cc in {"ZA","MZ","AO","NA"}:
#             parts.append("May be coastal, Atlantic or Indian Ocean, Southern Africa.")
#     elif cc in me:
#         parts.append(f"{name} is in the Middle East.")
#         if cc in {"AE","QA","BH","KW","SA","OM"}:
#             parts.append("Arabian Peninsula. Hot desert climate. Gulf state. Persian Gulf.")
#         elif cc in {"IL","LB"}:
#             parts.append("Mediterranean coastal city, Middle East.")
#     elif cc in sas:
#         parts.append(f"{name} is in South Asia.")
#         if cc == "IN": parts.append("India, South Asian subcontinent.")
#         if cc in {"IN","BD","LK","PK"}:
#             parts.append("May be coastal, Indian Ocean.")
#     elif cc in eas:
#         parts.append(f"{name} is in East Asia.")
#         if cc == "JP":
#             parts.append("Japan. Island nation. Pacific Ocean. East Asia.")
#         elif cc == "CN":
#             parts.append("China. Most populous country. East Asia.")
#         elif cc == "KR":
#             parts.append("South Korea. Korean peninsula. East Asia.")
#     elif cc in seas:
#         parts.append(f"{name} is in Southeast Asia.")
#         if cc in {"SG","ID","PH","MY","VN","TH"}:
#             parts.append("Coastal or island city, Southeast Asia.")
#     elif cc in we:
#         parts.append(f"{name} is in Western Europe.")
#         labels = {"GB":"United Kingdom British Isles","FR":"France Francophone",
#                   "DE":"Germany Central Europe","IT":"Italy Mediterranean Southern Europe",
#                   "ES":"Spain Iberian Peninsula Mediterranean"}
#         if cc in labels:
#             parts.append(labels[cc])
#     elif cc in ee:
#         parts.append(f"{name} is in Eastern Europe.")
#     elif cc in scan:
#         parts.append(f"{name} is in Scandinavia, Northern Europe. Cold Nordic climate.")
#     elif cc == "US":
#         parts.append(f"{name} is a city in the United States of America, North America.")
#         coastal = {"CA","OR","WA","TX","LA","FL","GA","SC","NC","VA",
#                    "MD","DE","NJ","NY","CT","RI","MA","ME","AK","HI"}
#         if state in coastal:
#             parts.append(f"Coastal US city in {state}, United States.")
#         elif state:
#             parts.append(f"Inland US city in {state}, United States.")
#     elif cc == "CA":
#         parts.append(f"{name} is in Canada, North America.")
#     elif cc in sam:
#         parts.append(f"{name} is in South America, Latin America.")
#         if cc in {"BR","AR","CL","PE","CO","VE","EC","UY"}:
#             parts.append("May be coastal, Atlantic or Pacific, South America.")
#     elif cc in oce:
#         parts.append(f"{name} is in Oceania, Pacific region.")
#         if cc in {"AU","NZ","FJ","PG"}:
#             parts.append("Coastal city, Pacific or Indian Ocean, Oceania.")

#     # Population
#     if pop > 10_000_000:
#         parts.append("Megacity with over 10 million people.")
#     elif pop > 5_000_000:
#         parts.append("Very large city, over 5 million people.")
#     elif pop > 1_000_000:
#         parts.append("Major city, over 1 million people.")
#     elif pop > 500_000:
#         parts.append("Large city.")
#     elif pop > 100_000:
#         parts.append("Medium-sized city.")
#     else:
#         parts.append("Small town.")

#     return f"{DOC_PREFIX}{' '.join(parts)}"


# # ─────────────────────────────────────────────────────────────
# # VERIFY OLLAMA
# # ─────────────────────────────────────────────────────────────

# def verify_ollama():
#     log(f"Verifying Ollama + {EMBED_MODEL}...")
#     try:
#         test = ollama.embed(model=EMBED_MODEL, input=f"{DOC_PREFIX}test")
#         dim  = len(test["embeddings"][0])
#         if dim != EMBED_DIM:
#             raise ValueError(f"Expected {EMBED_DIM}D, got {dim}D")
#         log(f"Ollama OK. Vector dimension: {dim}")
#     except ollama.ResponseError:
#         print(f"\n  [ERROR] Model '{EMBED_MODEL}' not found.")
#         print(f"  Run: ollama pull {EMBED_MODEL}")
#         sys.exit(1)
#     except ConnectionError:
#         print(f"\n  [ERROR] Cannot connect to Ollama.")
#         print(f"  Run: ollama serve  (in a separate terminal)")
#         sys.exit(1)


# # ─────────────────────────────────────────────────────────────
# # GET CITIES THAT NEED RE-EMBEDDING
# # Strategy: find cities whose embedding is identical to another
# # city's embedding — using a FAST query (no text cast)
# # ─────────────────────────────────────────────────────────────

# def get_cities_to_fix(db: DBConnection) -> list:
#     """
#     Returns city_ids that need re-embedding.

#     FAST approach: instead of casting vectors to text (slow),
#     we use a random sample to estimate the duplicate rate,
#     then simply re-embed ALL cities that were processed in
#     batches > 1 (i.e. all except the first in each batch).

#     Even simpler: since 03b processed in batches of 50,
#     we know every 2nd-50th city in each batch got a duplicate.
#     We re-embed all cities ordered by id, skipping cities
#     whose embedding is already verified unique via a fast
#     self-similarity check on a small sample.
#     """
#     log("Checking embedding quality with fast sample test...")

#     # Fast check: take 10 random pairs and measure similarity
#     # If avg similarity > 0.999 — most are duplicates
#     rows = db.fetchall("""
#         SELECT e1.city_id, 1-(e1.embedding<=>e2.embedding) as sim
#         FROM city_embeddings e1
#         JOIN city_embeddings e2
#           ON e2.city_id = e1.city_id + 1
#         WHERE e1.embedding IS NOT NULL
#           AND e2.embedding IS NOT NULL
#         ORDER BY RANDOM()
#         LIMIT 20;
#     """)

#     if rows:
#         avg_sim = sum(float(r[1]) for r in rows) / len(rows)
#         log(f"Average similarity between adjacent cities: {avg_sim:.6f}")

#         if avg_sim > 0.999:
#             log("Confirmed: most embeddings are identical (batch duplication bug).")
#             log("Will re-embed ALL cities.")
#             needs_all = True
#         elif avg_sim > 0.95:
#             log("Many duplicates detected. Will re-embed ALL cities to be safe.")
#             needs_all = True
#         else:
#             log("Embeddings look diverse. Only re-embedding cities with NULL embeddings.")
#             needs_all = False
#     else:
#         log("Cannot sample — re-embedding all cities.")
#         needs_all = True

#     if needs_all:
#         rows = db.fetchall("""
#             SELECT c.id, c.city_name, c.country_name, c.country_code,
#                    c.state_province, c.population, c.is_capital
#             FROM cities c
#             ORDER BY c.population DESC NULLS LAST;
#         """)
#     else:
#         rows = db.fetchall("""
#             SELECT c.id, c.city_name, c.country_name, c.country_code,
#                    c.state_province, c.population, c.is_capital
#             FROM cities c
#             LEFT JOIN city_embeddings e
#                 ON e.city_id = c.id AND e.embedding IS NOT NULL
#             WHERE e.id IS NULL
#             ORDER BY c.population DESC NULLS LAST;
#         """)

#     log(f"Cities to re-embed: {len(rows):,}")
#     return rows


# # ─────────────────────────────────────────────────────────────
# # INSTALL HYBRID resolve_city() FUNCTION
# # ─────────────────────────────────────────────────────────────

# HYBRID_RESOLVE = """
# CREATE OR REPLACE FUNCTION resolve_city(
#     input_text   TEXT,
#     query_vector vector(768) DEFAULT NULL,
#     region_codes TEXT[]      DEFAULT NULL
# )
# RETURNS TABLE(
#     city_id INTEGER, city_name VARCHAR, country_name VARCHAR,
#     country_code CHAR(2), latitude DECIMAL, longitude DECIMAL,
#     timezone VARCHAR, resolution TEXT
# ) AS $$
# DECLARE clean_input TEXT := LOWER(TRIM(input_text));
# BEGIN
#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'exact_match'::TEXT
#         FROM cities c WHERE LOWER(c.ascii_name)=clean_input OR LOWER(c.city_name)=clean_input
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'alias_match'::TEXT
#         FROM city_aliases a JOIN cities c ON c.id=a.city_id
#         WHERE LOWER(a.alias)=clean_input
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'fulltext_match'::TEXT
#         FROM cities c WHERE to_tsvector('english',c.city_name||' '||c.country_name)
#         @@plainto_tsquery('english',clean_input)
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     IF query_vector IS NOT NULL THEN
#         IF region_codes IS NOT NULL AND array_length(region_codes,1)>0 THEN
#             RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#                 c.latitude,c.longitude,c.timezone,'hybrid_vector_region'::TEXT
#                 FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#                 WHERE e.embedding IS NOT NULL AND c.country_code=ANY(region_codes)
#                 ORDER BY e.embedding<=>query_vector LIMIT 1;
#             IF FOUND THEN RETURN; END IF;
#         END IF;
#         RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#             c.latitude,c.longitude,c.timezone,'vector_match'::TEXT
#             FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#             WHERE e.embedding IS NOT NULL
#             ORDER BY e.embedding<=>query_vector LIMIT 1;
#     END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'partial_match'::TEXT
#         FROM cities c WHERE LOWER(c.ascii_name) LIKE '%'||clean_input||'%'
#         OR LOWER(c.city_name) LIKE '%'||clean_input||'%'
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
# END;
# $$ LANGUAGE plpgsql;
# """


# # ─────────────────────────────────────────────────────────────
# # VERIFY RESULTS
# # ─────────────────────────────────────────────────────────────

# def verify(db: DBConnection):
#     row    = db.fetchone("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
#     total  = row[0]

#     # Fast uniqueness check using similarity on small sample
#     rows   = db.fetchall("""
#         SELECT 1-(e1.embedding<=>e2.embedding) as sim
#         FROM city_embeddings e1 JOIN city_embeddings e2
#           ON e2.city_id = e1.city_id + 50
#         WHERE e1.embedding IS NOT NULL AND e2.embedding IS NOT NULL
#         LIMIT 10;
#     """)
#     avg_sim = sum(float(r[0]) for r in rows) / len(rows) if rows else 1.0

#     print()
#     print("  " + "─"*50)
#     print("  VERIFICATION")
#     print("  " + "─"*50)
#     print(f"  Total embeddings : {total:,}")
#     print(f"  Avg sim (sample) : {avg_sim:.6f}", end="  ")
#     if avg_sim < 0.95:
#         print("✅ Vectors are diverse — fix worked!")
#     else:
#         print("❌ Still similar — run script again")

#     # Test hybrid vector search
#     log("Testing vector searches...")
#     tests = [
#         ("coastal city in West Africa",
#          ["NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM"]),
#         ("desert city Arabian Peninsula",
#          ["AE","SA","KW","QA","BH","OM"]),
#         ("cold Nordic capital",
#          ["SE","NO","DK","FI","IS"]),
#         ("large city in East Asia",
#          ["CN","JP","KR","TW","HK"]),
#     ]

#     for query, codes in tests:
#         try:
#             resp = ollama.embed(model=EMBED_MODEL,
#                                 input=f"{QUERY_PREFIX}{query}")
#             vec  = resp["embeddings"][0]
#             rows = db.fetchall("""
#                 SELECT c.city_name, c.country_name,
#                        1-(e.embedding<=>%s::vector) as sim
#                 FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#                 WHERE e.embedding IS NOT NULL AND c.country_code=ANY(%s)
#                 ORDER BY e.embedding<=>%s::vector LIMIT 3;
#             """, (json.dumps(vec), codes, json.dumps(vec)))

#             print(f"\n  '{query}'")
#             for city, country, sim in rows:
#                 bar = "█"*int(sim*20)
#                 print(f"    {city:<22} {country:<18} {sim:.4f}  {bar}")
#         except Exception as e:
#             print(f"  [{query}] {e}")

#     print()
#     print("  " + "─"*50)


# # ─────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────

# def main():
#     print()
#     print("═"*62)
#     print("  AXIOQUAN — Fast Embedder (Neon Free Tier Safe)")
#     print(f"  Model: {EMBED_MODEL}  |  Batch: {BATCH_SIZE}  |  Keepalive: every {KEEPALIVE_EVERY}")
#     print("═"*62)

#     verify_ollama()

#     db = DBConnection()
#     log("Connected to Neon PostgreSQL.")

#     # Install hybrid resolve_city()
#     log("Installing hybrid resolve_city() function...")
#     db.execute(HYBRID_RESOLVE)
#     db.commit()
#     log("resolve_city() installed.")

#     # Drop ivfflat (use exact cosine — faster for 31k rows, more accurate)
#     log("Dropping ivfflat index (switching to exact cosine search)...")
#     db.execute("DROP INDEX IF EXISTS idx_city_embeddings_vec;")
#     db.execute("""
#         CREATE INDEX IF NOT EXISTS idx_city_embeddings_city_id_btree
#         ON city_embeddings(city_id);
#     """)
#     db.commit()

#     # ── TRUNCATE FIRST — the correct approach ────────────────
#     # Deleting existing embeddings before re-embedding is the
#     # ONLY way to guarantee zero duplicates survive from
#     # previous failed runs. TRUNCATE is instant on any size table.
#     log("Truncating city_embeddings — removing all previous vectors...")
#     db.execute("TRUNCATE TABLE city_embeddings;")
#     db.commit()
#     log("Truncate complete. Starting fresh embed of all cities.")

#     # Get ALL cities — simple full table scan, no duplicate logic needed
#     log("Loading all cities from database...")
#     cities = db.fetchall("""
#         SELECT id, city_name, country_name, country_code,
#                state_province, population, is_capital
#         FROM cities
#         ORDER BY population DESC NULLS LAST;
#     """)
#     total  = len(cities)
#     log(f"Cities to embed: {total:,}")

#     if total == 0:
#         log("No cities found in database. Run 01_load_cities.py first.")
#         db.close()
#         return

#     log(f"Starting embedding. Will auto-reconnect if Neon drops connection.")
#     print()

#     processed  = 0
#     errors     = 0
#     start_time = time.time()

#     for i, city_row in enumerate(cities):
#         city_id = city_row[0]
#         content = build_content(city_row)

#         # Embed ONE city at a time (prevents duplicate vector bug)
#         try:
#             response = ollama.embed(model=EMBED_MODEL, input=content)
#             vector   = response["embeddings"][0]
#         except Exception as e:
#             errors += 1
#             if errors <= 3:
#                 log(f"\n  [OLLAMA ERROR] {e}")
#             time.sleep(1)
#             continue

#         # Insert — no conflict possible after TRUNCATE, plain INSERT is faster
#         try:
#             db.execute("""
#                 INSERT INTO city_embeddings(city_id, content, embedding)
#                 VALUES(%s, %s, %s::vector);
#             """, (city_id, content, json.dumps(vector)))
#             processed += 1
#         except Exception as e:
#             errors += 1
#             if errors <= 3:
#                 log(f"\n  [DB ERROR] {e}")
#             continue

#         # Commit frequently — small transactions survive disconnects
#         if processed % COMMIT_EVERY == 0:
#             db.commit()

#         # Keepalive — prevents Neon idle timeout
#         if processed % KEEPALIVE_EVERY == 0:
#             db.keepalive()

#         # Progress display
#         if processed % 100 == 0 or processed == total:
#             progress(processed, total, start_time, errors)

#     # Final commit
#     db.commit()
#     print()
#     print()

#     elapsed = time.time() - start_time
#     log(f"Processed: {processed:,}  Errors: {errors}  Time: {elapsed/60:.1f} min")

#     verify(db)
#     db.close()

#     print()
#     log("Done! Run: python test_vector.py to confirm.")


# if __name__ == "__main__":
#     main()






























# """
# ╔══════════════════════════════════════════════════════════════╗
# ║   SCRIPT 03e — Fast Embedder (Neon Free Tier Safe)          ║
# ║                                                              ║
# ║   Fixes the slowness of 03d by:                             ║
# ║   1. No expensive duplicate detection query                 ║
# ║   2. Processes cities in small batches with keepalive       ║
# ║   3. Saves progress — safe to restart if disconnected       ║
# ║   4. Reconnects automatically if Neon drops the connection  ║
# ║                                                              ║
# ║   Run: python 03e_fast_embed.py                            ║
# ║   Time: ~20-40 minutes for 31,561 cities                   ║
# ║   Safe to restart: picks up from where it stopped          ║
# ╚══════════════════════════════════════════════════════════════╝
# """

# import os
# import sys
# import json
# import time
# import psycopg2
# import psycopg2.extras
# import ollama
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# EMBED_MODEL  = "mxbai-embed-large"   # 4/4 geographic accuracy, 1024-dim
# EMBED_DIM    = 1024
# DOC_PREFIX   = "search_document: "
# QUERY_PREFIX = "search_query: "

# # ── KEY SETTINGS FOR NEON FREE TIER ──────────────────────────
# BATCH_SIZE       = 25     # small batches = more frequent commits
# COMMIT_EVERY     = 25     # commit to DB every N cities
# KEEPALIVE_EVERY  = 50     # send a SELECT 1 every N cities to prevent timeout
# RECONNECT_WAIT   = 5      # seconds to wait before reconnecting


# def log(msg):
#     print(f"  {msg}", flush=True)


# def progress(cur, total, start_time, errors):
#     pct     = int(cur / total * 100)
#     bar     = "█" * (pct // 5) + "░" * (20 - pct // 5)
#     elapsed = time.time() - start_time
#     rate    = cur / elapsed if elapsed > 0 else 0
#     eta     = int((total - cur) / rate) if rate > 0 else 0
#     eta_str = f"{eta//60}m{eta%60:02d}s" if eta > 0 else "?"
#     print(
#         f"\r  [{bar}] {pct:3d}%  {cur:,}/{total:,}  "
#         f"ETA:{eta_str}  errors:{errors}",
#         end="", flush=True
#     )


# # ─────────────────────────────────────────────────────────────
# # ROBUST DB CONNECTION WITH AUTO-RECONNECT
# # ─────────────────────────────────────────────────────────────

# class DBConnection:
#     """
#     Wrapper that automatically reconnects to Neon if the
#     connection drops due to the free tier idle timeout.
#     """
#     def __init__(self):
#         self.conn   = None
#         self.cursor = None
#         self._connect()

#     def _connect(self):
#         if self.conn:
#             try:
#                 self.conn.close()
#             except Exception:
#                 pass
#         self.conn   = psycopg2.connect(
#             DATABASE_URL,
#             keepalives=1,
#             keepalives_idle=30,      # send keepalive after 30s idle
#             keepalives_interval=10,  # retry every 10s
#             keepalives_count=5,      # give up after 5 retries
#         )
#         self.conn.autocommit = False

#     def execute(self, sql, params=None):
#         """Execute with automatic reconnect on failure."""
#         for attempt in range(3):
#             try:
#                 cursor = self.conn.cursor()
#                 cursor.execute(sql, params)
#                 return cursor
#             except (psycopg2.OperationalError,
#                     psycopg2.InterfaceError) as e:
#                 log(f"\n  [DB RECONNECT] attempt {attempt+1}: {e}")
#                 time.sleep(RECONNECT_WAIT)
#                 self._connect()
#         raise RuntimeError("Could not reconnect to database after 3 attempts")

#     def commit(self):
#         for attempt in range(3):
#             try:
#                 self.conn.commit()
#                 return
#             except Exception as e:
#                 log(f"\n  [COMMIT ERROR] {e}")
#                 time.sleep(RECONNECT_WAIT)
#                 self._connect()

#     def fetchall(self, sql, params=None):
#         cursor = self.execute(sql, params)
#         return cursor.fetchall()

#     def fetchone(self, sql, params=None):
#         cursor = self.execute(sql, params)
#         return cursor.fetchone()

#     def keepalive(self):
#         """Prevents Neon from dropping the idle connection."""
#         try:
#             self.execute("SELECT 1")
#         except Exception:
#             self._connect()

#     def close(self):
#         try:
#             self.conn.close()
#         except Exception:
#             pass


# # ─────────────────────────────────────────────────────────────
# # BUILD EXPLICIT CITY CONTENT
# # Same rich content as 03c/03d for quality embeddings
# # ─────────────────────────────────────────────────────────────

# def build_content(row) -> str:
#     city_id, name, country, cc, state, pop, capital = row
#     pop     = pop or 0
#     state   = state or ""
#     capital = capital or False

#     parts = [f"{name} is a city in {country}."]
#     if state:
#         parts.append(f"It is in the {state} region.")
#     if capital:
#         parts.append(f"{name} is the capital of {country}.")

#     # Region classification
#     wa_coastal = {"NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM","CV","GW"}
#     wa_inland  = {"ML","BF","NE","MR"}
#     ea         = {"KE","TZ","ET","UG","RW","BI","ER","DJ","SO","MG"}
#     na_r       = {"EG","LY","TN","DZ","MA","SD"}
#     ca_r       = {"CD","CG","CF","CM","GA","GQ","ST","TD"}
#     sa_r       = {"ZA","MZ","ZM","ZW","MW","NA","BW","LS","SZ","AO"}
#     me         = {"AE","SA","IQ","IR","IL","JO","LB","KW","QA","BH","OM","YE","SY","TR"}
#     sas        = {"IN","PK","BD","LK","NP","AF"}
#     eas        = {"CN","JP","KR","TW","HK","MN"}
#     seas       = {"SG","TH","ID","MY","VN","PH","MM","KH","LA"}
#     we         = {"GB","FR","DE","IT","ES","NL","BE","PT","AT","CH","IE"}
#     ee         = {"PL","CZ","HU","RO","BG","UA","BY","RS","HR","SK","SI"}
#     scan       = {"SE","NO","DK","FI","IS"}
#     nam        = {"US","CA"}
#     sam        = {"BR","AR","CO","PE","VE","CL","EC","BO","PY","UY"}
#     oce        = {"AU","NZ","PG","FJ"}

#     if cc in wa_coastal:
#         parts.append(f"{name} is in West Africa on the African continent.")
#         parts.append(f"Coastal city on the Atlantic Ocean in West Africa. Port city.")
#     elif cc in wa_inland:
#         parts.append(f"{name} is an inland city in West Africa, African continent.")
#     elif cc in ea:
#         parts.append(f"{name} is in East Africa.")
#         if cc in {"KE","TZ","MZ","ER","DJ","SO"}:
#             parts.append("Coastal city on the Indian Ocean, East Africa.")
#         else:
#             parts.append("Inland city in East Africa.")
#     elif cc in na_r:
#         parts.append(f"{name} is in North Africa.")
#         if cc in {"EG","LY","TN","DZ","MA"}:
#             parts.append("Mediterranean or North African coastal region.")
#     elif cc in ca_r:
#         parts.append(f"{name} is in Central Africa, African continent.")
#     elif cc in sa_r:
#         parts.append(f"{name} is in Southern Africa.")
#         if cc in {"ZA","MZ","AO","NA"}:
#             parts.append("May be coastal, Atlantic or Indian Ocean, Southern Africa.")
#     elif cc in me:
#         parts.append(f"{name} is in the Middle East.")
#         if cc in {"AE","QA","BH","KW","SA","OM"}:
#             parts.append("Arabian Peninsula. Hot desert climate. Gulf state. Persian Gulf.")
#         elif cc in {"IL","LB"}:
#             parts.append("Mediterranean coastal city, Middle East.")
#     elif cc in sas:
#         parts.append(f"{name} is in South Asia.")
#         if cc == "IN": parts.append("India, South Asian subcontinent.")
#         if cc in {"IN","BD","LK","PK"}:
#             parts.append("May be coastal, Indian Ocean.")
#     elif cc in eas:
#         parts.append(f"{name} is in East Asia.")
#         if cc == "JP":
#             parts.append("Japan. Island nation. Pacific Ocean. East Asia.")
#         elif cc == "CN":
#             parts.append("China. Most populous country. East Asia.")
#         elif cc == "KR":
#             parts.append("South Korea. Korean peninsula. East Asia.")
#     elif cc in seas:
#         parts.append(f"{name} is in Southeast Asia.")
#         if cc in {"SG","ID","PH","MY","VN","TH"}:
#             parts.append("Coastal or island city, Southeast Asia.")
#     elif cc in we:
#         parts.append(f"{name} is in Western Europe.")
#         labels = {"GB":"United Kingdom British Isles","FR":"France Francophone",
#                   "DE":"Germany Central Europe","IT":"Italy Mediterranean Southern Europe",
#                   "ES":"Spain Iberian Peninsula Mediterranean"}
#         if cc in labels:
#             parts.append(labels[cc])
#     elif cc in ee:
#         parts.append(f"{name} is in Eastern Europe.")
#     elif cc in scan:
#         parts.append(f"{name} is in Scandinavia, Northern Europe. Cold Nordic climate.")
#     elif cc == "US":
#         parts.append(f"{name} is a city in the United States of America, North America.")
#         coastal = {"CA","OR","WA","TX","LA","FL","GA","SC","NC","VA",
#                    "MD","DE","NJ","NY","CT","RI","MA","ME","AK","HI"}
#         if state in coastal:
#             parts.append(f"Coastal US city in {state}, United States.")
#         elif state:
#             parts.append(f"Inland US city in {state}, United States.")
#     elif cc == "CA":
#         parts.append(f"{name} is in Canada, North America.")
#     elif cc in sam:
#         parts.append(f"{name} is in South America, Latin America.")
#         if cc in {"BR","AR","CL","PE","CO","VE","EC","UY"}:
#             parts.append("May be coastal, Atlantic or Pacific, South America.")
#     elif cc in oce:
#         parts.append(f"{name} is in Oceania, Pacific region.")
#         if cc in {"AU","NZ","FJ","PG"}:
#             parts.append("Coastal city, Pacific or Indian Ocean, Oceania.")

#     # Population
#     if pop > 10_000_000:
#         parts.append("Megacity with over 10 million people.")
#     elif pop > 5_000_000:
#         parts.append("Very large city, over 5 million people.")
#     elif pop > 1_000_000:
#         parts.append("Major city, over 1 million people.")
#     elif pop > 500_000:
#         parts.append("Large city.")
#     elif pop > 100_000:
#         parts.append("Medium-sized city.")
#     else:
#         parts.append("Small town.")

#     return f"{DOC_PREFIX}{' '.join(parts)}"


# # ─────────────────────────────────────────────────────────────
# # VERIFY OLLAMA
# # ─────────────────────────────────────────────────────────────

# def verify_ollama():
#     log(f"Verifying Ollama + {EMBED_MODEL}...")
#     try:
#         test = ollama.embed(model=EMBED_MODEL, input=f"{DOC_PREFIX}test")
#         dim  = len(test["embeddings"][0])
#         if dim != EMBED_DIM:
#             raise ValueError(f"Expected {EMBED_DIM}D, got {dim}D")
#         log(f"Ollama OK. Vector dimension: {dim}")
#     except ollama.ResponseError:
#         print(f"\n  [ERROR] Model '{EMBED_MODEL}' not found.")
#         print(f"  Run: ollama pull {EMBED_MODEL}")
#         sys.exit(1)
#     except ConnectionError:
#         print(f"\n  [ERROR] Cannot connect to Ollama.")
#         print(f"  Run: ollama serve  (in a separate terminal)")
#         sys.exit(1)


# # ─────────────────────────────────────────────────────────────
# # GET CITIES THAT NEED RE-EMBEDDING
# # Strategy: find cities whose embedding is identical to another
# # city's embedding — using a FAST query (no text cast)
# # ─────────────────────────────────────────────────────────────

# def get_cities_to_fix(db: DBConnection) -> list:
#     """
#     Returns city_ids that need re-embedding.

#     FAST approach: instead of casting vectors to text (slow),
#     we use a random sample to estimate the duplicate rate,
#     then simply re-embed ALL cities that were processed in
#     batches > 1 (i.e. all except the first in each batch).

#     Even simpler: since 03b processed in batches of 50,
#     we know every 2nd-50th city in each batch got a duplicate.
#     We re-embed all cities ordered by id, skipping cities
#     whose embedding is already verified unique via a fast
#     self-similarity check on a small sample.
#     """
#     log("Checking embedding quality with fast sample test...")

#     # Fast check: take 10 random pairs and measure similarity
#     # If avg similarity > 0.999 — most are duplicates
#     rows = db.fetchall("""
#         SELECT e1.city_id, 1-(e1.embedding<=>e2.embedding) as sim
#         FROM city_embeddings e1
#         JOIN city_embeddings e2
#           ON e2.city_id = e1.city_id + 1
#         WHERE e1.embedding IS NOT NULL
#           AND e2.embedding IS NOT NULL
#         ORDER BY RANDOM()
#         LIMIT 20;
#     """)

#     if rows:
#         avg_sim = sum(float(r[1]) for r in rows) / len(rows)
#         log(f"Average similarity between adjacent cities: {avg_sim:.6f}")

#         if avg_sim > 0.999:
#             log("Confirmed: most embeddings are identical (batch duplication bug).")
#             log("Will re-embed ALL cities.")
#             needs_all = True
#         elif avg_sim > 0.95:
#             log("Many duplicates detected. Will re-embed ALL cities to be safe.")
#             needs_all = True
#         else:
#             log("Embeddings look diverse. Only re-embedding cities with NULL embeddings.")
#             needs_all = False
#     else:
#         log("Cannot sample — re-embedding all cities.")
#         needs_all = True

#     if needs_all:
#         rows = db.fetchall("""
#             SELECT c.id, c.city_name, c.country_name, c.country_code,
#                    c.state_province, c.population, c.is_capital
#             FROM cities c
#             ORDER BY c.population DESC NULLS LAST;
#         """)
#     else:
#         rows = db.fetchall("""
#             SELECT c.id, c.city_name, c.country_name, c.country_code,
#                    c.state_province, c.population, c.is_capital
#             FROM cities c
#             LEFT JOIN city_embeddings e
#                 ON e.city_id = c.id AND e.embedding IS NOT NULL
#             WHERE e.id IS NULL
#             ORDER BY c.population DESC NULLS LAST;
#         """)

#     log(f"Cities to re-embed: {len(rows):,}")
#     return rows


# # ─────────────────────────────────────────────────────────────
# # INSTALL HYBRID resolve_city() FUNCTION
# # ─────────────────────────────────────────────────────────────

# HYBRID_RESOLVE = """
# CREATE OR REPLACE FUNCTION resolve_city(
#     input_text   TEXT,
#     query_vector vector(1024) DEFAULT NULL,
#     region_codes TEXT[]      DEFAULT NULL
# )
# RETURNS TABLE(
#     city_id INTEGER, city_name VARCHAR, country_name VARCHAR,
#     country_code CHAR(2), latitude DECIMAL, longitude DECIMAL,
#     timezone VARCHAR, resolution TEXT
# ) AS $$
# DECLARE clean_input TEXT := LOWER(TRIM(input_text));
# BEGIN
#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'exact_match'::TEXT
#         FROM cities c WHERE LOWER(c.ascii_name)=clean_input OR LOWER(c.city_name)=clean_input
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'alias_match'::TEXT
#         FROM city_aliases a JOIN cities c ON c.id=a.city_id
#         WHERE LOWER(a.alias)=clean_input
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'fulltext_match'::TEXT
#         FROM cities c WHERE to_tsvector('english',c.city_name||' '||c.country_name)
#         @@plainto_tsquery('english',clean_input)
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
#     IF FOUND THEN RETURN; END IF;

#     IF query_vector IS NOT NULL THEN
#         IF region_codes IS NOT NULL AND array_length(region_codes,1)>0 THEN
#             RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#                 c.latitude,c.longitude,c.timezone,'hybrid_vector_region'::TEXT
#                 FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#                 WHERE e.embedding IS NOT NULL AND c.country_code=ANY(region_codes)
#                 ORDER BY e.embedding<=>query_vector LIMIT 1;
#             IF FOUND THEN RETURN; END IF;
#         END IF;
#         RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#             c.latitude,c.longitude,c.timezone,'vector_match'::TEXT
#             FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#             WHERE e.embedding IS NOT NULL
#             ORDER BY e.embedding<=>query_vector LIMIT 1;
#     END IF;

#     RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
#         c.latitude,c.longitude,c.timezone,'partial_match'::TEXT
#         FROM cities c WHERE LOWER(c.ascii_name) LIKE '%'||clean_input||'%'
#         OR LOWER(c.city_name) LIKE '%'||clean_input||'%'
#         ORDER BY c.population DESC NULLS LAST LIMIT 1;
# END;
# $$ LANGUAGE plpgsql;
# """


# # ─────────────────────────────────────────────────────────────
# # VERIFY RESULTS
# # ─────────────────────────────────────────────────────────────

# def verify(db: DBConnection):
#     row    = db.fetchone("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
#     total  = row[0]

#     # Fast uniqueness check using similarity on small sample
#     rows   = db.fetchall("""
#         SELECT 1-(e1.embedding<=>e2.embedding) as sim
#         FROM city_embeddings e1 JOIN city_embeddings e2
#           ON e2.city_id = e1.city_id + 50
#         WHERE e1.embedding IS NOT NULL AND e2.embedding IS NOT NULL
#         LIMIT 10;
#     """)
#     avg_sim = sum(float(r[0]) for r in rows) / len(rows) if rows else 1.0

#     print()
#     print("  " + "─"*50)
#     print("  VERIFICATION")
#     print("  " + "─"*50)
#     print(f"  Total embeddings : {total:,}")
#     print(f"  Avg sim (sample) : {avg_sim:.6f}", end="  ")
#     if avg_sim < 0.95:
#         print("✅ Vectors are diverse — fix worked!")
#     else:
#         print("❌ Still similar — run script again")

#     # Test hybrid vector search
#     log("Testing vector searches...")
#     tests = [
#         ("coastal city in West Africa",
#          ["NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM"]),
#         ("desert city Arabian Peninsula",
#          ["AE","SA","KW","QA","BH","OM"]),
#         ("cold Nordic capital",
#          ["SE","NO","DK","FI","IS"]),
#         ("large city in East Asia",
#          ["CN","JP","KR","TW","HK"]),
#     ]

#     for query, codes in tests:
#         try:
#             resp = ollama.embed(model=EMBED_MODEL,
#                                 input=f"{QUERY_PREFIX}{query}")
#             vec  = resp["embeddings"][0]
#             rows = db.fetchall("""
#                 SELECT c.city_name, c.country_name,
#                        1-(e.embedding<=>%s::vector(1024)) as sim
#                 FROM city_embeddings e JOIN cities c ON c.id=e.city_id
#                 WHERE e.embedding IS NOT NULL AND c.country_code=ANY(%s)
#                 ORDER BY e.embedding<=>%s::vector(1024) LIMIT 3;
#             """, (json.dumps(vec), codes, json.dumps(vec)))

#             print(f"\n  '{query}'")
#             for city, country, sim in rows:
#                 bar = "█"*int(sim*20)
#                 print(f"    {city:<22} {country:<18} {sim:.4f}  {bar}")
#         except Exception as e:
#             print(f"  [{query}] {e}")

#     print()
#     print("  " + "─"*50)


# # ─────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────

# def main():
#     print()
#     print("═"*62)
#     print("  AXIOQUAN — Fast Embedder (Neon Free Tier Safe)")
#     print(f"  Model: {EMBED_MODEL}  |  Batch: {BATCH_SIZE}  |  Keepalive: every {KEEPALIVE_EVERY}")
#     print("═"*62)

#     verify_ollama()

#     db = DBConnection()
#     log("Connected to Neon PostgreSQL.")

#     # Install hybrid resolve_city()
#     log("Installing hybrid resolve_city() function...")
#     db.execute(HYBRID_RESOLVE)
#     db.commit()
#     log("resolve_city() installed.")

#     # Drop ivfflat (use exact cosine — faster for 31k rows, more accurate)
#     log("Dropping ivfflat index (switching to exact cosine search)...")
#     db.execute("DROP INDEX IF EXISTS idx_city_embeddings_vec;")
#     # Unique index on city_id is required for ON CONFLICT to work
#     db.execute("""
#         CREATE UNIQUE INDEX IF NOT EXISTS idx_city_embeddings_city_id_unique
#         ON city_embeddings(city_id);
#     """)
#     db.execute("""
#         CREATE INDEX IF NOT EXISTS idx_city_embeddings_city_id_btree
#         ON city_embeddings(city_id);
#     """)
#     db.commit()

#     # ── RESUME MODE — never truncate, always continue ───────
#     # Check how many cities are already embedded
#     done_row = db.fetchone("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
#     already_done = done_row[0] if done_row else 0
#     log(f"Already embedded: {already_done:,} cities — will skip these.")

#     # Load ONLY cities that do NOT yet have an embedding
#     # This is the key change — safe to restart anytime
#     log("Loading cities that still need embedding...")
#     cities = db.fetchall("""
#         SELECT c.id, c.city_name, c.country_name, c.country_code,
#                c.state_province, c.population, c.is_capital
#         FROM cities c
#         LEFT JOIN city_embeddings e
#             ON e.city_id = c.id AND e.embedding IS NOT NULL
#         WHERE e.id IS NULL
#         ORDER BY c.population DESC NULLS LAST;
#     """)
#     total  = len(cities)
#     log(f"Cities remaining to embed: {total:,}")
#     if already_done > 0:
#         log(f"Resuming from previous run. Total when complete: {already_done + total:,}")

#     if total == 0:
#         log("No cities found in database. Run 01_load_cities.py first.")
#         db.close()
#         return

#     log(f"Starting embedding. Will auto-reconnect if Neon drops connection.")
#     print()

#     processed  = 0
#     errors     = 0
#     start_time = time.time()

#     for i, city_row in enumerate(cities):
#         city_id = city_row[0]
#         content = build_content(city_row)

#         # Embed ONE city at a time (prevents duplicate vector bug)
#         try:
#             response = ollama.embed(model=EMBED_MODEL, input=content)
#             vector   = response["embeddings"][0]
#         except Exception as e:
#             errors += 1
#             if errors <= 3:
#                 log(f"\n  [OLLAMA ERROR] {e}")
#             time.sleep(1)
#             continue

#         # Upsert — ON CONFLICT skips cities already embedded
#         # This prevents duplicates if script restarts mid-run
#         try:
#             db.execute("""
#                 INSERT INTO city_embeddings(city_id, content, embedding)
#                 VALUES(%s, %s, %s::vector)
#                 ON CONFLICT (city_id) DO NOTHING;
#             """, (city_id, content, json.dumps(vector)))
#             processed += 1
#         except Exception as e:
#             errors += 1
#             if errors <= 3:
#                 log(f"\n  [DB ERROR] {e}")
#             continue

#         # Commit frequently — small transactions survive disconnects
#         if processed % COMMIT_EVERY == 0:
#             db.commit()

#         # Keepalive — prevents Neon idle timeout
#         if processed % KEEPALIVE_EVERY == 0:
#             db.keepalive()

#         # Progress display
#         if processed % 100 == 0 or processed == total:
#             progress(processed, total, start_time, errors)

#     # Final commit
#     db.commit()
#     print()
#     print()

#     elapsed = time.time() - start_time
#     log(f"Processed: {processed:,}  Errors: {errors}  Time: {elapsed/60:.1f} min")

#     verify(db)
#     db.close()

#     print()
#     log("Done! Run: python test_vector.py to confirm.")


# if __name__ == "__main__":
#     main()









































"""
╔══════════════════════════════════════════════════════════════╗
║   SCRIPT 03e — Fast Embedder (Neon Free Tier Safe)          ║
║                                                              ║
║   Fixes the slowness of 03d by:                             ║
║   1. No expensive duplicate detection query                 ║
║   2. Processes cities in small batches with keepalive       ║
║   3. Saves progress — safe to restart if disconnected       ║
║   4. Reconnects automatically if Neon drops the connection  ║
║                                                              ║
║   Run: python 03e_fast_embed.py                            ║
║   Time: ~20-40 minutes for 31,561 cities                   ║
║   Safe to restart: picks up from where it stopped          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import psycopg2
import psycopg2.extras
import ollama
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
EMBED_MODEL  = "mxbai-embed-large"   # 4/4 geographic accuracy, 1024-dim
EMBED_DIM    = 1024
DOC_PREFIX   = "search_document: "
QUERY_PREFIX = "search_query: "

# ── KEY SETTINGS FOR NEON FREE TIER ──────────────────────────
BATCH_SIZE       = 25     # small batches = more frequent commits
COMMIT_EVERY     = 25     # commit to DB every N cities
KEEPALIVE_EVERY  = 50     # send a SELECT 1 every N cities to prevent timeout
RECONNECT_WAIT   = 5      # seconds to wait before reconnecting


def log(msg):
    print(f"  {msg}", flush=True)


def progress(cur, total, start_time, errors):
    pct     = int(cur / total * 100)
    bar     = "█" * (pct // 5) + "░" * (20 - pct // 5)
    elapsed = time.time() - start_time
    rate    = cur / elapsed if elapsed > 0 else 0
    eta     = int((total - cur) / rate) if rate > 0 else 0
    eta_str = f"{eta//60}m{eta%60:02d}s" if eta > 0 else "?"
    print(
        f"\r  [{bar}] {pct:3d}%  {cur:,}/{total:,}  "
        f"ETA:{eta_str}  errors:{errors}",
        end="", flush=True
    )


# ─────────────────────────────────────────────────────────────
# ROBUST DB CONNECTION WITH AUTO-RECONNECT
# ─────────────────────────────────────────────────────────────

class DBConnection:
    """
    Wrapper that automatically reconnects to Neon if the
    connection drops due to the free tier idle timeout.
    """
    def __init__(self):
        self.conn   = None
        self.cursor = None
        self._connect()

    def _connect(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        self.conn   = psycopg2.connect(
            DATABASE_URL,
            keepalives=1,
            keepalives_idle=30,      # send keepalive after 30s idle
            keepalives_interval=10,  # retry every 10s
            keepalives_count=5,      # give up after 5 retries
        )
        self.conn.autocommit = False

    def execute(self, sql, params=None):
        """Execute with automatic reconnect on failure."""
        for attempt in range(3):
            try:
                cursor = self.conn.cursor()
                cursor.execute(sql, params)
                return cursor
            except (psycopg2.OperationalError,
                    psycopg2.InterfaceError) as e:
                log(f"\n  [DB RECONNECT] attempt {attempt+1}: {e}")
                time.sleep(RECONNECT_WAIT)
                self._connect()
        raise RuntimeError("Could not reconnect to database after 3 attempts")

    def commit(self):
        for attempt in range(3):
            try:
                self.conn.commit()
                return
            except Exception as e:
                log(f"\n  [COMMIT ERROR] {e}")
                time.sleep(RECONNECT_WAIT)
                self._connect()

    def fetchall(self, sql, params=None):
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def fetchone(self, sql, params=None):
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def keepalive(self):
        """Prevents Neon from dropping the idle connection."""
        try:
            self.execute("SELECT 1")
        except Exception:
            self._connect()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# BUILD EXPLICIT CITY CONTENT
# Same rich content as 03c/03d for quality embeddings
# ─────────────────────────────────────────────────────────────

def build_content(row) -> str:
    city_id, name, country, cc, state, pop, capital = row
    pop     = pop or 0
    state   = state or ""
    capital = capital or False

    parts = [f"{name} is a city in {country}."]
    if state:
        parts.append(f"It is in the {state} region.")
    if capital:
        parts.append(f"{name} is the capital of {country}.")

    # Region classification
    wa_coastal = {"NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM","CV","GW"}
    wa_inland  = {"ML","BF","NE","MR"}
    ea         = {"KE","TZ","ET","UG","RW","BI","ER","DJ","SO","MG"}
    na_r       = {"EG","LY","TN","DZ","MA","SD"}
    ca_r       = {"CD","CG","CF","CM","GA","GQ","ST","TD"}
    sa_r       = {"ZA","MZ","ZM","ZW","MW","NA","BW","LS","SZ","AO"}
    me         = {"AE","SA","IQ","IR","IL","JO","LB","KW","QA","BH","OM","YE","SY","TR"}
    sas        = {"IN","PK","BD","LK","NP","AF"}
    eas        = {"CN","JP","KR","TW","HK","MN"}
    seas       = {"SG","TH","ID","MY","VN","PH","MM","KH","LA"}
    we         = {"GB","FR","DE","IT","ES","NL","BE","PT","AT","CH","IE"}
    ee         = {"PL","CZ","HU","RO","BG","UA","BY","RS","HR","SK","SI"}
    scan       = {"SE","NO","DK","FI","IS"}
    nam        = {"US","CA"}
    sam        = {"BR","AR","CO","PE","VE","CL","EC","BO","PY","UY"}
    oce        = {"AU","NZ","PG","FJ"}

    if cc in wa_coastal:
        parts.append(f"{name} is in West Africa on the African continent.")
        # Only mark as coastal if the city is actually in the capital/coastal region
        # Use latitude/longitude proximity to coast as a proxy
        # West African coast runs roughly from lat 4 to 15, lon -17 to 3
        # Cities with state codes suggesting coastal regions get coastal label
        # Otherwise mark as inland to avoid misleading the embedding model
        coastal_capitals = {
            "NG": "Lagos",   # Nigeria coastal
            "GH": "Accra",   # Ghana coastal
            "SN": "Dakar",   # Senegal coastal
            "CI": "Abidjan", # Ivory Coast coastal
            "GN": "Conakry", # Guinea — capital is coastal but most cities inland
            "LR": "Monrovia",# Liberia coastal
            "SL": "Freetown",# Sierra Leone coastal
            "GM": "Banjul",  # Gambia coastal
            "GW": "Bissau",  # Guinea-Bissau coastal
            "CV": "Praia",   # Cape Verde island — all coastal
            "BJ": "Cotonou", # Benin coastal
            "TG": "Lome",    # Togo coastal
        }
        # A city is considered coastal if:
        # 1. It IS the coastal capital, OR
        # 2. It is Cape Verde (all islands), OR  
        # 3. It is the capital city of a coastal country
        is_coastal = (
            cc == "CV" or  # Cape Verde — entire country is islands
            capital or     # Capital cities are typically on the coast
            name in coastal_capitals.values()  # Known coastal cities
        )
        if is_coastal:
            parts.append(f"Coastal city on the Atlantic Ocean in West Africa. Port city.")
        else:
            parts.append(f"City in West Africa. Inland or interior region of the country.")
    elif cc in wa_inland:
        parts.append(f"{name} is an inland city in West Africa, African continent.")
    elif cc in ea:
        parts.append(f"{name} is in East Africa.")
        if cc in {"KE","TZ","MZ","ER","DJ","SO"}:
            parts.append("Coastal city on the Indian Ocean, East Africa.")
        else:
            parts.append("Inland city in East Africa.")
    elif cc in na_r:
        parts.append(f"{name} is in North Africa.")
        if cc in {"EG","LY","TN","DZ","MA"}:
            parts.append("Mediterranean or North African coastal region.")
    elif cc in ca_r:
        parts.append(f"{name} is in Central Africa, African continent.")
    elif cc in sa_r:
        parts.append(f"{name} is in Southern Africa.")
        if cc in {"ZA","MZ","AO","NA"}:
            parts.append("May be coastal, Atlantic or Indian Ocean, Southern Africa.")
    elif cc in me:
        parts.append(f"{name} is in the Middle East.")
        if cc in {"AE","QA","BH","KW","SA","OM"}:
            parts.append("Arabian Peninsula. Hot desert climate. Gulf state. Persian Gulf.")
        elif cc in {"IL","LB"}:
            parts.append("Mediterranean coastal city, Middle East.")
    elif cc in sas:
        parts.append(f"{name} is in South Asia.")
        if cc == "IN": parts.append("India, South Asian subcontinent.")
        if cc in {"IN","BD","LK","PK"}:
            parts.append("May be coastal, Indian Ocean.")
    elif cc in eas:
        parts.append(f"{name} is in East Asia.")
        if cc == "JP":
            parts.append("Japan. Island nation. Pacific Ocean. East Asia.")
        elif cc == "CN":
            parts.append("China. Most populous country. East Asia.")
        elif cc == "KR":
            parts.append("South Korea. Korean peninsula. East Asia.")
    elif cc in seas:
        parts.append(f"{name} is in Southeast Asia.")
        if cc in {"SG","ID","PH","MY","VN","TH"}:
            parts.append("Coastal or island city, Southeast Asia.")
    elif cc in we:
        parts.append(f"{name} is in Western Europe.")
        labels = {"GB":"United Kingdom British Isles","FR":"France Francophone",
                  "DE":"Germany Central Europe","IT":"Italy Mediterranean Southern Europe",
                  "ES":"Spain Iberian Peninsula Mediterranean"}
        if cc in labels:
            parts.append(labels[cc])
    elif cc in ee:
        parts.append(f"{name} is in Eastern Europe.")
    elif cc in scan:
        parts.append(f"{name} is in Scandinavia, Northern Europe. Cold Nordic climate.")
    elif cc == "US":
        parts.append(f"{name} is a city in the United States of America, North America.")
        coastal = {"CA","OR","WA","TX","LA","FL","GA","SC","NC","VA",
                   "MD","DE","NJ","NY","CT","RI","MA","ME","AK","HI"}
        if state in coastal:
            parts.append(f"Coastal US city in {state}, United States.")
        elif state:
            parts.append(f"Inland US city in {state}, United States.")
    elif cc == "CA":
        parts.append(f"{name} is in Canada, North America.")
    elif cc in sam:
        parts.append(f"{name} is in South America, Latin America.")
        if cc in {"BR","AR","CL","PE","CO","VE","EC","UY"}:
            parts.append("May be coastal, Atlantic or Pacific, South America.")
    elif cc in oce:
        parts.append(f"{name} is in Oceania, Pacific region.")
        if cc in {"AU","NZ","FJ","PG"}:
            parts.append("Coastal city, Pacific or Indian Ocean, Oceania.")

    # Population
    if pop > 10_000_000:
        parts.append("Megacity with over 10 million people.")
    elif pop > 5_000_000:
        parts.append("Very large city, over 5 million people.")
    elif pop > 1_000_000:
        parts.append("Major city, over 1 million people.")
    elif pop > 500_000:
        parts.append("Large city.")
    elif pop > 100_000:
        parts.append("Medium-sized city.")
    else:
        parts.append("Small town.")

    return f"{DOC_PREFIX}{' '.join(parts)}"


# ─────────────────────────────────────────────────────────────
# VERIFY OLLAMA
# ─────────────────────────────────────────────────────────────

def verify_ollama():
    log(f"Verifying Ollama + {EMBED_MODEL}...")
    try:
        test = ollama.embed(model=EMBED_MODEL, input=f"{DOC_PREFIX}test")
        dim  = len(test["embeddings"][0])
        if dim != EMBED_DIM:
            raise ValueError(f"Expected {EMBED_DIM}D, got {dim}D")
        log(f"Ollama OK. Vector dimension: {dim}")
    except ollama.ResponseError:
        print(f"\n  [ERROR] Model '{EMBED_MODEL}' not found.")
        print(f"  Run: ollama pull {EMBED_MODEL}")
        sys.exit(1)
    except ConnectionError:
        print(f"\n  [ERROR] Cannot connect to Ollama.")
        print(f"  Run: ollama serve  (in a separate terminal)")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# GET CITIES THAT NEED RE-EMBEDDING
# Strategy: find cities whose embedding is identical to another
# city's embedding — using a FAST query (no text cast)
# ─────────────────────────────────────────────────────────────

def get_cities_to_fix(db: DBConnection) -> list:
    """
    Returns city_ids that need re-embedding.

    FAST approach: instead of casting vectors to text (slow),
    we use a random sample to estimate the duplicate rate,
    then simply re-embed ALL cities that were processed in
    batches > 1 (i.e. all except the first in each batch).

    Even simpler: since 03b processed in batches of 50,
    we know every 2nd-50th city in each batch got a duplicate.
    We re-embed all cities ordered by id, skipping cities
    whose embedding is already verified unique via a fast
    self-similarity check on a small sample.
    """
    log("Checking embedding quality with fast sample test...")

    # Fast check: take 10 random pairs and measure similarity
    # If avg similarity > 0.999 — most are duplicates
    rows = db.fetchall("""
        SELECT e1.city_id, 1-(e1.embedding<=>e2.embedding) as sim
        FROM city_embeddings e1
        JOIN city_embeddings e2
          ON e2.city_id = e1.city_id + 1
        WHERE e1.embedding IS NOT NULL
          AND e2.embedding IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 20;
    """)

    if rows:
        avg_sim = sum(float(r[1]) for r in rows) / len(rows)
        log(f"Average similarity between adjacent cities: {avg_sim:.6f}")

        if avg_sim > 0.999:
            log("Confirmed: most embeddings are identical (batch duplication bug).")
            log("Will re-embed ALL cities.")
            needs_all = True
        elif avg_sim > 0.95:
            log("Many duplicates detected. Will re-embed ALL cities to be safe.")
            needs_all = True
        else:
            log("Embeddings look diverse. Only re-embedding cities with NULL embeddings.")
            needs_all = False
    else:
        log("Cannot sample — re-embedding all cities.")
        needs_all = True

    if needs_all:
        rows = db.fetchall("""
            SELECT c.id, c.city_name, c.country_name, c.country_code,
                   c.state_province, c.population, c.is_capital
            FROM cities c
            ORDER BY c.population DESC NULLS LAST;
        """)
    else:
        rows = db.fetchall("""
            SELECT c.id, c.city_name, c.country_name, c.country_code,
                   c.state_province, c.population, c.is_capital
            FROM cities c
            LEFT JOIN city_embeddings e
                ON e.city_id = c.id AND e.embedding IS NOT NULL
            WHERE e.id IS NULL
            ORDER BY c.population DESC NULLS LAST;
        """)

    log(f"Cities to re-embed: {len(rows):,}")
    return rows


# ─────────────────────────────────────────────────────────────
# INSTALL HYBRID resolve_city() FUNCTION
# ─────────────────────────────────────────────────────────────

HYBRID_RESOLVE = """
CREATE OR REPLACE FUNCTION resolve_city(
    input_text   TEXT,
    query_vector vector(1024) DEFAULT NULL,
    region_codes TEXT[]      DEFAULT NULL
)
RETURNS TABLE(
    city_id INTEGER, city_name VARCHAR, country_name VARCHAR,
    country_code CHAR(2), latitude DECIMAL, longitude DECIMAL,
    timezone VARCHAR, resolution TEXT
) AS $$
DECLARE clean_input TEXT := LOWER(TRIM(input_text));
BEGIN
    RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
        c.latitude,c.longitude,c.timezone,'exact_match'::TEXT
        FROM cities c WHERE LOWER(c.ascii_name)=clean_input OR LOWER(c.city_name)=clean_input
        ORDER BY c.population DESC NULLS LAST LIMIT 1;
    IF FOUND THEN RETURN; END IF;

    RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
        c.latitude,c.longitude,c.timezone,'alias_match'::TEXT
        FROM city_aliases a JOIN cities c ON c.id=a.city_id
        WHERE LOWER(a.alias)=clean_input
        ORDER BY c.population DESC NULLS LAST LIMIT 1;
    IF FOUND THEN RETURN; END IF;

    RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
        c.latitude,c.longitude,c.timezone,'fulltext_match'::TEXT
        FROM cities c WHERE to_tsvector('english',c.city_name||' '||c.country_name)
        @@plainto_tsquery('english',clean_input)
        ORDER BY c.population DESC NULLS LAST LIMIT 1;
    IF FOUND THEN RETURN; END IF;

    IF query_vector IS NOT NULL THEN
        IF region_codes IS NOT NULL AND array_length(region_codes,1)>0 THEN
            RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
                c.latitude,c.longitude,c.timezone,'hybrid_vector_region'::TEXT
                FROM city_embeddings e JOIN cities c ON c.id=e.city_id
                WHERE e.embedding IS NOT NULL AND c.country_code=ANY(region_codes)
                ORDER BY e.embedding<=>query_vector LIMIT 1;
            IF FOUND THEN RETURN; END IF;
        END IF;
        RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
            c.latitude,c.longitude,c.timezone,'vector_match'::TEXT
            FROM city_embeddings e JOIN cities c ON c.id=e.city_id
            WHERE e.embedding IS NOT NULL
            ORDER BY e.embedding<=>query_vector LIMIT 1;
    END IF;

    RETURN QUERY SELECT c.id,c.city_name,c.country_name,c.country_code,
        c.latitude,c.longitude,c.timezone,'partial_match'::TEXT
        FROM cities c WHERE LOWER(c.ascii_name) LIKE '%'||clean_input||'%'
        OR LOWER(c.city_name) LIKE '%'||clean_input||'%'
        ORDER BY c.population DESC NULLS LAST LIMIT 1;
END;
$$ LANGUAGE plpgsql;
"""


# ─────────────────────────────────────────────────────────────
# VERIFY RESULTS
# ─────────────────────────────────────────────────────────────

def verify(db: DBConnection):
    row    = db.fetchone("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
    total  = row[0]

    # Fast uniqueness check using similarity on small sample
    rows   = db.fetchall("""
        SELECT 1-(e1.embedding<=>e2.embedding) as sim
        FROM city_embeddings e1 JOIN city_embeddings e2
          ON e2.city_id = e1.city_id + 50
        WHERE e1.embedding IS NOT NULL AND e2.embedding IS NOT NULL
        LIMIT 10;
    """)
    avg_sim = sum(float(r[0]) for r in rows) / len(rows) if rows else 1.0

    print()
    print("  " + "─"*50)
    print("  VERIFICATION")
    print("  " + "─"*50)
    print(f"  Total embeddings : {total:,}")
    print(f"  Avg sim (sample) : {avg_sim:.6f}", end="  ")
    if avg_sim < 0.95:
        print("✅ Vectors are diverse — fix worked!")
    else:
        print("❌ Still similar — run script again")

    # Test hybrid vector search
    log("Testing vector searches...")
    tests = [
        ("coastal city in West Africa",
         ["NG","GH","SN","CI","BJ","TG","LR","SL","GN","GM"]),
        ("desert city Arabian Peninsula",
         ["AE","SA","KW","QA","BH","OM"]),
        ("cold Nordic capital",
         ["SE","NO","DK","FI","IS"]),
        ("large city in East Asia",
         ["CN","JP","KR","TW","HK"]),
    ]

    for query, codes in tests:
        try:
            resp = ollama.embed(model=EMBED_MODEL,
                                input=f"{QUERY_PREFIX}{query}")
            vec  = resp["embeddings"][0]
            rows = db.fetchall("""
                SELECT c.city_name, c.country_name,
                       1-(e.embedding<=>%s::vector(1024)) as sim
                FROM city_embeddings e JOIN cities c ON c.id=e.city_id
                WHERE e.embedding IS NOT NULL AND c.country_code=ANY(%s)
                ORDER BY e.embedding<=>%s::vector(1024) LIMIT 3;
            """, (json.dumps(vec), codes, json.dumps(vec)))

            print(f"\n  '{query}'")
            for city, country, sim in rows:
                bar = "█"*int(sim*20)
                print(f"    {city:<22} {country:<18} {sim:.4f}  {bar}")
        except Exception as e:
            print(f"  [{query}] {e}")

    print()
    print("  " + "─"*50)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print()
    print("═"*62)
    print("  AXIOQUAN — Fast Embedder (Neon Free Tier Safe)")
    print(f"  Model: {EMBED_MODEL}  |  Batch: {BATCH_SIZE}  |  Keepalive: every {KEEPALIVE_EVERY}")
    print("═"*62)

    verify_ollama()

    db = DBConnection()
    log("Connected to Neon PostgreSQL.")

    # Install hybrid resolve_city()
    log("Installing hybrid resolve_city() function...")
    db.execute(HYBRID_RESOLVE)
    db.commit()
    log("resolve_city() installed.")

    # Drop ivfflat (use exact cosine — faster for 31k rows, more accurate)
    log("Dropping ivfflat index (switching to exact cosine search)...")
    db.execute("DROP INDEX IF EXISTS idx_city_embeddings_vec;")
    # Unique index on city_id is required for ON CONFLICT to work
    db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_city_embeddings_city_id_unique
        ON city_embeddings(city_id);
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_city_embeddings_city_id_btree
        ON city_embeddings(city_id);
    """)
    db.commit()

    # ── RESUME MODE — never truncate, always continue ───────
    # Check how many cities are already embedded
    done_row = db.fetchone("SELECT COUNT(*) FROM city_embeddings WHERE embedding IS NOT NULL;")
    already_done = done_row[0] if done_row else 0
    log(f"Already embedded: {already_done:,} cities — will skip these.")

    # Load ONLY cities that do NOT yet have an embedding
    # This is the key change — safe to restart anytime
    log("Loading cities that still need embedding...")
    cities = db.fetchall("""
        SELECT c.id, c.city_name, c.country_name, c.country_code,
               c.state_province, c.population, c.is_capital
        FROM cities c
        LEFT JOIN city_embeddings e
            ON e.city_id = c.id AND e.embedding IS NOT NULL
        WHERE e.id IS NULL
        ORDER BY c.population DESC NULLS LAST;
    """)
    log(f"Note: cities with existing embeddings are skipped (resume mode)")
    log(f"To re-embed specific regions, use 03f_fix_west_africa.py")
    total  = len(cities)
    log(f"Cities remaining to embed: {total:,}")
    if already_done > 0:
        log(f"Resuming from previous run. Total when complete: {already_done + total:,}")

    if total == 0:
        log("No cities found in database. Run 01_load_cities.py first.")
        db.close()
        return

    log(f"Starting embedding. Will auto-reconnect if Neon drops connection.")
    print()

    processed  = 0
    errors     = 0
    start_time = time.time()

    for i, city_row in enumerate(cities):
        city_id = city_row[0]
        content = build_content(city_row)

        # Embed ONE city at a time (prevents duplicate vector bug)
        try:
            response = ollama.embed(model=EMBED_MODEL, input=content)
            vector   = response["embeddings"][0]
        except Exception as e:
            errors += 1
            if errors <= 3:
                log(f"\n  [OLLAMA ERROR] {e}")
            time.sleep(1)
            continue

        # Upsert — ON CONFLICT skips cities already embedded
        # This prevents duplicates if script restarts mid-run
        try:
            db.execute("""
                INSERT INTO city_embeddings(city_id, content, embedding)
                VALUES(%s, %s, %s::vector)
                ON CONFLICT (city_id) DO NOTHING;
            """, (city_id, content, json.dumps(vector)))
            processed += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                log(f"\n  [DB ERROR] {e}")
            continue

        # Commit frequently — small transactions survive disconnects
        if processed % COMMIT_EVERY == 0:
            db.commit()

        # Keepalive — prevents Neon idle timeout
        if processed % KEEPALIVE_EVERY == 0:
            db.keepalive()

        # Progress display
        if processed % 100 == 0 or processed == total:
            progress(processed, total, start_time, errors)

    # Final commit
    db.commit()
    print()
    print()

    elapsed = time.time() - start_time
    log(f"Processed: {processed:,}  Errors: {errors}  Time: {elapsed/60:.1f} min")

    verify(db)
    db.close()

    print()
    log("Done! Run: python test_vector.py to confirm.")


if __name__ == "__main__":
    main()
