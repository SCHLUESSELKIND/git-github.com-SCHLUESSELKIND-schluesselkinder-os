# ROPEMASTER Release Structure

## Status

Planning only.

No seed change.
No schema change.
No migration.
No runtime change.
No projection change.
No website change.
No provider references.
No trackKey backfill is approved.

## Purpose

Correct the release and track structure before any canonical `trackKey` assignment or external reference mapping.

The previous working assumption was:

```text
SKM-001 -> one-track MusicRelease
SKM-002 -> one-track MusicRelease
SKM-003 -> one-track MusicRelease
```

That assumption is now blocked.

New planning truth:

```text
ROPEMASTER is the album / LP anchor.
The current three tracks are album-track previews, pre-release fragments, or singles.
The final LP target track count is 12.
```

## Core Invariants

```text
LP anchor != single release
preview track != standalone canonical release by default
trackKey backfill requires approved release hierarchy
releaseCode assignment != provider availability
album lineage != frontend grouping
```

No track identity work may continue until the release hierarchy is approved.

## Required Decisions

| Question | Current Decision State |
| --- | --- |
| Is ROPEMASTER the LP / album release? | Yes, planning truth. |
| Are PICK ME UP, TUESDAY MORNING COMEDOWN, and ROPEMASTER tracks on this LP? | Yes, planning truth. |
| Is the final LP target track count 12? | Yes, planning truth. |
| Do `SKM-001`, `SKM-002`, and `SKM-003` remain canonical `MusicRelease` rows? | Open; likely no or requires reclassification. |
| Do previews/singles need separate `MusicRelease` rows? | Open. |
| How is album-to-preview lineage modeled? | Open. |
| What is the canonical LP `releaseCode`? | Open. |
| What is the canonical trackKey system for the 12-track LP? | Open. |

## Superseded Planning Assumptions

The following documents contain candidate key planning based on the old one-track-per-release assumption:

- `docs/governance/canonical-trackkey-completion.md`
- `docs/governance/minimal-trackkey-backfill-proposal.md`

Their proposed keys must now be treated as blocked candidates, not implementation-ready identities.

Blocked candidates:

```text
track_sk_0001_01
track_sk_0002_01
track_sk_0003_01
```

Reason:

```text
one-track release assumption != approved LP hierarchy
```

## Temporary Structural Interpretation

Until a new structure is approved, use this conceptual model only:

```text
ROPEMASTER LP
-> album track preview: PICK ME UP
-> album track preview: TUESDAY MORNING COMEDOWN
-> album track preview: ROPEMASTER
-> nine further LP tracks pending
```

This is not a database model.

It is not a seed instruction.

It is not a releaseCode assignment.

## ReleaseCode Planning Questions

Open options to review later:

- one canonical LP `MusicRelease` with a new LP releaseCode
- separate preview/single `MusicRelease` rows linked to the LP through lineage
- existing `SKM-001..003` rows retained but reclassified as preview/single releases
- existing `SKM-001..003` rows deprecated or superseded after a governed migration

No option is approved here.

## TrackKey Planning Questions

Track keys should likely reflect the LP anchor and album track position after the LP releaseCode is approved.

Possible future shape:

```text
track_<lp_release_key>_01
track_<lp_release_key>_02
...
track_<lp_release_key>_12
```

This is illustrative only.

Do not use it for implementation.

## Lineage Questions

If previews/singles are represented separately from the LP, the system must define:

- whether preview releases point to LP tracks
- whether single releases are variants, fragments, or related releases
- whether an album track can supersede a preview track
- whether `SUPERSEDES` remains excluded from current `LineageType`
- whether preview lineage is modeled through `MusicReleaseLineage`, `TrackLineage`, or a later governance layer

No lineage model is approved here.

## External Reference Impact

External references must remain blocked until the hierarchy is approved.

Do not map provider URLs to:

- current titles
- old `SKM-001..003` assumptions
- proposed blocked track keys
- frontend labels
- provider metadata

Required invariant:

```text
external reference mapping waits for canonical hierarchy
```

## Implementation Block

No implementation may proceed for:

- `Track.trackKey` backfill
- seed update
- Prisma migration
- ExternalReference insertion
- DistributionReference insertion
- catalog projection extension
- website external links
- provider embeds

until the LP / preview / single structure is approved.

## Next Gate

Next gate should be a release hierarchy decision document.

It should decide:

- LP releaseCode
- status of current `SKM-001..003` rows
- whether previews/singles exist as releases
- 12-track numbering system
- trackKey shape
- lineage approach

Only after that decision may trackKey planning resume.
