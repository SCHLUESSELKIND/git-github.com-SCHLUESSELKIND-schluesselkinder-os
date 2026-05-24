# RELEASE-001 — GRÜNLICHTBEZIRK

> SNUFFRAGGA SOUNDSYSTEM · 3-track EP · digital · self-released via SCHLUESSELKINDER

| Field | Value |
|---|---|
| Release ID | `RELEASE-001` |
| Title | GRÜNLICHTBEZIRK |
| Format | EP, 3 tracks |
| Date | **Friday 2026-06-12 · 00:00 CET** |
| Distribution | DistroKid (€19.99/year) — account TBD |
| Vehicles | Spotify · SoundCloud · Bandcamp · Apple Music · YouTube Music |
| Vinyl | NOT IN V1 — cuts cadence by 12+ weeks, decided against |
| Merch | OBJ-001 hoodie + OBJ-002 tee tied to cover motif (DRAFT in Shopify until cover final) |
| Signal color | `#5FB047` radio green — RELEASE-001 sets the SCHLUESSELKINDER signal-color lock |

## Tracklist

```
01  GRÜNLICHTBEZIRK         — district anchor, sub-bass spine
02  DISTRICT PRESSURE       — pressure-wave track, mid-record peak
03  NACHTFREQUENZ           — closer, pirate-radio decay
```

## Folder index

```
00-checklist.md             Week-by-week operator checklist + Mastering QA + DistroKid
01-cover-brief.md           Cover-art spec for commission or in-house production
02-video-scripts.md         3 short-form scripts + shot lists (T-9, T-3, T-1)
03-press-one-pager.md       Sparse one-pager PDF source — markdown → pandoc → PDF
04-shop-payloads.md         Shopify draft-product payload templates, real boundary
newsletter/                 5-touch sequence (T-7, T-2, T+0, T+3, T+7)
```

## Run-book entry points

- Public release page (auto-toggles `incoming` → `in transmission` on T-0): `/artists/snuffragga`
- Newsletter dispatch: Listmonk admin → Campaigns → drafts pre-loaded from `newsletter/`
- Shop drafts: `POST /v1/commerce/sync/shopify/drafts` with payloads from `04-shop-payloads.md`
- Release log: `docs/release-log.md` (append-only)

## What blocks T-0

In strict order. Each box is one operator action.

```
[ ]  Mastering QA pass on the 3 .wav files (see 00-checklist.md §1)
[ ]  DistroKid account exists + 3 .wav uploaded + metadata locked
[ ]  Cover art final at 3000×3000 PNG, signal-green tested at 40×40
[ ]  Shopify products go from DRAFT to ACTIVE on T-0 (manual flip in Shopify Admin)
[ ]  Listmonk SMTP wired (otherwise newsletter sequence does not actually send)
```

If any of those is still empty by T-3 (Tue 2026-06-09), the release window slips to Fri 2026-06-19. Slip is recorded in `release-log.md` with a reason. No silent slips.
