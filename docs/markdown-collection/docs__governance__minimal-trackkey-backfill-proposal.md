# Minimal TrackKey Backfill Proposal

## Status

Planning only.

No implementation approved.
No seed change.
No migration.
No runtime change.
No projection change.
No provider references.
No external reference insertion.

## Purpose

Define the smallest safe path for completing canonical `Track.trackKey` values before any external reference mapping begins.

The architectural decision:

```text
trackKey backfill = canonical registry stabilization
```

not:

```text
trackKey backfill = provider reconciliation
```

This proposal exists to prevent later SoundCloud, Spotify, YouTube, Instagram, or TikTok references from being matched by title, URL, provider metadata, or frontend labels.

## Recommended Method

Preferred method:

```text
seed update + explicit regression test
```

Rationale:

- seeded tracks already exist
- current seeds create the track rows directly
- keys belong to canonical registry identity
- seed update keeps the canonical identity near the seeded entity definition
- avoids unknown SQL targeting
- avoids provider coupling
- avoids runtime reconciliation logic
- avoids frontend-derived identity

This is a proposal only. It does not approve the seed update yet.

## Rejected Alternatives

Rejected:

- provider-derived key generation
- title-slug-derived key generation
- SoundCloud reconciliation
- Spotify reconciliation
- automatic migration SQL generation
- runtime-generated `trackKey`
- frontend-generated `trackKey`
- test-fixture-derived seed assignment without review

Reasons:

```text
provider ID != trackKey
title slug != trackKey
runtime generation != canonical authority
fixture key != seed approval
```

## Proposed Approved Candidates

These candidates are repeated from `canonical-trackkey-completion.md`.

| releaseCode | current title | proposed trackKey | status |
| --- | --- | --- | --- |
| `SKM-001` | PICK ME UP | `track_sk_0001_01` | candidate |
| `SKM-002` | TUESDAY MORNING COMEDOWN | `track_sk_0002_01` | candidate |
| `SKM-003` | ROPEMASTER | `track_sk_0003_01` | candidate |

Required invariant:

```text
candidate != approved assignment
proposed key != assigned key
```

Approval must explicitly confirm these candidates before implementation.

## Regression Test Requirement

A later implementation must include a regression test that verifies only registry identity completeness.

Required test intent:

```text
all seeded tracks have stable non-null trackKey
```

The test may assert:

- seeded track records include non-null `trackKey`
- each seeded `trackKey` is unique
- expected seeded release/title pairs map to expected candidate keys after approval

The test must not assert:

- provider matching
- URL mapping
- SoundCloud presence
- Spotify presence
- title parsing behavior
- frontend order
- projection eligibility
- external reference insertion

## Implementation Boundaries

Still forbidden in this proposal:

- editing `packages/db/prisma/seed.ts`
- creating or applying a Prisma migration
- inserting `ExternalReference`
- inserting `DistributionReference`
- adding provider URLs
- adding provider IDs
- changing catalog projection
- changing website rendering
- adding API routes
- adding provider SDKs
- adding OAuth

## Required Before Implementation

- approve the three candidate keys
- confirm current seed titles
- confirm `releaseCode` mapping
- confirm one track per seeded release
- confirm no duplicate track identities
- approve the exact seed update diff
- approve the exact regression test scope

## Next Gate

The next gate may be:

```text
Phase 7C.4 - TrackKey Seed Backfill Implementation
```

That gate should remain limited to:

- `packages/db/prisma/seed.ts`
- a focused regression test

and must still exclude:

- provider data
- external references
- public rendering
- projection extension
- runtime reconciliation
