# SNUFFRAGGA SOUNDSYSTEM — Go-Live Checklist

Concrete steps before `/artists/snuffragga` can be called "live". Tick every
box. **Do not announce the page publicly until every required item is green.**

> The page renders honestly when env vars are missing — it shows
> "transmission offline" / "signal endpoint offline" states. The checklist
> below is what turns those states green.

---

## 0. Coolify routing — prerequisite

Before any of the steps below, the four hostnames must be wired through
Coolify per `docs/deployment/COOLIFY_SCHLUESSELKINDER_ROUTING.md`:

- `schluesselkinder.de` → Next.js web app
- `www.schluesselkinder.de` → 301 → root
- `api.schluesselkinder.de` → FastAPI inference
- `listmonk.schluesselkinder.de` → Listmonk
- `shop.schluesselkinder.de` → **Shopify only — never Coolify**

Run `bash scripts/smoke_snuffragga_public.sh` to verify the routing surface
is green before proceeding to the operator checklist below.

> **`.env.local` is local dev only.** Production env vars must be set in
> Coolify's application settings panel and the app must be redeployed
> (`NEXT_PUBLIC_*` is build-time).

## 1. DNS + hosting

- [ ] `schluesselkinder.de` resolves to the Next.js deployment (Hetzner / Vercel
      / whatever you've chosen).
- [ ] HTTPS active. No mixed-content warnings.
- [ ] `/artists/snuffragga` returns HTTP 200 in production.
- [ ] Redirect from `/artists/snuffragga/` (trailing slash) handled by host.

## 2. Environment variables (Required)

Set every variable below in your hosting provider's env panel
(`apps/web/.env.example` documents the shape). After setting, redeploy.

- [ ] `NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED` — set to the production
      embed URL:
      `https://open.spotify.com/embed/artist/0Gt1TrN8G1DyXBa2Da5XLW?utm_source=generator`
      Until set, Spotify panel shows "spotify signal offline" placeholder.
      Note: the embed remains **consent-gated** — even with the URL set,
      the iframe is not rendered until the visitor clicks "Signal laden".
- [ ] `NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED` — set to the production
      embed URL:
      `https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing`
      Until set, SoundCloud panel shows "soundcloud signal offline"
      placeholder. Same consent gate applies.
- [ ] `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` — your real subscribe endpoint
      (Listmonk / Mailcoach / Shopify customer-collect / etc.). Until set,
      the newsletter form posts will fail with "signal endpoint offline".
- [ ] `NEXT_PUBLIC_SHOP_URL` — your real Shopify storefront URL
      (e.g. `https://shop.schluesselkinder.de`). Defaults to `/shop` for
      local dev.

> The page reads these at **build time** (Next.js `process.env.NEXT_PUBLIC_*`),
> so a redeploy is required after changing any of them.

## 3. Spotify (you, not the agent)

- [ ] Spotify for Artists account claimed for SNUFFRAGGA SOUNDSYSTEM.
- [ ] Header image uploaded (3:1, cold underground; no festival aesthetics).
- [ ] Avatar uploaded.
- [ ] Bio set — short, cold, no marketing voice.
- [ ] Artist Pick set.
- [ ] Canvas videos uploaded for GRÜNLICHTBEZIRK tracks.
- [ ] Social links wired (TikTok, Instagram, SoundCloud).
- [ ] Merch tile points to `NEXT_PUBLIC_SHOP_URL`.
- [ ] Embed iframe URL copied to `NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED`.

## 4. SoundCloud (you, not the agent)

- [ ] Artist profile set up — same brand discipline as Spotify.
- [ ] Avatar + header.
- [ ] At least one transmission uploaded (or playlist).
- [ ] Embed iframe URL copied to `NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED`.

## 5. Newsletter pipeline (S66 — Listmonk)

The public subscribe endpoint lives in the inference service at
`POST /v1/public/newsletter/subscribe`. It is offline-honest until Listmonk
env vars are set.

- [ ] Listmonk instance running (you already run one — point it at the
      `signal` list for SNUFFRAGGA).
- [ ] Generate a Listmonk API user + token (Listmonk Admin → Settings →
      Users → API tokens).
- [ ] Identify the numeric list ID Listmonk should subscribe people to.
- [ ] Set these env vars **on the inference service** (NOT on the Next.js
      app):
    - `SOUNDSYSTEM_LISTMONK_BASE_URL=https://listmonk.your-host.tld`
    - `SOUNDSYSTEM_LISTMONK_USERNAME=api_user`
    - `SOUNDSYSTEM_LISTMONK_PASSWORD=<api_token>`
    - `SOUNDSYSTEM_LISTMONK_LIST_ID=<numeric_list_id>`
- [ ] On the **Next.js side**, set
      `NEXT_PUBLIC_NEWSLETTER_ENDPOINT=https://api.schluesselkinder.de/v1/public/newsletter/subscribe`.
- [ ] `curl` the endpoint and verify response shape:
      ```bash
      curl -X POST https://api.schluesselkinder.de/v1/public/newsletter/subscribe \
        -H "Content-Type: application/json" \
        -d '{"email":"you@example.com","source":"snuffragga_artist_page","tags":["snuffragga","signal"]}'
      ```
      Expect `{"ok": true, "status": "subscribed"|"pending", "email_hash": "..."}`.
      The raw email should NEVER appear in the response.
- [ ] Double opt-in: if your Listmonk list requires confirmation, the
      response status will be `"pending"` and Listmonk will send the
      confirmation email itself. Don't add a custom confirmation email
      flow on top.
- [ ] First confirmation email landed in inbox (deliverability check).

## 6. Shopify shop link

- [ ] Shopify theme from `apps/shopify-theme/` pushed via `shopify theme push`.
- [ ] `shop.schluesselkinder.de` connected at IONOS DNS (CNAME) and verified
      in Shopify Admin (see `apps/shopify-theme/README.md`).
- [ ] Collection handle `gruenlichtbezirk` exists in Shopify Admin.
- [ ] At least one **real** GRÜNLICHTBEZIRK product synced from Printful.
- [ ] Test order placed end-to-end with your real card; refund issued.
- [ ] `NEXT_PUBLIC_SHOP_URL` points to the live shop domain.

## 7. Legal (DE)

- [ ] `/impressum` content reflects current legal entity, address, contact.
- [ ] `/datenschutz` covers all of the below — **non-negotiable** for the
      SNUFFRAGGA page going live:
    - **Listmonk (newsletter ESP):** processing of email + SHA-256 hash;
      Listmonk's hosting location; legal basis (Art. 6 (1) (a) consent);
      revocation path (`Einwilligung zurückziehen` link in every newsletter).
    - **Spotify Embed (consent-gated):** Spotify Technology S.A.; cookies
      and tracking set by Spotify when the user clicks "Signal laden";
      disclosure that the iframe is **only loaded after explicit click**.
    - **SoundCloud Embed (consent-gated):** SoundCloud Ltd.; same
      consent-gated behaviour.
    - **Local storage key `sk_embed_consent`:** purely a client-side
      consent record. Not a cookie. Not transmitted to any server. Set on
      the user's device only.
- [ ] `/kontakt` form (if it submits anywhere) has consent checkbox + privacy
      link.
- [ ] Shopify shop has Impressum / Datenschutz / Widerrufsbelehrung /
      Versand / AGB.

### S67 changes that affect privacy

- Newsletter form now correctly reflects the backend's `subscribed` /
  `pending` / `offline` / `failed` status — it **never** shows success on
  `offline`.
- Music embeds (Spotify + SoundCloud) are now **consent-gated**. The iframe
  is NOT in the DOM until the visitor clicks "Signal laden". This means no
  request reaches Spotify / SoundCloud before consent.
- Consent is stored in `localStorage.sk_embed_consent`. There is a small
  "Einwilligung zurücksetzen" link in the page footer that lets visitors
  revoke consent.

## 8. Mobile QA

Run on a real phone, not just devtools:

- [ ] Hero readable on iPhone SE (smallest reasonable).
- [ ] CTAs tappable, no overlap.
- [ ] Newsletter input doesn't trigger weird zoom (set `font-size: 16px` if so).
- [ ] Spotify + SoundCloud iframes render full-width.
- [ ] Sticky header doesn't cover content on small screens.
- [ ] German umlauts render correctly (GRÜNLICHTBEZIRK).

## 9. Performance + SEO

- [ ] Lighthouse Performance ≥ 90 on mobile profile.
- [ ] Lighthouse SEO = 100.
- [ ] Lighthouse Accessibility ≥ 95.
- [ ] OpenGraph image renders correctly in Twitter / iMessage / WhatsApp
      preview (use `opengraph.xyz` or `metatags.io`).
- [ ] `<title>` is `SNUFFRAGGA SOUNDSYSTEM — SCHLUESSELKINDER`.
- [ ] No 404 in browser console.
- [ ] No CORS errors when newsletter is wired.

## 10. Brand sanity check

- [ ] **No fake content visible.** Walk the page top-to-bottom on prod.
      Anything that says "offline" or "placeholder" or "no walk-in" is
      intentional honesty about pre-launch state — verify the operator
      copy is acceptable for public eyes.
- [ ] **SNUFFRAGGA** spelled with double-G everywhere on the page.
- [ ] **GRÜNLICHTBEZIRK** umlaut intact everywhere.
- [ ] No "EDM festival" voice slipped in. No happy emojis. No "Welcome!".
- [ ] No third-party tracking pixels added (you don't ship Meta / Google
      Analytics; respect the no-tracking stance).
- [ ] Lore copy reads cold, brutal, sparse — not occult / cyberpunk /
      cannabis-coded.

## 11. After launch — first 72 hours

- [ ] Drop the URL once in your bio (TikTok / IG / SC / Spotify).
- [ ] Don't sub-tweet the launch — the page IS the announcement.
- [ ] Watch real traffic in your analytics (Umami if you've run it; otherwise
      Vercel / hosting logs).
- [ ] First newsletter signup confirmed end-to-end.
- [ ] First real order through `shop.schluesselkinder.de` confirmed (place
      it yourself to test fulfillment).

---

## Honest red flags that block "live"

If any of these are true, the page is **not** live yet, even if it loads:

1. `NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED` empty + the public expects to hear
   music. Either ship a real embed or remove that section temporarily.
2. Newsletter endpoint empty + you're driving traffic to it. The form will
   error; people will see "signal endpoint offline" and bounce.
3. Shop URL still set to `/shop` (local) + a real shop CTA on the page.
   Either set `NEXT_PUBLIC_SHOP_URL` to the live domain or hide the
   GRÜNLICHTBEZIRK CTA.
4. Impressum / Datenschutz / AGB missing or stale. German legal exposure —
   non-negotiable.
5. No real product orderable yet. The CTA promises a drop; the storefront
   must back the promise.

Until all four of those are green, treat the URL as a soft-launch / staging
preview, not a public link.
