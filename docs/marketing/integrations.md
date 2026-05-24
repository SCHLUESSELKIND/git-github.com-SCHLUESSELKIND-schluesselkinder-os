# Marketing Integrations

External channels the Marketing OS reads from or exports to. This
document covers MVP posture, later automation strategy, auth
requirements, and risks.

The MVP posture for every channel is **manual publish**. The OS
produces export-ready artifacts and a publish checklist. It does not
call publishing APIs. Real API automation is sequenced channel by
channel in `docs/marketing/roadmap.md`.

## Provider Groups

The Marketing OS adds the following intent groups to the registry
pattern from `docs/soundsystem/model-provider-strategy.md`.

| Group                       | Intent                                                       |
| --------------------------- | ------------------------------------------------------------ |
| `storage_sync_provider`     | Project folder sync into operator storage                    |
| `social_export_provider`    | Channel-specific export pack rendering                       |
| `social_publishing_provider`| Direct publish to a channel (post-MVP)                       |
| `analytics_provider`        | KPI import from a channel or aggregator                      |

Provider candidates appear in this document only. The operator UI uses
creative actions such as `EXPORT CHANNEL ASSETS` and platform-neutral
labels such as `STORAGE` and `ANALYTICS`.

## Storage Sync

### Dropbox (MVP target)

Use case:

```text
/Artists/{artist_slug}/
  /Releases/{release_code}/
    /Audio/
    /Covers/
    /Clips/
    /Social/
    /Captions/
    /Exports/
    /Compliance/
```

Auth: long-lived app token stored locally; never committed; never in
`.env.example`. A short-lived OAuth flow is preferred once a service
account is decided.

Risks:

- Token leakage. Token must live in a vault and rotate.
- Folder schema drift. The schema must be enforced server-side.
- Rate limits during bulk export.

MVP posture: write only; the OS writes export packs into Dropbox. It
does not read user-uploaded media in MVP.

### Google Drive (optional)

Same use case as Dropbox. Considered optional because Dropbox is the
primary operator surface. Drive is the fallback when a partner studio
requires it.

### Local Filesystem (always available)

The OS writes a local export directory under
`apps/web/.export/{campaign_code}/` for offline review. Local files are
never committed.

## Audio Channels

### SoundCloud

MVP posture:

```text
read: artist link, release link, basic metadata
write: none
export: description draft, cover, banner, private release link, metadata JSON
```

Auth: SoundCloud OAuth, post-MVP. Public API has historically had
limited write coverage; upload reliability is uncertain.

Risks:

- Upload coverage may be limited or rate-controlled.
- Account suspension for repeated API failures or for using third-party
  upload tooling.

Long-term posture: descriptions, tags, and metadata are produced as a
SoundCloud release pack. The operator pastes the description and
uploads the master manually. Direct upload is a candidate only after
the OAuth flow and policy are reviewed.

### Spotify

MVP posture:

```text
read: artist link, release link (post-distribution)
write: none
export: Canvas asset, link-storage record, manual KPI snapshot
```

Distribution still runs through the artist's distributor. The OS does
not pretend to distribute to Spotify. The Spotify for Artists surface
remains the operator's source of truth for audience, song, and
playlist data; the OS captures snapshots manually.

Risks:

- No public upload API; distribution must remain external.
- Spotify for Artists has no general partner-facing read API for
  granular metrics; manual export is the realistic MVP path.

Later automation: Canvas upload via the distributor's Canvas pipeline
where supported. Direct Canvas uploads to Spotify are not assumed.

## Video And Short-Form Channels

### YouTube

MVP posture:

```text
read: video URL, channel URL
write: none
export: thumbnail, description, tags, end-screen plan, manual upload checklist
```

Later automation: YouTube Data API upload behind a per-account toggle.
Requires Google OAuth, app verification, and quota planning.

Risks:

- API quota and review.
- App verification for upload scope.
- Account suspension on repeated upload failures.

### Instagram / Meta

MVP posture:

```text
read: none
write: none
export: feed asset, story asset, reel asset, caption, hashtag set
```

Later automation: Meta Graph API publishing for Business accounts only.
Requires Facebook Page link, Business account, and app review.

Risks:

- Personal accounts cannot publish via API.
- App review cycles and policy churn.
- Caption length and hashtag policy may shift.

### TikTok

MVP posture:

```text
read: none
write: none
export: vertical video, caption, hashtag set, sound link
```

Later automation: TikTok Content Posting API where eligible. Posting
coverage varies by region and partner status.

Risks:

- Partner status required for full posting coverage.
- Region-specific policy changes.
- Sound-attribution and music-rights handling differs from Meta.

## Analytics

### MVP — Manual Snapshots

The OS exposes `AnalyticsSnapshot` records with a per-channel KPI
payload. Snapshots are entered by the operator from existing analytics
surfaces:

- Spotify for Artists (audience, songs, playlists).
- SoundCloud stats (plays, likes, reposts, top countries).
- YouTube Studio (views, retention, traffic sources).
- Instagram Insights (reach, impressions, profile actions).
- TikTok analytics (views, watch time, follower growth).

### Later — Read-Only API Imports

Sequence (subject to API access):

1. YouTube Data API analytics read.
2. Meta Graph API insights for Business accounts.
3. TikTok Research API or Content Insights where eligible.
4. SoundCloud stats where available.
5. Spotify for Artists data via distributor pipeline.

### Later — Aggregator

Chartmetric-style aggregation is a planning option for cross-channel
artist and track insights once the manual snapshot pattern proves
useful. Aggregators are never the source of truth, only an
acceleration over manual entry.

## Ad Accounts (post-MVP)

The OS exposes `AdCreativePack` artifacts in MVP. It does not connect
to Meta Ads, TikTok Ads Manager, Google Ads, or any other ad surface.
Later automation requires:

- Ad account ownership documentation.
- Spend controls and rollback rules.
- Operator confirmation before any spend action.

Ad activation is treated as a destructive operation. The OS will
require explicit operator confirmation for every spend change, not
just for the first one.

## Auth And Secrets

- Tokens and secrets never live in the repo. Real values stay in a
  vault.
- `.env.example` lists variable names only.
- The OS never logs raw tokens, raw OAuth codes, or raw publishing
  payloads. Logs redact by default.

## Risks Summary

| Risk                                | Mitigation                                       |
| ----------------------------------- | ------------------------------------------------ |
| Token leakage                       | Vault, redaction, no committed values            |
| Account suspension                  | Manual publish in MVP, gated automation later    |
| Provider policy churn               | Manifest-driven export specs, easy to revise     |
| Quota exhaustion                    | Per-channel quotas, retry policy, alerting       |
| License posture drift               | LicenseRegistry checks on every export           |
| Region-specific posting failures    | Per-region toggles in publishing rollout         |
| Distribution coupling               | OS never claims to replace the distributor       |

## Out Of Scope

Marketing Integrations deliberately do not include:

- Auto-publish in MVP.
- Real provider SDK calls in MVP.
- Spend operations in any sprint without explicit operator
  confirmation.
- Mutation of Brand Intelligence rules from integrations.
- Cross-channel cross-posting that bypasses per-channel review.
- Replacing the artist's distributor for Spotify, Apple, or others.

## Cross-Reference

- `docs/marketing/artist-marketing-os.md`
- `docs/marketing/visual-content-engine.md`
- `docs/marketing/data-model.md`
- `docs/marketing/roadmap.md`
- `docs/brand/manual-export-surface.md` (proposed sibling, not yet
  present)
