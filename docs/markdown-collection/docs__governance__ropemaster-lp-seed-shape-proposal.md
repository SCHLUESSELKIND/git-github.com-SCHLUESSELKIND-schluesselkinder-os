# ROPEMASTER LP Seed Shape Proposal

## Status

Planning only.

No seed change.
No schema change.
No migration.
No runtime change.
No projection change.
No website change.
No provider references.
No external reference insertion.

## Purpose

Define the safest future seed shape for the ROPEMASTER LP after the release hierarchy decision.

This document does not authorize implementation.

It prepares the next implementation proposal by separating confirmed registry entities from planned LP structure.

## Core Decision

`SKM-LP-001` is planned as the canonical ROPEMASTER LP `MusicRelease`.

The first LP seed slice should contain:

```text
SKM-LP-001 canonical MusicRelease
+ known Track rows only
+ planned LP slots as governance notation only
```

It should not immediately create 12 real `Track` rows.

Required invariant:

```text
planned slot != registry track
missing title != placeholder entity
LP target count != seed row count
trackKey reservation != assigned identity
```

## Recommended Seed Shape

Recommended first seed shape:

| Entity | Seed Status | Notes |
| --- | --- | --- |
| `MusicRelease` `SKM-LP-001` | proposed | canonical ROPEMASTER LP anchor |
| Known LP track: PICK ME UP | proposed Track row | final LP position pending |
| Known LP track: TUESDAY MORNING COMEDOWN | proposed Track row | final LP position pending |
| Known LP track: ROPEMASTER | proposed Track row | final LP position pending |
| LP slots 4-12 | governance notation only | no seed rows until title and position are approved |

This keeps the Registry from creating false certainty for unknown material.

## Known Track Rows

Known tracks may become real `Track` rows under `SKM-LP-001` only after implementation approval.

| Known title | Proposed parent release | Proposed row type | Final LP position | Proposed trackKey |
| --- | --- | --- | --- | --- |
| PICK ME UP | `SKM-LP-001` | `Track` | pending | pending |
| TUESDAY MORNING COMEDOWN | `SKM-LP-001` | `Track` | pending | pending |
| ROPEMASTER | `SKM-LP-001` | `Track` | pending | pending |

No trackKey is assigned in this document.

Reason:

Final LP position remains pending.

## Planned LP Slots

The final LP target count is 12 tracks.

Slots 4-12 should remain planning notation until title, position, and identity are reviewed.

| LP slot | Registry entity? | Reason |
| --- | --- | --- |
| 01 | maybe after known-track position approval | title/position still pending |
| 02 | maybe after known-track position approval | title/position still pending |
| 03 | maybe after known-track position approval | title/position still pending |
| 04 | no | planned slot only |
| 05 | no | planned slot only |
| 06 | no | planned slot only |
| 07 | no | planned slot only |
| 08 | no | planned slot only |
| 09 | no | planned slot only |
| 10 | no | planned slot only |
| 11 | no | planned slot only |
| 12 | no | planned slot only |

No placeholder titles should be seeded.

No placeholder tracks should be seeded.

## TrackKey Reservation

Future LP trackKey pattern remains:

```text
track_skm_lp_001_01
track_skm_lp_001_02
...
track_skm_lp_001_12
```

These are reserved planning shapes, not assigned identities.

Do not assign a trackKey until:

- track title is known
- LP position is approved
- parent LP release is approved in seed shape
- no duplicate track identity exists

## Current `SKM-001..003`

`SKM-001`, `SKM-002`, and `SKM-003` remain blocked signal-release candidates.

Recommended first LP seed slice:

- do not delete them
- do not reclassify them
- do not add lineage yet
- do not use them as LP hierarchy

Reason:

Their preview/single/signal status still requires review.

## Lineage

No lineage should be inserted in the first LP seed slice.

Reasons:

- preview/single release status is not approved
- LP track positions are not approved
- `SUPERSEDES` remains excluded
- lineage would imply a stronger historical relationship than currently governed

Required invariant:

```text
no lineage before release status review
```

## Regression Test Scope

Future implementation tests should verify only:

- `SKM-LP-001` exists as the canonical LP release
- only known approved LP tracks are seeded as real `Track` rows
- planned slots are not persisted as fake tracks
- no provider URLs or external IDs are involved
- current `SKM-001..003` rows are not treated as the LP hierarchy

Tests must not require:

- 12 persisted Track rows
- placeholder titles
- provider mappings
- external references
- projection rendering
- frontend order

## Forbidden In First Implementation Slice

- 12 real Track rows
- placeholder Track rows
- placeholder titles
- fake durations
- fake mood/world assignments
- provider URLs
- provider IDs
- ExternalReference rows
- DistributionReference rows
- lineage rows
- projection extension
- website rendering changes
- runtime reconciliation

## Next Gate

Next gate should be:

```text
Phase 7C.4d - LP Seed Update Proposal
```

That proposal may define an exact seed diff, but it must still remain reviewable before code changes.
