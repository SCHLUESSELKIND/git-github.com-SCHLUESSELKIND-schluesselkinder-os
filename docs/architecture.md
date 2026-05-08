# Architecture

## System Shape

SCHLUESSELKINDER OS starts as a pnpm TypeScript monorepo.

```text
apps/web        Next.js app router frontend for public, shop, and admin routes
services/api    Fastify service for backend endpoints
packages/db     Prisma-ready database package
packages/ui     Shared UI components
packages/brand  Brand tokens and seed copy
```

## Sprint 1 Decisions

- The web application uses Next.js, TypeScript, Tailwind, and the app router.
- The API service uses Fastify and exposes only `/health`.
- The database package contains a Prisma schema placeholder only.
- The UI package contains minimal shared components only.
- The brand package contains the SCHLUESSELKINDER seed context.

## Explicit Non-Goals

- No Stripe implementation.
- No Printful implementation.
- No authentication.
- No database migrations.
- No real external APIs.
- No Shopify.

## Deployment Context

- Backend hosting target: Hetzner later.
- Domain and DNS: IONOS DNS later.
- Commerce plan: Stripe and Printful later.
