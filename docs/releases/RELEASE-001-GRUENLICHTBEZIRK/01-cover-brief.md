# RELEASE-001 — Cover art brief

> One artefact. Three sizes. Six rules.

---

## Output deliverables

| File | Format | Use |
|---|---|---|
| `cover-3000.png` | 3000×3000 RGB PNG, ≤ 36 MB, no transparency | DistroKid → Spotify, Apple, YouTube |
| `cover-1500.jpg` | 1500×1500 JPG quality 90 | SoundCloud, Bandcamp |
| `cover-1000.jpg` | 1000×1000 JPG quality 85 | newsletter embed, social header |
| `cover-square-40.png` | 40×40 PNG | the survive-at-tile-size litmus test |

If the 40×40 does not survive — the cover is wrong. Restart.

---

## Six rules (non-negotiable)

1. **One dominant form.** Single glyph or single object centred. No grid of icons. No collage.
2. **Two-and-a-half colors:** ink black `#070605` + bone white `#EEE8DC` + signal green `#5FB047` as one accent stroke or one marker. The green covers ≤ 8% of total area.
3. **Type either huge or absent.** No medium-size type. Either `GRÜNLICHTBEZIRK` reads at 50% of the canvas, or it does not appear at all (let the back cover / metadata carry the title).
4. **Grayscale parity.** The cover must remain identifiable in pure grayscale. Signal green is a SPICE, not the load-bearing element.
5. **No faces. No humans. No hands.** This is a district, not a person. Add a person and you destroy the mythology.
6. **No AI portraits, no neural style transfer, no obvious generative artefacts.** If a viewer can guess it was generated, it doesn't belong on this label.

---

## Concept direction (pick ONE, do not blend)

### Concept A — DISTRICT MARKER
A single concrete bollard or zone-marker post photographed from low angle, slight side light, fog in background. Bollard has one painted-on green stripe at eye level. Heavy grain. Title set in tiny mono caps at bottom-left as if stencilled onto the asphalt.

References:
- East-Berlin street furniture
- Industrial port zone bollards
- The "Berlin Wall" series by Christiane Feser (composition, not subject)
- Photography style: Thomas Demand minus the colors

### Concept B — SIGNAL LIGHT
Macro-photograph or render of a single industrial green LED indicator (the kind on a rack-mounted radio transmitter or substation panel). Black surrounds, slight bloom on the LED, visible scratches on the housing metal. Title burned-in along the bottom in mono. The LED IS the signal color slot — nothing else is green.

References:
- old shortwave radio panels
- Substation gauges
- Trevor Paglen's "drone" surveillance photography (mood)

### Concept C — TRANSMISSION TOWER FRAGMENT
Tight crop of a transmission-tower truss against deep grey sky. Tower is partly out of frame, suggesting infrastructure too large to capture. Single green safety light at the visible top. Format: vertical centre composition, square crop. Title burned in at top-left.

References:
- Bernd & Hilla Becher industrial typology (composition discipline)
- shortwave broadcast towers in central / eastern Europe
- *Don't* reference Pink Floyd "Wish You Were Here" — too cliché

---

## Production-route options

| Route | Cost | Time | Recommendation |
|---|---|---|---|
| Stock photo + crop + treatment | €10–€30 | 2h | Use this if speed wins. Source: Unsplash + Adobe Stock; license must allow commercial label use. |
| Commission graphic designer | €200–€600 | 3–7d | Recommended path. German/EU designers who get this brief: search "brutalist editorial" on Are.na or Fonts In Use. |
| AI generation (carefully) | €5 | 1h | ONLY if you can avoid generative-looking artefacts. Stitch / DALL-E 3 / Flux. Will require manual cleanup pass. Test the 40×40 ruthlessly. |
| Photograph yourself | €0 | 4h | Best if you have any of: transmission tower nearby, industrial port, bollard with paint stripe. iPhone with manual exposure works — shoot at dusk, RAW. |

**My recommendation:** Concept A photographed at dusk in any industrial zone reachable within 1h of Köln (Frerich United Ventures address). Then 2h post in Lightroom (grain push, desaturate everything except the green stripe, slight crush of black point). Total cost: zero, total time: half a day.

Backup plan if weather kills it: Concept B as AI render via Stitch with manual cleanup. Allow 3h.

---

## Metadata embedded in the file

```
Title          GRÜNLICHTBEZIRK
Artist         SNUFFRAGGA SOUNDSYSTEM
Label          SCHLUESSELKINDER
Year           2026
Copyright      ℗ © 2026 SCHLUESSELKINDER
Comment        RELEASE-001 · GRÜNLICHTBEZIRK · self-released
```

Embed via ExifTool or Photoshop File Info. DistroKid does not require this, but it survives crop / re-upload by third parties and is the only way to verify provenance later.
