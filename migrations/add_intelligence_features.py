"""
Migration: Add intelligence features to monitors and incidents

Adds:
- Health score and grade to monitors
- Tags and revenue tracking to monitors
- Flapping and degradation detection flags
- Site DNA (pattern analysis)
- Intelligent incident analysis
- Time and money lost tracking
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import engine


def run_migration():
    """Add intelligence features to monitors and incidents."""
    with engine.connect() as conn:
        print("Adding intelligence features to monitors table...")

        # Add new columns to monitors
        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN health_score INTEGER DEFAULT 100"))
            print("  ✓ Added health_score")
        except Exception as e:
            print(f"  - health_score already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN health_grade VARCHAR DEFAULT 'A+'"))
            print("  ✓ Added health_grade")
        except Exception as e:
            print(f"  - health_grade already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN tags TEXT"))
            print("  ✓ Added tags")
        except Exception as e:
            print(f"  - tags already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN estimated_revenue_per_hour FLOAT DEFAULT 0"))
            print("  ✓ Added estimated_revenue_per_hour")
        except Exception as e:
            print(f"  - estimated_revenue_per_hour already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN is_flapping BOOLEAN DEFAULT FALSE"))
            print("  ✓ Added is_flapping")
        except Exception as e:
            print(f"  - is_flapping already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN is_degrading BOOLEAN DEFAULT FALSE"))
            print("  ✓ Added is_degrading")
        except Exception as e:
            print(f"  - is_degrading already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE monitors ADD COLUMN site_dna JSON"))
            print("  ✓ Added site_dna")
        except Exception as e:
            print(f"  - site_dna already exists or error: {e}")

        print("\nAdding intelligence features to incidents table...")

        # Add new columns to incidents
        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN intelligent_cause TEXT"))
            print("  ✓ Added intelligent_cause")
        except Exception as e:
            print(f"  - intelligent_cause already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN severity VARCHAR DEFAULT 'warning'"))
            print("  ✓ Added severity")
        except Exception as e:
            print(f"  - severity already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN analysis_data JSON"))
            print("  ✓ Added analysis_data")
        except Exception as e:
            print(f"  - analysis_data already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN recommendations JSON"))
            print("  ✓ Added recommendations")
        except Exception as e:
            print(f"  - recommendations already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN minutes_lost INTEGER DEFAULT 0"))
            print("  ✓ Added minutes_lost")
        except Exception as e:
            print(f"  - minutes_lost already exists or error: {e}")

        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN money_lost INTEGER DEFAULT 0"))
            print("  ✓ Added money_lost")
        except Exception as e:
            print(f"  - money_lost already exists or error: {e}")

        conn.commit()
        print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
