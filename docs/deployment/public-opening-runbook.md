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

## 1. Server Prerequisites

Provision one Hetzner VPS.

Required server basics:

- SSH access restricted to trusted keys
- firewall allows only `22`, `80`, and `443`
- Docker installed
- Docker Compose plugin installed
- Git installed
- enough disk space for one current and one rollback image

Do not expose database ports.

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

The first web-only deployment uses the environment values embedded in `docker-compose.prod.yml`.

Required production boundary:

```env
NODE_ENV=production
NEXT_PUBLIC_APP_NAME=SCHLUESSELKINDER
NEXT_PUBLIC_WEB_URL=https://schluesselkinder.de
NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
```

Do not set `NEXT_PUBLIC_API_URL` for the first silent live.

## 4. Build

From the repo root:

```bash
docker compose -f docker-compose.prod.yml build web
```

This builds only the Next.js public web app.

## 5. Start

```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Only `web` and `caddy` should be running.

## 6. Local Server IP Check

Before DNS cutover, verify the site from the server:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
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
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
```

Expected:

- valid HTTPS
- no certificate errors
- responses come from Caddy

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

If DNS is the issue, restore the previous IONOS records.

## 12. Logs

Use only the minimal logs needed for silent-live stability:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
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
