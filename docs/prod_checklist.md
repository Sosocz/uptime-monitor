# Production Checklist

- Set `APP_ENV=production`
- Provide analytics IDs (optional): PostHog, Clarity, GA4
- Provide `SENTRY_DSN` if error tracking is enabled
- Run `alembic upgrade head`
- Verify `/health` returns 200
- Validate background worker is running
- Confirm backups for the database
