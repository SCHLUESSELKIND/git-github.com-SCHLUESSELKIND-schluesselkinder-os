# SNUFFRAGGA SOUNDSYSTEM — Public Deployment

Operator playbook for shipping `/artists/snuffragga` from the
`apps/web` Next.js app.

> Companion docs:
> - `docs/SNUFFRAGGA_LIVE_CHECKLIST.md` — go-live blocker list
> - `docs/deployment/COOLIFY_SCHLUESSELKINDER_ROUTING.md` — routing runbook
> - `docs/deployment/PRODUCTION_ENV_SETUP.md` — per-host env-var setup
> - `docs/deployment/SNUFFRAGGA_SMOKE_TEST.md` — 13-section smoke checklist
> - `scripts/smoke_snuffragga_public.sh` — read-only smoke probe
> - `scripts/coolify_snuffragga_setup.sh` — safe Coolify helper (no API mutation)
> - `apps/web/.env.example` — env var template
> - `apps/shopify-theme/README.md` — Shopify side

> **`.env.local` (local dev) is NOT production.** The deployed site reads
> env vars from your hosting provider's panel. Coolify rebuild required
> for `NEXT_PUBLIC_*` changes. `shop.schluesselkinder.de` is Shopify-only
> and must never be added to Coolify.

## Build target

- App: `apps/web` (Next.js, app-router, server components).
- Route: `/artists/snuffragga` — public.
- Reachable from: artist index (`/artists`), homepage nav, footer nav.

## Environment variables

All four are **build-time** (`NEXT_PUBLIC_*`). Setting them post-deploy
requires a fresh build.

| Variable | Empty behaviour | Real example shape |
|---|---|---|
| `NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED` | "spotify signal offline" placeholder | `https://open.spotify.com/embed/artist/0Gt1TrN8G1DyXBa2Da5XLW?utm_source=generator` |
| `NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED` | "soundcloud signal offline" placeholder | `https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing` |

> The Spotify + SoundCloud URLs above are the **real production embeds** for
> SNUFFRAGGA SOUNDSYSTEM. They are documented here only — they are NOT
> hard-coded in any React component. They must be set in your hosting
> provider's environment panel (Vercel / Hetzner / etc.), never committed
> to the repository.
| `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` | Form renders; submit → honest offline state | `https://api.schluesselkinder.de/v1/public/newsletter/subscribe` |
| `NEXT_PUBLIC_SHOP_URL` | Defaults to `/shop` (local route) | `https://shop.schluesselkinder.de` |

The page never invents fake URLs. Each control either renders honestly with
the real URL or shows a "offline" state — there is no third state.

## Local development

```bash
cd /Users/thomasfrerich/schluesselkinder-os
cp apps/web/.env.example apps/web/.env.local
# Edit apps/web/.env.local with real or empty values
pnpm install
pnpm --filter @schluesselkinder/web dev
# → http://localhost:3000/artists/snuffragga
```

## Production build

```bash
pnpm --filter @schluesselkinder/web typecheck
pnpm --filter @schluesselkinder/web build
pnpm --filter @schluesselkinder/web start
```

## Verification before going public

