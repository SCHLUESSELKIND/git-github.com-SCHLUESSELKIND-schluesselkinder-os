# Architecture

## System Shape

SCHLUESSELKINDER OS starts as a pnpm TypeScript monorepo.

```text
apps/web        Next.js app router frontend for public, shop, and admin routes
services/api    Fastify service for read-only archive endpoints
packages/db     Prisma PostgreSQL package for archive domain data
packages/ui     Shared UI components
packages/brand  Brand tokens and seed copy
```

## Sprint 1 Decisions

- The web application uses Next.js, TypeScript, Tailwind, and the app router.
- The API service uses Fastify and exposes only `/health`.
- The database package contains a Prisma schema placeholder only.
- The UI package contains minimal shared components only.
- The brand package contains the SCHLUESSELKINDER seed context.

## Sprint 4 Backend Foundation

Sprint 4 establishes the institutional archive backend without commerce or authentication.

Domain packages:

- `packages/db` owns Prisma schema, generated client access, migrations, and seed data.
- `services/api` owns Fastify route plugins, Zod response contracts, and read-only repository access.

Archive models:

- `Artist` stores artist identity, symbol, status, and a sparse bio fragment.
- `MusicRelease` stores release-level music artifacts.
- `Track` stores track metadata under a music release.
- `ObjectRelease` stores future object archive records without commerce fields.
- `Fragment` stores reusable language and archive fragments.

Archive-native release states:

- `SIGNAL_PENDING`
- `ACTIVE`
- `CLOSED`
- `ARCHIVED`
- `HIDDEN`

Read-only API routes:

- `/health`
- `/artists`
- `/artists/:slug`
- `/objects`
- `/music`
- `/music/:releaseCode`
- `/fragments`

Sprint 4 deliberately excludes prices, stock, checkout, carts, Stripe, Printful, inventory, SKU, fulfillment, auth, analytics, and dashboard UI.

Prisma is pinned to `6.19.0` for Sprint 4. The pin preserves the stable `DATABASE_URL` schema workflow while the backend foundation is established.

## Sprint 5 Brand Intelligence

Sprint 5 turns brand strategy into read-only backend data for future Signal Engine evaluation.

Brand Intelligence models:

- `BrandRule`
- `VisualRule`
- `LanguageRule`
- `ForbiddenEnergy`
- `VoiceProfile`
- `AudiencePersona`
- `ChannelRule`
- `SignalScoringRule`

Concept boundaries:

- Audience psychology defines who the system resonates with.
- Voice profiles define how the system speaks.
- Rules define what future generated outputs may or may not do.
- Scoring rules define how future outputs will be evaluated later.

Read-only API routes:

- `/brand-intelligence`
- `/brand-intelligence/rules`
- `/brand-intelligence/visual-rules`
- `/brand-intelligence/language-rules`
- `/brand-intelligence/forbidden-energy`
- `/brand-intelligence/audience-personas`
- `/brand-intelligence/voice-profiles`
- `/brand-intelligence/channel-rules`
- `/brand-intelligence/scoring-rules`

Sprint 5 does not implement scoring execution, AI generation, automation, integrations, or admin UI.

## Security Direction

- No secrets in Git.
- No secrets in Markdown docs.
- No secrets in screenshots, Codex prompts, or handover files.
- `.env.example` lists variable names only.
- `.env`, `.env.*`, `.secrets/`, `ROTATE.md`, and `HANDOVER.old.md` are gitignored.
- Production secrets should be injected through deployment environment configuration or a vault.
- The API logger redacts common sensitive headers and does not log environment values.

## Explicit Non-Goals

- No Stripe implementation.
- No Printful implementation.
- No authentication.
- No real external APIs.
- No Shopify.
- No checkout, carts, prices, stock, inventory, SKUs, or fulfillment.

## Deployment Context

- Backend hosting target: Hetzner later.
- Domain and DNS: IONOS DNS later.
- Commerce plan: Stripe and Printful later.
