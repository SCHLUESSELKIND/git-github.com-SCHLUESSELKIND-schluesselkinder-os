# Visual Content Engine

Routing, brand lock, and review semantics for every visual artifact the
Marketing OS produces. Image generation, clip generation, and template
rendering share one engine and three intent groups.

This is a planning document. Provider names appear in routing and
compliance contexts only. The operator UI surfaces creative actions
described in `docs/marketing/artist-marketing-os.md`.

## Intent Groups

The Marketing OS adds three provider groups to the existing registry
pattern from `docs/soundsystem/model-provider-strategy.md`.

| Group                          | Intent                                                  |
| ------------------------------ | ------------------------------------------------------- |
| `image_generation_provider`    | Still images: covers, posters, portraits, banners, stills |
| `clip_generation_provider`     | Motion: visualizers, reels, stories, lyric snippets       |
| `template_rendering_provider`  | Deterministic frame composition for logos, titles, dates  |

The router resolves one provider per group per request. The registry
selects the provider based on capability, license posture, format
requirements, and risk tier.

## Risk Tiers

The Marketing OS reuses the audio engine tier scheme.

| Tier  | Meaning                                                             |
| ----- | ------------------------------------------------------------------- |
| green | Permissive license, low ambiguity, safe defaults                    |
| amber | License or consent caveat; requires operator review per use         |
| red   | Cannot ship without explicit additional legal work                  |

A provider may belong to multiple groups at different tiers.

## Image Generation Flow

```text
CreativeBrief
  → BrandLockSnapshot (visual rules, forbidden energy, palette)
  → ImagePromptDraft (operator)
  → PromptCompiler (system, adds brand lock, negative directives)
  → GenerationRequest (bound to ReviewItem)
  → image_generation_provider (registry)
  → CreativeAsset (file, format, metadata, ComplianceRecord)
  → Approval Review
```

### Provider Candidates (routing, not UI)

| Provider                      | Tier  | Notes                                                                 |
| ----------------------------- | ----- | --------------------------------------------------------------------- |
| Mock provider                 | green | Local deterministic stub, always available, MVP default               |
| OpenAI image generation       | amber | Vendor terms, content policy, requires license review                 |
| Stability AI Flux / SDXL      | amber | Open weights, license per checkpoint, requires registry validation    |
| Local ComfyUI workflows       | green | Self-hosted; license posture per checkpoint, full control over data   |
| Recraft, Ideogram, Midjourney | red   | Manual-only; no API integration in MVP, license review per export     |

Activation requires a `ModelRegistry` row with `commercial_status =
ready` and a `LicenseRegistry` reference whose `permits_commercial`
matches the intended use, mirroring the audio pattern.

## Clip Generation Flow

```text
CreativeBrief
  → BrandLockSnapshot (motion rules, format requirements)
  → StoryboardDraft (operator, optional shot list)
  → ClipPromptDraft (operator)
  → PromptCompiler (system)
  → GenerationRequest (bound to ReviewItem)
  → clip_generation_provider (registry)
  → CreativeAsset (file, duration, codec, audio status, ComplianceRecord)
  → Approval Review
```

### Provider Candidates (routing, not UI)

| Provider           | Tier  | Notes                                                                                  |
| ------------------ | ----- | -------------------------------------------------------------------------------------- |
| Mock provider      | green | Local deterministic stub for MVP                                                       |
| Runway             | amber | Vendor terms, commercial allowed under plan; check per-output rights                   |
| Luma               | amber | Vendor terms; check per-output rights                                                  |
| Kling              | amber | Vendor terms; jurisdiction caveats; check per-output rights                            |
| Pika               | amber | Vendor terms; check per-output rights                                                  |
| Local image-to-video stacks | amber | Open weights; license per checkpoint; high operational overhead                |
| FFmpeg + Remotion  | green | Deterministic motion from approved stills and templates; default for branded titles    |

For consistent typography, logos, release dates, and channel-specific
overlays, the engine prefers `template_rendering_provider` over a
generative clip model. Generative clips supply atmosphere; templates
supply legibility.

## Template Rendering Flow

```text
TemplatePack (declarative composition spec)
  → InputAssets (approved stills, audio, text)
  → BrandLockSnapshot
  → template_rendering_provider (Remotion or FFmpeg)
  → CreativeAsset (deterministic output, recordable seed)
  → Approval Review (optional, if assets already approved)
```

Template packs are versioned and live under
`packages/brand` once introduced. Each pack declares format,
typography, motion, and constraints. Renaming or breaking a pack is
a planning decision.

