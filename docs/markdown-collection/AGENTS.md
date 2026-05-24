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

## Public Brand Art Direction

- SCHLUESSELKINDER is not horror, not cyberpunk, not fetish decoration, and not an AI moodboard.
- SCHLUESSELKINDER is a cold underground music and streetwear label system.
- Core tension: post-club melancholy, brutalist fashion culture, ritual restraint, and techno-industrial emptiness.
- Use radical reduction. Do not add visual motifs just because they are available.
- The dungeon/chair image is the primary recurring campaign environment.
- The rune/key symbol is the systemic identity language.
- All other visuals are references only unless explicitly approved.
- Avoid moodboard collage energy.
- Avoid internet occult aesthetics.
- Avoid creepy doll, prop, or horror energy.
- Avoid overdesigned cyberpunk.
- Avoid generic SaaS, portfolio, Shopify, or merch-shop language.
- The shop must feel like a future object archive, not a store.
- Copy must stay sparse, cold, bilingual, and editorial.
- Every public page should pass this filter: would an obscure Berlin underground label actually publish this?

## Visual Decision Filter

1. Does it make the brand more iconic?
2. Does it increase tension without adding noise?
3. Does it feel expensive, cold, and controlled?
4. Does it avoid explaining too much?
5. Does it protect the chair and rune system?

## Sprint 1 Boundary

Sprint 1 establishes the repo structure only:

- Next.js public website, shop route, and admin route scaffold.
- Fastify API service with a health endpoint only.
- Prisma-ready database package placeholder only.
- Shared UI package placeholder.
- Brand token and seed copy package placeholder.
- Architecture documentation and first ADR.
