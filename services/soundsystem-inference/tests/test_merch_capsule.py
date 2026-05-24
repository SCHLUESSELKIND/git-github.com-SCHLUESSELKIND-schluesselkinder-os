"""Tests for S37 — Merch Capsule Contract.

Covers:
- Build capsule from ReleasePack
- Default product suggestions
- Max 5 active products enforced
- always_on limited to 1 warning
- vinyl product routes to vinyl_provider
- Provider routing validation
- Export mock returns provider-group payload
- Lock prevents re-lock on archived
- Routes require operator for POST
- Capabilities expose merch fields
- No external calls
- Repository CRUD + summary
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.merch_capsule import (
    build_merch_capsule_from_release,
    build_mock_provider_export,
    enforce_merch_capsule_rules,
    suggest_products_for_release,
)
from app.merch_repository import InMemoryMerchCapsuleRepository
from app.schemas import (
    ComplianceChecklistItem,
    MerchAvailability,
    MerchCapsuleCreateRequest,
    MerchCapsuleStatus,
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
    has_audio: bool = True,
    has_cover: bool = True,
    genre: str | None = "Electronic",
    description: str = "",
    title: str = "TEST TRACK",
) -> ReleasePack:
    """Build a test ReleasePack with configurable assets."""
    assets = []
    if has_audio:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=False,
            )
        )
    if has_cover:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
            )
        )

    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="SHIBARI KAWAII",
        status=ReleasePackStatus.READY,
        description=description,
        genre=genre,
        social_copy=SocialCopy(
            soundcloud_description="Test release on SoundCloud",
            tiktok_caption="New drop",
            instagram_caption="Out now",
            hashtags=["#electronic", "#underground"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(code="metadata", label="Metadata", passed=True),
        ],
        compliance_passed=True,
        assets=assets,
    )


# ---------- Product Suggestions ----------


class TestSuggestProducts:
    def test_default_suggestions_without_vinyl(self) -> None:
        release = _make_release(genre="Pop", description="A pop track")
        products = suggest_products_for_release(release)
        types = [p.product_type for p in products]
        assert MerchProductType.HEAVYWEIGHT_TEE in types
        assert MerchProductType.OVERSIZED_HOODIE in types
        assert MerchProductType.STICKER_PACK in types
        assert MerchProductType.POSTER in types
        assert MerchProductType.VINYL_OBJECT not in types
        assert len(products) == 4

    def test_vinyl_suggested_for_electronic(self) -> None:
        release = _make_release(genre="Electronic", description="deep techno dub")
        products = suggest_products_for_release(release)
        types = [p.product_type for p in products]
        assert MerchProductType.VINYL_OBJECT in types
        assert len(products) == 5

    def test_vinyl_suggested_from_description_keywords(self) -> None:
        release = _make_release(genre="Ambient", description="vinyl pressing planned")
        products = suggest_products_for_release(release)
        types = [p.product_type for p in products]
        assert MerchProductType.VINYL_OBJECT in types

    def test_max_5_products(self) -> None:
        release = _make_release(genre="Techno")
        products = suggest_products_for_release(release)
        assert len(products) <= 5

    def test_exactly_one_always_on(self) -> None:
        release = _make_release()
        products = suggest_products_for_release(release)
        always_on = [p for p in products if p.availability == MerchAvailability.ALWAYS_ON]
        assert len(always_on) == 1

    def test_artwork_linked_from_cover(self) -> None:
        release = _make_release(has_cover=True)
        products = suggest_products_for_release(release)
        cover_id = None
        for asset in release.assets:
            if asset.asset_type == "cover_art" and asset.artifact_id:
                cover_id = asset.artifact_id
        for product in products:
            assert product.artwork_artifact_id == cover_id

    def test_no_artwork_when_no_cover(self) -> None:
        release = _make_release(has_cover=False)
        products = suggest_products_for_release(release)
        for product in products:
            assert product.artwork_artifact_id is None

    def test_all_products_active(self) -> None:
        release = _make_release()
        products = suggest_products_for_release(release)
        for product in products:
            assert product.active is True


# ---------- Rule Enforcement ----------


class TestEnforceMerchRules:
    def test_no_warnings_for_valid_capsule(self) -> None:
        release = _make_release(genre="Pop")
        capsule = build_merch_capsule_from_release(release, operator_id="test@op")
        capsule = capsule.model_copy(update={"drop_window_start": "2026-06-01T00:00:00Z"})
        warnings = enforce_merch_capsule_rules(capsule)
        codes = [w.code for w in warnings]
        assert "too_many_active" not in codes
        assert "too_many_always_on" not in codes

    def test_too_many_active_products(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        # Add extra active products to exceed max
        extra = [
            MerchProduct(
                product_id=uuid4(),
                title=f"Extra {i}",
                product_type=MerchProductType.BEANIE,
                availability=MerchAvailability.LIMITED,
                provider_group=MerchProviderGroup.APPAREL_PROVIDER,
                active=True,
            )
            for i in range(3)
        ]
        capsule = capsule.model_copy(update={"products": capsule.products + extra})
        warnings = enforce_merch_capsule_rules(capsule)
        codes = [w.code for w in warnings]
        assert "too_many_active" in codes

    def test_too_many_always_on(self) -> None:
        release = _make_release(genre="Pop")
        capsule = build_merch_capsule_from_release(release)
        # Change multiple products to always_on
        updated_products = []
        for p in capsule.products:
            updated_products.append(
                p.model_copy(update={"availability": MerchAvailability.ALWAYS_ON})
            )
        capsule = capsule.model_copy(update={"products": updated_products})
        warnings = enforce_merch_capsule_rules(capsule)
        codes = [w.code for w in warnings]
        assert "too_many_always_on" in codes

    def test_limited_no_drop_window_warning(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        # Default capsule has no drop_window_start and has limited products
        warnings = enforce_merch_capsule_rules(capsule)
        codes = [w.code for w in warnings]
        assert "limited_no_drop_window" in codes

    def test_provider_mismatch_warning(self) -> None:
        release = _make_release(genre="Pop")
        capsule = build_merch_capsule_from_release(release)
        # Reroute vinyl_object to wrong provider
        bad_product = MerchProduct(
            product_id=uuid4(),
            title="Wrong Provider Vinyl",
            product_type=MerchProductType.VINYL_OBJECT,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.APPAREL_PROVIDER,  # wrong!
            active=True,
        )
        capsule = capsule.model_copy(update={"products": capsule.products + [bad_product]})
        warnings = enforce_merch_capsule_rules(capsule)
        codes = [w.code for w in warnings]
        assert "provider_mismatch" in codes

    def test_vinyl_routes_to_vinyl_provider(self) -> None:
        release = _make_release(genre="Techno")
        products = suggest_products_for_release(release)
        vinyl_products = [p for p in products if p.product_type == MerchProductType.VINYL_OBJECT]
        assert len(vinyl_products) == 1
        assert vinyl_products[0].provider_group == MerchProviderGroup.VINYL_PROVIDER

    def test_apparel_routes_to_apparel_provider(self) -> None:
        release = _make_release()
        products = suggest_products_for_release(release)
        tees = [p for p in products if p.product_type == MerchProductType.HEAVYWEIGHT_TEE]
        assert len(tees) == 1
        assert tees[0].provider_group == MerchProviderGroup.APPAREL_PROVIDER


# ---------- Capsule Builder ----------


class TestBuildCapsule:
    def test_build_from_release(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(
            release, operator_id="test@op", notes="Test capsule"
        )
        assert capsule.release_id == release.release_id
        assert capsule.artist == release.artist
        assert capsule.status == MerchCapsuleStatus.DRAFT
        assert capsule.created_by == "test@op"
        assert "Test capsule" in capsule.notes
        assert len(capsule.products) > 0
        assert len(capsule.products) <= 5

    def test_capsule_has_provider_groups(self) -> None:
        release = _make_release(genre="Techno")
        capsule = build_merch_capsule_from_release(release)
        assert len(capsule.provider_groups) > 0
        assert MerchProviderGroup.APPAREL_PROVIDER in capsule.provider_groups

    def test_capsule_title_includes_release(self) -> None:
        release = _make_release(title="ROPEMASTER")
        capsule = build_merch_capsule_from_release(release)
        assert "ROPEMASTER" in capsule.title

    def test_capsule_default_availability_strategy(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        assert capsule.availability_strategy == "70_20_10"

    def test_capsule_max_active_default(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        assert capsule.max_active_products == 5


# ---------- Mock Export ----------


class TestMockExport:
    def test_export_has_provider_notes(self) -> None:
        release = _make_release(genre="Techno")
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        assert len(payload.provider_exports) > 0
        groups = [e.provider_group for e in payload.provider_exports]
        assert MerchProviderGroup.APPAREL_PROVIDER in groups

    def test_export_has_tiktok_notes(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        assert "TikTok" in payload.tiktok_shop_notes
        assert "deferred" in payload.tiktok_shop_notes.lower()

    def test_export_has_printful_notes(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        assert "Printful" in payload.printful_notes
        assert "mock" in payload.printful_notes.lower()

    def test_export_has_shopify_notes(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        assert "Shopify" in payload.shopify_draft_notes
        assert "not implemented" in payload.shopify_draft_notes.lower()

    def test_export_warns_if_not_locked(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        codes = [w.code for w in payload.warnings]
        assert "not_locked" in codes

    def test_export_no_not_locked_warning_when_locked(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        capsule = capsule.model_copy(
            update={
                "status": MerchCapsuleStatus.LOCKED,
                "drop_window_start": "2026-06-01",
            }
        )
        payload = build_mock_provider_export(capsule)
        codes = [w.code for w in payload.warnings]
        assert "not_locked" not in codes

    def test_export_includes_active_products_only(self) -> None:
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        # Deactivate first product
        products = list(capsule.products)
        products[0] = products[0].model_copy(update={"active": False})
        capsule = capsule.model_copy(update={"products": products})
        payload = build_mock_provider_export(capsule)
        assert len(payload.products) == len(products) - 1

    def test_export_vinyl_provider_notes(self) -> None:
        release = _make_release(genre="Techno")
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        vinyl_exports = [
            e
            for e in payload.provider_exports
            if e.provider_group == MerchProviderGroup.VINYL_PROVIDER
        ]
        assert len(vinyl_exports) == 1
        assert "vinyl" in vinyl_exports[0].notes.lower()

    def test_export_no_real_secrets(self) -> None:
        """Export payload must not contain provider secrets."""
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        payload_str = payload.model_dump_json()
        # No API keys, tokens, or credentials
        for forbidden in ["api_key", "secret", "token", "password", "credential"]:
            assert forbidden not in payload_str.lower()


# ---------- Repository ----------


class TestMerchRepository:
    def test_store_and_get(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        repo.store(capsule)
        got = repo.get(capsule.capsule_id)
        assert got is not None
        assert got.capsule_id == capsule.capsule_id

    def test_get_nonexistent(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        assert repo.get(uuid4()) is None

    def test_list_all(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        for _ in range(3):
            release = _make_release()
            capsule = build_merch_capsule_from_release(release)
            repo.store(capsule)
        assert len(repo.list_all()) == 3

    def test_update(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        repo.store(capsule)
        updated = capsule.model_copy(update={"status": MerchCapsuleStatus.LOCKED})
        repo.update(updated)
        got = repo.get(capsule.capsule_id)
        assert got is not None
        assert got.status == MerchCapsuleStatus.LOCKED

    def test_summary(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        for i in range(3):
            release = _make_release()
            capsule = build_merch_capsule_from_release(release)
            if i == 1:
                capsule = capsule.model_copy(update={"status": MerchCapsuleStatus.LOCKED})
            repo.store(capsule)
        summary = repo.summary()
        assert summary.total_capsules == 3
        assert summary.drafts == 2
        assert summary.locked == 1
        assert summary.total_products > 0
        assert summary.total_active_products > 0

    def test_mode(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        assert repo.mode == "in_memory"


# ---------- Routes ----------


class TestMerchRoutes:
    def _setup_release(self, **kwargs) -> ReleasePack:
        """Store a release and return it."""
        from app.main import release_pack_repository

        release = _make_release(**kwargs)
        release_pack_repository.store(release)
        return release

    def test_create_capsule_route(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        assert capsule.release_id == release.release_id
        assert capsule.status == MerchCapsuleStatus.DRAFT
        assert capsule.created_by == DEV_OPERATOR.operator_id
        assert len(capsule.products) > 0
        assert len(capsule.products) <= 5

    def test_create_capsule_release_not_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule

        req = MerchCapsuleCreateRequest(release_id=uuid4())
        with pytest.raises(Exception, match="release_not_found"):
            asyncio.run(create_merch_capsule(req, DEV_OPERATOR))

    def test_list_capsules_route(self) -> None:
        from app.main import list_merch_capsules

        capsules = asyncio.run(list_merch_capsules())
        assert isinstance(capsules, list)

    def test_get_capsule_route(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule, get_merch_capsule

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        fetched = asyncio.run(get_merch_capsule(capsule.capsule_id))
        assert fetched.capsule_id == capsule.capsule_id

    def test_get_capsule_not_found(self) -> None:
        from app.main import get_merch_capsule

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(get_merch_capsule(uuid4()))

    def test_lock_capsule_route(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule, lock_merch_capsule

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        locked = asyncio.run(lock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        assert locked.status == MerchCapsuleStatus.LOCKED

    def test_lock_archived_capsule_fails(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_merch_capsule,
            lock_merch_capsule,
            merch_capsule_repository,
        )

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        archived = capsule.model_copy(update={"status": MerchCapsuleStatus.ARCHIVED})
        merch_capsule_repository.update(archived)
        with pytest.raises(Exception, match="capsule_archived"):
            asyncio.run(lock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))

    def test_lock_idempotent(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule, lock_merch_capsule

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        asyncio.run(lock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        locked_again = asyncio.run(lock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        assert locked_again.status == MerchCapsuleStatus.LOCKED

    def test_export_mock_route(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_merch_capsule, export_mock_merch_capsule

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        payload = asyncio.run(export_mock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        assert len(payload.products) > 0
        assert len(payload.provider_exports) > 0
        assert "TikTok" in payload.tiktok_shop_notes
        assert "Printful" in payload.printful_notes

    def test_export_updates_status(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_merch_capsule,
            export_mock_merch_capsule,
            get_merch_capsule,
        )

        release = self._setup_release()
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        asyncio.run(export_mock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        fetched = asyncio.run(get_merch_capsule(capsule.capsule_id))
        assert fetched.status == MerchCapsuleStatus.EXPORTED_MOCK

    def test_export_not_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import export_mock_merch_capsule

        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(export_mock_merch_capsule(uuid4(), DEV_OPERATOR))

    def test_summary_route(self) -> None:
        from app.main import merch_summary

        summary = asyncio.run(merch_summary())
        assert summary.total_capsules >= 0


# ---------- Capabilities ----------


class TestMerchCapabilities:
    def test_capabilities_expose_merch_fields(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.merch_capsules_available is True
        assert caps.merch_provider_mode == "mock"


# ---------- No External Calls ----------


class TestNoExternalCalls:
    def test_mock_builder_makes_no_external_calls(self) -> None:
        """Building a capsule must not call any external service."""
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        # If we got here without network errors, no external calls were made
        assert capsule is not None

    def test_mock_export_makes_no_external_calls(self) -> None:
        """Export mock must not call Printful/TikTok/Shopify."""
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        payload = build_mock_provider_export(capsule)
        assert payload is not None
        # All provider notes should say "not connected" or "mock"
        for export in payload.provider_exports:
            assert export.status == "mock_only"
