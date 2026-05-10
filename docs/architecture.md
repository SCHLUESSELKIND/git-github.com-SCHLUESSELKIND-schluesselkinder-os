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

## Sprint 6 Content Graph

Sprint 6 adds the semantic layer before campaign generation.

Content Graph models:

- `CampaignWorld`
- `VisualEnvironment`
- `MoodReference`
- `Asset`
- `AssetTag`
- `ReleaseFragment`
- `ChannelFragment`

Compatibility uses four verdicts:

- `REQUIRED`
- `ALLOWED`
- `DISCOURAGED`
- `FORBIDDEN`

The graph stores relationships between artists, releases, tracks, worlds, environments, mood references, symbolic assets, fragments, and channel fragments. It does not generate, approve, schedule, publish, upload, or process files.

Assets remain symbolic references through `referenceKey`. Sprint 6 does not introduce uploads, CDN logic, storage providers, dimensions, image processing, or file metadata systems.

Read-only API routes:

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

Sprint 6 is the data structure future moodboard generation, approval checks, channel adaptation, and brand-fit scoring will read from.

## Sprint 7 Approval Review

Sprint 7 adds human review data structures around the Content Graph before generation, posting, scheduling, automation, or campaign execution exists.

Review models:

- `ReviewItem`
- `ApprovalDecision`
- `ApprovalComment`
- `RuleViolation`

Review stages:

- `MOODBOARD_REVIEW`
- `CONTENT_REVIEW`
- `SCHEDULE_REVIEW`

`ReviewItem.status` is the current materialized review state. `ApprovalDecision` is the append-only historical decision log.

Rule violations store `source` and `ruleCode` without hard foreign keys so they can reference Brand Intelligence rules, Content Graph compatibility, or manual findings without locking the schema too early.

Read-only API routes:

- `/reviews`
- `/reviews/:reviewKey`
- `/reviews/stages`
- `/reviews/statuses`
- `/reviews/:reviewKey/decisions`
- `/reviews/:reviewKey/comments`
- `/reviews/:reviewKey/violations`

Sprint 7 does not implement write routes, auth, admin UI, status transitions, processors, schedulers, posting, generation, prompts, or integrations.

## Sprint 8 Controlled Generation

Sprint 8 adds the planning layer for constrained AI-assisted generation without calling providers or executing prompts.

Generation models:

- `ConstraintBundle`
- `GenerationBriefConstraint`
- `ChannelCompositionProfile`
- `GenerationBrief`
- `PromptSection`
- `GenerationRequest`
- `GenerationOutput`
- `GenerationOutputEvaluation`

`GenerationOutput` is review-bound material only. Approval truth lives only in `ReviewItem` and `ApprovalDecision`.

Generation output statuses:

- `GENERATED_PLACEHOLDER`
- `REVIEW_REQUIRED`
- `REVIEW_REJECTED`
- `REVIEW_ARCHIVED`

There is no `APPROVED` output status.

Read-only API routes:

- `/generation`
- `/generation/briefs`
- `/generation/briefs/:briefKey`
- `/generation/constraint-bundles`
- `/generation/channel-composition-profiles`
- `/generation/requests`
- `/generation/requests/:requestKey`
- `/generation/outputs`
- `/generation/outputs/:outputKey`
- `/generation/outputs/:outputKey/evaluations`

Sprint 8 does not implement AI provider SDKs, prompt execution, real generation, uploads, file generation, media rendering, schedulers, posting, social APIs, workers, auth, admin UI, commerce, or execution logic.

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
