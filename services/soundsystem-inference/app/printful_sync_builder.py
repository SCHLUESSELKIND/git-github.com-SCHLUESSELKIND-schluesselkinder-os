"""Printful Sync Builder Logic (S41).

Maps MerchCapsule products to Printful-compatible sync payloads.
No real Printful API calls. No product creation. No fulfillment.
No inventory sync. No order placement.

Product type mapping:
- heavyweight_tee -> DTG front/back, Printful apparel catalog
- oversized_hoodie -> DTG front, Printful apparel catalog
- longsleeve -> DTG front, Printful apparel catalog
- beanie -> embroidery, Printful accessories catalog
- tote -> DTG, Printful accessories catalog
- poster -> warning: prefer Gelato/premium drop provider
- sticker_pack -> warning: prefer premium drop provider
- vinyl_object -> blocked: not Printful-compatible
"""

from __future__ import annotations

from uuid import uuid4

from app.schemas import (
    MerchCapsule,
    MerchProduct,
    MerchProductType,
    PrintfulPrintTechnique,
    PrintfulProductSync,
    PrintfulSyncStatus,
    PrintfulVariantSync,
)

# ---------- Product type to Printful mapping ----------

_PRINTFUL_CATALOG_MAP: dict[MerchProductType, dict] = {
    MerchProductType.HEAVYWEIGHT_TEE: {
        "catalog_hint": "Unisex Heavyweight T-Shirt | Gildan 5000",
        "technique": PrintfulPrintTechnique.DTG,
        "placement": "front",
        "supported": True,
    },
    MerchProductType.OVERSIZED_HOODIE: {
        "catalog_hint": "Unisex Heavy Blend Hoodie | Gildan 18500",
        "technique": PrintfulPrintTechnique.DTG,
        "placement": "front",
        "supported": True,
    },
    MerchProductType.LONGSLEEVE: {
        "catalog_hint": "Unisex Long Sleeve Tee | Bella+Canvas 3501",
        "technique": PrintfulPrintTechnique.DTG,
        "placement": "front",
        "supported": True,
    },
    MerchProductType.BEANIE: {
        "catalog_hint": "Knit Beanie | Yupoong 1501KC",
        "technique": PrintfulPrintTechnique.EMBROIDERY,
        "placement": "front_center",
        "supported": True,
    },
    MerchProductType.TOTE: {
        "catalog_hint": "Tote Bag | Q-Tees Q800",
        "technique": PrintfulPrintTechnique.DTG,
        "placement": "front",
        "supported": True,
    },
    MerchProductType.POSTER: {
        "catalog_hint": "Enhanced Matte Paper Poster",
        "technique": PrintfulPrintTechnique.NOT_APPLICABLE,
        "placement": "full_bleed",
        "supported": True,
        "warning": (
            "Poster fulfillment via Printful is possible but Gelato/premium "
            "drop provider may offer better quality for limited runs."
        ),
    },
    MerchProductType.STICKER_PACK: {
        "catalog_hint": "Kiss-Cut Stickers",
        "technique": PrintfulPrintTechnique.NOT_APPLICABLE,
        "placement": "full",
        "supported": True,
        "warning": (
            "Sticker packs via Printful are limited. Consider premium drop "
            "provider or Gelato for higher-quality sticker production."
        ),
    },
    MerchProductType.VINYL_OBJECT: {
        "catalog_hint": "",
        "technique": PrintfulPrintTechnique.NOT_APPLICABLE,
        "placement": "",
        "supported": False,
        "warning": "Vinyl objects are not Printful-compatible. Use vinyl_provider.",
    },
}


