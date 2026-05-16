# Static Release Registry First Slice

## Status

Planning only.

No package created.
No runtime change.
No website change.
No API change.
No Prisma seed change.
No migration.
No provider references.
No external references.
No projection route change.

## Purpose

Define the first production-safe public release registry slice after the corrected ROPEMASTER signal planning.

The public website must not depend on API, PostgreSQL, Prisma seed state, or catalog route visibility for the first operational slice.

Required invariant:

```text
public website availability != API availability
public website release truth != live database state
static registry != Prisma replacement
```

## Architecture Decision

Use a static typed package as the first public release registry source:

```text
packages/registry
-> typed release records
-> web-only consumption
-> Prisma alignment later
```

This is an operational safety cut, not a new permanent authority split.

Required invariant:

```text
static registry first slice != permanent source split
```

## Why This Comes Before Prisma Alignment

The parked Prisma seed diff was technically viable but strategically premature.

Reason:

The current catalog routes can expose seeded `MusicRelease` rows. A Prisma seed write can therefore create accidental public catalog state unless projection eligibility is implemented first.

The static release registry avoids that by keeping the first public slice:

- web-only
- build-time typed
- explicit
- reviewable
- independent from API/Postgres availability
- disconnected from catalog route visibility

Required invariant:

```text
seed row != public projection eligibility
catalog route visibility != release approval
```

## Corrected Release Shape

The static release registry first slice should preserve the current corrected planning shape:

| Entity | Registry role |
| --- | --- |
| `SKM-LP-001` / ROPEMASTER LP | canonical album anchor |
| `SKM-SIG-001` / ROPEMASTER | first preview/signal release |
| `SKM-SIG-002` / TINDERMATCH | second preview/signal release |
| PICK ME UP | on hold / no public projection |
| TUESDAY MORNING COMEDOWN | on hold / no public projection |

Required invariants:

```text
preview release != LP release
preview release != final LP track order
current signal != album completion
album anchor != public distribution state
on hold != withdrawn
on hold != deleted
on hold != public projection
```

## Release-First Boundary

The first package shape should model release wrappers first.

Preview/signal records may have child track records, but those child tracks must not become final LP track identity.

Required invariants:

```text
release wrapper != track identity
preview Track != final LP track identity
LP plus preview signals != isolated singles architecture
```

Exact TypeScript names, file paths, and key formats remain for the next implementation proposal.

## Web-Only Production Boundary

The first static registry slice should support the current safe deployment posture:

```text
public website
-> static typed registry
-> no public API dependency
-> no production database dependency
```

This keeps the public site stable while Prisma and catalog projection eligibility remain under review.

Required invariant:

```text
web-only public slice != backend registry completion
```

## packages/brand Boundary

The static release registry must not be placed in `packages/brand`.

`packages/brand` may carry public language, symbols, atmosphere, and visual constants.

The new registry package should carry structured release identity.

Required invariants:

```text
brand language != registry identity
frontend label != canonical record
packages/brand != release registry
```

## First Implementation Scope Later

Allowed later in Phase 8A implementation:

- create `packages/registry`
- define strict TypeScript record types
- add release-first static records
- add public projection helpers
- add focused guard tests
- consume projections from website pages
- preserve current visual system

Forbidden in Phase 8A implementation:

- Prisma seed changes
- Prisma schema changes
- migrations
- API routes
- catalog route changes
- backend repository changes
- database access from website
- provider URLs
- Spotify/SoundCloud embeds
- OAuth
- external reference insertion
- distribution reference insertion
- analytics
- admin UI
- runtime writes
- checkout
- cart
- price CTA
- stock/variant logic
- Stripe activation
- Printful API

## Guard Test Direction

The first implementation should include tests that assert:

- static registry does not import Prisma
- static registry does not import Fastify or API code
- release ROPEMASTER and track/signal ROPEMASTER remain distinct concepts
- on-hold material is not public
- no provider URLs are required
- no commerce fields exist
- public projection helpers return controlled shapes

The tests should not require:

- PostgreSQL
- Prisma Client
- API server
- provider network access
- website rendering

## Prisma Alignment Later

The parked Prisma seed diff belongs to a later alignment pass:

```text
Prisma seed alignment pass
```

That later pass should reconcile:

- LP anchor shape
- preview/signal release shape
- on-hold handling
- release-scoped fragment lookup
- catalog projection eligibility
- future external/distribution reference mapping

It must not be mixed into the static registry first slice.

Required invariant:

```text
static release registry first slice != Prisma alignment pass
```

## Must Reject

Reject the first implementation slice if it:

- modifies `packages/db/prisma/seed.ts`
- applies or creates migrations
- changes catalog route behavior
- changes API route behavior
- introduces provider URLs
- introduces embeds
- makes on-hold material public
- derives LP order from signal releases
- assigns final LP track keys
- treats `SKM-LP-001` as public distribution state
- makes `packages/brand` the source of release truth
- depends on API/Postgres at website render time

## Review Outcome

The next implementation direction should be static release registry first:

```text
packages/registry
-> release-first typed records
-> web-only production-safe consumption
-> Prisma alignment later
```

No implementation is approved by this document.

## Next Gate

Next gate should be:

```text
Phase 8A.1 - Static Registry Package Proposal
```

That gate may prepare the exact package/file shape before any code is written.
