"""Tests for S49 — Analytics Event Graph Foundation.

Covers:
- AnalyticsEvent schema validation
- InMemoryAnalyticsRepository CRUD
- Aggregation: campaign performance, track performance
- Heat score calculation
- Viral score calculation
- Source/metric breakdowns
- Demo seed generation
- Routes: event creation, listing, summary, campaign/track perf, demo seed
- No external API calls
- Existing tests remain green
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4


from app.analytics_graph import (
    aggregate_campaign_performance,
    aggregate_track_performance,
    build_metric_breakdown,
    build_source_breakdown,
    calculate_heat_score,
    calculate_viral_score,
    generate_demo_analytics_events,
)
from app.analytics_repository import InMemoryAnalyticsRepository
from app.schemas import (
    AnalyticsEvent,
    AnalyticsEventCreateRequest,
    AnalyticsGranularity,
    AnalyticsMetric,
    AnalyticsSource,
    AnalyticsSummary,
    CampaignPerformance,
    TrackPerformance,
)


# ---------- Helpers ----------


def _make_event(
    *,
    source: AnalyticsSource = AnalyticsSource.SOUNDCLOUD,
    metric: AnalyticsMetric = AnalyticsMetric.PLAYS,
    value: float = 100.0,
    campaign_id: UUID | None = None,
    track_id: UUID | None = None,
    release_id: UUID | None = None,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_id=uuid4(),
        source=source,
        metric=metric,
        value=value,
        granularity=AnalyticsGranularity.DAILY,
        campaign_id=campaign_id,
        track_id=track_id,
        release_id=release_id,
    )


# ---------- Repository tests ----------


class TestInMemoryAnalyticsRepository:
    def test_add_and_list(self) -> None:
        repo = InMemoryAnalyticsRepository()
        event = _make_event()
        repo.add_event(event)
        events = repo.list_events()
        assert len(events) == 1
        assert events[0].event_id == event.event_id

    def test_add_events_batch(self) -> None:
        repo = InMemoryAnalyticsRepository()
        events = [_make_event() for _ in range(5)]
        repo.add_events(events)
        assert len(repo.list_events()) == 5

    def test_filter_by_source(self) -> None:
        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(source=AnalyticsSource.SOUNDCLOUD))
        repo.add_event(_make_event(source=AnalyticsSource.SPOTIFY))
        repo.add_event(_make_event(source=AnalyticsSource.TIKTOK))
        result = repo.list_events(source=AnalyticsSource.SPOTIFY)
        assert len(result) == 1
        assert result[0].source == AnalyticsSource.SPOTIFY

    def test_filter_by_metric(self) -> None:
        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(metric=AnalyticsMetric.PLAYS))
        repo.add_event(_make_event(metric=AnalyticsMetric.SAVES))
        result = repo.list_events(metric=AnalyticsMetric.SAVES)
        assert len(result) == 1

    def test_filter_by_campaign_id(self) -> None:
        repo = InMemoryAnalyticsRepository()
        cid = uuid4()
        repo.add_event(_make_event(campaign_id=cid))
        repo.add_event(_make_event(campaign_id=uuid4()))
        result = repo.list_events(campaign_id=cid)
        assert len(result) == 1

    def test_filter_by_track_id(self) -> None:
        repo = InMemoryAnalyticsRepository()
        tid = uuid4()
        repo.add_event(_make_event(track_id=tid))
        repo.add_event(_make_event(track_id=uuid4()))
        result = repo.list_events(track_id=tid)
        assert len(result) == 1

    def test_limit(self) -> None:
        repo = InMemoryAnalyticsRepository()
        for _ in range(10):
            repo.add_event(_make_event())
        result = repo.list_events(limit=3)
        assert len(result) == 3

    def test_get_campaign_events(self) -> None:
        repo = InMemoryAnalyticsRepository()
        cid = uuid4()
        repo.add_event(_make_event(campaign_id=cid))
        repo.add_event(_make_event(campaign_id=cid))
        repo.add_event(_make_event(campaign_id=uuid4()))
        assert len(repo.get_campaign_events(cid)) == 2

    def test_get_track_events(self) -> None:
        repo = InMemoryAnalyticsRepository()
        tid = uuid4()
        repo.add_event(_make_event(track_id=tid))
        repo.add_event(_make_event(track_id=uuid4()))
        assert len(repo.get_track_events(tid)) == 1

    def test_summary(self) -> None:
        repo = InMemoryAnalyticsRepository()
        cid = uuid4()
        tid = uuid4()
        repo.add_event(
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                metric=AnalyticsMetric.PLAYS,
                campaign_id=cid,
                track_id=tid,
            )
        )
        repo.add_event(
            _make_event(
                source=AnalyticsSource.SPOTIFY,
                metric=AnalyticsMetric.STREAMS,
                campaign_id=cid,
            )
        )
        summary = repo.summary()
        assert summary.total_events == 2
        assert summary.total_campaigns == 1
        assert summary.total_tracks == 1
        assert summary.source_breakdown["soundcloud"] == 1
        assert summary.source_breakdown["spotify"] == 1
        assert summary.metric_breakdown["plays"] == 1
        assert summary.latest_event_at is not None

    def test_mode(self) -> None:
        repo = InMemoryAnalyticsRepository()
        assert repo.mode == "in_memory"


# ---------- Aggregation tests ----------


class TestCampaignPerformance:
    def test_basic_aggregation(self) -> None:
        cid = uuid4()
        events = [
            _make_event(metric=AnalyticsMetric.PLAYS, value=1000, campaign_id=cid),
            _make_event(metric=AnalyticsMetric.LIKES, value=50, campaign_id=cid),
            _make_event(metric=AnalyticsMetric.CONVERSIONS, value=5, campaign_id=cid),
            _make_event(metric=AnalyticsMetric.REVENUE, value=100, campaign_id=cid),
        ]
        perf = aggregate_campaign_performance(cid, events)
        assert perf.campaign_id == cid
        assert perf.total_reach == 1000
        assert perf.engagement == 50
        assert perf.conversions == 5
        assert perf.revenue_estimate == 100
        assert perf.heat_score > 0

    def test_empty_events(self) -> None:
        cid = uuid4()
        perf = aggregate_campaign_performance(cid, [])
        assert perf.total_reach == 0
        assert perf.heat_score == 0
        assert "No reach data" in perf.warnings[0]

    def test_reach_only_warns(self) -> None:
        cid = uuid4()
        events = [
            _make_event(metric=AnalyticsMetric.VIEWS, value=5000, campaign_id=cid),
        ]
        perf = aggregate_campaign_performance(cid, events)
        assert perf.total_reach == 5000
        assert any("without engagement" in w for w in perf.warnings)

    def test_top_channel(self) -> None:
        cid = uuid4()
        events = [
            _make_event(
                source=AnalyticsSource.TIKTOK,
                metric=AnalyticsMetric.VIEWS,
                value=10000,
                campaign_id=cid,
            ),
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                metric=AnalyticsMetric.PLAYS,
                value=500,
                campaign_id=cid,
            ),
        ]
        perf = aggregate_campaign_performance(cid, events)
        assert perf.top_channel == AnalyticsSource.TIKTOK


class TestTrackPerformance:
    def test_basic_aggregation(self) -> None:
        tid = uuid4()
        events = [
            _make_event(metric=AnalyticsMetric.STREAMS, value=3000, track_id=tid),
            _make_event(metric=AnalyticsMetric.SAVES, value=150, track_id=tid),
            _make_event(metric=AnalyticsMetric.SHARES, value=30, track_id=tid),
        ]
        perf = aggregate_track_performance(tid, events, title="TEST TRACK")
        assert perf.track_id == tid
        assert perf.title == "TEST TRACK"
        assert perf.total_streams == 3000
        assert perf.saves == 150
        assert perf.shares == 30
        assert perf.viral_score > 0

    def test_empty_events(self) -> None:
        tid = uuid4()
        perf = aggregate_track_performance(tid, [])
        assert perf.total_streams == 0
        assert perf.viral_score == 0

    def test_top_platform(self) -> None:
        tid = uuid4()
        events = [
            _make_event(
                source=AnalyticsSource.SPOTIFY,
                metric=AnalyticsMetric.STREAMS,
                value=5000,
                track_id=tid,
            ),
            _make_event(
                source=AnalyticsSource.SOUNDCLOUD,
                metric=AnalyticsMetric.PLAYS,
                value=800,
                track_id=tid,
            ),
        ]
        perf = aggregate_track_performance(tid, events)
        assert perf.top_platform == AnalyticsSource.SPOTIFY


# ---------- Scoring tests ----------


class TestHeatScore:
    def test_zero_input(self) -> None:
        assert calculate_heat_score(0, 0, 0) == 0.0

    def test_positive_score(self) -> None:
        score = calculate_heat_score(1000, 100, 10)
        assert score > 0
        assert score <= 100

    def test_capped_at_100(self) -> None:
        score = calculate_heat_score(1_000_000, 500_000, 100_000)
        assert score <= 100

    def test_deterministic(self) -> None:
        s1 = calculate_heat_score(500, 50, 5)
        s2 = calculate_heat_score(500, 50, 5)
        assert s1 == s2

    def test_more_engagement_higher_score(self) -> None:
        low = calculate_heat_score(1000, 10, 0)
        high = calculate_heat_score(1000, 500, 0)
        assert high > low


class TestViralScore:
    def test_zero_input(self) -> None:
        assert calculate_viral_score(0, 0, 0) == 0.0

    def test_positive_score(self) -> None:
        score = calculate_viral_score(3000, 150, 30)
        assert score > 0
        assert score <= 100

    def test_capped_at_100(self) -> None:
        score = calculate_viral_score(1_000_000, 500_000, 100_000)
        assert score <= 100

    def test_deterministic(self) -> None:
        s1 = calculate_viral_score(1000, 100, 20)
        s2 = calculate_viral_score(1000, 100, 20)
        assert s1 == s2

    def test_more_shares_higher_score(self) -> None:
        low = calculate_viral_score(1000, 100, 5)
        high = calculate_viral_score(1000, 100, 500)
        assert high > low


# ---------- Breakdown tests ----------


class TestSourceBreakdown:
    def test_groups_by_source(self) -> None:
        events = [
            _make_event(source=AnalyticsSource.SOUNDCLOUD, value=100),
            _make_event(source=AnalyticsSource.SOUNDCLOUD, value=200),
            _make_event(source=AnalyticsSource.SPOTIFY, value=500),
        ]
        breakdown = build_source_breakdown(events)
        assert len(breakdown) == 2
        sc = next(c for c in breakdown if c.source == AnalyticsSource.SOUNDCLOUD)
        assert sc.total_events == 2
        assert sc.total_value == 300

    def test_empty_events(self) -> None:
        assert build_source_breakdown([]) == []


class TestMetricBreakdown:
    def test_groups_by_metric(self) -> None:
        events = [
            _make_event(metric=AnalyticsMetric.PLAYS, value=100),
            _make_event(metric=AnalyticsMetric.PLAYS, value=200),
            _make_event(metric=AnalyticsMetric.SAVES, value=50),
        ]
        breakdown = build_metric_breakdown(events)
        assert breakdown["plays"] == 300
        assert breakdown["saves"] == 50

    def test_sorted_by_value(self) -> None:
        events = [
            _make_event(metric=AnalyticsMetric.SAVES, value=50),
            _make_event(metric=AnalyticsMetric.PLAYS, value=300),
        ]
        breakdown = build_metric_breakdown(events)
        keys = list(breakdown.keys())
        assert keys[0] == "plays"  # Higher value first


# ---------- Demo seed tests ----------


class TestDemoSeed:
    def test_generates_events(self) -> None:
        events = generate_demo_analytics_events()
        assert len(events) > 0
        assert len(events) == 22  # Fixed count

    def test_deterministic(self) -> None:
        e1 = generate_demo_analytics_events()
        e2 = generate_demo_analytics_events()
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.event_id == b.event_id
            assert a.source == b.source
            assert a.metric == b.metric
            assert a.value == b.value

    def test_multiple_sources(self) -> None:
        events = generate_demo_analytics_events()
        sources = {e.source for e in events}
        assert AnalyticsSource.SOUNDCLOUD in sources
        assert AnalyticsSource.SPOTIFY in sources
        assert AnalyticsSource.TIKTOK in sources
        assert AnalyticsSource.SHOPIFY in sources

    def test_custom_ids(self) -> None:
        cid = uuid4()
        events = generate_demo_analytics_events(campaign_id=cid)
        assert all(e.campaign_id == cid for e in events)


# ---------- Route tests ----------


class TestAnalyticsRoutes:
    def test_create_event(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_analytics_event

        req = AnalyticsEventCreateRequest(
            source=AnalyticsSource.SOUNDCLOUD,
            metric=AnalyticsMetric.PLAYS,
            value=500,
        )
        result = asyncio.run(create_analytics_event(req, DEV_OPERATOR))
        assert result.source == AnalyticsSource.SOUNDCLOUD
        assert result.value == 500

    def test_list_events(self) -> None:
        from app.main import list_analytics_events

        result = asyncio.run(list_analytics_events())
        assert isinstance(result, list)

    def test_summary(self) -> None:
        from app.main import get_analytics_summary

        result = asyncio.run(get_analytics_summary())
        assert isinstance(result, AnalyticsSummary)
        assert result.total_events >= 0

    def test_campaign_performance(self) -> None:
        from app.main import get_campaign_performance

        cid = uuid4()
        result = asyncio.run(get_campaign_performance(cid))
        assert isinstance(result, CampaignPerformance)
        assert result.campaign_id == cid

    def test_track_performance(self) -> None:
        from app.main import get_track_performance

        tid = uuid4()
        result = asyncio.run(get_track_performance(tid))
        assert isinstance(result, TrackPerformance)
        assert result.track_id == tid

    def test_demo_seed(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import seed_demo_analytics

        events = asyncio.run(seed_demo_analytics(DEV_OPERATOR))
        assert len(events) == 22

    def test_channels_endpoint(self) -> None:
        from app.main import get_analytics_channels

        result = asyncio.run(get_analytics_channels())
        assert isinstance(result, list)


# ---------- Capabilities test ----------


class TestAnalyticsCapabilities:
    def test_analytics_graph_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.analytics_graph_available is True


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_repository(self) -> None:
        import inspect

        from app import analytics_repository

        source = inspect.getsource(analytics_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_http_imports_in_graph(self) -> None:
        import inspect

        from app import analytics_graph

        source = inspect.getsource(analytics_graph)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
