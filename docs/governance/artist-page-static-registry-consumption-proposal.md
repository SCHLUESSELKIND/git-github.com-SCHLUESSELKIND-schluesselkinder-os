# Artist Page Static Registry Consumption Proposal

## Status

Planning only.

This document does not authorize implementation, runtime changes, web page edits, registry shape expansion, Prisma/API changes, provider references, embeds, commerce additions, or public canon expansion.

## Target Page

Initial target:

```text
/artists/shibari-kawaii
```

No other artist page, shop page, object page, catalog route, registry route, or admin surface belongs to this phase.

## Consumption Architecture

The artist page should consume projection helpers only.

Raw registry arrays must not be imported by React components.

Visibility filtering must not happen inside React components.

`packages/brand` must not act as fallback release truth.

The artist page must not depend on API, catalog routes, Postgres, Prisma, fetch, runtime configuration, provider state, or live distribution availability.

The intended flow is:

```text
packages/registry
-> approved projection helpers
-> web-safe adapter
-> /artists/shibari-kawaii
```

Not:

```text
packages/brand
-> artist page release truth
```

Not:

```text
API/catalog runtime
-> artist page authority
```

## Planned Projection Inputs

The artist page migration may use approved projection helpers such as:

- `getArtistDossier()`
- `getPublicReleaseSignals()`
- `getPublicObjects()`

If helper names change later, the artist page must still consume only the approved projection-helper layer or a web-safe adapter over that layer.

The page must not directly render:

- `artists`
- `releases`
- `trackSignals`
- `objects`
- `worlds`
- `references`
- `lineage`

## Public Canon Boundary

Allowed public material:

| Entity | Public role |
|---|---|
| `SHIBARI KAWAII` | Artist dossier |
| `ROPEMASTER LP` | Release anchor |
| `TINDERMATCH` | Public preview signal |
| `ROPEMASTER` | Public preview signal |
| `SK-001` | Public object |
| `SK-002` | Public release-linked object |

Explicitly excluded:

- `PICK ME UP`
- `TUESDAY MORNING COMEDOWN`
- legacy material
- on-hold material
- provider references
- distribution references

## Projection Invariants

```text
release ROPEMASTER != track ROPEMASTER
public code != internal identity key
artist page != visibility authority
registry record existence != distribution existence
static registry consumption != API replacement
```

Additional artist-page invariants:

```text
artist page prominence != canonical importance
artist page copy != registry mutation
artist page object display != commerce approval
artist page release display != distribution approval
```

## Visual Boundary

The initial migration should preserve the current visual design as closely as possible.

No redesign.

No new CTA surfaces.

No embeds.

No player UI.

No provider links.

No commerce expansion.

No new storefront behavior.

The migration should replace only the data-source boundary, not the page concept.

## Future Compatibility

Prisma alignment comes later.

API/catalog alignment comes later.

Distribution references come later.

Expanded registry shape review is separate.

Artist page migration should remain deterministic and synchronous.

Future artist-page work must keep the artist page as a projection consumer, not a CMS surface, provider adapter, distribution dashboard, or commerce authority.

## Approval Gate Before Implementation

Before any code change, review must confirm:

- only `/artists/shibari-kawaii` is targeted
- the page consumes projection helpers or a web-safe adapter only
- raw registry arrays are not imported by React components
- no `packages/brand` release fallback remains
- no provider URL or embed is introduced
- no API/catalog/runtime dependency is introduced
- no commerce or checkout behavior is introduced
- no on-hold material becomes visible
- current visual design remains the baseline
