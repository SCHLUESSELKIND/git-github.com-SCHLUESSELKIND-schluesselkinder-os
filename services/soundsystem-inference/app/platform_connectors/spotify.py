"""Mock Spotify connector — S52.

Produces deterministic streaming analytics events:
streams, saves, followers.

No real Spotify API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.provider_normalization import (
    normalize_streaming_event,
    normalize_social_event,
)
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorType,
)


class MockSpotifyConnector:
    """Mock Spotify platform connector. Deterministic preview data."""

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.SPOTIFY

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.STREAMING,
            ConnectorCapability.ANALYTICS_PULL,
        ]

    def preview_events(
        self,
        *,
        campaign_id: str | None = None,
        release_id: str | None = None,
        track_id: str | None = None,
    ) -> list[AnalyticsEvent]:
        """Return deterministic mock Spotify events.

        Metrics: streams, saves, followers.
        """
        base = {"mock_adapter": "spotify", "preview": "true"}
        return [
            normalize_streaming_event(
                connector_type=ConnectorType.SPOTIFY,
                metric=AnalyticsMetric.STREAMS,
                value=12480,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
            normalize_streaming_event(
                connector_type=ConnectorType.SPOTIFY,
                metric=AnalyticsMetric.SAVES,
                value=843,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
            normalize_social_event(
                connector_type=ConnectorType.SPOTIFY,
                metric=AnalyticsMetric.FOLLOWERS,
                value=2150,
                campaign_id=campaign_id,
                metadata=base,
            ),
        ]

    def health(self) -> dict[str, str]:
        return {"status": "mock", "adapter": "spotify"}
