"""Add user settings fields

Revision ID: 20250111_user_settings
Revises: 914926815b9c
Create Date: 2025-01-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250111_user_settings"
down_revision = "914926815b9c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(), nullable=True, server_default="UTC"))
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))
    op.add_column("users", sa.Column("alerts_enabled", sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column("users", sa.Column("alerts_paused_from", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("alerts_paused_until", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "alerts_paused_until")
    op.drop_column("users", "alerts_paused_from")
    op.drop_column("users", "alerts_enabled")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "timezone")
    op.drop_column("users", "phone")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
