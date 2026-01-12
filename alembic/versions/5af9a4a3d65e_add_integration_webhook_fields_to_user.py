"""add_integration_webhook_fields_to_user

Revision ID: 5af9a4a3d65e
Revises: 20250207_breakdown_unavail
Create Date: 2026-01-12 22:18:00.650647

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5af9a4a3d65e'
down_revision = '20250207_breakdown_unavail'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('slack_webhook_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('discord_webhook_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('teams_webhook_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('pagerduty_integration_key', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'slack_webhook_url')
    op.drop_column('users', 'discord_webhook_url')
    op.drop_column('users', 'teams_webhook_url')
    op.drop_column('users', 'pagerduty_integration_key')
