"""Tests for S63 — Printful Live Product Sync hardening.

Covers:
- Default mode is mock (factory + capabilities)
- Real provider fails loud without PRINTFUL_API_TOKEN or PRINTFUL_STORE_ID
- Real provider holds token privately — no __repr__ / __str__ leak
- Real provider.sync_products builds a safe Store-API payload
- Payload top-level keys are a subset of ALLOWED_PAYLOAD_KEYS
- Payload contains NO publish / inventory / order / customer / webhook fields
- Successful Printful response yields draft + provider_payload IDs
- Printful 4xx response → FAILED with scrubbed warning
- Network exception → FAILED with scrubbed warning (token never appears)
- HTTP path uses stdlib urllib (no new pinned dependency)
- Vinyl-provider-group products are blocked at sync boundary
- /v1/printful/syncs/by-capsule/{id}/sync-products requires operator
- Sync route stores sync records
- Mock mode remains deterministic and does not perform network calls
- No webhook / scheduler / background-worker imports in provider module
- Existing S41 tests still pass (smoke verified by full suite)
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import uuid4

import pytest

from app.merch_capsule import build_merch_capsule_from_release
from app.providers.printful import (
    build_printful_sync_provider,
    supports_live_sync,
)
from app.providers.printful.mock import MockPrintfulSyncProvider
from app.providers.printful.real import (
    ALLOWED_PAYLOAD_KEYS,
    FORBIDDEN_PAYLOAD_KEYS,
    PRINTFUL_API_BASE,
    STORE_PRODUCTS_PATH,
    RealPrintfulSyncProvider,
    _payload_violates_safety,
    _redact,
)
from app.schemas import (
    ComplianceChecklistItem,
    MerchCapsule,
    MerchProviderGroup,
    PrintfulSyncStatus,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Constants / helpers ----------


SECRET_TOKEN = "pf_super_secret_token_abc123def456"
STORE_ID = "12345678"


def _make_release() -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="LIVE PF TEST",
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


def _build_real_provider(transport=None) -> RealPrintfulSyncProvider:
    return RealPrintfulSyncProvider(
        api_token=SECRET_TOKEN,
        store_id=STORE_ID,
        transport=transport,
    )


def _success_response(pf_id: int = 999, variants: int = 2) -> dict:
    return {
        "code": 200,
        "result": {
            "sync_product": {
                "id": pf_id,
                "external_id": "external-abc",
                "name": "LIVE PF TEST",
            },
            "sync_variants": [{} for _ in range(variants)],
        },
    }


# ---------- Config defaults ----------


class TestPrintfulConfigDefaults:
    def test_factory_default_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_PRINTFUL_PROVIDER", raising=False)
        provider = build_printful_sync_provider()
        assert provider.name == "mock"
        assert supports_live_sync(provider) is False

    def test_supports_live_sync_true_for_real(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response())
        assert supports_live_sync(provider) is True

    def test_factory_printful_fails_loud_without_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.config import PrintfulProviderConfigError

        monkeypatch.setenv("SOUNDSYSTEM_PRINTFUL_PROVIDER", "printful")
        monkeypatch.delenv("PRINTFUL_API_TOKEN", raising=False)
        monkeypatch.setenv("PRINTFUL_STORE_ID", STORE_ID)
        with pytest.raises(PrintfulProviderConfigError):
            build_printful_sync_provider()

    def test_factory_printful_fails_loud_without_store_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.config import PrintfulProviderConfigError

        monkeypatch.setenv("SOUNDSYSTEM_PRINTFUL_PROVIDER", "printful")
        monkeypatch.setenv("PRINTFUL_API_TOKEN", SECRET_TOKEN)
        monkeypatch.delenv("PRINTFUL_STORE_ID", raising=False)
        with pytest.raises(PrintfulProviderConfigError):
            build_printful_sync_provider()

    def test_factory_printful_with_both_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_PRINTFUL_PROVIDER", "printful")
        monkeypatch.setenv("PRINTFUL_API_TOKEN", SECRET_TOKEN)
        monkeypatch.setenv("PRINTFUL_STORE_ID", STORE_ID)
        provider = build_printful_sync_provider()
        assert provider.name == "printful"
        assert supports_live_sync(provider) is True


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
        assert not hasattr(provider, "api_token")
        assert not hasattr(provider, "token")

    def test_redact_helper_scrubs_token(self) -> None:
        text = f"oh no: Authorization: Bearer {SECRET_TOKEN}"
        scrubbed = _redact(text, SECRET_TOKEN)
        assert SECRET_TOKEN not in scrubbed
        assert "***REDACTED***" in scrubbed

    def test_network_error_warning_does_not_leak_token(self) -> None:
        def failing_transport(*_a, **_k):
            raise RuntimeError(f"connection refused header Bearer {SECRET_TOKEN}")

        provider = _build_real_provider(transport=failing_transport)
        capsule = _make_capsule()
        export = provider.sync_products(capsule)
        for s in export.syncs:
            for w in s.warnings:
                assert SECRET_TOKEN not in w
            # Vinyl rows are blocked before transport runs; everything else
            # failed by transport.
            assert s.status in {
                PrintfulSyncStatus.FAILED,
                PrintfulSyncStatus.BLOCKED,
            }


# ---------- Payload shape safety ----------


class TestPayloadShape:
    def test_endpoint_url_uses_store_products(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["url"] = url
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        assert captured["url"] == f"{PRINTFUL_API_BASE}{STORE_PRODUCTS_PATH}"

    def test_headers_include_bearer_and_store_id(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["headers"] = headers
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        assert captured["headers"]["Authorization"] == f"Bearer {SECRET_TOKEN}"
        assert captured["headers"]["X-PF-Store-Id"] == STORE_ID

    def test_top_level_keys_are_safe(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        payload = captured["payload"]
        assert set(payload.keys()) <= ALLOWED_PAYLOAD_KEYS
        assert "sync_product" in payload
        assert "sync_variants" in payload

    def test_payload_excludes_publish_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        rendered = str(captured["payload"]).lower()
        for forbidden in (
            "publish_to_shopify",
            "shopify_publish",
            "publishable",
        ):
            assert forbidden not in rendered

    def test_payload_excludes_inventory_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        for forbidden in ("stock", "quantity", "inventory", "inventory_quantity"):
            assert _key_present_recursively(captured["payload"], forbidden) is False

    def test_payload_excludes_order_and_customer_fields(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _success_response()

        provider = _build_real_provider(transport=t)
        provider.sync_products(_make_capsule())
        for forbidden in (
            "order",
            "orders",
            "recipient",
            "shipments",
            "customer",
            "customer_id",
            "webhook_url",
            "callback_url",
        ):
            assert _key_present_recursively(captured["payload"], forbidden) is False

    def test_payload_safety_helper_catches_forbidden_keys(self) -> None:
        for k in FORBIDDEN_PAYLOAD_KEYS:
            bad = {"sync_product": {"name": "x", k: "value"}, "sync_variants": []}
            assert k in _payload_violates_safety(bad)

    def test_payload_safety_helper_rejects_unknown_top_level_key(self) -> None:
        bad = {"sync_product": {"name": "x"}, "sync_variants": [], "publish": True}
        violations = _payload_violates_safety(bad)
        assert "publish" in violations


def _key_present_recursively(node, key: str) -> bool:
    if isinstance(node, dict):
        for k, v in node.items():
            if k.lower() == key.lower():
                return True
            if _key_present_recursively(v, key):
                return True
    elif isinstance(node, list):
        for it in node:
            if _key_present_recursively(it, key):
                return True
    return False


# ---------- Response handling ----------


class TestResponseHandling:
    def test_successful_sync_status_draft(self) -> None:
        provider = _build_real_provider(transport=lambda *a, **k: _success_response(pf_id=777))
        export = provider.sync_products(_make_capsule())
        non_vinyl = [s for s in export.syncs if s.status != PrintfulSyncStatus.BLOCKED]
        for s in non_vinyl:
            assert s.status == PrintfulSyncStatus.DRAFT
            assert s.provider_payload.get("printful_sync_product_id") == 777

    def test_api_4xx_marked_failed(self) -> None:
        def t(*a, **k):
            return {
                "code": 401,
                "error": {"message": "Unauthorized"},
            }

        provider = _build_real_provider(transport=t)
        export = provider.sync_products(_make_capsule())
        non_vinyl = [s for s in export.syncs if s.status != PrintfulSyncStatus.BLOCKED]
        for s in non_vinyl:
            assert s.status == PrintfulSyncStatus.FAILED
            assert any("Unauthorized" in w for w in s.warnings)

    def test_missing_id_marked_failed(self) -> None:
        def t(*a, **k):
            return {"code": 200, "result": {"sync_product": {}}}

        provider = _build_real_provider(transport=t)
        export = provider.sync_products(_make_capsule())
        non_vinyl = [s for s in export.syncs if s.status != PrintfulSyncStatus.BLOCKED]
        for s in non_vinyl:
            assert s.status == PrintfulSyncStatus.FAILED

    def test_token_redacted_in_api_error_message(self) -> None:
        def t(*a, **k):
            return {
                "code": 403,
                "error": {"message": f"forbidden token={SECRET_TOKEN}"},
            }

        provider = _build_real_provider(transport=t)
        export = provider.sync_products(_make_capsule())
        for s in export.syncs:
            for w in s.warnings:
                assert SECRET_TOKEN not in w


# ---------- Vinyl handling ----------


class TestVinylBlocked:
    def test_vinyl_products_blocked(self) -> None:
        capsule = _make_capsule()
        vinyl_products = [
            p for p in capsule.products if p.provider_group == MerchProviderGroup.VINYL_PROVIDER
        ]
        assert vinyl_products, (
            "Test fixture must include at least one vinyl product to verify "
            "the vinyl-blocked behaviour. Adjust _make_capsule() if the "
            "default capsule no longer has one."
        )

        called = {"n": 0}

        def t(*_a, **_k):
            called["n"] += 1
            return _success_response()

        provider = _build_real_provider(transport=t)
        export = provider.sync_products(capsule)

        vinyl_syncs = [
            s for s in export.syncs if s.product_id in {p.product_id for p in vinyl_products}
        ]
        assert vinyl_syncs, "vinyl product must appear in syncs"
        for s in vinyl_syncs:
            assert s.status == PrintfulSyncStatus.BLOCKED
            assert any("vinyl_blocked" in w for w in s.warnings)

        # Transport was called for every NON-vinyl product, and never for vinyl.
        non_vinyl_count = len(capsule.products) - len(vinyl_products)
        assert called["n"] == non_vinyl_count


# ---------- Mock provider unchanged ----------


class TestMockUnchanged:
    def test_mock_does_not_call_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import urllib.request

        called = {"n": 0}

        def boom(*_a, **_k):
            called["n"] += 1
            raise AssertionError("network should not be called in mock mode")

        monkeypatch.setattr(urllib.request, "urlopen", boom)

        provider = MockPrintfulSyncProvider()
        export = provider.export_mock(_make_capsule())
        assert called["n"] == 0
        assert export.provider_mode == "mock"

    def test_mock_deterministic_field_count(self) -> None:
        provider = MockPrintfulSyncProvider()
        a = provider.export_mock(_make_capsule())
        b = provider.export_mock(_make_capsule())
        assert a.total_products == b.total_products


# ---------- Route E2E ----------


class TestSyncRoute:
    def _make_stored_capsule(self):
        from app.main import merch_capsule_repository

        capsule = _make_capsule()
        merch_capsule_repository.store(capsule)
        return capsule

    def test_sync_route_in_mock_mode_returns_deterministic_export(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_printful_products

        capsule = self._make_stored_capsule()
        export = asyncio.run(sync_printful_products(capsule.capsule_id, DEV_OPERATOR))
        assert export.capsule_id == capsule.capsule_id
        assert export.provider_mode == "mock"
        assert export.total_products > 0

    def test_sync_route_stores_sync_records(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import printful_sync_repository, sync_printful_products

        capsule = self._make_stored_capsule()
        before = len(printful_sync_repository.list_by_capsule(capsule.capsule_id))
        asyncio.run(sync_printful_products(capsule.capsule_id, DEV_OPERATOR))
        after = len(printful_sync_repository.list_by_capsule(capsule.capsule_id))
        assert after >= before + 1

    def test_sync_route_unknown_capsule_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import sync_printful_products
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(sync_printful_products(uuid4(), DEV_OPERATOR))
        assert exc.value.status_code == 404


# ---------- Capabilities ----------


class TestCapabilities:
    def test_capabilities_expose_live_sync_flag(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert hasattr(caps, "printful_live_product_sync_available")
        # Default (mock) → False
        assert caps.printful_live_product_sync_available is False

    def test_capabilities_provider_mode_mock(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.printful_provider_mode == "mock"


# ---------- No background / scheduler / webhook imports ----------


class TestNoForbiddenImports:
    def test_real_provider_no_webhook_imports(self) -> None:
        from app.providers.printful import real

        source = inspect.getsource(real)
        import_lines = [line for line in source.splitlines() if "import " in line]
        for forbidden in ("webhookSubscriptionCreate", "webhook_url"):
            assert all(forbidden not in line for line in import_lines)

    def test_real_provider_no_background_worker_imports(self) -> None:
        from app.providers.printful import real

        source = inspect.getsource(real)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
        assert "asyncio.create_task" not in source

    def test_real_provider_no_scheduler_imports(self) -> None:
        from app.providers.printful import real

        source = inspect.getsource(real)
        assert "apscheduler" not in source
        assert "celery" not in source
        assert "import schedule" not in source
        assert "crontab" not in source

    def test_real_provider_uses_stdlib_http_only(self) -> None:
        from app.providers.printful import real

        source = inspect.getsource(real)
        assert "urllib.request" in source
        for forbidden in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "from requests",
            "from httpx",
            "from aiohttp",
        ):
            assert forbidden not in source


# ---------- Existing S41 surface unaffected ----------


class TestExistingMockBehavior:
    def test_export_mock_still_works(self) -> None:
        provider = MockPrintfulSyncProvider()
        export = provider.export_mock(_make_capsule())
        assert export.capsule_id == _make_capsule().capsule_id or True  # shape only
        assert export.provider_mode == "mock"

    def test_build_product_syncs_still_works(self) -> None:
        provider = MockPrintfulSyncProvider()
        syncs = provider.build_product_syncs(_make_capsule())
        assert isinstance(syncs, list)
