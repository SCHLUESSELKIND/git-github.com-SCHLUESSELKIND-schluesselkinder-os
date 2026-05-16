# Additive Schema Diff Proposal

## Status

Planning document only.

No Prisma schema has been changed.
No migration has been generated.
No migration has been applied.
No runtime code has been changed.
No API route has been added.
No provider integration has been added.

## 1. Scope

This proposal is the narrow Phase 2 bridge from governance and inventory into a future additive Prisma diff.

It is based on:

- `docs/governance/registry-inventory-audit.md`
- `docs/governance/external-channel-reference-strategy.md`
- existing Prisma schema in `packages/db/prisma/schema.prisma`

Proposal 1 covers only:

- `artistKey`
- `trackKey`
- `ChannelPresence`
- `ExternalReference`
- `DistributionReference`
- `MusicReleaseLineage`
- `TrackLineage`

The proposal is additive only. It does not rename, delete, migrate, backfill, or expose runtime behavior.

## 2. Non-Goals

Do not include in Proposal 1:

- Commerce
- Printful
- Stripe
- `SignalObservationSnapshot`
- `GPTDraftSuggestion`
- Asset pipeline
- Uploads
- Runtime API
- Admin UI
- OAuth
- provider SDKs
- provider webhooks
- sync jobs
- workers
- queues
- scheduling
- analytics ingestion
- provider write APIs
- automatic verification
- fake seed data

Admin-gating risk is real but separate. It must not be mixed into this schema diff proposal.

## 3. Existing Model Decisions

### Artist

Current:

- `Artist.id`
- `Artist.slug`
- `Artist.name`
- `Artist.symbol`
- `Artist.status`

Decision:

`Artist.slug` must not remain the only canonical identity surface.

Proposal:

- add `artistKey String? @unique` first
- backfill manually in a later approved migration
- only make non-null after data is verified

Reason:

```text
slug != canonical key
rename != new identity
```

### MusicRelease

Current:

- `MusicRelease.releaseCode String @unique`

Decision:

Do not create a duplicate `Release` model.

`releaseCode` should be treated as an archive/catalog code unless explicitly approved as canonical key.

Proposal:

- keep `releaseCode`
- do not add `releaseKey` in Proposal 1 unless governance decides `releaseCode` cannot safely carry canonical release identity
- use `MusicRelease.id` for internal relations in new lineage/reference models for now

Reason:

`MusicRelease` is already the canonical music release node. Proposal 1 should avoid unnecessary identity churn.

### Track

Current:

- `Track.id`
- `Track.releaseId`
- `Track.title`
- no stable public/internal key

Decision:

Track needs stable identity before lineage and provider references become useful.

Proposal:

- add `trackKey String? @unique`
- backfill manually in a later approved migration
- only make non-null after existing track inventory is verified

Reason:

Track identity must not collapse into title plus release relation.

### ObjectRelease

Current:

- `ObjectRelease.releaseId String @unique`

Decision:

`releaseId` is semantically misleading because it behaves like an archive code.

Proposal:

- no rename in Proposal 1
- do not touch object schema in Proposal 1 unless a minimal `archiveCode` classification note is added in comments/docs only
- revisit `objectReleaseKey` / `archiveCode` in a later object-commerce proposal

Reason:

Object work is out of scope for the first registry-reference diff.

### Asset

Current:

- `Asset.sourceType`
- `Asset.referenceKey`

Decision:

`Asset.referenceKey` must not become the external provider reference catch-all.

Proposal:

- leave `Asset` unchanged in Proposal 1
- add `ExternalReference` for provider-neutral links
- do not connect asset pipeline, file storage, or canonical media authority yet

Reason:

```text
asset != provider copy
asset != projection
provider URL != canonical identity
```

## 4. Additive Field Proposals

### `Artist.artistKey`

Potential Prisma shape:

```prisma
model Artist {
  artistKey String? @unique
}
```

Mutation strategy:

- immutable after assignment
- governance-created
- not derived from slug
- not provider-derived

Backfill example:

```text
artist_shibari_kawaii
```

Example is illustrative. Final seed value requires approval.

### `Track.trackKey`

Potential Prisma shape:

```prisma
model Track {
  trackKey String? @unique
}
```

Mutation strategy:

- immutable after assignment
- governance-created
- not title-derived without review
- not provider-derived

Backfill examples:

```text
track_sk_0001_01
track_sk_0002_01
track_sk_0003_01
```

