# ROPEMASTER LP Seed Update Proposal

## Status

Proposal only.

No implementation approved.
No seed write.
No migration.
No runtime change.
No projection change.
No website change.
No provider references.
No external reference insertion.

Required invariants:

```text
proposal != approved write
seed stabilization != release publication
seed row != public release confirmation
track existence != distribution approval
```

## Purpose

Define the exact future seed-update scope for introducing the ROPEMASTER LP anchor without creating false public release state, provider coupling, or premature album certainty.

This document prepares a later implementation review.

It does not authorize code changes.

## Allowed Future Write Scope

A later implementation proposal may touch only:

- `packages/db/prisma/seed.ts`
- focused regression tests for seed shape

No other files should be needed for the first LP seed slice.

Forbidden future write scope in this slice:

- Prisma schema files
- migration files
- runtime API files
- catalog projection files
- website files
- provider integration files
- external reference seed files

## Exact First LP Rows

Future seed diff should propose exactly one canonical LP `MusicRelease`:

| Model | Field | Proposed value |
| --- | --- | --- |
| `MusicRelease` | `releaseCode` | `SKM-LP-001` |
| `MusicRelease` | `title` | `ROPEMASTER` |
| `MusicRelease` | `status` | existing conservative release status, subject to review |
| `MusicRelease` | `artistId` | SHIBARI KAWAII artist |

Future seed diff should propose only known LP track rows:

| Model | Parent release | Title | trackKey | LP position |
| --- | --- | --- | --- | --- |
| `Track` | `SKM-LP-001` | PICK ME UP | pending | pending |
| `Track` | `SKM-LP-001` | TUESDAY MORNING COMEDOWN | pending | pending |
| `Track` | `SKM-LP-001` | ROPEMASTER | pending | pending |

No other LP tracks should be seeded in the first slice.

## Planned Slots Remain Absent

The LP target count remains 12.

The remaining 9 LP positions must not become seed rows yet.

```text
planned slot != registry track
missing title != placeholder entity
LP target count != seed row count
```

Do not seed:

- placeholder track titles
- placeholder `Track` rows
- fake runtime values
- fake mood/world values
- fake LP positions
- reserved trackKeys for unknown slots

## Initial Nullability / Pending Fields

The following fields may intentionally remain null, absent, or pending in the first LP seed slice:

- track runtime
- track mood fragments beyond known seed language
- controlled moods
- worlds
- artwork linkage
- LP position
- final trackKey
- distribution state
- external IDs
- provider URLs

Reason:

Avoid early semantic inflation and false certainty.

```text
unknown runtime != missing quality
unknown mood != taxonomy failure
unknown LP position != incomplete registry identity
```

## Current `SKM-001..003`

`SKM-001`, `SKM-002`, and `SKM-003` should remain untouched in the first LP seed slice.

Do not:

- delete them
- rename them
- reclassify them
- add lineage from them
- treat them as LP hierarchy
- attach provider references to them

Reason:

Their preview/single/signal-release status remains under governance review.

## Lineage

No lineage rows should be inserted in the first LP seed slice.

Reason:

- preview/single status remains unresolved
- LP positions remain pending
- historical relation strength is not approved
- `SUPERSEDES` remains excluded

Required invariant:

```text
LP seed stabilization != lineage decision
```

## Regression Test Scope

A later implementation review should include a focused regression test that verifies:

- `SKM-LP-001` is present as a `MusicRelease`
- `SKM-LP-001` has exactly the approved known track rows for the first slice
- no placeholder LP tracks are created
- current `SKM-001..003` rows are not used as LP hierarchy
- no provider URLs or external IDs are seeded
- no `ExternalReference` or `DistributionReference` rows are added
- no lineage rows are required by this slice

The regression test must not verify:

- public website rendering
- catalog projection output
- provider mapping
- track popularity
- stream availability
- SoundCloud or Spotify state
- final LP track order
- 12 persisted tracks

## Explicit Non-Goals

This proposal does not approve:

- external URLs
- provider IDs
- `ExternalReference`
- `DistributionReference`
- `MusicReleaseLineage`
- `TrackLineage`
- `SUPERSEDES`
- projection extension
- frontend rendering
- provider verification
- OAuth
- SDKs
- webhooks
- workers
- queues
- sync jobs

## Implementation Review Checklist

Before any seed write:

- exact seed diff is reviewed
- no accidental deletes are present
- no current `SKM-001..003` mutation is present
- no trackKey is assigned without LP position approval
- no provider fields or URLs are present
- no lineage rows are present
- no projection or frontend files are changed
- tests are focused on seed shape only

## Next Gate

Next gate should be:

```text
Phase 7C.4e - LP Seed Implementation Review
```

That gate may prepare an exact seed diff for review, but still should not apply broader runtime, projection, provider, or frontend changes.
