# Shopify `shop.schluesselkinder.de` — Primary Domain Check

**Goal:** make sure a visitor who lands on `https://shop.schluesselkinder.de`
stays on `shop.schluesselkinder.de` instead of being redirected to a
`*.myshopify.com` URL or to a `www.shop.*` variant.

This is a Shopify-side setting; nothing on the Hetzner box matters here.
The DNS record (CNAME `shop.schluesselkinder.de` → `shops.myshopify.com.`)
already points off-host (smoke test shows `23.227.38.74`, Shopify edge).

---

## Symptoms to look for

External smoke (`scripts/smoke_snuffragga_public.sh`):

```text
✓ shop.schluesselkinder.de   → 200|||https://shop.schluesselkinder.de/        # good
✗ shop.schluesselkinder.de   → 301|||https://schluesselkinder-store.myshopify.com/
✗ shop.schluesselkinder.de   → 301|||https://www.shop.schluesselkinder.de/
```

If the `final` URL after redirects is NOT `https://shop.schluesselkinder.de/...`,
the primary domain inside Shopify is wrong.

---

## Fix in Shopify Admin

1. Open `https://admin.shopify.com/store/schluesselkinder/settings/domains`.
2. In the **Domains** panel, locate `shop.schluesselkinder.de`.
   - If it is missing → click **Connect existing domain** and add it.
3. Click **Change to primary domain** on `shop.schluesselkinder.de`.
4. Under **Domain redirection**:
   - Toggle **Redirect all traffic to this domain** = ON.
   - This makes the `*.myshopify.com` URL 301 to the custom domain.
5. Save.

After the change, Shopify takes 1–5 minutes to propagate. Re-run the smoke:

```bash
bash scripts/smoke_snuffragga_public.sh
```

Expected: `shop.schluesselkinder.de → 200` with `final` column starting
with `https://shop.schluesselkinder.de/`.

---

## Why we do NOT touch DNS

The Caddy host (Hetzner, `178.104.103.37`) does NOT serve any block for
`shop.schluesselkinder.de`. The DNS CNAME sends the browser straight to
Shopify's edge. Adding a Caddy block here would either fail to issue a
cert (DNS does not point to us) or, worse, intercept Shopify traffic.

If you ever see `shop.schluesselkinder.de` resolve to `178.104.103.37`,
the DNS record was changed by accident — restore the CNAME to
`shops.myshopify.com.` in IONOS DNS.

---

## www.shop variant — do nothing

We do **not** publish `www.shop.schluesselkinder.de` and there is no DNS
record for it. Browsers that fat-finger the URL get NXDOMAIN, which is
correct — silently swallowing the typo would hide a misconfiguration.

---

## Audit checklist

- [ ] `dig shop.schluesselkinder.de` returns a CNAME ending in `shopify.com.`
- [ ] `curl -sIL https://shop.schluesselkinder.de | tail -5` shows final
      `HTTP/2 200` from `shop.schluesselkinder.de`, NOT `*.myshopify.com`.
- [ ] In Shopify Admin → Settings → Domains, `shop.schluesselkinder.de`
      is labelled **Primary**.
- [ ] Password page is enabled until launch (Settings → Preferences →
      Password protection = ON).
