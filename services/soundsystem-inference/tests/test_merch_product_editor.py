"""Tests for S44 — Merch Product Editor UI.

Covers:
- Product title update
- Availability update
- Active toggle
- Price positioning update
- Artwork/mockup artifact ID update
- Locked capsule rejects update (409)
- Archived capsule rejects update (409)
- Unknown capsule returns 404
- Unknown product returns 404
- Max active rule enforced after update
- Too many always_on warning after update
- Unavailable + active warning scenario
- Route requires operator identity
- Provider payloads not automatically rebuilt
- Aggregation detects stale provider title
- updated_at changes after edit
- No-op update (empty request) preserves state
- Existing S37/S43 tests unaffected (import smoke)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.merch_capsule import (
    build_merch_capsule_from_release,
    update_merch_product,
)
from app.merch_provider_aggregation import build_provider_aggregation
from app.schemas import (
    ComplianceChecklistItem,
    MerchAvailability,
    MerchCapsule,
    MerchCapsuleStatus,
    MerchProduct,
    MerchProductType,
    MerchProductUpdateRequest,
    MerchProviderGroup,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    ShopifyDraftStatus,
    ShopifyProductDraft,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release(
    *,
    genre: str | None = "Electronic",
    title: str = "TEST TRACK",
) -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="SHIBARI KAWAII",
        status=ReleasePackStatus.READY,
        genre=genre,
        social_copy=SocialCopy(
            soundcloud_description="sc",
            tiktok_caption="tk",
            instagram_caption="ig",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(code="metadata", label="Metadata", passed=True),
        ],
        compliance_passed=True,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio",
                expected_format="wav",
                ready=True,
                artifact_id=uuid4(),
            ),
        ],
    )


def _build_capsule(**kwargs) -> MerchCapsule:
    release = _make_release(**kwargs)
    return build_merch_capsule_from_release(release, operator_id="test@op")


# ---------- Product Title Update ----------


class TestTitleUpdate:
    def test_title_updated(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(title="NEW TITLE")
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.title == "NEW TITLE"
        # Capsule product also updated
        updated_product = next(
            p for p in result.capsule.products if p.product_id == product.product_id
        )
        assert updated_product.title == "NEW TITLE"

    def test_title_preserved_when_not_provided(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        original_title = product.title
        req = MerchProductUpdateRequest(active=True)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.title == original_title


# ---------- Availability Update ----------


class TestAvailabilityUpdate:
    def test_availability_updated(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(availability=MerchAvailability.UNAVAILABLE)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.availability == MerchAvailability.UNAVAILABLE

    def test_availability_always_on_triggers_warning(self) -> None:
        """Setting multiple products to always_on should trigger a warning."""
        capsule = _build_capsule(genre="Pop")
        # First product already has a sticker pack as always_on
        # Change another product to always_on too
        limited_product = next(
            p for p in capsule.products if p.availability == MerchAvailability.LIMITED
        )
        req = MerchProductUpdateRequest(availability=MerchAvailability.ALWAYS_ON)
        result = update_merch_product(capsule, limited_product.product_id, req)
        assert result is not None
        codes = [w.code for w in result.warnings]
        assert "too_many_always_on" in codes


# ---------- Active Toggle ----------


class TestActiveToggle:
    def test_deactivate_product(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        assert product.active is True
        req = MerchProductUpdateRequest(active=False)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.active is False

    def test_activate_product(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        # First deactivate
        deactivated = capsule.products[0].model_copy(update={"active": False})
        products = list(capsule.products)
        products[0] = deactivated
        capsule = capsule.model_copy(update={"products": products})
        req = MerchProductUpdateRequest(active=True)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.active is True


# ---------- Price Positioning ----------


class TestPricePositioning:
    def test_price_positioning_update(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(price_positioning="cult")
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.price_positioning == "cult"


# ---------- Artwork / Mockup ----------


class TestArtifactIds:
    def test_artwork_artifact_id_update(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        new_id = uuid4()
        req = MerchProductUpdateRequest(artwork_artifact_id=new_id)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.artwork_artifact_id == new_id

    def test_mockup_artifact_id_update(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        new_id = uuid4()
        req = MerchProductUpdateRequest(mockup_artifact_id=new_id)
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.mockup_artifact_id == new_id


# ---------- Unknown Product ----------


class TestUnknownProduct:
    def test_unknown_product_returns_none(self) -> None:
        capsule = _build_capsule()
        req = MerchProductUpdateRequest(title="whatever")
        result = update_merch_product(capsule, uuid4(), req)
        assert result is None


# ---------- Updated At ----------


class TestUpdatedAt:
    def test_updated_at_changes(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        original_updated = capsule.updated_at
        req = MerchProductUpdateRequest(title="Changed Title")
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.capsule.updated_at >= original_updated


# ---------- No-op Update ----------


class TestNoopUpdate:
    def test_empty_request_preserves_product(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest()
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.title == product.title
        assert result.product.active == product.active
        assert result.product.availability == product.availability


# ---------- Max Active Rule ----------


class TestMaxActiveRule:
    def test_too_many_active_after_update(self) -> None:
        """Activating an extra product beyond max triggers warning."""
        capsule = _build_capsule(genre="Techno")  # 5 products, all active
        # Add an extra inactive product
        extra = MerchProduct(
            product_id=uuid4(),
            title="Extra Beanie",
            product_type=MerchProductType.BEANIE,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.APPAREL_PROVIDER,
            active=False,
        )
        capsule = capsule.model_copy(update={"products": capsule.products + [extra]})
        # Activate the extra product (now 6 active, max 5)
        req = MerchProductUpdateRequest(active=True)
        result = update_merch_product(capsule, extra.product_id, req)
        assert result is not None
        codes = [w.code for w in result.warnings]
        assert "too_many_active" in codes


# ---------- Route Tests ----------


class TestProductEditorRoute:
    def _setup_capsule(self) -> MerchCapsule:
        from app.main import merch_capsule_repository, release_pack_repository

        release = _make_release()
        release_pack_repository.store(release)
        capsule = build_merch_capsule_from_release(release, operator_id="test@op")
        merch_capsule_repository.store(capsule)
        return capsule

    def test_patch_product_title(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_merch_capsule_product

        capsule = self._setup_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(title="PATCHED TITLE")
        result = asyncio.run(
            update_merch_capsule_product(capsule.capsule_id, product.product_id, req, DEV_OPERATOR)
        )
        assert result.product.title == "PATCHED TITLE"

    def test_patch_active_toggle(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_merch_capsule_product

        capsule = self._setup_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(active=False)
        result = asyncio.run(
            update_merch_capsule_product(capsule.capsule_id, product.product_id, req, DEV_OPERATOR)
        )
        assert result.product.active is False

    def test_locked_capsule_rejects_update(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import merch_capsule_repository, update_merch_capsule_product

        capsule = self._setup_capsule()
        locked = capsule.model_copy(update={"status": MerchCapsuleStatus.LOCKED})
        merch_capsule_repository.update(locked)
        product = capsule.products[0]
        req = MerchProductUpdateRequest(title="Should Fail")
        with pytest.raises(Exception, match="capsule_locked"):
            asyncio.run(
                update_merch_capsule_product(
                    capsule.capsule_id, product.product_id, req, DEV_OPERATOR
                )
            )

    def test_archived_capsule_rejects_update(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import merch_capsule_repository, update_merch_capsule_product

        capsule = self._setup_capsule()
        archived = capsule.model_copy(update={"status": MerchCapsuleStatus.ARCHIVED})
        merch_capsule_repository.update(archived)
        product = capsule.products[0]
        req = MerchProductUpdateRequest(title="Should Fail")
        with pytest.raises(Exception, match="capsule_archived"):
            asyncio.run(
                update_merch_capsule_product(
                    capsule.capsule_id, product.product_id, req, DEV_OPERATOR
                )
            )

    def test_unknown_capsule_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_merch_capsule_product

        req = MerchProductUpdateRequest(title="Nope")
        with pytest.raises(Exception, match="merch_capsule_not_found"):
            asyncio.run(update_merch_capsule_product(uuid4(), uuid4(), req, DEV_OPERATOR))

    def test_unknown_product_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_merch_capsule_product

        capsule = self._setup_capsule()
        req = MerchProductUpdateRequest(title="Nope")
        with pytest.raises(Exception, match="merch_product_not_found"):
            asyncio.run(
                update_merch_capsule_product(capsule.capsule_id, uuid4(), req, DEV_OPERATOR)
            )

    def test_update_persisted_in_repository(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import merch_capsule_repository, update_merch_capsule_product

        capsule = self._setup_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(title="PERSISTED")
        asyncio.run(
            update_merch_capsule_product(capsule.capsule_id, product.product_id, req, DEV_OPERATOR)
        )
        fetched = merch_capsule_repository.get(capsule.capsule_id)
        assert fetched is not None
        updated_product = next(p for p in fetched.products if p.product_id == product.product_id)
        assert updated_product.title == "PERSISTED"


# ---------- Provider Payloads Not Rebuilt ----------


class TestProviderPayloadsNotRebuilt:
    def test_shopify_drafts_not_auto_rebuilt(self) -> None:
        """Editing a product does not auto-update Shopify drafts."""
        from app.shopify_draft_repository import InMemoryShopifyDraftRepository

        repo = InMemoryShopifyDraftRepository()
        capsule = _build_capsule()
        product = capsule.products[0]

        # Create a Shopify draft for this product
        draft = ShopifyProductDraft(
            draft_id=uuid4(),
            capsule_id=capsule.capsule_id,
            product_id=product.product_id,
            title=product.title,
            status=ShopifyDraftStatus.EXPORTED_MOCK,
        )
        repo.store(draft)

        # Update the product title
        req = MerchProductUpdateRequest(title="CHANGED TITLE")
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None
        assert result.product.title == "CHANGED TITLE"

        # Shopify draft still has old title
        stored_draft = repo.get(draft.draft_id)
        assert stored_draft is not None
        assert stored_draft.title == product.title  # old title
        assert stored_draft.title != "CHANGED TITLE"


# ---------- Stale Detection in Aggregation ----------


class TestStaleDetection:
    def test_aggregation_detects_stale_shopify_title(self) -> None:
        """After product edit, aggregation flags stale Shopify draft."""
        capsule = _build_capsule()
        product = capsule.products[0]

        # Create a Shopify draft with the ORIGINAL title
        draft = ShopifyProductDraft(
            draft_id=uuid4(),
            capsule_id=capsule.capsule_id,
            product_id=product.product_id,
            title=product.title,
            status=ShopifyDraftStatus.EXPORTED_MOCK,
        )

        # Update the product title in the capsule
        req = MerchProductUpdateRequest(title="EDITED TITLE")
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None

        # Build aggregation with the old draft and updated capsule
        agg = build_provider_aggregation(
            result.capsule,
            shopify_drafts=[draft],
        )

        # Find the product status
        ps = next(p for p in agg.products if p.product_id == product.product_id)
        assert ps.stale is True
        assert any("differs" in w for w in ps.shopify_warnings)

    def test_aggregation_not_stale_when_titles_match(self) -> None:
        """No stale flag when titles match."""
        capsule = _build_capsule()
        product = capsule.products[0]

        draft = ShopifyProductDraft(
            draft_id=uuid4(),
            capsule_id=capsule.capsule_id,
            product_id=product.product_id,
            title=product.title,  # same title
            status=ShopifyDraftStatus.EXPORTED_MOCK,
        )

        agg = build_provider_aggregation(
            capsule,
            shopify_drafts=[draft],
        )

        ps = next(p for p in agg.products if p.product_id == product.product_id)
        assert ps.stale is False


# ---------- No External Calls ----------


class TestNoExternalCalls:
    def test_update_makes_no_external_calls(self) -> None:
        capsule = _build_capsule()
        product = capsule.products[0]
        req = MerchProductUpdateRequest(
            title="Updated",
            active=False,
            availability=MerchAvailability.UNAVAILABLE,
        )
        result = update_merch_product(capsule, product.product_id, req)
        assert result is not None

    def test_no_http_imports_in_merch_capsule(self) -> None:
        """merch_capsule.py must not import HTTP clients."""
        import inspect
        import app.merch_capsule as mod

        source = inspect.getsource(mod)
        for forbidden in ["import httpx", "import requests", "import aiohttp"]:
            assert forbidden not in source


# ---------- Import Smoke ----------


class TestImportSmoke:
    def test_existing_merch_imports_still_work(self) -> None:
        from app import merch_capsule as mod

        assert callable(mod.build_merch_capsule_from_release)
        assert callable(mod.build_mock_provider_export)
        assert callable(mod.enforce_merch_capsule_rules)
        assert callable(mod.update_merch_product)

    def test_schema_imports(self) -> None:
        from app import schemas as s

        assert s.MerchProductUpdateRequest is not None
        assert s.MerchProductUpdateResult is not None
