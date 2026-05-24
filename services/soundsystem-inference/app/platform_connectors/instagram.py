"""Mock Instagram connector — S52.

Produces deterministic social analytics events:
views, likes, shares, engagement_rate.

No real Instagram API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.provider_normalization import normalize_social_event
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorType,
)


class MockInstagramConnector:
    """Mock Instagram platform connector. Deterministic preview data."""

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.INSTAGRAM

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.SOCIAL,
            ConnectorCapability.ANALYTICS_PULL,
        ]

    def preview_events(
        self,
        *,
        campaign_id: str | None = None,
        release_id: str | None = None,
        track_id: str | None = None,
    ) -> list[AnalyticsEvent]:
        """Return deterministic mock Instagram events.

        Metrics: views, likes, shares, engagement_rate.
        """
        base = {"mock_adapter": "instagram", "preview": "true"}
        return [
            normalize_social_event(
                connector_type=ConnectorType.INSTAGRAM,
                metric=AnalyticsMetric.VIEWS,
                value=34500,
                campaign_id=campaign_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.INSTAGRAM,
                metric=AnalyticsMetric.LIKES,
                value=6120,
                campaign_id=campaign_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.INSTAGRAM,
                metric=AnalyticsMetric.SHARES,
                value=1890,
                campaign_id=campaign_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.INSTAGRAM,
                metric=AnalyticsMetric.ENGAGEMENT_RATE,
                value=4.7,
                campaign_id=campaign_id,
                metadata=base,
            ),
        ]

    def health(self) -> dict[str, str]:
        return {"status": "mock", "adapter": "instagram"}
