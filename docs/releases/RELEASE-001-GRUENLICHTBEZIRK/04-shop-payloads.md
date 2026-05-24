# RELEASE-001 — Shopify draft-product payloads

> Created via the hardened boundary in
> `services/soundsystem-inference/app/providers/shopify/real.py`.
> All products MUST go in as `status: DRAFT` and stay there until T-0 manual flip.

---

## Product 1 — `OBJ-001 · DISTRICT HOODIE`

```json
{
  "title": "OBJ-001 · District Hoodie · GRÜNLICHTBEZIRK",
  "handle": "obj-001-district-hoodie-gruenlichtbezirk",
  "vendor": "SCHLUESSELKINDER",
  "product_type": "Hoodie",
  "status": "DRAFT",
  "tags": [
    "snuffragga",
    "grünlichtbezirk",
    "release-001",
    "obj-001",
    "heavy",
    "limited"
  ],
  "body_html": "<p>Heavy garment. GRÜNLICHTBEZIRK kapsel.</p><p>Built for sound-architecture, not streetwear inflation. Cover-motif backprint, bone-on-ink. Limited run — when the lauflänge ends, the object closes.</p><p>—</p><p>Fabric: 480 gsm brushed cotton, oversized boxy fit.<br>Print: water-based, single-pass, signal green (#5FB047) accent stripe.<br>Sizes: S–XXL.<br>Ships from EU (Printful Riga).</p>",
  "options": [
    {
      "name": "Size",
      "values": ["S", "M", "L", "XL", "XXL"]
    }
  ],
  "variants": [
    {
      "option1": "S", "price": "89.00", "sku": "SK-OBJ-001-S", "inventory_quantity": 0},
    {
      "option1": "M", "price": "89.00", "sku": "SK-OBJ-001-M", "inventory_quantity": 0},
    {
      "option1": "L", "price": "89.00", "sku": "SK-OBJ-001-L", "inventory_quantity": 0},
    {
      "option1": "XL", "price": "89.00", "sku": "SK-OBJ-001-XL", "inventory_quantity": 0},
    {
      "option1": "XXL", "price": "89.00", "sku": "SK-OBJ-001-XXL", "inventory_quantity": 0}
  ]
}
```

Price reasoning: €89 sits at the lower end of underground-label hoodie pricing
(Carhartt WIP 80–110, A.P.C. 200+, Berlin underground labels 60–120). Enough to
signal quality + scarcity without going into Berghain-cliché territory. Adjust
based on Printful base cost — target 55–60% margin minimum.

---

## Product 2 — `OBJ-002 · BASS TEE`

```json
{
  "title": "OBJ-002 · Bass Tee · GRÜNLICHTBEZIRK",
  "handle": "obj-002-bass-tee-gruenlichtbezirk",
  "vendor": "SCHLUESSELKINDER",
  "product_type": "T-Shirt",
  "status": "DRAFT",
  "tags": [
    "snuffragga",
    "grünlichtbezirk",
    "release-001",
    "obj-002",
    "oversized",
    "limited"
  ],
  "body_html": "<p>Oversized tee. GRÜNLICHTBEZIRK kapsel.</p><p>Cover-motif backprint, bone-on-ink. Front: stencilled SNUFFRAGGA SOUNDSYSTEM in mono caps. Limited run.</p><p>—</p><p>Fabric: 240 gsm heavy combed cotton, drop-shoulder oversized.<br>Print: water-based, single-pass.<br>Sizes: S–XXL.<br>Ships from EU (Printful Riga).</p>",
  "options": [
    {
      "name": "Size",
      "values": ["S", "M", "L", "XL", "XXL"]
    }
  ],
  "variants": [
    { "option1": "S",   "price": "45.00", "sku": "SK-OBJ-002-S",   "inventory_quantity": 0 },
    { "option1": "M",   "price": "45.00", "sku": "SK-OBJ-002-M",   "inventory_quantity": 0 },
    { "option1": "L",   "price": "45.00", "sku": "SK-OBJ-002-L",   "inventory_quantity": 0 },
    { "option1": "XL",  "price": "45.00", "sku": "SK-OBJ-002-XL",  "inventory_quantity": 0 },
    { "option1": "XXL", "price": "45.00", "sku": "SK-OBJ-002-XXL", "inventory_quantity": 0 }
  ]
}
```

---

## How to submit via the hardened boundary

```bash
# Operator must have these in their session env:
#   SOUNDSYSTEM_SHOPIFY_STORE=schluesselkinder
#   SOUNDSYSTEM_SHOPIFY_TOKEN=shpat_xxxxxxxxxx
#   SOUNDSYSTEM_OPERATOR_TOKEN=<operator auth token from FastAPI>

curl -sS -X POST https://api.schluesselkinder.de/v1/commerce/sync/shopify/drafts \
  -H "Authorization: Bearer ${SOUNDSYSTEM_OPERATOR_TOKEN}" \
  -H "Content-Type: application/json" \
  --data @hoodie-payload.json
```

The boundary:
- Pins `status: DRAFT` server-side. Operator cannot accidentally publish.
- Allowlist on payload keys (`real.py`). Unknown keys rejected.
- Token redacted from all logs / errors.
- Append-only audit row written to `commerce_sync_audit` table.

---

## What still needs operator decisions

```
[ ]  Final pricing — €89 hoodie / €45 tee proposed. Check Printful base cost first.
[ ]  Cover art delivered → backprint mockup → Printful design upload
[ ]  Printful variant SKUs mapped to actual Printful product IDs (sync product layer)
[ ]  Shopify collection "GRÜNLICHTBEZIRK" created and linked
[ ]  Inventory_quantity stays 0 — Printful is print-on-demand, no stock tracking needed
[ ]  T-0 manual flip: Shopify Admin → Products → set DRAFT → ACTIVE for both objects
```