Examples are illustrative. Final seed values require approval.

## 5. Additive Model Proposals

### ChannelPresence

Purpose:

Represents public platform identity as a signal surface, not provider authority.

Potential Prisma shape:

```prisma
model ChannelPresence {
  id            String            @id @default(cuid())
  presenceKey   String            @unique
  platform      Platform
  handle        String?
  profileUrl    String?
  verifiedState VerificationState @default(UNVERIFIED)
  visibility    ChannelVisibility @default(INTERNAL)
  artistId      String?
  createdAt     DateTime          @default(now())

  artist Artist? @relation(fields: [artistId], references: [id])
}
```

Boundary:

```text
channel presence != artist authority
profile URL != canonical identity
```

### ExternalReference

Purpose:

Provider-neutral reference to external URLs/IDs for artists, tracks, music releases, object releases, or channel presences.

Potential Prisma shape:

```prisma
model ExternalReference {
  id                  String            @id @default(cuid())
  referenceKey        String            @unique
  platform            Platform
  url                 String
  externalId          String?
  verifiedState       VerificationState @default(UNVERIFIED)
  sourceAuthority     Boolean           @default(false)
  artistId            String?
  musicReleaseId      String?
  trackId             String?
  objectReleaseId     String?
  channelPresenceId   String?
  createdAt           DateTime          @default(now())

  artist          Artist?          @relation(fields: [artistId], references: [id])
  musicRelease    MusicRelease?    @relation(fields: [musicReleaseId], references: [id])
  track           Track?           @relation(fields: [trackId], references: [id])
  objectRelease   ObjectRelease?   @relation(fields: [objectReleaseId], references: [id])
  channelPresence ChannelPresence? @relation(fields: [channelPresenceId], references: [id])
}
```

Required rule:

Exactly one target relation should be set. Prisma cannot fully enforce that check portably without additional DB constraints; enforce through seed/repository policy before writes exist.

Boundary:

```text
external reference != source of truth
sourceAuthority must remain false
external availability != entity existence
```

### DistributionReference

Purpose:

Describes external distribution placement or release presence. It does not upload, publish, sync, or distribute.

Potential Prisma shape:

```prisma
model DistributionReference {
  id                String            @id @default(cuid())
  distributionKey   String            @unique
  platform          Platform
  url               String?
  externalId        String?
  verifiedState     VerificationState @default(UNVERIFIED)
  sourceAuthority   Boolean           @default(false)
  musicReleaseId    String?
  trackId           String?
  createdAt         DateTime          @default(now())

  musicRelease MusicRelease? @relation(fields: [musicReleaseId], references: [id])
  track        Track?        @relation(fields: [trackId], references: [id])
}
```

Boundary:

```text
distribution reference != distribution authority
Spotify endpoint != release truth
SoundCloud player != release truth
```

### MusicReleaseLineage

Purpose:

Explicit release-to-release relationship. Not inferred from provider references, projection grouping, or popularity.

Potential Prisma shape:

```prisma
model MusicReleaseLineage {
  id              String      @id @default(cuid())
  lineageKey      String      @unique
  parentReleaseId String
  childReleaseId  String
  relationType    LineageType
  note            String?
  createdAt       DateTime    @default(now())

  parentRelease MusicRelease @relation("ParentMusicReleaseLineage", fields: [parentReleaseId], references: [id])
  childRelease  MusicRelease @relation("ChildMusicReleaseLineage", fields: [childReleaseId], references: [id])

  @@unique([parentReleaseId, childReleaseId, relationType])
}
```

Boundary:

```text
lineage != convenience grouping
lineage relation != identity collapse
```

### TrackLineage

Purpose:

Explicit track-to-track relationship for edits, mixes, variants, fragments, or later supersession context.

Potential Prisma shape:

```prisma
model TrackLineage {
  id            String      @id @default(cuid())
  lineageKey    String      @unique
  parentTrackId String
  childTrackId  String
  relationType  LineageType
  note          String?
  createdAt     DateTime    @default(now())

  parentTrack Track @relation("ParentTrackLineage", fields: [parentTrackId], references: [id])
  childTrack  Track @relation("ChildTrackLineage", fields: [childTrackId], references: [id])

  @@unique([parentTrackId, childTrackId, relationType])
}
```

Boundary:

```text
version relation != duplicate merge
lineage must be reviewed
```

## 6. Enum Proposals

