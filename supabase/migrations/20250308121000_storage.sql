begin;

insert into storage.buckets (id, name, public)
values
  ('avatars', 'avatars', true),
  ('status-page-assets', 'status-page-assets', true),
  ('private-exports', 'private-exports', false)
on conflict (id) do nothing;

-- Avatars
create policy "Avatar read public" on storage.objects
  for select
  using (bucket_id = 'avatars');

create policy "Avatar write own" on storage.objects
  for all
  using (bucket_id = 'avatars' and auth.uid() = owner)
  with check (bucket_id = 'avatars' and auth.uid() = owner);

-- Status page assets
create policy "Status assets read public" on storage.objects
  for select
  using (bucket_id = 'status-page-assets');

create policy "Status assets write own" on storage.objects
  for all
  using (bucket_id = 'status-page-assets' and auth.uid() = owner)
  with check (bucket_id = 'status-page-assets' and auth.uid() = owner);

-- Private exports
create policy "Private exports read own" on storage.objects
  for select
  using (bucket_id = 'private-exports' and auth.uid() = owner);

create policy "Private exports write own" on storage.objects
  for all
  using (bucket_id = 'private-exports' and auth.uid() = owner)
  with check (bucket_id = 'private-exports' and auth.uid() = owner);

commit;
