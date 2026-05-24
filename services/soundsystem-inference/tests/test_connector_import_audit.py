"""Tests — S53 Connector Import Audit.

Covers: config, InMemory + Postgres repository, factory,
audit record creation, list/filter, summary, route tests,
import-demo audit wiring.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import (
    CONNECTOR_IMPORT_AUDIT_ENV,
    ConnectorImportAuditConfigError,
    ConnectorImportAuditMode,
    connector_import_audit_mode,
)
from app.connector_import_audit import (
    InMemoryConnectorImportAuditRepository,
    PostgresConnectorImportAuditRepository,
    build_connector_import_audit_repository,
)
from app.schemas import (
    ConnectorImportAuditRecord,
    ConnectorImportAuditSummary,
    ConnectorType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    *,
    connector_type: ConnectorType = ConnectorType.SPOTIFY,
    operator_id: str = "dev-operator",
    event_count: int = 5,
    status: str = "completed",
) -> ConnectorImportAuditRecord:
    return ConnectorImportAuditRecord(
        audit_id=uuid4(),
        connector_type=connector_type,
        operator_id=operator_id,
        event_count=event_count,
        event_ids=[uuid4() for _ in range(event_count)],
        status=status,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConnectorImportAuditConfig:
    """Config mode resolution."""

    def test_default_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CONNECTOR_IMPORT_AUDIT_ENV, raising=False)
        assert connector_import_audit_mode() == ConnectorImportAuditMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CONNECTOR_IMPORT_AUDIT_ENV, "in_memory")
        assert connector_import_audit_mode() == ConnectorImportAuditMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CONNECTOR_IMPORT_AUDIT_ENV, "postgres")
        assert connector_import_audit_mode() == ConnectorImportAuditMode.POSTGRES

    def test_invalid_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CONNECTOR_IMPORT_AUDIT_ENV, "banana")
        with pytest.raises(RuntimeError, match="invalid"):
            connector_import_audit_mode()


# ---------------------------------------------------------------------------
# InMemory Repository
# ---------------------------------------------------------------------------


class TestInMemoryAuditRepository:
    """InMemoryConnectorImportAuditRepository basics."""

    def test_mode(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        assert repo.mode == "in_memory"

    def test_add_and_list(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        record = _make_record()
        repo.add_record(record)
        records = repo.list_records()
        assert len(records) == 1
        assert records[0].audit_id == record.audit_id

    def test_filter_by_connector_type(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        repo.add_record(_make_record(connector_type=ConnectorType.SPOTIFY))
        repo.add_record(_make_record(connector_type=ConnectorType.TIKTOK))
        result = repo.list_records(connector_type=ConnectorType.SPOTIFY)
        assert len(result) == 1
        assert result[0].connector_type == ConnectorType.SPOTIFY

    def test_filter_by_operator_id(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        repo.add_record(_make_record(operator_id="alice"))
        repo.add_record(_make_record(operator_id="bob"))
        result = repo.list_records(operator_id="alice")
        assert len(result) == 1
        assert result[0].operator_id == "alice"

    def test_limit(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        for _ in range(10):
            repo.add_record(_make_record())
        result = repo.list_records(limit=3)
        assert len(result) == 3

    def test_most_recent_first(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        r1 = _make_record()
        r2 = _make_record()
        repo.add_record(r1)
        repo.add_record(r2)
        records = repo.list_records()
        # r2 should be first (more recent created_at)
        assert records[0].created_at >= records[1].created_at

    def test_summary(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        repo.add_record(_make_record(connector_type=ConnectorType.SPOTIFY, event_count=3))
        repo.add_record(_make_record(connector_type=ConnectorType.TIKTOK, event_count=5))
        summary = repo.summary()
        assert summary.total_imports == 2
        assert summary.total_events_imported == 8
        assert summary.connector_breakdown["spotify"] == 1
        assert summary.connector_breakdown["tiktok"] == 1
        assert summary.latest_import_at is not None

    def test_summary_empty(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        summary = repo.summary()
        assert summary.total_imports == 0
        assert summary.total_events_imported == 0
        assert summary.latest_import_at is None

    def test_failed_records_tracked(self) -> None:
        repo = InMemoryConnectorImportAuditRepository()
        repo.add_record(_make_record(status="failed", event_count=0))
        records = repo.list_records()
        assert len(records) == 1
        assert records[0].status == "failed"


# ---------------------------------------------------------------------------
# Postgres Repository
# ---------------------------------------------------------------------------


class TestPostgresAuditRepository:
    """PostgresConnectorImportAuditRepository basic contract."""

    def test_requires_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(ConnectorImportAuditConfigError, match="DATABASE_URL"):
            PostgresConnectorImportAuditRepository()

    def test_mode_is_postgres(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresConnectorImportAuditRepository()
        assert repo.mode == "postgres"

    def test_delegates_to_inner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = PostgresConnectorImportAuditRepository()
        record = _make_record()
        repo.add_record(record)
        assert len(repo.list_records()) == 1


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestBuildAuditRepository:
    """build_connector_import_audit_repository() factory tests."""

    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CONNECTOR_IMPORT_AUDIT_ENV, raising=False)
        repo = build_connector_import_audit_repository()
        assert repo.mode == "in_memory"

    def test_postgres_with_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CONNECTOR_IMPORT_AUDIT_ENV, "postgres")
        monkeypatch.setenv("SOUNDSYSTEM_DATABASE_URL", "postgresql://localhost/test")
        repo = build_connector_import_audit_repository()
        assert repo.mode == "postgres"

    def test_postgres_without_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CONNECTOR_IMPORT_AUDIT_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(ConnectorImportAuditConfigError):
            build_connector_import_audit_repository()


# ---------------------------------------------------------------------------
# Schema models
# ---------------------------------------------------------------------------


class TestAuditSchemas:
    """ConnectorImportAuditRecord and Summary models."""

    def test_record_defaults(self) -> None:
        record = ConnectorImportAuditRecord(
            audit_id=uuid4(),
            connector_type=ConnectorType.SPOTIFY,
            operator_id="test-op",
        )
        assert record.event_count == 0
        assert record.status == "completed"
        assert record.error_message is None
        assert record.event_ids == []

    def test_summary_defaults(self) -> None:
        summary = ConnectorImportAuditSummary()
        assert summary.total_imports == 0
        assert summary.total_events_imported == 0
        assert summary.latest_import_at is None

    def test_record_with_error(self) -> None:
        record = ConnectorImportAuditRecord(
            audit_id=uuid4(),
            connector_type=ConnectorType.TIKTOK,
            operator_id="test-op",
            status="failed",
            error_message="No mock adapter available.",
        )
        assert record.status == "failed"
        assert record.error_message is not None


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------


class TestAuditRoutes:
    """Route-level tests (asyncio.run pattern)."""

    def test_list_audit_empty(self) -> None:
        from app.main import list_connector_import_audit

        result = asyncio.run(list_connector_import_audit())
        assert isinstance(result, list)

    def test_audit_summary_empty(self) -> None:
        from app.main import connector_import_audit_summary

        result = asyncio.run(connector_import_audit_summary())
        assert isinstance(result, ConnectorImportAuditSummary)
        assert result.total_imports >= 0

    def test_import_demo_creates_audit_record(self) -> None:
        """import-demo creates an audit record in the audit repository."""
        from app.auth import DEV_OPERATOR
        from app.main import connector_import_audit, import_demo_events

        initial_count = len(connector_import_audit.list_records())
        asyncio.run(import_demo_events(ConnectorType.SPOTIFY, DEV_OPERATOR))
        after_count = len(connector_import_audit.list_records())
        assert after_count == initial_count + 1

    def test_import_demo_failed_creates_audit_record(self) -> None:
        """import-demo for unsupported connector still creates audit record."""
        from app.auth import DEV_OPERATOR
        from app.main import connector_import_audit, import_demo_events

        initial_count = len(connector_import_audit.list_records())
        # DITTO has no mock adapter
        asyncio.run(import_demo_events(ConnectorType.DITTO, DEV_OPERATOR))
        after_count = len(connector_import_audit.list_records())
        assert after_count == initial_count + 1
        # Last record should be failed
        records = connector_import_audit.list_records()
        latest = records[0]
        assert latest.status == "failed"

    def test_import_demo_audit_has_operator(self) -> None:
        """Audit record captures operator identity."""
        from app.auth import DEV_OPERATOR
        from app.main import connector_import_audit, import_demo_events

        asyncio.run(import_demo_events(ConnectorType.SPOTIFY, DEV_OPERATOR))
        records = connector_import_audit.list_records()
        latest = records[0]
        assert latest.operator_id == DEV_OPERATOR.operator_id

    def test_import_demo_audit_has_event_ids(self) -> None:
        """Audit record captures event IDs from imported events."""
        from app.auth import DEV_OPERATOR
        from app.main import connector_import_audit, import_demo_events

        asyncio.run(import_demo_events(ConnectorType.SPOTIFY, DEV_OPERATOR))
        records = connector_import_audit.list_records()
        latest = records[0]
        assert latest.event_count > 0
        assert len(latest.event_ids) == latest.event_count


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    """Capabilities endpoint exposes S53 fields."""

    def test_capabilities_has_audit_fields(self) -> None:
        from app.main import capabilities

        result = asyncio.run(capabilities())
        assert hasattr(result, "analytics_repository_mode")
        assert hasattr(result, "connector_import_audit_available")
        assert result.connector_import_audit_available is True
        assert result.analytics_repository_mode in ("in_memory", "postgres")
