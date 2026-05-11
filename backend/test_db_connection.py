#!/usr/bin/env python
"""Test database connection with real credentials"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    print("\n" + "="*60)
    print("Testing Database Connection")
    print("="*60)
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    # Mask password for display
    masked_url = DATABASE_URL.replace(
        DATABASE_URL.split(":")[2].split("@")[0], 
        "***HIDDEN***"
    )
    print(f"📡 Connecting to: {masked_url[:80]}...")
    
    try:
        # Attempt connection
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version(), current_database(), current_user")
        version, db_name, user = cursor.fetchone()
        
        print("\n✅ Connection Successful!")
        print(f"   Database: {db_name}")
        print(f"   User: {user}")
        print(f"   PostgreSQL Version: {version.split(',')[0]}")
        
        # Check for cities table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cities'
            );
        """)
        has_cities = cursor.fetchone()[0]
        
        if has_cities:
            cursor.execute("SELECT COUNT(*) FROM cities")
            city_count = cursor.fetchone()[0]
            print(f"\n📊 Cities table found: {city_count:,} cities loaded")
        else:
            print("\n⚠️  Cities table not found. Run 01_load_cities.py first")
        
        # Check for other tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Existing tables ({len(tables)}):")
            for table in tables[:10]:  # Show first 10
                print(f"   - {table[0]}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Database is ready for use!")
        print("="*60)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection Failed: {e}")
        print("\nPossible issues:")
        print("   - Check if database URL is correct")
        print("   - Check if IP is allowed in Neon")
        print("   - Check if database exists")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)