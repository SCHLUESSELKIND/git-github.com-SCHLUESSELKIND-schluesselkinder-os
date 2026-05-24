# SNUFFRAGGA Smoke Test

Walk this list against the **deployed** URL after every push to production.
Aim for ≤ 5 minutes. Do not announce the page externally until every box
is green.

> Test environment: a real device on real network, not a dev tunnel. The
> first run should be done on a phone (iPhone SE width if you have one)
> because that's the smallest viable target.

---

## 1. Index page reachable

- [ ] `https://schluesselkinder.de/artists` returns HTTP 200.
- [ ] Page renders without console errors.
- [ ] "SNUFFRAGGA SOUNDSYSTEM" district-002 card visible.
- [ ] "enter district →" link goes to `/artists/snuffragga`.

## 2. Artist page reachable

- [ ] `https://schluesselkinder.de/artists/snuffragga` returns HTTP 200.
- [ ] Page renders without console errors.
- [ ] German copy renders correctly. **Umlaut intact** on GRÜNLICHTBEZIRK.
- [ ] **SNUFFRAGGA spelled with double-G** everywhere.

## 3. Consent gate — Spotify

- [ ] Open the deployed page in an **incognito / private** window.
- [ ] DevTools → Network tab → filter `spotify`.
- [ ] Reload `/artists/snuffragga`. Confirm **zero** requests to
      `open.spotify.com` before any click.
- [ ] Confirm the Spotify panel says **"Externe Inhalte blockiert."**
      with a "Signal laden" button. **No iframe in DOM** — verify via
      DevTools → Elements: search for `iframe` returns no Spotify match.
- [ ] Click "Signal laden". A request to `open.spotify.com` should now
      appear. The iframe renders.

## 4. Consent gate — SoundCloud

- [ ] Same panel as Spotify on the SoundCloud side.
- [ ] Before consent: no request to `w.soundcloud.com`.
- [ ] After consent (same button — consent is page-wide): SoundCloud
      iframe renders and starts loading. Network tab shows
      `w.soundcloud.com/player` request.

## 5. Reset consent

- [ ] Scroll to the page footer (foot nav row with "← Artists / Music
      index → / Shop →").
- [ ] Click "Einwilligung zurücksetzen". The button only renders if
      consent is currently granted.
- [ ] Reload the page. Both panels go back to the consent state. No
      Spotify/SoundCloud requests on reload.
- [ ] Application → Local Storage → `sk_embed_consent` key is **removed**.

## 6. Newsletter — offline state

If `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` is unset OR Listmonk env vars are
unset on the inference service:

- [ ] Submit a valid email.
- [ ] Form shows **"Signal-Endpunkt offline. Keine Anmeldung gespeichert."**
- [ ] Form does **NOT** show "Signal empfangen. Check dein Postfach."
- [ ] No raw email visible in the response copy.

## 7. Newsletter — live state

If Listmonk is configured on the inference service:

- [ ] Submit a real email you own.
- [ ] Form shows either:
    - "Signal empfangen. Check dein Postfach." (status `subscribed`), OR
    - "Fast drin. Bitte bestätige deine Anmeldung per E-Mail." (status
      `pending` — double opt-in)
- [ ] Check your inbox. Listmonk's confirmation email arrives.
- [ ] DevTools → Network → confirm the response body contains
      `email_hash` and does NOT contain the raw email address.

## 8. Newsletter — failure state

To exercise the failure path (optional, only if you want to see the copy):

- [ ] Temporarily point `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` at a 404 URL on
      the same host (e.g. `https://api.schluesselkinder.de/nope`).
- [ ] Submit a valid email.
- [ ] Form shows **"Signal gestört. Versuch es später erneut."**
- [ ] Revert the env var. Redeploy.

## 9. Shop CTA target

- [ ] Hover over **"Enter GRÜNLICHTBEZIRK"** in the hero. URL preview
      ends with `/collections/gruenlichtbezirk`.
- [ ] Hover over **"Enter shop"** in the drop section. URL preview ends
      with the shop domain (or `/shop` if `NEXT_PUBLIC_SHOP_URL` is
      unset).
- [ ] Click one. Either it opens the live Shopify shop or — if the shop
      isn't published yet — confirms what visitors will see. **If the
      shop isn't real yet, do NOT announce the artist page externally.**

## 10. Mobile nav + tap targets

- [ ] On a phone, the sticky header doesn't cover content.
- [ ] All CTAs are tappable without zoom.
- [ ] Newsletter input doesn't trigger iOS auto-zoom (input must have
      `font-size: 16px` or larger — current code uses
      `font-mono text-sm` ≈ 14px, recheck if zoom happens).
- [ ] District uniform grid (3×2) is legible.
- [ ] Hero title doesn't break awkwardly.

## 11. Lighthouse — mobile profile

Run Lighthouse against the deployed URL with the **Mobile** profile.

- [ ] Performance ≥ 90.
- [ ] Accessibility ≥ 95.
- [ ] Best Practices ≥ 95.
- [ ] SEO = 100.
- [ ] No console errors.

## 12. Datenschutz / legal

- [ ] `/datenschutz` mentions **Listmonk** (newsletter ESP + hash retention).
- [ ] `/datenschutz` mentions **Spotify Technology S.A.** (consent-gated embed).
- [ ] `/datenschutz` mentions **SoundCloud Ltd.** (consent-gated embed).
- [ ] `/datenschutz` mentions the `sk_embed_consent` localStorage key.
- [ ] `/impressum` is up to date with current legal entity + contact.
- [ ] No third-party tracking scripts loaded on the page (no Meta pixel,
      no Google Analytics, no anything). Network tab should be quiet
      before consent.

## 13. OpenGraph / share preview

- [ ] Paste the URL in iMessage / Slack / WhatsApp. Preview renders.
- [ ] Title: `SNUFFRAGGA SOUNDSYSTEM — SCHLUESSELKINDER`.
- [ ] Image: `/brand/campaign-dungeon-chair.png` resolves.
- [ ] Description renders in German.

---

## Red flags that block announcement

If **any** of these are true, do not announce the URL externally:

1. Network tab shows requests to Spotify / SoundCloud before clicking
   "Signal laden". Consent gate is broken — investigate
   `SoundEmbed.tsx` and `localStorage`.
2. Newsletter form ever shows "Signal empfangen" without the visitor
   actually being subscribed to Listmonk. The status mapping is broken
   — investigate `NewsletterForm.tsx`.
3. `/datenschutz` doesn't mention Listmonk + Spotify + SoundCloud + the
   localStorage key. German legal exposure.
4. `/impressum` is missing or stale.
5. Shop CTA leads to a 404 or a Shopify page that says "This store is
   unavailable / password protected". External CTAs must back the
   promise.
6. Lighthouse Performance < 70 on mobile. The audience is mobile-first;
   anything slower than that bounces.
