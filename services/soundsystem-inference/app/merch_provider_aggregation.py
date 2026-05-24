"""Merch Provider Aggregation Builder (S43).

Builds a unified read-only view of all commerce provider statuses for
a MerchCapsule. Aggregates Shopify Draft, Printful Sync, and TikTok
Shop Listing statuses into a single product-by-provider matrix.

No real commerce API calls. No inventory mutation. No publishing.
Read-only aggregation of existing repository data.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas import (
    MerchCapsule,
    MerchProviderAggregation,
    MerchProviderAggregationSummary,
    MerchProviderProductStatus,
    MerchProviderStatus,
    PrintfulProductSync,
    ShopifyProductDraft,
    TikTokShopListing,
)


def build_provider_aggregation(
    capsule: MerchCapsule,
    *,
    shopify_drafts: list[ShopifyProductDraft] | None = None,
    printful_syncs: list[PrintfulProductSync] | None = None,
    tiktok_listings: list[TikTokShopListing] | None = None,
    shopify_mode: str = "mock",
    printful_mode: str = "mock",
    tiktok_mode: str = "mock",
) -> MerchProviderAggregation:
    """Build a unified provider aggregation for a capsule.

    All parameters are optional — missing providers show as not_created.
    """
    shopify_drafts = shopify_drafts or []
    printful_syncs = printful_syncs or []
    tiktok_listings = tiktok_listings or []

    # Index by product_id for O(1) lookup
    shopify_by_product: dict[UUID, ShopifyProductDraft] = {
        draft.product_id: draft for draft in shopify_drafts
    }
    printful_by_product: dict[UUID, PrintfulProductSync] = {
        sync.product_id: sync for sync in printful_syncs
    }
    tiktok_by_product: dict[UUID, TikTokShopListing] = {
        listing.product_id: listing for listing in tiktok_listings
    }

    # Build per-product status
    product_statuses: list[MerchProviderProductStatus] = []
    for product in capsule.products:
        shopify_draft = shopify_by_product.get(product.product_id)
        printful_sync = printful_by_product.get(product.product_id)
        tiktok_listing = tiktok_by_product.get(product.product_id)

        shopify_status = shopify_draft.status.value if shopify_draft else "not_created"
        printful_status = printful_sync.status.value if printful_sync else "not_created"
        tiktok_status = tiktok_listing.status.value if tiktok_listing else "not_created"

        shopify_warnings = list(shopify_draft.warnings) if shopify_draft else []
        printful_warnings = list(printful_sync.warnings) if printful_sync else []
        tiktok_warnings = list(tiktok_listing.warnings) if tiktok_listing else []

        total_warnings = len(shopify_warnings) + len(printful_warnings) + len(tiktok_warnings)

        # Detect stale provider payloads (title drift after product edit)
        stale = False
        if shopify_draft and shopify_draft.title != product.title:
            stale = True
            shopify_warnings.append(
                f"Shopify draft title '{shopify_draft.title}' differs from capsule product title '{product.title}'. Rebuild Shopify drafts."
            )
            total_warnings += 1
        if printful_sync and printful_sync.title != product.title:
            stale = True
            printful_warnings.append(
                f"Printful sync title '{printful_sync.title}' differs from capsule product title '{product.title}'. Rebuild Printful syncs."
            )
            total_warnings += 1
        if tiktok_listing and tiktok_listing.title != product.title:
            stale = True
            tiktok_warnings.append(
                f"TikTok listing title '{tiktok_listing.title}' differs from capsule product title '{product.title}'. Rebuild TikTok listings."
            )
            total_warnings += 1

        product_statuses.append(
            MerchProviderProductStatus(
                product_id=product.product_id,
                title=product.title,
                product_type=product.product_type.value,
                availability=product.availability.value,
                active=product.active,
                shopify_status=shopify_status,
                printful_status=printful_status,
                tiktok_status=tiktok_status,
                shopify_warnings=shopify_warnings,
                printful_warnings=printful_warnings,
                tiktok_warnings=tiktok_warnings,
                total_warnings=total_warnings,
                stale=stale,
            )
        )

    # Build per-provider summary
    shopify_provider = _build_provider_status(
        "shopify", shopify_mode, product_statuses, "shopify_status"
    )
    printful_provider = _build_provider_status(
        "printful", printful_mode, product_statuses, "printful_status"
    )
    tiktok_provider = _build_provider_status(
        "tiktok_shop", tiktok_mode, product_statuses, "tiktok_status"
    )

    # Build aggregate summary
    total_warnings = sum(ps.total_warnings for ps in product_statuses)
    ready_count = sum(
        1
        for ps in product_statuses
        if ps.shopify_status == "exported_mock"
        or ps.printful_status == "exported_mock"
        or ps.tiktok_status == "exported_mock"
    )
    blocked_count = sum(
        1
        for ps in product_statuses
        if ps.shopify_status == "blocked"
        or ps.printful_status == "blocked"
        or ps.tiktok_status == "blocked"
    )
    exported_mock_count = (
        shopify_provider.exported_mock
        + printful_provider.exported_mock
        + tiktok_provider.exported_mock
    )
    not_created_count = (
        shopify_provider.not_created + printful_provider.not_created + tiktok_provider.not_created
    )

    active_products = [p for p in capsule.products if p.active]

    return MerchProviderAggregation(
        capsule_id=capsule.capsule_id,
        capsule_title=capsule.title,
        capsule_status=capsule.status.value,
        product_count=len(capsule.products),
        active_product_count=len(active_products),
        providers={
            "shopify": shopify_provider,
            "printful": printful_provider,
            "tiktok_shop": tiktok_provider,
        },
        products=product_statuses,
        summary=MerchProviderAggregationSummary(
            total_warnings=total_warnings,
            ready_count=ready_count,
            blocked_count=blocked_count,
            exported_mock_count=exported_mock_count,
            not_created_count=not_created_count,
        ),
    )


def _build_provider_status(
    provider_name: str,
    mode: str,
    product_statuses: list[MerchProviderProductStatus],
    status_field: str,
) -> MerchProviderStatus:
    """Build a MerchProviderStatus from product statuses."""
    statuses = [getattr(ps, status_field) for ps in product_statuses]
    warnings_field = status_field.replace("_status", "_warnings")
    total_warnings = sum(len(getattr(ps, warnings_field)) for ps in product_statuses)

    return MerchProviderStatus(
        provider=provider_name,
        mode=mode,
        total_products=len(statuses),
        exported_mock=sum(1 for s in statuses if s == "exported_mock"),
        blocked=sum(1 for s in statuses if s == "blocked"),
        draft=sum(1 for s in statuses if s == "draft"),
        not_created=sum(1 for s in statuses if s == "not_created"),
        warnings=total_warnings,
    )
