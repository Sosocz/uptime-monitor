create or replace view public.user_monitor_stats as
select
  m.user_id,
  count(*) as total_monitors,
  sum(case when m.last_status = 'up' then 1 else 0 end) as up_monitors,
  sum(case when m.last_status = 'down' then 1 else 0 end) as down_monitors,
  max(m.last_checked_at) as last_checked_at
from public.monitors m
group by m.user_id;
