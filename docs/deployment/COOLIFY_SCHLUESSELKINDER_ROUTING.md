# Coolify Routing — SCHLUESSELKINDER

Operator runbook for routing the four hostnames that live on the Hetzner box,
plus the one hostname that must NOT touch Coolify (Shopify).

> **Companion artifacts**
> - `scripts/coolify_snuffragga_setup.sh` — safe dry-run helper (no mutations)
> - `scripts/smoke_snuffragga_public.sh` — read-only public smoke test
> - `docs/deployment/PRODUCTION_ENV_SETUP.md` — per-host env-var runbook
> - `docs/deployment/SNUFFRAGGA_SMOKE_TEST.md` — 13-section post-deploy checklist

---

## Current public state (snapshot)

Run `bash scripts/smoke_snuffragga_public.sh` for live state. As of the
last verified probe:

| Domain | DNS | TLS | App | OK? |
|---|---|---|---|---|
| `schluesselkinder.de` | Hetzner `178.104.103.37` | ✓ Caddy | Next.js (older build) | ⚠ stale |
| `www.schluesselkinder.de` | Hetzner | ✓ | same Next.js, no 301 | ⚠ needs redirect |
| `schluesselkinder.de/artists/snuffragga` | — | — | **HTTP 404** — route not in deployed build | ✗ |
| `api.schluesselkinder.de` | Hetzner | ✗ TLS fail | no Caddy route / no app | ✗ |
| `listmonk.schluesselkinder.de` | Hetzner | ✗ TLS fail | no Caddy route / no app | ✗ |
| `shop.schluesselkinder.de` | Shopify CDN | ✓ | Shopify (may redirect — see §6) | DNS correct |

---

## Desired final state

| Domain | Routes to | Notes |
|---|---|---|
| `schluesselkinder.de` | `apps/web` (Next.js) | primary public site |
| `www.schluesselkinder.de` | 301 → `schluesselkinder.de` | redirect only, canonical at root |
| `api.schluesselkinder.de` | `services/soundsystem-inference` (FastAPI) | exposes `/v1/public/*` only externally |
| `listmonk.schluesselkinder.de` | Listmonk container | self-hosted ESP |
| `shop.schluesselkinder.de` | **Shopify only** | NEVER added to Coolify |

---

## DNS — must match (do not change unless DNS is wrong)

```
schluesselkinder.de             A      178.104.103.37
www.schluesselkinder.de         A      178.104.103.37
api.schluesselkinder.de         A      178.104.103.37
listmonk.schluesselkinder.de    A      178.104.103.37
shop.schluesselkinder.de        CNAME  shops.myshopify.com
```

The first four point to the Hetzner VPS; Coolify dispatches them to the
right container via its reverse proxy. `shop` lives on Shopify's CDN and
must remain there — adding it to Coolify will break the storefront and
hand traffic to a 502.

---

## Coolify app mapping

