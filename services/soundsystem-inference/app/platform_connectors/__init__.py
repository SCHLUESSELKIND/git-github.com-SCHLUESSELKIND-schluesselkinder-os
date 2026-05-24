"""Mock Platform Connectors — S52 contract.

Factory and registry for platform-specific mock connectors.
Each connector produces deterministic normalized AnalyticsEvent
previews using the provider normalization layer.

No real provider API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.platform_connectors.base import MockPlatformConnector
from app.platform_connectors.instagram import MockInstagramConnector
from app.platform_connectors.shopify import MockShopifyConnector
from app.platform_connectors.soundcloud import MockSoundCloudConnector
from app.platform_connectors.spotify import MockSpotifyConnector
from app.platform_connectors.tiktok import MockTikTokConnector
from app.schemas import ConnectorType

_MOCK_CONNECTORS: dict[ConnectorType, MockPlatformConnector] = {
    ConnectorType.SPOTIFY: MockSpotifyConnector(),
    ConnectorType.TIKTOK: MockTikTokConnector(),
    ConnectorType.INSTAGRAM: MockInstagramConnector(),
    ConnectorType.SOUNDCLOUD: MockSoundCloudConnector(),
    ConnectorType.SHOPIFY: MockShopifyConnector(),
}

_SUPPORTED_TYPES: list[ConnectorType] = sorted(
    _MOCK_CONNECTORS.keys(),
    key=lambda t: t.value,
)


def build_mock_platform_connector(
    connector_type: ConnectorType,
) -> MockPlatformConnector:
    """Get a mock platform connector by type.

    Raises ValueError for unsupported connector types.
    Deterministic. No external calls.
    """
    connector = _MOCK_CONNECTORS.get(connector_type)
    if connector is None:
        raise ValueError(
            f"No mock platform connector for {connector_type.value!r}. "
            f"Supported: {[t.value for t in _SUPPORTED_TYPES]}"
        )
    return connector


def list_mock_platform_connector_types() -> list[ConnectorType]:
    """List all connector types that have mock platform adapters.

    Deterministic. No external calls.
    """
    return list(_SUPPORTED_TYPES)


def has_mock_platform_connector(connector_type: ConnectorType) -> bool:
    """Check whether a connector type has a mock platform adapter."""
    return connector_type in _MOCK_CONNECTORS
