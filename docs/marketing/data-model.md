# Marketing Data Model

Entities introduced or extended by the Artist Marketing OS. Field
shapes are illustrative, not migration-ready. The migration plan lives
in `docs/marketing/roadmap.md` and will land per slice under
`packages/db`.

The model reuses Sprint 4 (`Artist`, `MusicRelease`, `Track`),
Sprint 5 (Brand Intelligence), Sprint 6 (Content Graph), Sprint 7
(Approval Review), and Sprint 8 (Controlled Generation) instead of
duplicating them.

## Conventions

- Identifiers are UUIDs unless noted.
- Status enums are uppercase snake case to match the archive convention.
- Timestamps are stored in UTC.
- Every artifact-producing entity references either a `ReviewItem` or a
  parent that does, never a private approval state.

## Reused Entities (existing, not redefined)

| Entity                | Source sprint           | Role for the Marketing OS                  |
| --------------------- | ----------------------- | ------------------------------------------ |
| `Artist`              | Sprint 4 archive         | Artist identity, symbol, status            |
| `MusicRelease`        | Sprint 4 archive         | Canonical music release record             |
| `Track`               | Sprint 4 archive         | Track metadata                             |
| `Fragment`            | Sprint 4 archive         | Reusable language and archive fragments    |
| `BrandRule`           | Sprint 5 brand           | Rule of behavior                           |
| `VisualRule`          | Sprint 5 brand           | Visual constraint                          |
| `LanguageRule`        | Sprint 5 brand           | Language constraint                        |
| `ForbiddenEnergy`     | Sprint 5 brand           | Forbidden motif or aesthetic               |
| `VoiceProfile`        | Sprint 5 brand           | How an artist speaks                       |
| `AudiencePersona`     | Sprint 5 brand           | Audience definition                        |
| `ChannelRule`         | Sprint 5 brand           | Channel-specific rule                      |
| `SignalScoringRule`   | Sprint 5 brand           | Evaluation rule                            |
| `CampaignWorld`       | Sprint 6 content graph   | Long-form campaign frame                   |
| `VisualEnvironment`   | Sprint 6 content graph   | Recurring visual setting                   |
| `MoodReference`       | Sprint 6 content graph   | Mood anchor                                |
| `Asset` (graph)       | Sprint 6 content graph   | Semantic asset reference                   |
| `AssetTag`            | Sprint 6 content graph   | Asset tag                                  |
| `ReleaseFragment`     | Sprint 6 content graph   | Release-side fragment                      |
| `ChannelFragment`     | Sprint 6 content graph   | Channel-side fragment                      |
| `ReviewItem`          | Sprint 7 approval review | Single source of approval state            |
| `ApprovalDecision`    | Sprint 7 approval review | Append-only approval history               |
| `GenerationRequest`   | Sprint 8 controlled gen  | Constrained planning record                |
| `GenerationOutput`    | Sprint 8 controlled gen  | Output bound to `ReviewItem`               |

## New Entities

### ArtistBrandProfile

Brand DNA snapshot per artist. References Sprint 5 entities by id.

```text
artist_brand_profile_id  uuid
artist_id                uuid (FK Artist)
display_name             text
brand_mood               text[]                 — declarative tags
audience_persona_ids     uuid[]                 — FK AudiencePersona[]
voice_profile_id         uuid                   — FK VoiceProfile
visual_rule_ids          uuid[]                 — FK VisualRule[]
language_rule_ids        uuid[]                 — FK LanguageRule[]
forbidden_energy_ids     uuid[]                 — FK ForbiddenEnergy[]
palette                  jsonb                  — { required, avoided }
typography               jsonb                  — { typefaces, weights }
visual_links             jsonb                  — anchor URLs to the brand archive
created_at               timestamp
updated_at               timestamp
```

Notes:

- The profile does not contain copy. Copy lives in `Fragment`.
- The profile does not include posting credentials or analytics
  endpoints.

### Release (Marketing view)

Marketing-side release wrapper. Optional link to a Sprint 4
`MusicRelease`.

```text
release_id            uuid
artist_id             uuid (FK Artist)
music_release_id      uuid? (FK MusicRelease)
release_code          text unique               — operator-readable code
title                 text
release_type          enum: single, ep, album, drop, merch, event
status                enum: DRAFT, PLANNED, RELEASED, ARCHIVED
release_date          date
primary_track_id      uuid? (FK Track)
campaign_id           uuid? (FK Campaign)
created_at            timestamp
updated_at            timestamp
```

