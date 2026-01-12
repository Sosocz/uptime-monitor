# Migration Plan

## Steps
1) Provision Supabase project and set env vars.
2) Apply SQL migrations in `supabase/migrations`.
3) Seed baseline roles with `supabase/seed.sql`.
4) Run data migration script:
   ```bash
   SOURCE_DATABASE_URL=... \
   SUPABASE_DB_URL=... \
   SUPABASE_URL=... \
   SUPABASE_SERVICE_ROLE_KEY=... \
   npx tsx scripts/migrate_to_supabase.ts
   ```
5) Verify counts and integrity.
6) Switch app `DATABASE_URL` to Supabase DB and deploy.

## Rollback
- Revert app to old DATABASE_URL.
- Keep Supabase project for re-try or delete tables if needed.

## User migration
- Users created in Supabase Auth with temporary passwords.
- Force password reset by sending recovery email from Supabase.
