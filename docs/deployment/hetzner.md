# Hetzner Deployment Notes

## Status

Planning document only. No deployment automation exists yet.

## Expected Shape

- `services/api` is the backend service intended for Hetzner later.
- The API should run as a long-lived Node.js process behind a reverse proxy.
- The service should expose `/health` for uptime checks and rollout verification.
- Runtime configuration should come from environment variables, not committed files.

## Required Later Decisions

- Server type and region.
- Operating system image.
- Process manager strategy.
- Reverse proxy strategy.
- TLS certificate automation.
- PostgreSQL hosting location.
- Backup and restore policy.
- Deployment mechanism from Git.

## Environment Inputs

- `NODE_ENV`
- `LOG_LEVEL`
- `API_HOST`
- `API_PORT`
- `DATABASE_URL` later
- Stripe variables later
- Printful variables later

## Non-Goals For Sprint 1.5

- No server provisioning.
- No Dockerfile.
- No CI/CD pipeline.
- No database migration execution.
- No external API credentials.
