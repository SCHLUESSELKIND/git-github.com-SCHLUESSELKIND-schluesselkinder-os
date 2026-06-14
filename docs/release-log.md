# SCHLUESSELKINDER · Release log

> **CORRECTION (2026-06-14):** GRÜNLICHTBEZIRK shipped as a standalone single, not the planned 3-track EP. "DISTRICT PRESSURE" and "NACHTFREQUENZ" were never released. Any reference below to a 3-track EP or to those two track names reflects the original plan and is superseded. Canonical state: `docs/release-log.md`.

> Append-only ledger. Newest entry on top. Every release decision, slip, and learning
> recorded here by date. The log is the truth — if it didn't get logged, it didn't
> happen.

## Format

Each release block has:
- a stable release ID (`RELEASE-NNN`)
- the artist + title
- the locked release date
- a chronological list of operator entries (`YYYY-MM-DD · note`)

No section is ever rewritten. Corrections are appended, not edited.

---

## RELEASE-001 · SNUFFRAGGA SOUNDSYSTEM · GRÜNLICHTBEZIRK

**Locked release date:** Friday 2026-06-12 · 00:00 CET
**Format:** Single (geplant als 3-Track-EP, descoped 2026-06-14), digital only, self-released via SCHLUESSELKINDER
**Distribution:** DistroKid (account TBC)
**Vehicles:** Spotify, Apple Music, SoundCloud, Bandcamp, YouTube Music
**Artefact stack:** `docs/releases/RELEASE-001-GRUENLICHTBEZIRK/`

### Log

- **2026-06-14 · CORRECTION** GRÜNLICHTBEZIRK ist als eigenstaendige Single erschienen, nicht als geplanter 3-Track-EP. DISTRICT PRESSURE und NACHTFREQUENZ wurden nie veroeffentlicht. Der Katalog sind Einzel-Singles (Grünlichtbezirk, Kaputtes Blau, Kleiner Grüner Elf, Gorilla Glue). Live-Seite und Tracklist entsprechend auf Single korrigiert.
- **2026-05-24 · LOCK** — release scope locked under OPUS MAX directive. EP title
  GRÜNLICHTBEZIRK confirmed by operator. Tracklist: GRÜNLICHTBEZIRK / DISTRICT
  PRESSURE / NACHTFREQUENZ. Date Fri 2026-06-12. Vinyl explicitly cut from V1.
  Signal color locked as radio green `#5FB047` (was deep red — title says green
  light, district is green).
- **2026-05-24 · STACK SHIPPED** — operator artefact stack created
  (cover brief, 5-touch newsletter sequence, 3 video scripts, press one-pager,
  shop payloads, this log, web ReleaseStatus toggle, signal-green accent flip
  on /artists/snuffragga). All under `docs/releases/RELEASE-001-GRUENLICHTBEZIRK/`.
- **2026-05-24 · OPEN BLOCKERS** — (1) Mastering QA on the 3 .wav files. (2)
  DistroKid account check + upload. (3) Listmonk SMTP wired (blocks newsletter
  sequence dispatch). (4) Cover art commission or in-house production. T-3 hard
  slip-rule applies — Tue 2026-06-09 is the no-go-no-go decision day.
- **2026-05-24 · PRIORITY LOCK** — operator directive: P1 Shopify live · P2
  Cover system · P3 Ditto Music upload · P4 Newsletter (deprio) · P5 Automation
  (irrelevant until real signals). Reality test focus: real product → real
  checkout → real payment. Infrastructure expansion paused until real-signal
  loop closes.
- **2026-05-24 · DISTRIBUTOR CHANGE** — DistroKid replaced with **Ditto Music**.
  Closer to independent-label workflow, less creator-economy tooling, cleaner
  for the underground posture. Upload deadline tightens slightly to Tue
  2026-06-02 for Ditto's editorial-pitch lead time. DistroKid references in
  README + checklist updated; logged here as the audit truth.
- **2026-05-24 · NEWSLETTER DEPRIO** — Listmonk SMTP no longer blocks T-0.
  Newsletter sequence (T-7, T-1, T+0, T+3, T+7) stays archived in
  `newsletter/` as drafts. Dispatch deferred to post-launch, when real
  subscribers exist. Audience = 0 means newsletter = zero leverage right now.
- **2026-05-24 · PHASE S1 OPENED** — Shopify go-live runbook landed at
  `docs/runbooks/shopify-golive.md`. Theme push + 2 product drafts +
  end-to-end checkout test. Definition of done: payment step reached on the
  preview theme, abandoned cart logged in Shopify Admin.
- **2026-05-24 · DATE-DISPLAY BUG FIX (commit ecbb832)** — first prerender
  shipped "11.06.2026 · 00:00 CET" instead of "12.06.2026 · 00:00 CEST" due
  to `getUTCDate()` shifting a midnight-CEST moment back into UTC. Fixed by
  parsing ISO components directly. Lesson: server-rendered date strings MUST
  be parsed component-wise from the ISO source. Never use `Date.getUTC*()`
  for display.
