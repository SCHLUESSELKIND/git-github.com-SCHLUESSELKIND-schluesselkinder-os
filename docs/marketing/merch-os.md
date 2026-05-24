# MERCH OS — Internal Strategy Layer

Internal strategy document for the SCHLUESSELKINDER merch system.
This is NOT a Shopify clone, NOT a Printful-only integration, NOT a
public storefront. It is a production-side merch planning layer for
limited drops, collector culture, vinyl-on-demand, event capsules, and
release-linked merchandise.

## Guiding Posture

SCHLUESSELKINDER merch is anti-fast-fashion by design. The system
enforces scarcity, controls availability windows, and treats every
physical object as a cultural artifact — not a revenue-per-impression
play.

Hard rules:

1. **No Redbubble / Spreadshirt / Teespring / Society6 / Amazon Merch.**
   These providers are permanently excluded. They contradict the
   collector posture, leak brand control, and enable infinite stock.
2. **No public provider names in operator create flows.** The operator
   sees intents (`DROP CAPSULE`, `PRESS VINYL`), never adapter names.
3. **No commerce spam patterns.** No upsell modals, no cart abandonment
   emails, no urgency countdowns, no "only 3 left" badges.
4. **70 / 20 / 10 availability rule.** At any point: 70% of the catalog
   is unavailable (archived / unreleased), 20% is limited (active drop
   window), 10% is always available (core essentials).
5. **Three-provider maximum.** Complexity stays bounded.
6. **Upload only.** The system writes to providers. It never pulls
   customer data, never runs retargeting, never syncs order lists into
   the operator console.

## Provider Groups

Three provider groups. Provider names appear in this document and in
routing/compliance docs only — never in the operator UI.

| Group                    | Provider              | Role                                      | Tier         |
| ------------------------ | --------------------- | ----------------------------------------- | ------------ |
| `apparel_provider`       | Printful              | Essentials: tees, hoodies, bags           | Core         |
| `premium_drop_provider`  | Gelato                | Premium/event: poster, canvas, hardcover  | Limited Drop |
| `vinyl_provider`         | elasticStage + DISC_ARCHIVE | Vinyl press, dubplate, white-label  | Cult Object  |

### Provider Isolation Rules

- Each provider group gets a Protocol boundary (same pattern as
  `DropboxSyncProviderProtocol`, `LyricsProviderProtocol`).
- Mock adapters are the default. Real adapters are gated behind env
  vars (`MERCH_APPAREL_PROVIDER`, `MERCH_DROP_PROVIDER`,
  `MERCH_VINYL_PROVIDER`).
- No silent fallback. If a real provider is selected without
  credentials, the service fails at startup.
- Providers never see internal entity IDs. They receive sanitized
  payloads with only the data required for fulfillment.

## Data Model

### MerchCapsule

A capsule is the top-level grouping. It may be linked to a
`ReleasePack`, an event, or stand alone. A capsule has an availability
window and a drop strategy.

```text
merch_capsule_id         uuid
title                    text
slug                     text (unique, url-safe)
artist_id                uuid (FK Artist)
release_pack_id          uuid | null (FK ReleasePack)
event_tag                text | null
drop_strategy            enum (IMMEDIATE, COUNTDOWN, WAITLIST, EVENT_GATE)
availability_tier        enum (CORE_ESSENTIAL, LIMITED_DROP, CULT_OBJECT)
status                   enum (DRAFT, ANNOUNCED, ACTIVE, EXPIRED, ARCHIVED)
window_opens_at          timestamp | null
window_closes_at         timestamp | null
max_units                int | null — hard cap (null = no cap, only for CORE_ESSENTIAL)
units_claimed            int (default 0)
visual_direction_id      uuid | null (FK VisualEnvironment)
operator_id              text
created_at               timestamp
updated_at               timestamp
```

### MerchProduct

A single product within a capsule. Linked to exactly one provider
group.

```text
merch_product_id         uuid
capsule_id               uuid (FK MerchCapsule)
title                    text
product_type             enum (TEE, HOODIE, TOTE, POSTER, CANVAS, HARDCOVER, VINYL_12, VINYL_7, DUBPLATE, WHITE_LABEL, SLIPMAT, STICKER_PACK)
provider_group           enum (apparel_provider, premium_drop_provider, vinyl_provider)
base_cost_eur            decimal | null — provider cost estimate
suggested_price_eur      decimal | null
weight_grams             int | null
is_preorder              bool (default false)
mockup_id                uuid | null (FK ProductMockup)
status                   enum (DRAFT, READY, FULFILLED, DISCONTINUED)
created_at               timestamp
updated_at               timestamp
```

