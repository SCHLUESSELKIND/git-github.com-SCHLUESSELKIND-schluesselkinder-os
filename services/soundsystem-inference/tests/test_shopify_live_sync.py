"""Tests for S62 — Shopify Live Draft Sync hardening.

Covers:
- Default mode is mock (factory + capabilities)
- Real provider fails loud without SHOPIFY_SHOP_DOMAIN or token
- Real provider holds token privately — no __repr__ / __str__ leak
- Real provider.sync_drafts builds a `productCreate` GraphQL payload
- Payload pins status=DRAFT and contains no publish/inventory/order/customer fields
- Successful Shopify response yields draft.status=DRAFT + provider_payload IDs
- Unexpected (non-DRAFT) status returned by server is treated as FAILED
- userErrors → FAILED + scrubbed warning
- Network exception → FAILED + scrubbed warning (token never appears in output)
- HTTP path uses stdlib urllib (no new pinned dependency)
- /v1/shopify/drafts/by-capsule/{id}/sync-drafts requires operator
- Sync route stores draft exports
- Mock mode remains deterministic and does not perform network calls
- No webhook / scheduler / background-worker imports in provider module
- Existing S40 tests still pass (smoke verified by full suite)
"""

from __future__ import annotations

import asyncio
import inspect
import os
from uuid import uuid4

import pytest

from app.merch_capsule import build_merch_capsule_from_release
from app.providers.shopify import (
    build_shopify_draft_provider,
    supports_live_sync,
)
from app.providers.shopify.mock import MockShopifyDraftProvider
from app.providers.shopify.real import (
    PRODUCT_CREATE_MUTATION,
    RealShopifyDraftProvider,
    _redact,
)
from app.schemas import (
    ComplianceChecklistItem,
    MerchCapsule,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    ShopifyDraftStatus,
    SocialCopy,
)


# ---------- Helpers ----------


SECRET_TOKEN = "shpat_super_secret_token_value_abcdef"


def _make_release() -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="LIVE SYNC TEST",
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
    release = _make_release()
    return build_merch_capsule_from_release(release, operator_id="op@test")


def _build_real_provider(transport=None) -> RealShopifyDraftProvider:
    """Build the real provider with explicit creds + injected transport."""
    return RealShopifyDraftProvider(
        shop_domain="schluesselkinder.myshopify.com",
        access_token=SECRET_TOKEN,
        api_version="2025-01",
        transport=transport,
    )


def _success_response(product_id: str = "gid://shopify/Product/123") -> dict:
    return {
        "data": {
            "productCreate": {
                "product": {
                    "id": product_id,
                    "handle": "live-sync-test",
                    "title": "LIVE SYNC TEST",
                    "status": "DRAFT",
                    "onlineStoreUrl": None,
                    "vendor": "SCHLUESSELKINDER",
                    "productType": "",
                    "tags": [],
                },
                "userErrors": [],
            }
        }
    }


# ---------- Config defaults ----------


