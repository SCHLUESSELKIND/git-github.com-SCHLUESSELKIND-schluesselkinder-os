# SCHLUESSELKINDER OS

SCHLUESSELKINDER OS is the monorepo for the SCHLUESSELKINDER masterbrand, starting with the first artist, SHIBARI KAWAII.

Initial seed tracks:

- PICK ME UP
- TUESDAY MORNING COMEDOWN
- ROPEMASTER

## Architecture

```text
apps/web        Next.js app router site, shop route, and admin route
services/api    Fastify API service
packages/db     Prisma-ready database package placeholder
packages/ui     Shared UI component placeholder
packages/brand  Brand tokens and seed copy placeholder
docs/            Architecture notes and ADRs
```

## Sprint 1 Scope

Implemented:

- pnpm TypeScript monorepo scaffold
- Next.js app router scaffold
- Tailwind setup for the web app
- Fastify health endpoint
- Placeholder packages for database, UI, and brand data
- Architecture documentation

Not implemented yet:

- Stripe
- Printful
- Auth
- Database migrations
- Real external APIs
- Shopify

## Commands

```bash
pnpm install
pnpm typecheck
pnpm build
pnpm dev
```

Run the services separately during development when needed:

```bash
pnpm dev:web
pnpm dev:api
```

The API health endpoint is available at `/health` when `services/api` is running.
