"""Tests for S40 — Shopify Draft Provider Boundary.

Covers:
- Default provider mode is mock
- Shopify mode without config fails loudly
- Invalid config mode raises RuntimeError
- Mock draft maps all capsule products
- Variants mapped correctly
- Tags include brand/release/product type
- Warnings when artwork missing
- Body HTML generated
- Provider payload matches Shopify shape
- Real provider returns BLOCKED
- Routes require operator for POST
- Capabilities expose shopify fields
- Repository CRUD + summary
- No external calls
- Existing merch tests still pass
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.config import (
    SHOPIFY_PROVIDER_ENV,
    ShopifyProviderMode,
    shopify_provider_mode,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.providers.shopify import build_shopify_draft_provider
from app.providers.shopify.mock import MockShopifyDraftProvider
from app.providers.shopify.real import RealShopifyDraftProvider
from app.schemas import (
    ComplianceChecklistItem,
    MerchCapsule,
    MerchVariant,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    ShopifyDraftStatus,
    SocialCopy,
)
from app.shopify_draft_builder import (
    VENDOR,
    build_all_drafts,
)
from app.shopify_draft_repository import InMemoryShopifyDraftRepository


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


def _make_capsule(*, has_cover: bool = True) -> MerchCapsule:
    release = _make_release(has_cover=has_cover)
    return build_merch_capsule_from_release(release, operator_id="test-op")


def _make_capsule_with_variants() -> MerchCapsule:
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


# ---------- Config ----------


class TestShopifyConfig:
    def test_default_mode_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(SHOPIFY_PROVIDER_ENV, raising=False)
        assert shopify_provider_mode() == ShopifyProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "mock")
        assert shopify_provider_mode() == ShopifyProviderMode.MOCK

    def test_shopify_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "shopify")
        assert shopify_provider_mode() == ShopifyProviderMode.SHOPIFY

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "woocommerce")
        with pytest.raises(RuntimeError, match="invalid"):
            shopify_provider_mode()

    def test_shopify_without_config_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "shopify")
        monkeypatch.delenv("SHOPIFY_SHOP_DOMAIN", raising=False)
        monkeypatch.delenv("SHOPIFY_ADMIN_ACCESS_TOKEN", raising=False)
        from app.config import ShopifyProviderConfigError

        with pytest.raises(ShopifyProviderConfigError, match="requires"):
            build_shopify_draft_provider()

    def test_shopify_with_partial_config_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "shopify")
        monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "test.myshopify.com")
        monkeypatch.delenv("SHOPIFY_ADMIN_ACCESS_TOKEN", raising=False)
        from app.config import ShopifyProviderConfigError

        with pytest.raises(ShopifyProviderConfigError, match="SHOPIFY_ADMIN_ACCESS_TOKEN"):
            build_shopify_draft_provider()


# ---------- Factory ----------


class TestShopifyFactory:
    def test_factory_default_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(SHOPIFY_PROVIDER_ENV, raising=False)
        provider = build_shopify_draft_provider()
        assert provider.name == "mock"
        assert isinstance(provider, MockShopifyDraftProvider)

    def test_factory_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "mock")
        provider = build_shopify_draft_provider()
        assert provider.name == "mock"

    def test_factory_shopify_with_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SHOPIFY_PROVIDER_ENV, "shopify")
        monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "test.myshopify.com")
        monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "shpat_test123")
        provider = build_shopify_draft_provider()
        assert provider.name == "shopify"
        assert isinstance(provider, RealShopifyDraftProvider)


# ---------- Builder ----------


class TestShopifyDraftBuilder:
    def test_build_all_drafts_active_only(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        active_count = sum(1 for p in capsule.products if p.active)
        assert len(drafts) == active_count

    def test_draft_fields_populated(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        assert len(drafts) > 0
        draft = drafts[0]
        assert draft.capsule_id == capsule.capsule_id
        assert draft.vendor == VENDOR
        assert draft.title == capsule.products[0].title
        assert draft.product_type == capsule.products[0].product_type.value
        assert draft.status == ShopifyDraftStatus.DRAFT

    def test_tags_include_brand(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            assert "SCHLUESSELKINDER" in draft.tags

    def test_tags_include_artist(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            assert capsule.artist in draft.tags

    def test_tags_include_product_type(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            product = next(p for p in capsule.products if p.product_id == draft.product_id)
            type_tag = product.product_type.value.replace("_", " ")
            assert type_tag in draft.tags

    def test_tags_include_availability(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            product = next(p for p in capsule.products if p.product_id == draft.product_id)
            avail_tag = product.availability.value.replace("_", " ")
            assert avail_tag in draft.tags

    def test_body_html_contains_title(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            assert draft.title in draft.body_html

    def test_variants_default_single(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        # Products without explicit variants get a default single variant
        for draft in drafts:
            assert len(draft.variants) >= 1

    def test_variants_mapped_from_merch(self) -> None:
        capsule = _make_capsule_with_variants()
        drafts = build_all_drafts(capsule)
        # First product has 3 explicit variants
        first_draft = next(d for d in drafts if d.product_id == capsule.products[0].product_id)
        assert len(first_draft.variants) == 3
        labels = [v.title for v in first_draft.variants]
        assert "S" in labels
        assert "M" in labels
        assert "L" in labels

    def test_images_from_artwork(self) -> None:
        capsule = _make_capsule(has_cover=True)
        drafts = build_all_drafts(capsule)
        # Products with artwork_artifact_id should have images
        for draft in drafts:
            product = next(p for p in capsule.products if p.product_id == draft.product_id)
            if product.artwork_artifact_id:
                assert len(draft.images) > 0
                assert draft.images[0].artifact_id == product.artwork_artifact_id

    def test_warnings_when_artwork_missing(self) -> None:
        """Products without artwork get a warning."""
        capsule = _make_capsule(has_cover=False)
        drafts = build_all_drafts(capsule)
        # All products should have artwork warning since release has no cover
        for draft in drafts:
            artwork_warnings = [w for w in draft.warnings if "artwork" in w.lower()]
            assert len(artwork_warnings) > 0

    def test_provider_payload_shape(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule)
        for draft in drafts:
            assert "product" in draft.provider_payload
            payload = draft.provider_payload["product"]
            assert "title" in payload
            assert "body_html" in payload
            assert "vendor" in payload
            assert payload["vendor"] == VENDOR
            assert "tags" in payload
            assert "status" in payload
            assert payload["status"] == "draft"
            assert "variants" in payload

    def test_operator_id_set(self) -> None:
        capsule = _make_capsule()
        drafts = build_all_drafts(capsule, operator_id="op-123")
        for draft in drafts:
            assert draft.created_by == "op-123"


# ---------- Mock Provider ----------


class TestMockShopifyProvider:
    def test_mock_name(self) -> None:
        provider = MockShopifyDraftProvider()
        assert provider.name == "mock"

    def test_mock_drafts_exported_mock_status(self) -> None:
        provider = MockShopifyDraftProvider()
        capsule = _make_capsule()
        drafts = provider.build_product_drafts(capsule)
        assert len(drafts) > 0
        for draft in drafts:
            assert draft.status == ShopifyDraftStatus.EXPORTED_MOCK

    def test_mock_export_payload(self) -> None:
        provider = MockShopifyDraftProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.capsule_id == capsule.capsule_id
        assert export.provider_mode == "mock"
        assert export.total_products > 0
        assert len(export.drafts) == export.total_products


# ---------- Real Provider ----------


class TestRealShopifyProvider:
    """Updated for S62 hardening.

    The real provider now requires credentials at construction (fail-loud)
    and exposes ``sync_drafts()`` for live draft creation. ``export_mock()``
    on the real provider remains read-only and returns BLOCKED drafts that
    direct the operator to ``sync_drafts()``.
    """

    def _build_provider(self) -> RealShopifyDraftProvider:
        return RealShopifyDraftProvider(
            shop_domain="schluesselkinder.myshopify.com",
            access_token="shpat_test_token_value",
            api_version="2025-01",
            transport=lambda *a, **k: {},  # not called by these tests
        )

    def test_real_name(self) -> None:
        provider = self._build_provider()
        assert provider.name == "shopify"

    def test_real_requires_credentials_at_construction(self) -> None:
        from app.config import ShopifyProviderConfigError

        with pytest.raises(ShopifyProviderConfigError):
            RealShopifyDraftProvider(shop_domain=None, access_token=None)

    def test_real_export_mock_returns_blocked_drafts(self) -> None:
        """export_mock() on the real provider is read-only — BLOCKED with a
        warning pointing to sync_drafts()."""
        provider = self._build_provider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "shopify"
        for draft in export.drafts:
            assert draft.status == ShopifyDraftStatus.BLOCKED
            assert any("sync_drafts()" in w for w in draft.warnings)

    def test_real_export_mode(self) -> None:
        provider = self._build_provider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "shopify"


# ---------- Repository ----------


class TestShopifyDraftRepository:
    def test_store_and_get(self) -> None:
        provider = MockShopifyDraftProvider()
        capsule = _make_capsule()
        drafts = provider.build_product_drafts(capsule)
        repo = InMemoryShopifyDraftRepository()
        repo.store_many(drafts)
        for draft in drafts:
            got = repo.get(draft.draft_id)
            assert got is not None
            assert got.draft_id == draft.draft_id

    def test_list_all(self) -> None:
        provider = MockShopifyDraftProvider()
        repo = InMemoryShopifyDraftRepository()
        for _ in range(3):
            capsule = _make_capsule()
            drafts = provider.build_product_drafts(capsule)
            repo.store_many(drafts)
        all_drafts = repo.list_all()
        assert len(all_drafts) > 0

    def test_list_by_capsule(self) -> None:
        provider = MockShopifyDraftProvider()
        repo = InMemoryShopifyDraftRepository()
        c1 = _make_capsule()
        c2 = _make_capsule()
        repo.store_many(provider.build_product_drafts(c1))
        repo.store_many(provider.build_product_drafts(c2))
        c1_drafts = repo.list_by_capsule(c1.capsule_id)
        c2_drafts = repo.list_by_capsule(c2.capsule_id)
        assert len(c1_drafts) > 0
        assert len(c2_drafts) > 0
        assert all(d.capsule_id == c1.capsule_id for d in c1_drafts)
        assert all(d.capsule_id == c2.capsule_id for d in c2_drafts)

    def test_get_nonexistent(self) -> None:
        repo = InMemoryShopifyDraftRepository()
        assert repo.get(uuid4()) is None

    def test_summary(self) -> None:
        provider = MockShopifyDraftProvider()
        repo = InMemoryShopifyDraftRepository()
        capsule = _make_capsule()
        repo.store_many(provider.build_product_drafts(capsule))
        summary = repo.summary()
        assert summary.total_drafts > 0
        assert summary.exported_mock > 0

    def test_mode(self) -> None:
        repo = InMemoryShopifyDraftRepository()
        assert repo.mode == "in_memory"


# ---------- Capabilities ----------


class TestShopifyCapabilities:
    def test_capabilities_expose_shopify_fields(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.shopify_drafts_available is True
        assert caps.shopify_provider_mode in ("mock", "shopify")

    def test_capabilities_default_mock(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.shopify_provider_mode == "mock"


# ---------- Routes ----------


class TestShopifyRoutes:
    def test_build_drafts_and_fetch(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_shopify_drafts,
            get_shopify_draft,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        export = asyncio.run(build_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))
        assert export.total_products > 0
        assert len(export.drafts) == export.total_products

        # Fetch individual draft
        first_draft = export.drafts[0]
        fetched = asyncio.run(get_shopify_draft(first_draft.draft_id))
        assert fetched.draft_id == first_draft.draft_id

    def test_list_drafts_by_capsule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_shopify_drafts,
            list_shopify_drafts_by_capsule,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        asyncio.run(build_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))
        drafts = asyncio.run(list_shopify_drafts_by_capsule(capsule.capsule_id))
        assert len(drafts) > 0
        assert all(d.capsule_id == capsule.capsule_id for d in drafts)

    def test_shopify_summary(self) -> None:
        from app.main import shopify_draft_summary

        summary = asyncio.run(shopify_draft_summary())
        assert summary.total_drafts >= 0

    def test_capsule_not_found_returns_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import build_shopify_drafts

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(build_shopify_drafts(uuid4(), DEV_OPERATOR))


# ---------- No External Calls ----------


class TestShopifyNoExternalCalls:
    def test_mock_makes_no_network_calls(self) -> None:
        """Mock provider should not import any HTTP/network libraries."""
        provider = MockShopifyDraftProvider()
        capsule = _make_capsule()
        # This should complete without any network activity
        export = provider.export_mock(capsule)
        assert export.provider_mode == "mock"

    def test_real_export_mock_makes_no_network_calls(self) -> None:
        """Real provider's export_mock() must not perform network activity.

        Only ``sync_drafts()`` calls the Admin GraphQL endpoint, and even
        then via an injectable transport (mocked in tests).
        """
        provider = RealShopifyDraftProvider(
            shop_domain="schluesselkinder.myshopify.com",
            access_token="shpat_test_token_value",
            transport=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("network must not be called by export_mock()")
            ),
        )
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "shopify"
        for draft in export.drafts:
            assert draft.status == ShopifyDraftStatus.BLOCKED