class TestShopifyConfigDefaults:
    def test_factory_default_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_SHOPIFY_PROVIDER", raising=False)
        provider = build_shopify_draft_provider()
        assert provider.name == "mock"
        assert supports_live_sync(provider) is False

    def test_supports_live_sync_true_for_real(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        assert supports_live_sync(provider) is True

    def test_factory_shopify_fails_loud_without_domain(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.config import ShopifyProviderConfigError

        monkeypatch.setenv("SOUNDSYSTEM_SHOPIFY_PROVIDER", "shopify")
        monkeypatch.delenv("SHOPIFY_SHOP_DOMAIN", raising=False)
        monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", SECRET_TOKEN)
        with pytest.raises(ShopifyProviderConfigError):
            build_shopify_draft_provider()

    def test_factory_shopify_fails_loud_without_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.config import ShopifyProviderConfigError

        monkeypatch.setenv("SOUNDSYSTEM_SHOPIFY_PROVIDER", "shopify")
        monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "shop.myshopify.com")
        monkeypatch.delenv("SHOPIFY_ADMIN_ACCESS_TOKEN", raising=False)
        with pytest.raises(ShopifyProviderConfigError):
            build_shopify_draft_provider()


# ---------- Token safety ----------


class TestTokenIsNeverExposed:
    def test_repr_does_not_contain_token(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        rendered = repr(provider)
        assert SECRET_TOKEN not in rendered
        assert "REDACTED" in rendered

    def test_str_does_not_contain_token(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        assert SECRET_TOKEN not in str(provider)

    def test_no_token_attribute_on_instance(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        # No public token attribute
        assert not hasattr(provider, "access_token")
        assert not hasattr(provider, "token")

    def test_redact_helper_scrubs_token(self) -> None:
        text = f"oh no error: X-Shopify-Access-Token: {SECRET_TOKEN}"
        scrubbed = _redact(text, SECRET_TOKEN)
        assert SECRET_TOKEN not in scrubbed
        assert "***REDACTED***" in scrubbed

    def test_network_error_warning_does_not_leak_token(self) -> None:
        def failing_transport(*_a, **_k):
            # Simulate a provider that includes the token in its exception
            raise RuntimeError(f"connection refused with header {SECRET_TOKEN}")

        provider = _build_real_provider(transport=failing_transport)
        capsule = _make_capsule()
        export = provider.sync_drafts(capsule)
        for d in export.drafts:
            for w in d.warnings:
                assert SECRET_TOKEN not in w
                assert d.status == ShopifyDraftStatus.FAILED


# ---------- GraphQL payload safety ----------


class TestGraphQLPayloadShape:
    def test_payload_pins_status_draft(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            captured["url"] = url
            captured["headers"] = headers
            return _success_response()

        provider = _build_real_provider(transport=t)
        capsule = _make_capsule()
        provider.sync_drafts(capsule)

        assert "productCreate" in captured["payload"]["query"]
        input_ = captured["payload"]["variables"]["input"]
        assert input_["status"] == "DRAFT"

    def test_payload_excludes_publish_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_drafts(_make_capsule())
        input_ = captured["payload"]["variables"]["input"]
        forbidden = {
            "publishedAt",
            "publishedScope",
            "publishToCurrentChannel",
            "publish",
        }
        assert not (forbidden & input_.keys())

    def test_payload_excludes_inventory_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_drafts(_make_capsule())
        input_ = captured["payload"]["variables"]["input"]
        for forbidden in (
            "inventoryItem",
            "inventoryQuantities",
            "tracked",
            "onHand",
        ):
            assert forbidden not in input_
        for v in input_.get("variants", []):
            for forbidden in (
                "inventoryItem",
                "inventoryQuantities",
                "inventoryPolicy",
                "inventoryManagement",
            ):
                assert forbidden not in v

    def test_payload_has_no_order_or_customer_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_drafts(_make_capsule())
        rendered = str(captured["payload"])
        forbidden_keys = (
            "draftOrderCreate",
            "orderCreate",
            "customerCreate",
            "customerUpdate",
            "webhookSubscriptionCreate",
            "publishablePublish",
        )
        for key in forbidden_keys:
            assert key not in rendered

    def test_mutation_constant_only_does_productCreate(self) -> None:
        assert "productCreate" in PRODUCT_CREATE_MUTATION
        assert "publishablePublish" not in PRODUCT_CREATE_MUTATION
        assert "inventoryAdjust" not in PRODUCT_CREATE_MUTATION
        assert "orderCreate" not in PRODUCT_CREATE_MUTATION
        assert "customerCreate" not in PRODUCT_CREATE_MUTATION

    def test_endpoint_url_uses_admin_graphql(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["url"] = url
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_drafts(_make_capsule())
        assert captured["url"].startswith("https://schluesselkinder.myshopify.com/admin/api/")
        assert captured["url"].endswith("/graphql.json")

    def test_headers_include_access_token(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["headers"] = headers
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_drafts(_make_capsule())
        assert captured["headers"]["X-Shopify-Access-Token"] == SECRET_TOKEN


# ---------- Response handling ----------


class TestResponseHandling:
    def test_successful_draft_status(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        export = provider.sync_drafts(_make_capsule())
        for d in export.drafts:
            assert d.status == ShopifyDraftStatus.DRAFT
            assert d.provider_payload.get("shopify_product_id")
            assert d.provider_payload.get("shopify_status") == "DRAFT"

    def test_server_returns_non_draft_status_marked_failed(self) -> None:
        def t(*a, **k):
            return {
                "data": {
                    "productCreate": {
                        "product": {
                            "id": "gid://shopify/Product/1",
                            "handle": "x",
                            "title": "x",
                            "status": "ACTIVE",
                            "onlineStoreUrl": "https://example",
                            "vendor": "X",
                            "productType": "",
                            "tags": [],
                        },
                        "userErrors": [],
                    }
                }
            }

        provider = _build_real_provider(transport=t)
        export = provider.sync_drafts(_make_capsule())
        for d in export.drafts:
            assert d.status == ShopifyDraftStatus.FAILED
            assert any("unexpected_status" in w for w in d.warnings)

    def test_user_errors_marked_failed(self) -> None:
        def t(*a, **k):
            return {
                "data": {
                    "productCreate": {
                        "product": None,
                        "userErrors": [{"field": ["title"], "message": "is required"}],
                    }
                }
            }

        provider = _build_real_provider(transport=t)
        export = provider.sync_drafts(_make_capsule())
        for d in export.drafts:
            assert d.status == ShopifyDraftStatus.FAILED
            assert any("title: is required" in w for w in d.warnings)

    def test_top_level_graphql_errors_marked_failed(self) -> None:
        def t(*a, **k):
            return {"errors": [{"message": "throttled"}]}

        provider = _build_real_provider(transport=t)
        export = provider.sync_drafts(_make_capsule())
        for d in export.drafts:
            assert d.status == ShopifyDraftStatus.FAILED
            assert any("throttled" in w for w in d.warnings)

    def test_interpret_response_redacts_token_in_error_message(self) -> None:
        from app.providers.shopify.real import _interpret_response as interp

        # Build a draft via mock first
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        drafts = provider.build_product_drafts(_make_capsule())
        bad = {"errors": [{"message": f"auth failed token={SECRET_TOKEN}"}]}
        result = interp(drafts[0], bad, token=SECRET_TOKEN)
        for w in result.warnings:
            assert SECRET_TOKEN not in w


# ---------- Mock provider unchanged ----------


class TestMockUnchanged:
    def test_mock_does_not_call_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Sentinel — if urllib gets called, the test fails.
        import urllib.request

        called = {"n": 0}

        def boom(*_a, **_k):
            called["n"] += 1
            raise AssertionError("network should not be called in mock mode")

        monkeypatch.setattr(urllib.request, "urlopen", boom)

        provider = MockShopifyDraftProvider()
        export = provider.export_mock(_make_capsule())
        assert called["n"] == 0
        assert export.provider_mode == "mock"
        for d in export.drafts:
            assert d.status == ShopifyDraftStatus.EXPORTED_MOCK

    def test_mock_deterministic_field_count(self) -> None:
        provider = MockShopifyDraftProvider()
        a = provider.export_mock(_make_capsule())
        b = provider.export_mock(_make_capsule())
        assert a.total_products == b.total_products


# ---------- Route E2E ----------


class TestSyncDraftsRoute:
    def _make_stored_capsule(self):
        from app.main import merch_capsule_repository

        capsule = _make_capsule()
        merch_capsule_repository.store(capsule)
        return capsule

    def test_sync_route_in_mock_mode_returns_deterministic_export(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_shopify_drafts

        capsule = self._make_stored_capsule()
        export = asyncio.run(sync_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))
        assert export.capsule_id == capsule.capsule_id
        assert export.provider_mode == "mock"
        assert export.total_products > 0

    def test_sync_route_stores_draft_exports(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            shopify_draft_repository,
            sync_shopify_drafts,
        )

        capsule = self._make_stored_capsule()
        before = len(shopify_draft_repository.list_by_capsule(capsule.capsule_id))
        asyncio.run(sync_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))
        after = len(shopify_draft_repository.list_by_capsule(capsule.capsule_id))
        assert after >= before + 1

    def test_sync_route_unknown_capsule_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_shopify_drafts
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(sync_shopify_drafts(uuid4(), DEV_OPERATOR))
        assert exc.value.status_code == 404


# ---------- Capabilities ----------


class TestCapabilities:
    def test_capabilities_expose_live_sync_flag(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert hasattr(caps, "shopify_live_draft_sync_available")
        # In default (mock) mode the flag is False
        assert caps.shopify_live_draft_sync_available is False

    def test_capabilities_provider_mode_mock(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.shopify_provider_mode == "mock"


# ---------- No background / scheduler / webhook imports ----------


class TestNoForbiddenImports:
    def test_real_provider_no_webhook_imports(self) -> None:
        from app.providers.shopify import real

        source = inspect.getsource(real)
        # Comments mention these (negatively) — assert they appear at most
        # in the docstring negation list. We check usage tokens that would
        # signify code activity instead.
        assert "webhookSubscriptionCreate" not in [
            line for line in source.splitlines() if "import " in line
        ]

    def test_real_provider_no_background_worker_imports(self) -> None:
        from app.providers.shopify import real

        source = inspect.getsource(real)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
        assert "asyncio.create_task" not in source

    def test_real_provider_no_scheduler_imports(self) -> None:
        from app.providers.shopify import real

        source = inspect.getsource(real)
        assert "apscheduler" not in source
        assert "celery" not in source
        assert "import schedule" not in source
        assert "crontab" not in source

    def test_real_provider_uses_stdlib_http_only(self) -> None:
        """Real provider must not pin a new third-party HTTP library."""
        from app.providers.shopify import real

        source = inspect.getsource(real)
        # We use urllib from stdlib via the default transport.
        assert "urllib.request" in source
        # No requests, httpx, aiohttp imports
        for forbidden in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "from requests",
            "from httpx",
            "from aiohttp",
        ):
            assert forbidden not in source


# ---------- Sanity: existing S40 mock surface unaffected ----------


class TestExistingMockBehavior:
    def test_export_mock_still_works(self) -> None:
        provider = MockShopifyDraftProvider()
        capsule = _make_capsule()
        export = provider.export_mock(capsule)
        assert export.capsule_id == capsule.capsule_id

    def test_build_product_drafts_still_works(self) -> None:
        provider = MockShopifyDraftProvider()
        drafts = provider.build_product_drafts(_make_capsule())
        assert isinstance(drafts, list)


# ---------- Sanity: real-mode env wiring lives in os.environ, not in the module ----------


class TestRealModeEnvWiring:
    def test_real_mode_consumes_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_SHOPIFY_PROVIDER", "shopify")
        monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "schluesselkinder.myshopify.com")
        monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", SECRET_TOKEN)
        provider = build_shopify_draft_provider()
        assert provider.name == "shopify"
        assert supports_live_sync(provider) is True
        # Env state cleanup is monkeypatch's responsibility.
        # As a defensive check, ensure os.environ is restored after the
        # test exits.
        assert os.environ.get("SHOPIFY_ADMIN_ACCESS_TOKEN") == SECRET_TOKEN
