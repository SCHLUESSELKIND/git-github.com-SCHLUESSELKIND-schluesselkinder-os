"""Provider Connector Registry — S51 contract.

In-memory registry of provider connectors. Tracks connector state,
capabilities, health, and sync readiness.

No real provider API calls. No auth flows. No ingestion workers.
No background jobs. No webhook listeners. No scheduling.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    ConnectorHealth,
    ConnectorRegistrySummary,
    ConnectorStatus,
    ConnectorType,
    ProviderConnector,
)


class ProviderConnectorRegistryProtocol(Protocol):
    """Persistence boundary for provider connectors."""

    @property
    def mode(self) -> str: ...

    def register(self, connector: ProviderConnector) -> None: ...

    def list_connectors(self) -> list[ProviderConnector]: ...

    def get_connector(self, connector_type: ConnectorType) -> ProviderConnector | None: ...

    def connector_health(self, connector_type: ConnectorType) -> ConnectorHealth | None: ...

    def registry_summary(self) -> ConnectorRegistrySummary: ...


class InMemoryConnectorRegistry:
    """In-memory connector registry. Data lost on restart."""

    def __init__(self) -> None:
        self._connectors: dict[ConnectorType, ProviderConnector] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def register(self, connector: ProviderConnector) -> None:
        self._connectors[connector.connector_type] = connector

    def list_connectors(self) -> list[ProviderConnector]:
        return sorted(
            self._connectors.values(),
            key=lambda c: c.connector_type.value,
        )

    def get_connector(self, connector_type: ConnectorType) -> ProviderConnector | None:
        return self._connectors.get(connector_type)

    def connector_health(self, connector_type: ConnectorType) -> ConnectorHealth | None:
        connector = self._connectors.get(connector_type)
        if connector is None:
            return None

        return _build_health(connector)

    def registry_summary(self) -> ConnectorRegistrySummary:
        connectors = list(self._connectors.values())
        if not connectors:
            return ConnectorRegistrySummary()

        enabled = 0
        ready = 0
        mock = 0
        blocked = 0
        capability_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        warnings: list[str] = []

        for c in connectors:
            status_key = c.status.value
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

            if c.enabled:
                enabled += 1
            if c.status == ConnectorStatus.MOCK:
                mock += 1
            elif c.status == ConnectorStatus.READY:
                ready += 1
            elif c.status == ConnectorStatus.BLOCKED:
                blocked += 1
                warnings.append(f"{c.connector_type.value} is blocked. Check configuration.")

            for cap in c.capabilities:
                cap_key = cap.value
                capability_counts[cap_key] = capability_counts.get(cap_key, 0) + 1

        return ConnectorRegistrySummary(
            total_connectors=len(connectors),
            enabled_connectors=enabled,
            ready_connectors=ready,
            mock_connectors=mock,
            blocked_connectors=blocked,
            capability_breakdown=capability_counts,
            status_breakdown=status_counts,
            warnings=warnings,
        )


# ---------- Helpers ----------


def _build_health(connector: ProviderConnector) -> ConnectorHealth:
    """Build health check from connector state. Deterministic."""
    warnings: list[str] = list(connector.warnings)
    missing: list[str] = []

    healthy = connector.enabled and connector.status in (
        ConnectorStatus.READY,
        ConnectorStatus.MOCK,
        ConnectorStatus.CONFIGURED,
    )

    if connector.status == ConnectorStatus.DISCONNECTED:
        warnings.append("Connector is disconnected. No data will flow.")
    if connector.status == ConnectorStatus.BLOCKED:
        warnings.append("Connector is blocked. Check configuration.")
        healthy = False
    if not connector.enabled:
        warnings.append("Connector is disabled.")
        healthy = False

    # Platform-specific missing config hints
    _CONFIG_HINTS: dict[ConnectorType, list[str]] = {
        ConnectorType.SPOTIFY: [
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
        ],
        ConnectorType.SOUNDCLOUD: [
            "SOUNDCLOUD_CLIENT_ID",
            "SOUNDCLOUD_CLIENT_SECRET",
        ],
        ConnectorType.TIKTOK: [
            "TIKTOK_ACCESS_TOKEN",
        ],
        ConnectorType.INSTAGRAM: [
            "INSTAGRAM_ACCESS_TOKEN",
        ],
        ConnectorType.YOUTUBE: [
            "YOUTUBE_API_KEY",
        ],
        ConnectorType.DISCORD: [
            "DISCORD_BOT_TOKEN",
        ],
        ConnectorType.DITTO: [
            "DITTO_API_KEY",
        ],
        ConnectorType.SHOPIFY: [
            "SHOPIFY_STORE_URL",
            "SHOPIFY_ACCESS_TOKEN",
        ],
        ConnectorType.PRINTFUL: [
            "PRINTFUL_API_KEY",
        ],
        ConnectorType.TIKTOK_SHOP: [
            "TIKTOK_SHOP_ACCESS_TOKEN",
        ],
    }

    if connector.status == ConnectorStatus.DISCONNECTED:
        missing = _CONFIG_HINTS.get(connector.connector_type, [])

    return ConnectorHealth(
        connector_type=connector.connector_type,
        status=connector.status,
        healthy=healthy,
        warnings=warnings,
        missing_configuration=missing,
        capabilities=list(connector.capabilities),
    )


# ---------- Factory ----------


def build_connector_registry() -> InMemoryConnectorRegistry:
    """Build and seed the default in-memory connector registry.

    Creates an InMemoryConnectorRegistry, populates it with all
    default connectors from :func:`build_default_connectors`, and
    returns it ready to use.

    Deterministic. No external calls.
    """
    from app.provider_connector_seed import build_default_connectors

    registry = InMemoryConnectorRegistry()
    for connector in build_default_connectors():
        registry.register(connector)
    return registry
