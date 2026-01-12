# Supabase Edge Functions

## stripe-webhook
- Purpose: handle Stripe webhooks in Supabase Edge Functions.
- Env vars required:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
- Deploy:
  - `supabase functions deploy stripe-webhook`

If you keep the existing FastAPI webhook, either:
- forward events to the API, or
- move the logic here and delete the old endpoint.
