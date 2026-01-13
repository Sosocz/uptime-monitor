begin;

create extension if not exists "pgcrypto";

-- Enums
create type incident_status as enum ('OPEN', 'ACKNOWLEDGED', 'RESOLVED');
create type incident_severity as enum ('sev1', 'sev2', 'sev3', 'sev4');
create type incident_role_type as enum ('commander', 'deputy', 'lead', 'responder');
create type rotation_type as enum ('daily', 'weekly', 'custom');
create type cover_request_status as enum ('pending', 'accepted', 'rejected', 'cancelled');
create type subscription_status as enum ('active', 'past_due', 'canceled', 'trialing');
create type telemetry_bundle as enum ('none', 'nano', 'micro', 'mega', 'tera');
create type telemetry_region as enum ('us_east', 'us_west', 'germany', 'singapore');
create type warehouse_plan_type as enum ('standard', 'turbo', 'ultra', 'hyper');
create type error_level as enum ('debug', 'info', 'warning', 'error', 'fatal');
create type error_group_status as enum ('unresolved', 'ignored', 'resolved');
create type sso_provider as enum ('google', 'azure', 'okta');

-- Helpers
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Core tables
create table public.users (
  id bigserial primary key,
  auth_user_id uuid unique not null,
  email text unique not null,
  plan text default 'FREE',
  stripe_customer_id text,
  stripe_subscription_id text,
  telegram_chat_id text,
  webhook_url text,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  first_name text,
  last_name text,
  phone text,
  timezone text default 'UTC',
  avatar_url text,
  alerts_enabled boolean default true,
  alerts_paused_from timestamptz,
  alerts_paused_until timestamptz,
  oauth_provider text,
  oauth_id text,
  password_reset_token text,
  password_reset_expires_at timestamptz,
  onboarding_completed boolean default false,
  onboarding_email_j1_sent boolean default false,
  onboarding_email_j3_sent boolean default false
);
create index users_email_idx on public.users (email);
create index users_auth_user_id_idx on public.users (auth_user_id);

create table public.roles (
  id bigserial primary key,
  name text unique not null,
  description text
);

create table public.user_roles (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  role_id bigint not null references public.roles(id) on delete cascade,
  assigned_at timestamptz default now(),
  unique (user_id, role_id)
);

create table public.monitors (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  name text not null,
  url text not null,
  interval integer default 600,
  timeout integer default 30,
  is_active boolean default true,
  last_status text,
  last_checked_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  health_score integer default 100,
  health_grade text default 'A+',
  tags text,
  estimated_revenue_per_hour double precision default 0,
  is_flapping boolean default false,
  is_degrading boolean default false,
  site_dna jsonb
);
create index monitors_user_id_idx on public.monitors (user_id);

create table public.checks (
  id bigserial primary key,
  monitor_id bigint not null references public.monitors(id) on delete cascade,
  status text not null,
  status_code integer,
  response_time double precision,
  name_lookup_ms double precision,
  connection_ms double precision,
  tls_ms double precision,
  transfer_ms double precision,
  total_ms double precision,
  breakdown_unavailable boolean,
  error_message text,
  checked_at timestamptz default now(),
  ip_address text,
  server text,
  content_type text,
  ssl_expires_at timestamptz,
  response_headers text
);
create index checks_monitor_id_idx on public.checks (monitor_id);
create index checks_checked_at_idx on public.checks (checked_at);

create table public.escalation_rules (
  id bigserial primary key,
  monitor_id bigint not null references public.monitors(id) on delete cascade,
  threshold_minutes integer default 10,
  escalation_channels text default 'telegram',
  is_active boolean default true,
  escalated boolean default false
);
create index escalation_rules_monitor_id_idx on public.escalation_rules (monitor_id);

