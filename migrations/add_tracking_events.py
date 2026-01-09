"""
Migration: Add tracking_events table
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add tracking_events table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tracking_events (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                event_type VARCHAR NOT NULL,
                event_data JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_tracking_user_id ON tracking_events(user_id);
            CREATE INDEX IF NOT EXISTS idx_tracking_event_type ON tracking_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_tracking_created_at ON tracking_events(created_at);
        """)

        conn.commit()
        print("✅ tracking_events table created")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
