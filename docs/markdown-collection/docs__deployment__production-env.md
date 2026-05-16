# Production Environment

This is the minimal environment contract for the first SCHLUESSELKINDER silent live.

The first public deployment is web-only. It does not expose the API, database, worker processes, external provider integrations, payments, fulfillment, social posting, or automation.

Two deployment modes are supported:

- dedicated VPS mode: `docker-compose.prod.yml` runs `web` and a dedicated Caddy container
- existing-server mode: `docker-compose.existing-server.yml` runs only `web`; existing host Caddy proxies to it

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

## Existing-Server Environment Isolation

Existing-server mode must isolate SCHLUESSELKINDER from every other brand on the host.

Required isolation:

- app path: `/opt/schluesselkinder/schluesselkinder-os`
- compose project name: `schluesselkinder_web`
- optional env path, if introduced later: `/opt/schluesselkinder/env/web.env`
- host Caddy site block: SCHLUESSELKINDER-only block for `schluesselkinder.de` and `www.schluesselkinder.de`
- Doppler project/config: `schluesselkinder` / `prd`

Never share env files, app secrets, database tables, webhook secrets, or runtime services between brands.

Existing-server mode binds the web container only to localhost:

```text
127.0.0.1:3091:3000
```

Host Caddy then proxies public traffic to:

```text
127.0.0.1:3091
```

Never expose `3091` publicly. It is an internal host loopback port only.

Before changing host Caddy:

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%Y%m%d%H%M%S)
sudo caddy validate --config /etc/caddy/Caddyfile
```

After adding the SCHLUESSELKINDER site block:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Never restart shared Caddy blindly. Use validate, then reload.

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
