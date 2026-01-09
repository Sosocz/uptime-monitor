"""
Migration: Add show_powered_by field to status_pages table
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add show_powered_by field to status_pages table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Add show_powered_by field
        cur.execute("""
            ALTER TABLE status_pages
            ADD COLUMN IF NOT EXISTS show_powered_by BOOLEAN DEFAULT TRUE;
        """)

        conn.commit()
        print("✅ show_powered_by field added to status_pages table")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
