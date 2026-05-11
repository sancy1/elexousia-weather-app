#!/usr/bin/env python
"""
FILE: backend/get_schemas.py
Query actual database schemas for all tables.
Includes connection diagnostics and graceful error handling.
"""

import os
import sys
import socket

# ── Load .env ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    # Walk up directories to find .env if not in current folder
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(3):
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ Loaded .env from: {env_path}")
            break
        current = os.path.dirname(current)
    else:
        load_dotenv()  # fallback: look in cwd
except ImportError:
    print("⚠️  python-dotenv not installed. Reading environment variables directly.")

# ── Read DATABASE_URL ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    print("\n❌ ERROR: DATABASE_URL is not set.")
    print("   Make sure your .env file exists and contains:")
    print("   DATABASE_URL=postgresql://user:password@host/dbname")
    sys.exit(1)

# ── Mask password for safe printing ───────────────────────────────────────
def mask_url(url: str) -> str:
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(url)
        masked = p._replace(netloc=f"{p.username}:***@{p.hostname}" +
                            (f":{p.port}" if p.port else ""))
        return urlunparse(masked)
    except Exception:
        return url[:40] + "***"

print(f"🔗 DATABASE_URL (masked): {mask_url(DATABASE_URL)}")

# ── DNS check before attempting connection ─────────────────────────────────
def check_dns(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname
        if not host:
            print("❌ Could not parse hostname from DATABASE_URL")
            return False
        print(f"🌐 Checking DNS for host: {host}")
        ip = socket.gethostbyname(host)
        print(f"✅ DNS resolved: {host} → {ip}")
        return True
    except socket.gaierror as e:
        print(f"\n❌ DNS RESOLUTION FAILED: {e}")
        print("\n── Possible causes ──────────────────────────────────────────")
        print("  1. You are offline or on a restricted network")
        print("  2. The hostname in DATABASE_URL is wrong")
        print("  3. Your DNS server is not reachable")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during DNS check: {e}")
        return False

# ── Try importing psycopg2 ─────────────────────────────────────────────────
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("\n❌ psycopg2 is not installed.")
    print("   Run:  pip install psycopg2-binary")
    sys.exit(1)

# ── Schema helpers ─────────────────────────────────────────────────────────
def get_table_schema(cursor, table_name: str) -> list:
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return cursor.fetchall()


def get_constraints(cursor, table_name: str) -> list:
    """Return primary keys, foreign keys, unique constraints."""
    cursor.execute("""
        SELECT
            tc.constraint_type,
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name  AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema    = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema    = tc.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.table_name   = %s
          AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
        ORDER BY tc.constraint_type, kcu.column_name
    """, (table_name,))
    return cursor.fetchall()


def get_indexes(cursor, table_name: str) -> list:
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename  = %s
        ORDER BY indexname
    """, (table_name,))
    return cursor.fetchall()


def resolve_type(col: dict) -> str:
    """Return a clean, readable type string."""
    base = col["data_type"]
    udt  = col.get("udt_name", "")

    if base == "ARRAY":
        element = udt.lstrip("_") if udt.startswith("_") else udt
        return f"{element}[]"
    if base == "USER-DEFINED":
        return udt or "user-defined"
    if base == "character varying":
        maxlen = col.get("character_maximum_length")
        return f"varchar({maxlen})" if maxlen else "varchar"
    if base == "numeric":
        p, s = col.get("numeric_precision"), col.get("numeric_scale")
        if p is not None and s is not None:
            return f"numeric({p},{s})"
    return base


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 80)
    print("  ACTUAL DATABASE SCHEMAS")
    print("=" * 80)

    # DNS check first
    if not check_dns(DATABASE_URL):
        sys.exit(1)

    # ── Connect ────────────────────────────────────────────────────────────
    print("\n🔌 Connecting to PostgreSQL …")
    try:
        # IMPORTANT: NO options parameter for Neon pooled connections!
        conn = psycopg2.connect(
            DATABASE_URL,
            connect_timeout=15  # seconds only - no statement_timeout
        )
        conn.set_session(readonly=True, autocommit=True)
        print("✅ Connected successfully\n")
    except psycopg2.OperationalError as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("\n── Common fixes ─────────────────────────────────────────────")
        print("  • Verify the password in DATABASE_URL is correct")
        print("  • Check that the database name exists")
        print("  • Ensure your IP is allowed (Neon → Settings → Connection)")
        print("  • Try the connection string directly in psql")
        sys.exit(1)

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # ── List tables ────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type   = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()

    if not tables:
        print("⚠️  No tables found in the 'public' schema.")
        cursor.close()
        conn.close()
        sys.exit(0)

    print(f"📦 Found {len(tables)} table(s): "
          + ", ".join(t["table_name"] for t in tables))

    # ── Per-table output ───────────────────────────────────────────────────
    for table in tables:
        table_name = table["table_name"]

        print(f"\n{'─' * 80}")
        print(f"📋  TABLE: {table_name.upper()}")
        print(f"{'─' * 80}")

        # Columns
        columns = get_table_schema(cursor, table_name)

        col_w   = 28
        type_w  = 22
        null_w  = 10
        def_w   = 30

        header  = (f"{'Column':<{col_w}} {'Type':<{type_w}} "
                   f"{'Nullable':<{null_w}} {'Default':<{def_w}}")
        divider = f"{'-'*col_w} {'-'*type_w} {'-'*null_w} {'-'*def_w}"
        print(header)
        print(divider)

        for col in columns:
            col_name = col["column_name"]
            col_type = resolve_type(col)
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            default  = str(col["column_default"] or "")
            if len(default) > def_w - 1:
                default = default[:def_w - 4] + "…"

            print(f"{col_name:<{col_w}} {col_type:<{type_w}} "
                  f"{nullable:<{null_w}} {default:<{def_w}}")

        # Constraints
        constraints = get_constraints(cursor, table_name)
        if constraints:
            print("\n  ── Constraints ───────────────────────────────────────")
            for c in constraints:
                ctype  = c["constraint_type"]
                col    = c["column_name"]
                if ctype == "PRIMARY KEY":
                    print(f"  🔑 PK  : {col}")
                elif ctype == "FOREIGN KEY":
                    print(f"  🔗 FK  : {col} → "
                          f"{c['foreign_table']}.{c['foreign_column']}")
                elif ctype == "UNIQUE":
                    print(f"  🔒 UQ  : {col}")

        # Indexes
        indexes = get_indexes(cursor, table_name)
        if indexes:
            print("\n  ── Indexes ───────────────────────────────────────────")
            for idx in indexes:
                print(f"  📇 {idx['indexname']}")
                defn = idx["indexdef"]
                if len(defn) > 76:
                    defn = defn[:73] + "…"
                print(f"       {defn}")

        # Row count
        try:
            cursor.execute(f'SELECT COUNT(*) AS count FROM "{table_name}"')
            row = cursor.fetchone()
            print(f"\n  📊 Row count: {int(row['count']):,}")
        except Exception as e:
            print(f"\n  ⚠️  Could not count rows: {e}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("  COMPLETE — Use these schemas to build / verify models.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()