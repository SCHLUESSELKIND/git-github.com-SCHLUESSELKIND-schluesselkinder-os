# Manual Reference Seed Planning

## Status

Planning document only.

This document is not a seed file.
This document does not authorize runtime insertion.
This document does not authorize Prisma writes.
This document does not authorize website rendering.
This document does not authorize provider integration.

No URL in this document should be treated as approved provider data.

## 1. Purpose

Phase 7C.1 prepares a controlled review surface for future SoundCloud, Spotify, YouTube, Instagram, and TikTok references.

The goal is to plan how exact external references may later enter the registry without allowing static frontend files, `packages/brand`, or provider metadata to become authority.

Required sequence:

```text
Registry inventory
-> reference planning
-> manual verification
-> projection eligibility
-> implementation
```

Forbidden sequence:

```text
URL discovery
-> frontend constant
-> public link
```

## 2. Canonical Preconditions

Before any external URL may be planned for insertion:

- `trackKey` must exist for track-level references.
- `releaseCode` must exist for release-level references.
- artist assignment must be canonical and review-confirmed.
- target entity identity must not be derived from slug, title, URL, handle, provider ID, or frontend route.
- reference type must be classified as `ExternalReference` or `DistributionReference`.
- `sourceAuthority` must remain `false`.

Current inventory facts:

- Current seed data defines `MusicRelease.releaseCode` values for `SKM-001`, `SKM-002`, and `SKM-003`.
- Current seed data creates tracks for those releases but does not assign `Track.trackKey`.
- `Track.trackKey` exists in the Prisma schema as an optional unique field.
- Existing route and repository tests use `track_sk_0001_01` as a fixture key, but test fixture keys are not seed approval.

Required invariant:

```text
test fixture key != approved seed key
slug != canonical key
title != canonical key
provider URL != canonical key
```

## 3. Reference Planning Table

Do not replace `PENDING_*` values until the corresponding manual review is complete.

| Track title | trackKey | releaseCode | Platform | URL | Reference Type | Projection Eligible? | Verification State | Review Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PICK ME UP | `PENDING_CANONICAL_TRACK_KEY` | `SKM-001` | `PENDING_PLATFORM_SELECTION` | `PENDING_MANUAL_CONFIRMATION` | `DistributionReference` if track/release endpoint is confirmed | No | `UNVERIFIED` | Release code exists in seed. Track key is not seed-backed yet. |
| TUESDAY MORNING COMEDOWN | `PENDING_CANONICAL_TRACK_KEY` | `SKM-002` | `PENDING_PLATFORM_SELECTION` | `PENDING_MANUAL_CONFIRMATION` | `DistributionReference` if track/release endpoint is confirmed | No | `UNVERIFIED` | Release code exists in seed. Track key is not seed-backed yet. |
| ROPEMASTER | `PENDING_CANONICAL_TRACK_KEY` | `SKM-003` | `PENDING_PLATFORM_SELECTION` | `PENDING_MANUAL_CONFIRMATION` | `DistributionReference` if track/release endpoint is confirmed | No | `UNVERIFIED` | Release code exists in seed. Track key is not seed-backed yet. |

Artist or channel-level references should use a separate review table before insertion.

| Artist / Channel | artistKey | Platform | URL | Reference Type | Projection Eligible? | Verification State | Review Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SHIBARI KAWAII | `PENDING_CANONICAL_ARTIST_KEY_CONFIRMATION` | `PENDING_PLATFORM_SELECTION` | `PENDING_MANUAL_CONFIRMATION` | `ExternalReference` or `ChannelPresence` after review | No | `UNVERIFIED` | Current seed uses slug/name. Artist key backfill must be confirmed before public projection. |

## 4. Guardrails

```text
planning row != approved insertion
URL presence != verification
provider existence != canonical approval
projection eligible != public by default
manual confirmation != provider authority
```

Do not commit:

- fake SoundCloud URLs
- fake Spotify URLs
- inferred platform handles
- inferred external IDs
- ISRCs, UPCs, dates, profile IDs, or provider titles not manually confirmed
- provider URLs in `packages/brand`
- provider URLs in static React components
- provider URLs in public frontend constants

## 5. Pending-State Semantics

Initial reference planning rows must remain:

- `pending`
- `unverified`
- `unmapped`
- `review-required`

They must not be described as:

- `verified`
- `active`
- `canonical`
- `published`
- `approved`
- `synced`

Reason:

```text
pending reference != registry fact
unverified URL != public signal
review-required != ready to render
```

## 6. Reference Type Decision Rules

Use `ExternalReference` when the external surface represents a general presence or identity context.

Examples:

- artist profile
- channel profile
- public account
- platform page

Use `DistributionReference` when the external surface represents a release, track, playlist, visualizer, or distribution endpoint.

Examples:

- track URL
- release URL
- album URL
- visualizer URL

Required separation:

```text
ExternalReference != DistributionReference
artist profile != track endpoint
platform account != release distribution
```

## 7. Projection Eligibility

Projection eligibility requires separate review after insertion planning.

Minimum approval inputs:

- exact URL
- exact target entity
- platform
- reference type
- verification state
- visibility state
- projection-safe label
- no provider authority claim

Default state:

```text
Projection Eligible? = No
```

Only after review may the value become:

```text
Projection Eligible? = Yes, public text link only
```

No first-pass projection may include:

- iframe
- embed
- player
- waveform
- autoplay
- provider SDK
- live provider fetch
- follower count
- stream count
- popularity label
- top-track sorting

## 8. Drift Prevention

Forbidden paths:

```text
packages/brand -> website
static component -> provider URL
frontend constants -> external authority
provider metadata -> registry overwrite
provider availability -> entity existence
```

Allowed future path:

```text
ExternalReference / DistributionReference
-> Catalog Projection
-> Website
```

The preserved drift patches must not be applied as implementation patches:

- `/tmp/schluesselkinder-drift-review.patch`
- `/tmp/schluesselkinder-shop-drift-review.patch`
- `/tmp/schluesselkinder-current-ui-drift.patch`

They are useful as evidence of the exact drift pattern this document blocks.

## 9. Implementation Gate

Implementation remains blocked until:

- canonical `artistKey` and `trackKey` decisions are confirmed
- exact URLs are manually supplied
- target mappings are reviewed
- projection eligibility is approved per row
- insertion path is registry-first
- no frontend direct provider links are present

Next technical phase should be manual seed or fixture review only.

It must not be website linking.
