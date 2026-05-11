# Public Opening Runbook

This runbook describes the smallest safe deployment for the first SCHLUESSELKINDER silent live.

The deployment is web-only:

- Next.js public site
- Caddy reverse proxy and TLS
- no API
- no PostgreSQL
- no Redis
- no workers
- no scheduler
- no Stripe
- no Printful
- no social automation

Two production modes are supported:

- dedicated VPS mode: this repo runs both the Next.js web container and its own Caddy container
- existing-server mode: an existing host Caddy reverse-proxies to a localhost-only Next.js web container

Use exactly one mode. Do not run the dedicated Caddy container on a server where host Caddy already owns `80` and `443`.

## 1. Server Prerequisites

Use either one dedicated Hetzner VPS or one approved existing Hetzner server.

Required server basics:

- SSH access restricted to trusted keys
- firewall allows only `22`, `80`, and `443`
- Docker installed
- Docker Compose plugin installed
- Git installed
- enough disk space for one current and one rollback image

Do not expose database ports.

Existing-server mode additionally requires:

- existing host Caddy already owns public `80` and `443`
- localhost port `3091` is unused
- SCHLUESSELKINDER app path is isolated at `/opt/schluesselkinder/schluesselkinder-os`
- SCHLUESSELKINDER env file, if introduced later, is isolated from every other brand
- SCHLUESSELKINDER compose project name remains isolated as `schluesselkinder_web`

Never share env files between brands.

## 2. Clone From Clean Git Commit

Deploy from Git, not from a dirty local working tree.

```bash
git clone <REPO_URL> schluesselkinder-os
cd schluesselkinder-os
git checkout <COMMIT_HASH>
git status --short --branch
```

Expected deployment status:

```text
## main
```

Do not copy local untracked files such as `newsroom_connector.py` to the server.

## 3. Production Environment

The first web-only deployment uses explicit public environment values.

Required production boundary:

```env
NODE_ENV=production
NEXT_PUBLIC_APP_NAME=SCHLUESSELKINDER
NEXT_PUBLIC_WEB_URL=https://schluesselkinder.de
NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
```

Do not set `NEXT_PUBLIC_API_URL` for the first silent live.

In existing-server mode, keep these values on the `web` service in `docker-compose.existing-server.yml`. If a server-side env file is introduced later, keep it under a SCHLUESSELKINDER-only path such as `/opt/schluesselkinder/env/web.env`.

## 4. Dedicated VPS Mode

Use this mode only when SCHLUESSELKINDER owns the server Caddy surface.

From the repo root:

```bash
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Expected:

- `web` is running
- `caddy` is running
- public ports exposed by compose are only `80` and `443`
- no API, database, Redis, worker, or scheduler services exist

Inspect logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
```

## 5. Existing-Server Mode

Use this mode when the server already runs shared host Caddy for multiple brands.

The existing-server compose file runs only the Next.js web container:

```bash
docker compose -f docker-compose.existing-server.yml build web
docker compose -f docker-compose.existing-server.yml up -d
docker compose -f docker-compose.existing-server.yml ps
```

Expected:

- only the `web` service is created by this compose file
- the container binds `127.0.0.1:3091:3000`
- port `3091` is not exposed publicly
- host Caddy, not a container Caddy, handles public `80` and `443`

Verify the localhost-only binding:

```bash
sudo ss -tulpn | grep ':3091'
```

Expected binding:

```text
127.0.0.1:3091
```

Stop if the binding is `0.0.0.0:3091` or `[::]:3091`.