### Platform

Potential Prisma shape:

```prisma
enum Platform {
  SOUNDCLOUD
  SPOTIFY
  TIKTOK
  INSTAGRAM
  APPLE_MUSIC
  YOUTUBE
  MANUAL
  OTHER
}
```

Note:

Existing `Channel` should remain for content/channel context. `Platform` is for external reference identity.

### VerificationState

Potential Prisma shape:

```prisma
enum VerificationState {
  UNVERIFIED
  MANUALLY_VERIFIED
  EXTERNALLY_OBSERVED
  STALE
  UNAVAILABLE
}
```

Boundary:

```text
verified != source authority
unavailable != entity deleted
```

### ChannelVisibility

Potential Prisma shape:

```prisma
enum ChannelVisibility {
  INTERNAL
  PUBLIC
  HIDDEN
}
```

Boundary:

```text
visibility != importance
hidden != deleted
```

### LineageType

Potential Prisma shape:

```prisma
enum LineageType {
  ORIGINAL
  VARIANT
  EDIT
  MIX
  REMIX
  REMASTER
  FRAGMENT
  SUPERSEDES
  RELATED
}
```

Risk:

`SUPERSEDES` may overlap with a future historical revision/supersession layer. Include only if governance wants lineage to carry this relation now.

## 7. Migration Risks

### Optional-First Fields

`artistKey` and `trackKey` should start nullable to avoid unsafe immediate backfill.

Risk if non-null immediately:

- migration requires invented keys
- seed order can break
- unstable existing tracks become falsely canonical

### Relation Ambiguity

`ExternalReference` has multiple optional target relations.

Risk:

- a row can accidentally point to multiple entities or none

Mitigation:

- no write routes in this phase
- seed/manual creation only after validation helper exists
- consider DB check constraint later if supported and approved

### `sourceAuthority=false`

Risk:

Future code may set `sourceAuthority=true`.

Mitigation:

- default false
- document as invariant
- governance regression test before any write path exists

### Existing Status Drift

This proposal does not solve `ReleaseStatus` or `active` ambiguity.

Mitigation:

- do not add registry state in Proposal 1
- classify state separately before adding new status fields

### Existing Projection Split

This proposal does not move `packages/brand` constants into Prisma.

Mitigation:

- keep public web as curated projection for now
- no registry-backed projection migration in Proposal 1

### Admin Gating

This proposal does not address admin/internal console route exposure.

Mitigation:

- handle as separate runtime hardening issue
- do not mix admin route changes into schema diff

## 8. Rejected Alternatives

### Create Generic `Release`

Rejected.

Reason:

`MusicRelease` already exists as the canonical music release node. A generic `Release` model would create split authority.

### Rename `ObjectRelease.releaseId` Now

Rejected for Proposal 1.

Reason:

Renaming requires migration and backfill semantics outside this narrow registry-reference scope.

### Store SoundCloud/Spotify URLs In `Track`

Rejected.

Reason:

Provider references should not become track fields or canonical identity.

### Reuse `Asset.referenceKey` For Provider URLs

Rejected.

Reason:

`Asset.referenceKey` is too broad and should not absorb external channel identity.

### Add `SignalObservationSnapshot`

Rejected for Proposal 1.

Reason:

Observation can wait until references and distribution mapping exist.

### Add Commerce/Fulfillment Models

Rejected.

Reason:

Printful and Stripe remain infrastructure-only future concerns.

### Add Runtime Registry API

Rejected.

Reason:

Schema proposal must be approved before runtime API work.

## 9. Approval Checklist

Before editing `schema.prisma`, approve:

- `Artist.artistKey` optional-first strategy
- `Track.trackKey` optional-first strategy
- whether `MusicRelease.releaseCode` remains archive code only
- whether `ObjectRelease.releaseId` remains untouched in Proposal 1
- `Platform` enum values
- `VerificationState` enum values
- `ChannelVisibility` enum values
- `LineageType` enum values
- `ExternalReference` one-target policy
- `DistributionReference` relation targets
- whether `sourceAuthority` is allowed as a DB field or should be omitted and treated as a constant invariant
- whether `SUPERSEDES` belongs in `LineageType` now or later

Explicitly confirm:

- no migration will be applied during schema proposal review
- no runtime route will be added
- no provider SDK will be added
- no SoundCloud/Spotify placeholder URLs will be seeded
- no admin/internal-console runtime change is part of this schema proposal
