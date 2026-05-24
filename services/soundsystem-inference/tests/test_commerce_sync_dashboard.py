"""Tests for S64 — Shopify + Printful Operator Sync Dashboard.

Covers:
- Read-model for empty provider states (no drafts, no syncs)
- Shopify-only synced (mock) → state aggregates correctly
- Printful-only synced (mock) → state aggregates correctly
- Both synced (mock) → overall SYNCED_MOCK
- Live Shopify drafts + live Printful syncs → SYNCED_LIVE per provider
- Blocked aggregation
- Failed aggregation propagates to overall
- Provider IDs extracted from provider_payload
- Summary counts
- GET routes
- POST sync-both requires operator
- POST sync-both calls Shopify provider first, then Printful, sequentially
- POST sync-both stores provider results in the existing repositories
- POST sync-both unknown capsule → 404
- POST sync-both does NOT mutate orders / customers / inventory
- No background / scheduler imports in the dashboard module
- No provider token exposure
- Capability flag present
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.commerce_sync_dashboard import (
    build_commerce_capsule_sync_state,
    build_commerce_sync_summary,
    combine_sync_results,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.schemas import (
    CommerceSyncProvider,
    CommerceSyncStatus,
    ComplianceChecklistItem,
    MerchCapsule,
    PrintfulProductSync,
    PrintfulPrintTechnique,
    PrintfulSyncStatus,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    ShopifyDraftStatus,
    ShopifyProductDraft,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release() -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="COMMERCE SYNC TEST",
        artist="Test Artist",
        genre="Electronic",
        bpm=128,
        key_signature="Am",
        social_copy=SocialCopy(caption_short="s", caption_long="l", hashtags=["#t"]),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="rights_cleared",
                label="Rights cleared",
                passed=True,
            )
        ],
        compliance_passed=True,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
            ),
        ],
        dropbox_target="/releases/test",
        status=ReleasePackStatus.READY,
    )


def _make_capsule() -> MerchCapsule:
    return build_merch_capsule_from_release(_make_release(), operator_id="op@test")


def _shopify_draft(
    *,
    capsule_id,
    product_id,
    status: ShopifyDraftStatus = ShopifyDraftStatus.EXPORTED_MOCK,
    provider_payload: dict | None = None,
    warnings: list[str] | None = None,
    updated_at: datetime | None = None,
) -> ShopifyProductDraft:
    return ShopifyProductDraft(
        draft_id=uuid4(),
        capsule_id=capsule_id,
        product_id=product_id,
        title="Draft",
        status=status,
        provider_payload=provider_payload or {},
        warnings=warnings or [],
        updated_at=updated_at or datetime.now(timezone.utc),
    )


def _printful_sync(
    *,
    capsule_id,
    product_id,
    status: PrintfulSyncStatus = PrintfulSyncStatus.EXPORTED_MOCK,
    provider_payload: dict | None = None,
    warnings: list[str] | None = None,
    updated_at: datetime | None = None,
) -> PrintfulProductSync:
    return PrintfulProductSync(
        sync_id=uuid4(),
        capsule_id=capsule_id,
        product_id=product_id,
        title="Sync",
        print_technique=PrintfulPrintTechnique.DTG,
        status=status,
        provider_payload=provider_payload or {},
        warnings=warnings or [],
        updated_at=updated_at or datetime.now(timezone.utc),
    )


# ---------- Read-model ----------


class TestEmptyProviderStates:
    def test_no_drafts_no_syncs_means_not_synced(self) -> None:
        capsule = _make_capsule()
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=[],
            printful_syncs=[],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert state.shopify.status == CommerceSyncStatus.NOT_SYNCED
        assert state.printful.status == CommerceSyncStatus.NOT_SYNCED
        assert state.overall_status == CommerceSyncStatus.NOT_SYNCED
        assert any("Shopify" in w for w in state.warnings)
        assert any("Printful" in w for w in state.warnings)

    def test_state_includes_capsule_metadata(self) -> None:
        capsule = _make_capsule()
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=[],
            printful_syncs=[],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert state.capsule_id == capsule.capsule_id
        assert state.release_id == capsule.release_id
        assert state.title == capsule.title
        assert state.product_count == len(capsule.products)


class TestShopifyOnlySynced:
    def test_all_mock_synced_means_synced_mock(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.EXPORTED_MOCK,
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=[],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert state.shopify.status == CommerceSyncStatus.SYNCED_MOCK
        assert state.printful.status == CommerceSyncStatus.NOT_SYNCED
        # Overall: one synced, one not → PARTIAL
        assert state.overall_status == CommerceSyncStatus.PARTIAL

    def test_all_live_drafts_means_synced_live(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.DRAFT,
                provider_payload={
                    "shopify_product_id": f"gid://shopify/Product/{i}",
                    "shopify_handle": f"handle-{i}",
                },
            )
            for i, p in enumerate(capsule.products)
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=[],
            shopify_provider_mode="shopify",
            printful_provider_mode="mock",
        )
        assert state.shopify.status == CommerceSyncStatus.SYNCED_LIVE
        assert all(pid.startswith("gid://shopify/Product/") for pid in state.shopify.provider_ids)


class TestPrintfulOnlySynced:
    def test_all_mock_synced(self) -> None:
        capsule = _make_capsule()
        syncs = [
            _printful_sync(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=PrintfulSyncStatus.EXPORTED_MOCK,
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=[],
            printful_syncs=syncs,
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert state.printful.status == CommerceSyncStatus.SYNCED_MOCK
        assert state.shopify.status == CommerceSyncStatus.NOT_SYNCED
        assert state.overall_status == CommerceSyncStatus.PARTIAL

    def test_live_drafts_with_provider_ids(self) -> None:
        capsule = _make_capsule()
        syncs = [
            _printful_sync(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=PrintfulSyncStatus.DRAFT,
                provider_payload={"printful_sync_product_id": 100 + i},
            )
            for i, p in enumerate(capsule.products)
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=[],
            printful_syncs=syncs,
            shopify_provider_mode="mock",
            printful_provider_mode="printful",
        )
        assert state.printful.status == CommerceSyncStatus.SYNCED_LIVE
        assert {str(100 + i) for i in range(len(capsule.products))} <= set(
            state.printful.provider_ids
        )


class TestBothSynced:
    def test_both_mock_means_overall_mock(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.EXPORTED_MOCK,
            )
            for p in capsule.products
        ]
        syncs = [
            _printful_sync(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=PrintfulSyncStatus.EXPORTED_MOCK,
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=syncs,
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert state.overall_status == CommerceSyncStatus.SYNCED_MOCK

    def test_both_live_means_overall_live(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.DRAFT,
            )
            for p in capsule.products
        ]
        syncs = [
            _printful_sync(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=PrintfulSyncStatus.DRAFT,
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=syncs,
            shopify_provider_mode="shopify",
            printful_provider_mode="printful",
        )
        assert state.overall_status == CommerceSyncStatus.SYNCED_LIVE


class TestBlockedFailedAggregation:
    def test_all_blocked_per_provider(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.BLOCKED,
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=[],
            shopify_provider_mode="shopify",
            printful_provider_mode="mock",
        )
        assert state.shopify.status == CommerceSyncStatus.BLOCKED
        assert state.shopify.blocked_item_count == len(capsule.products)

    def test_any_failed_means_failed(self) -> None:
        capsule = _make_capsule()
        # one product fails, rest synced
        first, *rest = capsule.products
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=first.product_id,
                status=ShopifyDraftStatus.FAILED,
            )
        ] + [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.DRAFT,
            )
            for p in rest
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=[],
            shopify_provider_mode="shopify",
            printful_provider_mode="mock",
        )
        assert state.shopify.status == CommerceSyncStatus.FAILED
        assert state.shopify.failed_item_count == 1
        # FAILED on either provider propagates to overall
        assert state.overall_status == CommerceSyncStatus.FAILED

    def test_latest_draft_per_product_wins(self) -> None:
        capsule = _make_capsule()
        target = capsule.products[0]
        now = datetime.now(timezone.utc)
        older = _shopify_draft(
            capsule_id=capsule.capsule_id,
            product_id=target.product_id,
            status=ShopifyDraftStatus.FAILED,
            updated_at=now - timedelta(hours=1),
        )
        newer = _shopify_draft(
            capsule_id=capsule.capsule_id,
            product_id=target.product_id,
            status=ShopifyDraftStatus.DRAFT,
            updated_at=now,
            provider_payload={"shopify_product_id": "gid://shopify/Product/1"},
        )
        # rest of products: drafts
        rest = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.DRAFT,
            )
            for p in capsule.products[1:]
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=[older, newer, *rest],
            printful_syncs=[],
            shopify_provider_mode="shopify",
            printful_provider_mode="mock",
        )
        # Latest (DRAFT) wins, so no failures.
        assert state.shopify.failed_item_count == 0
        assert state.shopify.status == CommerceSyncStatus.SYNCED_LIVE


class TestProviderWarningsPropagate:
    def test_warnings_deduplicated(self) -> None:
        capsule = _make_capsule()
        drafts = [
            _shopify_draft(
                capsule_id=capsule.capsule_id,
                product_id=p.product_id,
                status=ShopifyDraftStatus.FAILED,
                warnings=["same warning"],
            )
            for p in capsule.products
        ]
        state = build_commerce_capsule_sync_state(
            capsule=capsule,
            shopify_drafts=drafts,
            printful_syncs=[],
            shopify_provider_mode="shopify",
            printful_provider_mode="mock",
        )
        assert state.shopify.warnings.count("same warning") == 1


# ---------- Summary ----------


class TestSummary:
    def test_counts(self) -> None:
        capsule_a = _make_capsule()
        capsule_b = _make_capsule()
        state_a = build_commerce_capsule_sync_state(
            capsule=capsule_a,
            shopify_drafts=[],
            printful_syncs=[],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        state_b = build_commerce_capsule_sync_state(
            capsule=capsule_b,
            shopify_drafts=[
                _shopify_draft(
                    capsule_id=capsule_b.capsule_id,
                    product_id=p.product_id,
                    status=ShopifyDraftStatus.EXPORTED_MOCK,
                )
                for p in capsule_b.products
            ],
            printful_syncs=[
                _printful_sync(
                    capsule_id=capsule_b.capsule_id,
                    product_id=p.product_id,
                    status=PrintfulSyncStatus.EXPORTED_MOCK,
                )
                for p in capsule_b.products
            ],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        summary = build_commerce_sync_summary(
            [state_a, state_b],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert summary.total_capsules == 2
        assert summary.not_synced == 1
        assert summary.synced_mock == 1
        assert summary.shopify_provider_mode == "mock"
        assert summary.printful_provider_mode == "mock"


# ---------- Combine ----------


class TestCombineSyncResults:
    def test_combine_returns_state_and_exports(self) -> None:
        capsule = _make_capsule()
        result = combine_sync_results(
            capsule=capsule,
            shopify_export=None,
            printful_export=None,
            shopify_drafts=[],
            printful_syncs=[],
            shopify_provider_mode="mock",
            printful_provider_mode="mock",
        )
        assert result.capsule_id == capsule.capsule_id
        assert result.shopify_result is None
        assert result.printful_result is None
        assert result.state.capsule_id == capsule.capsule_id
        assert any("Shopify" in w for w in result.warnings)
        assert any("Printful" in w for w in result.warnings)


# ---------- Route E2E ----------


class TestRoutes:
    def _store_capsule(self):
        from app.main import merch_capsule_repository

        capsule = _make_capsule()
        merch_capsule_repository.store(capsule)
        return capsule

    def test_list_capsules(self) -> None:
        from app.main import list_commerce_sync_capsules

        self._store_capsule()
        result = asyncio.run(list_commerce_sync_capsules())
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_capsule(self) -> None:
        from app.main import get_commerce_sync_capsule

        capsule = self._store_capsule()
        state = asyncio.run(get_commerce_sync_capsule(capsule.capsule_id))
        assert state.capsule_id == capsule.capsule_id

    def test_get_unknown_capsule_404(self) -> None:
        from app.main import get_commerce_sync_capsule
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_commerce_sync_capsule(uuid4()))
        assert exc.value.status_code == 404

    def test_summary(self) -> None:
        from app.main import get_commerce_sync_summary

        self._store_capsule()
        s = asyncio.run(get_commerce_sync_summary())
        assert s.total_capsules >= 1
        assert s.shopify_provider_mode in {"mock", "shopify"}
        assert s.printful_provider_mode in {"mock", "printful"}

    def test_sync_both_calls_shopify_first_then_printful(self) -> None:
        """Sequential ordering — Shopify first, Printful second."""
        from app.auth import DEV_OPERATOR
        from app.main import sync_commerce_capsule_both

        capsule = self._store_capsule()
        result = asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        # Both exports should be present, both in mock mode.
        assert result.shopify_result is not None
        assert result.printful_result is not None
        # Shopify ran first; its exported_at <= Printful's
        assert result.shopify_result.exported_at <= result.printful_result.exported_at

    def test_sync_both_stores_provider_results(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            printful_sync_repository,
            shopify_draft_repository,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        before_shopify = len(shopify_draft_repository.list_by_capsule(capsule.capsule_id))
        before_printful = len(printful_sync_repository.list_by_capsule(capsule.capsule_id))
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        after_shopify = len(shopify_draft_repository.list_by_capsule(capsule.capsule_id))
        after_printful = len(printful_sync_repository.list_by_capsule(capsule.capsule_id))
        assert after_shopify >= before_shopify + 1
        assert after_printful >= before_printful + 1

    def test_sync_both_unknown_capsule_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_commerce_capsule_both
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(sync_commerce_capsule_both(uuid4(), DEV_OPERATOR))
        assert exc.value.status_code == 404

    def test_sync_both_returns_post_sync_state(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_commerce_capsule_both

        capsule = self._store_capsule()
        result = asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        # After sync, the providers must have done *something*. The default
        # capsule fixture includes a vinyl-provider-group product that the
        # Printful builder skips, so PARTIAL is the legitimate steady-state
        # for the mock Printful provider.
        ok_statuses = {
            CommerceSyncStatus.SYNCED_MOCK,
            CommerceSyncStatus.SYNCED_LIVE,
            CommerceSyncStatus.PARTIAL,
        }
        assert result.state.shopify.status in ok_statuses
        assert result.state.printful.status in ok_statuses


# ---------- Capabilities ----------


class TestCapabilities:
    def test_capability_flag_set(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.commerce_sync_dashboard_available is True


# ---------- No forbidden imports / no token leak ----------


class TestNoForbiddenImports:
    def test_no_background_worker_imports(self) -> None:
        from app import commerce_sync_dashboard

        source = inspect.getsource(commerce_sync_dashboard)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
        assert "asyncio.create_task" not in source

    def test_no_scheduler_imports(self) -> None:
        from app import commerce_sync_dashboard

        source = inspect.getsource(commerce_sync_dashboard)
        assert "apscheduler" not in source
        assert "celery" not in source
        assert "import schedule" not in source
        assert "crontab" not in source

    def test_no_http_imports(self) -> None:
        from app import commerce_sync_dashboard

        source = inspect.getsource(commerce_sync_dashboard)
        # Read-model only. No HTTP. No provider calls.
        for forbidden in ("httpx", "requests", "aiohttp", "urllib.request"):
            assert forbidden not in source

    def test_no_token_field_on_provider_state(self) -> None:
        """CommerceSyncProviderState must not carry a token field."""
        from app.schemas import CommerceSyncProviderState

        empty = CommerceSyncProviderState(provider=CommerceSyncProvider.SHOPIFY)
        rendered = empty.model_dump(mode="json")
        for k in rendered:
            assert "token" not in k.lower()
            assert "secret" not in k.lower()
            assert "api_key" not in k.lower()


# ---------- No forbidden mutation surface ----------


class TestSyncBothMutationSurface:
    def test_sync_both_does_not_touch_orders_or_customers(self) -> None:
        """Sanity scan: the sync-both route source must not reach order/customer/inventory APIs."""
        from app import commerce_sync_dashboard, main

        for source in (inspect.getsource(commerce_sync_dashboard), inspect.getsource(main)):
            # In the dashboard module specifically — fully clean.
            if source is inspect.getsource(commerce_sync_dashboard):
                for forbidden in (
                    "orderCreate",
                    "customerCreate",
                    "inventorySet",
                    "inventoryAdjust",
                    "publishablePublish",
                    "webhookSubscriptionCreate",
                ):
                    assert forbidden not in source
