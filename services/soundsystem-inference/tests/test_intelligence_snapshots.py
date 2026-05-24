"""Tests — S54 Intelligence Snapshot Persistence.

Covers:
- Config modes (default in_memory, postgres, invalid)
- InMemory + Postgres repository lifecycle
- Factory (build_intelligence_snapshot_repository)
- Snapshot creation from current events
- Summary with heat delta
- Supersede on new snapshot
- Route tests (POST, GET list, GET by ID, GET summary)
- POST requires operator
- Capabilities flags
- No scheduler/automation
- No external calls
- Intelligence routes still work
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import (
    INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV,
    IntelligenceSnapshotRepositoryConfigError,
    IntelligenceSnapshotRepositoryMode,
    intelligence_snapshot_repository_mode,
)
from app.intelligence_snapshot_repository import (
    InMemoryIntelligenceSnapshotRepository,
    PostgresIntelligenceSnapshotRepository,
    build_intelligence_snapshot_repository,
)
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    AnalyticsSource,
    IntelligenceOverview,
    IntelligenceSnapshot,
    IntelligenceSnapshotCreateRequest,
    IntelligenceSnapshotStatus,
    IntelligenceSnapshotSummary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    *,
    source: AnalyticsSource = AnalyticsSource.SPOTIFY,
    metric: AnalyticsMetric = AnalyticsMetric.STREAMS,
    value: float = 1000.0,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_id=uuid4(),
        source=source,
        metric=metric,
        value=value,
        timestamp=datetime.now(timezone.utc),
    )


def _make_snapshot(
    *,
    total_heat: float = 42.0,
    event_count: int = 10,
    notes: str | None = None,
    created_by: str = "dev-operator",
) -> IntelligenceSnapshot:
    overview = IntelligenceOverview(total_heat=total_heat)
    return IntelligenceSnapshot(
        snapshot_id=uuid4(),
        status=IntelligenceSnapshotStatus.CREATED,
        overview=overview,
        event_count=event_count,
        notes=notes,
        created_by=created_by,
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestSnapshotConfig:
    def test_default_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, raising=False)
        assert (
            intelligence_snapshot_repository_mode() == IntelligenceSnapshotRepositoryMode.IN_MEMORY
        )

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "in_memory")
        assert (
            intelligence_snapshot_repository_mode() == IntelligenceSnapshotRepositoryMode.IN_MEMORY
        )

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "postgres")
        assert (
            intelligence_snapshot_repository_mode() == IntelligenceSnapshotRepositoryMode.POSTGRES
        )

    def test_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "POSTGRES")
        assert (
            intelligence_snapshot_repository_mode() == IntelligenceSnapshotRepositoryMode.POSTGRES
        )

    def test_invalid_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "banana")
        with pytest.raises(RuntimeError, match="invalid"):
            intelligence_snapshot_repository_mode()

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "  in_memory  ")
        assert (
            intelligence_snapshot_repository_mode() == IntelligenceSnapshotRepositoryMode.IN_MEMORY
        )


# ---------------------------------------------------------------------------
# InMemory Repository
# ---------------------------------------------------------------------------


class TestInMemorySnapshotRepository:
    def test_mode(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        assert repo.mode == "in_memory"

    def test_add_and_get(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        snapshot = _make_snapshot()
        repo.add_snapshot(snapshot)
        result = repo.get_snapshot(snapshot.snapshot_id)
        assert result is not None
        assert result.snapshot_id == snapshot.snapshot_id

    def test_get_nonexistent(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        assert repo.get_snapshot(uuid4()) is None

    def test_list_empty(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        assert repo.list_snapshots() == []

    def test_list_most_recent_first(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        s1 = _make_snapshot(total_heat=10.0)
        s2 = _make_snapshot(total_heat=20.0)
        repo.add_snapshot(s1)
        repo.add_snapshot(s2)
        result = repo.list_snapshots()
        assert len(result) == 2
        assert result[0].created_at >= result[1].created_at

    def test_list_with_status_filter(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        repo.add_snapshot(_make_snapshot(total_heat=10.0))
        repo.add_snapshot(_make_snapshot(total_heat=20.0))
        # First should be superseded after second was added
        created = repo.list_snapshots(status=IntelligenceSnapshotStatus.CREATED)
        superseded = repo.list_snapshots(status=IntelligenceSnapshotStatus.SUPERSEDED)
        assert len(created) == 1
        assert len(superseded) == 1

    def test_list_with_limit(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        for i in range(5):
            repo.add_snapshot(_make_snapshot(total_heat=float(i)))
        result = repo.list_snapshots(limit=2)
        assert len(result) == 2

    def test_supersede_on_new_snapshot(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        s1 = _make_snapshot(total_heat=10.0)
        repo.add_snapshot(s1)
        assert s1.status == IntelligenceSnapshotStatus.CREATED

        s2 = _make_snapshot(total_heat=20.0)
        repo.add_snapshot(s2)
        assert s1.status == IntelligenceSnapshotStatus.SUPERSEDED
        assert s2.status == IntelligenceSnapshotStatus.CREATED

    def test_summary_empty(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        summary = repo.summary()
        assert summary.total_snapshots == 0
        assert summary.active_snapshots == 0
        assert summary.archived_snapshots == 0
        assert summary.latest_snapshot_at is None
        assert summary.latest_total_heat == 0.0
        assert summary.heat_delta_from_previous is None

    def test_summary_with_snapshots(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        repo.add_snapshot(_make_snapshot(total_heat=30.0))
        repo.add_snapshot(_make_snapshot(total_heat=50.0))
        summary = repo.summary()
        assert summary.total_snapshots == 2
        assert summary.active_snapshots == 2
        assert summary.archived_snapshots == 0
        assert summary.latest_total_heat == 50.0
        assert summary.heat_delta_from_previous == 20.0

    def test_summary_heat_delta_negative(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        repo.add_snapshot(_make_snapshot(total_heat=80.0))
        repo.add_snapshot(_make_snapshot(total_heat=60.0))
        summary = repo.summary()
        assert summary.heat_delta_from_previous == -20.0

    def test_notes_stored(self) -> None:
        repo = InMemoryIntelligenceSnapshotRepository()
        snapshot = _make_snapshot(notes="Weekly checkpoint")
        repo.add_snapshot(snapshot)
        result = repo.get_snapshot(snapshot.snapshot_id)
        assert result is not None
        assert result.notes == "Weekly checkpoint"


# ---------------------------------------------------------------------------
# Postgres Repository
# ---------------------------------------------------------------------------


class TestPostgresSnapshotRepository:
    def test_requires_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(IntelligenceSnapshotRepositoryConfigError, match="DATABASE_URL"):
            PostgresIntelligenceSnapshotRepository()

    def test_mode_is_postgres(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresIntelligenceSnapshotRepository()
        assert repo.mode == "postgres"

    def test_delegates_to_inner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresIntelligenceSnapshotRepository()
        snapshot = _make_snapshot()
        repo.add_snapshot(snapshot)
        assert repo.get_snapshot(snapshot.snapshot_id) is not None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestBuildSnapshotRepository:
    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, raising=False)
        repo = build_intelligence_snapshot_repository()
        assert repo.mode == "in_memory"

    def test_postgres_with_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "postgres")
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = build_intelligence_snapshot_repository()
        assert repo.mode == "postgres"

    def test_postgres_without_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(IntelligenceSnapshotRepositoryConfigError):
            build_intelligence_snapshot_repository()


# ---------------------------------------------------------------------------
# Schema models
# ---------------------------------------------------------------------------


class TestSnapshotSchemas:
    def test_snapshot_defaults(self) -> None:
        snapshot = IntelligenceSnapshot(
            snapshot_id=uuid4(),
            overview=IntelligenceOverview(),
        )
        assert snapshot.status == IntelligenceSnapshotStatus.CREATED
        assert snapshot.event_count == 0
        assert snapshot.source_event_latest_at is None
        assert snapshot.notes is None
        assert snapshot.created_by is None

    def test_create_request_defaults(self) -> None:
        req = IntelligenceSnapshotCreateRequest()
        assert req.notes is None

    def test_create_request_with_notes(self) -> None:
        req = IntelligenceSnapshotCreateRequest(notes="Test run")
        assert req.notes == "Test run"

    def test_summary_defaults(self) -> None:
        summary = IntelligenceSnapshotSummary()
        assert summary.total_snapshots == 0
        assert summary.heat_delta_from_previous is None


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------


class TestSnapshotRoutes:
    def test_list_snapshots_empty(self) -> None:
        from app.main import list_intelligence_snapshots

        result = asyncio.run(list_intelligence_snapshots())
        assert isinstance(result, list)

    def test_snapshot_summary_empty(self) -> None:
        from app.main import get_intelligence_snapshot_summary

        result = asyncio.run(get_intelligence_snapshot_summary())
        assert isinstance(result, IntelligenceSnapshotSummary)
        assert result.total_snapshots >= 0

    def test_create_snapshot(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_intelligence_snapshot

        result = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        assert isinstance(result, IntelligenceSnapshot)
        assert result.status == IntelligenceSnapshotStatus.CREATED
        assert result.created_by == DEV_OPERATOR.operator_id

    def test_create_snapshot_with_notes(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_intelligence_snapshot

        body = IntelligenceSnapshotCreateRequest(notes="Weekly review")
        result = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, body))
        assert result.notes == "Weekly review"

    def test_get_snapshot_by_id(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_intelligence_snapshot, get_intelligence_snapshot

        created = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        result = asyncio.run(get_intelligence_snapshot(created.snapshot_id))
        assert result.snapshot_id == created.snapshot_id

    def test_get_snapshot_not_found(self) -> None:
        from fastapi import HTTPException

        from app.main import get_intelligence_snapshot

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_intelligence_snapshot(uuid4()))
        assert exc_info.value.status_code == 404

    def test_create_snapshot_captures_event_count(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_intelligence_snapshot

        result = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        assert result.event_count >= 0

    def test_create_snapshot_has_overview(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_intelligence_snapshot

        result = asyncio.run(create_intelligence_snapshot(DEV_OPERATOR, None))
        assert isinstance(result.overview, IntelligenceOverview)


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class TestSnapshotCapabilities:
    def test_capabilities_has_snapshot_fields(self) -> None:
        from app.main import capabilities

        result = asyncio.run(capabilities())
        assert result.intelligence_snapshots_available is True
        assert result.intelligence_snapshot_repository_mode in ("in_memory", "postgres")


# ---------------------------------------------------------------------------
# Intelligence routes still work
# ---------------------------------------------------------------------------


class TestIntelligenceRoutesStillWork:
    def test_overview_route(self) -> None:
        from app.main import get_intelligence_overview

        result = asyncio.run(get_intelligence_overview())
        assert isinstance(result, IntelligenceOverview)

    def test_viral_moments_route(self) -> None:
        from app.main import get_viral_moments

        result = asyncio.run(get_viral_moments())
        assert isinstance(result, list)

    def test_heatmap_route(self) -> None:
        from app.main import get_audience_heatmap

        result = asyncio.run(get_audience_heatmap())
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# No external calls / no automation
# ---------------------------------------------------------------------------


class TestNoExternalCalls:
    def test_no_http_imports_in_repository(self) -> None:
        import inspect

        from app import intelligence_snapshot_repository

        source = inspect.getsource(intelligence_snapshot_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_scheduler_imports(self) -> None:
        import inspect

        from app import intelligence_snapshot_repository

        source = inspect.getsource(intelligence_snapshot_repository)
        assert "import schedule" not in source
        assert "import cron" not in source
        assert "import celery" not in source
        assert "import apscheduler" not in source

    def test_no_automation_in_routes(self) -> None:
        import inspect

        from app import main

        source = inspect.getsource(main)
        assert "apscheduler" not in source
        assert "celery" not in source
