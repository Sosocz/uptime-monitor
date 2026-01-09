"""
Migration: Add indexes to onboarding fields for performance
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add indexes to onboarding fields."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Add composite index for onboarding email check queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_onboarding_j1
            ON users(created_at, onboarding_email_j1_sent, onboarding_completed, is_active)
            WHERE onboarding_email_j1_sent = FALSE AND onboarding_completed = FALSE AND is_active = TRUE;
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_onboarding_j3
            ON users(created_at, onboarding_email_j3_sent, onboarding_completed, is_active)
            WHERE onboarding_email_j3_sent = FALSE AND onboarding_completed = FALSE AND is_active = TRUE;
        """)

        conn.commit()
        print("✅ Onboarding indexes added to users table")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
