# SCHLUESSELKINDER OS

SCHLUESSELKINDER OS is the monorepo for the SCHLUESSELKINDER masterbrand, starting with the first artist, SHIBARI KAWAII.

Initial seed tracks:

- PICK ME UP
- TUESDAY MORNING COMEDOWN
- ROPEMASTER

## Current Architecture

```text
apps/web        Next.js app router site, shop route, and admin route
services/api    Fastify API service with read-only archive endpoints
packages/db     Prisma PostgreSQL package for archive domain data
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

Do not commit real secrets. `.env.example` lists variable names only; local values belong in `.env` or a secret vault.

Run both app processes:

```bash
pnpm dev
```

Run services separately:

```bash
pnpm dev:web
pnpm dev:api
```

The API exposes read-only archive endpoints when `services/api` is running:

- `/health`
- `/artists`
- `/artists/:slug`
- `/objects`
- `/music`
- `/music/:releaseCode`
- `/fragments`
- `/brand-intelligence`
- `/brand-intelligence/rules`
- `/brand-intelligence/visual-rules`
- `/brand-intelligence/language-rules`
- `/brand-intelligence/forbidden-energy`
- `/brand-intelligence/audience-personas`
- `/brand-intelligence/voice-profiles`
- `/brand-intelligence/channel-rules`
- `/brand-intelligence/scoring-rules`
- `/content-graph`
- `/content-graph/campaign-worlds`
- `/content-graph/campaign-worlds/:code`
- `/content-graph/visual-environments`
- `/content-graph/mood-references`
- `/content-graph/assets`
- `/content-graph/asset-tags`
- `/content-graph/release-fragments`
- `/content-graph/channel-fragments`
- `/content-graph/compatibility`
- `/content-graph/music/:releaseCode`

Start local Postgres:

```bash
cp .env.example .env
# Fill DATABASE_URL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_PORT locally.
docker compose up -d postgres
```

Generate Prisma client, apply migrations, and seed local archive data:

```bash
pnpm --filter @schluesselkinder/db db:generate
pnpm --filter @schluesselkinder/db db:migrate:dev --name backend_foundation
pnpm --filter @schluesselkinder/db db:seed
```

## Scripts

```bash
pnpm typecheck
pnpm build
pnpm test
```

## Secret Scanning

Install local guardrails:

```bash
brew install gitleaks pre-commit
pre-commit install
```

Run a local scan:

```bash
gitleaks detect --redact --config .gitleaks.toml
```

See `docs/security/secret-management.md` for remediation and reusable setup snippets.

Database package scripts:

```bash
pnpm --filter @schluesselkinder/db db:generate
pnpm --filter @schluesselkinder/db db:migrate:dev
pnpm --filter @schluesselkinder/db db:migrate:deploy
pnpm --filter @schluesselkinder/db db:seed
```

## Environment Contract

Secret rules:

- No secrets in Git, Markdown, screenshots, prompts, or handover docs.
- Keep local values in `.env`.
- Keep real keys in a vault such as 1Password or Infisical.
- Keep `ROTATE.md` local only; it is gitignored.
- Keep `.secrets/` local only; it is gitignored.
- `HANDOVER.md`, if introduced later, must remain secret-free.

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

Database:

- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`

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
- Prisma PostgreSQL schema, migration, client export, and seed setup
- Read-only API routes for artists, objects, music, and fragments
- Read-only Brand Intelligence routes and seed data
- Read-only Content Graph routes for semantic asset orchestration
- Zod response contracts for archive endpoints
- Placeholder packages for UI and brand data
- Architecture documentation
- Hetzner and IONOS DNS planning notes

Not implemented yet:

- Stripe
- Printful
- Auth
- Real external APIs
- Shopify
- Checkout, carts, prices, stock, inventory, SKUs, fulfillment

## Next Sprint

Recommended next sprint: plan the approval layer around content graph relationships, rule violations, and human review. Stripe, Printful, checkout, carts, inventory, auth, admin UI, and fulfillment remain separate future sprints.

Sprint 6 Content Graph deliberately does not include uploads, CDN logic, AI generation, prompts, approval queues, posting, scheduling, automation, or admin UI.

## Prisma Version

`packages/db` pins Prisma and `@prisma/client` to `6.19.0`. This keeps the classic `DATABASE_URL` workflow stable for Sprint 4 and avoids Prisma 7 adapter/config churn until the backend foundation is committed and deployed cleanly.
