# Canonical TrackKey Completion

## Status

Planning only.

No migration.
No seed change.
No provider references.
No UI change.
No projection change.
No runtime behavior change.

## Purpose

Prepare stable track identity before external reference mapping.

Track-level external references must not be planned against titles, slugs, provider URLs, frontend labels, or temporary fixture assumptions.

Required order:

```text
stable trackKey
-> reviewed target mapping
-> manual external reference planning
-> projection eligibility
-> implementation
```

Forbidden order:

```text
provider URL
-> title matching
-> implicit track identity
```

## Core Invariants

```text
trackKey != provider ID
trackKey != title slug
trackKey != frontend label
trackKey != SoundCloud URL
trackKey != Spotify URL
rename != new track identity
test fixture key != approved seed key
```

Track identity must survive:

- title corrections
- spelling changes
- release copy changes
- provider URL changes
- provider takedowns
- frontend route changes
- future distribution reference changes

## Inventory Table

Current seed inspection shows one seeded track per seeded music release.

The current seed creates tracks for `SKM-001`, `SKM-002`, and `SKM-003`, but does not assign `Track.trackKey`.

| releaseCode | current title | proposed trackKey | confidence | notes |
| --- | --- | --- | --- | --- |
| `SKM-001` | PICK ME UP | `track_sk_0001_01` | pending | Verify current seed title, release mapping, and one-track release shape before assignment. |
| `SKM-002` | TUESDAY MORNING COMEDOWN | `track_sk_0002_01` | pending | Verify current seed title, release mapping, and one-track release shape before assignment. |
| `SKM-003` | ROPEMASTER | `track_sk_0003_01` | pending | Verify current seed title, release mapping, and one-track release shape before assignment. |

## Proposed Initial Candidates

```text
SKM-001 | PICK ME UP | track_sk_0001_01 | pending | verify current seed
SKM-002 | TUESDAY MORNING COMEDOWN | track_sk_0002_01 | pending | verify current seed
SKM-003 | ROPEMASTER | track_sk_0003_01 | pending | verify current seed
```

These are proposed candidates only.

They are not assigned keys.

## Guardrails

```text
planning row != approved backfill
proposed key != assigned key
track title != identity
release position != provider truth
releaseCode != provider authority
```

Do not use:

- SoundCloud URL
- Spotify URL
- provider title
- provider ID
- frontend text
- title slug
- visual order on the website
- test-only fixture assumptions

as a source for `trackKey`.

## Required Before Implementation

- confirm current seed titles
- confirm releaseCode mapping
- confirm one track per release
- confirm no duplicate track identities
- approve backfill method
- decide whether backfill happens through seed update, migration SQL, or manual dev database operation
- confirm tests do not imply seed authority

## Backfill Method Decision

No backfill method is approved in this document.

Potential methods require a separate implementation gate:

- additive seed update
- migration SQL backfill
- manual dev-only database operation

Production backfill requires separate approval.

## Non-Goals

Do not add:

- external URLs
- provider IDs
- `ExternalReference` rows
- `DistributionReference` rows
- channel presences
- projection fields
- website links
- embeds
- provider SDKs
- OAuth
- provider verification

## Next Gate

After this planning document is approved, the next technical gate may be a minimal trackKey backfill proposal.

That gate must still exclude:

- provider data
- public rendering
- projection extension
- runtime exposure
- external reference insertion
