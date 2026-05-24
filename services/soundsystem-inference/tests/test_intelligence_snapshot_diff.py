"""Tests — S55 Intelligence Snapshot Diff View.

Covers:
- safe_delta_percent zero behavior
- improved/declined/unchanged/mixed direction
- platform heatmap deltas
- viral moment appeared/disappeared/changed
- revenue delta
- warning changes
- compare_snapshots full integration
- route 404s
- route success
- deterministic ordering
- no external calls
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.intelligence_snapshot_diff import (
    compare_platform_heatmaps,
    compare_snapshots,
    compare_viral_moments,
    infer_snapshot_diff_direction,
    safe_delta_percent,
)
from app.schemas import (
    AnalyticsSource,
    AudienceHeatmap,
    CorrelationStrength,
    IntelligenceOverview,
    IntelligenceSnapshot,
    IntelligenceSnapshotDiff,
    RevenueCorrelation,
    SnapshotDiffDirection,
    SnapshotPlatformDelta,
    ViralMoment,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_overview(
    *,
    total_heat: float = 50.0,
    heatmaps: list[AudienceHeatmap] | None = None,
    viral_moments: list[ViralMoment] | None = None,
    revenue_correlations: list[RevenueCorrelation] | None = None,
    warnings: list[str] | None = None,
) -> IntelligenceOverview:
    return IntelligenceOverview(
        total_heat=total_heat,
        audience_heatmaps=heatmaps or [],
        viral_moments=viral_moments or [],
        revenue_correlations=revenue_correlations or [],
        warnings=warnings or [],
    )


def _make_snapshot(
    *,
    overview: IntelligenceOverview | None = None,
    event_count: int = 10,
) -> IntelligenceSnapshot:
    return IntelligenceSnapshot(
        snapshot_id=uuid4(),
        overview=overview or _make_overview(),
        event_count=event_count,
    )


def _make_heatmap(
    platform: AnalyticsSource,
    heat: float = 30.0,
    engagement: float = 100.0,
    conversion_rate: float = 2.0,
) -> AudienceHeatmap:
    return AudienceHeatmap(
        platform=platform,
        heat_score=heat,
        engagement=engagement,
        conversion_rate=conversion_rate,
    )


def _make_viral(
    title: str,
    strength: CorrelationStrength = CorrelationStrength.MEDIUM,
) -> ViralMoment:
    return ViralMoment(
        moment_id=uuid4(),
        title=title,
        source=AnalyticsSource.SPOTIFY,
        trigger_metric="streams",
        strength=strength,
    )


def _make_revenue(
    source: AnalyticsSource = AnalyticsSource.SHOPIFY,
    revenue: float = 500.0,
) -> RevenueCorrelation:
    return RevenueCorrelation(source=source, revenue=revenue)


# ---------------------------------------------------------------------------
# safe_delta_percent
# ---------------------------------------------------------------------------


class TestSafeDeltaPercent:
    def test_positive_change(self) -> None:
        assert safe_delta_percent(100, 150) == 50.0

    def test_negative_change(self) -> None:
        assert safe_delta_percent(200, 100) == -50.0

    def test_zero_before(self) -> None:
        assert safe_delta_percent(0, 100) is None

    def test_zero_both(self) -> None:
        assert safe_delta_percent(0, 0) is None

    def test_no_change(self) -> None:
        assert safe_delta_percent(100, 100) == 0.0

    def test_large_growth(self) -> None:
        result = safe_delta_percent(10, 1000)
        assert result == 9900.0


# ---------------------------------------------------------------------------
# Platform Heatmap Comparison
# ---------------------------------------------------------------------------


class TestPlatformHeatmapComparison:
    def test_same_platforms(self) -> None:
        before = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=30)])
        after = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=50)])
        deltas = compare_platform_heatmaps(before, after)
        assert len(deltas) == 1
        assert deltas[0].platform == AnalyticsSource.SPOTIFY
        assert deltas[0].heat_delta == 20.0
        assert deltas[0].direction == SnapshotDiffDirection.IMPROVED

    def test_platform_appeared(self) -> None:
        before = _make_overview(heatmaps=[])
        after = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.TIKTOK, heat=40)])
        deltas = compare_platform_heatmaps(before, after)
        assert len(deltas) == 1
        assert deltas[0].before_heat == 0.0
        assert deltas[0].after_heat == 40.0
        assert deltas[0].direction == SnapshotDiffDirection.IMPROVED

    def test_platform_disappeared(self) -> None:
        before = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SOUNDCLOUD, heat=25)])
        after = _make_overview(heatmaps=[])
        deltas = compare_platform_heatmaps(before, after)
        assert len(deltas) == 1
        assert deltas[0].heat_delta == -25.0
        assert deltas[0].direction == SnapshotDiffDirection.DECLINED

    def test_multiple_platforms_sorted_by_abs_delta(self) -> None:
        before = _make_overview(
            heatmaps=[
                _make_heatmap(AnalyticsSource.SPOTIFY, heat=50),
                _make_heatmap(AnalyticsSource.TIKTOK, heat=30),
            ]
        )
        after = _make_overview(
            heatmaps=[
                _make_heatmap(AnalyticsSource.SPOTIFY, heat=55),
                _make_heatmap(AnalyticsSource.TIKTOK, heat=10),
            ]
        )
        deltas = compare_platform_heatmaps(before, after)
        assert len(deltas) == 2
        # TikTok has |delta|=20, Spotify has |delta|=5
        assert deltas[0].platform == AnalyticsSource.TIKTOK
        assert deltas[1].platform == AnalyticsSource.SPOTIFY

    def test_empty_both(self) -> None:
        before = _make_overview(heatmaps=[])
        after = _make_overview(heatmaps=[])
        assert compare_platform_heatmaps(before, after) == []

    def test_unchanged_platform(self) -> None:
        before = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=30)])
        after = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=30)])
        deltas = compare_platform_heatmaps(before, after)
        assert deltas[0].direction == SnapshotDiffDirection.UNCHANGED

    def test_engagement_delta(self) -> None:
        before = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, engagement=100)])
        after = _make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, engagement=250)])
        deltas = compare_platform_heatmaps(before, after)
        assert deltas[0].engagement_delta == 150.0

    def test_conversion_delta(self) -> None:
        before = _make_overview(
            heatmaps=[_make_heatmap(AnalyticsSource.SHOPIFY, conversion_rate=2.0)]
        )
        after = _make_overview(
            heatmaps=[_make_heatmap(AnalyticsSource.SHOPIFY, conversion_rate=4.5)]
        )
        deltas = compare_platform_heatmaps(before, after)
        assert deltas[0].conversion_delta == 2.5


# ---------------------------------------------------------------------------
# Viral Moment Comparison
# ---------------------------------------------------------------------------


class TestViralMomentComparison:
    def test_moment_appeared(self) -> None:
        before = _make_overview(viral_moments=[])
        after = _make_overview(viral_moments=[_make_viral("TikTok spike +200%")])
        deltas = compare_viral_moments(before, after)
        assert len(deltas) == 1
        assert deltas[0].appeared is True
        assert deltas[0].disappeared is False
        assert deltas[0].direction == SnapshotDiffDirection.IMPROVED

    def test_moment_disappeared(self) -> None:
        before = _make_overview(viral_moments=[_make_viral("Spotify surge +150%")])
        after = _make_overview(viral_moments=[])
        deltas = compare_viral_moments(before, after)
        assert len(deltas) == 1
        assert deltas[0].disappeared is True
        assert deltas[0].direction == SnapshotDiffDirection.DECLINED

    def test_moment_strength_improved(self) -> None:
        before = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.WEAK)])
        after = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.STRONG)])
        deltas = compare_viral_moments(before, after)
        assert deltas[0].direction == SnapshotDiffDirection.IMPROVED

    def test_moment_strength_declined(self) -> None:
        before = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.EXPLOSIVE)])
        after = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.WEAK)])
        deltas = compare_viral_moments(before, after)
        assert deltas[0].direction == SnapshotDiffDirection.DECLINED

    def test_moment_unchanged(self) -> None:
        before = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.MEDIUM)])
        after = _make_overview(viral_moments=[_make_viral("Spike", CorrelationStrength.MEDIUM)])
        deltas = compare_viral_moments(before, after)
        assert deltas[0].direction == SnapshotDiffDirection.UNCHANGED

    def test_empty_both(self) -> None:
        before = _make_overview(viral_moments=[])
        after = _make_overview(viral_moments=[])
        assert compare_viral_moments(before, after) == []

    def test_sort_appeared_first(self) -> None:
        before = _make_overview(viral_moments=[_make_viral("Old spike")])
        after = _make_overview(viral_moments=[_make_viral("New spike")])
        deltas = compare_viral_moments(before, after)
        # "New spike" appeared, "Old spike" disappeared
        assert deltas[0].appeared is True
        assert deltas[1].disappeared is True


# ---------------------------------------------------------------------------
# Overall Direction
# ---------------------------------------------------------------------------


class TestOverallDirection:
    def test_all_improved(self) -> None:
        pd = [
            SnapshotPlatformDelta(
                platform=AnalyticsSource.SPOTIFY,
                heat_delta=10,
                direction=SnapshotDiffDirection.IMPROVED,
            )
        ]
        result = infer_snapshot_diff_direction(5.0, pd, [])
        assert result == SnapshotDiffDirection.IMPROVED

    def test_all_declined(self) -> None:
        pd = [
            SnapshotPlatformDelta(
                platform=AnalyticsSource.SPOTIFY,
                heat_delta=-10,
                direction=SnapshotDiffDirection.DECLINED,
            )
        ]
        result = infer_snapshot_diff_direction(-5.0, pd, [])
        assert result == SnapshotDiffDirection.DECLINED

    def test_mixed_signals(self) -> None:
        pd = [
            SnapshotPlatformDelta(
                platform=AnalyticsSource.SPOTIFY,
                heat_delta=10,
                direction=SnapshotDiffDirection.IMPROVED,
            ),
            SnapshotPlatformDelta(
                platform=AnalyticsSource.TIKTOK,
                heat_delta=-5,
                direction=SnapshotDiffDirection.DECLINED,
            ),
        ]
        result = infer_snapshot_diff_direction(5.0, pd, [])
        assert result == SnapshotDiffDirection.MIXED

    def test_no_signals_unchanged(self) -> None:
        result = infer_snapshot_diff_direction(0.0, [], [])
        assert result == SnapshotDiffDirection.UNCHANGED


# ---------------------------------------------------------------------------
# Full compare_snapshots
# ---------------------------------------------------------------------------


class TestCompareSnapshots:
    def test_basic_diff(self) -> None:
        before = _make_snapshot(overview=_make_overview(total_heat=40.0))
        after = _make_snapshot(overview=_make_overview(total_heat=60.0))
        diff = compare_snapshots(before, after)
        assert isinstance(diff, IntelligenceSnapshotDiff)
        assert diff.before_snapshot_id == before.snapshot_id
        assert diff.after_snapshot_id == after.snapshot_id
        assert diff.total_heat_delta == 20.0
        assert diff.total_heat_delta_percent == 50.0

    def test_declined_heat(self) -> None:
        before = _make_snapshot(overview=_make_overview(total_heat=80.0))
        after = _make_snapshot(overview=_make_overview(total_heat=60.0))
        diff = compare_snapshots(before, after)
        assert diff.total_heat_delta == -20.0
        assert diff.total_heat_delta_percent == -25.0

    def test_zero_before_heat(self) -> None:
        before = _make_snapshot(overview=_make_overview(total_heat=0.0))
        after = _make_snapshot(overview=_make_overview(total_heat=50.0))
        diff = compare_snapshots(before, after)
        assert diff.total_heat_delta == 50.0
        assert diff.total_heat_delta_percent is None

    def test_with_platforms(self) -> None:
        before = _make_snapshot(
            overview=_make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=30)])
        )
        after = _make_snapshot(
            overview=_make_overview(heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=50)])
        )
        diff = compare_snapshots(before, after)
        assert len(diff.platform_deltas) == 1
        assert diff.platform_deltas[0].heat_delta == 20.0

    def test_with_revenue(self) -> None:
        before = _make_snapshot(
            overview=_make_overview(revenue_correlations=[_make_revenue(revenue=500)])
        )
        after = _make_snapshot(
            overview=_make_overview(revenue_correlations=[_make_revenue(revenue=800)])
        )
        diff = compare_snapshots(before, after)
        assert diff.revenue_delta is not None
        assert diff.revenue_delta.delta == 300.0

    def test_no_revenue_both(self) -> None:
        diff = compare_snapshots(_make_snapshot(), _make_snapshot())
        assert diff.revenue_delta is None

    def test_warning_changes(self) -> None:
        before = _make_snapshot(overview=_make_overview(warnings=["Low event count"]))
        after = _make_snapshot(overview=_make_overview(warnings=["No revenue data"]))
        diff = compare_snapshots(before, after)
        assert any("+ No revenue data" in w for w in diff.warning_changes)
        assert any("- Low event count" in w for w in diff.warning_changes)

    def test_deterministic(self) -> None:
        before = _make_snapshot(
            overview=_make_overview(
                total_heat=40.0,
                heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=30)],
            )
        )
        after = _make_snapshot(
            overview=_make_overview(
                total_heat=60.0,
                heatmaps=[_make_heatmap(AnalyticsSource.SPOTIFY, heat=50)],
            )
        )
        d1 = compare_snapshots(before, after)
        d2 = compare_snapshots(before, after)
        assert d1.total_heat_delta == d2.total_heat_delta
        assert d1.overall_direction == d2.overall_direction
        assert len(d1.platform_deltas) == len(d2.platform_deltas)

    def test_generated_at_present(self) -> None:
        diff = compare_snapshots(_make_snapshot(), _make_snapshot())
        assert diff.generated_at is not None


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------


class TestDiffRoute:
    def test_diff_route_both_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_intelligence_snapshot,
            get_intelligence_snapshot_diff,
        )

        s1 = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        s2 = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        diff = asyncio.run(get_intelligence_snapshot_diff(s1.snapshot_id, s2.snapshot_id))
        assert isinstance(diff, IntelligenceSnapshotDiff)
        assert diff.before_snapshot_id == s1.snapshot_id
        assert diff.after_snapshot_id == s2.snapshot_id

    def test_diff_route_before_not_found(self) -> None:
        from fastapi import HTTPException

        from app.auth import DEV_OPERATOR
        from app.main import (
            create_intelligence_snapshot,
            get_intelligence_snapshot_diff,
        )

        s = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_intelligence_snapshot_diff(uuid4(), s.snapshot_id))
        assert exc_info.value.status_code == 404
        assert "before" in exc_info.value.detail

    def test_diff_route_after_not_found(self) -> None:
        from fastapi import HTTPException

        from app.auth import DEV_OPERATOR
        from app.main import (
            create_intelligence_snapshot,
            get_intelligence_snapshot_diff,
        )

        s = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_intelligence_snapshot_diff(s.snapshot_id, uuid4()))
        assert exc_info.value.status_code == 404
        assert "after" in exc_info.value.detail

    def test_diff_route_both_not_found(self) -> None:
        from fastapi import HTTPException

        from app.main import get_intelligence_snapshot_diff

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_intelligence_snapshot_diff(uuid4(), uuid4()))
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# No external calls
# ---------------------------------------------------------------------------


class TestNoExternalCalls:
    def test_no_http_imports(self) -> None:
        import inspect

        from app import intelligence_snapshot_diff

        source = inspect.getsource(intelligence_snapshot_diff)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_ml_imports(self) -> None:
        import inspect

        from app import intelligence_snapshot_diff

        source = inspect.getsource(intelligence_snapshot_diff)
        assert "sklearn" not in source
        assert "tensorflow" not in source
        assert "torch" not in source
