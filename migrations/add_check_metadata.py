"""Add metadata columns to checks table"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add new columns to checks table."""
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='checks' AND column_name='ip_address'
        """))

        if not result.fetchone():
            print("Adding new metadata columns to checks table...")

            conn.execute(text("""
                ALTER TABLE checks
                ADD COLUMN ip_address VARCHAR,
                ADD COLUMN server VARCHAR,
                ADD COLUMN content_type VARCHAR,
                ADD COLUMN ssl_expires_at TIMESTAMP,
                ADD COLUMN response_headers TEXT
            """))
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Columns already exist, skipping migration.")


if __name__ == "__main__":
    upgrade()
