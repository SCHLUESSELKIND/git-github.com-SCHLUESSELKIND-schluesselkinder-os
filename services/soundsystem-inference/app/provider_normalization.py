"""Provider Normalization — S51 event normalization contract.

Pure, deterministic functions for normalizing provider-specific data
into the unified AnalyticsEvent schema.

No real provider API calls. No external dependencies.
These functions convert structured provider data dicts into
AnalyticsEvent objects that feed the analytics graph.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    AnalyticsEvent,
    AnalyticsGranularity,
    AnalyticsMetric,
    AnalyticsSource,
    ConnectorType,
)


# ---------- Source Mapping ----------

_CONNECTOR_TO_SOURCE: dict[ConnectorType, AnalyticsSource] = {
    ConnectorType.SPOTIFY: AnalyticsSource.SPOTIFY,
    ConnectorType.SOUNDCLOUD: AnalyticsSource.SOUNDCLOUD,
    ConnectorType.TIKTOK: AnalyticsSource.TIKTOK,
    ConnectorType.INSTAGRAM: AnalyticsSource.INSTAGRAM,
    ConnectorType.YOUTUBE: AnalyticsSource.YOUTUBE,
    ConnectorType.DISCORD: AnalyticsSource.DISCORD,
    ConnectorType.DITTO: AnalyticsSource.DITTO,
    ConnectorType.SHOPIFY: AnalyticsSource.SHOPIFY,
    ConnectorType.PRINTFUL: AnalyticsSource.PRINTFUL,
    ConnectorType.TIKTOK_SHOP: AnalyticsSource.TIKTOK_SHOP,
    ConnectorType.MANUAL: AnalyticsSource.MANUAL,
}


def connector_to_source(connector_type: ConnectorType) -> AnalyticsSource:
    """Map connector type to analytics source. Deterministic."""
    return _CONNECTOR_TO_SOURCE.get(connector_type, AnalyticsSource.MANUAL)


# ---------- Metric validation ----------

_STREAMING_METRICS: frozenset[AnalyticsMetric] = frozenset(
    {
        AnalyticsMetric.PLAYS,
        AnalyticsMetric.STREAMS,
        AnalyticsMetric.SAVES,
        AnalyticsMetric.LIKES,
        AnalyticsMetric.REPOSTS,
        AnalyticsMetric.COMMENTS,
        AnalyticsMetric.SHARES,
    }
)

_SOCIAL_METRICS: frozenset[AnalyticsMetric] = frozenset(
    {
        AnalyticsMetric.VIEWS,
        AnalyticsMetric.LIKES,
        AnalyticsMetric.SHARES,
        AnalyticsMetric.COMMENTS,
        AnalyticsMetric.ENGAGEMENT_RATE,
        AnalyticsMetric.FOLLOWERS,
    }
)

_COMMERCE_METRICS: frozenset[AnalyticsMetric] = frozenset(
    {
        AnalyticsMetric.VIEWS,
        AnalyticsMetric.CART_ADDS,
        AnalyticsMetric.ORDERS,
        AnalyticsMetric.REVENUE,
        AnalyticsMetric.CONVERSIONS,
    }
)

_DISTRIBUTION_METRICS: frozenset[AnalyticsMetric] = frozenset(
    {
        AnalyticsMetric.STREAMS,
        AnalyticsMetric.PLAYS,
        AnalyticsMetric.REVENUE,
        AnalyticsMetric.SAVES,
    }
)


def _validate_metric(
    metric: AnalyticsMetric, allowed: frozenset[AnalyticsMetric], category: str
) -> None:
    """Raise ValueError if the metric is not valid for the category."""
    if metric not in allowed:
        raise ValueError(
            f"Metric {metric.value!r} is not valid for {category} normalization. "
            f"Allowed: {sorted(m.value for m in allowed)}"
        )


# ---------- Streaming Normalization ----------


def normalize_streaming_event(
    *,
    connector_type: ConnectorType,
    metric: AnalyticsMetric,
    value: float,
    track_id: str | None = None,
    release_id: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, str] | None = None,
) -> AnalyticsEvent:
    """Normalize a streaming platform event into AnalyticsEvent.

    Streaming connectors: Spotify, SoundCloud, Ditto, YouTube.
    Metrics: plays, streams, saves, likes, reposts, comments, shares.

    Deterministic. No external calls.
    """
    _validate_metric(metric, _STREAMING_METRICS, "streaming")
    from uuid import UUID

    return AnalyticsEvent(
        event_id=uuid4(),
        source=connector_to_source(connector_type),
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        track_id=UUID(track_id) if track_id else None,
        release_id=UUID(release_id) if release_id else None,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata={
            "connector": connector_type.value,
            "category": "streaming",
            **(metadata or {}),
        },
    )


# ---------- Social Normalization ----------


def normalize_social_event(
    *,
    connector_type: ConnectorType,
    metric: AnalyticsMetric,
    value: float,
    campaign_id: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, str] | None = None,
) -> AnalyticsEvent:
    """Normalize a social platform event into AnalyticsEvent.

    Social connectors: TikTok, Instagram, Discord, YouTube.
    Metrics: views, likes, shares, comments, engagement_rate, followers.

    Deterministic. No external calls.
    """
    _validate_metric(metric, _SOCIAL_METRICS, "social")
    from uuid import UUID

    return AnalyticsEvent(
        event_id=uuid4(),
        source=connector_to_source(connector_type),
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        campaign_id=UUID(campaign_id) if campaign_id else None,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata={
            "connector": connector_type.value,
            "category": "social",
            **(metadata or {}),
        },
    )


# ---------- Commerce Normalization ----------


def normalize_commerce_event(
    *,
    connector_type: ConnectorType,
    metric: AnalyticsMetric,
    value: float,
    merch_capsule_id: str | None = None,
    vinyl_id: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, str] | None = None,
) -> AnalyticsEvent:
    """Normalize a commerce platform event into AnalyticsEvent.

    Commerce connectors: Shopify, Printful, TikTok Shop.
    Metrics: views, cart_adds, orders, revenue, conversions.

    Deterministic. No external calls.
    """
    _validate_metric(metric, _COMMERCE_METRICS, "commerce")
    from uuid import UUID

    return AnalyticsEvent(
        event_id=uuid4(),
        source=connector_to_source(connector_type),
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        merch_capsule_id=UUID(merch_capsule_id) if merch_capsule_id else None,
        vinyl_id=UUID(vinyl_id) if vinyl_id else None,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata={
            "connector": connector_type.value,
            "category": "commerce",
            **(metadata or {}),
        },
    )


# ---------- Distribution Normalization ----------


def normalize_distribution_event(
    *,
    connector_type: ConnectorType,
    metric: AnalyticsMetric,
    value: float,
    release_id: str | None = None,
    track_id: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, str] | None = None,
) -> AnalyticsEvent:
    """Normalize a distribution platform event into AnalyticsEvent.

    Distribution connectors: Ditto.
    Metrics: streams, plays, revenue, saves.

    Deterministic. No external calls.
    """
    _validate_metric(metric, _DISTRIBUTION_METRICS, "distribution")
    from uuid import UUID

    return AnalyticsEvent(
        event_id=uuid4(),
        source=connector_to_source(connector_type),
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        release_id=UUID(release_id) if release_id else None,
        track_id=UUID(track_id) if track_id else None,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata={
            "connector": connector_type.value,
            "category": "distribution",
            **(metadata or {}),
        },
    )
