# ADR 0001: Project Structure

## Status

Accepted for Sprint 1.

## Context

SCHLUESSELKINDER OS needs a foundation for a public website, shop routes, admin routes, backend services, and shared domain packages. The repository starts empty, so the first decision is the filesystem and package boundary.

## Decision

Use a pnpm TypeScript monorepo with these top-level areas:

- `apps/web` for the Next.js app router frontend.
- `services/api` for the Fastify backend service.
- `packages/db` for the Prisma-ready database package.
- `packages/ui` for shared UI components.
- `packages/brand` for brand tokens and seed copy.
- `docs` for architecture notes and ADRs.

## Consequences

- Web, API, and shared packages can evolve independently while using one lockfile.
- Shared brand context is explicit and importable.
- Prisma can be introduced later without mixing database concerns into the web app.
- Stripe, Printful, auth, database migrations, and external APIs remain outside Sprint 1.
