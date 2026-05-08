# SCHLUESSELKINDER OS

SCHLUESSELKINDER OS is the monorepo for the SCHLUESSELKINDER masterbrand, starting with the first artist, SHIBARI KAWAII.

Initial seed tracks:

- PICK ME UP
- TUESDAY MORNING COMEDOWN
- ROPEMASTER

## Current Architecture

```text
apps/web        Next.js app router site, shop route, and admin route
services/api    Fastify API service with /health
packages/db     Prisma-ready database package placeholder
packages/ui     Shared UI component placeholder
packages/brand  Brand tokens and seed copy placeholder
docs/            Architecture notes and ADRs
```

## Local Development

Install dependencies:

```bash
pnpm install
```

Copy the environment example only when local overrides are needed:

```bash
cp .env.example .env
```

Do not commit real secrets. Stripe, Printful, and database values in `.env.example` are placeholders for later sprints.

Run both app processes:

```bash
pnpm dev
```

Run services separately:

```bash
pnpm dev:web
pnpm dev:api
```

The API health endpoint is available at `/health` when `services/api` is running.

## Scripts

```bash
pnpm typecheck
pnpm build
pnpm test
```

## Environment Contract

Shared:

- `NODE_ENV`
- `LOG_LEVEL`

Web:

- `NEXT_PUBLIC_APP_NAME`
- `NEXT_PUBLIC_WEB_URL`
- `NEXT_PUBLIC_API_URL`

API:

- `API_HOST`
- `API_PORT`

Database later:

- `DATABASE_URL`

Stripe later:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

Printful later:

- `PRINTFUL_API_TOKEN`
- `PRINTFUL_STORE_ID`

## Implemented Scope

Implemented:

- pnpm TypeScript monorepo scaffold
- Next.js app router scaffold
- Tailwind setup for the web app
- Fastify health endpoint
- API environment loader and route separation
- API health endpoint test
- Placeholder packages for database, UI, and brand data
- Architecture documentation
- Hetzner and IONOS DNS planning notes

Not implemented yet:

- Stripe
- Printful
- Auth
- Database migrations
- Real external APIs
- Shopify

## Next Sprint

Recommended next sprint: define the database model and commerce state machine before adding Stripe or Printful SDKs. That should include orders, products, artists, releases, provider event logs, and webhook idempotency rules.
