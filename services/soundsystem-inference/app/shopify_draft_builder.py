"""Shopify Draft Builder Logic (S40).

Maps MerchCapsule products to Shopify-compatible product drafts.
No real Shopify API calls. No publishing. No inventory mutation.

Vendor: SCHLUESSELKINDER (masterbrand).
Tags: SCHLUESSELKINDER, artist name, release title, product type, availability.
Body HTML: from capsule/release context.
Warnings: missing artwork, missing mockup, product inactive.
"""

from __future__ import annotations

from uuid import uuid4

from app.schemas import (
    MerchCapsule,
    MerchProduct,
    ShopifyDraftStatus,
    ShopifyImageRef,
    ShopifyProductDraft,
    ShopifyVariantDraft,
)

VENDOR = "SCHLUESSELKINDER"
BRAND_TAG = "SCHLUESSELKINDER"


def build_product_draft(
    product: MerchProduct,
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> ShopifyProductDraft:
    """Convert a single MerchProduct into a ShopifyProductDraft.

    Tags include brand, artist, release title, product type, availability.
    Warnings flag missing artwork/mockup.
    """
    tags = _build_tags(product, capsule)
    body_html = _build_body_html(product, capsule)
    variants = _build_variants(product)
    images = _build_images(product)
    warnings = _build_warnings(product)
    provider_payload = _build_provider_payload(product, capsule)

    return ShopifyProductDraft(
        draft_id=uuid4(),
        capsule_id=capsule.capsule_id,
        product_id=product.product_id,
        title=product.title,
        body_html=body_html,
        vendor=VENDOR,
        product_type=product.product_type.value,
        tags=tags,
        status=ShopifyDraftStatus.DRAFT,
        variants=variants,
        images=images,
        provider_payload=provider_payload,
        warnings=warnings,
        created_by=operator_id,
    )


def build_all_drafts(
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> list[ShopifyProductDraft]:
    """Build Shopify product drafts for all active products in a capsule."""
    drafts: list[ShopifyProductDraft] = []
    for product in capsule.products:
        if not product.active:
            continue
        draft = build_product_draft(
            product,
            capsule,
            operator_id=operator_id,
        )
        drafts.append(draft)
    return drafts


# ---------- Internal builders ----------


def _build_tags(product: MerchProduct, capsule: MerchCapsule) -> list[str]:
    """Build Shopify tags from product/capsule metadata."""
    tags = [
        BRAND_TAG,
        capsule.artist,
        capsule.title.split(" — ")[0] if " — " in capsule.title else capsule.title,
        product.product_type.value.replace("_", " "),
        product.availability.value.replace("_", " "),
    ]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(tag)
    return unique


def _build_body_html(product: MerchProduct, capsule: MerchCapsule) -> str:
    """Build product body HTML from capsule context."""
    lines = [
        f"<p><strong>{product.title}</strong></p>",
        f"<p>{capsule.artist} — {capsule.title}</p>",
        f"<p>Availability: {product.availability.value.replace('_', ' ').title()}</p>",
    ]
    if product.price_positioning:
        lines.append(f"<p>Positioning: {product.price_positioning}</p>")
    return "\n".join(lines)


def _build_variants(product: MerchProduct) -> list[ShopifyVariantDraft]:
    """Map MerchVariants to ShopifyVariantDrafts.

    If no variants exist, create a single default variant.
    """
    if product.variants:
        return [
            ShopifyVariantDraft(
                variant_id=v.variant_id,
                title=v.label,
                sku_suffix=v.sku_suffix,
                option1=v.label,
            )
            for v in product.variants
        ]
    # Default single variant
    return [
        ShopifyVariantDraft(
            variant_id=product.product_id,
            title="Default",
            option1="Default",
        )
    ]


def _build_images(product: MerchProduct) -> list[ShopifyImageRef]:
    """Build image references from artwork/mockup artifact IDs."""
    images: list[ShopifyImageRef] = []
    position = 1

    if product.artwork_artifact_id:
        images.append(
            ShopifyImageRef(
                artifact_id=product.artwork_artifact_id,
                alt=f"{product.title} artwork",
                position=position,
            )
        )
        position += 1

    if product.mockup_artifact_id:
        images.append(
            ShopifyImageRef(
                artifact_id=product.mockup_artifact_id,
                alt=f"{product.title} mockup",
                position=position,
            )
        )

    return images


def _build_warnings(product: MerchProduct) -> list[str]:
    """Generate warnings for missing assets or configuration."""
    warnings: list[str] = []

    if not product.artwork_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no artwork artifact. "
            "Shopify listing will have no primary image."
        )

    if not product.mockup_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no mockup artifact. "
            "Consider adding product mockups before export."
        )

    if not product.active:
        warnings.append(
            f"Product '{product.title}' is inactive. Draft created but should not be exported."
        )

    return warnings


def _build_provider_payload(product: MerchProduct, capsule: MerchCapsule) -> dict:
    """Build the raw Shopify Admin API payload shape (for inspection).

    This is what would be sent to POST /admin/api/{version}/products.json
    if the real provider were connected. No API call is made.
    """
    return {
        "product": {
            "title": product.title,
            "body_html": _build_body_html(product, capsule),
            "vendor": VENDOR,
            "product_type": product.product_type.value,
            "tags": ", ".join(_build_tags(product, capsule)),
            "status": "draft",
            "variants": [
                {
                    "title": v.label if product.variants else "Default",
                    "sku": v.sku_suffix if product.variants else "",
                    "option1": v.label if product.variants else "Default",
                    "requires_shipping": True,
                }
                for v in (product.variants or [])
            ]
            or [{"title": "Default", "option1": "Default", "requires_shipping": True}],
        }
    }
