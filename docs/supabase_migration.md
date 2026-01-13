# Supabase Migration (TrezApp)

## Prerequisites
- Supabase project created and reachable.
- Supabase keys ready: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`.
- Staging host (subdomain or host-header based routing).

## Staging Setup (no prod impact)
Pick one:
1) Subdomain
   - Create `staging.trezapp.fr` DNS record pointing to the server.
   - Add an Nginx server block to route `staging.trezapp.fr` to the staging app instance.
2) Host header
   - Reuse the same server but route by `Host:` header to a staging app instance.

Set staging env vars (example):
```
APP_ENV=staging
SITE_URL=https://staging.trezapp.fr
APP_BASE_URL=https://staging.trezapp.fr
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_DB_URL=...
```

## Supabase DB Migrations (SQL)
Apply schema migrations first, then enable RLS after validation:
1) Apply schema + policies (RLS still disabled):
   - `supabase/migrations/20250308120000_init.sql`
   - `supabase/migrations/20250308120500_rls.sql`
   - `supabase/migrations/20250308121000_storage.sql`
   - `supabase/migrations/20250308121500_realtime.sql`
   - `supabase/migrations/20250308122000_views.sql`
2) Validate staging app with Supabase DB.
3) Enable RLS by applying:
   - `supabase/migrations/20250308123000_enable_rls.sql`

You can apply migrations via Supabase CLI or by running the SQL in the Supabase SQL editor.

## Data Migration (idempotent + dry-run)
Script supports dry-run, batch size, table selection, and logs.

Dry-run:
```
npx tsx scripts/migrate_to_supabase.ts --dry-run --log-file=./supabase_migration.log
```

Real migration:
```
SOURCE_DATABASE_URL=postgresql://... \
SUPABASE_DB_URL=postgresql://... \
SUPABASE_URL=https://<project>.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=... \
npx tsx scripts/migrate_to_supabase.ts --batch-size=500 --log-file=./supabase_migration.log
```

## Cutover Checklist
- Staging: login/register/session/logout works with Supabase Auth.
- Core endpoints return 200 and data loads correctly.
- Background workers operate normally.
- Apply RLS enable migration.
- Update production env `SUPABASE_DB_URL` and Supabase keys.
- Restart app + workers.

## Rollback (no code rollback)
- Switch `SUPABASE_DB_URL` back to the previous DB URL.
- Restart app + workers.
