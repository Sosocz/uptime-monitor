"""Add Better Stack models

Revision ID: 914926815b9c
Revises:
Create Date: 2026-01-10 14:08:00

This migration adds Better Stack models: services, oncall, subscriptions, errors, status_page_subscribers
and extends existing incidents, monitors, and status_pages models.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '914926815b9c'
down_revision = None
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
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['escalation_policy_id'], ['escalation_rules.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
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
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
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
        sa.Column('rotation_user_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('google_calendar_id', sa.String(), nullable=True),
        sa.Column('outlook_calendar_id', sa.String(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oncall_schedules_id'), 'oncall_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_oncall_schedules_team_id'), 'oncall_schedules', ['team_id'], unique=False)

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
        sa.ForeignKeyConstraint(['overridden_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['overridden_shift_id'], ['oncall_shifts.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['oncall_schedules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oncall_shifts_id'), 'oncall_shifts', ['id'], unique=False)
    op.create_index(op.f('ix_oncall_shifts_schedule_id'), 'oncall_shifts', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_oncall_shifts_start_time'), 'oncall_shifts', ['start_time'], unique=False)
    op.create_index(op.f('ix_oncall_shifts_end_time'), 'oncall_shifts', ['end_time'], unique=False)
    op.create_index(op.f('ix_oncall_shifts_user_id'), 'oncall_shifts', ['user_id'], unique=False)

    # === COVER REQUESTS ===
    op.create_table('cover_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('potential_covers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED', name='coverrequeststatus'), nullable=True),
        sa.Column('accepted_by_id', sa.Integer(), nullable=True),
        sa.Column('response_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['accepted_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shift_id'], ['oncall_shifts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cover_requests_id'), 'cover_requests', ['id'], unique=False)
    op.create_index(op.f('ix_cover_requests_requester_id'), 'cover_requests', ['requester_id'], unique=False)
    op.create_index(op.f('ix_cover_requests_shift_id'), 'cover_requests', ['shift_id'], unique=False)

    # === SUBSCRIPTIONS ===
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAST_DUE', 'CANCELED', 'INCOMPLETE', 'TRIALING', name='subscriptionstatus'), nullable=True),
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
        sa.Column('warehouse_plan', sa.Enum('NONE', 'STANDARD', 'TURBO', 'ULTRA', 'HYPER', name='warehouseplan'), nullable=True),
        sa.Column('warehouse_object_storage_gb', sa.Float(), nullable=True),
        sa.Column('warehouse_nvme_storage_gb', sa.Float(), nullable=True),
        sa.Column('warehouse_custom_bucket', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_team_id'), 'subscriptions', ['team_id'], unique=False)

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
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_records_id'), 'usage_records', ['id'], unique=False)
    op.create_index(op.f('ix_usage_records_subscription_id'), 'usage_records', ['subscription_id'], unique=False)

    # === ERROR PROJECTS ===
    op.create_table('error_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('dsn', sa.String(), nullable=False),
        sa.Column('platform', sa.Enum('PYTHON', 'JAVASCRIPT', 'JAVA', 'GO', 'PHP', 'RUBY', 'CSHARP', 'RUST', name='errorplatform'), nullable=False),
        sa.Column('events_this_month', sa.Integer(), nullable=True),
        sa.Column('events_quota', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('linear_integration_enabled', sa.Boolean(), nullable=True),
        sa.Column('linear_api_key', sa.String(), nullable=True),
        sa.Column('jira_integration_enabled', sa.Boolean(), nullable=True),
        sa.Column('jira_api_key', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_projects_dsn'), 'error_projects', ['dsn'], unique=True)
    op.create_index(op.f('ix_error_projects_id'), 'error_projects', ['id'], unique=False)
    op.create_index(op.f('ix_error_projects_team_id'), 'error_projects', ['team_id'], unique=False)

    # === ERROR GROUPS ===
    op.create_table('error_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('event_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('UNRESOLVED', 'IGNORED', 'RESOLVED', name='errorgroupstatus'), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(), nullable=True),
        sa.Column('bugfix_prompt', sa.Text(), nullable=True),
        sa.Column('linear_issue_id', sa.String(), nullable=True),
        sa.Column('jira_issue_key', sa.String(), nullable=True),
        sa.Column('release', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['error_projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_groups_fingerprint'), 'error_groups', ['fingerprint'], unique=False)
    op.create_index(op.f('ix_error_groups_id'), 'error_groups', ['id'], unique=False)
    op.create_index(op.f('ix_error_groups_project_id'), 'error_groups', ['project_id'], unique=False)

    # === ERROR EVENTS ===
    op.create_table('error_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', name='errorlevel'), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('exception_type', sa.String(), nullable=True),
        sa.Column('exception_value', sa.String(), nullable=True),
        sa.Column('stacktrace', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('breadcrumbs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id_str', sa.String(), nullable=True),
        sa.Column('user_email', sa.String(), nullable=True),
        sa.Column('release', sa.String(), nullable=True),
        sa.Column('environment', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contexts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['error_groups.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['error_projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_events_fingerprint'), 'error_events', ['fingerprint'], unique=False)
    op.create_index(op.f('ix_error_events_group_id'), 'error_events', ['group_id'], unique=False)
    op.create_index(op.f('ix_error_events_id'), 'error_events', ['id'], unique=False)
    op.create_index(op.f('ix_error_events_project_id'), 'error_events', ['project_id'], unique=False)
    op.create_index(op.f('ix_error_events_timestamp'), 'error_events', ['timestamp'], unique=False)

    # === STATUS PAGE SUBSCRIBERS ===
    op.create_table('status_page_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status_page_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('notify_incidents', sa.Boolean(), nullable=True),
        sa.Column('notify_maintenance', sa.Boolean(), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_token', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['status_page_id'], ['status_pages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_status_page_subscribers_email'), 'status_page_subscribers', ['email'], unique=False)
    op.create_index(op.f('ix_status_page_subscribers_id'), 'status_page_subscribers', ['id'], unique=False)
    op.create_index(op.f('ix_status_page_subscribers_status_page_id'), 'status_page_subscribers', ['status_page_id'], unique=False)

    # === EXTEND INCIDENTS ===
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('OPEN', 'ACKNOWLEDGED', 'RESOLVED', name='incidentstatus'), nullable=True))
        batch_op.add_column(sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('acknowledged_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('title', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('time_to_acknowledge', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('time_to_resolve', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('root_cause_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('ai_postmortem', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_postmortem_generated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('slack_channel_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('slack_thread_ts', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('slack_message_ts', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('teams_channel_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('teams_message_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('timeline_events', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('escalation_level', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('escalation_policy_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('responder_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_incidents_service_id'), ['service_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_incidents_status'), ['status'], unique=False)
        batch_op.create_foreign_key('fk_incidents_service_id', 'services', ['service_id'], ['id'])
        batch_op.create_foreign_key('fk_incidents_acknowledged_by_id', 'users', ['acknowledged_by_id'], ['id'])
        batch_op.create_foreign_key('fk_incidents_responder_id', 'users', ['responder_id'], ['id'])

    # === EXTEND MONITORS ===
    with op.batch_alter_table('monitors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_monitors_service_id', 'services', ['service_id'], ['id'])

    # === EXTEND STATUS PAGES ===
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
        batch_op.add_column(sa.Column('ip_whitelist', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
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
        batch_op.add_column(sa.Column('languages', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('default_language', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('subscriber_quota', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subscriber_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_status_pages_subdomain'), ['subdomain'], unique=True)


def downgrade() -> None:
    # Drop extended status pages columns
    with op.batch_alter_table('status_pages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_status_pages_subdomain'))
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('subscriber_count')
        batch_op.drop_column('subscriber_quota')
        batch_op.drop_column('default_language')
        batch_op.drop_column('languages')
        batch_op.drop_column('intercom_app_id')
        batch_op.drop_column('mixpanel_token')
        batch_op.drop_column('google_analytics_id')
        batch_op.drop_column('custom_email_enabled')
        batch_op.drop_column('custom_email_domain')
        batch_op.drop_column('sso_tenant_id')
        batch_op.drop_column('sso_client_secret')
        batch_op.drop_column('sso_client_id')
        batch_op.drop_column('sso_provider')
        batch_op.drop_column('sso_enabled')
        batch_op.drop_column('ip_whitelist')
        batch_op.drop_column('is_ip_restricted')
        batch_op.drop_column('password_hash')
        batch_op.drop_column('is_password_protected')
        batch_op.drop_column('footer_text')
        batch_op.drop_column('is_white_label')
        batch_op.drop_column('has_custom_styling')
        batch_op.drop_column('custom_js')
        batch_op.drop_column('custom_css')
        batch_op.drop_column('subdomain')

    # Drop extended monitors columns
    with op.batch_alter_table('monitors', schema=None) as batch_op:
        batch_op.drop_constraint('fk_monitors_service_id', type_='foreignkey')
        batch_op.drop_column('service_id')

    # Drop extended incidents columns
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_incidents_responder_id', type_='foreignkey')
        batch_op.drop_constraint('fk_incidents_acknowledged_by_id', type_='foreignkey')
        batch_op.drop_constraint('fk_incidents_service_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_incidents_status'))
        batch_op.drop_index(batch_op.f('ix_incidents_service_id'))
        batch_op.drop_column('responder_id')
        batch_op.drop_column('escalation_policy_id')
        batch_op.drop_column('escalation_level')
        batch_op.drop_column('timeline_events')
        batch_op.drop_column('teams_message_id')
        batch_op.drop_column('teams_channel_id')
        batch_op.drop_column('slack_message_ts')
        batch_op.drop_column('slack_thread_ts')
        batch_op.drop_column('slack_channel_id')
        batch_op.drop_column('ai_postmortem_generated_at')
        batch_op.drop_column('ai_postmortem')
        batch_op.drop_column('root_cause_analysis')
        batch_op.drop_column('time_to_resolve')
        batch_op.drop_column('time_to_acknowledge')
        batch_op.drop_column('title')
        batch_op.drop_column('service_id')
        batch_op.drop_column('acknowledged_by_id')
        batch_op.drop_column('acknowledged_at')
        batch_op.drop_column('status')

    # Drop new tables
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