### MerchVariant

Size/color/format variant of a product.

```text
merch_variant_id         uuid
product_id               uuid (FK MerchProduct)
variant_label            text — e.g. "L / Black", "180g Clear"
sku_suffix               text — appended to product SKU
provider_variant_ref     text | null — external variant ID at provider
stock_limit              int | null — per-variant cap
units_sold               int (default 0)
status                   enum (AVAILABLE, SOLD_OUT, DISCONTINUED)
```

### MerchDrop

A scheduled drop event. One capsule may have multiple drops (e.g.
pre-sale + general).

```text
merch_drop_id            uuid
capsule_id               uuid (FK MerchCapsule)
drop_label               text — "Pre-Sale", "General Drop", "Event Exclusive"
scheduled_at             timestamp
actual_opened_at         timestamp | null
closes_at                timestamp | null
notify_list_id           uuid | null — waitlist reference (external)
status                   enum (SCHEDULED, LIVE, CLOSED, CANCELLED)
operator_notes           text | null
```

### MerchAvailability

Point-in-time availability snapshot. Used for the 70/20/10 audit.

```text
merch_availability_id    uuid
snapshot_at              timestamp
total_products           int
unavailable_count        int
limited_count            int
always_available_count   int
ratio_unavailable        float
ratio_limited            float
ratio_available          float
compliant                bool — true if 70/20/10 holds
```

### MerchProviderGroup

Registry entry for a provider group (matches the pattern from
`model-provider-strategy.md`).

```text
merch_provider_group_id  uuid
group_key                text (unique) — apparel_provider | premium_drop_provider | vinyl_provider
display_label            text — shown only in admin/compliance views
mock_adapter             text — module path
real_adapter             text | null — module path (null until activated)
env_var                  text — activation env var name
commercial_status        enum (RESEARCH_ONLY, READY, ACTIVE, DEPRECATED)
capabilities             text[] — e.g. ["tee", "hoodie", "poster"]
cost_model               jsonb — base cost ranges per product type
```

### VinylReleaseObject

Dedicated entity for vinyl/dubplate orders. These are high-value cult
objects with their own lifecycle.

```text
vinyl_release_id         uuid
capsule_id               uuid (FK MerchCapsule)
product_id               uuid (FK MerchProduct)
release_pack_id          uuid | null (FK ReleasePack)
format                   enum (VINYL_12, VINYL_7, DUBPLATE, WHITE_LABEL)
weight                   enum (STANDARD_140G, HEAVY_180G, EXTRA_200G)
color                    text — "Black", "Clear", "Splatter Red/Black"
pressing_quantity        int
label_artwork_asset_id   uuid | null (FK CreativeAsset)
sleeve_artwork_asset_id  uuid | null (FK CreativeAsset)
mastering_job_id         uuid | null (FK MasterBusJob — from Soundsystem)
audio_source             enum (MASTER_BUS, EXTERNAL_FILE, DUBPLATE_LIVE)
cutting_notes            text | null — lathe cut / pressing notes
test_press_requested     bool (default true)
provider_order_ref       text | null — elasticStage/DISC_ARCHIVE order ID
status                   enum (DRAFT, ARTWORK_PENDING, AUDIO_PENDING, SUBMITTED, TEST_PRESS, APPROVED, IN_PRODUCTION, SHIPPED, ARCHIVED)
soundcloud_vinyl_cta     bool (default false) — link to SoundCloud release
estimated_delivery_at    timestamp | null
created_at               timestamp
updated_at               timestamp
```

### ProductMockup

Visual mockup of a product. Generated or uploaded. Bound to
`ReviewItem` for approval.

```text
product_mockup_id        uuid
product_id               uuid (FK MerchProduct)
mockup_type              enum (FLAT_LAY, WORN, ENVIRONMENT, VINYL_SLEEVE, VINYL_LABEL, POSTER_FRAME)
file_path                text | null
generation_request_id    uuid | null (FK GenerationRequest)
review_item_id           uuid | null (FK ReviewItem)
status                   enum (DRAFT, PENDING_REVIEW, APPROVED, REJECTED)
created_at               timestamp
```

### MerchExportPack

Bundled export of capsule data for fulfillment provider submission or
Dropbox archive.

```text
merch_export_pack_id     uuid
capsule_id               uuid (FK MerchCapsule)
export_type              enum (PROVIDER_SUBMISSION, DROPBOX_ARCHIVE, PRESS_KIT)
included_products        uuid[] — product IDs
included_mockups         uuid[] — mockup IDs
manifest                 jsonb — full export manifest
dropbox_target           text | null
status                   enum (BUILDING, READY, EXPORTED)
created_at               timestamp
```

