# Marketing OS Roadmap

Planning sequence for the Artist Marketing OS. Each slice is small,
scoped, and reversible. Each slice has explicit exclusions to keep the
boundary honest.

The roadmap continues the Sprint sequence after Sprint 10 Internal
Evaluation Console. Slices are numbered M-1 through M-10. Sprint
numbers are assigned at landing time.

## Guiding Constraints

- Docs first, code per slice.
- Provider names live in routing and compliance docs only.
- Approval truth never leaves `ReviewItem` and `ApprovalDecision`.
- Every artifact must carry a full `ComplianceRecord`.
- No publishing API in MVP.
- No commerce, no auth, no posting, no scheduling before their slice.
- `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED` gates the entire surface.

## M-1 Marketing Core Scaffold

Goal: route map and operator hub render with placeholder content.

In scope:

- `apps/web/app/admin/marketing/*` routes scaffolded behind the
  console gate.
- Operator hub page with five board lanes that read existing read-only
  archive routes.
- `Artist`, `MusicRelease`, and `Fragment` read views.
- Navigation, layout, and operator-mode tokens reused from the
  Operator Console pattern.

Out of scope: writes of any kind, generation, exports, social APIs,
analytics imports, captions, briefs.

## M-2 Marketing Domain Tables

Goal: persist the new entities defined in `data-model.md`.

In scope:

- `packages/db` migration for: `ArtistBrandProfile`, `Release`,
  `Campaign`, `CreativeBrief`, `BrandLockSnapshot`, `CreativeAsset`,
  `AssetVersion`, `ChannelExport`, `CaptionPack`, `CampaignTask`,
  `AnalyticsSnapshot`, `ComplianceRecord`.
- Seed data for one demo artist and one demo release.
- Read-only Fastify routes under `services/api` for the new entities.

Out of scope: write routes, write UI, generation calls, integrations.

## M-3 CreativeBrief Surface

Goal: operator can compose a brief, freeze a brand lock, and emit
`GenerationRequest` records.

In scope:

- Write routes for `CreativeBrief`, `BrandLockSnapshot`, and the
  binding to existing Sprint 8 `GenerationRequest`.
- Operator UI for `BUILD RELEASE CAMPAIGN` and content-factory single
  actions that materialize a brief.
- Brand-lock freeze logic that snapshots Sprint 5 and Sprint 6 records
  into `BrandLockSnapshot`.

Out of scope: real generation, exports, captions, posting.

## M-4 CaptionPack As Text-Only Artifact

Goal: produce per-channel caption variants without any generative
media.

In scope:

- `CREATE CAPTION PACK` action.
- `CaptionPack` write routes.
- Text generation through the existing controlled generation pattern,
  bound to `ReviewItem`.
- Variants per channel with channel-rule enforcement.

Out of scope: imagery, motion, hashtags policy automation, posting.

## M-5 Mock Visual Generation

Goal: end-to-end flow for image artifacts using a mock provider.

In scope:

- `image_generation_provider` registry rows with the mock provider
  marked `commercial_status = ready`.
- `CREATE COVER`, `CREATE POSTER`, `CREATE STORY PACK`,
  `CREATE PRESS IMAGE` actions producing `CreativeAsset` rows with
  placeholder files and complete `ComplianceRecord` payloads.
- Brand-lock enforcement on every request.
- Approval flow exercised end to end against `ReviewItem`.

Out of scope: real image providers, real renders, ad pack rendering.

## M-6 Mock Clip Generation And Template Rendering

Goal: motion artifacts through a mock clip provider and a real
deterministic template renderer.

In scope:

- `clip_generation_provider` mock and `template_rendering_provider`
  registry rows.
- `CREATE REEL`, `CREATE VISUALIZER CLIP`, `CREATE LYRIC VIDEO`,
  `CREATE SPOTIFY CANVAS STILL` actions.
- Template renderer producing deterministic outputs from approved
  stills, audio, and titles via FFmpeg or Remotion through a server
  job, not a provider SDK call.

Out of scope: real generative clip providers, real audio analysis,
auto-publishing.

## M-7 Asset Library And Versioning

Goal: a single library view of approved artifacts with versions.

In scope:

- `/admin/marketing/library` page with filters.
- `AssetVersion` write flow and history view.
- Cross-campaign asset reuse with explicit license carry-forward.

Out of scope: external storage sync, public asset gallery, commerce.

## M-8 ChannelExport And Manual Publish Checklist

Goal: bundled export packs and a manual publish checklist per channel.

In scope:

- `EXPORT CHANNEL ASSETS`, `EXPORT RELEASE PACK` actions.
- `ChannelExport` rendering with channel-specific format enforcement.
- Manifest file inside every export with caption pack, hashtags,
  posting order, and asset references.
- Local filesystem export under `apps/web/.export/`.

Out of scope: posting APIs, scheduling, ad accounts.

## M-9 Storage Sync (Dropbox)

Goal: write export packs to Dropbox in the canonical folder schema.

In scope:

- `storage_sync_provider` registry rows.
- Dropbox write-only adapter with vault-stored credentials.
- Folder schema enforcement and idempotent uploads.
- Read-only manifest reflection back into `ChannelExport`.

Out of scope: Drive sync, posting, downloads of operator-uploaded
media in MVP.

## M-10 Manual Analytics And Campaign Report

Goal: capture KPIs and produce a campaign report artifact.

In scope:

- `AnalyticsSnapshot` write routes and operator entry forms.
- Campaign report generation as a text artifact bound to `ReviewItem`.
- Reporting view inside the campaign workspace.

Out of scope: real analytics imports, aggregator integrations, ad
performance, real-time dashboards.

## M-11 And Beyond — Publishing And Aggregators

Sequenced individually, each behind its own gate.

| Slice    | Goal                                                          |
| -------- | ------------------------------------------------------------- |
| M-11     | YouTube Data API upload behind per-account toggle             |
| M-12     | Meta Graph API publishing for Business accounts only          |
| M-13     | TikTok Content Posting API where eligible                     |
| M-14     | SoundCloud OAuth and metadata pipeline                        |
| M-15     | YouTube analytics imports                                     |
| M-16     | Meta insights imports                                         |
| M-17     | TikTok insights where eligible                                |
| M-18     | Aggregator integration evaluation                             |
| M-19     | Ad creative pack delivery to ad accounts (no spend in slice)   |
| M-20     | Ad spend controls behind explicit operator confirmation        |

Each slice ships with provider candidates, risk tier, registry rows,
operator action additions if any, and exclusions.

## Cross-Slice Exclusions

The Marketing OS deliberately does not include, at any slice, until a
dedicated planning doc lands:

- A public marketing surface.
- Commerce, cart, or fulfillment.
- Auth for operators in MVP; the console gate stands until a real auth
  slice is approved.
- Replacing the distributor for any audio platform.
- Engagement-first scoring or virality optimization.
- Auto-mutation of Brand Intelligence rules.
- Cross-channel cross-posting that bypasses per-channel review.

## Verification Per Slice

Each slice ships with:

- `pnpm typecheck` and `pnpm build` for any touched code.
- Read-route contract tests for new Fastify routes.
- Migration dry-run note.
- A short slice memo under `docs/marketing/slices/M-<n>.md` with
  what landed and what was deferred.

## Cross-Reference

- `docs/marketing/artist-marketing-os.md`
- `docs/marketing/visual-content-engine.md`
- `docs/marketing/integrations.md`
- `docs/marketing/data-model.md`
- `docs/architecture.md`
