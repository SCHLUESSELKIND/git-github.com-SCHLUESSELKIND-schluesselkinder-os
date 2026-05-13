# Static Registry Package Proposal

## Status

Proposal only.

No package created.
No runtime change.
No website change.
No API change.
No Prisma seed change.
No migration.
No provider references.
No external references.
No commerce path.

## Purpose

Define the exact static registry package shape before implementation.

The first implementation slice must create a typed, release-first public registry package that the website can consume without depending on API, PostgreSQL, Prisma seed state, or catalog route visibility.

Required invariants:

```text
public website availability != API availability
public website release truth != live database state
static registry first slice != permanent source split
```

## Proposed Package Structure

Recommended structure:

```text
packages/registry/
  package.json
  tsconfig.json
  src/
    index.ts
    types.ts
    artists.ts
    releases.ts
    tracks.ts
    objects.ts
    worlds.ts
    references.ts
    lineage.ts
    projections.ts
    guards.ts
```

Primary file responsibilities:

| File | Responsibility |
| --- | --- |
| `types.ts` | shared static registry and projection types |
| `artists.ts` | artist identity records |
| `releases.ts` | release wrappers; primary music registry entry point |
| `tracks.ts` | preview/signal track records, not final LP sequencing |
| `objects.ts` | archive object records |
| `worlds.ts` | minimal controlled world records |
| `references.ts` | provider-neutral reference shapes only; no URLs initially |
| `lineage.ts` | explicit relation records only if approved |
| `projections.ts` | public read helpers for website consumption |
| `guards.ts` | deterministic static validation helpers |
| `index.ts` | public exports only |

Required invariants:

```text
releases.ts = primary public music registry surface
tracks.ts = signal-oriented, not final LP sequencing
packages/registry != packages/brand
packages/registry != Prisma
```

## Dependency Boundary

`packages/registry` must not import:

- Prisma
- Fastify
- API routes
- database clients
- Next.js page modules
- provider SDKs
- Stripe
- Printful
- filesystem storage helpers

Allowed dependencies:

- TypeScript only
- local static data files inside `packages/registry`
- optional test runner support if needed by existing workspace patterns

Required invariant:

```text
static registry package != runtime integration layer
```

## Canonical Namespace Rules

Internal keys must be stable identity keys.

Proposed internal keys:

```text
ARTIST-SHIBARI-KAWAII
RELEASE-ROPEMASTER-LP
TRACK-TINDERMATCH
TRACK-ROPEMASTER
OBJ-SK-001
OBJ-SK-002
WORLD-POST-CLUB-SILENCE
WORLD-ROOM-AFTER-LIGHT
WORLD-COLD-ARCHIVE
```

Public codes are display/catalog codes, not identity keys:

```text
SKR-LP-001
SKR-001
SKR-002
SK-001
SK-002
```

Required invariants:

```text
public code != internal identity key
slug != canonical key
provider ID != registry key
rename != new identity
```

Do not use in the first implementation:

- `SKM-SIG-*` as public static registry codes
- `SND-*` as canonical music codes
- lowercase generated keys such as `track_sk_0001_01`
- provider-derived identifiers

## Initial Canonical Records

The first package implementation should include only:

| Entity | Role | Public state |
| --- | --- | --- |
| SHIBARI KAWAII | active artist | visible |
| ROPEMASTER LP | canonical LP anchor | contextual / visible as anchor |
| ROPEMASTER | preview signal | visible |
| TINDERMATCH | preview signal | visible |
| SK-001 | active object | visible |
| SK-002 | release-linked object | visible |

On-hold material stays out of public static projections:

- PICK ME UP
- TUESDAY MORNING COMEDOWN

Required invariants:

```text
on hold != withdrawn
on hold != deleted
on hold != public projection
```

## Release / Track Boundary

ROPEMASTER exists in multiple roles:

- LP anchor
- preview/signal release
- future possible LP track identity

The static registry must preserve these as separate concepts.

Required invariants:

```text
release ROPEMASTER != track ROPEMASTER
release wrapper != track identity
preview Track != final LP track identity
preview release != final LP track order
```

## Projection Helper Boundary

Website code should consume public projections only.

Proposed helper surface:

```text
getArtistDossier()
getPublicReleaseSignals()
getReleaseByCode(code)
getPublicObjects()
getObjectByCode(code)
```

The helpers should return controlled public shapes, not raw mutable records.

Website components must not decide:

- visibility
- on-hold state
- LP sequencing
- provider authority
- registry identity

Required invariants:

```text
React component != visibility authority
projection helper != mutation surface
public projection != raw registry record
```

## Guard Test Plan

The first implementation must include guard tests.

Required guard checks:

- registry package does not import Prisma
- registry package does not import Fastify
- registry package does not import API routes
- registry package does not import database clients
- release ROPEMASTER and track ROPEMASTER are distinct concepts
- internal keys are unique
- public codes are unique within their namespace
- on-hold material is not public
- no provider URLs are required
- no commerce fields exist
- public projection helpers return controlled shapes

Tests must not require:

- PostgreSQL
- Prisma Client
- API server
- provider network access
- website rendering

## References Boundary

Reference types may be defined for future compatibility, but first implementation should not include live SoundCloud or Spotify URLs.

Required invariants:

```text
registry record existence != external distribution existence
SoundCloud URL != identity
Spotify URL != identity
verified reference != provider authority
```

Forbidden in the first implementation:

- SoundCloud URLs
- Spotify URLs
- `ExternalReference` runtime insertion
- `DistributionReference` runtime insertion
- OAuth
- provider SDKs
- oEmbed
- embeds
- live provider fetches

## Prisma Alignment Boundary

Prisma alignment is later.

The first package implementation must not change:

- `packages/db/prisma/seed.ts`
- Prisma schema
- migrations
- catalog routes
- registry routes
- API repositories

Parked Prisma work belongs to:

```text
Prisma seed alignment pass
```

Required invariant:

```text
static registry implementation != Prisma alignment
```

## Must Reject

Reject implementation if it:

- places release registry data in `packages/brand`
- imports Prisma
- imports API/server code
- changes web pages before the package and guards exist
- changes Prisma seed or schema
- changes catalog route behavior
- introduces provider URLs
- introduces embeds
- makes on-hold material public
- assigns final LP track order
- assigns final LP track keys
- adds checkout, cart, price, stock, or variant logic
- adds Stripe or Printful integration

## Review Outcome

The approved next implementation shape should be:

```text
packages/registry
-> strict TypeScript records
-> release-first static data
-> public projection helpers
-> guard tests
```

No code implementation is approved by this document.

## Next Gate

Next gate should be:

```text
Phase 8A.2 - Static Registry Package Implementation
```

That gate may create `packages/registry` and tests, but must not modify Prisma, API routes, catalog routes, providers, or website pages yet.
