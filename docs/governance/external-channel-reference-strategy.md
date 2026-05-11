# External Channel Reference Strategy

## Status

Planning and boundary document only.

No provider integration is implemented here.
No OAuth flow is introduced.
No API client is introduced.
No schema migration is proposed.
No runtime route is changed.

## Purpose

SoundCloud and Spotify may support the public website as listening surfaces, but they must not become backend authorities.

The internal SCHLUESSELKINDER registry remains canonical.

## Platform Roles

| Platform | Website Role | Backend Role |
| --- | --- | --- |
| SoundCloud | underground/raw-signal player | `ExternalReference` + `DistributionReference` later |
| Spotify | official release/legitimacy endpoint | `ExternalReference` + `DistributionReference` later |
| Spotify for Artists | manual artist office and statistics surface | no direct registry-authority layer |

Spotify for Artists may be used manually for artist profile management, promotion, and statistics review. It is not a registry source of truth.

## Core Invariants

```text
provider URL != canonical identity
provider embed != registry source
Spotify for Artists != registry authority
SoundCloud player != release truth
external stream availability != entity existence
provider stats != cultural authority
```

## Phase 1: Embed-First

Immediate website direction:

```text
Artist Page
-> Release Cards
-> SoundCloud Embed
-> Spotify Embed / Link
-> canonical SCHLUESSELKINDER Metadata
```

Rules:

- show canonical SCHLUESSELKINDER metadata first
- use SoundCloud and Spotify as listening references
- prefer official embed/oEmbed patterns
- do not scrape provider pages
- do not call provider APIs from the backend
- do not store OAuth tokens
- do not infer title, artist, release date, artwork, or track identity from embeds

Implementation boundary:

```text
embed display != provider integration
listen link != distribution authority
```

## Phase 2: Registry Mapping Later

Manual registry mapping may later store provider-neutral references per track.

Example shape:

```json
{
  "trackKey": "track_sk_0001_01",
  "platform": "SOUNDCLOUD",
  "url": "...",
  "externalId": "...",
  "sourceAuthority": false,
  "verified": true
}
```

Spotify uses the same shape:

```json
{
  "trackKey": "track_sk_0001_01",
  "platform": "SPOTIFY",
  "url": "...",
  "externalId": "...",
  "sourceAuthority": false,
  "verified": true
}
```

Required:

- exact manually approved URLs only
- exact manually approved external IDs only
- no invented URLs
- no inferred ISRC, UPC, release date, handle, or profile ID
- `sourceAuthority=false`

## Phase 3: Read-Only Verification Later

Spotify Web API can later support read-only verification of artist, album, and track metadata after separate approval.

SoundCloud API should remain out of scope unless a concrete verification need appears. For now, SoundCloud oEmbed and embedded player behavior are enough.

Read-only verification, if approved later, must remain:

- non-authoritative
- manual-review-bound
- non-reactive
- no OAuth token persistence unless separately approved
- no automatic registry mutation
- no sync jobs
- no KPI sorting

## Current No-Gos

- no Spotify upload
- no SoundCloud upload
- no OAuth
- no provider SDKs
- no auto-sync
- no webhook
- no worker
- no queue
- no KPI-driven sorting
- no top-track logic
- no provider data as truth
- no provider metadata overwrite
- no provider artwork as canonical artwork

## First Technical Slice

The first safe technical slice is:

1. Finish Prisma inventory.
2. Check current gaps for `ExternalReference` and `DistributionReference`.
3. Collect exact manual SoundCloud and Spotify URLs per track.
4. Build a website embed/link component that renders only approved provided URLs.
5. Add no API integration.

Required input before website embed implementation:

- exact SoundCloud URL per track or release
- exact Spotify URL per track, album, artist, or release
- decision whether each URL is a player embed, link-only reference, or both

No placeholder provider URLs should be committed.

## Official Reference Points

- Spotify supports official Embeds and oEmbed for artist, album, track, playlist, podcast show, and episode URLs.
- Spotify Web API exposes read endpoints for catalog metadata such as tracks, albums, and artists, subject to Spotify developer policy and attribution requirements.
- SoundCloud provides an oEmbed endpoint for embeddable widgets.
- SoundCloud API/SDK usage touches app/OAuth context and is not needed for the embed-first phase.

Sources:

- [Spotify Embeds](https://developer.spotify.com/documentation/embeds)
- [Spotify oEmbed API](https://developer.spotify.com/documentation/embeds/reference/oembed)
- [Spotify Web API track reference](https://developer.spotify.com/documentation/web-api/reference/get-track)
- [SoundCloud oEmbed](https://developers.soundcloud.com/docs/oembed)
- [SoundCloud API guide](https://developers.soundcloud.com/docs/api/)
