"""Add status_pages and status_page_monitors tables"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Create status_pages and status_page_monitors tables."""
    with engine.connect() as conn:
        # Check if status_pages table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='status_pages'
        """))

        if not result.fetchone():
            print("Creating status_pages table...")

            conn.execute(text("""
                CREATE TABLE status_pages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    slug VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    logo_url VARCHAR,
                    custom_domain VARCHAR,
                    is_public BOOLEAN DEFAULT TRUE,
                    access_token VARCHAR,
                    header_text TEXT,
                    brand_color VARCHAR DEFAULT '#3b82f6',
                    show_uptime_percentage BOOLEAN DEFAULT TRUE,
                    show_response_time BOOLEAN DEFAULT TRUE,
                    show_incident_history BOOLEAN DEFAULT TRUE
                )
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX idx_status_pages_user_id ON status_pages(user_id);
                CREATE INDEX idx_status_pages_slug ON status_pages(slug);
            """))

            conn.commit()
            print("status_pages table created successfully!")
        else:
            print("status_pages table already exists, skipping.")

        # Check if status_page_monitors table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='status_page_monitors'
        """))

        if not result.fetchone():
            print("Creating status_page_monitors table...")

            conn.execute(text("""
                CREATE TABLE status_page_monitors (
                    id SERIAL PRIMARY KEY,
                    status_page_id INTEGER NOT NULL REFERENCES status_pages(id) ON DELETE CASCADE,
                    monitor_id INTEGER NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
                    position INTEGER DEFAULT 0
                )
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX idx_status_page_monitors_status_page_id ON status_page_monitors(status_page_id);
                CREATE INDEX idx_status_page_monitors_monitor_id ON status_page_monitors(monitor_id);
            """))

            conn.commit()
            print("status_page_monitors table created successfully!")
        else:
            print("status_page_monitors table already exists, skipping.")


if __name__ == "__main__":
    upgrade()
