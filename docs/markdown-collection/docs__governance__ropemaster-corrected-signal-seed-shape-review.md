# ROPEMASTER Corrected Signal Seed Shape Review

## Status

Decision / review document only.

No seed diff.
No seed write.
No migration.
No runtime change.
No projection change.
No frontend change.
No provider references.
No external references.
No lineage rows.

## Purpose

Decide the corrected first seed-shape direction after the ROPEMASTER signal release plan correction.

The seed shape must preserve the LP-centered registry model while allowing current preview/signal releases to exist without becoming LP authority.

## Decisions

| Entity | First seed role |
| --- | --- |
| `SKM-LP-001` | canonical LP anchor |
| `SKM-SIG-001` | ROPEMASTER preview/signal `MusicRelease` |
| `SKM-SIG-002` | TINDERMATCH preview/signal `MusicRelease` |
| PICK ME UP | on hold / no public projection |
| TUESDAY MORNING COMEDOWN | on hold / no public projection |

Required invariants:

```text
preview MusicRelease != LP hierarchy
preview Track != final LP track identity
preview release != final LP track order
album anchor != public distribution state
on hold != withdrawn
on hold != deleted
on hold != public projection
```

## Entity Shape Decision

Preview/signal releases should be modeled as both a `MusicRelease` and a child `Track`.

Recommended first seed-shape direction:

| MusicRelease releaseCode | MusicRelease title | Track title | Role |
| --- | --- | --- | --- |
| `SKM-LP-001` | ROPEMASTER LP | none in first slice | canonical album anchor |
| `SKM-SIG-001` | ROPEMASTER | ROPEMASTER | first preview/signal release |
| `SKM-SIG-002` | TINDERMATCH | TINDERMATCH | second preview/signal release |

Reason:

A preview/signal release needs a release wrapper and a track underneath it. Otherwise release-level references and track-level references collapse into one implicit authority layer.

Required invariant:

```text
release reference != track reference
```

## LP Anchor Boundary

`SKM-LP-001` should exist as the canonical LP anchor.

The first seed slice should not create LP track rows under `SKM-LP-001`.

Reason:

Current preview/signal tracks are not approved as final LP hierarchy or final LP order.

Required invariants:

```text
SKM-LP-001 != public album release
SKM-LP-001 != finalized tracklist
current signal != album completion
```

## Preview / Signal Boundary

`SKM-SIG-001` and `SKM-SIG-002` are signal releases for the ROPEMASTER LP context.

They do not define:

- final LP track order
- final LP track keys
- LP sequencing
- LP completion
- provider mapping
- public distribution authority

Required invariant:

```text
LP plus preview signals != isolated singles architecture
```

## On-Hold Boundary

PICK ME UP and TUESDAY MORNING COMEDOWN are on hold.

They must not be public projection candidates in the next seed slice.

They must not receive:

- active preview/signal release rows
- LP track rows
- trackKeys
- external references
- distribution references
- provider URLs
- embeds
- lineage rows

Required invariant:

```text
on hold material != catalog candidate
```

## Catalog Projection Eligibility Blocker

Catalog projection eligibility must be decided before any seed write.

Current risk:

`/catalog/music-releases` can expose all seeded `MusicRelease` rows.

Therefore, seed insertion alone could accidentally make:

- `SKM-LP-001`
- `SKM-SIG-001`
- `SKM-SIG-002`

visible through catalog routes.

Required invariants:

```text
seed row != public projection approval
catalog visibility != release approval
projection eligibility != seed existence
```

Before seed implementation, one of these must be explicitly approved:

1. keep seed implementation dev/local only until projection eligibility exists
2. add a projection eligibility guard before seed write
3. choose a status/filtering strategy that prevents unintended catalog exposure

This document does not approve any of those implementation paths.

## Proposed Seed Status Direction

Recommended review direction, subject to projection eligibility decision:

| Entity | Proposed status |
| --- | --- |
| `SKM-LP-001` | `ReleaseStatus.SIGNAL_PENDING` |
| `SKM-SIG-001` | pending explicit decision |
| `SKM-SIG-002` | pending explicit decision |
| PICK ME UP | no first-slice seed entity |
| TUESDAY MORNING COMEDOWN | no first-slice seed entity |

Do not treat status as projection authority.

Required invariant:

```text
status != visibility authority
```

## Must Reject

Reject the next seed proposal if it includes:

- PICK ME UP as active/public material
- TUESDAY MORNING COMEDOWN as active/public material
- LP track rows under `SKM-LP-001`
- final LP track order
- final LP trackKeys
- provider URLs
- provider IDs
- `ExternalReference` rows
- `DistributionReference` rows
- `MusicReleaseLineage` rows
- `TrackLineage` rows
- `SUPERSEDES`
- projection changes without a separate projection eligibility decision
- frontend changes
- runtime API changes
- admin changes
- fake runtime, mood, world, or artwork authority

## Review Outcome

The corrected signal seed shape is approved at the planning level:

```text
SKM-LP-001 = canonical LP anchor
SKM-SIG-001 = ROPEMASTER preview/signal MusicRelease + Track
SKM-SIG-002 = TINDERMATCH preview/signal MusicRelease + Track
PICK ME UP = on hold / no public projection
TUESDAY MORNING COMEDOWN = on hold / no public projection
```

No seed write is approved.

The next blocker is catalog projection eligibility.

## Next Gate

Next gate should be:

```text
Phase 7C.4e-projection Gate - Catalog Projection Eligibility Decision
```

Only after that gate may a seed diff be prepared for review.
