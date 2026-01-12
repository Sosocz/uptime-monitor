# TrezApp Docs

This folder contains lightweight product and ops notes for a low-cost stack.

## Analytics (optional)
- Backend events are no-op unless `APP_ENV=production` and keys are present.
- Frontend scripts only load in production when IDs are provided.

## CI
- GitHub Actions runs compile checks, pytest, and a Docker build on each push/PR.
