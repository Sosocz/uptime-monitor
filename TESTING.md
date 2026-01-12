# Testing Checklist

## Auth
- Signup/login/logout/reset password
- OAuth Google/GitHub

## RLS
- Access denied when using token for another user
- Public status page readable without auth

## CRUD
- Monitors: create/update/delete
- Incidents: read/update
- Status pages: create/update

## Storage
- Upload avatar/status page asset
- Public URL works (avatars/status assets)
- Private export access requires signed URL

## Realtime
- Monitor/incident updates push to subscribers

## Performance
- Basic API latency acceptable
