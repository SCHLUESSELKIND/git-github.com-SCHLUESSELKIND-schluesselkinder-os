# AGENTS.md

## Product Rules

- SCHLUESSELKINDER is the masterbrand.
- SHIBARI KAWAII is the first artist.
- Initial seed tracks are PICK ME UP, TUESDAY MORNING COMEDOWN, and ROPEMASTER.
- Do not use Shopify.
- Stripe and Printful are planned later, but must not be implemented in Sprint 1.
- Auth, database migrations, and real external APIs are out of scope for Sprint 1.
- The backend is expected to run on Hetzner later.
- Domain and DNS will be managed through IONOS DNS later.

## Engineering Rules

- Use pnpm as the package manager.
- Keep the repository as a TypeScript monorepo.
- Keep app code under `apps/`, deployable services under `services/`, and shared packages under `packages/`.
- Keep domain and brand constants out of route components when practical.
- Prefer small, explicit scaffolds over premature abstractions.
- Add integrations only after their sprint is explicitly approved.

## Sprint 1 Boundary

Sprint 1 establishes the repo structure only:

- Next.js public website, shop route, and admin route scaffold.
- Fastify API service with a health endpoint only.
- Prisma-ready database package placeholder only.
- Shared UI package placeholder.
- Brand token and seed copy package placeholder.
- Architecture documentation and first ADR.
