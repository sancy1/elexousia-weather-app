#!/usr/bin/env python
"""
FILE: backend/test_db_simple.py
Simple database test without any config imports
"""

import os
import sys
import asyncio
import time
import psycopg2
from psycopg2 import pool, OperationalError
from dotenv import load_dotenv

# Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

print("\n" + "="*60)
print("DATABASE CONNECTION TEST")
print("="*60)

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

print(f"✅ DATABASE_URL found")
print(f"✅ WEATHER_API_KEY found: {WEATHER_API_KEY[:10]}...")

# Test connection with retry
max_retries = 5
delay = 1

for attempt in range(max_retries):
    try:
        print(f"\n🔄 Attempt {attempt + 1}/{max_retries}...")
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version(), current_database(), NOW()")
        version, db_name, now = cursor.fetchone()
        
        print("\n" + "="*60)
        print("✅ CONNECTION SUCCESSFUL!")
        print("="*60)
        print(f"📊 Database: {db_name}")
        print(f"🐘 Version: {version.split(',')[0]}")
        print(f"⏰ Time: {now}")
        
        # Check cities
        cursor.execute("SELECT COUNT(*) FROM cities")
        city_count = cursor.fetchone()[0]
        print(f"🏙️  Cities: {city_count:,}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database is ready!")
        print("="*60 + "\n")
        
        # Test a simple weather query
        print("\n🌤️  Testing Weather API...")
        import httpx
        
        response = httpx.get(
            "https://api.weatherapi.com/v1/current.json",
            params={"key": WEATHER_API_KEY, "q": "Lagos"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Weather API working!")
            print(f"   Lagos: {data['current']['temp_c']}°C, {data['current']['condition']['text']}")
        else:
            print(f"⚠️  Weather API returned {response.status_code}")
        
        sys.exit(0)
        
    except OperationalError as e:
        print(f"   ❌ Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            print(f"   ⏳ Retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay * 2, 30)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        if attempt < max_retries - 1:
            time.sleep(delay)
            delay = min(delay * 2, 30)

print("\n❌ All connection attempts failed")
sys.exit(1)