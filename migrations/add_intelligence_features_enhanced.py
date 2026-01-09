"""
Add intelligence features to monitors table (health score, grades, flags)
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uptime_monitor")
engine = create_engine(DATABASE_URL)


def upgrade():
    """Add intelligence columns to monitors table."""
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='monitors' AND column_name='health_score'
        """))

        if result.fetchone() is None:
            print("Adding intelligence features to monitors table...")

            conn.execute(text("""
                ALTER TABLE monitors
                ADD COLUMN IF NOT EXISTS health_score INTEGER DEFAULT 100,
                ADD COLUMN IF NOT EXISTS health_grade VARCHAR DEFAULT 'A+',
                ADD COLUMN IF NOT EXISTS tags TEXT,
                ADD COLUMN IF NOT EXISTS estimated_revenue_per_hour FLOAT DEFAULT 0,
                ADD COLUMN IF NOT EXISTS is_flapping BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_degrading BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS site_dna JSON
            """))

            conn.commit()
            print("✓ Intelligence features added successfully")
        else:
            print("✓ Intelligence features already exist")


def downgrade():
    """Remove intelligence columns from monitors table."""
    with engine.connect() as conn:
        print("Removing intelligence features from monitors table...")

        conn.execute(text("""
            ALTER TABLE monitors
            DROP COLUMN IF EXISTS health_score,
            DROP COLUMN IF EXISTS health_grade,
            DROP COLUMN IF EXISTS tags,
            DROP COLUMN IF EXISTS estimated_revenue_per_hour,
            DROP COLUMN IF EXISTS is_flapping,
            DROP COLUMN IF EXISTS is_degrading,
            DROP COLUMN IF EXISTS site_dna
        """))

        conn.commit()
        print("✓ Intelligence features removed")


if __name__ == "__main__":
    print("Running migration: add_intelligence_features_enhanced")
    upgrade()
    print("Migration complete!")
