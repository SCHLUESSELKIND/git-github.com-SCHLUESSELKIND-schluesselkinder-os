# ROPEMASTER Release Plan Correction

## Status

Planning correction only.

No seed diff.
No seed write.
No migration.
No runtime change.
No projection change.
No frontend change.
No provider references.
No external references.
No lineage rows.

This document blocks the previous LP seed implementation review assumptions.

## Purpose

Correct the first ROPEMASTER release planning slice before any seed implementation is prepared.

The previous planning assumption treated three known titles as the first LP seed candidates:

- PICK ME UP
- TUESDAY MORNING COMEDOWN
- ROPEMASTER

That assumption is no longer valid.

## Corrected Release Reality

Canonical album anchor:

- `SKM-LP-001` / ROPEMASTER LP

Current / active preview releases:

- ROPEMASTER
- TINDERMATCH

On hold / later material:

- PICK ME UP
- TUESDAY MORNING COMEDOWN

Required invariants:

```text
on hold != withdrawn
on hold != deleted
on hold != public projection
preview release != LP release
preview release != final LP track order
current release signal != final LP order
current signal != album completion
album anchor != public distribution state
seed stabilization != release publication
track existence != distribution approval
```

## Consequences

The first LP seed slice must not create three active known LP tracks.

Specifically:

- PICK ME UP must not be seeded as active LP/public material in the first slice.
- TUESDAY MORNING COMEDOWN must not be seeded as active LP/public material in the first slice.
- ROPEMASTER may be planned as the first preview/signal `MusicRelease` candidate.
- TINDERMATCH may be planned as the second preview/signal `MusicRelease` candidate.
- `SKM-LP-001` remains the planned canonical LP anchor.
- The first active preview/signal slice contains only ROPEMASTER and TINDERMATCH.
- ROPEMASTER release signal must not be treated as the complete LP.
- TINDERMATCH must not be treated as the LP.

## Blocked Previous Assumptions

Blocked:

- `SKM-LP-001` with PICK ME UP, TUESDAY MORNING COMEDOWN, and ROPEMASTER as first LP track rows
- any seed test expecting three first-slice LP tracks
- any projection that makes on-hold material public
- any frontend fallback that treats on-hold material as current
- any provider/external reference mapping for on-hold material
- any trackKey assignment for on-hold material

Required invariant:

```text
old three-track slice != approved seed shape
TINDERMATCH != LP
TINDERMATCH = preview signal for ROPEMASTER LP
ROPEMASTER release signal != full LP
```

## Projection Boundary

The current catalog projection layer can expose seeded `MusicRelease` records.

Therefore, seed planning must account for visibility before any write.

Required invariants:

```text
seed row != public projection approval
catalog visibility != release approval
on hold material != catalog candidate
```

No on-hold material may become publicly visible through:

- catalog routes
- website fallbacks
- static brand data
- object/shop pages
- provider links
- embedded players

## Current Material Classification

| Title | Current classification | Public projection eligibility | Notes |
| --- | --- | --- | --- |
| ROPEMASTER LP | canonical album anchor | pending review | `SKM-LP-001`; must not imply public distribution state. |
| ROPEMASTER | first preview/signal release | pending review | Must not be treated as the complete LP. |
| TINDERMATCH | second preview/signal release | pending review | Must be treated as a preview signal for the ROPEMASTER LP, not as the LP. |
| PICK ME UP | on hold / later | no | Must not be treated as active LP, preview, or public projection material in the first slice. |
| TUESDAY MORNING COMEDOWN | on hold / later | no | Must not be treated as active LP, preview, or public projection material in the first slice. |

## LP Anchor Boundary

`SKM-LP-001` remains the planned canonical LP anchor.

This does not mean:

- the LP is publicly released
- the LP is publicly distributed
- all known titles are LP seed rows
- current signal order is LP order
- public signal material defines final album sequencing
- preview releases define LP track identity
- on-hold material is withdrawn or deleted

Required invariant:

```text
LP anchor != final tracklist
LP anchor != public distribution state
```

## Next Seed-Shape Direction

The next seed-shape gate should use this direction:

- `SKM-LP-001` remains the canonical LP `MusicRelease` anchor.
- ROPEMASTER may be planned as a separate preview/signal `MusicRelease` candidate.
- TINDERMATCH may be planned as a separate preview/signal `MusicRelease` candidate.
- No final LP `trackKey` values are assigned while album positions are unconfirmed.
- No final LP ordering is persisted.
- No provider references, URLs, embeds, or external mappings are introduced.

Required invariant:

```text
LP plus preview signals != isolated singles architecture
```

## Required Before Seed Diff

Before any seed diff is prepared, governance must decide:

- whether TINDERMATCH is a `MusicRelease`, `Track`, or both in the first slice
- whether ROPEMASTER remains `SKM-003`, becomes part of `SKM-LP-001`, or both
- which release codes are used for ROPEMASTER preview and TINDERMATCH preview
- whether `SKM-001` and `SKM-002` are hidden, inactive, removed from public projection, or left untouched pending a separate correction
- whether the seed needs projection eligibility fields before any current/on-hold split is safe
- whether catalog projection must filter `ReleaseStatus.SIGNAL_PENDING` or another status before seed application

## Must Reject

Reject the next implementation proposal if it includes:

- PICK ME UP as active LP material
- TUESDAY MORNING COMEDOWN as active LP material
- public projection of on-hold material
- provider URLs
- external references
- distribution references
- trackKey assignment for on-hold material
- LP position assignment
- final LP ordering
- lineage rows
- `SUPERSEDES`
- frontend edits
- runtime API edits
- catalog projection edits without a separate projection-eligibility gate

## Review Outcome

Phase 7C.4e remains blocked.

No seed diff should be prepared until this corrected release plan is reviewed and the next seed shape is approved.

## Next Gate

Next gate should be:

```text
Phase 7C.4e-revision Review - Corrected Signal Seed Shape
```

That gate should decide the exact first seed planning shape for TINDERMATCH and ROPEMASTER before any file diff is prepared.
