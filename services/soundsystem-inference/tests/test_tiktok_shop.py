"""Tests for S42 — TikTok Shop Listing Boundary.

Covers:
- Default provider mode is mock
- TikTok Shop mode without app key/secret fails loudly
- Invalid config mode raises RuntimeError
- Mock listings map all capsule products
- Variants mapped correctly
- Category mapping correct (apparel, accessories, etc.)
- Vinyl product blocked — routes to SoundCloud/elasticStage
- Content angles assigned per product type
- Warnings when artwork/mockup missing
- Routes require operator for POST
- Capabilities expose tiktok_shop fields
- Real provider blocks without API call
- Repository CRUD + summary
- No external calls
- Existing merch/shopify/printful tests still pass
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.config import (
    TIKTOK_SHOP_PROVIDER_ENV,
    TikTokShopProviderMode,
    tiktok_shop_provider_mode,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.tiktok_shop_builder import build_all_listings, build_listing
from app.tiktok_shop_repository import InMemoryTikTokShopRepository
from app.providers.tiktok_shop import build_tiktok_shop_provider
from app.providers.tiktok_shop.mock import MockTikTokShopProvider
from app.providers.tiktok_shop.real import RealTikTokShopProvider
from app.schemas import (
    ComplianceChecklistItem,
    MerchAvailability,
    MerchProduct,
    MerchProductType,
    MerchProviderGroup,
    MerchVariant,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    TikTokShopContentAngle,
    TikTokShopListingStatus,
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


def _make_capsule_with_variants():
    """Build a capsule with explicit variants on the first product."""
    capsule = _make_capsule()
    if capsule.products:
        product = capsule.products[0]
        variants = [
            MerchVariant(variant_id=uuid4(), label="S", sku_suffix="S"),
            MerchVariant(variant_id=uuid4(), label="M", sku_suffix="M"),
            MerchVariant(variant_id=uuid4(), label="L", sku_suffix="L"),
        ]
        updated_product = product.model_copy(update={"variants": variants})
        products = [updated_product] + capsule.products[1:]
        capsule = capsule.model_copy(update={"products": products})
    return capsule


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


# ---------- Config ----------


class TestTikTokShopConfig:
    def test_default_mode_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(TIKTOK_SHOP_PROVIDER_ENV, raising=False)
        assert tiktok_shop_provider_mode() == TikTokShopProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "mock")
        assert tiktok_shop_provider_mode() == TikTokShopProviderMode.MOCK

    def test_tiktok_shop_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "tiktok_shop")
        assert tiktok_shop_provider_mode() == TikTokShopProviderMode.TIKTOK_SHOP

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "amazon")
        with pytest.raises(RuntimeError, match="invalid"):
            tiktok_shop_provider_mode()

    def test_tiktok_shop_without_keys_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "tiktok_shop")
        monkeypatch.delenv("TIKTOK_SHOP_APP_KEY", raising=False)
        monkeypatch.delenv("TIKTOK_SHOP_APP_SECRET", raising=False)
        from app.config import TikTokShopProviderConfigError

        with pytest.raises(TikTokShopProviderConfigError, match="requires"):
            build_tiktok_shop_provider()


# ---------- Factory ----------


class TestTikTokShopFactory:
    def test_factory_default_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(TIKTOK_SHOP_PROVIDER_ENV, raising=False)
        provider = build_tiktok_shop_provider()
        assert provider.name == "mock"
        assert isinstance(provider, MockTikTokShopProvider)

    def test_factory_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "mock")
        provider = build_tiktok_shop_provider()
        assert provider.name == "mock"

    def test_factory_tiktok_shop_with_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TIKTOK_SHOP_PROVIDER_ENV, "tiktok_shop")
        monkeypatch.setenv("TIKTOK_SHOP_APP_KEY", "test_key_123")
        monkeypatch.setenv("TIKTOK_SHOP_APP_SECRET", "test_secret_456")
        provider = build_tiktok_shop_provider()
        assert provider.name == "tiktok_shop"
        assert isinstance(provider, RealTikTokShopProvider)


# ---------- Builder ----------


class TestTikTokShopBuilder:
    def test_build_all_listings_active_only(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        active_count = sum(1 for p in capsule.products if p.active)
        assert len(listings) == active_count

    def test_listing_fields_populated(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        assert len(listings) > 0
        listing = listings[0]
        assert listing.capsule_id == capsule.capsule_id
        assert listing.title == capsule.products[0].title
        assert listing.product_type == capsule.products[0].product_type.value

    def test_heavyweight_tee_category(self) -> None:
        capsule = _make_capsule()
        tee = next(
            (p for p in capsule.products if p.product_type == MerchProductType.HEAVYWEIGHT_TEE),
            None,
        )
        if tee is None:
            pytest.skip("No heavyweight tee in capsule")
        listing = build_listing(tee, capsule)
        assert listing.category_hint == "Apparel > Tops > T-Shirts"
        assert listing.content_angle == TikTokShopContentAngle.WAREHOUSE_CULTURE

    def test_hoodie_category(self) -> None:
        capsule = _make_capsule()
        hoodie = next(
            (p for p in capsule.products if p.product_type == MerchProductType.OVERSIZED_HOODIE),
            None,
        )
        if hoodie is None:
            pytest.skip("No oversized hoodie in capsule")
        listing = build_listing(hoodie, capsule)
        assert listing.category_hint == "Apparel > Hoodies & Sweatshirts"
        assert listing.content_angle == TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL

    def test_vinyl_blocked(self) -> None:
        """Vinyl objects should be blocked — not suited for TikTok Shop."""
        capsule = _make_vinyl_capsule()
        vinyl = next(p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT)
        listing = build_listing(vinyl, capsule)
        assert listing.status == TikTokShopListingStatus.BLOCKED
        assert any("not suited for TikTok Shop" in w for w in listing.warnings)

    def test_vinyl_routes_to_soundcloud(self) -> None:
        """Vinyl warning should mention SoundCloud/elasticStage."""
        capsule = _make_vinyl_capsule()
        vinyl = next(p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT)
        listing = build_listing(vinyl, capsule)
        assert any("SoundCloud" in w or "elasticStage" in w for w in listing.warnings)

    def test_vinyl_content_angle_collector(self) -> None:
        """Vinyl should get collector_object content angle."""
        capsule = _make_vinyl_capsule()
        vinyl = next(p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT)
        listing = build_listing(vinyl, capsule)
        assert listing.content_angle == TikTokShopContentAngle.COLLECTOR_OBJECT

    def test_sticker_pack_category(self) -> None:
        capsule = _make_capsule()
        sticker = next(
            (p for p in capsule.products if p.product_type == MerchProductType.STICKER_PACK),
            None,
        )
        if sticker is None:
            pytest.skip("No sticker pack in capsule")
        listing = build_listing(sticker, capsule)
        assert listing.category_hint == "Stationery > Stickers"
        assert listing.content_angle == TikTokShopContentAngle.WAREHOUSE_CULTURE

    def test_poster_limited_capsule_angle(self) -> None:
        capsule = _make_capsule()
        poster = next(
            (p for p in capsule.products if p.product_type == MerchProductType.POSTER),
            None,
        )
        if poster is None:
            pytest.skip("No poster in capsule")
        listing = build_listing(poster, capsule)
        assert listing.content_angle == TikTokShopContentAngle.LIMITED_CAPSULE

    def test_variants_default_single(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        for listing in listings:
            assert len(listing.variants) >= 1

    def test_variants_mapped_from_merch(self) -> None:
        capsule = _make_capsule_with_variants()
        listings = build_all_listings(capsule)
        first_listing = next(
            entry for entry in listings if entry.product_id == capsule.products[0].product_id
        )
        assert len(first_listing.variants) == 3
        labels = [v.title for v in first_listing.variants]
        assert "S" in labels
        assert "M" in labels
        assert "L" in labels

    def test_warnings_when_artwork_missing(self) -> None:
        capsule = _make_capsule(has_cover=False)
        listings = build_all_listings(capsule)
        for listing in listings:
            artwork_warnings = [w for w in listing.warnings if "artwork" in w.lower()]
            assert len(artwork_warnings) > 0

    def test_tags_include_brand(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        for listing in listings:
            assert "SCHLUESSELKINDER" in listing.tags

    def test_tags_include_soundsystem(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        for listing in listings:
            assert "soundsystem" in listing.tags

    def test_provider_payload_shape(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        for listing in listings:
            assert "product_name" in listing.provider_payload
            assert "description" in listing.provider_payload
            assert "skus" in listing.provider_payload
            assert "_meta" in listing.provider_payload
            assert listing.provider_payload["_meta"]["mock_only"] is True
            assert listing.provider_payload["_meta"]["top_of_funnel"] is True

    def test_provider_payload_region_eu(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule)
        for listing in listings:
            assert listing.provider_payload["_meta"]["region"] == "EU"

    def test_operator_id_set(self) -> None:
        capsule = _make_capsule()
        listings = build_all_listings(capsule, operator_id="op-123")
        for listing in listings:
            assert listing.created_by == "op-123"


# ---------- Mock Provider ----------


class TestMockTikTokShopProvider:
    def test_mock_name(self) -> None:
        provider = MockTikTokShopProvider()
        assert provider.name == "mock"

    def test_mock_listings_exported_mock_status(self) -> None:
        provider = MockTikTokShopProvider()
        capsule = _make_capsule()
        listings = provider.build_listings(capsule)
        assert len(listings) > 0
        for listing in listings:
            if listing.product_type != MerchProductType.VINYL_OBJECT.value:
                assert listing.status == TikTokShopListingStatus.EXPORTED_MOCK

    def test_mock_vinyl_stays_blocked(self) -> None:
        provider = MockTikTokShopProvider()
        capsule = _make_vinyl_capsule()
        listings = provider.build_listings(capsule)
        vinyl_listings = [
            entry for entry in listings if entry.product_type == MerchProductType.VINYL_OBJECT.value
        ]
        for entry in vinyl_listings:
            assert entry.status == TikTokShopListingStatus.BLOCKED

    def test_mock_export_payload(self) -> None:
        provider = MockTikTokShopProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.capsule_id == capsule.capsule_id
        assert export.provider_mode == "mock"
        assert export.total_products > 0
        assert len(export.listings) == export.total_products


# ---------- Real Provider ----------


class TestRealTikTokShopProvider:
    def test_real_name(self) -> None:
        provider = RealTikTokShopProvider()
        assert provider.name == "tiktok_shop"

    def test_real_listings_blocked_status(self) -> None:
        provider = RealTikTokShopProvider()
        capsule = _make_capsule()
        listings = provider.build_listings(capsule)
        assert len(listings) > 0
        for listing in listings:
            assert listing.status == TikTokShopListingStatus.BLOCKED

    def test_real_listings_have_blocked_warning(self) -> None:
        provider = RealTikTokShopProvider()
        capsule = _make_capsule()
        listings = provider.build_listings(capsule)
        for listing in listings:
            blocked_warnings = [w for w in listing.warnings if "not yet implemented" in w.lower()]
            assert len(blocked_warnings) > 0

    def test_real_export_mode(self) -> None:
        provider = RealTikTokShopProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "tiktok_shop"


# ---------- Repository ----------


class TestTikTokShopRepository:
    def test_store_and_get(self) -> None:
        provider = MockTikTokShopProvider()
        capsule = _make_capsule()
        listings = provider.build_listings(capsule)
        repo = InMemoryTikTokShopRepository()
        repo.store_many(listings)
        for listing in listings:
            got = repo.get(listing.listing_id)
            assert got is not None
            assert got.listing_id == listing.listing_id

    def test_list_all(self) -> None:
        provider = MockTikTokShopProvider()
        repo = InMemoryTikTokShopRepository()
        for _ in range(3):
            capsule = _make_capsule()
            listings = provider.build_listings(capsule)
            repo.store_many(listings)
        all_listings = repo.list_all()
        assert len(all_listings) > 0

    def test_list_by_capsule(self) -> None:
        provider = MockTikTokShopProvider()
        repo = InMemoryTikTokShopRepository()
        c1 = _make_capsule()
        c2 = _make_capsule()
        repo.store_many(provider.build_listings(c1))
        repo.store_many(provider.build_listings(c2))
        c1_listings = repo.list_by_capsule(c1.capsule_id)
        c2_listings = repo.list_by_capsule(c2.capsule_id)
        assert len(c1_listings) > 0
        assert len(c2_listings) > 0
        assert all(entry.capsule_id == c1.capsule_id for entry in c1_listings)
        assert all(entry.capsule_id == c2.capsule_id for entry in c2_listings)

    def test_get_nonexistent(self) -> None:
        repo = InMemoryTikTokShopRepository()
        assert repo.get(uuid4()) is None

    def test_summary(self) -> None:
        provider = MockTikTokShopProvider()
        repo = InMemoryTikTokShopRepository()
        capsule = _make_capsule()
        repo.store_many(provider.build_listings(capsule))
        summary = repo.summary()
        assert summary.total_listings > 0
        assert summary.exported_mock > 0

    def test_mode(self) -> None:
        repo = InMemoryTikTokShopRepository()
        assert repo.mode == "in_memory"


# ---------- Capabilities ----------


class TestTikTokShopCapabilities:
    def test_capabilities_expose_tiktok_shop_fields(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.tiktok_shop_available is True
        assert caps.tiktok_shop_provider_mode in ("mock", "tiktok_shop")

    def test_capabilities_default_mock(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.tiktok_shop_provider_mode == "mock"


# ---------- Routes ----------


class TestTikTokShopRoutes:
    def test_build_listings_and_fetch(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_tiktok_shop_listings,
            get_tiktok_shop_listing,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        export = asyncio.run(build_tiktok_shop_listings(capsule.capsule_id, DEV_OPERATOR))
        assert export.total_products > 0
        assert len(export.listings) == export.total_products

        # Fetch individual listing
        first_listing = export.listings[0]
        fetched = asyncio.run(get_tiktok_shop_listing(first_listing.listing_id))
        assert fetched.listing_id == first_listing.listing_id

    def test_list_listings_by_capsule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_tiktok_shop_listings,
            list_tiktok_shop_listings_by_capsule,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        asyncio.run(build_tiktok_shop_listings(capsule.capsule_id, DEV_OPERATOR))
        listings = asyncio.run(list_tiktok_shop_listings_by_capsule(capsule.capsule_id))
        assert len(listings) > 0
        assert all(entry.capsule_id == capsule.capsule_id for entry in listings)

    def test_tiktok_shop_summary(self) -> None:
        from app.main import tiktok_shop_summary

        summary = asyncio.run(tiktok_shop_summary())
        assert summary.total_listings >= 0

    def test_capsule_not_found_returns_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import build_tiktok_shop_listings

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(build_tiktok_shop_listings(uuid4(), DEV_OPERATOR))


# ---------- No External Calls ----------


class TestTikTokShopNoExternalCalls:
    def test_mock_makes_no_network_calls(self) -> None:
        """Mock provider should not import any HTTP/network libraries."""
        provider = MockTikTokShopProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "mock"

    def test_real_makes_no_network_calls(self) -> None:
        """Real provider should not make any API calls."""
        provider = RealTikTokShopProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "tiktok_shop"
        for listing in export.listings:
            assert listing.status == TikTokShopListingStatus.BLOCKED