## Operator Intents

The operator UI exposes creative actions. Provider routing is internal.

| Intent                     | Description                                          | Provider Group         |
| -------------------------- | ---------------------------------------------------- | ---------------------- |
| `DROP CAPSULE`             | Create a new merch capsule with products and window  | (multi)                |
| `PRESS VINYL`             | Commission vinyl/dubplate from a ReleasePack         | vinyl_provider         |
| `GENERATE MOCKUP`          | Create product mockup via controlled generation      | (visual engine)        |
| `SUBMIT TO PROVIDER`       | Send ready products to fulfillment provider          | per-product group      |
| `ARCHIVE CAPSULE`          | Close a capsule and move to archive tier             | —                      |
| `EXTEND DROP WINDOW`       | Push the close date of an active drop                | —                      |
| `AUDIT AVAILABILITY`       | Run 70/20/10 compliance check                        | —                      |
| `EXPORT MERCH PACK`        | Bundle capsule for Dropbox or press kit              | storage_sync_provider  |
| `LINK RELEASE`             | Bind a capsule to an existing ReleasePack            | —                      |

## Release-Linked Flows

The primary flow connects Soundsystem output to physical objects:

```text
ReleasePack (S22)
  → MerchCapsule (linked via release_pack_id)
    → MerchProduct (VINYL_12)
      → VinylReleaseObject
        → mastering_job_id (from MASTER BUS)
        → audio validated against SoundGraph arrangement
        → artwork from Marketing OS CreativeAsset pipeline
        → submitted to vinyl_provider
    → MerchProduct (TEE, POSTER)
      → mockups generated via visual engine
      → submitted to apparel_provider / premium_drop_provider
    → MerchDrop (scheduled around SoundCloud release date)
      → capsule window aligns with release marketing campaign
  → MerchExportPack (DROPBOX_ARCHIVE)
    → synced via existing Dropbox adapter (S21)
```

The `LINK RELEASE` intent is the entry point. It creates the capsule
scaffold and pre-populates product suggestions based on the release
metadata (genre, energy, campaign world).

### SoundCloud Vinyl CTA

When `soundcloud_vinyl_cta = true` on a VinylReleaseObject, the
Marketing OS generates a link card asset for the SoundCloud release
description. This is a static asset — no SoundCloud API write. The
operator pastes it manually until the SoundCloud OAuth slice (M-14)
lands.

## Anti-Fast-Fashion Constraints

### Catalog Composition Rule (70/20/10)

At any given time, the full catalog must satisfy:

- **70% unavailable** — archived, unreleased, or expired drops.
- **20% limited** — active drop windows with unit caps or time gates.
- **10% always available** — core essentials with no artificial scarcity.

The `AUDIT AVAILABILITY` intent runs a point-in-time check and
produces a `MerchAvailability` snapshot. If the ratio is violated, the
operator receives a warning — but no auto-correction. The operator
decides what to archive.

### Unit Caps

- `CULT_OBJECT` tier: hard cap required (`max_units` must be set).
  Typical: 50–300 for vinyl, 25–100 for dubplate.
- `LIMITED_DROP` tier: hard cap or time window required (at least one).
- `CORE_ESSENTIAL` tier: no cap required.

### Drop Window Enforcement

- A drop window cannot exceed 14 days for `LIMITED_DROP` products.
- A drop window cannot exceed 72 hours for `CULT_OBJECT` products.
- `EXTEND DROP WINDOW` requires explicit operator confirmation and logs
  an audit event.

### No Infinite Restock

Once a `LIMITED_DROP` or `CULT_OBJECT` capsule reaches `EXPIRED` or
`ARCHIVED` status, it cannot be re-opened. The operator must create a
new capsule if a repress is desired. This prevents invisible restocks
that undermine collector trust.

### Production Minimums

- Vinyl: minimum 50 units per pressing (elasticStage constraint).
- Dubplate: minimum 1 (lathe cut), typically 1–10.
- Apparel: no minimum (print-on-demand via Printful).
- Premium: no minimum (print-on-demand via Gelato).

## Vinyl Strategy

### Provider Chain

1. **elasticStage** — vinyl pressing (12", 7"). Handles mastering
   transfer, test press, production run. EU-based.
2. **DISC_ARCHIVE** — dubplate cutting and white-label service.
   Single-unit lathe cuts for DJ sets and collector editions.

### Formats