`release_code` mirrors the archive convention used by `MusicRelease`.
A marketing `Release` may exist without a `MusicRelease` row, for
example for a merch drop or event.

### Campaign

```text
campaign_id      uuid
campaign_code    text unique
release_id       uuid? (FK Release)
artist_id        uuid (FK Artist)
objective        enum: RELEASE_LAUNCH, PRE_SAVE, DROP_WEEK, CLUB_TEASER,
                       MERCH_PUSH, SOUNDCLOUD_LAUNCH, TIKTOK_SNIPPET_PACK
channels         enum_set: SOUNDCLOUD, INSTAGRAM, TIKTOK, YOUTUBE, SPOTIFY,
                            EMAIL, DISCORD
status           enum: DRAFT, IN_REVIEW, SCHEDULED, LIVE, COMPLETE, ARCHIVED
start_date       date
end_date         date
created_at       timestamp
updated_at       timestamp
```

A `Campaign` is not an approval surface. Approval state lives on the
artifacts that hang under the campaign.

### CreativeBrief

Operator-authored brief that compiles into one or more
`GenerationRequest` records.

```text
creative_brief_id        uuid
campaign_id              uuid (FK Campaign)
brief_code               text unique
title                    text
objective                text
mood_reference_ids       uuid[]                  — FK MoodReference[]
campaign_world_id        uuid? (FK CampaignWorld)
visual_environment_id    uuid? (FK VisualEnvironment)
brand_lock_snapshot_id   uuid (FK BrandLockSnapshot)
channels                 enum_set
format_keys              text[]                  — keys from format catalog
status                   enum: DRAFT, READY, IN_GENERATION, COMPLETE
created_at               timestamp
updated_at               timestamp
```

### BrandLockSnapshot

Freeze-frame of the brand state for a creative brief.

```text
brand_lock_snapshot_id   uuid
artist_brand_profile_id  uuid (FK ArtistBrandProfile)
voice_profile_id         uuid
campaign_world_id        uuid?
visual_environment_id    uuid?
mood_reference_ids       uuid[]
visual_rules             jsonb                   — required/allowed/discouraged/forbidden
forbidden_energy         jsonb
palette                  jsonb
typography               jsonb
format_rules             jsonb
runtime_rules            jsonb
created_at               timestamp
```

A `BrandLockSnapshot` is immutable. New constraints create a new
snapshot referenced by a new brief.

### CreativeAsset

Marketing-side artifact wrapper. Backed by a Sprint 8
`GenerationOutput`, never standalone.

```text
creative_asset_id        uuid
generation_output_id     uuid (FK GenerationOutput)
review_item_id           uuid (FK ReviewItem)
campaign_id              uuid (FK Campaign)
creative_brief_id        uuid (FK CreativeBrief)
asset_kind               enum: COVER, REEL, STORY, POSTER, BANNER, CANVAS,
                                LYRIC_CLIP, AD_CREATIVE, PRESS_IMAGE, CAPTION
format_key               text                    — from format catalog
provider_group           enum: IMAGE_GENERATION, CLIP_GENERATION,
                                TEMPLATE_RENDERING, CAPTION_GENERATION
file_path                text
duration_seconds         numeric?
status                   enum: DRAFT, NEEDS_REVIEW, APPROVED, REJECTED, EXPORTED
commercial_status        enum: REVIEW_NEEDED, APPROVED, BLOCKED
compliance_record_id     uuid (FK ComplianceRecord)
created_at               timestamp
updated_at               timestamp
```

`status` is the materialized review state. Approval truth still lives
in `ApprovalDecision` history per Sprint 7.

### AssetVersion

Versioned variants under a `CreativeAsset`.

```text
asset_version_id      uuid
creative_asset_id     uuid (FK CreativeAsset)
version_index         int
file_path             text
prompt_used           text
seed                  text?
parameters            jsonb
created_at            timestamp
```

A new version is the artifact of a re-generation. Versions never mutate
approval truth.

### ChannelExport

Channel-specific export pack for an approved asset.

```text
channel_export_id        uuid
creative_asset_id        uuid (FK CreativeAsset)
channel                  enum: INSTAGRAM_FEED, INSTAGRAM_STORY, INSTAGRAM_REEL,
                                TIKTOK, YOUTUBE_SHORT, YOUTUBE_VIDEO,
                                SOUNDCLOUD_BANNER, SPOTIFY_CANVAS, EMAIL, DISCORD
format_requirements      jsonb
export_path              text
caption_pack_id          uuid? (FK CaptionPack)
status                   enum: PENDING, READY, FAILED
checklist                jsonb
created_at               timestamp
```

