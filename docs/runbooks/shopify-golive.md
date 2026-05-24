# Shopify go-live — Phase S1

> P1 priority. Get `shop.schluesselkinder.de` from "infrastructure exists" to
> "real checkout reaches payment". Not perfect. Not pretty. **Real.**

---

## Pre-state

- DNS: `shop.schluesselkinder.de` CNAMEs to Shopify edge (verified, 23.227.38.74)
- Shopify store: `schluesselkinder.myshopify.com` (operator-owned)
- Theme: `apps/shopify-theme/` (13 sections · 8 templates · 3 snippets · de+en locales)
- Theme config: `apps/shopify-theme/shopify.theme.toml` (store pre-pinned)
- Shopify CLI: **not yet installed locally** (operator runs install in step 1)

---

## Step 1 · Install Shopify CLI (one-time)

Pick ONE path. Both deliver Shopify CLI 3.x.

```bash
# Path A — Homebrew (recommended on macOS)
brew install shopify-cli

# Path B — npm (works anywhere with Node ≥ 18)
npm install -g @shopify/cli @shopify/theme

# verify
shopify version    # should print 3.x.x
```

---

## Step 2 · First theme push (unpublished)

From the repo root:

```bash
cd apps/shopify-theme

# First push. Creates a new UNPUBLISHED theme on the store.
# Opens browser for auth on first run — log in with the store owner account.
shopify theme push -e dev --unpublished
```

Expected output:
- browser auth completes
- "Uploading theme files..." progress
- "Theme created" with a numeric theme ID and a preview URL like:
  `https://schluesselkinder.myshopify.com/?preview_theme_id=XXXXXXXXXXXXX`

**Save the theme ID.** Paste it into `apps/shopify-theme/shopify.theme.toml` so
subsequent pushes target the same theme:

```toml
[environments.dev]
store = "schluesselkinder.myshopify.com"
theme = "XXXXXXXXXXXXX"   # paste the ID from `shopify theme push` output
unpublished = true
```

Commit that change — the theme ID is not a secret.

---

## Step 3 · Preview QA (mobile-first)

Open the preview URL on your **phone** first. The brand has to land on mobile or
it lands nowhere.

Check, in order:

```
[ ]  Homepage loads → no console errors → no missing fonts → no missing images
[ ]  Header nav links work (Shop, About, all visible items)
[ ]  Featured-collection section: even with no products, renders empty state
     without crashing the page
[ ]  Sound-embed section: respects consent gate (if applicable to shop pages)
[ ]  Footer: copyright year correct, all 3 social links resolve
[ ]  Cart drawer: opens, closes, shows empty state
[ ]  PDP template: navigate to /products/<any-slug>, even if 404 placeholder,
     no Liquid render errors
[ ]  /collections/all: lists products (empty for now), no crash
[ ]  Locale switch: de ↔ en works, both have all strings
[ ]  Theme inspector: no console errors, no 404s on assets
```

If any box fails, fix in the local files, push again with:

```bash
shopify theme push -e dev
```

(no need for `--unpublished` after the first push — the theme ID is now in the config)

---

## Step 4 · Add 2 product DRAFTS

Two paths to choose from. Both end with the same Shopify state.

### Path A · Shopify Admin UI (recommended for first products)

`https://admin.shopify.com/store/schluesselkinder/products/new`

For each of the two products (hoodie + tee):

1. Use the title from `docs/releases/RELEASE-001-GRUENLICHTBEZIRK/04-shop-payloads.md`
2. Paste the `body_html` description
3. Add the price + 5 size variants (S/M/L/XL/XXL)
4. Upload placeholder image (replace with real cover-derived mockup later)
5. Set status: **DRAFT** (NOT active)
6. Save
7. Add to collection: create "GRÜNLICHTBEZIRK" collection if missing,
   then add both products to it

### Path B · API via the hardened boundary

```bash
# requires SOUNDSYSTEM_SHOPIFY_TOKEN + SOUNDSYSTEM_OPERATOR_TOKEN in env
curl -sS -X POST https://api.schluesselkinder.de/v1/commerce/sync/shopify/drafts \
  -H "Authorization: Bearer ${SOUNDSYSTEM_OPERATOR_TOKEN}" \
  -H "Content-Type: application/json" \
  --data @apps/shopify-theme/_payloads/hoodie.json
```

Path A is faster for the first two products. Path B is the future for the
broader catalog when there are 5+ items going in at once.

---

## Step 5 · End-to-end checkout test (the actual win condition)

This is the reality test. Phase S1 is NOT done until this passes.

```
[ ]  In the preview theme, navigate to one of the 2 DRAFT products
       (DRAFT products are visible in preview themes via direct URL, even
        though they're not in collections-all)
       URL pattern: https://schluesselkinder.myshopify.com/products/<handle>?preview_theme_id=XXX
[ ]  Pick a size, add to cart
[ ]  Open cart drawer / page — shows the product, quantity, price
[ ]  Click "Checkout"
[ ]  Reach the Shopify checkout page (Shopify-hosted, not theme-controlled)
[ ]  Verify shipping options load (Printful EU)
[ ]  Verify payment step renders Stripe / PayPal / Apple Pay
       (DO NOT actually pay — abandon the cart)
[ ]  Verify the cart abandonment email is queued in Shopify Admin →
       Marketing → Abandoned checkouts
```

If you reach the payment step, **Phase S1 P1 is DONE**. Everything else is
polish.

---

## Step 6 · Promote to live (when ready, NOT before payment test passes)

Only after Step 5 passes:

```bash
cd apps/shopify-theme
shopify theme push -e live    # NEVER use --live until you're sure
```

OR in Shopify Admin:
- Themes → find the unpublished theme → "Publish"

Publishing makes the theme the default for `shop.schluesselkinder.de`.

---

## Hard rules (operator must enforce, CLI doesn't)

- **Never push `live` from CI**. Live promotion is a deliberate human act.
- **Never blast `shopify theme push --live` as a first command** — that
  overwrites whatever live theme is currently published with whatever happens
  to be in your local working tree.
- **Password page stays ON until Friday 2026-06-12 00:00 CEST**:
  Shopify Admin → Online Store → Preferences → Password protection = ENABLED.
  Set the password to something short (e.g. `snuffragga`) so internal
  stakeholders can preview without exposing the storefront publicly.
- **Disable Shopify's default "thank you" automation tracking** if any —
  privacy is brand. Settings → Customer events → review what's enabled.

---

## What to send back to me after Steps 1–3

```
1. Preview URL                          https://...?preview_theme_id=XXXX
2. Theme ID                             XXXXXXXXXXXXX
3. Screenshot                           mobile homepage
4. Screenshot                           a PDP (any product, even empty)
5. Screenshot                           cart drawer (with one item)
```

I'll do a brutal QA pass on the screenshots, flag what to cut / fix, and
hand back a punch-list. Then we move to Step 4 (products) and Step 5 (the
checkout reality test).
