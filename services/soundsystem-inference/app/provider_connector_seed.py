"""Provider Connector Seed — S51 default connectors.

Deterministic seed data for the connector registry.
All connectors start in mock or disconnected mode.
No real provider API calls. No OAuth. No credentials.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas import (
    ConnectorCapability,
    ConnectorStatus,
    ConnectorSyncMode,
    ConnectorType,
    ProviderConnector,
)


def build_default_connectors() -> list[ProviderConnector]:
    """Build deterministic default connectors for the registry.

    Existing provider boundaries (SoundCloud, Ditto, Shopify, Printful,
    TikTok Shop) are seeded as MOCK with their known capabilities.
    Unimplemented providers (Spotify, TikTok, Instagram, YouTube,
    Discord) are seeded as DISCONNECTED.
    Manual is always READY.

    Deterministic. Fixed UUIDs. No randomness. No external calls.
    """
    return [
        # --- Existing provider boundaries (mock mode) ---
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000001"),
            connector_type=ConnectorType.SOUNDCLOUD,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[
                ConnectorCapability.STREAMING,
                ConnectorCapability.PUBLISHING,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=True,
            mock_mode=True,
            metadata={
                "provider_module": "app.providers.soundcloud",
                "boundary_slice": "S36",
            },
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000002"),
            connector_type=ConnectorType.DITTO,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[
                ConnectorCapability.DISTRIBUTION,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=True,
            mock_mode=True,
            metadata={
                "provider_module": "app.providers.ditto",
                "boundary_slice": "S38",
            },
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000003"),
            connector_type=ConnectorType.SHOPIFY,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[
                ConnectorCapability.COMMERCE,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=True,
            mock_mode=True,
            metadata={
                "provider_module": "app.providers.shopify",
                "boundary_slice": "S39",
            },
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000004"),
            connector_type=ConnectorType.PRINTFUL,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[
                ConnectorCapability.MERCH,
                ConnectorCapability.COMMERCE,
            ],
            enabled=True,
            mock_mode=True,
            metadata={
                "provider_module": "app.providers.printful",
                "boundary_slice": "S40",
            },
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000005"),
            connector_type=ConnectorType.TIKTOK_SHOP,
            status=ConnectorStatus.MOCK,
            sync_mode=ConnectorSyncMode.MOCK,
            capabilities=[
                ConnectorCapability.COMMERCE,
                ConnectorCapability.SOCIAL,
            ],
            enabled=True,
            mock_mode=True,
            metadata={
                "provider_module": "app.providers.tiktok_shop",
                "boundary_slice": "S41",
            },
        ),
        # --- Unimplemented providers (disconnected) ---
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000006"),
            connector_type=ConnectorType.SPOTIFY,
            status=ConnectorStatus.DISCONNECTED,
            sync_mode=ConnectorSyncMode.DISABLED,
            capabilities=[
                ConnectorCapability.STREAMING,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=False,
            mock_mode=False,
            warnings=["No Spotify adapter implemented yet."],
            metadata={"boundary_slice": "future"},
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000007"),
            connector_type=ConnectorType.TIKTOK,
            status=ConnectorStatus.DISCONNECTED,
            sync_mode=ConnectorSyncMode.DISABLED,
            capabilities=[
                ConnectorCapability.SOCIAL,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=False,
            mock_mode=False,
            warnings=["No TikTok adapter implemented yet."],
            metadata={"boundary_slice": "future"},
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000008"),
            connector_type=ConnectorType.INSTAGRAM,
            status=ConnectorStatus.DISCONNECTED,
            sync_mode=ConnectorSyncMode.DISABLED,
            capabilities=[
                ConnectorCapability.SOCIAL,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=False,
            mock_mode=False,
            warnings=["No Instagram adapter implemented yet."],
            metadata={"boundary_slice": "future"},
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000009"),
            connector_type=ConnectorType.YOUTUBE,
            status=ConnectorStatus.DISCONNECTED,
            sync_mode=ConnectorSyncMode.DISABLED,
            capabilities=[
                ConnectorCapability.STREAMING,
                ConnectorCapability.SOCIAL,
                ConnectorCapability.ANALYTICS_PULL,
            ],
            enabled=False,
            mock_mode=False,
            warnings=["No YouTube adapter implemented yet."],
            metadata={"boundary_slice": "future"},
        ),
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000010"),
            connector_type=ConnectorType.DISCORD,
            status=ConnectorStatus.DISCONNECTED,
            sync_mode=ConnectorSyncMode.DISABLED,
            capabilities=[
                ConnectorCapability.SOCIAL,
                ConnectorCapability.CAMPAIGN_SYNC,
            ],
            enabled=False,
            mock_mode=False,
            warnings=["No Discord adapter implemented yet."],
            metadata={"boundary_slice": "future"},
        ),
        # --- Manual (always ready) ---
        ProviderConnector(
            connector_id=UUID("00000000-0000-4000-a000-000000000011"),
            connector_type=ConnectorType.MANUAL,
            status=ConnectorStatus.READY,
            sync_mode=ConnectorSyncMode.MANUAL,
            capabilities=[
                ConnectorCapability.ANALYTICS_PULL,
                ConnectorCapability.CAMPAIGN_SYNC,
            ],
            enabled=True,
            mock_mode=False,
            metadata={"description": "Manual event entry via API"},
        ),
    ]
