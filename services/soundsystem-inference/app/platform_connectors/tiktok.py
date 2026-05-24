"""Mock TikTok connector — S52.

Produces deterministic social analytics events:
views, shares, comments, merch_interest.

No real TikTok API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.provider_normalization import normalize_social_event
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorType,
)


class MockTikTokConnector:
    """Mock TikTok platform connector. Deterministic preview data."""

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.TIKTOK

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
        """Return deterministic mock TikTok events.

        Metrics: views, shares, comments.
        """
        base = {"mock_adapter": "tiktok", "preview": "true"}
        return [
            normalize_social_event(
                connector_type=ConnectorType.TIKTOK,
                metric=AnalyticsMetric.VIEWS,
                value=87300,
                campaign_id=campaign_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.TIKTOK,
                metric=AnalyticsMetric.SHARES,
                value=4210,
                campaign_id=campaign_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.TIKTOK,
                metric=AnalyticsMetric.COMMENTS,
                value=1580,
                campaign_id=campaign_id,
                metadata=base,
            ),
        ]

    def health(self) -> dict[str, str]:
        return {"status": "mock", "adapter": "tiktok"}
