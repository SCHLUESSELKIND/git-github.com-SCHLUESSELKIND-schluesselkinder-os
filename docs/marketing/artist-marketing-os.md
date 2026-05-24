# Artist Marketing OS

Internal admin module that turns a release into a campaign. Lives under
`apps/web/app/admin/marketing/`. Not a public surface.

This document is a planning slice. It does not introduce new runtime code,
real provider integrations, or social automation. It anchors the operator
surface, the route map, the data model boundary, and the slice sequence
that will land under future sprints.

## Position In The Existing Architecture

The Marketing OS sits one layer above Brand Intelligence, Content Graph,
Controlled Generation, and Approval Review. It is the operator-facing
campaign and content surface that consumes those archives instead of
re-implementing them.

| Existing layer                       | Role for the Marketing OS                              |
| ------------------------------------ | ------------------------------------------------------ |
| Brand Intelligence (Sprint 5)        | Source of voice, visual, channel, and scoring rules    |
| Content Graph (Sprint 6)             | Source of campaign worlds, environments, mood, assets  |
| Approval Review (Sprint 7)           | Single source of truth for human approval state        |
| Controlled Generation (Sprint 8)     | Carries every generated artifact under a `ReviewItem`  |
| Evaluation Rule Engine (Sprint 9)    | Issues interpretability reports, never approval        |
| Internal Evaluation Console (Sprint 10) | Local interpretability surface, no operator actions |
| SOUNDSYSTEM Inference Engine         | Internal audio generation provider, not exposed in UI  |

The Marketing OS does not introduce a parallel approval store. Every
generated marketing artifact must remain bound to a `ReviewItem`, and
approval truth stays inside `ApprovalDecision` history exactly as
Sprint 7 and Sprint 8 require.

## Vision

> From release to campaign. The operator describes a track, a release,
> a mood, and a goal. The OS produces the campaign brief, the creative
> assets, the channel exports, the posting checklist, and the analytics
> targets.

Three principles bind the design:

1. **Intent-driven, not vendor-driven.** The main UI exposes creative
   actions such as `CREATE COVER` or `BUILD RELEASE CAMPAIGN`. It never
   exposes generator names, model identifiers, or provider SDKs.
2. **Manual publishing first.** MVP produces export packs and a manual
   publish checklist. It does not call social network publishing APIs.
3. **Compliance is part of the artifact.** Every generated asset
   carries its prompt, provider group, model identifier, seed, license
   posture, and human approver alongside the file itself.

## Route Map

```text
apps/web/app/admin/marketing/
  page.tsx                               operator hub
  artists/
    page.tsx                             artist list
    [artistSlug]/
      page.tsx                           artist profile and brand DNA
      releases/page.tsx
      campaigns/page.tsx
      content/page.tsx
      analytics/page.tsx
  releases/
    page.tsx                             cross-artist release pipeline
    [releaseCode]/
      page.tsx                           release detail and asset board
      campaigns/page.tsx
  campaigns/
    page.tsx                             campaign pipeline
    [campaignCode]/
      page.tsx                           campaign workspace
      assets/page.tsx
      calendar/page.tsx
      exports/page.tsx
      analytics/page.tsx
  content-factory/
    page.tsx                             creative action hub
    cover/page.tsx
    reel/page.tsx
    story/page.tsx
    poster/page.tsx
    caption/page.tsx
    lyric/page.tsx
    canvas/page.tsx
  library/
    page.tsx                             asset library and version tree
  calendar/page.tsx                      consolidated posting calendar
  exports/page.tsx                       export pack queue
  ads/page.tsx                           ad creative packs
```

The entire `/admin/marketing/*` subtree is gated by
`NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true` exactly like the Operator
Console. Production deployments keep the variable unset. The gate is a
local boundary marker, not authentication.

## Operator Hub

`/admin/marketing` exposes five board lanes:

```text
ACTIVE RELEASES
CAMPAIGNS IN PROGRESS
CONTENT TO REVIEW
ASSETS READY TO EXPORT
ANALYTICS WARNINGS
```

Each lane reads from existing read-only routes (see
`docs/architecture.md`) plus new Marketing OS routes added in later
slices. No lane mutates archive state from the hub itself.

## Operator Actions

Operator actions are the only verbs that appear in the primary UI.

```text
BUILD RELEASE CAMPAIGN
BUILD PRE-SAVE CAMPAIGN
BUILD DROP WEEK
BUILD CLUB TEASER
BUILD MERCH PUSH
BUILD SOUNDCLOUD LAUNCH
BUILD TIKTOK SNIPPET PACK
CREATE COVER
CREATE VISUALIZER CLIP
CREATE REEL
CREATE STORY PACK
CREATE POSTER
CREATE LYRIC VIDEO
CREATE AD CREATIVE
CREATE PRESS IMAGE
CREATE SOUNDCLOUD BANNER
CREATE SPOTIFY CANVAS STILL
CREATE CAPTION PACK
EXPORT CHANNEL ASSETS
EXPORT RELEASE PACK
```

