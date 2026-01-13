begin;

create or replace function public.current_user_id()
returns bigint
language sql
stable
as $$
  select id from public.users where auth_user_id = auth.uid();
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.user_roles ur
    join public.roles r on r.id = ur.role_id
    where ur.user_id = public.current_user_id()
      and r.name = 'admin'
  );
$$;

-- Policies
create policy "Users select own profile" on public.users for select
  using (auth.uid() = auth_user_id);
create policy "Users update own profile" on public.users for update
  using (auth.uid() = auth_user_id)
  with check (auth.uid() = auth_user_id);

create policy "Roles view own" on public.user_roles for select
  using (user_id = public.current_user_id());
create policy "Roles manage admin" on public.user_roles for all
  using (public.is_admin())
  with check (public.is_admin());
create policy "Roles read admin" on public.roles for select using (public.is_admin());

create policy "Monitors owner access" on public.monitors for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Checks owner access" on public.checks for all
  using (monitor_id in (select id from public.monitors where user_id = public.current_user_id()))
  with check (monitor_id in (select id from public.monitors where user_id = public.current_user_id()));

create policy "Escalation rules owner access" on public.escalation_rules for all
  using (monitor_id in (select id from public.monitors where user_id = public.current_user_id()))
  with check (monitor_id in (select id from public.monitors where user_id = public.current_user_id()));

create policy "Incidents owner access" on public.incidents for all
  using (monitor_id in (select id from public.monitors where user_id = public.current_user_id()))
  with check (monitor_id in (select id from public.monitors where user_id = public.current_user_id()));

create policy "Incident roles owner access" on public.incident_roles for all
  using (incident_id in (select id from public.incidents where monitor_id in (select id from public.monitors where user_id = public.current_user_id())))
  with check (incident_id in (select id from public.incidents where monitor_id in (select id from public.monitors where user_id = public.current_user_id())));

create policy "Notification logs owner access" on public.notification_logs for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Status pages owner access" on public.status_pages for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Status pages public read" on public.status_pages for select
  using (is_public = true);

create policy "Status page monitors owner access" on public.status_page_monitors for all
  using (status_page_id in (select id from public.status_pages where user_id = public.current_user_id()))
  with check (status_page_id in (select id from public.status_pages where user_id = public.current_user_id()));

create policy "Status page monitors public read" on public.status_page_monitors for select
  using (status_page_id in (select id from public.status_pages where is_public = true));

create policy "Status page subscribers owner read" on public.status_page_subscribers for select
  using (status_page_id in (select id from public.status_pages where user_id = public.current_user_id()));

create policy "Status page subscribers owner manage" on public.status_page_subscribers for update
  using (status_page_id in (select id from public.status_pages where user_id = public.current_user_id()))
  with check (status_page_id in (select id from public.status_pages where user_id = public.current_user_id()));

create policy "Status page subscribers public insert" on public.status_page_subscribers for insert
  with check (status_page_id in (select id from public.status_pages where is_public = true));

create policy "Subscriptions owner access" on public.subscriptions for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Usage records owner access" on public.usage_records for all
  using (subscription_id in (select id from public.subscriptions where user_id = public.current_user_id()))
  with check (subscription_id in (select id from public.subscriptions where user_id = public.current_user_id()));

create policy "Oncall schedules owner access" on public.oncall_schedules for all
  using (team_id = public.current_user_id())
  with check (team_id = public.current_user_id());

create policy "Oncall shifts owner access" on public.oncall_shifts for all
  using (schedule_id in (select id from public.oncall_schedules where team_id = public.current_user_id()))
  with check (schedule_id in (select id from public.oncall_schedules where team_id = public.current_user_id()));

create policy "Cover requests owner access" on public.cover_requests for all
  using (requester_id = public.current_user_id())
  with check (requester_id = public.current_user_id());

create policy "Services owner access" on public.services for all
  using (team_id = public.current_user_id())
  with check (team_id = public.current_user_id());

create policy "Webhooks owner access" on public.webhooks for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Webhook logs owner access" on public.webhook_logs for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Error projects owner access" on public.error_projects for all
  using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

create policy "Error groups owner access" on public.error_groups for all
  using (project_id in (select id from public.error_projects where user_id = public.current_user_id()))
  with check (project_id in (select id from public.error_projects where user_id = public.current_user_id()));

create policy "Error events owner access" on public.error_events for all
  using (project_id in (select id from public.error_projects where user_id = public.current_user_id()))
  with check (project_id in (select id from public.error_projects where user_id = public.current_user_id()));

commit;
