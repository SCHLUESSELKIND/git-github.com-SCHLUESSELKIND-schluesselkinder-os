# Content Graph + Asset Orchestration

## Purpose

Sprint 6 adds the semantic layer before campaign generation.

It models what belongs together, what is required, what is discouraged, and what is forbidden across releases, assets, symbols, fragments, campaign worlds, channel fragments, visual environments, and operational mood references.

This is not a posting system, generation system, approval system, asset upload system, or admin surface.

## Core Principle

The graph exists so the future Signal Engine can understand context before producing any proposal.

The path is:

```text
Artist
Track / MusicRelease
CampaignWorld
VisualEnvironment
MoodReference
Asset
Fragment
ChannelFragment
Compatibility
```

The graph answers:

- Which world does this release belong to?
- Which visual environment is required?
- Which symbol is institutional?
- Which asset is only secondary?
- Which channel fragment is allowed?
- Which combination creates brand drift?

## Compatibility Verdicts

Compatibility is not binary.

- `REQUIRED`: must appear or remain attached.
- `ALLOWED`: compatible without being mandatory.
- `DISCOURAGED`: possible only with review and a clear reason.
- `FORBIDDEN`: must not be used.

Examples:

- `ROOM_AFTER_LIGHT` requires `DUNGEON_CHAIR_PRIMARY`.
- `COLD_ARCHIVE` requires `RUNE_KEY_SYMBOL`.
- `ROPEFACE_ARTIST_STAMP` is discouraged as a primary campaign-world asset.
- `ROPEFACE_ARTIST_STAMP` is forbidden as institutional archive language.
- `SHIBARI_KAWAII_WORDMARK` is forbidden as a concrete signal lead asset.
- Collage energy, cyberpunk glow, luxury flex, horror props, and meme captions remain outside the graph.

## Campaign Worlds

Campaign worlds are not marketing concepts. They are controlled semantic environments.

Initial worlds:

- `ROOM_AFTER_LIGHT`
- `COLD_ARCHIVE`
- `CONCRETE_SIGNAL`
- `POST_CLUB_SILENCE`

## Visual Environments

Visual environments describe recurring image logic.

Initial environments:

- `DUNGEON_CHAIR_PRIMARY`
- `BLACK_FABRIC_VOID`
- `CONCRETE_WALL_LOW_LIGHT`
- `ARCHIVE_OBJECT_TABLE`

The chair environment remains the primary recurring campaign environment.

## Mood References

Mood references must stay operational and machine-readable.

Allowed examples:

- `INSTITUTIONAL_COLDNESS`
- `EMPTY_ROOM_PRESSURE`
- `TENSION_LOW_LIGHT`
- `BLACKOUT_SILENCE`
- `POST_CLUB_MELANCHOLY`

Avoid poetic or moodboard naming. Do not introduce codes like soft darkness, dreamcore melancholy, or lonely neon heartbreak.

## Assets

Assets are symbolic references only.

The `Asset.referenceKey` field is intentionally not a URL, file path, upload pointer, CDN key, or image metadata object.

Sprint 6 does not introduce:

- uploads
- CDN logic
- storage providers
- dimensions
- file processing
- image metadata systems
- variants or thumbnails

Initial assets:

- `CHAIR_CAMPAIGN_ENVIRONMENT`
- `RUNE_KEY_SYMBOL`
- `ROPEFACE_ARTIST_STAMP`
- `SHIBARI_KAWAII_WORDMARK`
- `EIN_POSTER_TEXTURE`

## Fragments

Release fragments attach language to releases and tracks.

Channel fragments attach language to channels, worlds, and mood references.

Fragments remain sparse, German-first, and metadata-driven.

## Non-Goals

- No AI generation.
- No prompts.
- No moodboard generation.
- No approval queue.
- No posting.
- No scheduling.
- No automation.
- No admin UI.
- No uploads.
- No commerce.

## Future Use

Sprint 7 can add approvals and rule violation review.

Sprint 8 can add controlled generation, but only inside this graph and never as autonomous publishing.
