"""Add breakdown availability flag to checks

Revision ID: 20250207_breakdown_unavail
Revises: 20250112_check_timing_columns
Create Date: 2025-02-07
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250207_breakdown_unavail"
down_revision = "20250112_check_timing_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE checks ADD COLUMN IF NOT EXISTS breakdown_unavailable BOOLEAN")


def downgrade():
    op.execute("ALTER TABLE checks DROP COLUMN IF EXISTS breakdown_unavailable")