create table public.incidents (
  id bigserial primary key,
  monitor_id bigint not null references public.monitors(id) on delete cascade,
  incident_type text not null,
  started_at timestamptz default now(),
  resolved_at timestamptz,
  status incident_status default 'OPEN',
  acknowledged_at timestamptz,
  acknowledged_by_id bigint references public.users(id),
  severity incident_severity default 'sev3',
  title text,
  duration_seconds integer,
  failed_checks_count integer default 0,
  status_code integer,
  error_message text,
  cause text,
  intelligent_cause text,
  analysis_data jsonb,
  recommendations jsonb,
  minutes_lost integer default 0,
  money_lost integer default 0,
  time_to_acknowledge integer,
  time_to_resolve integer,
  root_cause_analysis jsonb,
  ai_postmortem text,
  ai_postmortem_generated_at timestamptz,
  slack_channel_id text,
  slack_thread_ts text,
  slack_message_ts text,
  teams_channel_id text,
  teams_message_id text,
  timeline_events jsonb,
  escalation_level integer default 0,
  escalation_policy_id bigint references public.escalation_rules(id),
  responder_id bigint references public.users(id),
  notified boolean default false,
  notification_sent_at timestamptz
);
create index incidents_monitor_id_idx on public.incidents (monitor_id);
create index incidents_status_idx on public.incidents (status);

create table public.incident_roles (
  id bigserial primary key,
  incident_id bigint not null references public.incidents(id) on delete cascade,
  user_id bigint not null references public.users(id),
  role_type incident_role_type not null,
  assigned_at timestamptz default now(),
  assigned_by_id bigint references public.users(id)
);
create index incident_roles_incident_id_idx on public.incident_roles (incident_id);

create table public.notification_logs (
  id bigserial primary key,
  incident_id bigint not null references public.incidents(id) on delete cascade,
  user_id bigint not null references public.users(id) on delete cascade,
  monitor_id bigint not null references public.monitors(id) on delete cascade,
  channel text not null,
  recipient text not null,
  status text not null default 'pending',
  attempts integer default 0,
  last_attempt_at timestamptz,
  sent_at timestamptz,
  error_message text,
  retry_count integer default 0,
  created_at timestamptz default now()
);
create index notification_logs_created_at_idx on public.notification_logs (created_at);
create index notification_logs_status_idx on public.notification_logs (status, created_at);
create index notification_logs_dedup_idx on public.notification_logs (incident_id, user_id, channel, created_at);

