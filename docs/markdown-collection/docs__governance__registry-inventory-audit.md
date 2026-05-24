# Registry Inventory Audit

## Status

Phase 1 inventory only.

No Prisma migration was created or applied.
No runtime code was changed.
No API route was added.
No provider integration was added.
No schema diff is proposed in this document.

## Scope

This audit inventories the current SCHLUESSELKINDER repository against the Registry Foundation boundary:

- Prisma models and enums
- runtime read/write surface
- provider, commerce, worker, queue, scheduler, webhook, GPT, storage, and upload traces
- canonical identity and naming fields
- state, temporal, projection, mutation, and authority risks

## Repository Reality

The actual app repository is present at:

```text
/Users/thomasfrerich/schluesselkinder-os
```

Repository state during audit:

- branch: `main`
- git status: clean before this document was added
- package manager: `pnpm`
- stack present: Next.js web app, Fastify API, Prisma/PostgreSQL package

## Prisma Inventory

Prisma schema:

```text
packages/db/prisma/schema.prisma
```

Inventory count:

- 39 Prisma models
- 21 Prisma enums

Core canonical models already present:

| Model | Current Role | Audit Note |
| --- | --- | --- |
| `Artist` | artist identity | exists, uses `slug` as unique lookup; no separate `artistKey` |
| `MusicRelease` | music release archive node | exists, uses `releaseCode` as unique code; no duplicate generic `Release` model found |
| `Track` | track under `MusicRelease` | exists, no stable `trackKey`; identity is `id` plus release relation/title |
| `ObjectRelease` | physical/object archive node | exists, uses `releaseId` as unique code; no commerce fields found |

Important positive finding:

```text
MusicRelease remains canonical; no duplicate Release model exists.
```

## Model Groups

### Archive Foundation

- `Artist`
- `MusicRelease`
- `Track`
- `ObjectRelease`
- `Fragment`

### Brand Intelligence

- `BrandRule`
- `VisualRule`
- `LanguageRule`
- `ForbiddenEnergy`
- `VoiceProfile`
- `AudiencePersona`
- `ChannelRule`
- `SignalScoringRule`

### Content Graph

- `CampaignWorld`
- `VisualEnvironment`
- `MoodReference`
- `Asset`
- `AssetTag`
- `ArtistCampaignWorld`
- `MusicReleaseCampaignWorld`
- `TrackMoodReference`
- `CampaignWorldVisualEnvironment`
- `CampaignWorldMoodReference`
- `CampaignWorldAsset`
- `AssetTagAssignment`
- `ReleaseFragment`
- `ChannelFragment`

### Review And Governance

- `ReviewItem`
- `ApprovalDecision`
- `ApprovalComment`
- `RuleViolation`

### Controlled Generation / Draft Preparation

- `ConstraintBundle`
- `GenerationBriefConstraint`
- `ChannelCompositionProfile`
- `GenerationBrief`
- `PromptSection`
- `GenerationRequest`
- `GenerationOutput`
- `GenerationOutputEvaluation`

## Missing Registry Foundation Candidates

The following planning candidates do not exist yet:

- `ChannelPresence`
- `ExternalReference`
- `DistributionReference`
- `MusicReleaseLineage`
- `TrackLineage`
- `ArtistCredit`
- `ObjectVariant`
- `FulfillmentReference`
- `ManualOrderIntent`
- `OrderReviewRecord`
- `SignalObservationSnapshot`

This is expected for Phase 1. Do not add them until the additive schema proposal is approved.

## Enum Inventory Notes

Relevant current enums:

- `ArtistStatus`
- `ReleaseStatus`
- `Channel`
- `AssetType`
- `AssetSourceType`
- `CompatibilityVerdict`
- `ReviewStage`
- `ReviewStatus`
- `DecisionType`
- `ReviewSubjectType`
- `GenerationRequestStatus`
- `GenerationOutputStatus`
- `EvaluationVerdict`

Risk notes:

- `ReleaseStatus` mixes archive-ish terms and operational-sounding terms: `SIGNAL_PENDING`, `ACTIVE`, `CLOSED`, `ARCHIVED`, `HIDDEN`.
- `ReviewStage` includes `SCHEDULE_REVIEW` even though scheduling is explicitly out of scope.
- `GenerationRequestStatus` includes `READY_FOR_REVIEW` and `REVIEW_ACCEPTED`; existing governance docs already flag accepted/approval terminology risk.
- `Channel` includes signal surfaces but is not a `Platform` enum and does not model provider identity or authority.

