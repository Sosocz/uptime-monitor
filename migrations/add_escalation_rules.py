"""Add escalation_rules table"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Create escalation_rules table."""
    with engine.connect() as conn:
        # Check if escalation_rules table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='escalation_rules'
        """))

        if not result.fetchone():
            print("Creating escalation_rules table...")

            conn.execute(text("""
                CREATE TABLE escalation_rules (
                    id SERIAL PRIMARY KEY,
                    monitor_id INTEGER NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
                    threshold_minutes INTEGER NOT NULL DEFAULT 10,
                    escalation_channels VARCHAR NOT NULL DEFAULT 'telegram',
                    is_active BOOLEAN DEFAULT TRUE,
                    escalated BOOLEAN DEFAULT FALSE
                )
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX idx_escalation_rules_monitor_id ON escalation_rules(monitor_id);
            """))

            conn.commit()
            print("escalation_rules table created successfully!")
        else:
            print("escalation_rules table already exists, skipping.")


if __name__ == "__main__":
    upgrade()
