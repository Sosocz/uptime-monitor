"""Add enriched fields to incidents table and create notification_logs table"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add new columns to incidents table and create notification_logs table."""
    with engine.connect() as conn:
        # Check if incidents enrichment columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='incidents' AND column_name='duration_seconds'
        """))

        if not result.fetchone():
            print("Adding enrichment columns to incidents table...")

            conn.execute(text("""
                ALTER TABLE incidents
                ADD COLUMN duration_seconds INTEGER,
                ADD COLUMN failed_checks_count INTEGER DEFAULT 0,
                ADD COLUMN status_code INTEGER,
                ADD COLUMN error_message TEXT,
                ADD COLUMN cause VARCHAR,
                ADD COLUMN notification_sent_at TIMESTAMP
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_incidents_monitor_id ON incidents(monitor_id);
                CREATE INDEX IF NOT EXISTS idx_incidents_started_at ON incidents(started_at);
            """))

            conn.commit()
            print("Incidents enrichment completed!")
        else:
            print("Incidents enrichment columns already exist, skipping.")

        # Check if notification_logs table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='notification_logs'
        """))

        if not result.fetchone():
            print("Creating notification_logs table...")

            conn.execute(text("""
                CREATE TABLE notification_logs (
                    id SERIAL PRIMARY KEY,
                    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    monitor_id INTEGER NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
                    channel VARCHAR NOT NULL,
                    recipient VARCHAR NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    last_attempt_at TIMESTAMP,
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX idx_notification_logs_incident_id ON notification_logs(incident_id);
                CREATE INDEX idx_notification_logs_user_id ON notification_logs(user_id);
                CREATE INDEX idx_notification_logs_monitor_id ON notification_logs(monitor_id);
                CREATE INDEX idx_notification_logs_created_at ON notification_logs(created_at);
                CREATE INDEX idx_notification_dedup ON notification_logs(incident_id, user_id, channel, created_at);
                CREATE INDEX idx_notification_status ON notification_logs(status, created_at);
            """))

            conn.commit()
            print("notification_logs table created successfully!")
        else:
            print("notification_logs table already exists, skipping.")


if __name__ == "__main__":
    upgrade()
