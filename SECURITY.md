# Security

## RLS
- RLS enabled on all public tables.
- Policies enforce ownership using `auth.uid()` mapped to `public.users.auth_user_id`.
- Public read only for status pages and status page monitors.

## Admin access
- Admin role managed via `roles` + `user_roles`.
- `public.is_admin()` helper used for privileged policies.

## Service role
- `SUPABASE_SERVICE_ROLE_KEY` is server-only.
- Never expose service role in client code.

## Storage
- Public buckets: `avatars`, `status-page-assets` (read public, write own).
- Private bucket: `private-exports` (owner only).
