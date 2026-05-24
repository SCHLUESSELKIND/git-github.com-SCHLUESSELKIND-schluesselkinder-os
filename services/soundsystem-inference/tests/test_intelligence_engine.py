"""Tests for S50 — Intelligence Engine Correlation Layer.

Covers:
- Viral moment detection
- Audience heatmap construction
- Revenue correlation building
- Timeline fusion
- Platform heat scoring
- Trend direction inference
- Intelligence overview composition
- Growth/revenue strength mapping
- Routes: overview, viral-moments, heatmap, revenue, timeline
- Capabilities flag
- No external calls
- Deterministic outputs
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.intelligence_engine import (
    build_audience_heatmaps,
    build_intelligence_overview,
    build_revenue_correlations,
    build_timeline_correlations,
    calculate_platform_heat,
    detect_viral_moments,
    infer_trend_direction,
)
from app.schemas import (
    AnalyticsEvent,
    AnalyticsGranularity,
    AnalyticsMetric,
    AnalyticsSource,
    CorrelationStrength,
    IntelligenceOverview,
    TrendDirection,
)


# ---------- Helpers ----------


def _make_event(
    *,
    source: AnalyticsSource = AnalyticsSource.SOUNDCLOUD,
    metric: AnalyticsMetric = AnalyticsMetric.PLAYS,
    value: float = 100.0,
    campaign_id: UUID | None = None,
    release_id: UUID | None = None,
    track_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_id=uuid4(),
        source=source,
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        campaign_id=campaign_id,
        release_id=release_id,
        track_id=track_id,
        timestamp=timestamp or datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
    )


# ---------- Viral Moment Detection ----------


class TestViralMomentDetection:
    def test_detects_spike(self) -> None:
        events = [
            _make_event(
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=300,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events)
        assert len(moments) == 1
        assert moments[0].growth_percent == 200.0
        assert moments[0].strength == CorrelationStrength.STRONG

    def test_no_spike_below_threshold(self) -> None:
        events = [
            _make_event(
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=120,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events)
        assert len(moments) == 0

    def test_custom_threshold(self) -> None:
        events = [
            _make_event(
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=120,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events, threshold_percent=10.0)
        assert len(moments) == 1

    def test_ignores_zero_before_value(self) -> None:
        events = [
            _make_event(
                value=0,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=1000,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events)
        assert len(moments) == 0

    def test_sorted_by_growth_descending(self) -> None:
        events = [
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                value=200,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
            _make_event(
                source=AnalyticsSource.SPOTIFY,
                metric=AnalyticsMetric.STREAMS,
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                source=AnalyticsSource.SPOTIFY,
                metric=AnalyticsMetric.STREAMS,
                value=500,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events)
        assert len(moments) == 2
        assert moments[0].growth_percent > moments[1].growth_percent

    def test_empty_events(self) -> None:
        moments = detect_viral_moments([])
        assert moments == []

    def test_single_event_no_spike(self) -> None:
        events = [_make_event(value=500)]
        moments = detect_viral_moments(events)
        assert moments == []

    def test_explosive_strength(self) -> None:
        events = [
            _make_event(
                value=10,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=100,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        moments = detect_viral_moments(events)
        assert len(moments) == 1
        assert moments[0].growth_percent == 900.0
        assert moments[0].strength == CorrelationStrength.EXPLOSIVE

    def test_deterministic(self) -> None:
        events = [
            _make_event(
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                value=300,
                timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
        ]
        m1 = detect_viral_moments(events)
        m2 = detect_viral_moments(events)
        assert len(m1) == len(m2)
        assert m1[0].growth_percent == m2[0].growth_percent
        assert m1[0].strength == m2[0].strength


# ---------- Audience Heatmap ----------


class TestAudienceHeatmap:
    def test_builds_per_platform(self) -> None:
        events = [
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD, metric=AnalyticsMetric.PLAYS, value=1000
            ),
            _make_event(source=AnalyticsSource.SOUNDCLOUD, metric=AnalyticsMetric.LIKES, value=50),
            _make_event(source=AnalyticsSource.SPOTIFY, metric=AnalyticsMetric.STREAMS, value=3000),
        ]
        heatmaps = build_audience_heatmaps(events)
        assert len(heatmaps) == 2

    def test_audience_from_reach_metrics(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.TIKTOK, metric=AnalyticsMetric.VIEWS, value=10000),
            _make_event(source=AnalyticsSource.TIKTOK, metric=AnalyticsMetric.LIKES, value=500),
        ]
        heatmaps = build_audience_heatmaps(events)
        assert len(heatmaps) == 1
        assert heatmaps[0].audience_size == 10000
        assert heatmaps[0].engagement == 500

    def test_conversion_rate(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.VIEWS, value=1000),
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.ORDERS, value=50),
        ]
        heatmaps = build_audience_heatmaps(events)
        assert len(heatmaps) == 1
        assert heatmaps[0].conversion_rate == 5.0

    def test_sorted_by_heat_descending(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SOUNDCLOUD, metric=AnalyticsMetric.PLAYS, value=100),
            _make_event(source=AnalyticsSource.TIKTOK, metric=AnalyticsMetric.VIEWS, value=50000),
            _make_event(source=AnalyticsSource.TIKTOK, metric=AnalyticsMetric.LIKES, value=2000),
        ]
        heatmaps = build_audience_heatmaps(events)
        assert heatmaps[0].heat_score >= heatmaps[-1].heat_score

    def test_empty_events(self) -> None:
        assert build_audience_heatmaps([]) == []

    def test_heat_score_positive(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SPOTIFY, metric=AnalyticsMetric.STREAMS, value=5000),
        ]
        heatmaps = build_audience_heatmaps(events)
        assert heatmaps[0].heat_score > 0


# ---------- Revenue Correlations ----------


class TestRevenueCorrelations:
    def test_builds_per_source(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.REVENUE, value=500),
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.VIEWS, value=2000),
        ]
        correlations = build_revenue_correlations(events)
        assert len(correlations) == 1
        assert correlations[0].revenue == 500
        assert correlations[0].related_metric == AnalyticsMetric.VIEWS

    def test_no_revenue_events(self) -> None:
        events = [
            _make_event(metric=AnalyticsMetric.PLAYS, value=1000),
        ]
        correlations = build_revenue_correlations(events)
        assert correlations == []

    def test_sorted_by_revenue_descending(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.REVENUE, value=100),
            _make_event(source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.VIEWS, value=500),
            _make_event(source=AnalyticsSource.MANUAL, metric=AnalyticsMetric.REVENUE, value=1000),
            _make_event(
                source=AnalyticsSource.MANUAL, metric=AnalyticsMetric.MERCH_INTEREST, value=200
            ),
        ]
        correlations = build_revenue_correlations(events)
        assert len(correlations) == 2
        assert correlations[0].revenue >= correlations[1].revenue

    def test_strength_mapping(self) -> None:
        events = [
            _make_event(
                source=AnalyticsSource.SHOPIFY, metric=AnalyticsMetric.REVENUE, value=15000
            ),
        ]
        correlations = build_revenue_correlations(events)
        assert correlations[0].conversion_strength == CorrelationStrength.EXPLOSIVE

    def test_empty_events(self) -> None:
        assert build_revenue_correlations([]) == []


# ---------- Timeline Fusion ----------


class TestTimelineCorrelations:
    def test_groups_by_day(self) -> None:
        events = [
            _make_event(timestamp=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)),
            _make_event(timestamp=datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)),
            _make_event(timestamp=datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc)),
        ]
        timeline = build_timeline_correlations(events)
        assert len(timeline) == 2
        assert timeline[0].event_count == 2
        assert timeline[1].event_count == 1

    def test_sorted_chronologically(self) -> None:
        events = [
            _make_event(timestamp=datetime(2026, 5, 3, tzinfo=timezone.utc)),
            _make_event(timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc)),
        ]
        timeline = build_timeline_correlations(events)
        assert timeline[0].timestamp < timeline[1].timestamp

    def test_dominant_source(self) -> None:
        events = [
            _make_event(
                source=AnalyticsSource.TIKTOK,
                metric=AnalyticsMetric.VIEWS,
                value=10000,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                metric=AnalyticsMetric.PLAYS,
                value=100,
                timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ),
        ]
        timeline = build_timeline_correlations(events)
        assert timeline[0].dominant_source == AnalyticsSource.TIKTOK

    def test_heat_positive(self) -> None:
        events = [
            _make_event(value=5000, timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc)),
        ]
        timeline = build_timeline_correlations(events)
        assert timeline[0].heat > 0

    def test_empty_events(self) -> None:
        assert build_timeline_correlations([]) == []


# ---------- Platform Heat Scoring ----------


class TestPlatformHeat:
    def test_zero_input(self) -> None:
        assert calculate_platform_heat(0, 0, 0) == 0.0

    def test_positive_score(self) -> None:
        score = calculate_platform_heat(1000, 100, 10)
        assert score > 0
        assert score <= 100

    def test_capped_at_100(self) -> None:
        score = calculate_platform_heat(1_000_000, 500_000, 100_000)
        assert score <= 100

    def test_deterministic(self) -> None:
        s1 = calculate_platform_heat(500, 50, 5)
        s2 = calculate_platform_heat(500, 50, 5)
        assert s1 == s2

    def test_more_engagement_higher_score(self) -> None:
        low = calculate_platform_heat(1000, 10, 0)
        high = calculate_platform_heat(1000, 500, 0)
        assert high > low


# ---------- Trend Direction ----------


class TestTrendDirection:
    def test_zero_input_stable(self) -> None:
        assert infer_trend_direction(0, 0) == TrendDirection.STABLE

    def test_no_audience_rising(self) -> None:
        assert infer_trend_direction(0, 100) == TrendDirection.RISING

    def test_high_ratio_exploding(self) -> None:
        assert infer_trend_direction(1000, 200) == TrendDirection.EXPLODING

    def test_medium_ratio_rising(self) -> None:
        assert infer_trend_direction(1000, 80) == TrendDirection.RISING

    def test_low_ratio_stable(self) -> None:
        assert infer_trend_direction(1000, 15) == TrendDirection.STABLE

    def test_very_low_ratio_down(self) -> None:
        assert infer_trend_direction(10000, 50) == TrendDirection.DOWN


# ---------- Intelligence Overview ----------


class TestIntelligenceOverview:
    def test_empty_events(self) -> None:
        overview = build_intelligence_overview([])
        assert overview.total_heat == 0.0
        assert len(overview.warnings) > 0
        assert "No analytics events" in overview.warnings[0]

    def test_with_events(self) -> None:
        from app.analytics_graph import generate_demo_analytics_events

        events = generate_demo_analytics_events()
        overview = build_intelligence_overview(events)
        assert overview.total_heat > 0
        assert overview.hottest_platform is not None
        assert len(overview.audience_heatmaps) > 0
        assert len(overview.timeline) > 0

    def test_warns_low_event_count(self) -> None:
        events = [
            _make_event(value=100),
            _make_event(value=200),
        ]
        overview = build_intelligence_overview(events)
        assert any("Low event count" in w for w in overview.warnings)

    def test_warns_no_revenue(self) -> None:
        events = [
            _make_event(metric=AnalyticsMetric.PLAYS, value=100),
        ]
        overview = build_intelligence_overview(events)
        assert any("No revenue data" in w for w in overview.warnings)

    def test_viral_moments_capped_at_10(self) -> None:
        # Create many events with spikes across different sources/metrics
        events = []
        sources = [
            AnalyticsSource.SOUNDCLOUD,
            AnalyticsSource.SPOTIFY,
            AnalyticsSource.TIKTOK,
            AnalyticsSource.INSTAGRAM,
            AnalyticsSource.SHOPIFY,
            AnalyticsSource.MANUAL,
        ]
        metrics = [
            AnalyticsMetric.PLAYS,
            AnalyticsMetric.STREAMS,
            AnalyticsMetric.VIEWS,
        ]
        for i, source in enumerate(sources):
            for j, metric in enumerate(metrics):
                events.append(
                    _make_event(
                        source=source,
                        metric=metric,
                        value=10 + i,
                        timestamp=datetime(2026, 5, 1, tzinfo=timezone.utc),
                    )
                )
                events.append(
                    _make_event(
                        source=source,
                        metric=metric,
                        value=1000 * (i + 1) * (j + 1),
                        timestamp=datetime(2026, 5, 2, tzinfo=timezone.utc),
                    )
                )
        overview = build_intelligence_overview(events)
        assert len(overview.viral_moments) <= 10

    def test_deterministic(self) -> None:
        from app.analytics_graph import generate_demo_analytics_events

        events = generate_demo_analytics_events()
        o1 = build_intelligence_overview(events)
        o2 = build_intelligence_overview(events)
        assert o1.total_heat == o2.total_heat
        assert o1.hottest_platform == o2.hottest_platform
        assert o1.trend == o2.trend


# ---------- Route tests ----------


class TestIntelligenceRoutes:
    def test_overview(self) -> None:
        from app.main import get_intelligence_overview

        result = asyncio.run(get_intelligence_overview())
        assert isinstance(result, IntelligenceOverview)

    def test_viral_moments(self) -> None:
        from app.main import get_viral_moments

        result = asyncio.run(get_viral_moments())
        assert isinstance(result, list)

    def test_heatmap(self) -> None:
        from app.main import get_audience_heatmap

        result = asyncio.run(get_audience_heatmap())
        assert isinstance(result, list)

    def test_revenue(self) -> None:
        from app.main import get_revenue_correlations

        result = asyncio.run(get_revenue_correlations())
        assert isinstance(result, list)

    def test_timeline(self) -> None:
        from app.main import get_intelligence_timeline

        result = asyncio.run(get_intelligence_timeline())
        assert isinstance(result, list)


# ---------- Capabilities test ----------


class TestIntelligenceCapabilities:
    def test_intelligence_engine_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.intelligence_engine_available is True


# ---------- No external calls ----------


class TestNoExternalCallsIntelligence:
    def test_no_http_imports_in_engine(self) -> None:
        import inspect

        from app import intelligence_engine

        source = inspect.getsource(intelligence_engine)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_ml_imports_in_engine(self) -> None:
        import inspect

        from app import intelligence_engine

        source = inspect.getsource(intelligence_engine)
        assert "sklearn" not in source
        assert "tensorflow" not in source
        assert "torch" not in source
        assert "numpy" not in source
        assert "pandas" not in source
