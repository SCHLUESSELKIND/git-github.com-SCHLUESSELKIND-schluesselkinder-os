"""Tests for S51 — Provider Connector Framework.

Covers:
- InMemoryConnectorRegistry CRUD
- Connector health checks
- Registry summary (new schema: enabled/ready/mock/blocked + breakdowns)
- Provider normalization (streaming, social, commerce, distribution)
- Metric validation (ValueError for unknown metrics)
- Connector seed generation
- Sync preview builder
- Routes: list, summary, get, health, preview-sync
- Factory function
- Capabilities flag
- No external calls
- Deterministic outputs
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.provider_connector_registry import (
    InMemoryConnectorRegistry,
    build_connector_registry,
)
from app.provider_connector_seed import build_default_connectors
from app.provider_normalization import (
    connector_to_source,
    normalize_commerce_event,
    normalize_distribution_event,
    normalize_social_event,
    normalize_streaming_event,
)
from app.provider_sync_preview import build_connector_sync_preview
from app.schemas import (
    AnalyticsMetric,
    AnalyticsSource,
    ConnectorCapability,
    ConnectorHealth,
    ConnectorRegistrySummary,
    ConnectorStatus,
    ConnectorSyncMode,
    ConnectorSyncPreview,
    ConnectorType,
    ProviderConnector,
)


# ---------- Helpers ----------


def _make_connector(
    *,
    connector_type: ConnectorType = ConnectorType.SOUNDCLOUD,
    status: ConnectorStatus = ConnectorStatus.MOCK,
    sync_mode: ConnectorSyncMode = ConnectorSyncMode.MOCK,
    capabilities: list[ConnectorCapability] | None = None,
    enabled: bool = True,
    mock_mode: bool = True,
) -> ProviderConnector:
    return ProviderConnector(
        connector_id=uuid4(),
        connector_type=connector_type,
        status=status,
        sync_mode=sync_mode,
        capabilities=capabilities or [ConnectorCapability.STREAMING],
        enabled=enabled,
        mock_mode=mock_mode,
    )


# ---------- Registry tests ----------


class TestInMemoryConnectorRegistry:
    def test_register_and_list(self) -> None:
        registry = InMemoryConnectorRegistry()
        connector = _make_connector()
        registry.register(connector)
        connectors = registry.list_connectors()
        assert len(connectors) == 1
        assert connectors[0].connector_type == ConnectorType.SOUNDCLOUD

    def test_get_connector(self) -> None:
        registry = InMemoryConnectorRegistry()
        connector = _make_connector(connector_type=ConnectorType.SPOTIFY)
        registry.register(connector)
        result = registry.get_connector(ConnectorType.SPOTIFY)
        assert result is not None
        assert result.connector_type == ConnectorType.SPOTIFY

    def test_get_connector_not_found(self) -> None:
        registry = InMemoryConnectorRegistry()
        assert registry.get_connector(ConnectorType.SPOTIFY) is None

    def test_register_replaces_existing(self) -> None:
        registry = InMemoryConnectorRegistry()
        c1 = _make_connector(status=ConnectorStatus.MOCK)
        c2 = _make_connector(status=ConnectorStatus.READY)
        registry.register(c1)
        registry.register(c2)
        connectors = registry.list_connectors()
        assert len(connectors) == 1
        assert connectors[0].status == ConnectorStatus.READY

    def test_list_sorted_by_type(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(_make_connector(connector_type=ConnectorType.TIKTOK))
        registry.register(_make_connector(connector_type=ConnectorType.DISCORD))
        registry.register(_make_connector(connector_type=ConnectorType.DITTO))
        connectors = registry.list_connectors()
        types = [c.connector_type.value for c in connectors]
        assert types == sorted(types)

    def test_mode(self) -> None:
        registry = InMemoryConnectorRegistry()
        assert registry.mode == "in_memory"


# ---------- Health tests ----------


class TestConnectorHealth:
    def test_mock_connector_healthy(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                status=ConnectorStatus.MOCK,
                enabled=True,
            )
        )
        health = registry.connector_health(ConnectorType.SOUNDCLOUD)
        assert health is not None
        assert health.healthy is True

    def test_disconnected_connector_unhealthy(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                status=ConnectorStatus.DISCONNECTED,
                enabled=False,
            )
        )
        health = registry.connector_health(ConnectorType.SOUNDCLOUD)
        assert health is not None
        assert health.healthy is False
        assert any("disconnected" in w.lower() for w in health.warnings)

    def test_blocked_connector_unhealthy(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                status=ConnectorStatus.BLOCKED,
                enabled=True,
            )
        )
        health = registry.connector_health(ConnectorType.SOUNDCLOUD)
        assert health is not None
        assert health.healthy is False

    def test_disabled_connector_unhealthy(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                status=ConnectorStatus.MOCK,
                enabled=False,
            )
        )
        health = registry.connector_health(ConnectorType.SOUNDCLOUD)
        assert health is not None
        assert health.healthy is False
        assert any("disabled" in w.lower() for w in health.warnings)

    def test_missing_config_for_disconnected(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SPOTIFY,
                status=ConnectorStatus.DISCONNECTED,
                enabled=False,
            )
        )
        health = registry.connector_health(ConnectorType.SPOTIFY)
        assert health is not None
        assert len(health.missing_configuration) > 0
        assert "SPOTIFY_CLIENT_ID" in health.missing_configuration

    def test_health_not_found(self) -> None:
        registry = InMemoryConnectorRegistry()
        assert registry.connector_health(ConnectorType.YOUTUBE) is None


# ---------- Summary tests ----------


class TestConnectorRegistrySummary:
    def test_empty_registry(self) -> None:
        registry = InMemoryConnectorRegistry()
        summary = registry.registry_summary()
        assert summary.total_connectors == 0

    def test_counts(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SOUNDCLOUD,
                status=ConnectorStatus.MOCK,
                enabled=True,
            )
        )
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SPOTIFY,
                status=ConnectorStatus.DISCONNECTED,
                enabled=False,
            )
        )
        registry.register(
            _make_connector(
                connector_type=ConnectorType.MANUAL,
                status=ConnectorStatus.READY,
                enabled=True,
            )
        )
        summary = registry.registry_summary()
        assert summary.total_connectors == 3
        assert summary.mock_connectors == 1
        assert summary.ready_connectors == 1
        assert summary.enabled_connectors == 2
        assert summary.blocked_connectors == 0

    def test_status_breakdown(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SOUNDCLOUD,
                status=ConnectorStatus.MOCK,
            )
        )
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SPOTIFY,
                status=ConnectorStatus.DISCONNECTED,
                enabled=False,
            )
        )
        summary = registry.registry_summary()
        assert summary.status_breakdown["mock"] == 1
        assert summary.status_breakdown["disconnected"] == 1

    def test_capability_breakdown(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SOUNDCLOUD,
                capabilities=[ConnectorCapability.STREAMING],
            )
        )
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SHOPIFY,
                capabilities=[ConnectorCapability.COMMERCE, ConnectorCapability.STREAMING],
            )
        )
        summary = registry.registry_summary()
        assert summary.capability_breakdown["streaming"] == 2
        assert summary.capability_breakdown["commerce"] == 1

    def test_blocked_warnings(self) -> None:
        registry = InMemoryConnectorRegistry()
        registry.register(
            _make_connector(
                connector_type=ConnectorType.SPOTIFY,
                status=ConnectorStatus.BLOCKED,
                enabled=True,
            )
        )
        summary = registry.registry_summary()
        assert summary.blocked_connectors == 1
        assert len(summary.warnings) > 0
        assert any("blocked" in w.lower() for w in summary.warnings)


# ---------- Normalization tests ----------


class TestProviderNormalization:
    def test_connector_to_source_mapping(self) -> None:
        assert connector_to_source(ConnectorType.SPOTIFY) == AnalyticsSource.SPOTIFY
        assert connector_to_source(ConnectorType.SOUNDCLOUD) == AnalyticsSource.SOUNDCLOUD
        assert connector_to_source(ConnectorType.SHOPIFY) == AnalyticsSource.SHOPIFY

    def test_normalize_streaming_event(self) -> None:
        event = normalize_streaming_event(
            connector_type=ConnectorType.SPOTIFY,
            metric=AnalyticsMetric.STREAMS,
            value=3000,
        )
        assert event.source == AnalyticsSource.SPOTIFY
        assert event.metric == AnalyticsMetric.STREAMS
        assert event.value == 3000
        assert event.metadata["connector"] == "spotify"
        assert event.metadata["category"] == "streaming"

    def test_normalize_social_event(self) -> None:
        event = normalize_social_event(
            connector_type=ConnectorType.TIKTOK,
            metric=AnalyticsMetric.VIEWS,
            value=50000,
        )
        assert event.source == AnalyticsSource.TIKTOK
        assert event.metric == AnalyticsMetric.VIEWS
        assert event.value == 50000
        assert event.metadata["category"] == "social"

    def test_normalize_commerce_event(self) -> None:
        event = normalize_commerce_event(
            connector_type=ConnectorType.SHOPIFY,
            metric=AnalyticsMetric.ORDERS,
            value=12,
        )
        assert event.source == AnalyticsSource.SHOPIFY
        assert event.metric == AnalyticsMetric.ORDERS
        assert event.value == 12
        assert event.metadata["category"] == "commerce"

    def test_normalize_distribution_event(self) -> None:
        event = normalize_distribution_event(
            connector_type=ConnectorType.DITTO,
            metric=AnalyticsMetric.STREAMS,
            value=8000,
        )
        assert event.source == AnalyticsSource.DITTO
        assert event.metric == AnalyticsMetric.STREAMS
        assert event.value == 8000
        assert event.metadata["category"] == "distribution"

    def test_streaming_with_track_id(self) -> None:
        tid = str(uuid4())
        event = normalize_streaming_event(
            connector_type=ConnectorType.SOUNDCLOUD,
            metric=AnalyticsMetric.PLAYS,
            value=500,
            track_id=tid,
        )
        assert event.track_id is not None
        assert str(event.track_id) == tid

    def test_commerce_with_merch_id(self) -> None:
        mid = str(uuid4())
        event = normalize_commerce_event(
            connector_type=ConnectorType.PRINTFUL,
            metric=AnalyticsMetric.ORDERS,
            value=5,
            merch_capsule_id=mid,
        )
        assert event.merch_capsule_id is not None
        assert str(event.merch_capsule_id) == mid

    def test_custom_metadata_merged(self) -> None:
        event = normalize_streaming_event(
            connector_type=ConnectorType.SPOTIFY,
            metric=AnalyticsMetric.SAVES,
            value=100,
            metadata={"track_name": "PICK ME UP"},
        )
        assert event.metadata["connector"] == "spotify"
        assert event.metadata["track_name"] == "PICK ME UP"

    def test_manual_connector_maps(self) -> None:
        assert connector_to_source(ConnectorType.MANUAL) == AnalyticsSource.MANUAL

    def test_unknown_streaming_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="not valid for streaming"):
            normalize_streaming_event(
                connector_type=ConnectorType.SPOTIFY,
                metric=AnalyticsMetric.ORDERS,
                value=10,
            )

    def test_unknown_social_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="not valid for social"):
            normalize_social_event(
                connector_type=ConnectorType.TIKTOK,
                metric=AnalyticsMetric.ORDERS,
                value=10,
            )

    def test_unknown_commerce_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="not valid for commerce"):
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.STREAMS,
                value=10,
            )

    def test_unknown_distribution_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="not valid for distribution"):
            normalize_distribution_event(
                connector_type=ConnectorType.DITTO,
                metric=AnalyticsMetric.ORDERS,
                value=10,
            )


# ---------- Sync preview tests ----------


class TestConnectorSyncPreview:
    def test_mock_connector_produces_events(self) -> None:
        connector = _make_connector(
            connector_type=ConnectorType.SOUNDCLOUD,
            status=ConnectorStatus.MOCK,
            capabilities=[
                ConnectorCapability.STREAMING,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=True,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count > 0
        assert len(preview.normalized_events) == preview.event_count
        assert len(preview.blocked_reasons) == 0
        # S52: SoundCloud has a mock adapter producing deterministic non-zero values
        for event in preview.normalized_events:
            assert event.metadata["preview"] == "true"

    def test_disconnected_connector_blocked(self) -> None:
        connector = _make_connector(
            connector_type=ConnectorType.SPOTIFY,
            status=ConnectorStatus.DISCONNECTED,
            enabled=False,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count == 0
        assert len(preview.blocked_reasons) > 0
        assert any("disconnected" in r.lower() for r in preview.blocked_reasons)

    def test_blocked_connector_has_blocked_reasons(self) -> None:
        connector = _make_connector(
            connector_type=ConnectorType.SPOTIFY,
            status=ConnectorStatus.BLOCKED,
            enabled=True,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count == 0
        assert len(preview.blocked_reasons) > 0
        assert any("blocked" in r.lower() for r in preview.blocked_reasons)

    def test_disabled_connector_blocked(self) -> None:
        connector = _make_connector(
            connector_type=ConnectorType.SOUNDCLOUD,
            status=ConnectorStatus.MOCK,
            enabled=False,
        )
        preview = build_connector_sync_preview(connector)
        assert preview.event_count == 0
        assert any("disabled" in r.lower() for r in preview.blocked_reasons)


# ---------- Factory tests ----------


class TestConnectorRegistryFactory:
    def test_build_connector_registry(self) -> None:
        registry = build_connector_registry()
        connectors = registry.list_connectors()
        assert len(connectors) == 11
        assert registry.mode == "in_memory"

    def test_factory_seeds_default_connectors(self) -> None:
        registry = build_connector_registry()
        sc = registry.get_connector(ConnectorType.SOUNDCLOUD)
        assert sc is not None
        assert sc.status == ConnectorStatus.MOCK


# ---------- Seed tests ----------


class TestConnectorSeed:
    def test_build_default_connectors(self) -> None:
        connectors = build_default_connectors()
        assert len(connectors) == 11  # 5 mock + 5 disconnected + 1 manual

    def test_deterministic(self) -> None:
        c1 = build_default_connectors()
        c2 = build_default_connectors()
        assert len(c1) == len(c2)
        for a, b in zip(c1, c2):
            assert a.connector_id == b.connector_id
            assert a.connector_type == b.connector_type
            assert a.status == b.status

    def test_soundcloud_mock(self) -> None:
        connectors = build_default_connectors()
        sc = next(c for c in connectors if c.connector_type == ConnectorType.SOUNDCLOUD)
        assert sc.status == ConnectorStatus.MOCK
        assert sc.mock_mode is True
        assert sc.enabled is True
        assert ConnectorCapability.STREAMING in sc.capabilities

    def test_spotify_disconnected(self) -> None:
        connectors = build_default_connectors()
        sp = next(c for c in connectors if c.connector_type == ConnectorType.SPOTIFY)
        assert sp.status == ConnectorStatus.DISCONNECTED
        assert sp.enabled is False

    def test_manual_ready(self) -> None:
        connectors = build_default_connectors()
        manual = next(c for c in connectors if c.connector_type == ConnectorType.MANUAL)
        assert manual.status == ConnectorStatus.READY
        assert manual.enabled is True
        assert manual.mock_mode is False

    def test_all_types_covered(self) -> None:
        connectors = build_default_connectors()
        types = {c.connector_type for c in connectors}
        assert ConnectorType.SOUNDCLOUD in types
        assert ConnectorType.DITTO in types
        assert ConnectorType.SHOPIFY in types
        assert ConnectorType.PRINTFUL in types
        assert ConnectorType.TIKTOK_SHOP in types
        assert ConnectorType.SPOTIFY in types
        assert ConnectorType.TIKTOK in types
        assert ConnectorType.INSTAGRAM in types
        assert ConnectorType.YOUTUBE in types
        assert ConnectorType.DISCORD in types
        assert ConnectorType.MANUAL in types


# ---------- Route tests ----------


class TestConnectorRoutes:
    def test_list_connectors(self) -> None:
        from app.main import list_connectors

        result = asyncio.run(list_connectors())
        assert isinstance(result, list)
        assert len(result) == 11

    def test_connector_summary(self) -> None:
        from app.main import get_connector_summary

        result = asyncio.run(get_connector_summary())
        assert isinstance(result, ConnectorRegistrySummary)
        assert result.total_connectors == 11

    def test_get_connector(self) -> None:
        from app.main import get_connector

        result = asyncio.run(get_connector(ConnectorType.SOUNDCLOUD))
        assert isinstance(result, ProviderConnector)
        assert result.connector_type == ConnectorType.SOUNDCLOUD

    def test_get_connector_not_found(self) -> None:

        # ConnectorType only has valid values, so let's test via the health
        # route pattern — but for 404 we test via the registry directly
        registry = InMemoryConnectorRegistry()
        assert registry.get_connector(ConnectorType.SPOTIFY) is None

    def test_connector_health(self) -> None:
        from app.main import get_connector_health

        result = asyncio.run(get_connector_health(ConnectorType.SOUNDCLOUD))
        assert isinstance(result, ConnectorHealth)
        assert result.healthy is True

    def test_connector_health_disconnected(self) -> None:
        from app.main import get_connector_health

        result = asyncio.run(get_connector_health(ConnectorType.SPOTIFY))
        assert isinstance(result, ConnectorHealth)
        assert result.healthy is False

    def test_preview_sync_mock(self) -> None:
        from app.main import preview_connector_sync

        result = asyncio.run(preview_connector_sync(ConnectorType.SOUNDCLOUD))
        assert isinstance(result, ConnectorSyncPreview)
        assert result.event_count >= 0
        assert len(result.blocked_reasons) == 0
        assert any("preview" in w.lower() for w in result.warnings)

    def test_preview_sync_disconnected(self) -> None:
        from app.main import preview_connector_sync

        result = asyncio.run(preview_connector_sync(ConnectorType.SPOTIFY))
        assert isinstance(result, ConnectorSyncPreview)
        assert result.event_count == 0
        assert len(result.blocked_reasons) > 0


# ---------- Capabilities test ----------


class TestConnectorCapabilities:
    def test_provider_connector_framework_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.provider_connector_framework_available is True


# ---------- No external calls ----------


class TestNoExternalCallsConnectors:
    def test_no_http_imports_in_registry(self) -> None:
        import inspect

        from app import provider_connector_registry

        source = inspect.getsource(provider_connector_registry)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_http_imports_in_normalization(self) -> None:
        import inspect

        from app import provider_normalization

        source = inspect.getsource(provider_normalization)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_http_imports_in_seed(self) -> None:
        import inspect

        from app import provider_connector_seed

        source = inspect.getsource(provider_connector_seed)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_http_imports_in_sync_preview(self) -> None:
        import inspect

        from app import provider_sync_preview

        source = inspect.getsource(provider_sync_preview)
        assert "httpx" not in source
        assert "aiohttp" not in source

    def test_no_oauth_imports(self) -> None:
        import inspect

        from app import provider_connector_registry, provider_normalization, provider_sync_preview

        for mod in [provider_connector_registry, provider_normalization, provider_sync_preview]:
            source = inspect.getsource(mod)
            assert "oauth" not in source.lower()
            assert "authlib" not in source
