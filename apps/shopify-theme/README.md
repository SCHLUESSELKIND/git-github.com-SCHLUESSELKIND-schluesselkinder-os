# shop.schluesselkinder.de — Shopify Theme

A custom Shopify theme for **SCHLUESSELKINDER**, the masterbrand for SHIBARI KAWAII and the SNUFFRAGGA SOUNDSYSTEM drop line.

> **Note on AGENTS.md (top-level repo rules):** This theme directly conflicts with `AGENTS.md` line 8 ("Do not use Shopify") and the merch-shop language guidance in lines 36–37. Before merging or shipping to prod, update `AGENTS.md` to record the policy change. This theme exists because of an explicit override; it should not be the default reading of the repo rules.

---

## What this theme is

- Custom theme written from scratch (no Dawn fork).
- Mobile-first, no JS frameworks, minimal client-side code.
- Brutal-condensed editorial typography with **one accent color** (radioactive green) used sparingly.
- Cold-underground / radical-reduction aesthetic — not cyberpunk, not moodboard, not cannabis-coded.
- Vocabulary follows the brand: DISTRICT UNIFORM, BASS PRESSURE EDITION, LIMITED SIGNAL, NIGHT SYSTEM READY.

## What this theme is NOT

- Not a product seeder. No fake products are created. Products are pulled live from your Shopify admin (where Printful syncs them in).
- Not a payment integration. Stripe/Checkout is whatever your Shopify store is already configured for.
- Not a CMS replacement for the rest of `apps/web` — only `shop.schluesselkinder.de` is touched.

---

## Directory layout

```
apps/shopify-theme/
├── assets/                # CSS, JS, fonts, static images
├── config/                # settings_schema.json, settings_data.json
├── layout/                # theme.liquid, password.liquid
├── locales/               # en.default.json, de.json
├── sections/              # reusable Liquid sections
├── snippets/              # small Liquid partials
└── templates/             # JSON templates that compose sections
```

This matches Shopify's expected theme structure exactly — you can `shopify theme push` from this directory.

---

## Local development

### Prerequisites

1. Install Shopify CLI (one-time):

   ```bash
   npm install -g @shopify/cli @shopify/theme
   ```

