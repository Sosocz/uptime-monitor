# Supabase Setup

## Project
- URL: https://yviwqmrmbdyeyztezkto.supabase.co
- Anon key: sb_publishable_bXJTiXT2rG6pCkh77EWVNg_-ODXpoZ5

## Env vars
```
SUPABASE_URL=https://yviwqmrmbdyeyztezkto.supabase.co
SUPABASE_ANON_KEY=sb_publishable_bXJTiXT2rG6pCkh77EWVNg_-ODXpoZ5
SUPABASE_SERVICE_ROLE_KEY=***
SUPABASE_DB_URL=postgresql://... (Supabase DB connection string)
NEXT_PUBLIC_SUPABASE_URL=https://yviwqmrmbdyeyztezkto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_bXJTiXT2rG6pCkh77EWVNg_-ODXpoZ5
```

## Migrations
```
supabase db push
supabase db seed
```

## Local dev
- Update `DATABASE_URL` to Supabase Postgres.
- Run app: `python -m uvicorn app.main:app --reload`