## Brand Lock

`BrandLockSnapshot` is the freeze-frame of brand state for a single
generation request. It captures:

```text
artist_id
artist_brand_profile_id
voice_profile_id
campaign_world_id
visual_environment_id
mood_reference_ids
visual_rules: required, allowed, discouraged, forbidden
forbidden_energy: list of forbidden motifs and aesthetics
palette: required colors, avoided colors, contrast rules
typography: required typefaces, allowed weights
format_rules: aspect ratio, safe zones, channel constraints
runtime_rules: duration min/max, audio policy
```

A request without a frozen `BrandLockSnapshot` cannot reach a
generation provider. The snapshot is recorded under
`ComplianceRecord` alongside the prompt and provider metadata.

## Prompt Provenance

Every generation request and every artifact carries:

```text
prompt: compiled prompt sent to the provider
prompt_template_id: which template compiled it
brand_lock_snapshot_id: which snapshot constrained it
provider_group: image, clip, or template_rendering
provider_id: registry row (debug context only)
model_id: model identifier (debug context only)
seed: deterministic seed where supported
parameters: provider-specific parameter dictionary
license_tag: derived from LicenseRegistry at request time
commercial_status: review_needed, approved, or blocked
human_approved_by: operator id from ApprovalDecision, or null
generated_at: timestamp
```

This record is the minimum compliance footprint per artifact. It
mirrors the audio engine pattern.

## Format Outputs

The engine exposes named formats. Channel-specific export requirements
live in `docs/marketing/integrations.md`.

| Format key            | Aspect | Typical duration | Typical use                              |
| --------------------- | ------ | ---------------- | ---------------------------------------- |
| `cover_square`        | 1:1    | n/a              | Release cover, podcast art, single art   |
| `poster_portrait`     | 4:5    | n/a              | Feed posters, campaign posters           |
| `story_vertical`      | 9:16   | n/a              | IG / TikTok stories, static or motion    |
| `reel_vertical`       | 9:16   | 10–30s           | Reels, TikTok, Shorts                    |
| `clip_widescreen`     | 16:9   | up to 60s        | YouTube, web embeds                      |
| `canvas_loop`         | 9:16   | 3–8s             | Spotify Canvas                           |
| `lyric_snippet`       | 9:16   | 6–15s            | Lyric promo clip                         |
| `banner_wide`         | 4:1    | n/a              | SoundCloud / channel banner              |
| `thumbnail_youtube`   | 16:9   | n/a              | Video thumbnail                          |

Format keys are stable. Adding or renaming a format key is a planning
decision.

## Review And Approval States

Every `CreativeAsset` carries a status field that follows the
Sprint 7 Approval Review semantics:

```text
draft
needs_review
approved
rejected
exported
```

`exported` is set only after a `ChannelExport` record is materialized
and bundled. The Sprint 7 contract still holds: approval truth lives in
`ApprovalDecision` history; `CreativeAsset.status` is materialized
state for display.

A separate field captures commercial posture:

```text
commercial_status: review_needed | approved | blocked
```

`commercial_status = blocked` overrides everything; a blocked asset
cannot enter a `ChannelExport`, regardless of `status`.

## Mock-First MVP Posture

The MVP renders neither real images nor real clips. The engine produces
placeholder artifacts with full metadata. This keeps the schema, the
review flow, and the export pipeline honest while no provider SDK is
linked.

The mock provider returns:

- A deterministic placeholder asset path.
- A complete `ComplianceRecord` with `commercial_status = approved` for
  mock outputs only.
- A `BrandLockSnapshot` reference.

A real provider may only be linked once the registry rows are present
and the operator activates the provider through a registry mutation —
not from the Marketing OS UI.

## Out Of Scope

The Visual Content Engine deliberately does not include:

- Real provider SDK calls or HTTP integrations.
- Account management for any third-party generator.
- Live cost reporting or per-request billing.
- Image super-resolution, upscaling, or face-restoration as separate
  operator actions in MVP.
- Auto-publish or scheduling.
- Automatic background music selection for clips.
- Lyric extraction from audio in MVP.

## Cross-Reference

- `docs/marketing/artist-marketing-os.md`
- `docs/marketing/data-model.md`
- `docs/marketing/integrations.md`
- `docs/marketing/roadmap.md`
- `docs/soundsystem/model-provider-strategy.md`
- `docs/brand/controlled-generation-layer.md`
- `docs/brand/approval-review-system.md`
