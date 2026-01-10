"""add betterstack models

Revision ID: betterstack_001
Revises: <previous_revision>
Create Date: 2026-01-10

This migration adds all Better Stack models and extends existing ones.
Run: alembic revision --autogenerate -m "betterstack_models" to generate proper migration.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'betterstack_001'
down_revision = None  # Replace with latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === SERVICES ===
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('escalation_policy_id', sa.Integer(), nullable=True),
        sa.Column('runbook_url', sa.String(), nullable=True),
        sa.Column('documentation_url', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['escalation_policy_id'], ['escalation_rules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_services_id'), 'services', ['id'], unique=False)
    op.create_index(op.f('ix_services_name'), 'services', ['name'], unique=False)
    op.create_index(op.f('ix_services_team_id'), 'services', ['team_id'], unique=False)

    # === INCIDENT ROLES ===
    op.create_table('incident_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_type', sa.Enum('COMMANDER', 'DEPUTY', 'LEAD', 'RESPONDER', name='roletype'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incident_roles_incident_id'), 'incident_roles', ['incident_id'], unique=False)
    op.create_index(op.f('ix_incident_roles_user_id'), 'incident_roles', ['user_id'], unique=False)

    # === ON-CALL SCHEDULES ===
    op.create_table('oncall_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False),
        sa.Column('rotation_type', sa.Enum('DAILY', 'WEEKLY', 'CUSTOM', name='rotationtype'), nullable=True),
        sa.Column('rotation_start', sa.DateTime(), nullable=False),
        sa.Column('rotation_interval_hours', sa.Integer(), nullable=True),
        sa.Column('rotation_user_ids', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('google_calendar_id', sa.String(), nullable=True),
        sa.Column('outlook_calendar_id', sa.String(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # === ON-CALL SHIFTS ===
    op.create_table('oncall_shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_override', sa.Boolean(), nullable=True),
        sa.Column('overridden_shift_id', sa.Integer(), nullable=True),
        sa.Column('override_reason', sa.String(), nullable=True),
        sa.Column('overridden_by_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['oncall_schedules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['overridden_shift_id'], ['oncall_shifts.id'], ),
        sa.ForeignKeyConstraint(['overridden_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oncall_shifts_start_time'), 'oncall_shifts', ['start_time'], unique=False)
    op.create_index(op.f('ix_oncall_shifts_end_time'), 'oncall_shifts', ['end_time'], unique=False)

    # === COVER REQUESTS ===
    op.create_table('cover_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('potential_covers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED', name='coverrequeststatus'), nullable=True),
        sa.Column('accepted_by_id', sa.Integer(), nullable=True),
        sa.Column('response_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shift_id'], ['oncall_shifts.id'], ),
        sa.ForeignKeyConstraint(['accepted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # === SUBSCRIPTIONS ===
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAST_DUE', 'CANCELED', 'TRIALING', name='subscriptionstatus'), nullable=True),
        sa.Column('responder_count', sa.Integer(), nullable=True),
        sa.Column('monitor_packs', sa.Integer(), nullable=True),
        sa.Column('status_page_count', sa.Integer(), nullable=True),
        sa.Column('status_page_custom_css_count', sa.Integer(), nullable=True),
        sa.Column('status_page_whitelabel_count', sa.Integer(), nullable=True),
        sa.Column('status_page_password_count', sa.Integer(), nullable=True),
        sa.Column('status_page_ip_restrict_count', sa.Integer(), nullable=True),
        sa.Column('status_page_sso_count', sa.Integer(), nullable=True),
        sa.Column('status_page_custom_email_count', sa.Integer(), nullable=True),
        sa.Column('status_page_subscriber_packs', sa.Integer(), nullable=True),
        sa.Column('telemetry_bundle', sa.Enum('NONE', 'NANO', 'MICRO', 'MEGA', 'TERA', name='telemetrybundle'), nullable=True),
        sa.Column('telemetry_region', sa.Enum('US_EAST', 'US_WEST', 'GERMANY', 'SINGAPORE', name='telemetryregion'), nullable=True),
        sa.Column('logs_gb_this_month', sa.Float(), nullable=True),
        sa.Column('traces_gb_this_month', sa.Float(), nullable=True),
        sa.Column('metrics_1b_this_month', sa.Float(), nullable=True),
        sa.Column('error_events_this_month', sa.Integer(), nullable=True),
        sa.Column('phone_number_count', sa.Integer(), nullable=True),
        sa.Column('warehouse_plan', sa.Enum('STANDARD', 'TURBO', 'ULTRA', 'HYPER', name='warehouseplantype'), nullable=True),
        sa.Column('warehouse_object_storage_gb', sa.Float(), nullable=True),
        sa.Column('warehouse_nvme_storage_gb', sa.Float(), nullable=True),
        sa.Column('warehouse_custom_bucket', sa.Boolean(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # === USAGE RECORDS ===
    op.create_table('usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('logs_ingested_gb', sa.Float(), nullable=True),
        sa.Column('traces_ingested_gb', sa.Float(), nullable=True),
        sa.Column('metrics_ingested_1b', sa.Float(), nullable=True),
        sa.Column('error_events', sa.Integer(), nullable=True),
        sa.Column('call_minutes', sa.Integer(), nullable=True),
        sa.Column('warehouse_queries', sa.Integer(), nullable=True),
        sa.Column('uptime_cost', sa.Float(), nullable=True),
        sa.Column('status_pages_cost', sa.Float(), nullable=True),
        sa.Column('telemetry_cost', sa.Float(), nullable=True),
        sa.Column('errors_cost', sa.Float(), nullable=True),
        sa.Column('call_routing_cost', sa.Float(), nullable=True),
        sa.Column('warehouse_cost', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_records_period_start'), 'usage_records', ['period_start'], unique=False)

    # === ERROR PROJECTS ===
    op.create_table('error_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('dsn', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('secret_key', sa.String(), nullable=False),
        sa.Column('project_key', sa.String(), nullable=False),
        sa.Column('events_this_month', sa.Integer(), nullable=True),
        sa.Column('events_quota', sa.Integer(), nullable=True),
        sa.Column('sample_rate', sa.Float(), nullable=True),
        sa.Column('filter_localhost', sa.Boolean(), nullable=True),
        sa.Column('linear_api_key', sa.String(), nullable=True),
        sa.Column('jira_url', sa.String(), nullable=True),
        sa.Column('jira_api_token', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dsn'),
        sa.UniqueConstraint('public_key'),
        sa.UniqueConstraint('project_key')
    )

    # === ERROR GROUPS ===
    op.create_table('error_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('exception_type', sa.String(), nullable=True),
        sa.Column('exception_value', sa.Text(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=True),
        sa.Column('user_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('UNRESOLVED', 'IGNORED', 'RESOLVED', name='errorgroupstatus'), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(), nullable=True),
        sa.Column('bugfix_prompt', sa.Text(), nullable=True),
        sa.Column('linear_issue_id', sa.String(), nullable=True),
        sa.Column('jira_issue_key', sa.String(), nullable=True),
        sa.Column('resolved_in_release', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['error_projects.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_fingerprint', 'error_groups', ['project_id', 'fingerprint'], unique=True)

    # === ERROR EVENTS ===
    op.create_table('error_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('error_group_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('level', sa.Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', name='errorlevel'), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('exception_type', sa.String(), nullable=True),
        sa.Column('exception_value', sa.Text(), nullable=True),
        sa.Column('stacktrace', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id_context', sa.String(), nullable=True),
        sa.Column('user_email', sa.String(), nullable=True),
        sa.Column('user_username', sa.String(), nullable=True),
        sa.Column('release', sa.String(), nullable=True),
        sa.Column('environment', sa.String(), nullable=True),
        sa.Column('server_name', sa.String(), nullable=True),
        sa.Column('request_url', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(), nullable=True),
        sa.Column('request_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('sdk_name', sa.String(), nullable=True),
        sa.Column('sdk_version', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('extra', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('breadcrumbs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('bugfix_prompt_generated', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['error_projects.id'], ),
        sa.ForeignKeyConstraint(['error_group_id'], ['error_groups.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index('idx_project_timestamp', 'error_events', ['project_id', 'timestamp'], unique=False)
    op.create_index('idx_group_timestamp', 'error_events', ['error_group_id', 'timestamp'], unique=False)

    # === STATUS PAGE SUBSCRIBERS ===
    op.create_table('status_page_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status_page_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('notify_incidents', sa.Boolean(), nullable=True),
        sa.Column('notify_maintenance', sa.Boolean(), nullable=True),
        sa.Column('notify_resolved', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True),
        sa.Column('last_notification_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_token', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['status_page_id'], ['status_pages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('unsubscribe_token')
    )
    op.create_index(op.f('ix_status_page_subscribers_email'), 'status_page_subscribers', ['email'], unique=False)

    # === EXTEND EXISTING TABLES ===

    # Extend incidents table
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('OPEN', 'ACKNOWLEDGED', 'RESOLVED', name='incidentstatus'), nullable=True))
        batch_op.add_column(sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('acknowledged_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('severity', sa.Enum('SEV1', 'SEV2', 'SEV3', 'SEV4', name='incidentseverity'), nullable=True))
        batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('title', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('time_to_acknowledge', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('time_to_resolve', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('root_cause_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('ai_postmortem', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_postmortem_generated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('slack_channel_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('slack_thread_ts', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('slack_message_ts', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('teams_channel_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('teams_message_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('timeline_events', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('escalation_level', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('responder_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_incident_service', 'services', ['service_id'], ['id'])
        batch_op.create_foreign_key('fk_incident_acknowledged_by', 'users', ['acknowledged_by_id'], ['id'])
        batch_op.create_foreign_key('fk_incident_responder', 'users', ['responder_id'], ['id'])

    # Extend monitors table
    with op.batch_alter_table('monitors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_monitor_service', 'services', ['service_id'], ['id'])
        batch_op.create_index(op.f('ix_monitors_service_id'), ['service_id'], unique=False)

    # Extend status_pages table
    with op.batch_alter_table('status_pages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subdomain', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('custom_css', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('custom_js', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('has_custom_styling', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_white_label', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('footer_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_password_protected', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('is_ip_restricted', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('ip_whitelist', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('sso_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('sso_provider', sa.Enum('GOOGLE', 'AZURE', 'OKTA', name='ssoprovider'), nullable=True))
        batch_op.add_column(sa.Column('sso_client_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('sso_client_secret', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('sso_tenant_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('custom_email_domain', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('custom_email_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('google_analytics_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('mixpanel_token', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('intercom_app_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('languages', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('default_language', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('subscriber_quota', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subscriber_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_index(op.f('ix_status_pages_subdomain'), ['subdomain'], unique=True)


def downgrade() -> None:
    # Reverse all operations (truncated for brevity)
    op.drop_table('status_page_subscribers')
    op.drop_table('error_events')
    op.drop_table('error_groups')
    op.drop_table('error_projects')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
    op.drop_table('cover_requests')
    op.drop_table('oncall_shifts')
    op.drop_table('oncall_schedules')
    op.drop_table('incident_roles')
    op.drop_table('services')

    # Revert column additions (implement as needed)
    pass
