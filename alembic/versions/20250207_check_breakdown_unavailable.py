"""Add breakdown availability flag to checks

Revision ID: 20250207_check_breakdown_unavailable
Revises: 20250112_check_timing_columns
Create Date: 2025-02-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250207_check_breakdown_unavailable"
down_revision = "20250112_check_timing_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("checks", sa.Column("breakdown_unavailable", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("checks", "breakdown_unavailable")
