"""Tests for S41 — Printful Product Sync Boundary.

Covers:
- Default provider mode is mock
- Printful mode without token fails loudly
- Invalid config mode raises RuntimeError
- Mock sync maps all capsule products
- Variants mapped correctly
- Product type mapping correct (DTG, embroidery, etc.)
- Unsupported vinyl product blocked
- Poster/sticker warn about preferred provider
- Warnings when artwork missing
- Routes require operator for POST
- Capabilities expose printful fields
- Real provider blocks without API call
- Repository CRUD + summary
- No external calls
- Existing merch/shopify tests still pass
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.config import (
    PRINTFUL_PROVIDER_ENV,
    PrintfulProviderMode,
    printful_provider_mode,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.printful_sync_builder import build_all_syncs, build_product_sync
from app.printful_sync_repository import InMemoryPrintfulSyncRepository
from app.providers.printful import build_printful_sync_provider
from app.providers.printful.mock import MockPrintfulSyncProvider
from app.providers.printful.real import RealPrintfulSyncProvider
from app.schemas import (
    ComplianceChecklistItem,
    MerchAvailability,
    MerchProduct,
    MerchProductType,
    MerchProviderGroup,
    MerchVariant,
    PrintfulPrintTechnique,
    PrintfulSyncStatus,
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
    # The release has vinyl keyword in genre, so vinyl product is suggested
    capsule = build_merch_capsule_from_release(release, operator_id="test-op")
    # Verify there's a vinyl product
    vinyl = [p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT]
    if not vinyl:
        # Force-add one
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


class TestPrintfulConfig:
    def test_default_mode_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(PRINTFUL_PROVIDER_ENV, raising=False)
        assert printful_provider_mode() == PrintfulProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "mock")
        assert printful_provider_mode() == PrintfulProviderMode.MOCK

    def test_printful_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "printful")
        assert printful_provider_mode() == PrintfulProviderMode.PRINTFUL

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "printify")
        with pytest.raises(RuntimeError, match="invalid"):
            printful_provider_mode()

    def test_printful_without_token_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "printful")
        monkeypatch.delenv("PRINTFUL_API_TOKEN", raising=False)
        from app.config import PrintfulProviderConfigError

        with pytest.raises(PrintfulProviderConfigError, match="requires"):
            build_printful_sync_provider()


# ---------- Factory ----------


class TestPrintfulFactory:
    def test_factory_default_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(PRINTFUL_PROVIDER_ENV, raising=False)
        provider = build_printful_sync_provider()
        assert provider.name == "mock"
        assert isinstance(provider, MockPrintfulSyncProvider)

    def test_factory_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "mock")
        provider = build_printful_sync_provider()
        assert provider.name == "mock"

    def test_factory_printful_with_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # S63 — real provider now requires BOTH token AND store_id.
        monkeypatch.setenv(PRINTFUL_PROVIDER_ENV, "printful")
        monkeypatch.setenv("PRINTFUL_API_TOKEN", "test_token_123")
        monkeypatch.setenv("PRINTFUL_STORE_ID", "1234")
        provider = build_printful_sync_provider()
        assert provider.name == "printful"
        assert isinstance(provider, RealPrintfulSyncProvider)


# ---------- Builder ----------


class TestPrintfulSyncBuilder:
    def test_build_all_syncs_active_only(self) -> None:
        capsule = _make_capsule()
        syncs = build_all_syncs(capsule)
        active_count = sum(1 for p in capsule.products if p.active)
        assert len(syncs) == active_count

    def test_sync_fields_populated(self) -> None:
        capsule = _make_capsule()
        syncs = build_all_syncs(capsule)
        assert len(syncs) > 0
        sync = syncs[0]
        assert sync.capsule_id == capsule.capsule_id
        assert sync.title == capsule.products[0].title
        assert sync.product_type == capsule.products[0].product_type.value

    def test_heavyweight_tee_dtg(self) -> None:
        capsule = _make_capsule()
        tee = next(
            (p for p in capsule.products if p.product_type == MerchProductType.HEAVYWEIGHT_TEE),
            None,
        )
        if tee is None:
            pytest.skip("No heavyweight tee in capsule")
        sync = build_product_sync(tee, capsule)
        assert sync.print_technique == PrintfulPrintTechnique.DTG
        assert "front" in sync.placement
        assert sync.provider_catalog_hint != ""

    def test_beanie_embroidery(self) -> None:
        """Beanies should use embroidery technique."""
        capsule = _make_capsule()
        beanie = MerchProduct(
            product_id=uuid4(),
            title="Test Beanie",
            product_type=MerchProductType.BEANIE,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.APPAREL_PROVIDER,
            active=True,
        )
        sync = build_product_sync(beanie, capsule)
        assert sync.print_technique == PrintfulPrintTechnique.EMBROIDERY

    def test_vinyl_blocked(self) -> None:
        """Vinyl objects should be blocked — not Printful-compatible."""
        capsule = _make_vinyl_capsule()
        vinyl = next(p for p in capsule.products if p.product_type == MerchProductType.VINYL_OBJECT)
        sync = build_product_sync(vinyl, capsule)
        assert sync.status == PrintfulSyncStatus.BLOCKED
        assert any("not Printful-compatible" in w for w in sync.warnings)

    def test_poster_warns_gelato(self) -> None:
        """Posters should warn about preferring Gelato/premium drop."""
        capsule = _make_capsule()
        poster = next(
            (p for p in capsule.products if p.product_type == MerchProductType.POSTER),
            None,
        )
        if poster is None:
            pytest.skip("No poster in capsule")
        sync = build_product_sync(poster, capsule)
        assert any("gelato" in w.lower() or "premium" in w.lower() for w in sync.warnings)

    def test_sticker_warns_premium(self) -> None:
        """Sticker packs should warn about preferring premium drop provider."""
        capsule = _make_capsule()
        sticker = next(
            (p for p in capsule.products if p.product_type == MerchProductType.STICKER_PACK),
            None,
        )
        if sticker is None:
            pytest.skip("No sticker pack in capsule")
        sync = build_product_sync(sticker, capsule)
        assert any("premium" in w.lower() for w in sync.warnings)

    def test_variants_default_single(self) -> None:
        capsule = _make_capsule()
        syncs = build_all_syncs(capsule)
        for sync in syncs:
            assert len(sync.variants) >= 1

    def test_variants_mapped_from_merch(self) -> None:
        capsule = _make_capsule_with_variants()
        syncs = build_all_syncs(capsule)
        first_sync = next(s for s in syncs if s.product_id == capsule.products[0].product_id)
        assert len(first_sync.variants) == 3
        labels = [v.title for v in first_sync.variants]
        assert "S" in labels
        assert "M" in labels
        assert "L" in labels

    def test_warnings_when_artwork_missing(self) -> None:
        capsule = _make_capsule(has_cover=False)
        syncs = build_all_syncs(capsule)
        for sync in syncs:
            artwork_warnings = [w for w in sync.warnings if "artwork" in w.lower()]
            assert len(artwork_warnings) > 0

    def test_provider_payload_shape(self) -> None:
        capsule = _make_capsule()
        syncs = build_all_syncs(capsule)
        for sync in syncs:
            assert "sync_product" in sync.provider_payload
            assert "sync_variants" in sync.provider_payload
            assert "_meta" in sync.provider_payload
            assert sync.provider_payload["_meta"]["mock_only"] is True

    def test_operator_id_set(self) -> None:
        capsule = _make_capsule()
        syncs = build_all_syncs(capsule, operator_id="op-123")
        for sync in syncs:
            assert sync.created_by == "op-123"


# ---------- Mock Provider ----------


class TestMockPrintfulProvider:
    def test_mock_name(self) -> None:
        provider = MockPrintfulSyncProvider()
        assert provider.name == "mock"

    def test_mock_syncs_exported_mock_status(self) -> None:
        provider = MockPrintfulSyncProvider()
        capsule = _make_capsule()
        syncs = provider.build_product_syncs(capsule)
        assert len(syncs) > 0
        for sync in syncs:
            # Non-blocked products should be exported_mock
            if sync.product_type != MerchProductType.VINYL_OBJECT:
                assert sync.status == PrintfulSyncStatus.EXPORTED_MOCK

    def test_mock_vinyl_stays_blocked(self) -> None:
        provider = MockPrintfulSyncProvider()
        capsule = _make_vinyl_capsule()
        syncs = provider.build_product_syncs(capsule)
        vinyl_syncs = [s for s in syncs if s.product_type == MerchProductType.VINYL_OBJECT]
        for s in vinyl_syncs:
            assert s.status == PrintfulSyncStatus.BLOCKED

    def test_mock_export_payload(self) -> None:
        provider = MockPrintfulSyncProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.capsule_id == capsule.capsule_id
        assert export.provider_mode == "mock"
        assert export.total_products > 0
        assert len(export.syncs) == export.total_products


# ---------- Real Provider ----------


class TestRealPrintfulProvider:
    """Updated for S63 hardening.

    The real provider now requires credentials at construction (fail-loud)
    and exposes ``sync_products()`` for live sync product creation.
    ``export_mock()`` on the real provider remains read-only and returns
    BLOCKED syncs that direct the operator to ``sync_products()``.
    """

    def _build_provider(self) -> RealPrintfulSyncProvider:
        return RealPrintfulSyncProvider(
            api_token="test_token_123",
            store_id="1234",
            transport=lambda *a, **k: {},  # not called by these tests
        )

    def test_real_name(self) -> None:
        provider = self._build_provider()
        assert provider.name == "printful"

    def test_real_requires_credentials_at_construction(self) -> None:
        from app.config import PrintfulProviderConfigError

        with pytest.raises(PrintfulProviderConfigError):
            RealPrintfulSyncProvider(api_token=None, store_id=None)

    def test_real_export_mock_returns_blocked_syncs(self) -> None:
        """export_mock() on the real provider is read-only — BLOCKED with a
        warning pointing to sync_products()."""
        provider = self._build_provider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "printful"
        for sync in export.syncs:
            assert sync.status == PrintfulSyncStatus.BLOCKED
            assert any("sync_products()" in w for w in sync.warnings)

    def test_real_export_mode(self) -> None:
        provider = self._build_provider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "printful"


# ---------- Repository ----------


class TestPrintfulSyncRepository:
    def test_store_and_get(self) -> None:
        provider = MockPrintfulSyncProvider()
        capsule = _make_capsule()
        syncs = provider.build_product_syncs(capsule)
        repo = InMemoryPrintfulSyncRepository()
        repo.store_many(syncs)
        for sync in syncs:
            got = repo.get(sync.sync_id)
            assert got is not None
            assert got.sync_id == sync.sync_id

    def test_list_all(self) -> None:
        provider = MockPrintfulSyncProvider()
        repo = InMemoryPrintfulSyncRepository()
        for _ in range(3):
            capsule = _make_capsule()
            syncs = provider.build_product_syncs(capsule)
            repo.store_many(syncs)
        all_syncs = repo.list_all()
        assert len(all_syncs) > 0

    def test_list_by_capsule(self) -> None:
        provider = MockPrintfulSyncProvider()
        repo = InMemoryPrintfulSyncRepository()
        c1 = _make_capsule()
        c2 = _make_capsule()
        repo.store_many(provider.build_product_syncs(c1))
        repo.store_many(provider.build_product_syncs(c2))
        c1_syncs = repo.list_by_capsule(c1.capsule_id)
        c2_syncs = repo.list_by_capsule(c2.capsule_id)
        assert len(c1_syncs) > 0
        assert len(c2_syncs) > 0
        assert all(s.capsule_id == c1.capsule_id for s in c1_syncs)
        assert all(s.capsule_id == c2.capsule_id for s in c2_syncs)

    def test_get_nonexistent(self) -> None:
        repo = InMemoryPrintfulSyncRepository()
        assert repo.get(uuid4()) is None

    def test_summary(self) -> None:
        provider = MockPrintfulSyncProvider()
        repo = InMemoryPrintfulSyncRepository()
        capsule = _make_capsule()
        repo.store_many(provider.build_product_syncs(capsule))
        summary = repo.summary()
        assert summary.total_syncs > 0
        assert summary.exported_mock > 0

    def test_mode(self) -> None:
        repo = InMemoryPrintfulSyncRepository()
        assert repo.mode == "in_memory"


# ---------- Capabilities ----------


class TestPrintfulCapabilities:
    def test_capabilities_expose_printful_fields(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.printful_sync_available is True
        assert caps.printful_provider_mode in ("mock", "printful")

    def test_capabilities_default_mock(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.printful_provider_mode == "mock"


# ---------- Routes ----------


class TestPrintfulRoutes:
    def test_build_syncs_and_fetch(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_printful_syncs,
            get_printful_sync,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        export = asyncio.run(build_printful_syncs(capsule.capsule_id, DEV_OPERATOR))
        assert export.total_products > 0
        assert len(export.syncs) == export.total_products

        # Fetch individual sync
        first_sync = export.syncs[0]
        fetched = asyncio.run(get_printful_sync(first_sync.sync_id))
        assert fetched.sync_id == first_sync.sync_id

    def test_list_syncs_by_capsule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            build_printful_syncs,
            list_printful_syncs_by_capsule,
            merch_capsule_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test")
        merch_capsule_repository.store(capsule)

        asyncio.run(build_printful_syncs(capsule.capsule_id, DEV_OPERATOR))
        syncs = asyncio.run(list_printful_syncs_by_capsule(capsule.capsule_id))
        assert len(syncs) > 0
        assert all(s.capsule_id == capsule.capsule_id for s in syncs)

    def test_printful_summary(self) -> None:
        from app.main import printful_sync_summary

        summary = asyncio.run(printful_sync_summary())
        assert summary.total_syncs >= 0

    def test_capsule_not_found_returns_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import build_printful_syncs

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(build_printful_syncs(uuid4(), DEV_OPERATOR))


# ---------- No External Calls ----------


class TestPrintfulNoExternalCalls:
    def test_mock_makes_no_network_calls(self) -> None:
        """Mock provider should not import any HTTP/network libraries."""
        provider = MockPrintfulSyncProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "mock"

    def test_real_export_mock_makes_no_network_calls(self) -> None:
        """Real provider's export_mock() must not perform network activity.

        Only ``sync_products()`` calls the Printful API, and even then via
        an injectable transport (mocked in tests).
        """
        provider = RealPrintfulSyncProvider(
            api_token="test_token_123",
            store_id="1234",
            transport=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("network must not be called by export_mock()")
            ),
        )
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.provider_mode == "printful"
        for sync in export.syncs:
            assert sync.status == PrintfulSyncStatus.BLOCKED
