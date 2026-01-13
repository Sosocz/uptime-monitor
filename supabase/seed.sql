insert into public.roles (name, description) values
  ('admin', 'Full access admin'),
  ('staff', 'Internal staff role'),
  ('user', 'Default user role')
on conflict (name) do nothing;