In your Coolify dashboard, map application UUIDs to these domains via
**Application → Domains** (no API mutation from this repo — see "Future
automation"):

| Coolify application | Domain(s) | Cert source |
|---|---|---|
| Next.js web app | `schluesselkinder.de`, `www.schluesselkinder.de` | Let's Encrypt (auto via Coolify) |
| FastAPI / soundsystem-inference | `api.schluesselkinder.de` | Let's Encrypt |
| Listmonk | `listmonk.schluesselkinder.de` | Let's Encrypt |

---

## Required env vars on the Next.js app

These are **build-time** (`NEXT_PUBLIC_*` is baked at compile, not runtime).
Set them in Coolify under **Application → Environment Variables**, mark
each as a build variable, then redeploy **without** build cache.

```
NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=https://open.spotify.com/embed/artist/1jzZXWDrVb0jDp32zxcqc2?utm_source=generator
NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing
NEXT_PUBLIC_NEWSLETTER_ENDPOINT=https://api.schluesselkinder.de/v1/public/newsletter/subscribe
NEXT_PUBLIC_SHOP_URL=https://shop.schluesselkinder.de
```

> **`.env.local` is local dev only.** It is gitignored. It does not reach
> production. Production env vars must be set in Coolify's application
> settings panel. After saving, **redeploy the app** — `NEXT_PUBLIC_*`
> requires a rebuild.

---

## Required env vars on the FastAPI inference app

These are **runtime** server-side vars (not `NEXT_PUBLIC_*`). They enable
the newsletter subscribe route to forward to your Listmonk:

```
SOUNDSYSTEM_LISTMONK_BASE_URL=https://listmonk.schluesselkinder.de
SOUNDSYSTEM_LISTMONK_USERNAME=<api_user>
SOUNDSYSTEM_LISTMONK_PASSWORD=<api_token>
SOUNDSYSTEM_LISTMONK_LIST_ID=<numeric_list_id>
```

Set in Coolify on the FastAPI app, then restart the container. Without these
the subscribe route returns `status="offline"` honestly — never fake success.

---

## Manual Coolify steps (the only supported path right now)

1. **Open Coolify** at your Coolify URL (e.g. `https://coolify.<host>` or
   the in-cluster admin URL — varies per install).
2. **Next.js web app → Environment Variables.** Paste the four
   `NEXT_PUBLIC_*` lines above. Mark each as build-time. Save.
3. **Next.js web app → Domains.** List both `schluesselkinder.de` and
   `www.schluesselkinder.de`. For the www → root redirect, use Coolify's
   "Redirect www to root" toggle if your version supports it; otherwise
   add a Caddy/Nginx custom directive:

   ```
   www.schluesselkinder.de {
       redir https://schluesselkinder.de{uri} permanent
   }
   ```

4. **Next.js web app → Redeploy.** Disable "Use build cache". Wait for
   the build to complete. Verify in the deployment log that
   `/artists/snuffragga` appears in the route manifest.
5. **FastAPI inference app → Domains.** Add `api.schluesselkinder.de`.
   Wait for the Let's Encrypt ACME challenge to complete (~30 s). Verify
   `curl https://api.schluesselkinder.de/v1/capabilities` returns 200.
6. **FastAPI inference app → Environment Variables.** Set the four
   Listmonk vars above. Restart the app.
7. **Listmonk app → Domains.** Add `listmonk.schluesselkinder.de`. Wait
   for cert. Verify `curl -I https://listmonk.schluesselkinder.de` returns
   200 / 302 / 401 (any of these is fine — it means Listmonk is reachable).
8. **Run the smoke test:** `bash scripts/smoke_snuffragga_public.sh`.
9. **Walk the 13-section checklist** in
   `docs/deployment/SNUFFRAGGA_SMOKE_TEST.md` on a real phone.

---

## What NOT to do

- ❌ Do **not** add `shop.schluesselkinder.de` to any Coolify application.
  DNS already routes it to Shopify. Adding it to Coolify will break the
  shop and hand traffic to a 502.
- ❌ Do **not** modify DNS unless something in the table above is wrong.
  Adding a Hetzner A-record for `shop.*` (or removing the CNAME) will
  break Shopify.
- ❌ Do **not** publish the Shopify shop from inside Coolify. The Shopify
  side is operated separately in Shopify Admin.
- ❌ Do **not** export `COOLIFY_API_TOKEN` into a committed file. Keep it
  in your shell only.
- ❌ Do **not** delete apps or databases in Coolify while wiring routing —
  destructive actions are reversible only via backups.

---

## Future automation (TODO)

The helper script `scripts/coolify_snuffragga_setup.sh` intentionally does
**not** call Coolify's mutating API endpoints. Two reasons:

1. The repo carries no verified Coolify v4 API reference. Guessing endpoint
   shapes risks silently posting to the wrong URL or sending the token in
   the wrong header. Both are bad in different ways.
2. Production-modifying actions (env-var write, domain add, restart)
   trigger redeploys and Let's Encrypt issuance. A failed ACME challenge
   rate-limits the hostname for an hour.

When a verified Coolify v4 API reference lands here (committed at
`docs/deployment/coolify-api-reference.md` or similar) and is signed off
by the operator, extend the helper with these actions:

- `set-web-env --apply` → `PATCH /api/v1/applications/{uuid}/envs` with
  the four `NEXT_PUBLIC_*` lines.
- `apply-domains --apply` → `POST /api/v1/applications/{uuid}/domains`
  for each of the three Coolify-managed hostnames.
- `restart-web --apply` → `POST /api/v1/applications/{uuid}/restart`.

Each must:
- Require `--apply` AND the relevant env vars.
- Print a redacted diff of intended changes before sending.
- Confirm with the operator before each mutation (`-y` to skip).
- Never echo the token. Use `curl -H "Authorization: Bearer …"` with the
  variable, never with the literal value.

---

## Notes on `shop.schluesselkinder.de` (Shopify-side)

The smoke test currently shows `shop.schluesselkinder.de` returning a 301
redirect (via Shopify / Cloudflare) **away** from the Shopify storefront.
That's a **Shopify Admin** configuration issue, not Coolify.

Check in Shopify Admin:
- Settings → Domains → Primary domain (should be `shop.schluesselkinder.de`,
  not your `.myshopify.com` URL).
- Online Store → Preferences → Password protection (turn off only when
  the shop is genuinely ready to be public).
- Online Store → Themes → Customize → confirm the active theme is the
  S62 SCHLUESSELKINDER theme, not a previous draft.

Do NOT investigate this from Coolify. The Shopify side is owned in Shopify
Admin only.