def build_product_sync(
    product: MerchProduct,
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> PrintfulProductSync:
    """Convert a single MerchProduct into a PrintfulProductSync."""
    mapping = _PRINTFUL_CATALOG_MAP.get(
        product.product_type,
        {
            "catalog_hint": "",
            "technique": PrintfulPrintTechnique.NOT_APPLICABLE,
            "placement": "",
            "supported": False,
            "warning": f"Unknown product type: {product.product_type}",
        },
    )

    variants = _build_variants(product)
    warnings = _build_warnings(product, mapping)
    provider_payload = _build_provider_payload(product, capsule, mapping)

    status = PrintfulSyncStatus.DRAFT
    if not mapping.get("supported", True):
        status = PrintfulSyncStatus.BLOCKED

    return PrintfulProductSync(
        sync_id=uuid4(),
        capsule_id=capsule.capsule_id,
        product_id=product.product_id,
        title=product.title,
        product_type=product.product_type.value,
        provider_catalog_hint=mapping["catalog_hint"],
        print_technique=mapping["technique"],
        placement=mapping["placement"],
        variants=variants,
        artwork_artifact_id=product.artwork_artifact_id,
        mockup_artifact_id=product.mockup_artifact_id,
        provider_payload=provider_payload,
        status=status,
        warnings=warnings,
        created_by=operator_id,
    )


def build_all_syncs(
    capsule: MerchCapsule,
    *,
    operator_id: str | None = None,
) -> list[PrintfulProductSync]:
    """Build Printful sync payloads for all active products in a capsule."""
    syncs: list[PrintfulProductSync] = []
    for product in capsule.products:
        if not product.active:
            continue
        sync = build_product_sync(product, capsule, operator_id=operator_id)
        syncs.append(sync)
    return syncs


# ---------- Internal builders ----------


def _build_variants(product: MerchProduct) -> list[PrintfulVariantSync]:
    """Map MerchVariants to PrintfulVariantSyncs."""
    if product.variants:
        return [
            PrintfulVariantSync(
                variant_id=v.variant_id,
                title=v.label,
                sku_suffix=v.sku_suffix,
                size=v.label,
            )
            for v in product.variants
        ]
    return [
        PrintfulVariantSync(
            variant_id=product.product_id,
            title="Default",
            size="One Size",
        )
    ]


def _build_warnings(product: MerchProduct, mapping: dict) -> list[str]:
    """Generate warnings for the product sync."""
    warnings: list[str] = []

    # Mapping-specific warning
    if "warning" in mapping:
        warnings.append(mapping["warning"])

    # Unsupported product
    if not mapping.get("supported", True):
        warnings.append(
            f"Product '{product.title}' ({product.product_type.value}) "
            "is not supported by Printful. Sync blocked."
        )

    # Missing artwork
    if not product.artwork_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no artwork artifact. "
            "Printful sync requires print-ready artwork."
        )

    # Missing mockup
    if not product.mockup_artifact_id:
        warnings.append(
            f"Product '{product.title}' has no mockup artifact. "
            "Consider generating mockups before sync."
        )

    # Unavailable product
    if product.availability.value == "unavailable":
        warnings.append(
            f"Product '{product.title}' availability is 'unavailable'. "
            "Verify availability before syncing to Printful."
        )

    return warnings


def _build_provider_payload(
    product: MerchProduct,
    capsule: MerchCapsule,
    mapping: dict,
) -> dict:
    """Build the Printful API payload shape (for inspection).

    This is what would be sent to POST /store/products if the real
    provider were connected. No API call is made.
    """
    return {
        "sync_product": {
            "name": product.title,
            "thumbnail": (
                str(product.artwork_artifact_id) if product.artwork_artifact_id else None
            ),
        },
        "sync_variants": [
            {
                "variant_id": None,
                "retail_price": "0.00",
                "sku": v.sku_suffix if product.variants else "",
                "files": [
                    {
                        "type": mapping.get("placement", "front"),
                        "url": (
                            str(product.artwork_artifact_id)
                            if product.artwork_artifact_id
                            else "artwork_required"
                        ),
                    }
                ],
            }
            for v in (product.variants or [])
        ]
        or [
            {
                "variant_id": None,
                "retail_price": "0.00",
                "files": [
                    {
                        "type": mapping.get("placement", "front"),
                        "url": (
                            str(product.artwork_artifact_id)
                            if product.artwork_artifact_id
                            else "artwork_required"
                        ),
                    }
                ],
            }
        ],
        "_meta": {
            "catalog_hint": mapping.get("catalog_hint", ""),
            "print_technique": mapping.get("technique", "").value
            if hasattr(mapping.get("technique", ""), "value")
            else str(mapping.get("technique", "")),
            "capsule_id": str(capsule.capsule_id),
            "mock_only": True,
        },
    }