## Canonical Key Inventory

Current identity/key fields:

| Entity | Current Key-Like Field | Risk |
| --- | --- | --- |
| `Artist` | `slug` | slug may be acting as canonical identity |
| `MusicRelease` | `releaseCode` | likely de facto archive code; no separate `releaseKey` |
| `Track` | none besides `id` | no stable `trackKey`; title/release relation may become identity by convention |
| `ObjectRelease` | `releaseId` | name implies relation/id, but value acts like object archive code |
| `ReviewItem` | `reviewKey` | review key exists and is unique |
| `GenerationBrief` | `briefKey` | draft/prep key exists and is unique |
| `GenerationRequest` | `requestKey` | request key exists and is unique |
| `GenerationOutput` | `outputKey` | output key exists and is unique |
| content graph records | `code` | many semantic and rule records use `code` as unique key |

Boundary risks:

- `Artist.slug` currently does double duty as route slug and unique identity.
- `ObjectRelease.releaseId` is a misleading name for an archive code.
- `Track` lacks a stable canonical key.
- `code` is used across many semantic/vocabulary/rule models without an explicit vocabulary authority model.

Required next classification:

```text
slug != canonical key
rename != new identity
provider ID != archive key
```

## State Inventory

Current state-like fields:

- `Artist.status`
- `ObjectRelease.status`
- `MusicRelease.status`
- `Fragment.active`
- rule/profile/persona/world/mood/asset `active`
- `ReviewItem.status`
- `GenerationRequest.status`
- `GenerationOutput.status`
- `RuleViolation.active`

Boundary risks:

- `ReleaseStatus.ACTIVE`, `CLOSED`, `ARCHIVED`, and `HIDDEN` can be read as archive state, workflow state, projection visibility, or commerce availability unless hardened.
- `active` appears on many rule/content graph entities and currently functions as projection/read-filter state.
- `ReviewItem.status` is materialized review state; governance docs correctly state it is not full approval truth.
- `GenerationRequest.status` and `GenerationOutput.status` are draft/prep states and must not become execution authority.

No automation-state fields were found in Prisma:

- no `queuedAt`
- no `scheduledFor`
- no `syncStatus`
- no `autoVerified`
- no `lastSyncedAt`
- no `retryCount`

## Temporal Inventory

Current temporal fields are mostly system bookkeeping:

- `createdAt`
- `updatedAt` only on `ReviewItem`

Missing temporal distinctions:

- no `effectiveFrom`
- no `observedAt`
- no `canonicalizedAt`
- no `supersededAt`
- no `withdrawnAt`
- no provenance timestamp fields

Boundary risk:

`createdAt` can be misread as historical reality if not explicitly documented in future contracts.

Required invariant for future proposal:

```text
effectiveFrom != createdAt
observedAt != canonicalizedAt
supersededAt != deletedAt
withdrawnAt != unavailableAt
```

## External Reference Inventory

No dedicated external reference model exists.

Current related fields:

- `Asset.sourceType`
- `Asset.referenceKey`
- `Channel`
- channel fragments and channel rules

No provider-specific database fields found for:

- Spotify IDs
- SoundCloud IDs
- TikTok IDs
- Instagram IDs
- YouTube IDs
- Apple Music IDs
- Stripe IDs
- Printful IDs

Boundary risk:

`Asset.referenceKey` is intentionally loose and may later absorb provider IDs, local file paths, public URLs, or symbolic references unless split by policy.

Required next proposal direction:

- introduce provider-neutral external references only after approval
- keep `sourceAuthority=false`
- do not treat external availability as entity existence

## Commerce And Fulfillment Inventory

No Stripe or Printful dependencies were found in package manifests.

No Prisma models found for:

- orders
- checkout
- payments
- Stripe products/prices/webhooks
- Printful products/variants/SKUs/orders
- fulfillment queue

Positive boundary:

`ObjectRelease` exists without commerce fields.

Risk:

Existing docs `docs/adr/0002-commerce-with-stripe-and-printful.md` describe future Stripe/Printful ownership in stronger operational terms than the newer registry governance direction. Reconcile later before commerce work so Printful/Stripe remain infrastructure, not archive authority.

## Media Asset Inventory

`Asset` currently stores:

- `code`
- `type`
- `sourceType`
- `title`
- `description`
- `referenceKey`
- `active`
- `weight`

