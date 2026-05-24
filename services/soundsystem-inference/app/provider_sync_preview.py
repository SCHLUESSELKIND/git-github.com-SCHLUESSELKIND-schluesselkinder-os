"""Provider Sync Preview — S51/S52 sync preview builder.

Builds deterministic preview of what a connector sync would produce.
Uses platform-specific mock adapters (S52) when available, otherwise
falls back to generic zero-value placeholder events.

No real provider API calls. No auth flows. No ingestion workers.
"""

from __future__ import annotations

from app.platform_connectors import has_mock_platform_connector, build_mock_platform_connector
from app.provider_normalization import normalize_streaming_event
from app.schemas import (
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorStatus,
    ConnectorSyncPreview,
    ProviderConnector,
)


def build_connector_sync_preview(connector: ProviderConnector) -> ConnectorSyncPreview:
    """Build a deterministic sync preview for a connector.

    Blocked/disconnected/disabled connectors return zero events with
    blocked_reasons. Active connectors with a mock platform adapter
    (S52) return connector-specific deterministic events. Others
    return generic zero-value placeholders.

    Deterministic. No external calls.
    """
    blocked_reasons: list[str] = []
    warnings: list[str] = []

    if not connector.enabled:
        blocked_reasons.append("Connector is disabled.")
    if connector.status == ConnectorStatus.DISCONNECTED:
        blocked_reasons.append("Connector is disconnected. Configure credentials first.")
    if connector.status == ConnectorStatus.BLOCKED:
        blocked_reasons.append("Connector is blocked. Resolve issues first.")

    if blocked_reasons:
        return ConnectorSyncPreview(
            connector_type=connector.connector_type,
            event_count=0,
            normalized_events=[],
            warnings=warnings,
            blocked_reasons=blocked_reasons,
        )

    # S52: use platform-specific mock adapter if available
    if has_mock_platform_connector(connector.connector_type):
        adapter = build_mock_platform_connector(connector.connector_type)
        mock_events = adapter.preview_events()
        warnings.append("Mock preview only — no data imported.")
        if connector.mock_mode:
            warnings.append("Connector is in mock mode. Real sync requires provider credentials.")
        return ConnectorSyncPreview(
            connector_type=connector.connector_type,
            event_count=len(mock_events),
            normalized_events=mock_events,
            warnings=warnings,
            blocked_reasons=[],
        )

    # Fallback: generic zero-value placeholder events
    mock_events = []
    if ConnectorCapability.STREAMING in connector.capabilities:
        mock_events.append(
            normalize_streaming_event(
                connector_type=connector.connector_type,
                metric=AnalyticsMetric.STREAMS,
                value=0,
                metadata={"preview": "true"},
            )
        )
    if ConnectorCapability.ANALYTICS_PULL in connector.capabilities:
        mock_events.append(
            normalize_streaming_event(
                connector_type=connector.connector_type,
                metric=AnalyticsMetric.PLAYS,
                value=0,
                metadata={"preview": "true"},
            )
        )

    warnings.append("Preview only. No real data pulled. Values are zero placeholders.")
    if connector.mock_mode:
        warnings.append("Connector is in mock mode. Real sync requires provider credentials.")

    return ConnectorSyncPreview(
        connector_type=connector.connector_type,
        event_count=len(mock_events),
        normalized_events=mock_events,
        warnings=warnings,
        blocked_reasons=[],
    )
