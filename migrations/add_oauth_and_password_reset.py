"""Add OAuth and password reset support to users table"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add OAuth and password reset columns to users table."""
    with engine.connect() as conn:
        # Check if oauth_provider column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='oauth_provider'
        """))

        if not result.fetchone():
            print("Adding OAuth and password reset columns to users table...")

            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR,
                ADD COLUMN IF NOT EXISTS oauth_id VARCHAR,
                ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR,
                ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP
            """))

            # Make hashed_password nullable for OAuth users
            conn.execute(text("""
                ALTER TABLE users
                ALTER COLUMN hashed_password DROP NOT NULL
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_oauth_provider_id ON users(oauth_provider, oauth_id);
                CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON users(password_reset_token);
            """))

            conn.commit()
            print("✓ OAuth and password reset columns added successfully!")
        else:
            print("✓ OAuth and password reset columns already exist")


def downgrade():
    """Remove OAuth and password reset columns from users table."""
    with engine.connect() as conn:
        print("Removing OAuth and password reset columns from users table...")

        conn.execute(text("""
            DROP INDEX IF EXISTS idx_users_oauth_provider_id;
            DROP INDEX IF EXISTS idx_users_password_reset_token;
        """))

        conn.execute(text("""
            ALTER TABLE users
            DROP COLUMN IF EXISTS oauth_provider,
            DROP COLUMN IF EXISTS oauth_id,
            DROP COLUMN IF EXISTS password_reset_token,
            DROP COLUMN IF EXISTS password_reset_expires_at
        """))

        conn.commit()
        print("✓ OAuth and password reset columns removed")


if __name__ == "__main__":
    print("Running migration: add_oauth_and_password_reset")
    upgrade()
    print("Migration complete!")
