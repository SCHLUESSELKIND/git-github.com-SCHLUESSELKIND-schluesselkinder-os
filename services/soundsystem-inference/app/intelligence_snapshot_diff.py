"""Intelligence Snapshot Diff — S55 comparison engine.

Pure, deterministic functions for comparing two IntelligenceSnapshots.
No external calls. No persistence. No automation. Read-only.
"""

from __future__ import annotations

from app.schemas import (
    AnalyticsSource,
    AudienceHeatmap,
    CorrelationStrength,
    IntelligenceOverview,
    IntelligenceSnapshot,
    IntelligenceSnapshotDiff,
    SnapshotDiffDirection,
    SnapshotMetricDelta,
    SnapshotPlatformDelta,
    SnapshotViralMomentDelta,
    ViralMoment,
)


def safe_delta_percent(before: float, after: float) -> float | None:
    """Compute percentage change. Returns None if before is zero."""
    if before == 0:
        return None
    return round(((after - before) / before) * 100, 2)


def _value_direction(delta: float) -> SnapshotDiffDirection:
    """Map a numeric delta to a direction."""
    if delta > 0:
        return SnapshotDiffDirection.IMPROVED
    if delta < 0:
        return SnapshotDiffDirection.DECLINED
    return SnapshotDiffDirection.UNCHANGED


def _strength_rank(s: CorrelationStrength) -> int:
    """Rank correlation strengths for comparison."""
    return {"weak": 0, "medium": 1, "strong": 2, "explosive": 3}.get(s.value, 0)


# ---------- Platform Heatmap Comparison ----------


def compare_platform_heatmaps(
    before_overview: IntelligenceOverview,
    after_overview: IntelligenceOverview,
) -> list[SnapshotPlatformDelta]:
    """Compare per-platform audience heatmaps between two overviews.

    Produces a delta for every platform that appears in either snapshot.
    Sorted by absolute heat_delta descending.
    Deterministic. No external calls.
    """
    before_map: dict[AnalyticsSource, AudienceHeatmap] = {
        h.platform: h for h in before_overview.audience_heatmaps
    }
    after_map: dict[AnalyticsSource, AudienceHeatmap] = {
        h.platform: h for h in after_overview.audience_heatmaps
    }

    all_platforms = sorted(
        set(before_map.keys()) | set(after_map.keys()),
        key=lambda p: p.value,
    )

    deltas: list[SnapshotPlatformDelta] = []
    for platform in all_platforms:
        bh = before_map.get(platform)
        ah = after_map.get(platform)

        before_heat = bh.heat_score if bh else 0.0
        after_heat = ah.heat_score if ah else 0.0
        heat_delta = round(after_heat - before_heat, 2)

        before_eng = bh.engagement if bh else 0.0
        after_eng = ah.engagement if ah else 0.0
        engagement_delta = round(after_eng - before_eng, 2)

        before_cvr = bh.conversion_rate if bh else 0.0
        after_cvr = ah.conversion_rate if ah else 0.0
        conversion_delta = round(after_cvr - before_cvr, 2)

        deltas.append(
            SnapshotPlatformDelta(
                platform=platform,
                before_heat=before_heat,
                after_heat=after_heat,
                heat_delta=heat_delta,
                direction=_value_direction(heat_delta),
                engagement_delta=engagement_delta,
                conversion_delta=conversion_delta,
            )
        )

    # Sort by absolute heat delta descending
    deltas.sort(key=lambda d: abs(d.heat_delta), reverse=True)
    return deltas


# ---------- Viral Moment Comparison ----------


def compare_viral_moments(
    before_overview: IntelligenceOverview,
    after_overview: IntelligenceOverview,
) -> list[SnapshotViralMomentDelta]:
    """Compare viral moments between two overviews.

    Tracks appeared, disappeared, and changed-strength moments.
    Matched by title. Sorted: appeared first, then disappeared, then changed.
    Deterministic. No external calls.
    """
    before_by_title: dict[str, ViralMoment] = {m.title: m for m in before_overview.viral_moments}
    after_by_title: dict[str, ViralMoment] = {m.title: m for m in after_overview.viral_moments}

    all_titles = sorted(set(before_by_title.keys()) | set(after_by_title.keys()))

    deltas: list[SnapshotViralMomentDelta] = []
    for title in all_titles:
        bm = before_by_title.get(title)
        am = after_by_title.get(title)

        appeared = bm is None and am is not None
        disappeared = bm is not None and am is None

        before_strength = bm.strength if bm else None
        after_strength = am.strength if am else None

        if appeared:
            direction = SnapshotDiffDirection.IMPROVED
        elif disappeared:
            direction = SnapshotDiffDirection.DECLINED
        elif before_strength and after_strength:
            br = _strength_rank(before_strength)
            ar = _strength_rank(after_strength)
            if ar > br:
                direction = SnapshotDiffDirection.IMPROVED
            elif ar < br:
                direction = SnapshotDiffDirection.DECLINED
            else:
                direction = SnapshotDiffDirection.UNCHANGED
        else:
            direction = SnapshotDiffDirection.UNCHANGED

        deltas.append(
            SnapshotViralMomentDelta(
                title=title,
                before_strength=before_strength,
                after_strength=after_strength,
                appeared=appeared,
                disappeared=disappeared,
                direction=direction,
            )
        )

    # Sort: appeared first, then disappeared, then by title
    deltas.sort(key=lambda d: (not d.appeared, not d.disappeared, d.title))
    return deltas


