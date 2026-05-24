# Website Static Registry Consumption Proposal

## Status

Planning only.

This document does not authorize runtime changes, website edits, Prisma changes, API/catalog changes, provider references, embeds, commerce additions, or public release expansion.

## Purpose

Phase 8A.3 defines how the public website should later consume the static registry package without turning UI code, `packages/brand`, API availability, or provider surfaces into release authority.

The goal is controlled website consumption of static registry projections while preserving the Phase 8A.2 boundary:

```text
registry state = git state
public projection != raw registry record
static registry consumption != API replacement
```

## Consumption Boundary

The website may consume projection helpers only.

The website must not consume raw registry records directly.

React components and route files are not visibility authorities.

`packages/brand` is not the release registry.

Static registry consumption is not an API replacement.

The website must not derive:

- canonical identity
- release hierarchy
- track identity
- projection eligibility
- provider authority
- distribution state
- commerce state

from component-local constants, slugs, filenames, routes, or visual layout.

## First Planned Target Pages

The first website migration slice should be limited to existing public pages:

| Page | Planned consumption role |
|---|---|
| `/music` | Render public release and track-signal projections |
| `/artists/shibari-kawaii` | Render public artist dossier and related public signals |
| `/shop` | Render public object projections only |
| `/objects/sk-001` | Render public object projection for `SK-001` |
| `/objects/sk-002` | Render public object projection for `SK-002` |

The initial website migration should preserve the current visual design and replace only the data source boundary.

## Planned Projection Helpers

Later website consumption should use projection helpers such as:

- `getPublicReleaseSignals()`
- `getReleaseByCode()`
- `getPublicObjects()`
- `getArtistDossier()`

If helper names differ in the implemented package, the website migration must use the approved projection-helper layer rather than raw exports.

No React component should decide whether a raw registry record is public.

No page should reconstruct projection shape from raw `artists`, `releases`, `trackSignals`, `objects`, `worlds`, `references`, or `lineage` exports.

## Explicit Exclusions

Phase 8A.3 planning does not authorize:

- Prisma
- API runtime dependency
- Postgres dependency
- provider URLs
- embeds
- SoundCloud references
- Spotify references
- provider SDKs
- OAuth
- fetch
- filesystem reads
- commerce fields
- checkout
- cart
- Stripe
- Printful
- on-hold material exposure

## Public Canon Boundary

Current public canon is limited to:

| Entity | Public role |
|---|---|
| `ARTIST-SHIBARI-KAWAII` | Artist |
| `RELEASE-ROPEMASTER-LP` / `SKR-LP-001` | ROPEMASTER LP anchor |
| `TRACK-TINDERMATCH` / `SKR-001` | Public preview signal |
| `TRACK-ROPEMASTER` / `SKR-002` | Public preview signal |
| `OBJ-SK-001` / `SK-001` | Public object |
| `OBJ-SK-002` / `SK-002` | Public release-linked object |

Explicitly excluded from public projection:

- `PICK ME UP`
- `TUESDAY MORNING COMEDOWN`
- legacy material
- on-hold material
- old SKM/SND assumptions

## Projection Invariants

```text
release ROPEMASTER != track ROPEMASTER
public code != internal identity key
on-hold material != public render candidate
registry record existence != distribution existence
static registry consumption != API replacement
```

Additional invariants:

```text
website route != release authority
React component != visibility authority
packages/brand != release registry
projection helper != mutable CMS surface
visual prominence != canonical importance
```

## Future Compatibility

Prisma alignment comes later.

API catalog alignment comes later.

Distribution references come later.

Expanded registry shape review is separate.

Website migration should preserve the current visual design initially.

The static registry package should remain a deterministic archive layer. Future alignment with Prisma or API catalog routes must compare against the registry intentionally, not silently replace it or split authority.

## Approval Gate Before Implementation

Before any website change, review must confirm:

- the target page consumes only approved projection helpers
- raw registry exports are not imported by page components
- no provider URL or embed is introduced
- no commerce or checkout logic is introduced
- no on-hold material becomes visible
- existing visual design is preserved unless separately approved
- fallback behavior does not create alternate truth from `packages/brand`

Implementation remains blocked until this planning document is approved.