| Format       | Use Case                           | Min Qty | Typical Run |
| ------------ | ---------------------------------- | ------- | ----------- |
| VINYL_12     | Full release, EP, album            | 50      | 100–300     |
| VINYL_7      | Single, B-side exclusive           | 50      | 100–200     |
| DUBPLATE     | DJ exclusive, event giveaway       | 1       | 1–10        |
| WHITE_LABEL  | Anonymous promo, DJ pool           | 25      | 25–100      |

### Audio Pipeline

The vinyl audio source flows from the Soundsystem MASTER BUS:

```text
SoundGraph Arrangement
  → Music Router Job (completed artifacts)
    → MASTER BUS Job (vinyl mastering mode)
      → VinylReleaseObject.mastering_job_id
```

The MASTER BUS already supports a `vinyl` mastering mode (defined in
`docs/soundsystem/master-bus.md`). The vinyl provider receives the
mastered WAV — no additional DSP happens outside the Soundsystem
boundary.

### Artwork Pipeline

Label and sleeve artwork flows from the Marketing OS visual engine:

```text
CreativeBrief (brand-locked)
  → GenerationRequest (controlled generation)
    → GenerationOutput (ReviewItem-bound)
      → CreativeAsset (approved)
        → VinylReleaseObject.label_artwork_asset_id
        → VinylReleaseObject.sleeve_artwork_asset_id
```

### SoundCloud ↔ Vinyl Link

Every vinyl release that ships can optionally generate a "vinyl
available" CTA asset. This is a static image card with:

- Release title + artist
- Vinyl format + color
- "Limited to N copies"
- No purchase link (link is added manually by operator)

The card is placed in the Dropbox export pack for manual paste into
SoundCloud descriptions.

## Admin Route Map (Future)

All routes live under the existing Marketing OS admin surface, gated
behind `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED`.

```text
/admin/marketing/merch              — Capsule overview (5-lane board)
/admin/marketing/merch/[capsule_id] — Capsule detail + product list
/admin/marketing/merch/drops        — Drop calendar / timeline view
/admin/marketing/merch/vinyl        — Vinyl workspace (pressing status)
/admin/marketing/merch/mockups      — Mockup gallery + approval flow
/admin/marketing/merch/archive      — Expired/archived capsules (read-only)
/admin/marketing/merch/audit        — 70/20/10 availability dashboard
```

### Capsule Board Lanes

The operator hub shows capsules in five lanes:

| Lane         | Status filter                    |
| ------------ | -------------------------------- |
| DRAFT        | `status = DRAFT`                 |
| ANNOUNCED    | `status = ANNOUNCED`             |
| ACTIVE       | `status = ACTIVE`                |
| EXPIRED      | `status = EXPIRED`               |
| ARCHIVED     | `status = ARCHIVED`              |

## Visual Direction

The merch admin interface follows the SCHLUESSELKINDER visual system:

- **Dark minimal.** No bright ecommerce aesthetics.
- **Industrial typography.** Same system as the Operator Console.
- **No product photography grids.** Mockups shown one-at-a-time in
  detail view, not in a marketplace browse layout.
- **No shopping cart metaphor.** Products are "commissioned" or
  "submitted", never "added to cart".
- **Monochrome default.** Color only in mockup previews and vinyl
  artwork. The UI itself stays dark/neutral.
- **Status over decoration.** Every card shows status, unit count,
  and window timer. No lifestyle imagery in the admin.

## Automation Boundaries

### Allowed (operator-triggered)

- Capsule creation from ReleasePack metadata (pre-populated scaffold).
- Mockup generation via controlled generation pipeline.
- Provider submission of ready products (operator confirms).
- Dropbox export of merch packs.
- 70/20/10 audit calculation.
- Social copy generation for drop announcements (text only, via
  CaptionPack pattern).

### Not Allowed (requires dedicated planning doc)

- Auto-pricing based on demand signals.
- Auto-restock or auto-repress decisions.
- Purchase flow / checkout / payment processing.
- Customer data import or CRM sync.
- Real-time inventory polling from providers.
- Auto-publishing drop announcements to social channels.
- Ad creative generation tied to merch products.
- Discount codes or promotional pricing.
- Affiliate or referral systems.
- Email marketing automation for drops.

## Roadmap (M-12 through M-18)

Continues the Marketing OS roadmap sequence. The existing M-11 through
M-20 in `docs/marketing/roadmap.md` cover publishing and analytics.
MERCH OS occupies a parallel track numbered M-12M through M-18M to
avoid collision.

### M-12M Merch Core Scaffold

Goal: route map and capsule board render with placeholder content.

In scope:

- `/admin/marketing/merch/*` routes scaffolded behind the console gate.
- Capsule board with five lanes reading existing read-only data.
- `MerchCapsule` and `MerchProduct` read views.
- Navigation integrated into Marketing OS hub.

