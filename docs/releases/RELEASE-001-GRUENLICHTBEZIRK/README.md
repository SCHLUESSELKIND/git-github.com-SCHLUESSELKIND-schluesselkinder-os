# RELEASE-001 — GRÜNLICHTBEZIRK

> **CORRECTION (2026-06-14):** GRÜNLICHTBEZIRK shipped as a standalone single, not the planned 3-track EP. "DISTRICT PRESSURE" and "NACHTFREQUENZ" were never released. Any reference below to a 3-track EP or to those two track names reflects the original plan and is superseded. Canonical state: `docs/release-log.md`.

> SNUFFRAGGA SOUNDSYSTEM · single · digital · self-released via SCHLUESSELKINDER

| Field | Value |
|---|---|
| Release ID | `RELEASE-001` |
| Title | GRÜNLICHTBEZIRK |
| Format | Single, 1 track |
| Date | **Friday 2026-06-12 · 00:00 CEST** |
| Distribution | **Ditto Music** (UK indie) — replaces DistroKid per 2026-05-24 operator lock |
| Upload deadline | **Tue 2026-06-02** (10-day Ditto lead for editorial pitch + propagation) |
| Vehicles | Spotify · SoundCloud · Bandcamp |
| Vinyl | NOT IN V1 — cuts cadence by 12+ weeks, decided against |
| Merch | OBJ-001 hoodie + OBJ-002 tee tied to cover motif (DRAFT in Shopify until cover final) |
| Signal color | `#5FB047` radio green — RELEASE-001 sets the SCHLUESSELKINDER signal-color lock |

## Tracklist

```
01  GRÜNLICHTBEZIRK         — district anchor, sub-bass spine
```

## Priority lock (operator directive 2026-05-24)

```
P1   Shopify live                                 ACTIVE
P2   Cover system                                 next
P3   Ditto Music upload                           after cover + WAV final
P4   Newsletter / Listmonk                        DEPRIORITIZED (audience = 0)
P5   Automation / Growth                          irrelevant until real signals exist
```

Newsletter / SMTP infrastructure stays built but receives zero attention until
RELEASE-001 ships and real subscribers exist. Newsletter drafts in `newsletter/`
remain queued as artefacts — dispatch deferred to post-launch.

## Folder index

```
00-checklist.md             Week-by-week operator checklist + Mastering QA + Ditto Music
01-cover-brief.md           Cover-art spec for commission or in-house production
02-video-scripts.md         3 short-form scripts + shot lists (T-9, T-3, T-1)
03-press-one-pager.md       Sparse one-pager PDF source — markdown → pandoc → PDF
04-shop-payloads.md         Shopify draft-product payload templates, real boundary
newsletter/                 5-touch sequence — DEFERRED per P4 priority
```

See also: `docs/runbooks/shopify-golive.md` — Phase S1 theme push + product activation.

## Run-book entry points

- Public release page (auto-toggles `incoming` → `in transmission` on T-0): `/artists/snuffragga`
- Shopify theme push: `apps/shopify-theme/` → `docs/runbooks/shopify-golive.md`
- Shop drafts: `POST /v1/commerce/sync/shopify/drafts` with payloads from `04-shop-payloads.md`
- Release log: `docs/release-log.md` (append-only)
- Newsletter (deferred): Listmonk admin → Campaigns — see `newsletter/` drafts

## What blocks T-0 — revised under P1–P5 lock

```
P1  [ ]  Shopify theme pushed as unpublished + previewed on mobile + PDP + cart
P1  [ ]  2 products DRAFTed in Shopify (hoodie + tee), checkout reaches payment step
P2  [ ]  Cover art final at 3000×3000 PNG, signal-green tested at 40×40
P3  [ ]  Ditto Music account exists + 1 .wav uploaded + metadata locked by 2026-06-02
P3  [ ]  Mastering QA pass on the 1 .wav file (see 00-checklist.md §1)
T-0 [ ]  Shopify products manually flip DRAFT → ACTIVE on Fri 2026-06-12
```

P4 (Listmonk SMTP) is NO LONGER a T-0 blocker. Newsletter waves can ship later
or be replaced by direct-channel comms.

If any P1/P2/P3 box is still empty by T-3 (Tue 2026-06-09), the release window
slips to Fri 2026-06-19. Slip recorded in `release-log.md` with reason. No
silent slips.
