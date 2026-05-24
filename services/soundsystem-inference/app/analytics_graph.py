"""Analytics Graph — S49 aggregation logic.

Pure, deterministic functions for computing campaign/track performance,
heat scores, viral scores, and breakdowns from normalized events.

No ML. No AI inference. No external calls. No provider API calls.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from app.schemas import (
    AnalyticsEvent,
    AnalyticsGranularity,
    AnalyticsMetric,
    AnalyticsSource,
    CampaignPerformance,
    ChannelPerformance,
    TrackPerformance,
)


# ---------- Campaign Performance ----------


def aggregate_campaign_performance(
    campaign_id: UUID,
    events: list[AnalyticsEvent],
) -> CampaignPerformance:
    """Aggregate events into a campaign performance summary.

    Heat score is a composite of reach, engagement, and conversion signals.
    Deterministic — same events always produce same result.
    """
    reach_metrics = {
        AnalyticsMetric.PLAYS,
        AnalyticsMetric.STREAMS,
        AnalyticsMetric.VIEWS,
    }
    engagement_metrics = {
        AnalyticsMetric.LIKES,
        AnalyticsMetric.REPOSTS,
        AnalyticsMetric.COMMENTS,
        AnalyticsMetric.SHARES,
        AnalyticsMetric.SAVES,
    }
    conversion_metrics = {
        AnalyticsMetric.CONVERSIONS,
        AnalyticsMetric.ORDERS,
        AnalyticsMetric.CART_ADDS,
    }
    revenue_metrics = {AnalyticsMetric.REVENUE}

    total_reach = 0.0
    engagement = 0.0
    conversions = 0.0
    revenue_estimate = 0.0

    source_values: dict[AnalyticsSource, float] = defaultdict(float)

    for event in events:
        if event.metric in reach_metrics:
            total_reach += event.value
        if event.metric in engagement_metrics:
            engagement += event.value
        if event.metric in conversion_metrics:
            conversions += event.value
        if event.metric in revenue_metrics:
            revenue_estimate += event.value
        source_values[event.source] += event.value

    heat_score = calculate_heat_score(total_reach, engagement, conversions)

    top_channel = (
        max(source_values, key=source_values.get)  # type: ignore[arg-type]
        if source_values
        else None
    )

    warnings: list[str] = []
    if total_reach == 0:
        warnings.append("No reach data — campaign may not have launched yet.")
    if engagement == 0 and total_reach > 0:
        warnings.append("Reach without engagement — check content quality.")
    if heat_score < 10:
        warnings.append("Low heat score — consider amplifying distribution.")

    return CampaignPerformance(
        campaign_id=campaign_id,
        total_reach=total_reach,
        engagement=engagement,
        conversions=conversions,
        revenue_estimate=revenue_estimate,
        heat_score=heat_score,
        top_channel=top_channel,
        warnings=warnings,
    )


# ---------- Track Performance ----------


def aggregate_track_performance(
    track_id: UUID,
    events: list[AnalyticsEvent],
    title: str = "",
) -> TrackPerformance:
    """Aggregate events into a track performance summary.

    Viral score is a composite of shares, saves, and engagement velocity.
    Deterministic — same events always produce same result.
    """
    total_streams = 0.0
    saves = 0.0
    shares = 0.0

    source_values: dict[AnalyticsSource, float] = defaultdict(float)

    for event in events:
        if event.metric in (AnalyticsMetric.STREAMS, AnalyticsMetric.PLAYS):
            total_streams += event.value
        if event.metric == AnalyticsMetric.SAVES:
            saves += event.value
        if event.metric == AnalyticsMetric.SHARES:
            shares += event.value
        source_values[event.source] += event.value

    viral_score = calculate_viral_score(total_streams, saves, shares)

    top_platform = (
        max(source_values, key=source_values.get)  # type: ignore[arg-type]
        if source_values
        else None
    )

    return TrackPerformance(
        track_id=track_id,
        title=title,
        total_streams=total_streams,
        saves=saves,
        shares=shares,
        viral_score=viral_score,
        top_platform=top_platform,
    )


# ---------- Scoring ----------


def calculate_heat_score(reach: float, engagement: float, conversions: float) -> float:
    """Calculate campaign heat score (0-100).

    Formula: weighted composite of reach, engagement, and conversions.
    Reach is the base, engagement amplifies, conversions are the signal.
    Capped at 100.

    Deterministic. No randomness.
    """
    if reach == 0 and engagement == 0 and conversions == 0:
        return 0.0

    # Logarithmic dampening to prevent runaway scores
    import math

    reach_component = min(math.log1p(reach) * 5, 40)
    engagement_component = min(math.log1p(engagement) * 8, 35)
    conversion_component = min(math.log1p(conversions) * 12, 25)

    raw = reach_component + engagement_component + conversion_component
    return round(min(raw, 100.0), 2)


def calculate_viral_score(streams: float, saves: float, shares: float) -> float:
    """Calculate track viral score (0-100).

    Shares and saves weighted heavily. Raw streams are the base.
    Capped at 100.

    Deterministic. No randomness.
    """
    if streams == 0 and saves == 0 and shares == 0:
        return 0.0

    import math

    stream_component = min(math.log1p(streams) * 4, 30)
    save_component = min(math.log1p(saves) * 10, 35)
    share_component = min(math.log1p(shares) * 12, 35)

    raw = stream_component + save_component + share_component
    return round(min(raw, 100.0), 2)


# ---------- Breakdowns ----------


def build_source_breakdown(
    events: list[AnalyticsEvent],
) -> list[ChannelPerformance]:
    """Build per-source performance breakdown."""
    groups: dict[AnalyticsSource, list[AnalyticsEvent]] = defaultdict(list)
    for event in events:
        groups[event.source].append(event)

    result: list[ChannelPerformance] = []
    for source, source_events in sorted(groups.items(), key=lambda x: x[0].value):
        total_value = sum(e.value for e in source_events)

        # Find top metric by total value
        metric_totals: dict[AnalyticsMetric, float] = defaultdict(float)
        for event in source_events:
            metric_totals[event.metric] += event.value

        top_metric = (
            max(metric_totals, key=metric_totals.get)  # type: ignore[arg-type]
            if metric_totals
            else None
        )
        top_metric_value = metric_totals[top_metric] if top_metric else 0.0

        result.append(
            ChannelPerformance(
                source=source,
                total_events=len(source_events),
                total_value=total_value,
                top_metric=top_metric,
                top_metric_value=top_metric_value,
            )
        )

    return result


def build_metric_breakdown(
    events: list[AnalyticsEvent],
) -> dict[str, float]:
    """Build per-metric total value breakdown."""
    totals: dict[str, float] = defaultdict(float)
    for event in events:
        totals[event.metric.value] += event.value
    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))


# ---------- Demo Seed ----------


def generate_demo_analytics_events(
    *,
    campaign_id: UUID | None = None,
    release_id: UUID | None = None,
    track_id: UUID | None = None,
) -> list[AnalyticsEvent]:
    """Generate deterministic demo analytics events for testing/dashboard population.

    NOT random. Uses fixed values so tests are reproducible.
    No real data. No API calls. Internal graph only.
    """
    if campaign_id is None:
        campaign_id = UUID("00000000-0000-4000-8000-000000000001")
    if release_id is None:
        release_id = UUID("00000000-0000-4000-8000-000000000002")
    if track_id is None:
        track_id = UUID("00000000-0000-4000-8000-000000000003")

    events: list[AnalyticsEvent] = []

    # SoundCloud events
    _demo_events = [
        (AnalyticsSource.SOUNDCLOUD, AnalyticsMetric.PLAYS, 1247),
        (AnalyticsSource.SOUNDCLOUD, AnalyticsMetric.LIKES, 89),
        (AnalyticsSource.SOUNDCLOUD, AnalyticsMetric.REPOSTS, 23),
        (AnalyticsSource.SOUNDCLOUD, AnalyticsMetric.COMMENTS, 14),
        (AnalyticsSource.SOUNDCLOUD, AnalyticsMetric.SAVES, 45),
        # Spotify events
        (AnalyticsSource.SPOTIFY, AnalyticsMetric.STREAMS, 3421),
        (AnalyticsSource.SPOTIFY, AnalyticsMetric.SAVES, 178),
        (AnalyticsSource.SPOTIFY, AnalyticsMetric.SHARES, 34),
        # TikTok events
        (AnalyticsSource.TIKTOK, AnalyticsMetric.VIEWS, 18500),
        (AnalyticsSource.TIKTOK, AnalyticsMetric.LIKES, 920),
        (AnalyticsSource.TIKTOK, AnalyticsMetric.SHARES, 156),
        (AnalyticsSource.TIKTOK, AnalyticsMetric.COMMENTS, 67),
        # Instagram events
        (AnalyticsSource.INSTAGRAM, AnalyticsMetric.VIEWS, 4200),
        (AnalyticsSource.INSTAGRAM, AnalyticsMetric.LIKES, 310),
        (AnalyticsSource.INSTAGRAM, AnalyticsMetric.ENGAGEMENT_RATE, 4.7),
        # Shopify events
        (AnalyticsSource.SHOPIFY, AnalyticsMetric.VIEWS, 890),
        (AnalyticsSource.SHOPIFY, AnalyticsMetric.CART_ADDS, 45),
        (AnalyticsSource.SHOPIFY, AnalyticsMetric.ORDERS, 12),
        (AnalyticsSource.SHOPIFY, AnalyticsMetric.REVENUE, 348.0),
        # Campaign-level event
        (AnalyticsSource.CAMPAIGN, AnalyticsMetric.CAMPAIGN_HEAT, 67.5),
        # Vinyl interest
        (AnalyticsSource.MANUAL, AnalyticsMetric.VINYL_INTEREST, 28),
        (AnalyticsSource.MANUAL, AnalyticsMetric.MERCH_INTEREST, 53),
    ]

    for i, (source, metric, value) in enumerate(_demo_events):
        events.append(
            AnalyticsEvent(
                event_id=UUID(f"00000000-0000-4000-8000-{i:012d}"),
                source=source,
                metric=metric,
                value=float(value),
                granularity=AnalyticsGranularity.DAILY,
                campaign_id=campaign_id,
                release_id=release_id,
                track_id=track_id
                if source
                in (
                    AnalyticsSource.SOUNDCLOUD,
                    AnalyticsSource.SPOTIFY,
                    AnalyticsSource.TIKTOK,
                )
                else None,
                timestamp=datetime(
                    2026,
                    5,
                    1 + (i % 15),
                    12,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
                metadata={"demo": "true", "seed_index": str(i)},
            )
        )

    return events