Positive boundary:

No upload, CDN, storage provider, dimensions, media processing, or file metadata pipeline exists.

Risks:

- `Asset.referenceKey` can become a file path, provider reference, or symbolic key without stronger typing.
- `Asset.title` can be mistaken for canonical media title.
- `Asset.active` and `weight` can turn assets into projection priority if not bounded.
- no canonical-master versus derivative/projection asset distinction exists.

## Projection Inventory

Public web routes are static/curated projection surfaces under `apps/web/app`.

Current public projection sources:

- brand constants in `packages/brand/src/index.ts`
- static pages in `apps/web/app`
- static public assets under `apps/web/public/brand`

Boundary risks:

- `packages/brand/src/index.ts` defines `firstArtist.slug`, `firstArtist.archiveCode`, track `code` values, track titles, and public copy separately from Prisma seed values.
- Public route `/objects/sk-001` hardcodes object metadata and archive copy independent of `ObjectRelease`.
- Public music and artist pages use brand constants rather than registry reads.

This is acceptable for the current minimal public stack, but it is a projection/source split to resolve before registry-backed projections.

Required invariant:

```text
projection != source
projection selection != canonical importance
canonical projection != canonical source
```

## Runtime Route Surface

Fastify route files currently register GET routes only.

No API `post`, `put`, `patch`, or `delete` route registrations were found.

Current route areas:

- health
- artists
- objects
- music
- fragments
- brand intelligence
- content graph
- reviews
- generation
- evaluation
- drafts
- exports

Runtime repository access in `services/api/src/repositories.ts` uses read methods (`findUnique`, `findMany`) only.

No runtime Prisma writes were found outside seed/migration context.

## Admin / Internal Console Surface

Next.js admin files exist under:

```text
apps/web/app/admin
apps/web/app/admin/evaluation
```

Current observations:

- `apps/web/app/admin/page.tsx` calls `notFound()` when `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED !== "true"`.
- `apps/web/app/admin/evaluation/page.tsx` returns a `ConsoleUnavailable` component when disabled instead of `notFound()`.
- There is no shared `apps/web/app/admin/layout.tsx` gate in the tracked source tree inspected for this audit.
- Current working tree note: an untracked `apps/web/app/admin/layout.tsx` exists and appears to add shared `notFound()` gating, but it is not part of the tracked repository state and is not evaluated here as an accepted runtime change.

Boundary risk:

The internal console has per-page gating instead of highest-shared-layout gating. This is outside the schema inventory, but it is relevant to projection/runtime boundary discipline.

## Provider / Worker / Storage Dependency Inventory

Package manifests do not include:

- Stripe
- Printful
- TikTok
- Instagram
- Spotify
- SoundCloud
- OpenAI
- Anthropic
- worker libraries such as BullMQ, Agenda, Inngest, Temporal, QStash
- storage providers such as AWS SDK, Cloudinary, Vercel Blob, Firebase

Positive boundary:

Current dependency graph matches the no-provider/no-worker/no-storage posture.

## Mutation Inventory

Runtime API:

- no write routes found
- repository layer is read-only

Prisma schema:

- `ApprovalDecision` is append-only by convention, but Prisma does not enforce immutability by itself.
- `ReviewItem.updatedAt` exists and can support materialized review state updates later.
- no revision history or supersession models exist for canonical records.

Risk:

Future write routes could mutate canonical fields in place unless mutation governance is enforced at repository and route level.

## Seed Inventory

Seed data includes exact initial artist and tracks from `AGENTS.md`:

- `SHIBARI KAWAII`
- `PICK ME UP`
- `TUESDAY MORNING COMEDOWN`
- `ROPEMASTER`

Seed creates one track per music release and deletes/recreates tracks for each release during seed.

Risk:

Track identity is not stable across reseed because tracks are deleted and recreated. This is acceptable for seed/bootstrap today, but it conflicts with future stable `trackKey` and lineage requirements.

Seed also creates object studies:

- `SK-001`
- `SK-002`
- `SK-A001`

Risk:

`SK-A001` is also used as `firstArtist.archiveCode` in `packages/brand/src/index.ts`, creating potential archive-code namespace ambiguity between artist and object contexts.

## Primary Risk Findings

### R1: Slug And Canonical Identity Are Not Separated

`Artist.slug` is unique and used by API lookup. There is no `artistKey`.

Risk:

```text
slug == canonical identity
```

Needed later:

