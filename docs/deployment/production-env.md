# Production Environment

This is the minimal environment contract for the first SCHLUESSELKINDER silent live.

The first public deployment is web-only. It does not expose the API, database, worker processes, external provider integrations, payments, fulfillment, social posting, or automation.

## Web Container

Required values:

```env
NODE_ENV=production
NEXT_PUBLIC_APP_NAME=SCHLUESSELKINDER
NEXT_PUBLIC_WEB_URL=https://schluesselkinder.de
NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
```

Do not set `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true` in public production.

Do not set `NEXT_PUBLIC_API_URL` for the first silent live. The public site does not require the API, and the internal evaluation console must remain unavailable.

## Not Used In First Live

Do not configure these for the first web-only public opening:

- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `PRINTFUL_API_TOKEN`
- `PRINTFUL_STORE_ID`

These belong to later explicitly approved backend, commerce, or fulfillment phases.

## Production Boundary

The first deployment must expose only:

- `https://schluesselkinder.de`
- `https://www.schluesselkinder.de`

No API hostname, admin hostname, database port, provider webhook, scheduler, worker, or automation surface should be exposed.
