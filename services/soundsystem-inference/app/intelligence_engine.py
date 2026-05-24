"""Intelligence Engine — S50 correlation layer.

Pure, deterministic functions for detecting viral moments,
building audience heatmaps, revenue correlations, and timeline
fusion from the normalized analytics event graph.

No ML. No AI inference. No external calls. No predictive models.
No provider API calls. No automation execution.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    AnalyticsSource,
    AudienceHeatmap,
    CorrelationStrength,
    IntelligenceOverview,
    RevenueCorrelation,
    TimelineCorrelation,
    TrendDirection,
    ViralMoment,
)


# ---------- Viral Moment Detection ----------


def detect_viral_moments(
    events: list[AnalyticsEvent],
    *,
    threshold_percent: float = 50.0,
) -> list[ViralMoment]:
    """Detect viral spikes by comparing metric values across time windows.

    Groups events by (source, metric, track_id/release_id) and looks for
    jumps exceeding threshold_percent between consecutive values.

    Deterministic. No randomness. No ML.
    """
    # Group events by (source, metric) and sort by timestamp
    groups: dict[tuple[AnalyticsSource, AnalyticsMetric], list[AnalyticsEvent]] = defaultdict(list)
    for event in events:
        groups[(event.source, event.metric)].append(event)

    moments: list[ViralMoment] = []

    for (source, metric), group_events in groups.items():
        sorted_events = sorted(group_events, key=lambda e: e.timestamp)
        if len(sorted_events) < 2:
            continue

        for i in range(1, len(sorted_events)):
            before = sorted_events[i - 1]
            after = sorted_events[i]

            if before.value <= 0:
                continue

            growth = ((after.value - before.value) / before.value) * 100

            if growth < threshold_percent:
                continue

            strength = _growth_to_strength(growth)

            moments.append(
                ViralMoment(
                    moment_id=uuid4(),
                    title=f"{source.value.upper()} {metric.value} spike +{growth:.0f}%",
                    source=source,
                    trigger_metric=metric,
                    before_value=before.value,
                    after_value=after.value,
                    growth_percent=round(growth, 2),
                    timestamp=after.timestamp,
                    related_release_id=after.release_id,
                    related_campaign_id=after.campaign_id,
                    strength=strength,
                )
            )

    # Sort by growth_percent descending
    moments.sort(key=lambda m: m.growth_percent, reverse=True)
    return moments


# ---------- Audience Heatmap ----------


def build_audience_heatmaps(
    events: list[AnalyticsEvent],
) -> list[AudienceHeatmap]:
    """Build per-platform audience heat summaries.

    Audience size = sum of reach metrics (plays, streams, views).
    Engagement = sum of engagement metrics (likes, saves, shares, comments).
    Conversion rate = conversions / audience_size if both > 0.
    Heat score = log-damped composite of audience + engagement.

    Deterministic. No randomness.
    """
    reach_metrics = {
        AnalyticsMetric.PLAYS,
        AnalyticsMetric.STREAMS,
        AnalyticsMetric.VIEWS,
    }
    engagement_metrics = {
        AnalyticsMetric.LIKES,
        AnalyticsMetric.SAVES,
        AnalyticsMetric.SHARES,
        AnalyticsMetric.COMMENTS,
        AnalyticsMetric.REPOSTS,
    }
    conversion_metrics = {
        AnalyticsMetric.CONVERSIONS,
        AnalyticsMetric.ORDERS,
    }

    platforms: dict[AnalyticsSource, dict[str, float]] = defaultdict(
        lambda: {"audience": 0.0, "engagement": 0.0, "conversions": 0.0}
    )

    for event in events:
        bucket = platforms[event.source]
        if event.metric in reach_metrics:
            bucket["audience"] += event.value
        if event.metric in engagement_metrics:
            bucket["engagement"] += event.value
        if event.metric in conversion_metrics:
            bucket["conversions"] += event.value

    result: list[AudienceHeatmap] = []
    for platform, vals in sorted(platforms.items(), key=lambda x: x[0].value):
        audience = vals["audience"]
        engagement = vals["engagement"]
        conversions = vals["conversions"]

        conversion_rate = (conversions / audience * 100) if audience > 0 else 0.0

        heat = calculate_platform_heat(audience, engagement, conversions)
        trend = infer_trend_direction(audience, engagement)

        result.append(
            AudienceHeatmap(
                platform=platform,
                audience_size=audience,
                engagement=engagement,
                conversion_rate=round(conversion_rate, 2),
                heat_score=heat,
                trend=trend,
            )
        )

    # Sort by heat descending
    result.sort(key=lambda h: h.heat_score, reverse=True)
    return result


# ---------- Revenue Correlations ----------


def build_revenue_correlations(
    events: list[AnalyticsEvent],
) -> list[RevenueCorrelation]:
    """Build per-source revenue attribution.

    For each source with revenue events, find the most correlated
    non-revenue metric (highest co-occurrence).

    Deterministic. No ML.
    """
    revenue_by_source: dict[AnalyticsSource, float] = defaultdict(float)
    metric_by_source: dict[AnalyticsSource, dict[AnalyticsMetric, float]] = defaultdict(
        lambda: defaultdict(float)
    )

    revenue_metrics = {AnalyticsMetric.REVENUE, AnalyticsMetric.ORDERS}

    for event in events:
        if event.metric in revenue_metrics:
            revenue_by_source[event.source] += event.value
        else:
            metric_by_source[event.source][event.metric] += event.value

    result: list[RevenueCorrelation] = []
    for source, revenue in sorted(revenue_by_source.items(), key=lambda x: x[1], reverse=True):
        metrics = metric_by_source.get(source, {})
        related_metric = None
        related_value = 0.0
        if metrics:
            related_metric = max(metrics, key=metrics.get)  # type: ignore[arg-type]
            related_value = metrics[related_metric]

        strength = _revenue_to_strength(revenue)

        result.append(
            RevenueCorrelation(
                source=source,
                revenue=revenue,
                related_metric=related_metric,
                related_metric_value=related_value,
                conversion_strength=strength,
            )
        )

    return result


# ---------- Timeline Fusion ----------


def build_timeline_correlations(
    events: list[AnalyticsEvent],
) -> list[TimelineCorrelation]:
    """Build timeline fusion points by grouping events into daily buckets.

    Each point shows event density, dominant source/metric, and heat.

    Deterministic. No randomness.
    """
    # Group by date
    buckets: dict[str, list[AnalyticsEvent]] = defaultdict(list)
    for event in events:
        day_key = event.timestamp.strftime("%Y-%m-%d")
        buckets[day_key].append(event)

    result: list[TimelineCorrelation] = []
    for day_key in sorted(buckets.keys()):
        day_events = buckets[day_key]
        event_count = len(day_events)

        # Find dominant source
        source_totals: dict[AnalyticsSource, float] = defaultdict(float)
        metric_totals: dict[AnalyticsMetric, float] = defaultdict(float)
        for event in day_events:
            source_totals[event.source] += event.value
            metric_totals[event.metric] += event.value

        dominant_source = (
            max(source_totals, key=source_totals.get)  # type: ignore[arg-type]
            if source_totals
            else None
        )
        dominant_metric = (
            max(metric_totals, key=metric_totals.get)  # type: ignore[arg-type]
            if metric_totals
            else None
        )

        total_value = sum(e.value for e in day_events)
        heat = min(math.log1p(total_value) * 5, 100)

        ts = datetime.strptime(day_key, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        result.append(
            TimelineCorrelation(
                timestamp=ts,
                event_count=event_count,
                dominant_source=dominant_source,
                dominant_metric=dominant_metric,
                heat=round(heat, 2),
            )
        )

    return result


# ---------- Scoring ----------


def calculate_platform_heat(audience: float, engagement: float, conversions: float) -> float:
    """Calculate platform heat score (0-100).

    Logarithmic composite. Deterministic.
    """
    if audience == 0 and engagement == 0 and conversions == 0:
        return 0.0

    a = min(math.log1p(audience) * 4, 35)
    e = min(math.log1p(engagement) * 8, 40)
    c = min(math.log1p(conversions) * 12, 25)

    return round(min(a + e + c, 100.0), 2)


def infer_trend_direction(audience: float, engagement: float) -> TrendDirection:
    """Infer trend direction from audience/engagement ratio.

    Deterministic heuristic. No ML.
    """
    if audience == 0 and engagement == 0:
        return TrendDirection.STABLE

    if audience == 0:
        return TrendDirection.RISING

    ratio = engagement / audience if audience > 0 else 0

    if ratio > 0.15:
        return TrendDirection.EXPLODING
    if ratio > 0.05:
        return TrendDirection.RISING
    if ratio > 0.01:
        return TrendDirection.STABLE
    return TrendDirection.DOWN


# ---------- Intelligence Overview ----------


def build_intelligence_overview(
    events: list[AnalyticsEvent],
) -> IntelligenceOverview:
    """Build the full intelligence overview from all analytics events.

    Composes viral moments, audience heatmaps, revenue correlations,
    and timeline fusion into a single read-model object.

    Deterministic. No ML. No AI. No external calls.
    """
    if not events:
        return IntelligenceOverview(
            warnings=["No analytics events. Seed data or record events first."],
        )

    viral_moments = detect_viral_moments(events)
    audience_heatmaps = build_audience_heatmaps(events)
    revenue_correlations = build_revenue_correlations(events)
    timeline = build_timeline_correlations(events)

    # Compute total heat from all platforms
    total_heat = sum(h.heat_score for h in audience_heatmaps)
    total_heat = round(min(total_heat, 100.0), 2) if audience_heatmaps else 0.0

    # Hottest platform
    hottest_platform = audience_heatmaps[0].platform if audience_heatmaps else None

    # Hottest release: find the release_id with most event value
    release_values: dict[UUID, float] = defaultdict(float)
    campaign_values: dict[UUID, float] = defaultdict(float)
    for event in events:
        if event.release_id is not None:
            release_values[event.release_id] += event.value
        if event.campaign_id is not None:
            campaign_values[event.campaign_id] += event.value

    hottest_release_id = (
        max(release_values, key=release_values.get)  # type: ignore[arg-type]
        if release_values
        else None
    )
    hottest_campaign_id = (
        max(campaign_values, key=campaign_values.get)  # type: ignore[arg-type]
        if campaign_values
        else None
    )

    # Overall trend from dominant heatmap
    trend = audience_heatmaps[0].trend if audience_heatmaps else TrendDirection.STABLE

    # Warnings
    warnings: list[str] = []
    if len(events) < 10:
        warnings.append("Low event count — intelligence improves with more data.")
    if not revenue_correlations:
        warnings.append("No revenue data — commerce correlations unavailable.")
    if not viral_moments:
        warnings.append("No viral spikes detected in current data window.")

    return IntelligenceOverview(
        total_heat=total_heat,
        hottest_platform=hottest_platform,
        hottest_release_id=hottest_release_id,
        hottest_campaign_id=hottest_campaign_id,
        viral_moments=viral_moments[:10],  # Top 10
        audience_heatmaps=audience_heatmaps,
        revenue_correlations=revenue_correlations,
        timeline=timeline,
        trend=trend,
        warnings=warnings,
    )


# ---------- Helpers ----------


def _growth_to_strength(growth_percent: float) -> CorrelationStrength:
    """Map growth percentage to correlation strength."""
    if growth_percent >= 500:
        return CorrelationStrength.EXPLOSIVE
    if growth_percent >= 200:
        return CorrelationStrength.STRONG
    if growth_percent >= 100:
        return CorrelationStrength.MEDIUM
    return CorrelationStrength.WEAK


def _revenue_to_strength(revenue: float) -> CorrelationStrength:
    """Map revenue amount to correlation strength."""
    if revenue >= 10000:
        return CorrelationStrength.EXPLOSIVE
    if revenue >= 1000:
        return CorrelationStrength.STRONG
    if revenue >= 100:
        return CorrelationStrength.MEDIUM
    return CorrelationStrength.WEAK
