"""Tests for S52 — Mock Platform Connector Contracts.

Covers:
- Each connector returns deterministic events
- Event sources match connector type
- Metrics are valid AnalyticsMetric values
- Context IDs (campaign_id, release_id, track_id) are preserved
- No external imports / HTTP clients in connector modules
- preview-sync uses connector-specific events for supported types
- preview-sync does not mutate analytics repository
- import-demo mutates analytics repository only when POSTed
- import-demo requires operator
- Unsupported connector returns blocked/warnings or ValueError
- Factory and registry functions
- Capabilities flag
- Existing S51 tests still pass (covered by full suite)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.platform_connectors import (
    build_mock_platform_connector,
    has_mock_platform_connector,
    list_mock_platform_connector_types,
)
from app.platform_connectors.instagram import MockInstagramConnector
from app.platform_connectors.shopify import MockShopifyConnector
from app.platform_connectors.soundcloud import MockSoundCloudConnector
from app.platform_connectors.spotify import MockSpotifyConnector
from app.platform_connectors.tiktok import MockTikTokConnector
from app.schemas import (
    AnalyticsMetric,
    AnalyticsSource,
    ConnectorSyncPreview,
    ConnectorType,
)


# ---------- Spotify ----------


class TestMockSpotifyConnector:
    def test_connector_type(self) -> None:
        c = MockSpotifyConnector()
        assert c.connector_type == ConnectorType.SPOTIFY

    def test_capabilities(self) -> None:
        c = MockSpotifyConnector()
        caps = c.capabilities()
        assert len(caps) >= 2

    def test_preview_events_deterministic(self) -> None:
        c = MockSpotifyConnector()
        e1 = c.preview_events()
        e2 = c.preview_events()
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.metric == b.metric
            assert a.value == b.value

    def test_preview_events_source(self) -> None:
        c = MockSpotifyConnector()
        for event in c.preview_events():
            assert event.source == AnalyticsSource.SPOTIFY

    def test_preview_events_metrics(self) -> None:
        c = MockSpotifyConnector()
        metrics = {e.metric for e in c.preview_events()}
        assert AnalyticsMetric.STREAMS in metrics
        assert AnalyticsMetric.SAVES in metrics
        assert AnalyticsMetric.FOLLOWERS in metrics

    def test_context_ids_preserved(self) -> None:
        c = MockSpotifyConnector()
        tid = str(uuid4())
        rid = str(uuid4())
        events = c.preview_events(track_id=tid, release_id=rid)
        streaming = [e for e in events if e.metadata.get("category") == "streaming"]
        for event in streaming:
            assert event.track_id is not None
            assert str(event.track_id) == tid

    def test_health(self) -> None:
        c = MockSpotifyConnector()
        h = c.health()
        assert h["status"] == "mock"


# ---------- TikTok ----------


class TestMockTikTokConnector:
    def test_connector_type(self) -> None:
        c = MockTikTokConnector()
        assert c.connector_type == ConnectorType.TIKTOK

    def test_preview_events_source(self) -> None:
        c = MockTikTokConnector()
        for event in c.preview_events():
            assert event.source == AnalyticsSource.TIKTOK

    def test_preview_events_metrics(self) -> None:
        c = MockTikTokConnector()
        metrics = {e.metric for e in c.preview_events()}
        assert AnalyticsMetric.VIEWS in metrics
        assert AnalyticsMetric.SHARES in metrics
        assert AnalyticsMetric.COMMENTS in metrics

    def test_deterministic(self) -> None:
        c = MockTikTokConnector()
        e1 = c.preview_events()
        e2 = c.preview_events()
        for a, b in zip(e1, e2):
            assert a.value == b.value

    def test_campaign_id_preserved(self) -> None:
        c = MockTikTokConnector()
        cid = str(uuid4())
        events = c.preview_events(campaign_id=cid)
        for event in events:
            assert event.campaign_id is not None
            assert str(event.campaign_id) == cid


# ---------- Instagram ----------


class TestMockInstagramConnector:
    def test_connector_type(self) -> None:
        c = MockInstagramConnector()
        assert c.connector_type == ConnectorType.INSTAGRAM

    def test_preview_events_source(self) -> None:
        c = MockInstagramConnector()
        for event in c.preview_events():
            assert event.source == AnalyticsSource.INSTAGRAM

    def test_preview_events_metrics(self) -> None:
        c = MockInstagramConnector()
        metrics = {e.metric for e in c.preview_events()}
        assert AnalyticsMetric.VIEWS in metrics
        assert AnalyticsMetric.LIKES in metrics
        assert AnalyticsMetric.SHARES in metrics
        assert AnalyticsMetric.ENGAGEMENT_RATE in metrics

    def test_deterministic(self) -> None:
        c = MockInstagramConnector()
        e1 = c.preview_events()
        e2 = c.preview_events()
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.value == b.value


# ---------- SoundCloud ----------


class TestMockSoundCloudConnector:
    def test_connector_type(self) -> None:
        c = MockSoundCloudConnector()
        assert c.connector_type == ConnectorType.SOUNDCLOUD

    def test_preview_events_source(self) -> None:
        c = MockSoundCloudConnector()
        for event in c.preview_events():
            assert event.source == AnalyticsSource.SOUNDCLOUD

    def test_preview_events_metrics(self) -> None:
        c = MockSoundCloudConnector()
        metrics = {e.metric for e in c.preview_events()}
        assert AnalyticsMetric.PLAYS in metrics
        assert AnalyticsMetric.REPOSTS in metrics
        assert AnalyticsMetric.COMMENTS in metrics
        assert AnalyticsMetric.LIKES in metrics

    def test_track_id_preserved(self) -> None:
        c = MockSoundCloudConnector()
        tid = str(uuid4())
        events = c.preview_events(track_id=tid)
        for event in events:
            assert event.track_id is not None
            assert str(event.track_id) == tid


# ---------- Shopify ----------


class TestMockShopifyConnector:
    def test_connector_type(self) -> None:
        c = MockShopifyConnector()
        assert c.connector_type == ConnectorType.SHOPIFY

    def test_preview_events_source(self) -> None:
        c = MockShopifyConnector()
        for event in c.preview_events():
            assert event.source == AnalyticsSource.SHOPIFY

    def test_preview_events_metrics(self) -> None:
        c = MockShopifyConnector()
        metrics = {e.metric for e in c.preview_events()}
        assert AnalyticsMetric.VIEWS in metrics
        assert AnalyticsMetric.CART_ADDS in metrics
        assert AnalyticsMetric.ORDERS in metrics
        assert AnalyticsMetric.REVENUE in metrics
        assert AnalyticsMetric.CONVERSIONS in metrics

    def test_deterministic(self) -> None:
        c = MockShopifyConnector()
        e1 = c.preview_events()
        e2 = c.preview_events()
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.value == b.value


# ---------- Factory / Registry ----------


class TestPlatformConnectorFactory:
    def test_list_supported_types(self) -> None:
        types = list_mock_platform_connector_types()
        assert ConnectorType.SPOTIFY in types
        assert ConnectorType.TIKTOK in types
        assert ConnectorType.INSTAGRAM in types
        assert ConnectorType.SOUNDCLOUD in types
        assert ConnectorType.SHOPIFY in types
        assert len(types) == 5

    def test_build_spotify(self) -> None:
        c = build_mock_platform_connector(ConnectorType.SPOTIFY)
        assert c.connector_type == ConnectorType.SPOTIFY

    def test_build_tiktok(self) -> None:
        c = build_mock_platform_connector(ConnectorType.TIKTOK)
        assert c.connector_type == ConnectorType.TIKTOK

    def test_build_instagram(self) -> None:
        c = build_mock_platform_connector(ConnectorType.INSTAGRAM)
        assert c.connector_type == ConnectorType.INSTAGRAM

    def test_build_soundcloud(self) -> None:
        c = build_mock_platform_connector(ConnectorType.SOUNDCLOUD)
        assert c.connector_type == ConnectorType.SOUNDCLOUD

    def test_build_shopify(self) -> None:
        c = build_mock_platform_connector(ConnectorType.SHOPIFY)
        assert c.connector_type == ConnectorType.SHOPIFY

    def test_unsupported_raises(self) -> None:
        with pytest.raises(ValueError, match="No mock platform connector"):
            build_mock_platform_connector(ConnectorType.DISCORD)

    def test_has_mock_platform_connector(self) -> None:
        assert has_mock_platform_connector(ConnectorType.SPOTIFY) is True
        assert has_mock_platform_connector(ConnectorType.DISCORD) is False
        assert has_mock_platform_connector(ConnectorType.MANUAL) is False


# ---------- Preview-sync integration ----------


class TestPreviewSyncWithMockAdapters:
    def test_spotify_preview_uses_adapter(self) -> None:
        """Spotify is seeded as DISCONNECTED in default registry,
        so preview-sync route returns blocked. Test the adapter directly
        through build_connector_sync_preview with a mock connector."""
        from app.provider_sync_preview import build_connector_sync_preview
        from app.schemas import (
            ConnectorCapability,
            ConnectorStatus,
            ConnectorSyncMode,
            ProviderConnector,
        )

        connector = ProviderConnector(
            connector_id=uuid4(),
            connector_type=ConnectorType.SPOTIFY,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[ConnectorCapability.STREAMING, ConnectorCapability.ANALYTICS_PULL],
            enabled=True,
            mock_mode=True,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count == 3  # streams, saves, followers
        assert len(preview.blocked_reasons) == 0
        assert any("mock preview" in w.lower() for w in preview.warnings)
        # Events should have real values, not zero placeholders
        assert all(e.value > 0 for e in preview.normalized_events)

    def test_soundcloud_preview_uses_adapter(self) -> None:
        """SoundCloud is seeded as MOCK, so the route should use the adapter."""
        from app.main import preview_connector_sync

        result = asyncio.run(preview_connector_sync(ConnectorType.SOUNDCLOUD))
        assert isinstance(result, ConnectorSyncPreview)
        assert result.event_count == 4  # plays, reposts, comments, likes
        assert len(result.blocked_reasons) == 0
        # S52 adapter produces non-zero values
        assert all(e.value > 0 for e in result.normalized_events)
        assert any("mock preview" in w.lower() for w in result.warnings)

    def test_shopify_preview_uses_adapter(self) -> None:
        from app.provider_sync_preview import build_connector_sync_preview
        from app.schemas import (
            ConnectorCapability,
            ConnectorStatus,
            ConnectorSyncMode,
            ProviderConnector,
        )

        connector = ProviderConnector(
            connector_id=uuid4(),
            connector_type=ConnectorType.SHOPIFY,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[ConnectorCapability.COMMERCE, ConnectorCapability.ANALYTICS_PULL],
            enabled=True,
            mock_mode=True,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count == 5  # views, cart_adds, orders, revenue, conversions
        sources = {e.source for e in preview.normalized_events}
        assert AnalyticsSource.SHOPIFY in sources

    def test_preview_does_not_mutate_analytics(self) -> None:
        """Preview-sync must NOT add events to the analytics repository."""
        from app.main import analytics_repository, preview_connector_sync

        before = analytics_repository.summary().total_events
        asyncio.run(preview_connector_sync(ConnectorType.SOUNDCLOUD))
        after = analytics_repository.summary().total_events
        assert after == before

    def test_fallback_for_unsupported_connector(self) -> None:
        """Connectors without mock adapters still get generic previews."""
        from app.provider_sync_preview import build_connector_sync_preview
        from app.schemas import (
            ConnectorCapability,
            ConnectorStatus,
            ConnectorSyncMode,
            ProviderConnector,
        )

        connector = ProviderConnector(
            connector_id=uuid4(),
            connector_type=ConnectorType.DITTO,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[ConnectorCapability.DISTRIBUTION, ConnectorCapability.ANALYTICS_PULL],
            enabled=True,
            mock_mode=True,
        )
        preview = build_connector_sync_preview(connector)
        # Ditto has no S52 adapter, falls back to generic
        assert preview.event_count >= 0
        assert "zero placeholders" in " ".join(preview.warnings).lower()


# ---------- Import-demo route ----------


class TestImportDemoRoute:
    def test_import_demo_spotify(self) -> None:
        """Import-demo should add events to analytics repository."""
        from app.auth import DEV_OPERATOR
        from app.main import analytics_repository, import_demo_events

        before = analytics_repository.summary().total_events
        result = asyncio.run(import_demo_events(ConnectorType.SPOTIFY, DEV_OPERATOR))
        after = analytics_repository.summary().total_events
        assert isinstance(result, ConnectorSyncPreview)
        assert result.event_count == 3  # streams, saves, followers
        assert after == before + 3
        assert any("imported" in w.lower() for w in result.warnings)

    def test_import_demo_soundcloud(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import analytics_repository, import_demo_events

        before = analytics_repository.summary().total_events
        result = asyncio.run(import_demo_events(ConnectorType.SOUNDCLOUD, DEV_OPERATOR))
        after = analytics_repository.summary().total_events
        assert result.event_count == 4
        assert after == before + 4

    def test_import_demo_unsupported(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import import_demo_events

        result = asyncio.run(import_demo_events(ConnectorType.DISCORD, DEV_OPERATOR))
        assert result.event_count == 0
        assert len(result.blocked_reasons) > 0
        assert any("no mock adapter" in r.lower() for r in result.blocked_reasons)

    def test_import_demo_returns_events(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import import_demo_events

        result = asyncio.run(import_demo_events(ConnectorType.SHOPIFY, DEV_OPERATOR))
        assert result.event_count == 5
        assert len(result.normalized_events) == 5
        metrics = {e.metric for e in result.normalized_events}
        assert AnalyticsMetric.ORDERS in metrics
        assert AnalyticsMetric.REVENUE in metrics


# ---------- Capabilities ----------


class TestPlatformConnectorCapabilities:
    def test_mock_platform_connectors_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.mock_platform_connectors_available is True


# ---------- No external calls ----------


class TestNoExternalCallsPlatformConnectors:
    def test_no_http_imports_in_connectors(self) -> None:
        import inspect

        from app.platform_connectors import spotify, tiktok, instagram, soundcloud, shopify

        for mod in [spotify, tiktok, instagram, soundcloud, shopify]:
            source = inspect.getsource(mod)
            assert "httpx" not in source
            assert "aiohttp" not in source

    def test_no_http_imports_in_init(self) -> None:
        import inspect

        from app import platform_connectors

        source = inspect.getsource(platform_connectors)
        assert "httpx" not in source
        assert "aiohttp" not in source

    def test_no_oauth_imports(self) -> None:
        import inspect

        from app.platform_connectors import spotify, tiktok, instagram, soundcloud, shopify

        for mod in [spotify, tiktok, instagram, soundcloud, shopify]:
            source = inspect.getsource(mod)
            assert "oauth" not in source.lower()
            assert "authlib" not in source

    def test_no_requests_library(self) -> None:
        """Ensure 'requests' library is not imported (word may appear in docstrings)."""
        import inspect

        from app.platform_connectors import spotify, tiktok, instagram, soundcloud, shopify

        for mod in [spotify, tiktok, instagram, soundcloud, shopify]:
            source = inspect.getsource(mod)
            # Check for import statements specifically
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("import requests") or stripped.startswith("from requests"):
                    pytest.fail(f"Found requests import in {mod.__name__}")
