"""Add timing breakdown to checks

Revision ID: 20250112_check_timing_columns
Revises: 20250111_user_settings
Create Date: 2025-01-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250112_check_timing_columns"
down_revision = "20250111_user_settings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("checks", sa.Column("name_lookup_ms", sa.Float(), nullable=True))
    op.add_column("checks", sa.Column("connection_ms", sa.Float(), nullable=True))
    op.add_column("checks", sa.Column("tls_ms", sa.Float(), nullable=True))
    op.add_column("checks", sa.Column("transfer_ms", sa.Float(), nullable=True))
    op.add_column("checks", sa.Column("total_ms", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("checks", "total_ms")
    op.drop_column("checks", "transfer_ms")
    op.drop_column("checks", "tls_ms")
    op.drop_column("checks", "connection_ms")
    op.drop_column("checks", "name_lookup_ms")