create table public.status_pages (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  slug text not null unique,
  subdomain text unique,
  name text not null,
  logo_url text,
  custom_domain text,
  custom_css text,
  custom_js text,
  has_custom_styling boolean default false,
  is_white_label boolean default false,
  footer_text text,
  is_public boolean default true,
  is_password_protected boolean default false,
  password_hash text,
  access_token text,
  is_ip_restricted boolean default false,
  ip_whitelist jsonb,
  sso_enabled boolean default false,
  sso_provider sso_provider,
  sso_client_id text,
  sso_client_secret text,
  sso_tenant_id text,
  header_text text,
  brand_color text default '#3b82f6',
  custom_email_domain text,
  custom_email_enabled boolean default false,
  google_analytics_id text,
  mixpanel_token text,
  intercom_app_id text,
  languages jsonb,
  default_language text default 'en',
  subscriber_quota integer default 1000,
  subscriber_count integer default 0,
  show_uptime_percentage boolean default true,
  show_response_time boolean default true,
  show_incident_history boolean default true,
  show_powered_by boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index status_pages_user_id_idx on public.status_pages (user_id);

create table public.status_page_monitors (
  id bigserial primary key,
  status_page_id bigint not null references public.status_pages(id) on delete cascade,
  monitor_id bigint not null references public.monitors(id) on delete cascade,
  position integer default 0
);
create index status_page_monitors_page_idx on public.status_page_monitors (status_page_id);

create table public.status_page_subscribers (
  id bigserial primary key,
  status_page_id bigint not null references public.status_pages(id) on delete cascade,
  email text,
  phone text,
  notify_incidents boolean default true,
  notify_maintenance boolean default true,
  notify_resolved boolean default true,
  is_verified boolean default false,
  verification_token text,
  verified_at timestamptz,
  language text default 'en',
  subscribed_at timestamptz default now(),
  last_notification_at timestamptz,
  is_active boolean default true,
  unsubscribed_at timestamptz,
  unsubscribe_token text unique not null
);
create index status_page_subscribers_page_idx on public.status_page_subscribers (status_page_id);
create index status_page_subscribers_email_idx on public.status_page_subscribers (email);

create table public.subscriptions (
  id bigserial primary key,
  user_id bigint not null unique references public.users(id) on delete cascade,
  stripe_subscription_id text,
  status subscription_status default 'active',
  responder_count integer default 1,
  monitor_packs integer default 0,
  status_page_count integer default 1,
  status_page_custom_css_count integer default 0,
  status_page_whitelabel_count integer default 0,
  status_page_password_count integer default 0,
  status_page_ip_restrict_count integer default 0,
  status_page_sso_count integer default 0,
  status_page_custom_email_count integer default 0,
  status_page_subscriber_packs integer default 0,
  telemetry_bundle telemetry_bundle default 'none',
  telemetry_region telemetry_region default 'germany',
  logs_gb_this_month double precision default 0,
  traces_gb_this_month double precision default 0,
  metrics_1b_this_month double precision default 0,
  error_events_this_month integer default 0,
  phone_number_count integer default 0,
  warehouse_plan warehouse_plan_type default 'standard',
  warehouse_object_storage_gb double precision default 0,
  warehouse_nvme_storage_gb double precision default 0,
  warehouse_custom_bucket boolean default false,
  current_period_start timestamptz,
  current_period_end timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table public.usage_records (
  id bigserial primary key,
  subscription_id bigint not null references public.subscriptions(id) on delete cascade,
  period_start timestamptz not null,
  period_end timestamptz not null,
  logs_ingested_gb double precision default 0,
  traces_ingested_gb double precision default 0,
  metrics_ingested_1b double precision default 0,
  error_events integer default 0,
  call_minutes integer default 0,
  warehouse_queries integer default 0,
  uptime_cost double precision default 0,
  status_pages_cost double precision default 0,
  telemetry_cost double precision default 0,
  errors_cost double precision default 0,
  call_routing_cost double precision default 0,
  warehouse_cost double precision default 0,
  total_cost double precision default 0,
  created_at timestamptz default now()
);
create index usage_records_subscription_idx on public.usage_records (subscription_id);

create table public.oncall_schedules (
  id bigserial primary key,
  name text not null,
  description text,
  team_id bigint not null references public.users(id) on delete cascade,
  timezone text default 'UTC' not null,
  rotation_type rotation_type default 'weekly',
  rotation_start timestamptz not null,
  rotation_interval_hours integer default 168,
  rotation_user_ids jsonb not null,
  google_calendar_id text,
  outlook_calendar_id text,
  sync_enabled boolean default false,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index oncall_schedules_team_idx on public.oncall_schedules (team_id);

create table public.oncall_shifts (
  id bigserial primary key,
  schedule_id bigint not null references public.oncall_schedules(id) on delete cascade,
  user_id bigint not null references public.users(id) on delete cascade,
  start_time timestamptz not null,
  end_time timestamptz not null,
  is_override boolean default false,
  overridden_shift_id bigint references public.oncall_shifts(id),
  override_reason text,
  overridden_by_id bigint references public.users(id),
  is_active boolean default true,
  created_at timestamptz default now()
);
create index oncall_shifts_schedule_idx on public.oncall_shifts (schedule_id);
create index oncall_shifts_user_idx on public.oncall_shifts (user_id);

create table public.cover_requests (
  id bigserial primary key,
  requester_id bigint not null references public.users(id) on delete cascade,
  shift_id bigint not null references public.oncall_shifts(id) on delete cascade,
  reason text,
  potential_covers jsonb,
  status cover_request_status default 'pending',
  accepted_by_id bigint references public.users(id),
  response_message text,
  created_at timestamptz default now(),
  responded_at timestamptz
);
create index cover_requests_requester_idx on public.cover_requests (requester_id);

create table public.services (
  id bigserial primary key,
  name text not null,
  description text,
  team_id bigint not null references public.users(id) on delete cascade,
  escalation_policy_id bigint references public.escalation_rules(id),
  runbook_url text,
  documentation_url text,
  service_metadata jsonb,
  tags jsonb,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table public.webhooks (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  name text not null,
  url text not null,
  is_active boolean default true,
  events jsonb,
  monitor_ids jsonb,
  auth_type text,
  auth_header text,
  auth_value text,
  custom_headers jsonb,
  max_retries integer default 3,
  retry_delay_seconds integer default 60,
  created_at timestamptz default now(),
  last_triggered_at timestamptz,
  last_success_at timestamptz,
  last_failure_at timestamptz,
  failure_count integer default 0
);

create table public.webhook_logs (
  id bigserial primary key,
  webhook_id bigint not null references public.webhooks(id) on delete cascade,
  user_id bigint not null references public.users(id) on delete cascade,
  event_type text not null,
  payload jsonb not null,
  status_code integer,
  response_body text,
  response_time_ms integer,
  status text not null,
  error_message text,
  attempts integer default 0,
  created_at timestamptz default now(),
  sent_at timestamptz
);

create table public.error_projects (
  id bigserial primary key,
  name text not null,
  user_id bigint not null references public.users(id) on delete cascade,
  dsn text not null unique,
  platform text,
  public_key text not null unique,
  secret_key text not null,
  project_key text not null unique,
  events_this_month integer default 0,
  events_quota integer default 100000,
  sample_rate double precision default 1.0,
  filter_localhost boolean default true,
  linear_api_key text,
  jira_url text,
  jira_api_token text,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table public.error_groups (
  id bigserial primary key,
  project_id bigint not null references public.error_projects(id) on delete cascade,
  fingerprint text not null,
  title text not null,
  exception_type text,
  exception_value text,
  first_seen timestamptz default now(),
  last_seen timestamptz default now(),
  event_count integer default 0,
  user_count integer default 0,
  status error_group_status default 'unresolved',
  assigned_to_id bigint references public.users(id),
  snoozed_until timestamptz,
  bugfix_prompt text,
  linear_issue_id text,
  jira_issue_key text,
  resolved_in_release text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (project_id, fingerprint)
);

create table public.error_events (
  id bigserial primary key,
  project_id bigint not null references public.error_projects(id) on delete cascade,
  error_group_id bigint not null references public.error_groups(id) on delete cascade,
  event_id text not null unique,
  fingerprint text not null,
  timestamp timestamptz default now(),
  level error_level default 'error',
  message text,
  exception_type text,
  exception_value text,
  stacktrace jsonb,
  user_id_context text,
  user_email text,
  user_username text,
  release text,
  environment text,
  server_name text,
  request_url text,
  request_method text,
  request_headers jsonb,
  platform text,
  sdk_name text,
  sdk_version text,
  tags jsonb,
  extra jsonb,
  breadcrumbs jsonb,
  bugfix_prompt_generated boolean default false,
  created_at timestamptz default now()
);
create index error_events_project_ts_idx on public.error_events (project_id, timestamp);
create index error_events_group_ts_idx on public.error_events (error_group_id, timestamp);

-- Triggers for updated_at
create trigger users_set_updated_at before update on public.users
for each row execute function public.set_updated_at();

create trigger monitors_set_updated_at before update on public.monitors
for each row execute function public.set_updated_at();

create trigger status_pages_set_updated_at before update on public.status_pages
for each row execute function public.set_updated_at();

create trigger subscriptions_set_updated_at before update on public.subscriptions
for each row execute function public.set_updated_at();

create trigger oncall_schedules_set_updated_at before update on public.oncall_schedules
for each row execute function public.set_updated_at();

create trigger services_set_updated_at before update on public.services
for each row execute function public.set_updated_at();

create trigger error_projects_set_updated_at before update on public.error_projects
for each row execute function public.set_updated_at();

create trigger error_groups_set_updated_at before update on public.error_groups
for each row execute function public.set_updated_at();

-- Supabase auth hook
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (auth_user_id, email, plan, created_at, updated_at)
  values (new.id, new.email, 'FREE', now(), now())
  on conflict (auth_user_id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

commit;
