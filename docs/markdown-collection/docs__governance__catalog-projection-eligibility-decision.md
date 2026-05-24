# Catalog Projection Eligibility Decision

## Status

Decision document only.

No seed diff.
No seed write.
No migration.
No runtime change.
No catalog route change.
No projection mapper change.
No frontend change.
No provider references.
No external references.

## Purpose

Define the boundary between registry seed existence and public catalog projection eligibility before the corrected ROPEMASTER signal seed shape is implemented.

The catalog layer must not turn internal registry stabilization into public release state.

Required invariants:

```text
seed row != public projection approval
status != visibility authority
catalog route visibility != release approval
projection eligibility != seed existence
```

## Current Risk

The current catalog read surface can expose all `MusicRelease` rows through `/catalog/music-releases`.

If a seed diff adds:

- `SKM-LP-001`
- `SKM-SIG-001`
- `SKM-SIG-002`

those rows may become visible wherever the seed data is available.

That would collapse registry stabilization into public catalog state.

## Decision

No production/shared seed apply is allowed until catalog projection eligibility is implemented or explicitly waived by a later governance decision.

The next seed implementation may be prepared and reviewed only as a local/dev registry stabilization step.

Required invariant:

```text
dev seed review != public projection approval
```

## ROPEMASTER Eligibility State

Initial eligibility decision:

| Entity | Registry role | Public catalog eligibility |
| --- | --- | --- |
| `SKM-LP-001` | canonical LP anchor | no |
| `SKM-SIG-001` | ROPEMASTER preview/signal release | no |
| `SKM-SIG-002` | TINDERMATCH preview/signal release | no |
| PICK ME UP | on hold / later | no |
| TUESDAY MORNING COMEDOWN | on hold / later | no |

Reason:

The next seed slice is registry stabilization only. It is not a public release, public catalog, or distribution approval.

## Eligibility Mechanism Options

The system needs an explicit projection eligibility mechanism before any public catalog exposure of corrected ROPEMASTER rows.

Options:

| Option | Description | Review |
| --- | --- | --- |
| status filter | Catalog excludes non-public statuses such as `SIGNAL_PENDING` | insufficient alone |
| explicit allowlist mapper | Catalog maps only approved release codes | acceptable short-term |
| dedicated projection field | Add explicit field such as `catalogVisible` or `publicProjectionEligible` | likely long-term |
| separate projection table | Add a public projection model/table | future, not current slice |

Decision for next slice:

```text
dev/local seed allowed only
no production/shared seed apply
no public catalog projection until explicit eligibility guard exists
```

## Status Is Not Enough

Release status must not become the only projection authority.

Reasons:

- status can describe registry/release state
- projection eligibility describes public visibility
- on-hold/internal material may still need registry state
- preview/signal releases may need internal existence before public projection

Required invariant:

```text
release status != projection eligibility
```

## Recommended Future Direction

For the eventual projection implementation, prefer an explicit eligibility guard over blind status inference.

Short-term acceptable direction:

- keep corrected seed rows dev/local only
- add no production/shared seed apply
- add no public catalog exposure
- decide explicit projection eligibility before route behavior changes

Long-term likely direction:

- additive explicit projection eligibility field or projection-owned allowlist
- catalog mappers filter by eligibility
- tests assert that hidden/internal/on-hold releases are not projected

This document does not approve schema or mapper changes.

## Catalog Route Requirement

Future catalog implementation must not blindly project all `MusicRelease` rows.

Required future behavior:

```text
/catalog/music-releases = eligible public projections only
```

This does not mean registry rows are deleted or invalid.

Required invariants:

```text
not projected != not canonical
hidden from catalog != withdrawn
internal registry row != public release
```

## Seed-Diff Gate Impact

The next seed-diff gate may prepare an exact seed diff for review only if it includes this boundary:

- local/dev application only
- no production/shared seed apply
- no public projection expectation
- no frontend consumption expectation
- no provider/external reference expectation

The seed diff must not modify:

- catalog mappers
- catalog routes
- website rendering
- provider references
- external references
- distribution references

## Must Reject

Reject any next proposal that:

- treats `SKM-LP-001` as public catalog-ready
- treats `SKM-SIG-001` as public catalog-ready
- treats `SKM-SIG-002` as public catalog-ready
- exposes on-hold material
- uses `ReleaseStatus.ACTIVE` as public visibility proof
- makes `/catalog/music-releases` a blind registry dump
- adds provider URLs
- adds embeds
- changes frontend rendering
- applies seed data to production/shared environments before eligibility exists

## Review Outcome

Projection eligibility is not implemented.

The corrected ROPEMASTER seed shape may proceed only to a local/dev seed-diff review.

Production/shared seed apply remains blocked.

Public catalog exposure remains blocked.

## Next Gate

Next gate should be:

```text
Phase 7C.4f - Corrected Signal Seed Diff Review
```

That gate may prepare an exact `seed.ts` and focused regression-test diff for inspection only.