A `ChannelExport` may only be created from an approved
`CreativeAsset`. Blocked assets cannot enter an export, regardless of
status.

### CaptionPack

Text-only artifact tied to a campaign or a creative asset.

```text
caption_pack_id         uuid
campaign_id             uuid (FK Campaign)
creative_brief_id       uuid? (FK CreativeBrief)
audience_persona_id     uuid? (FK AudiencePersona)
voice_profile_id        uuid (FK VoiceProfile)
brand_lock_snapshot_id  uuid (FK BrandLockSnapshot)
channels                enum_set
variants                jsonb                   — per channel variants
status                  enum: DRAFT, NEEDS_REVIEW, APPROVED, REJECTED
created_at              timestamp
updated_at              timestamp
```

### CampaignTask

Operator task that drives the calendar.

```text
campaign_task_id      uuid
campaign_id           uuid (FK Campaign)
title                 text
description           text
due_date              date
status                enum: TODO, IN_PROGRESS, BLOCKED, DONE
linked_export_id      uuid? (FK ChannelExport)
created_at            timestamp
updated_at            timestamp
```

### AnalyticsSnapshot

Manual or imported KPI snapshot.

```text
analytics_snapshot_id   uuid
artist_id               uuid (FK Artist)
release_id              uuid? (FK Release)
campaign_id             uuid? (FK Campaign)
channel                 enum
captured_at             timestamp
captured_by             enum: MANUAL, AUTO_IMPORT
payload                 jsonb
notes                   text?
```

The payload is intentionally schema-light to accommodate channel
variance. Cross-channel reporting consumes the payload through a
read adapter, not a normalized table, until aggregation matures.

### ComplianceRecord

Per-artifact compliance footprint. Mirrors the audio compliance
pattern.

```text
compliance_record_id      uuid
generation_output_id      uuid (FK GenerationOutput)
prompt                    text
prompt_template_id        uuid
brand_lock_snapshot_id    uuid (FK BrandLockSnapshot)
provider_group            text
provider_id               text              — registry id, debug context
model_id                  text              — debug context
seed                      text?
parameters                jsonb
license_tag               text
commercial_status         enum: REVIEW_NEEDED, APPROVED, BLOCKED
human_approved_by         uuid?             — from ApprovalDecision
human_approved_at         timestamp?
generated_at              timestamp
```

## Relationship Map

```text
Artist 1—1 ArtistBrandProfile
Artist 1—* Release
Release *—? MusicRelease
Release 1—1 Campaign
Campaign 1—* CreativeBrief
Campaign 1—* CampaignTask
Campaign 1—* AnalyticsSnapshot
CreativeBrief 1—* GenerationRequest (Sprint 8)
GenerationRequest 1—1 ReviewItem (Sprint 7)
GenerationOutput 1—1 CreativeAsset
CreativeAsset 1—* AssetVersion
CreativeAsset 1—* ChannelExport
CreativeBrief 1—1 BrandLockSnapshot
CreativeAsset 1—1 ComplianceRecord
CaptionPack *—? CreativeBrief
CaptionPack 1—1 BrandLockSnapshot
```

## Status Lifecycle Summary

```text
Release          DRAFT → PLANNED → RELEASED → ARCHIVED
Campaign         DRAFT → IN_REVIEW → SCHEDULED → LIVE → COMPLETE → ARCHIVED
CreativeBrief    DRAFT → READY → IN_GENERATION → COMPLETE
CreativeAsset    DRAFT → NEEDS_REVIEW → APPROVED | REJECTED → EXPORTED
CaptionPack      DRAFT → NEEDS_REVIEW → APPROVED | REJECTED
ChannelExport    PENDING → READY | FAILED
CampaignTask     TODO → IN_PROGRESS | BLOCKED → DONE
```

`commercial_status` is an independent axis. It can block any artifact
regardless of `status`.

## Out Of Scope

The Marketing data model deliberately does not introduce:

- A parallel approval store.
- Commerce, cart, or fulfillment entities.
- Direct social network token storage in the model layer; tokens live
  in vaults outside the schema.
- Auto-derived performance signals; analytics stay snapshot-shaped
  until aggregation matures.
- Engagement-first scoring rules; scoring rules remain in Sprint 5.

## Cross-Reference

- `docs/marketing/artist-marketing-os.md`
- `docs/marketing/visual-content-engine.md`
- `docs/marketing/integrations.md`
- `docs/marketing/roadmap.md`
- `docs/brand/controlled-generation-layer.md`
- `docs/brand/approval-review-system.md`
- `docs/architecture.md`
