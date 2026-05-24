"""Mock SoundCloud connector — S52.

Produces deterministic streaming analytics events:
plays, reposts, comments, likes.

No real SoundCloud API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.provider_normalization import normalize_streaming_event
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorType,
)


class MockSoundCloudConnector:
    """Mock SoundCloud platform connector. Deterministic preview data."""

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.SOUNDCLOUD

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.STREAMING,
            ConnectorCapability.PUBLISHING,
            ConnectorCapability.ANALYTICS_PULL,
        ]

    def preview_events(
        self,
        *,
        campaign_id: str | None = None,
        release_id: str | None = None,
        track_id: str | None = None,
    ) -> list[AnalyticsEvent]:
        """Return deterministic mock SoundCloud events.

        Metrics: plays, reposts, comments, likes.
        """
        base = {"mock_adapter": "soundcloud", "preview": "true"}
        return [
            normalize_streaming_event(
                connector_type=ConnectorType.SOUNDCLOUD,
                metric=AnalyticsMetric.PLAYS,
                value=5670,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
            normalize_streaming_event(
                connector_type=ConnectorType.SOUNDCLOUD,
                metric=AnalyticsMetric.REPOSTS,
                value=312,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
            normalize_streaming_event(
                connector_type=ConnectorType.SOUNDCLOUD,
                metric=AnalyticsMetric.COMMENTS,
                value=89,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
            normalize_streaming_event(
                connector_type=ConnectorType.SOUNDCLOUD,
                metric=AnalyticsMetric.LIKES,
                value=1430,
                track_id=track_id,
                release_id=release_id,
                metadata=base,
            ),
        ]

    def health(self) -> dict[str, str]:
        return {"status": "mock", "adapter": "soundcloud"}
