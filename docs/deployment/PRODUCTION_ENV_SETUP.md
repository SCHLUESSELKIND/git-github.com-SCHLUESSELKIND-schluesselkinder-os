# Production Env Setup — SNUFFRAGGA Public Surface

How to set the four `NEXT_PUBLIC_*` variables the SNUFFRAGGA page reads at
build time, for each supported hosting target.

> **Companion docs**
> - `docs/deployment/snuffragga-public.md` — operator playbook
> - `docs/SNUFFRAGGA_LIVE_CHECKLIST.md` — go-live blockers
> - `docs/deployment/SNUFFRAGGA_SMOKE_TEST.md` — post-deploy verification
> - `docs/deployment/production-env.md` — infra-level env contract
> - `apps/web/.env.example` — the source of truth for variable shapes

---

## ⚠ Read this first

`NEXT_PUBLIC_*` env vars are **baked into the build at compile time**. Setting
them on a running container or in your provider's panel *without* a fresh
build will NOT change what the browser sees. Always redeploy after changing
any of these.

Local `.env.local` is **not production**. It only affects `pnpm dev` on your
machine. The deployed site reads from the hosting provider's environment
panel.

---

## Required variables (4)

Copy these into the env panel of whichever hosting target you use.

```
NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=https://open.spotify.com/embed/artist/0Gt1TrN8G1DyXBa2Da5XLW?utm_source=generator
NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing
NEXT_PUBLIC_NEWSLETTER_ENDPOINT=https://api.schluesselkinder.de/v1/public/newsletter/subscribe
NEXT_PUBLIC_SHOP_URL=https://shop.schluesselkinder.de
```

### What happens if a var is empty

| Variable | Empty state |
|---|---|
| `*_SPOTIFY_EMBED` | Spotify panel renders "transmission offline" placeholder. No iframe. |
| `*_SOUNDCLOUD_EMBED` | SoundCloud panel renders "transmission offline" placeholder. No iframe. |
| `*_NEWSLETTER_ENDPOINT` | Form renders. Submit → honest offline state ("Signal-Endpunkt offline. Keine Anmeldung gespeichert."). Never fake success. |
| `*_SHOP_URL` | Falls back to local `/shop` route. CTAs work in dev. In production this almost certainly means a broken external link — set it explicitly. |

Even with `*_SPOTIFY_EMBED` and `*_SOUNDCLOUD_EMBED` set, the consent gate
still applies — iframes only render after the visitor clicks "Signal laden".

---

## Vercel

If `apps/web` deploys via Vercel.

1. Open https://vercel.com/<your-team>/<project> → **Settings** → **Environment Variables**.
2. For each of the four variables above:
   - **Name:** the env var key
   - **Value:** the value above
   - **Environments:** check `Production`, `Preview`, and `Development` (you'll likely want all three)
3. Click **Save** for each one.
4. Trigger a redeploy: **Deployments** → latest deployment → ⋮ → **Redeploy**. Confirm "Use existing build cache" is **off** so the env change actually flows into the build.

Verification after redeploy:
- Visit `/artists/snuffragga`.
- Open DevTools → Network. Reload.
- Confirm there are **zero** requests to `open.spotify.com` or
  `w.soundcloud.com` before clicking "Signal laden".
- Submit the newsletter form. Confirm the response copy matches the
  subscribe/pending/offline/failed state your inference service is in.

## Coolify (Hetzner)

If `apps/web` is deployed via Coolify on a Hetzner VPS.

1. Open Coolify dashboard → project → application for `apps/web`.
2. **Configuration** → **Environment Variables**.
3. Add each of the four variables. Mark each as **"Build variable"** (or
   "Available at build time" depending on Coolify version) — `NEXT_PUBLIC_*`
   must exist at build, not just runtime.
4. **Save** → **Redeploy**. Make sure Coolify rebuilds the image; "restart
   only" will not pick up new build vars.

Verification: same as Vercel.

## Generic Docker host

If you build the image yourself and deploy via `docker-compose.prod.yml` or
similar.

```bash
# 1. Build the image with env vars exposed as build args
docker build \
  --build-arg NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED='https://open.spotify.com/embed/artist/0Gt1TrN8G1DyXBa2Da5XLW?utm_source=generator' \
  --build-arg NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED='https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing' \
  --build-arg NEXT_PUBLIC_NEWSLETTER_ENDPOINT='https://api.schluesselkinder.de/v1/public/newsletter/subscribe' \
  --build-arg NEXT_PUBLIC_SHOP_URL='https://shop.schluesselkinder.de' \
  -t schluesselkinder/web:latest \
  -f apps/web/Dockerfile .

# 2. Replace the running container
docker compose -f docker-compose.prod.yml up -d --force-recreate web
```

> Your `Dockerfile` must declare matching `ARG NEXT_PUBLIC_*` lines and
> re-export them as `ENV` **before** the `pnpm build` step, so the Next.js
> build inlines them. If you change a value but the container shows the old
> placeholder, your Dockerfile is missing one of those `ARG`/`ENV` pairs.

Verification: same as Vercel.

---

## Variables that are NOT documented here

Newsletter subscribe needs four backend env vars set on the **inference
service** (not the web app):

```
SOUNDSYSTEM_LISTMONK_BASE_URL=
SOUNDSYSTEM_LISTMONK_USERNAME=
SOUNDSYSTEM_LISTMONK_PASSWORD=
SOUNDSYSTEM_LISTMONK_LIST_ID=
```

Until those are set on the inference service host, the newsletter route at
`/v1/public/newsletter/subscribe` returns `status="offline"` honestly and
the form shows "Signal-Endpunkt offline. Keine Anmeldung gespeichert." See
`services/soundsystem-inference/README.md` (S66 section).

---

## Final reminder

- **`.env.local` is local dev only.** It exists at `apps/web/.env.local`,
  is gitignored, and never reaches production.
- **`NEXT_PUBLIC_*` rebuild required.** Any env change requires a redeploy.
- **No fake values, ever.** If a URL is missing, the page renders honestly
  offline. We never bake fallback URLs into React.
- **Consent gate is not removable.** Spotify and SoundCloud iframes only
  render after the visitor clicks "Signal laden", regardless of how the
  env vars are configured.
