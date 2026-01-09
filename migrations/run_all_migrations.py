"""Run all pending migrations in order"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all migration modules
from migrations import (
    add_check_metadata,
    add_incidents_enrichment_and_notification_logs,
    add_escalation_rules,
    add_status_pages,
    add_onboarding_fields,
    add_show_powered_by_field,
    add_onboarding_indexes,
    add_tracking_events
)

from sqlalchemy import text
from app.core.database import engine


def add_webhook_url_to_users():
    """Add webhook_url column to users table."""
    with engine.connect() as conn:
        # Check if webhook_url column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='webhook_url'
        """))

        if not result.fetchone():
            print("Adding webhook_url column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN webhook_url VARCHAR"))
            conn.commit()
            print("webhook_url column added successfully!")
        else:
            print("webhook_url column already exists, skipping.")


def main():
    """Run all migrations."""
    print("=== Running all migrations ===\n")

    print("1. Adding check metadata...")
    add_check_metadata.upgrade()

    print("\n2. Adding incidents enrichment and notification_logs...")
    add_incidents_enrichment_and_notification_logs.upgrade()

    print("\n3. Adding escalation_rules...")
    add_escalation_rules.upgrade()

    print("\n4. Adding status_pages...")
    add_status_pages.upgrade()

    print("\n5. Adding webhook_url to users...")
    add_webhook_url_to_users()

    print("\n6. Adding onboarding fields to users...")
    add_onboarding_fields.run_migration()

    print("\n7. Adding show_powered_by field to status_pages...")
    add_show_powered_by_field.run_migration()

    print("\n8. Adding onboarding indexes...")
    add_onboarding_indexes.run_migration()

    print("\n9. Adding tracking_events table...")
    add_tracking_events.run_migration()

    print("\n=== All migrations completed! ===")


if __name__ == "__main__":
    main()