1. Walk the page on a real phone. Every CTA tappable. No layout overflow.
2. Disable each env var in turn and reload — make sure the offline state is
   visually acceptable (it's intentional, but operator-readable).
3. Run Lighthouse mobile profile. Target ≥ 90 Performance.
4. Open OpenGraph preview at `opengraph.xyz/url/https://schluesselkinder.de/artists/snuffragga`.
5. Tick every item in `docs/SNUFFRAGGA_LIVE_CHECKLIST.md`.

## What the page contains

| Section | Behaviour | Operator wires |
|---|---|---|
| Hero | Static (district-002 marker, CTA, status chips). | nothing |
| Transmissions | **Consent-gated** Spotify + SoundCloud embeds. With URLs set: shows a "Signal laden" prompt; iframe loads only after the visitor clicks. Without URLs: "transmission offline" placeholder. | both `*_EMBED` env vars + visitor consent click |
| GRÜNLICHTBEZIRK CTA | Links to `${SHOP_URL}/collections/gruenlichtbezirk` | `NEXT_PUBLIC_SHOP_URL` |
| District uniforms | Static descriptive object cards. No images, no prices, no fake products. | nothing — real garments live in the shop |
| District lore | Static cold copy, German. | nothing |
| Newsletter | Posts to `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` JSON `{ "email": "…" }`. The inference service subscribe route returns `subscribed` / `pending` / `offline` / `failed` and never echoes the raw email. | `NEXT_PUBLIC_NEWSLETTER_ENDPOINT` + 4 Listmonk env vars on the inference service |
| Foot nav | Internal links to `/artists`, `/music`, `${SHOP_URL}` | nothing |

## Newsletter — Listmonk wiring (S66)

The public subscribe endpoint lives in the inference service at
`POST /v1/public/newsletter/subscribe`. Wire `NEXT_PUBLIC_NEWSLETTER_ENDPOINT`
on the Next.js side to that URL (typically `https://api.schluesselkinder.de/v1/public/newsletter/subscribe`).

On the **inference service** side, set four env vars to enable Listmonk:

```
SOUNDSYSTEM_LISTMONK_BASE_URL=https://listmonk.your-host.tld
SOUNDSYSTEM_LISTMONK_USERNAME=api_user
SOUNDSYSTEM_LISTMONK_PASSWORD=<api_token>
SOUNDSYSTEM_LISTMONK_LIST_ID=<numeric_list_id>
```

Behaviour:

- All four set → route forwards to Listmonk via `POST /api/subscribers`,
  returns `SUBSCRIBED` (or `PENDING` if the list requires double opt-in).
- Any one missing → route returns `status="offline"`, no upstream call.
- Listmonk error → route returns `status="failed"`, never reveals upstream
  error verbatim. Listmonk credentials are never logged, never echoed.
- Tags + `source` from the request are filtered through a server-side
  allowlist (`snuffragga`, `signal`, `gruenlichtbezirk`, `vinyl`, `manual`).
  Unknown tags / sources are dropped silently.
- The raw email is **never** returned. Response carries only the SHA-256
  hex hash so the frontend can reconcile state without cookies.

## Embed consent (S67)

Spotify and SoundCloud iframes are **never rendered until the visitor clicks
"Signal laden"**. No request reaches Spotify or SoundCloud before that
click. The consent decision is stored client-side only:

- Key: `localStorage.sk_embed_consent`
- Value: `"granted"` (the only accepted value)
- Scope: per origin, applies to every music embed on the site
- No cookies are set by our code
- Visitors can revoke consent via the footer link "Einwilligung zurücksetzen"

Datenschutz implications (`/datenschutz` must reflect):

- Spotify Technology S.A. — processes user data when the iframe loads
- SoundCloud Ltd. — same
- Both load only after explicit visitor click
- The `sk_embed_consent` key is a client-side preference; we never read it
  server-side and never transmit it anywhere

## Newsletter response handling (S67)

The form parses the JSON envelope from `/v1/public/newsletter/subscribe`
and maps the four backend statuses to operator-readable German copy:

| Backend `status` | Form behaviour |
|---|---|
| `subscribed` | "Signal empfangen. Check dein Postfach." |
| `pending` | "Fast drin. Bitte bestätige deine Anmeldung per E-Mail." |
| `offline` | "Signal-Endpunkt offline. Keine Anmeldung gespeichert." |
| `failed` (or non-2xx) | "Signal gestört. Versuch es später erneut." |

We never show success on `offline`. We never echo the raw email back to
the visitor.

## What the page DOES NOT do

- It does **not** call any Spotify / SoundCloud / Shopify / Printful / TikTok
  API. The only client-side fetch happens when a visitor submits the newsletter
  form, and only if you've wired a real endpoint.
- It does **not** track visitors. No Meta pixel, no Google Analytics, no
  ad-tech. Add your own (Umami self-hosted recommended) at the root layout
  level if you want it.
- It does **not** auto-publish anything. No background jobs. No schedulers.
- It does **not** carry any provider tokens (Spotify / SoundCloud embeds are
  public iframe URLs; nothing authenticated).

## Brand sanity floor

The page sits inside the wider AGENTS.md brand rules:

- Cold underground, radical reduction, red accent.
- German umlauts preserved (GRÜNLICHTBEZIRK).
- SNUFFRAGGA spelled with double G everywhere.
- No EDM / festival / colorful / cyberpunk / occult / cannabis copy.

Any future edit that drifts from these rules will fail manual brand review.
