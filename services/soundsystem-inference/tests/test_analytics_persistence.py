"""Tests — S53 Analytics Persistence.

Covers: config modes, factory, InMemory + Postgres repository,
build_analytics_repository(), backward compatibility with
existing InMemoryAnalyticsRepository consumers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.analytics_repository import (
    InMemoryAnalyticsRepository,
    PostgresAnalyticsRepository,
    build_analytics_repository,
)
from app.config import (
    ANALYTICS_REPOSITORY_ENV,
    AnalyticsRepositoryConfigError,
    AnalyticsRepositoryMode,
    analytics_repository_mode,
)
from app.schemas import AnalyticsEvent, AnalyticsMetric, AnalyticsSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    *,
    source: AnalyticsSource = AnalyticsSource.SPOTIFY,
    metric: AnalyticsMetric = AnalyticsMetric.STREAMS,
    value: float = 100.0,
    campaign_id=None,
    release_id=None,
    track_id=None,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_id=uuid4(),
        source=source,
        metric=metric,
        value=value,
        campaign_id=campaign_id,
        release_id=release_id,
        track_id=track_id,
        metadata={},
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestAnalyticsRepositoryConfig:
    """Config mode resolution."""

    def test_default_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ANALYTICS_REPOSITORY_ENV, raising=False)
        assert analytics_repository_mode() == AnalyticsRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "in_memory")
        assert analytics_repository_mode() == AnalyticsRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "postgres")
        assert analytics_repository_mode() == AnalyticsRepositoryMode.POSTGRES

    def test_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "POSTGRES")
        assert analytics_repository_mode() == AnalyticsRepositoryMode.POSTGRES

    def test_invalid_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "banana")
        with pytest.raises(RuntimeError, match="invalid"):
            analytics_repository_mode()

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "  in_memory  ")
        assert analytics_repository_mode() == AnalyticsRepositoryMode.IN_MEMORY


# ---------------------------------------------------------------------------
# InMemory Repository
# ---------------------------------------------------------------------------


class TestInMemoryAnalyticsRepository:
    """InMemoryAnalyticsRepository basics (backward compat)."""

    def test_mode(self) -> None:
        repo = InMemoryAnalyticsRepository()
        assert repo.mode == "in_memory"

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
        repo.add_event(_make_event(source=AnalyticsSource.SPOTIFY))
        repo.add_event(_make_event(source=AnalyticsSource.TIKTOK))
        result = repo.list_events(source=AnalyticsSource.SPOTIFY)
        assert len(result) == 1
        assert result[0].source == AnalyticsSource.SPOTIFY

    def test_filter_by_metric(self) -> None:
        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(metric=AnalyticsMetric.STREAMS))
        repo.add_event(_make_event(metric=AnalyticsMetric.SAVES))
        result = repo.list_events(metric=AnalyticsMetric.SAVES)
        assert len(result) == 1
        assert result[0].metric == AnalyticsMetric.SAVES

    def test_filter_by_campaign_id(self) -> None:
        repo = InMemoryAnalyticsRepository()
        cid = uuid4()
        repo.add_event(_make_event(campaign_id=cid))
        repo.add_event(_make_event())
        result = repo.list_events(campaign_id=cid)
        assert len(result) == 1

    def test_filter_by_track_id(self) -> None:
        repo = InMemoryAnalyticsRepository()
        tid = uuid4()
        repo.add_event(_make_event(track_id=tid))
        repo.add_event(_make_event())
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
        repo.add_event(_make_event())
        result = repo.get_campaign_events(cid)
        assert len(result) == 2

    def test_get_track_events(self) -> None:
        repo = InMemoryAnalyticsRepository()
        tid = uuid4()
        repo.add_event(_make_event(track_id=tid))
        repo.add_event(_make_event())
        result = repo.get_track_events(tid)
        assert len(result) == 1

    def test_summary(self) -> None:
        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(source=AnalyticsSource.SPOTIFY))
        repo.add_event(_make_event(source=AnalyticsSource.TIKTOK))
        summary = repo.summary()
        assert summary.total_events == 2
        assert summary.source_breakdown["spotify"] == 1
        assert summary.source_breakdown["tiktok"] == 1

    def test_summary_empty(self) -> None:
        repo = InMemoryAnalyticsRepository()
        summary = repo.summary()
        assert summary.total_events == 0
        assert summary.latest_event_at is None


# ---------------------------------------------------------------------------
# Postgres Repository
# ---------------------------------------------------------------------------


class TestPostgresAnalyticsRepository:
    """PostgresAnalyticsRepository basic contract."""

    def test_requires_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(AnalyticsRepositoryConfigError, match="DATABASE_URL"):
            PostgresAnalyticsRepository()

    def test_mode_is_postgres(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresAnalyticsRepository()
        assert repo.mode == "postgres"

    def test_delegates_to_inner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresAnalyticsRepository()
        event = _make_event()
        repo.add_event(event)
        assert len(repo.list_events()) == 1

    def test_add_events_batch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresAnalyticsRepository()
        events = [_make_event() for _ in range(3)]
        repo.add_events(events)
        assert len(repo.list_events()) == 3

    def test_summary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresAnalyticsRepository()
        repo.add_event(_make_event())
        summary = repo.summary()
        assert summary.total_events == 1


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestBuildAnalyticsRepository:
    """build_analytics_repository() factory tests."""

    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ANALYTICS_REPOSITORY_ENV, raising=False)
        repo = build_analytics_repository()
        assert repo.mode == "in_memory"

    def test_postgres_with_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "postgres")
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = build_analytics_repository()
        assert repo.mode == "postgres"

    def test_postgres_without_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ANALYTICS_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(AnalyticsRepositoryConfigError):
            build_analytics_repository()


# ---------------------------------------------------------------------------
# Intelligence engine compatibility (S49)
# ---------------------------------------------------------------------------


class TestIntelligenceCompatibility:
    """Verify intelligence_engine functions still work with repository events."""

    def test_detect_viral_moments_with_repo_events(self) -> None:
        from app.intelligence_engine import detect_viral_moments

        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(value=50000))
        repo.add_event(_make_event(value=100))
        events = repo.list_events()
        viral = detect_viral_moments(events)
        # Should return list (possibly with viral moments)
        assert isinstance(viral, list)

    def test_build_intelligence_overview_with_repo_events(self) -> None:
        from app.intelligence_engine import build_intelligence_overview

        repo = InMemoryAnalyticsRepository()
        repo.add_event(_make_event(source=AnalyticsSource.SPOTIFY, value=5000))
        repo.add_event(_make_event(source=AnalyticsSource.TIKTOK, value=80000))
        events = repo.list_events()
        overview = build_intelligence_overview(events)
        assert overview is not None
        assert overview.total_heat >= 0