Out of scope: writes, generation, provider calls, vinyl, drops.

### M-13M Merch Domain Tables

Goal: persist merch entities.

In scope:

- `packages/db` migration for: `MerchCapsule`, `MerchProduct`,
  `MerchVariant`, `MerchDrop`, `MerchAvailability`,
  `MerchProviderGroup`.
- Seed data for one demo capsule with products.
- Read-only routes under `services/api`.

Out of scope: write routes, vinyl entities, mockups, exports.

### M-14M Capsule Builder And Drop Scheduler

Goal: operator can create capsules, add products, schedule drops.

In scope:

- Write routes for `MerchCapsule`, `MerchProduct`, `MerchVariant`,
  `MerchDrop`.
- `DROP CAPSULE` intent in operator UI.
- Availability tier enforcement (unit caps, window limits).
- `LINK RELEASE` intent binding capsules to ReleasePack.

Out of scope: vinyl, mockups, provider submission, exports.

### M-15M Vinyl Workspace

Goal: vinyl/dubplate commissioning from ReleasePack.

In scope:

- `VinylReleaseObject` entity and write routes.
- `PRESS VINYL` intent with format/weight/color selection.
- MASTER BUS job reference binding.
- Artwork asset binding from Marketing OS pipeline.
- Vinyl workspace admin view with status tracking.
- Mock vinyl_provider adapter (no real elasticStage calls).

Out of scope: real provider calls, shipping, SoundCloud CTA generation.

### M-16M Product Mockup Generation

Goal: mockup generation for products using the visual engine.

In scope:

- `ProductMockup` entity and write routes.
- `GENERATE MOCKUP` intent using controlled generation.
- ReviewItem-bound approval flow for mockups.
- Mockup gallery view under `/admin/marketing/merch/mockups`.
- Mock image provider (same pattern as M-5).

Out of scope: real image generation, provider submission, exports.

### M-17M Provider Submission And Export

Goal: submit ready products to fulfillment providers.

In scope:

- `SUBMIT TO PROVIDER` intent with provider group routing.
- Mock adapters for all three provider groups.
- `MerchExportPack` build and Dropbox archive export.
- `EXPORT MERCH PACK` intent.
- Provider Isolation Layer for `apparel_provider`,
  `premium_drop_provider`, `vinyl_provider`.

Out of scope: real provider API calls, purchase flow, tracking.

### M-18M Availability Audit And Archive

Goal: enforce 70/20/10 rule and capsule archival.

In scope:

- `AUDIT AVAILABILITY` intent producing `MerchAvailability` snapshots.
- Availability dashboard under `/admin/marketing/merch/audit`.
- `ARCHIVE CAPSULE` intent with no-reopen enforcement.
- Warning system for ratio violations.
- Historical compliance view.

Out of scope: auto-correction, auto-archive, real analytics.

## Risks

1. **elasticStage API stability.** Small provider, API may change.
   Mitigation: Protocol boundary isolates adapter; swap is local.
2. **Vinyl lead times.** 8–16 weeks typical. The system must surface
   estimated delivery clearly and not promise dates it cannot control.
3. **70/20/10 gaming.** Operators could create fake archived items to
   pass the audit. Mitigation: audit counts only items that were
   previously `ACTIVE`, not items created directly as `ARCHIVED`.
4. **Printful/Gelato pricing changes.** Cost model is informational
   only; final pricing is the operator's responsibility.
5. **Scope creep toward storefront.** The MERCH OS is a production
   system. It does not serve buyers. Any purchase/checkout layer is a
   separate product decision requiring its own planning doc.

## Non-Goals (Permanent Exclusions)

- Public-facing storefront or product pages.
- Shopping cart, checkout, or payment processing.
- Customer accounts or order management.
- Inventory sync from provider warehouses.
- Returns / refunds / customer support tooling.
- Marketplace integrations (Bandcamp, Discogs, eBay).
- Pricing optimization or demand-based dynamic pricing.
- Influencer or affiliate programs.
- Subscription boxes or recurring merch.
- Fast-fashion providers (Redbubble, Spreadshirt, Teespring, Society6,
  Amazon Merch) — permanently excluded.

## Cross-Reference

- `docs/marketing/artist-marketing-os.md`
- `docs/marketing/data-model.md`
- `docs/marketing/integrations.md`
- `docs/marketing/roadmap.md`
- `docs/marketing/visual-content-engine.md`
- `docs/soundsystem/master-bus.md`
- `docs/soundsystem/operator-interface-principles.md`
- `docs/soundsystem/model-provider-strategy.md`
- `docs/soundsystem/admin-integration-strategy.md`