Install the SCHLUESSELKINDER Caddy site block only after backing up and validating the existing host Caddy configuration:

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%Y%m%d%H%M%S)
sudo grep -R "schluesselkinder.de" -n /etc/caddy || true
sudo caddy validate --config /etc/caddy/Caddyfile
```

Then add the contents of `deploy/schluesselkinder.caddy` to the host Caddy configuration using the server's existing Caddy pattern.

Validate before reload:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

Never restart shared Caddy blindly. Use `caddy validate`, then `systemctl reload caddy`.

## 6. Local Server IP Check

Before DNS cutover, verify the site from the server:

```bash
curl -I http://127.0.0.1:3091
```

If DNS is not pointed yet, use a local hosts-file override from a test machine:

```text
<SERVER_IPV4> schluesselkinder.de www.schluesselkinder.de
```

Then verify:

- `https://schluesselkinder.de`
- `https://www.schluesselkinder.de`

TLS may not issue until DNS reaches the server. If using a hosts-file check before DNS, HTTP may be the only useful preflight check.

## 7. DNS Cutover At IONOS

At IONOS, configure:

- apex `A` record to the Hetzner IPv4 address
- optional apex `AAAA` record to the Hetzner IPv6 address
- `www` as `CNAME` to `schluesselkinder.de` or `A` to the same IPv4 address

Keep the DNS setup minimal. Do not add API, admin, worker, webhook, or provider hostnames.

## 8. TLS Verification

Caddy obtains TLS automatically after DNS points to the server.

Verify:

```bash
curl -I https://schluesselkinder.de
curl -I https://www.schluesselkinder.de
```

Expected:

- valid HTTPS
- no certificate errors
- responses come from Caddy

For dedicated VPS mode, inspect Caddy logs with:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
```

For existing-server mode, inspect host Caddy logs with:

```bash
sudo journalctl -u caddy -n 100 --no-pager
```

## 9. Public Route Checklist

Verify on desktop and real mobile:

- `/`
- `/artists`
- `/artists/shibari-kawaii`
- `/music`
- `/shop`
- `/objects/sk-001`
- `/about`
- `/kontakt`
- `/impressum`
- `/datenschutz`

The object page must remain archive-only. It must not contain checkout, price, cart, stock, payment, or fulfillment mechanics.

## 10. Admin Unavailable Check

Production must keep:

```env
NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
```

Verify:

- `/admin` returns not found
- `/admin/evaluation` does not expose the internal console
- no public nav links to internal surfaces

## 11. Rollback

### Dedicated VPS Mode

Rollback by returning to the previous known-good Git commit and rebuilding the web container:

```bash
git checkout <PREVIOUS_COMMIT_HASH>
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d web
docker compose -f docker-compose.prod.yml ps
```

If Caddy configuration is the issue:

```bash
docker compose -f docker-compose.prod.yml restart caddy
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
```

### Existing-Server Mode

Rollback the web container:

```bash
git checkout <PREVIOUS_COMMIT_HASH>
docker compose -f docker-compose.existing-server.yml build web
docker compose -f docker-compose.existing-server.yml up -d web
docker compose -f docker-compose.existing-server.yml ps
docker compose -f docker-compose.existing-server.yml logs --tail=100 web
```

Rollback shared Caddy configuration only from the backup made before mutation:

```bash
sudo cp /etc/caddy/Caddyfile.bak.<TIMESTAMP> /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

Do not restart shared Caddy unless explicitly approved.

If DNS is the issue, restore the previous IONOS records.

## 12. Logs

Use only the minimal logs needed for silent-live stability:

Dedicated VPS mode:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
```

Existing-server mode:

```bash
docker compose -f docker-compose.existing-server.yml ps
docker compose -f docker-compose.existing-server.yml logs --tail=100 web
sudo journalctl -u caddy -n 100 --no-pager
```

Do not add analytics, growth dashboards, session replay, ad pixels, or social tracking for the first opening.

## 13. Do Not Deploy Yet

Do not deploy these in the first public opening:

- Fastify API
- PostgreSQL
- Redis
- workers
- schedulers
- cron jobs
- admin dashboard
- auth
- Stripe
- Printful
- provider SDKs
- social posting
- automation
- CI/CD pipeline
- monitoring stack

The first live state is a controlled public room, not an operational platform.
