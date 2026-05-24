# AGENTS.md

## Product Rules

- SCHLUESSELKINDER is the masterbrand.
- SNUFFRAGGA SOUNDSYSTEM is the first publicly active artist (lives at `/artists/snuffragga`).
- Public-facing artist roster is opened one artist at a time. Add a roster entry only after its surface is shipped.
- Commerce stack is live: Shopify (drafts only via `productCreate` with `status: DRAFT`), Printful (no vinyl SKUs), Listmonk (newsletter, double opt-in).
- Stripe Connect is reserved for label-internal payouts (future), not for the public shop.
- Auth, database migrations, and real external API integrations are now in scope and must respect the boundary + audit rules in `services/soundsystem-inference/app/`.
- Backend runs on Hetzner (Frankfurt). DNS is managed through IONOS.
- Newsletter endpoint must NEVER fake success when Listmonk is offline — return `status=offline`.
- Embeds (Spotify, SoundCloud) MUST be consent-gated client-side via `sk_embed_consent` localStorage. No iframe in DOM before consent.

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

## Sprint 1 Boundary (historical)

Sprint 1 established the repo structure only:

- Next.js public website, shop route, and admin route scaffold.
- Fastify API service with a health endpoint only.
- Prisma-ready database package placeholder only.
- Shared UI package placeholder.
- Brand token and seed copy package placeholder.
- Architecture documentation and first ADR.

## Active Stack (post-Sprint 1)

- Public web: `apps/web` (Next.js 16, Turbopack, static-first), deployed to `schluesselkinder.de` via Hetzner + Caddy.
- Operator console: `apps/web/app/admin`, gated by `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED` + operator auth.
- Inference + commerce API: `services/soundsystem-inference` (FastAPI, Python 3.12), deployed to `api.schluesselkinder.de`.
- Newsletter: self-hosted Listmonk at `listmonk.schluesselkinder.de`, double opt-in, one list (`snuffragga` tag).
- Commerce: Shopify (`shop.schluesselkinder.de`, drafts only from API; storefront is Shopify-hosted), Printful (sync, no vinyl).
- Sound embeds: Spotify + SoundCloud, gated client-side via `sk_embed_consent` localStorage.
- Repository pattern across persistence: Protocol → InMemory → Postgres → factory. Tests run against InMemory.

## Live Deploy Rules

- No restart of any production service during business hours (08:00–20:00 CET) without explicit user go.
- Every container build must inline `NEXT_PUBLIC_*` envs through both `build.args` AND `environment` in `docker-compose.existing-server.yml`.
- Caddy is the only public ingress. Never bind a service to a public port directly.
- All API mutations require operator auth (`require_operator`). Only `/health`, `/v1/capabilities`, and `/v1/public/newsletter/subscribe` are open.
- Audit log is append-only. Never expose a delete path for `commerce_sync_audit`.
