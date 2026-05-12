# ROPEMASTER Release Hierarchy Decision

## Status

Planning and governance decision document only.

No seed change.
No schema change.
No migration.
No runtime change.
No projection change.
No website change.
No provider references.
No trackKey backfill is implemented here.

This document decides the target hierarchy that future implementation proposals must follow.

## Decision Summary

ROPEMASTER is the canonical LP / album anchor.

Recommended canonical LP releaseCode:

```text
SKM-LP-001
```

Recommended LP trackKey form:

```text
track_skm_lp_001_01
track_skm_lp_001_02
...
track_skm_lp_001_12
```

Current `SKM-001`, `SKM-002`, and `SKM-003` must not be treated as canonical one-track LP releases.

They may remain as preview/single/signal releases only if future review confirms they were or will be publicly distributed as separate release surfaces.

## Core Invariants

```text
ROPEMASTER LP = canonical MusicRelease anchor
LP track != standalone release by default
preview release != album track authority
single distribution != LP hierarchy authority
trackKey shape follows approved LP hierarchy
```

External provider state must not decide the hierarchy.

## LP ReleaseCode

Decision:

```text
SKM-LP-001
```

Rationale:

- explicitly marks LP scope
- avoids overloading `SKM-001`, `SKM-002`, or `SKM-003`
- keeps the LP anchor separate from preview/single signal codes
- provides a stable base for 12 LP track keys

Status:

Planning-approved for future implementation proposal.

Not yet inserted into seed data.

## Status Of Current `SKM-001..003`

Decision:

`SKM-001`, `SKM-002`, and `SKM-003` should be treated as legacy preview/single/signal-release candidates, not the canonical LP structure.

They should remain implementation-blocked until review answers:

- were they publicly distributed as separate releases?
- should they remain `MusicRelease` rows?
- should they become preview/single releases related to `SKM-LP-001`?
- should any be deprecated or superseded later?

Interim rule:

```text
SKM-001..003 != LP hierarchy
```

## Preview / Single Release Policy

Decision:

Preview/single `MusicRelease` rows are allowed only if they represent real public distribution or a deliberately approved archive signal.

They must not be created merely because a track exists on the LP.

Allowed later:

- preview release row for a real public pre-release
- single release row for a real public single
- archival signal release if approved by governance

Forbidden:

- one release row per LP track by default
- frontend grouping treated as release hierarchy
- provider URL treated as release existence
- automatic preview release creation

## LP Track Numbering

Decision:

LP tracks should be numbered by album position after final track order is approved.

Target count:

```text
12 LP tracks
```

Current preview tracks should be mapped to final LP positions only after track order review.

No current title gets a final LP position in this document.

## TrackKey System

Decision:

Future LP track keys should use LP releaseCode ancestry and two-digit LP position:

```text
track_skm_lp_001_01
track_skm_lp_001_02
track_skm_lp_001_03
track_skm_lp_001_04
track_skm_lp_001_05
track_skm_lp_001_06
track_skm_lp_001_07
track_skm_lp_001_08
track_skm_lp_001_09
track_skm_lp_001_10
track_skm_lp_001_11
track_skm_lp_001_12
```

These keys remain planned candidates until implementation approval.

Required invariant:

```text
LP position key != provider track number
LP position key != title order in frontend
LP position key != SoundCloud order
LP position key != Spotify order
```

## Current Preview Track Mapping

The three known tracks are treated as LP-track preview candidates:

| Known title | LP relationship | Final LP position | Future trackKey |
| --- | --- | --- | --- |
| PICK ME UP | preview / pre-release candidate | pending | pending |
| TUESDAY MORNING COMEDOWN | preview / pre-release candidate | pending | pending |
| ROPEMASTER | preview / title-track candidate | pending | pending |

No final trackKey is assigned to these titles here.

## Lineage Approach

Decision:

Use existing lineage types only if preview/single releases are retained as separate `MusicRelease` rows.

Recommended initial relation:

```text
RELATED
```

or, if governance needs stronger structure later:

```text
VARIANT
FRAGMENT
```

`SUPERSEDES` remains excluded from `LineageType`.

Reason:

Supersession is historical rewrite governance. It should not be smuggled into LP planning before revision and archival-retention rules are approved.

Required invariant:

```text
preview lineage != historical overwrite
related preview != superseded entity
```

## Implementation Implications

Future implementation proposal should likely:

1. add or update seed representation for canonical LP `SKM-LP-001`
2. model 12 LP tracks under that canonical LP
3. decide whether to retain `SKM-001..003` as preview/single releases
4. add lineage only if separate preview/single releases are retained
5. keep `SUPERSEDES` out of the implementation

No implementation is approved here.

## External Reference Impact

External reference planning remains blocked until:

- LP release row is approved
- LP track order is approved
- trackKey assignment is approved
- preview/single release status is approved

Do not map SoundCloud, Spotify, YouTube, TikTok, or Instagram references to:

- `SKM-001..003` as LP assumptions
- blocked `track_sk_0001_01..0003_01` candidates
- titles alone
- frontend order
- provider order

## Blocked Prior Candidates

The following prior candidates remain blocked:

```text
track_sk_0001_01
track_sk_0002_01
track_sk_0003_01
```

They were based on the superseded one-track-per-release assumption.

## Next Gate

Next gate should be a seed-shape proposal, not implementation.

It should propose:

- how `SKM-LP-001` is represented in `MusicRelease`
- how 12 LP `Track` rows are represented
- whether current `SKM-001..003` rows are retained, reclassified, or replaced
- whether lineage rows are needed now
- exact regression-test scope

Still forbidden in the next gate unless separately approved:

- provider URLs
- external references
- projection extension
- website rendering
- runtime reconciliation
- migrations against production data
