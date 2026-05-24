"""TikTok Shop Listing Builder Logic (S42).

Maps MerchCapsule products to TikTok Shop-compatible listing drafts.
No real TikTok Shop API calls. No product creation. No publishing.
No inventory mutation.

TikTok Shop is top-of-funnel. Best products: tees, hoodies, sticker
packs, totes, posters. Avoid premium collector vinyl — route those
to SoundCloud/elasticStage funnel.

Category mapping:
- heavyweight_tee -> Apparel > Tops > T-Shirts
- oversized_hoodie -> Apparel > Hoodies & Sweatshirts
- longsleeve -> Apparel > Tops > Long Sleeves
- beanie -> Accessories > Hats
- tote -> Bags > Tote Bags
- poster -> Home > Posters & Prints
- sticker_pack -> Stationery > Stickers
- vinyl_object -> blocked: collector object, not TikTok Shop
"""

from __future__ import annotations

from uuid import uuid4

from app.schemas import (
    MerchAvailability,
    MerchCapsule,
    MerchProduct,
    MerchProductType,
    TikTokShopContentAngle,
    TikTokShopListing,
    TikTokShopListingStatus,
    TikTokShopVariantListing,
)

# ---------- Product type to TikTok Shop category mapping ----------

_TIKTOK_CATEGORY_MAP: dict[MerchProductType, dict] = {
    MerchProductType.HEAVYWEIGHT_TEE: {
        "category_hint": "Apparel > Tops > T-Shirts",
        "content_angle": TikTokShopContentAngle.WAREHOUSE_CULTURE,
        "supported": True,
    },
    MerchProductType.OVERSIZED_HOODIE: {
        "category_hint": "Apparel > Hoodies & Sweatshirts",
        "content_angle": TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL,
        "supported": True,
    },
    MerchProductType.LONGSLEEVE: {
        "category_hint": "Apparel > Tops > Long Sleeves",
        "content_angle": TikTokShopContentAngle.WAREHOUSE_CULTURE,
        "supported": True,
    },
    MerchProductType.BEANIE: {
        "category_hint": "Accessories > Hats",
        "content_angle": TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL,
        "supported": True,
    },
    MerchProductType.TOTE: {
        "category_hint": "Bags > Tote Bags",
        "content_angle": TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL,
        "supported": True,
    },
    MerchProductType.POSTER: {
        "category_hint": "Home > Posters & Prints",
        "content_angle": TikTokShopContentAngle.LIMITED_CAPSULE,
        "supported": True,
    },
    MerchProductType.STICKER_PACK: {
        "category_hint": "Stationery > Stickers",
        "content_angle": TikTokShopContentAngle.WAREHOUSE_CULTURE,
        "supported": True,
    },
    MerchProductType.VINYL_OBJECT: {
        "category_hint": "",
        "content_angle": TikTokShopContentAngle.COLLECTOR_OBJECT,
        "supported": False,
        "warning": (
            "Vinyl objects are collector items — not suited for TikTok Shop. "
            "Route to SoundCloud/elasticStage vinyl funnel instead."
        ),
    },
}


