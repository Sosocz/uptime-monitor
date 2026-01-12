begin;

alter table public.users enable row level security;
alter table public.roles enable row level security;
alter table public.user_roles enable row level security;
alter table public.monitors enable row level security;
alter table public.checks enable row level security;
alter table public.escalation_rules enable row level security;
alter table public.incidents enable row level security;
alter table public.incident_roles enable row level security;
alter table public.notification_logs enable row level security;
alter table public.status_pages enable row level security;
alter table public.status_page_monitors enable row level security;
alter table public.status_page_subscribers enable row level security;
alter table public.subscriptions enable row level security;
alter table public.usage_records enable row level security;
alter table public.oncall_schedules enable row level security;
alter table public.oncall_shifts enable row level security;
alter table public.cover_requests enable row level security;
alter table public.services enable row level security;
alter table public.webhooks enable row level security;
alter table public.webhook_logs enable row level security;
alter table public.error_projects enable row level security;
alter table public.error_groups enable row level security;
alter table public.error_events enable row level security;

commit;
