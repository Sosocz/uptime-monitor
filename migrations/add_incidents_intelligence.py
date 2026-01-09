"""Add intelligence fields to incidents table"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add intelligence columns to incidents table."""
    with engine.connect() as conn:
        # Check if intelligent_cause column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='incidents' AND column_name='intelligent_cause'
        """))

        if not result.fetchone():
            print("Adding intelligence columns to incidents table...")

            conn.execute(text("""
                ALTER TABLE incidents
                ADD COLUMN IF NOT EXISTS intelligent_cause TEXT,
                ADD COLUMN IF NOT EXISTS severity VARCHAR DEFAULT 'warning',
                ADD COLUMN IF NOT EXISTS analysis_data JSON,
                ADD COLUMN IF NOT EXISTS recommendations JSON,
                ADD COLUMN IF NOT EXISTS minutes_lost INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS money_lost INTEGER DEFAULT 0
            """))

            conn.commit()
            print("✓ Intelligence columns added to incidents table successfully!")
        else:
            print("✓ Intelligence columns already exist in incidents table")


def downgrade():
    """Remove intelligence columns from incidents table."""
    with engine.connect() as conn:
        print("Removing intelligence columns from incidents table...")

        conn.execute(text("""
            ALTER TABLE incidents
            DROP COLUMN IF EXISTS intelligent_cause,
            DROP COLUMN IF EXISTS severity,
            DROP COLUMN IF EXISTS analysis_data,
            DROP COLUMN IF EXISTS recommendations,
            DROP COLUMN IF EXISTS minutes_lost,
            DROP COLUMN IF EXISTS money_lost
        """))

        conn.commit()
        print("✓ Intelligence columns removed from incidents table")


if __name__ == "__main__":
    print("Running migration: add_incidents_intelligence")
    upgrade()
    print("Migration complete!")