The action vocabulary is the public contract of the OS. Renaming or
removing an action is a planning decision; adding a new action requires
a doc update before code.

## No Raw Provider UI

The operator never sees:

- Model names (MusicGen, Stable Audio, Flux, SDXL, Runway, Luma, Kling,
  Pika, Stable Diffusion).
- Vendor names (OpenAI, Anthropic, Stability AI, Meta, ByteDance,
  Anthropic, Google).
- SDK identifiers, endpoint URLs, or raw prompt scaffolding.

Provider names live in three places only:

- `docs/marketing/integrations.md` and
  `docs/marketing/visual-content-engine.md` for design.
- The provider registry inside `services/api` for routing.
- The Internal Evaluation Console (Sprint 10) for interpretability.

The Marketing OS UI references intent groups instead, for example
`image_generation_provider` or `clip_generation_provider`. Provider
selection is a routing decision made by the registry, not an operator
decision in the primary flow.

## Primary User Flows

### Flow A — Build A Release Campaign

```text
1. Operator opens /admin/marketing/artists/[artistSlug]
2. Operator selects a Release in SIGNAL_PENDING or ACTIVE
3. Operator runs BUILD RELEASE CAMPAIGN
4. OS opens a CreativeBrief draft prefilled from:
     ArtistBrandProfile
     ReleaseFragment
     CampaignWorld
     ChannelRule
     VoiceProfile
5. Operator picks objective, channels, key dates
6. OS opens GenerationRequest records bound to ReviewItem entries
7. CreativeAssets are produced under each ReviewItem
8. Operator reviews, approves, or rejects through ApprovalDecision
9. Approved assets enter the ChannelExport queue
10. Export pack is downloadable; manual publish checklist is produced
```

### Flow B — Single Cover Generation

```text
1. Operator opens /admin/marketing/content-factory/cover
2. Operator picks artist, release, format, brand-lock setting
3. OS opens a CreativeBrief subset (cover only)
4. OS opens a GenerationRequest bound to a ReviewItem
5. CreativeAsset is produced with prompt, seed, provider, license tag
6. Operator approves or rejects
7. Asset lands in the AssetLibrary under the release
```

### Flow C — Caption Pack

```text
1. Operator opens /admin/marketing/content-factory/caption
2. Operator picks artist, release, channel set, length, tone
3. OS produces a CaptionPack with channel-specific variants
4. Operator approves; pack joins the campaign workspace
```

### Flow D — Channel Export

```text
1. Operator opens a Campaign workspace
2. Operator selects approved CreativeAssets
3. Operator runs EXPORT CHANNEL ASSETS
4. OS produces ChannelExport records per asset per channel
5. Format Renderer enforces channel format requirements
6. Export pack is bundled with metadata and publish checklist
```

## MVP Scope

The MVP must do the following without calling any external publishing
API and without rendering real generated media:

- Create and edit Artist profiles and ArtistBrandProfile records.
- Create and edit Release records linked to existing `MusicRelease`
  archive rows where applicable.
- Open a CreativeBrief for a campaign or for a single creative action.
- Open GenerationRequest records bound to ReviewItem entries.
- Produce CreativeAsset placeholders with prompt and provider-group
  metadata, no media rendering yet.
- Produce CaptionPack drafts as text only.
- Produce ChannelExport records with format requirements and a
  manifest, no upload, no posting.
- Produce a manual publish checklist per channel.

## Out Of MVP

The MVP deliberately does not include:

- Real image, video, or audio generation execution.
- Provider SDK calls.
- Posting, scheduling, or autopublish for Instagram, TikTok, YouTube,
  SoundCloud, or any other social network.
- Dropbox or Google Drive sync.
- Real-time analytics imports.
- Ad account management.
- Auth, roles, or RBAC.
- Stripe, Printful, commerce, inventory, or checkout.
- Mutation of approval truth outside the `ApprovalDecision` flow
  defined by Sprint 7.

## Slice Sequence (Summary)

The full sequence and exclusions live in `docs/marketing/roadmap.md`.
Headline order:

1. Marketing Core scaffold and operator hub.
2. Artist and release surfaces wired to existing archive routes.
3. CreativeBrief draft surface bound to existing GenerationRequest
   records.
4. CaptionPack as text-only artifact.
5. Asset Library read surface.
6. ChannelExport pack and manifest.
7. Visual generation mock and brand lock concept.
8. Clip generation mock.
9. Storage sync (Dropbox first, Drive optional).
10. Manual analytics imports and campaign reporting.
11. Publishing integrations, gated per channel.

## Cross-Reference

- `docs/architecture.md`
- `docs/brand/brand-intelligence-system.md`
- `docs/brand/content-graph.md`
- `docs/brand/approval-review-system.md`
- `docs/brand/controlled-generation-layer.md`
- `docs/brand/evaluation-rule-engine.md`
- `docs/brand/manual-export-surface.md` (if introduced under
  Marketing OS, not yet present)
- `docs/soundsystem/model-provider-strategy.md`
- `docs/soundsystem/operator-console.md`
