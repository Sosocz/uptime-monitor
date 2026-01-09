"""
Migration: Add onboarding tracking fields to users table
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add onboarding tracking fields to users table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Add onboarding tracking fields
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS onboarding_email_j1_sent BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS onboarding_email_j3_sent BOOLEAN DEFAULT FALSE;
        """)

        conn.commit()
        print("✅ Onboarding fields added to users table")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