- add canonical artist identity key or explicitly freeze slug as immutable identity after governance review
- keep public URL slug changes separate from canonical identity

### R2: Track Has No Stable Canonical Key

`Track` has `id`, `releaseId`, `title`, `duration`, and `moodFragment`.

Risk:

Track identity can collapse into title plus release relation.

Needed later:

- `trackKey` or equivalent stable canonical identifier
- seed policy that does not destroy track identity once lineage matters

### R3: ObjectRelease Uses `releaseId` As Archive Code

`ObjectRelease.releaseId` is unique and appears to store values like `SK-001`.

Risk:

Field name implies a relational ID but behaves like archive code.

Needed later:

- classify as archive code or introduce clearer key/code semantics in additive proposal

### R4: Semantic Layer Already Exists And Needs Restraint

`CampaignWorld`, `MoodReference`, `VisualEnvironment`, `AssetTag`, fragments, and compatibility records already model semantic context.

Risk:

The system already has enough semantic surface for taxonomy drift.

Needed later:

- controlled vocabulary authority
- no broad new worlds/moods/fragments before registry keys and lineage are hardened

### R5: State Fields Mix Multiple Meanings By Name

`ReleaseStatus`, `active`, `ReviewStatus`, `GenerationRequestStatus`, and `GenerationOutputStatus` are all state-like.

Risk:

Workflow, projection, registry, and review state can collapse.

Needed later:

- state taxonomy before adding registry state
- classify each state field by authority and mutation semantics

### R6: Projection Source Split Is Real

Public pages and `packages/brand` constants contain artist, track, object, and archive copy independent of Prisma.

Risk:

Projection can become source unless registry-backed projections are designed deliberately.

Needed later:

- catalog projection policy
- migration path from brand constants to registry reads or explicit projection-copy ownership

### R7: Asset References Are Too Loose For Future Media Authority

`Asset.referenceKey` and `AssetSourceType` are intentionally broad.

Risk:

File paths, provider refs, symbolic refs, and canonical assets can collapse.

Needed later:

- media asset governance before upload/storage work
- canonical-master versus derivative/projection/provider-reference distinction

### R8: Admin/Internal Console Gating Is Per Page

Admin root gates with `notFound()`, evaluation page returns unavailable UI.

Risk:

Nested admin routes can diverge in exposure behavior without a shared layout boundary.

Needed later:

- shared admin layout gating before public deployment of internal surfaces

## Positive Findings

- No duplicate generic `Release` model.
- `MusicRelease` is the current music release archive node.
- `ObjectRelease` exists without commerce fields.
- API route surface is GET-only.
- Repository layer is read-only.
- No provider SDK dependencies.
- No worker, queue, scheduler, or webhook dependencies.
- No Stripe or Printful database models.
- No upload/storage/CDN pipeline.
- Evaluation and draft/export contracts carry explicit non-authority flags.
- `GenerationOutputStatus` has no `APPROVED` value.
- `ApprovalDecision` exists as separate decision history around `ReviewItem`.

## Additive Schema Proposal Preconditions

Do not propose a schema diff until these classifications are decided:

1. Whether to add `artistKey` or freeze `Artist.slug` as canonical identity.
2. Whether `MusicRelease.releaseCode` is the canonical release key, archive code, or both.
3. Whether `ObjectRelease.releaseId` should be renamed later by migration or supplemented with clearer additive fields.
4. Stable identity strategy for `Track`.
5. Registry state taxonomy versus current `ReleaseStatus` and `active` fields.
6. External reference strategy around `Asset.referenceKey`.
7. Controlled vocabulary authority for worlds, moods, environments, asset tags, fragments, and compatibility labels.
8. Projection-copy ownership for `packages/brand` constants and public static pages.
9. Revision/supersession strategy for canonical titles, archive codes, and lineage.

## Recommended Next Step

Prepare an additive schema diff proposal only after reviewing the primary risks above.

The first proposal should be narrow:

- canonical key hardening
- external reference separation
- channel presence references
- release/track lineage references
- no runtime changes
- no migrations applied
- no provider integrations
- no write routes

External channel implementation note:

- SoundCloud and Spotify should enter first as website embeds/listen links plus manual `ExternalReference` / `DistributionReference` candidates.
- Exact provider URLs must be supplied manually.
- No API integration, OAuth, provider SDK, auto-sync, or provider authority should be introduced in the first technical slice.
- See `docs/governance/external-channel-reference-strategy.md`.