2. Authenticate against the store (browser auth — runs in **your** session, not Claude's):

   ```bash
   cd apps/shopify-theme
   shopify auth login --store schluesselkinder.myshopify.com
   ```

### Run a local preview

```bash
cd apps/shopify-theme
shopify theme dev --store schluesselkinder.myshopify.com
```

This opens a local preview against a development theme — your live theme is untouched.

### Push to a development theme

```bash
shopify theme push --unpublished --store schluesselkinder.myshopify.com
```

You'll get a preview URL like `https://schluesselkinder.myshopify.com/?preview_theme_id=...`.

### Publish (only when ready)

```bash
shopify theme push --live --store schluesselkinder.myshopify.com
```

**Never publish directly.** Always push to a development theme first, walk the storefront end-to-end on mobile + desktop, then publish from the Shopify admin.

---

## Domain setup (shop.schluesselkinder.de)

Done in **Shopify Admin** + **IONOS DNS**, not in this repo:

1. Shopify Admin → Settings → Domains → Connect existing domain → enter `shop.schluesselkinder.de`.
2. Shopify will give you a target hostname (something like `shops.myshopify.com`).
3. At IONOS DNS for `schluesselkinder.de`:
   - Delete any existing `shop` A/CNAME record.
   - Add a **CNAME** record: `shop` → `shops.myshopify.com` (whatever Shopify gives you).
4. Back in Shopify Admin, click **Verify connection**. Wait for DNS propagation (5–60 min).
5. Set `shop.schluesselkinder.de` as the **primary domain** for this store, or keep `*.myshopify.com` primary and use the custom domain as redirect — your call.

Per the existing repo memory (`feedback_dns_state.md`): respect the Punycode rule and keep DNS in sync with the documented state.

---

## Printful integration

Done in **Shopify Admin** + **Printful Admin**, not in this repo:

1. Shopify Admin → Apps → search "Printful" → Install.
2. Authorize Shopify in Printful.
3. In Printful, create the catalogue:
   - **DISTRICT UNIFORM** (Hoodie) — heavyweight, oversized, garment-dyed, dark colours only.
   - **BASS PRESSURE EDITION** (Tee) — oversized, heavy cotton, dark colours only.
   - **NIGHT SYSTEM LONGSLEEVE** (Longsleeve).
   - **LIMITED SIGNAL BEANIE** (Beanie).
   - **STREET POSTER** (Poster, A2 and A1 sizes).
   - **STICKER SHEET** (Vinyl sticker pack).
4. Sync each Printful product to Shopify. Each one shows up as a Shopify product with the variants pre-built.
5. In Shopify Admin → Products, **tag** the new products with:
   - `district-uniform`, `bass-pressure`, `night-system`, `limited-signal`, `street-poster`, `sticker` (used by collections).
   - `limited-drop` for capsule/drop-only items.
   - `snuffragga-soundsystem` for items in that drop line.
   - `gruenlichtbezirk` for that capsule.

### Vinyl, music, non-POD items

Vinyl, cassettes, and physical merch the label fulfills directly should NOT be on Printful. Add those as standard Shopify products with manual fulfillment, tagged `vinyl` or `physical`. The theme reads tags only; it doesn't care how the item is fulfilled.

---

## Collections to create (Shopify Admin → Products → Collections)

| Handle | Title | Type | Rule |
|---|---|---|---|
| `district-uniforms` | DISTRICT UNIFORMS | Automated | Tagged `district-uniform` |
| `bass-pressure` | BASS PRESSURE EDITION | Automated | Tagged `bass-pressure` |
| `night-system` | NIGHT SYSTEM | Automated | Tagged `night-system` |
| `limited-signal` | LIMITED SIGNAL | Automated | Tagged `limited-drop` |
| `vinyl` | VINYL | Automated | Tagged `vinyl` |
| `posters` | POSTERS | Automated | Tagged `street-poster` |
| `gruenlichtbezirk` | GRÜNLICHTBEZIRK | Automated | Tagged `gruenlichtbezirk` |
| `snuffragga-soundsystem` | SNUFFRAGGA SOUNDSYSTEM | Automated | Tagged `snuffragga-soundsystem` |
| `all` | ALL OBJECTS | Automated | All products |

---

## Navigation (Shopify Admin → Online Store → Navigation)

**Main menu** — replace what Shopify gives you with:

```
SHOP                   → /collections/all
DISTRICT UNIFORMS      → /collections/district-uniforms
BASS PRESSURE          → /collections/bass-pressure
LIMITED SIGNAL         → /collections/limited-signal
VINYL                  → /collections/vinyl
GRÜNLICHTBEZIRK        → /collections/gruenlichtbezirk
ARCHIVE                → /pages/archive
```

**Footer menu**:

```
IMPRESSUM              → /policies/legal-notice
DATENSCHUTZ            → /policies/privacy-policy
SHIPPING               → /policies/shipping-policy
RETURNS                → /policies/refund-policy
CONTACT                → /pages/contact
```

---

## What's stubbed vs. done in this first pass

**Done:**
- Layout (`layout/theme.liquid`)
- Design tokens + base CSS (`assets/base.css`)
- Header + footer + cart-drawer (`sections/header.liquid`, `sections/footer.liquid`, `snippets/cart-drawer.liquid`)
- Home sections: hero, featured-collection, featured-product, sound-embed, newsletter
- Product page (`sections/main-product.liquid` + `templates/product.json`)
- Collection page (`sections/main-collection.liquid` + `templates/collection.json`)
- Cart page (`templates/cart.json`)
- Product card snippet (`snippets/product-card.liquid`)
- Settings schema with brand-aligned controls
- en + de locales

**Stubbed (add next pass):**
- Password / coming-soon page (`layout/password.liquid`)
- Search results template
- Blog templates (intentionally not built; brand uses pages, not Shopify blog)
- 404 styling (currently falls back to default)
- Customer account templates (Shopify defaults are OK for first launch)
- Live PWA features (offline, install prompt) — not required for first launch
- Gift-card template (only needed if you sell gift cards)

When you want any of these built out, ask and I'll add them.

---

## Performance targets

- Lighthouse Performance ≥ 90 on a moderate-throttling mobile profile.
- No third-party JS except: Shopify analytics (forced), Printful (only on product pages where needed), embeds the merchant explicitly enables (Spotify, SoundCloud).
- No web fonts loaded synchronously. Self-hosted fonts via `@font-face` with `font-display: swap`.
- Inline critical CSS for the fold, lazy-load images below.

---

## Accessibility

- WCAG AA contrast on the radioactive-green accent against black/off-white.
- All interactive elements keyboard-reachable.
- `aria-` labels on the cart drawer, mobile nav toggle, and product gallery.
- `prefers-reduced-motion` respected — grain/noise animations stop.

---

## Open / known limitations

- Spotify and SoundCloud embeds require the merchant to paste a real embed URL in section settings. No fake URLs are baked in (`feedback_no_fake_urls.md`).
- Newsletter form posts to Shopify's built-in customer-collect endpoint. If you want Klaviyo / a separate ESP, swap the form action.
- Printful product images are pulled from whatever Printful syncs in. If you want bespoke editorial photography, replace images in Shopify Admin per product.
- The "STREET UNIFORMS" / "Lifestyle Grid" section assumes you upload real editorial imagery via Shopify Files. The section renders a stark grid; without your images, it renders empty placeholder cells (no fake image URLs, no AI-generated imagery, per `feedback_no_fake_data.md`).