# ---------- Revenue Comparison ----------


def _compute_revenue_delta(
    before_overview: IntelligenceOverview,
    after_overview: IntelligenceOverview,
) -> SnapshotMetricDelta | None:
    """Compare total revenue between two overviews.

    Sums revenue from all RevenueCorrelation entries.
    Returns None if neither snapshot has revenue data.
    """
    before_rev = sum(rc.revenue for rc in before_overview.revenue_correlations)
    after_rev = sum(rc.revenue for rc in after_overview.revenue_correlations)

    if before_rev == 0 and after_rev == 0:
        return None

    delta = round(after_rev - before_rev, 2)

    return SnapshotMetricDelta(
        metric="revenue",
        before_value=before_rev,
        after_value=after_rev,
        delta=delta,
        delta_percent=safe_delta_percent(before_rev, after_rev),
        direction=_value_direction(delta),
    )


# ---------- Warning Comparison ----------


def _compute_warning_changes(
    before_overview: IntelligenceOverview,
    after_overview: IntelligenceOverview,
) -> list[str]:
    """Compute warning changes between two overviews."""
    before_set = set(before_overview.warnings)
    after_set = set(after_overview.warnings)

    changes: list[str] = []

    for w in sorted(after_set - before_set):
        changes.append(f"+ {w}")
    for w in sorted(before_set - after_set):
        changes.append(f"- {w}")

    return changes


# ---------- Overall Direction ----------


def infer_snapshot_diff_direction(
    heat_delta: float,
    platform_deltas: list[SnapshotPlatformDelta],
    viral_moment_deltas: list[SnapshotViralMomentDelta],
) -> SnapshotDiffDirection:
    """Infer overall direction from component deltas.

    Deterministic heuristic:
    - All positive → improved
    - All negative → declined
    - No change → unchanged
    - Mixed signals → mixed
    """
    signals: list[SnapshotDiffDirection] = []

    if heat_delta > 0:
        signals.append(SnapshotDiffDirection.IMPROVED)
    elif heat_delta < 0:
        signals.append(SnapshotDiffDirection.DECLINED)

    for pd in platform_deltas:
        if pd.direction != SnapshotDiffDirection.UNCHANGED:
            signals.append(pd.direction)

    for vmd in viral_moment_deltas:
        if vmd.direction != SnapshotDiffDirection.UNCHANGED:
            signals.append(vmd.direction)

    if not signals:
        return SnapshotDiffDirection.UNCHANGED

    unique = set(signals)
    if unique == {SnapshotDiffDirection.IMPROVED}:
        return SnapshotDiffDirection.IMPROVED
    if unique == {SnapshotDiffDirection.DECLINED}:
        return SnapshotDiffDirection.DECLINED
    return SnapshotDiffDirection.MIXED


# ---------- Main Entry Point ----------


def compare_snapshots(
    before: IntelligenceSnapshot,
    after: IntelligenceSnapshot,
) -> IntelligenceSnapshotDiff:
    """Compare two intelligence snapshots.

    Produces a deterministic diff with platform deltas, viral moment
    changes, revenue delta, warning changes, and overall direction.

    Pure function. No external calls. No persistence.
    """
    before_ov = before.overview
    after_ov = after.overview

    heat_delta = round(after_ov.total_heat - before_ov.total_heat, 2)
    heat_delta_pct = safe_delta_percent(before_ov.total_heat, after_ov.total_heat)

    platform_deltas = compare_platform_heatmaps(before_ov, after_ov)
    viral_deltas = compare_viral_moments(before_ov, after_ov)
    revenue_delta = _compute_revenue_delta(before_ov, after_ov)
    warning_changes = _compute_warning_changes(before_ov, after_ov)

    overall = infer_snapshot_diff_direction(heat_delta, platform_deltas, viral_deltas)

    return IntelligenceSnapshotDiff(
        before_snapshot_id=before.snapshot_id,
        after_snapshot_id=after.snapshot_id,
        before_created_at=before.created_at,
        after_created_at=after.created_at,
        overall_direction=overall,
        total_heat_delta=heat_delta,
        total_heat_delta_percent=heat_delta_pct,
        platform_deltas=platform_deltas,
        viral_moment_deltas=viral_deltas,
        revenue_delta=revenue_delta,
        warning_changes=warning_changes,
    )