def build_listing(
    product: MerchProduct,
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> TikTokShopListing:
    """Convert a single MerchProduct into a TikTokShopListing."""
    mapping = _TIKTOK_CATEGORY_MAP.get(
        product.product_type,
        {
            "category_hint": "",
            "content_angle": TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL,
            "supported": False,
            "warning": f"Unknown product type: {product.product_type}",
        },
    )

    tags = _build_tags(product, capsule)
    description = _build_description(product, capsule)
    variants = _build_variants(product)
    images = _build_images(product)
    warnings = _build_warnings(product, capsule, mapping)
    provider_payload = _build_provider_payload(product, capsule, mapping)

    status = TikTokShopListingStatus.DRAFT
    if not mapping.get("supported", True):
        status = TikTokShopListingStatus.BLOCKED

    return TikTokShopListing(
        listing_id=uuid4(),
        capsule_id=capsule.capsule_id,
        product_id=product.product_id,
        title=product.title,
        description=description,
        category_hint=mapping["category_hint"],
        product_type=product.product_type.value,
        tags=tags,
        content_angle=mapping["content_angle"],
        variants=variants,
        images=images,
        provider_payload=provider_payload,
        status=status,
        warnings=warnings,
        created_by=operator_id,
    )


def build_all_listings(
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> list[TikTokShopListing]:
    """Build TikTok Shop listings for all active products in a capsule."""
    listings: list[TikTokShopListing] = []
    for product in capsule.products:
        if not product.active:
            continue
        listing = build_listing(product, capsule, operator_id=operator_id)
        listings.append(listing)
    return listings


# ---------- Internal builders ----------


def _build_tags(product: MerchProduct, capsule: MerchCapsule) -> list[str]:
    """Build TikTok Shop tags from product/capsule metadata."""
    tags = [
        "SCHLUESSELKINDER",
        capsule.artist,
        capsule.title.split(" — ")[0] if " — " in capsule.title else capsule.title,
        product.product_type.value.replace("_", " "),
        "underground",
        "soundsystem",
    ]
    if product.availability == MerchAvailability.LIMITED:
        tags.append("limited drop")
    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(tag)
    return unique


def _build_description(product: MerchProduct, capsule: MerchCapsule) -> str:
    """Build listing description optimized for TikTok Shop."""
    lines = [
        f"{product.title}",
        f"{capsule.artist} — {capsule.title}",
        "",
        f"Availability: {product.availability.value.replace('_', ' ').title()}",
    ]
    if product.availability == MerchAvailability.LIMITED:
        lines.append("Limited drop — once gone, gone.")
    lines.append("")
    lines.append("SCHLUESSELKINDER — cold underground music and streetwear.")
    return "\n".join(lines)


def _build_variants(product: MerchProduct) -> list[TikTokShopVariantListing]:
    """Map MerchVariants to TikTokShopVariantListings."""
    if product.variants:
        return [
            TikTokShopVariantListing(
                variant_id=v.variant_id,
                title=v.label,
                sku_suffix=v.sku_suffix,
                option=v.label,
            )
            for v in product.variants
        ]
    return [
        TikTokShopVariantListing(
            variant_id=product.product_id,
            title="Default",
            option="One Size",
        )
    ]


def _build_images(product: MerchProduct) -> list:
    """Build image references from artifact IDs."""
    images = []
    if product.artwork_artifact_id:
        images.append(product.artwork_artifact_id)
    if product.mockup_artifact_id:
        images.append(product.mockup_artifact_id)
    return images


def _build_warnings(
    product: MerchProduct,
    capsule: MerchCapsule,
    mapping: dict,
) -> list[str]:
    """Generate warnings for the listing."""
    warnings: list[str] = []

    # Mapping-specific warning
    if "warning" in mapping:
        warnings.append(mapping["warning"])

    # Unsupported product
    if not mapping.get("supported", True):
        warnings.append(
            f"Product '{product.title}' ({product.product_type.value}) "
            "is not suited for TikTok Shop. Listing blocked."
        )

    # Missing artwork
    if not product.artwork_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no artwork artifact. "
            "TikTok Shop listings require product images."
        )

    # Missing mockup
    if not product.mockup_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no mockup artifact. "
            "Consider adding lifestyle/mockup images for TikTok."
        )

    # Unavailable product
    if product.availability == MerchAvailability.UNAVAILABLE:
        warnings.append(
            f"Product '{product.title}' availability is 'unavailable'. "
            "Should not be listed on TikTok Shop."
        )

    # Limited item without drop window
    if product.availability == MerchAvailability.LIMITED and not capsule.drop_window_start:
        warnings.append(
            f"Product '{product.title}' is limited but capsule has no "
            "drop window set. Set drop_window_start before listing."
        )

    return warnings


def _build_provider_payload(
    product: MerchProduct,
    capsule: MerchCapsule,
    mapping: dict,
) -> dict:
    """Build the TikTok Shop API payload shape (for inspection).

    This is what would be sent to POST /products if the real provider
    were connected. No API call is made.
    """
    return {
        "product_name": product.title,
        "description": _build_description(product, capsule),
        "category_id": None,
        "category_hint": mapping.get("category_hint", ""),
        "brand_name": "SCHLUESSELKINDER",
        "images": [{"uri": str(aid)} for aid in _build_images(product)],
        "skus": [
            {
                "sales_attributes": [{"attribute_name": "Size", "value_name": v.label}]
                if product.variants
                else [],
                "seller_sku": v.sku_suffix if product.variants else "",
                "original_price": "0.00",
            }
            for v in (product.variants or [])
        ]
        or [
            {
                "sales_attributes": [],
                "seller_sku": "",
                "original_price": "0.00",
            }
        ],
        "_meta": {
            "content_angle": mapping.get("content_angle", "").value
            if hasattr(mapping.get("content_angle", ""), "value")
            else str(mapping.get("content_angle", "")),
            "capsule_id": str(capsule.capsule_id),
            "region": "EU",
            "mock_only": True,
            "top_of_funnel": True,
        },
    }
