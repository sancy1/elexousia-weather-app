import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found in environment variables")

# Parse the database URL
# Expected format: postgresql://user:password@host:port/database
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgres://")

conn = None
try:
    # Connect to database
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Read migration file and execute directly
    with open('app/migrations/005_saved_locations.sql', 'r') as f:
        sql = f.read()
        print(f"Executing migration...")
        cursor.execute(sql)
    
    print("Migration completed successfully")
    
except Exception as e:
    print(f"Migration failed: {e}")
    if conn:
        conn.rollback()
finally:
    if conn:
        conn.close()
