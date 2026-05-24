"""Tests for S43 — Merch Provider Aggregation View.

Covers:
- Empty providers show not_created for all products
- Shopify drafts reflected in aggregation
- Printful syncs reflected in aggregation
- TikTok listings reflected in aggregation
- All providers combined in matrix
- Warnings aggregated across providers
- Vinyl blocked shown across incompatible providers
- 404 for unknown capsule
- No mutating behavior (read-only)
- Product count and active count correct
- Provider modes reflected
- Summary counts correct
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.merch_capsule import build_merch_capsule_from_release
from app.merch_provider_aggregation import build_provider_aggregation
from app.providers.printful.mock import MockPrintfulSyncProvider
from app.providers.shopify.mock import MockShopifyDraftProvider
from app.providers.tiktok_shop.mock import MockTikTokShopProvider
from app.schemas import (
    ComplianceChecklistItem,
    MerchAvailability,
    MerchProduct,
    MerchProductType,
    MerchProviderGroup,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release(
    *,
    title: str = "TEST TRACK",
    genre: str | None = "Electronic",
    has_cover: bool = True,
) -> ReleasePack:
    assets = []
    if has_cover:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    assets.append(
        ReleaseAssetPlaceholder(
            asset_type="audio_master",
            label="Audio",
            expected_format="wav",
            ready=True,
            artifact_id=uuid4(),
        )
    )
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="SHIBARI KAWAII",
        status=ReleasePackStatus.DRAFT,
        genre=genre,
        social_copy=SocialCopy(
            soundcloud_description="sc",
            tiktok_caption="tk",
            instagram_caption="ig",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(code="license_clear", label="Licenses", passed=False),
        ],
        compliance_passed=False,
        assets=assets,
    )


def _make_capsule(*, has_cover: bool = True):
    release = _make_release(has_cover=has_cover)
    return build_merch_capsule_from_release(release, operator_id="test-op")


def _make_vinyl_capsule():
    """Build a capsule that includes a vinyl product."""
    release = _make_release(genre="Electronic")
    capsule = build_merch_capsule_from_release(release, operator_id="test-op")
    vinyl = [p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT]
    if not vinyl:
        products = list(capsule.products) + [
            MerchProduct(
                product_id=uuid4(),
                title="TEST VINYL",
                product_type=MerchProductType.VINYL_OBJECT,
                availability=MerchAvailability.LIMITED,
                provider_group=MerchProviderGroup.VINYL_PROVIDER,
                active=True,
            )
        ]
        capsule = capsule.model_copy(update={"products": products})
    return capsule


# ---------- Empty Providers ----------


class TestEmptyProviders:
    def test_all_not_created_when_no_providers(self) -> None:
        capsule = _make_capsule()
        agg = build_provider_aggregation(capsule)

        assert agg.capsule_id == capsule.capsule_id
        assert agg.product_count == len(capsule.products)
        assert agg.active_product_count == sum(1 for p in capsule.products if p.active)

        for ps in agg.products:
            assert ps.shopify_status == "not_created"
            assert ps.printful_status == "not_created"
            assert ps.tiktok_status == "not_created"

    def test_provider_summaries_show_not_created(self) -> None:
        capsule = _make_capsule()
        agg = build_provider_aggregation(capsule)

        for provider in agg.providers.values():
            assert provider.not_created == len(capsule.products)
            assert provider.exported_mock == 0
            assert provider.blocked == 0

    def test_summary_counts_zero_warnings(self) -> None:
        capsule = _make_capsule()
        agg = build_provider_aggregation(capsule)
        assert agg.summary.total_warnings == 0
        assert agg.summary.exported_mock_count == 0


# ---------- Shopify Drafts ----------


class TestShopifyDraftsReflected:
    def test_shopify_statuses_mapped(self) -> None:
        capsule = _make_capsule()
        provider = MockShopifyDraftProvider()
        drafts = provider.build_product_drafts(capsule)

        agg = build_provider_aggregation(capsule, shopify_drafts=drafts)

        for ps in agg.products:
            assert ps.shopify_status != "not_created"
        assert agg.providers["shopify"].exported_mock > 0

    def test_shopify_warnings_aggregated(self) -> None:
        capsule = _make_capsule(has_cover=False)
        provider = MockShopifyDraftProvider()
        drafts = provider.build_product_drafts(capsule)

        agg = build_provider_aggregation(capsule, shopify_drafts=drafts)

        shopify_warning_count = sum(len(ps.shopify_warnings) for ps in agg.products)
        assert shopify_warning_count > 0
        assert agg.providers["shopify"].warnings > 0


# ---------- Printful Syncs ----------


class TestPrintfulSyncsReflected:
    def test_printful_statuses_mapped(self) -> None:
        capsule = _make_capsule()
        provider = MockPrintfulSyncProvider()
        syncs = provider.build_product_syncs(capsule)

        agg = build_provider_aggregation(capsule, printful_syncs=syncs)

        for ps in agg.products:
            assert ps.printful_status != "not_created"
        assert agg.providers["printful"].exported_mock > 0

    def test_printful_warnings_aggregated(self) -> None:
        capsule = _make_capsule(has_cover=False)
        provider = MockPrintfulSyncProvider()
        syncs = provider.build_product_syncs(capsule)

        agg = build_provider_aggregation(capsule, printful_syncs=syncs)

        printful_warning_count = sum(len(ps.printful_warnings) for ps in agg.products)
        assert printful_warning_count > 0
        assert agg.providers["printful"].warnings > 0


# ---------- TikTok Listings ----------


class TestTikTokListingsReflected:
    def test_tiktok_statuses_mapped(self) -> None:
        capsule = _make_capsule()
        provider = MockTikTokShopProvider()
        listings = provider.build_listings(capsule)

        agg = build_provider_aggregation(capsule, tiktok_listings=listings)

        for ps in agg.products:
            assert ps.tiktok_status != "not_created"
        assert agg.providers["tiktok_shop"].exported_mock > 0

    def test_tiktok_warnings_aggregated(self) -> None:
        capsule = _make_capsule(has_cover=False)
        provider = MockTikTokShopProvider()
        listings = provider.build_listings(capsule)

        agg = build_provider_aggregation(capsule, tiktok_listings=listings)

        tiktok_warning_count = sum(len(ps.tiktok_warnings) for ps in agg.products)
        assert tiktok_warning_count > 0
        assert agg.providers["tiktok_shop"].warnings > 0


# ---------- Combined Providers ----------


class TestCombinedProviders:
    def test_all_providers_populated(self) -> None:
        capsule = _make_capsule()
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        for ps in agg.products:
            assert ps.shopify_status != "not_created"
            assert ps.printful_status != "not_created"
            assert ps.tiktok_status != "not_created"

    def test_summary_exported_mock_count(self) -> None:
        capsule = _make_capsule()
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        assert agg.summary.exported_mock_count > 0

    def test_provider_modes_reflected(self) -> None:
        capsule = _make_capsule()
        agg = build_provider_aggregation(
            capsule,
            shopify_mode="shopify",
            printful_mode="printful",
            tiktok_mode="tiktok_shop",
        )

        assert agg.providers["shopify"].mode == "shopify"
        assert agg.providers["printful"].mode == "printful"
        assert agg.providers["tiktok_shop"].mode == "tiktok_shop"


# ---------- Vinyl Blocked ----------


class TestVinylBlocked:
    def test_vinyl_blocked_across_providers(self) -> None:
        capsule = _make_vinyl_capsule()
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        vinyl_products = [
            ps for ps in agg.products if ps.product_type == MerchProductType.VINYL_OBJECT.value
        ]
        assert len(vinyl_products) > 0

        for vp in vinyl_products:
            # Vinyl should be blocked on Printful and TikTok
            assert vp.printful_status == "blocked"
            assert vp.tiktok_status == "blocked"

    def test_blocked_count_in_summary(self) -> None:
        capsule = _make_vinyl_capsule()
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        assert agg.summary.blocked_count > 0


# ---------- Warnings Aggregation ----------


class TestWarningsAggregation:
    def test_total_warnings_across_providers(self) -> None:
        capsule = _make_capsule(has_cover=False)
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        assert agg.summary.total_warnings > 0

    def test_per_product_warning_count(self) -> None:
        capsule = _make_capsule(has_cover=False)
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=shopify.build_product_drafts(capsule),
            printful_syncs=printful.build_product_syncs(capsule),
            tiktok_listings=tiktok.build_listings(capsule),
        )

        for ps in agg.products:
            expected = (
                len(ps.shopify_warnings) + len(ps.printful_warnings) + len(ps.tiktok_warnings)
            )
            assert ps.total_warnings == expected


# ---------- Route Tests ----------


class TestProviderAggregationRoute:
    def test_route_returns_aggregation(self) -> None:
        from app.main import (
            get_merch_provider_status,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        agg = asyncio.run(get_merch_provider_status(capsule.capsule_id))
        assert agg.capsule_id == capsule.capsule_id
        assert agg.capsule_status == capsule.status.value
        assert agg.product_count == len(capsule.products)
        assert "shopify" in agg.providers
        assert "printful" in agg.providers
        assert "tiktok_shop" in agg.providers

    def test_route_reflects_shopify_drafts(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_shopify_drafts,
            get_merch_provider_status,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        # Build shopify drafts first
        asyncio.run(build_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))

        # Now check aggregation
        agg = asyncio.run(get_merch_provider_status(capsule.capsule_id))
        has_shopify = any(ps.shopify_status != "not_created" for ps in agg.products)
        assert has_shopify

    def test_route_reflects_printful_syncs(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_printful_syncs,
            get_merch_provider_status,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        asyncio.run(build_printful_syncs(capsule.capsule_id, DEV_OPERATOR))

        agg = asyncio.run(get_merch_provider_status(capsule.capsule_id))
        has_printful = any(ps.printful_status != "not_created" for ps in agg.products)
        assert has_printful

    def test_route_reflects_tiktok_listings(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_tiktok_shop_listings,
            get_merch_provider_status,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        asyncio.run(build_tiktok_shop_listings(capsule.capsule_id, DEV_OPERATOR))

        agg = asyncio.run(get_merch_provider_status(capsule.capsule_id))
        has_tiktok = any(ps.tiktok_status != "not_created" for ps in agg.products)
        assert has_tiktok

    def test_route_404_for_unknown_capsule(self) -> None:
        from app.main import get_merch_provider_status

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(get_merch_provider_status(uuid4()))


# ---------- No Mutating Behavior ----------


class TestNoMutatingBehavior:
    def test_aggregation_is_read_only(self) -> None:
        """Building an aggregation should not modify any repository data."""
        capsule = _make_capsule()
        shopify = MockShopifyDraftProvider()
        printful = MockPrintfulSyncProvider()
        tiktok = MockTikTokShopProvider()

        drafts = shopify.build_product_drafts(capsule)
        syncs = printful.build_product_syncs(capsule)
        listings = tiktok.build_listings(capsule)

        # Build aggregation multiple times
        agg1 = build_provider_aggregation(
            capsule,
            shopify_drafts=drafts,
            printful_syncs=syncs,
            tiktok_listings=listings,
        )
        agg2 = build_provider_aggregation(
            capsule,
            shopify_drafts=drafts,
            printful_syncs=syncs,
            tiktok_listings=listings,
        )

        # Same results — no state mutation
        assert agg1.capsule_id == agg2.capsule_id
        assert agg1.summary.total_warnings == agg2.summary.total_warnings
        assert len(agg1.products) == len(agg2.products)

    def test_no_commerce_api_imports(self) -> None:
        """The aggregation module should not import HTTP libraries."""
        import app.merch_provider_aggregation as mod

        source = open(mod.__file__).read()
        assert "requests" not in source
        assert "httpx" not in source
        assert "aiohttp" not in source
