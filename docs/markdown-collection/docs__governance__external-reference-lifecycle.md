# External Reference Lifecycle

## Status

Planning and governance document only.

No runtime code is changed here.
No Prisma schema is changed here.
No migration is generated or applied here.
No provider integration is introduced here.
No website rendering is changed here.

This document defines the approval boundary for future external reference rendering.

## Purpose

External references let SCHLUESSELKINDER point from canonical registry entities to external signal surfaces without allowing those surfaces to become authority.

The central question is not how to show Spotify, SoundCloud, YouTube, Instagram, or TikTok.

The central question is how an external reference becomes eligible to enter the registry and later become eligible for projection.

## Core Invariants

```text
provider URL != canonical identity
provider availability != entity existence
provider metadata != registry truth
provider profile != artist authority
provider release page != release authority
external reference != distribution approval
projection eligibility != cultural importance
```

External platforms remain references only.

They must not define:

- artist identity
- track identity
- release identity
- archive codes
- titles
- artwork authority
- object status
- cultural meaning
- public importance

## External Reference Intake Model

Initial intake must be manual.

Allowed initial intake path:

```text
Human Operator
-> exact external URL collection
-> exact target entity selection
-> human review
-> canonical mapping decision
-> projection eligibility decision
```

Forbidden initial intake path:

```text
OAuth
-> provider sync
-> provider import
-> automatic matching
-> registry overwrite
```

Reference intake must record intent before visibility.

Required intake questions:

- Which internal entity is the reference for?
- Is the target an artist, release, track, object, channel, or distribution surface?
- Is the reference an `ExternalReference` or a `DistributionReference`?
- Is the URL exact and manually supplied?
- Is the platform identity known, uncertain, unavailable, or disputed?
- Should the reference remain internal, archival, or public?

## Manual Registry Insertion Flow

Initial registry insertion should follow this order:

1. Human operator proposes exact URL.
2. Reviewer confirms the intended internal target entity.
3. Reviewer classifies the reference type.
4. Reviewer confirms `sourceAuthority=false`.
5. Reviewer assigns initial verification state.
6. Reviewer assigns initial visibility.
7. Registry stores the reference.
8. Projection layer decides whether public rendering is allowed.

Insertion must not imply public display.

```text
stored reference != public reference
public reference != canonical importance
```

## Verification States

Verification state describes review confidence around the reference mapping.

It is not a truth score and not a ranking signal.

Recommended states:

- `UNVERIFIED`: URL exists in review context but mapping is not yet confirmed.
- `VERIFIED`: human review confirms that the URL points to the intended external surface.
- `UNVERIFIABLE`: review cannot confirm the mapping, but the reference may have archival value.
- `DISPUTED`: conflicting evidence exists.
- `WITHDRAWN`: internal governance intentionally removes the reference from active use while preserving history.
- `DECAYED`: the external surface appears unavailable, moved, removed, or inaccessible.

Required invariant:

```text
verified != authoritative
unverifiable != worthless
disputed != invalid
decayed != deleted
```

## Projection Eligibility Rules

Not every stored external reference may appear publicly.

Projection eligibility is a separate review decision.

Recommended visibility values:

- `INTERNAL`: stored for internal registry context only.
- `ARCHIVE`: eligible for archival context, not promotional display.
- `PUBLIC`: eligible for public website rendering.
- `WITHDRAWN`: intentionally removed from public projection while retained historically.

Projection may render only a narrow public shape:

- platform
- url
- verified state, if approved for public language
- visibility-safe label

Projection must not expose:

- provider authority claims
- `sourceAuthority`
- internal review notes
- lineage internals
- matching mechanics
- confidence mechanics
- private operator notes

## Reference Typology

### ExternalReference

Represents a general external signal surface.

Examples:

- Spotify artist profile
- SoundCloud artist profile
- Instagram profile
- TikTok profile
- YouTube channel

Use when the reference points to external presence or identity context.

### DistributionReference

Represents a concrete distribution surface for a release, track, or related archive object.

Examples:

- Spotify track URL
- Spotify album URL
- SoundCloud track URL
- SoundCloud playlist or release URL
- YouTube visualizer URL

Use when the reference points to a distributed instance or public distribution endpoint.

Required separation:

```text
ExternalReference != DistributionReference
profile presence != release distribution
artist channel != track endpoint
```

## Decay And Rot Governance

External references may decay.

Decay must not mutate the canonical entity.

If a link disappears, changes, region-locks, redirects, or becomes unavailable:

```text
reference unavailable != entity removed
provider death != archive deletion
dead link != false entity
```

Decay review should be manual in the registry foundation phase.

Allowed later:

- manual verification
- manual decay marking
- manual replacement reference proposal
- historical tombstone retention

Forbidden initially:

- link-health workers
- cron verification
- webhooks
- provider sync jobs
- automatic decay mutation
- scraping
- mirroring
- crawler infrastructure

## Withdrawal

Withdrawal is an internal governance action.

It is not the same as provider unavailability.

```text
withdrawn != unavailable
withdrawn != deleted
withdrawn != decayed
```

A withdrawn reference may remain historically retained while becoming ineligible for public projection.

Withdrawal requires explicit human review.

## Authority Boundaries

External references can support public context.

They cannot create cultural truth.

Allowed future public rendering:

- small platform badge
- text link
- external reference label
- archival signal list

Forbidden future public rendering without separate approval:

- iframes
- embeds
- waveform players
- autoplay
- provider SDKs
- OAuth
- live provider fetches
- follower counts
- stream counts
- popularity ranking
- top-track sorting
- recommendation logic

## Phase 7C Implementation Gate

Before implementation, approve all of the following:

- exact source of each reference
- exact target entity mapping
- reference type: `ExternalReference` or `DistributionReference`
- initial verification state
- initial visibility state
- projection-safe public label
- no provider SDK or OAuth requirement
- no frontend direct provider fetch
- no `packages/brand` authority path

Implementation remains blocked until the reference data path is:

```text
Registry
-> Projection
-> Website
```

and not:

```text
packages/brand
-> Website
-> Provider Link
```

## Drift Artifacts

The following local patch files were intentionally preserved as drift-review artifacts:

- `/tmp/schluesselkinder-drift-review.patch`
- `/tmp/schluesselkinder-shop-drift-review.patch`

They document a rejected direction where provider URLs and commerce/status language entered public website surfaces outside the registry projection path.

They should be reviewed as drift evidence, not applied as implementation patches.
