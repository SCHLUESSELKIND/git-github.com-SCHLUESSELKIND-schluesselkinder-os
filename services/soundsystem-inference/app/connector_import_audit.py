"""Connector Import Audit — S53 audit log for connector imports.

Protocol + InMemory + Postgres factory. Tracks every import-demo
invocation with operator identity, event counts, and metadata.
"""

from __future__ import annotations

import os
from typing import Protocol

from app.config import (
    ConnectorImportAuditConfigError,
    ConnectorImportAuditMode,
    DATABASE_URL_ENV,
    connector_import_audit_mode,
)
from app.schemas import (
    ConnectorImportAuditRecord,
    ConnectorImportAuditSummary,
    ConnectorType,
)


class ConnectorImportAuditRepository(Protocol):
    """Persistence boundary for connector import audit records."""

    @property
    def mode(self) -> str: ...

    def add_record(self, record: ConnectorImportAuditRecord) -> None: ...

    def list_records(
        self,
        *,
        connector_type: ConnectorType | None = None,
        operator_id: str | None = None,
        limit: int = 100,
    ) -> list[ConnectorImportAuditRecord]: ...

    def summary(self) -> ConnectorImportAuditSummary: ...


class InMemoryConnectorImportAuditRepository:
    """In-memory audit repository. Data lost on restart."""

    def __init__(self) -> None:
        self._records: list[ConnectorImportAuditRecord] = []

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_record(self, record: ConnectorImportAuditRecord) -> None:
        self._records.append(record)

    def list_records(
        self,
        *,
        connector_type: ConnectorType | None = None,
        operator_id: str | None = None,
        limit: int = 100,
    ) -> list[ConnectorImportAuditRecord]:
        result = self._records
        if connector_type is not None:
            result = [r for r in result if r.connector_type == connector_type]
        if operator_id is not None:
            result = [r for r in result if r.operator_id == operator_id]
        result = sorted(result, key=lambda r: r.created_at, reverse=True)
        return result[:limit]

    def summary(self) -> ConnectorImportAuditSummary:
        total_imports = len(self._records)
        total_events_imported = sum(r.event_count for r in self._records)
        connector_breakdown: dict[str, int] = {}
        operator_breakdown: dict[str, int] = {}
        latest_import_at = None

        for record in self._records:
            ct = record.connector_type.value
            connector_breakdown[ct] = connector_breakdown.get(ct, 0) + 1
            operator_breakdown[record.operator_id] = (
                operator_breakdown.get(record.operator_id, 0) + 1
            )
            if latest_import_at is None or record.created_at > latest_import_at:
                latest_import_at = record.created_at

        return ConnectorImportAuditSummary(
            total_imports=total_imports,
            total_events_imported=total_events_imported,
            connector_breakdown=connector_breakdown,
            operator_breakdown=operator_breakdown,
            latest_import_at=latest_import_at,
        )


class PostgresConnectorImportAuditRepository:
    """Postgres-backed audit repository. S53.

    Placeholder — delegates to InMemory until a real connection pool
    is wired. Raises ConnectorImportAuditConfigError if DATABASE_URL
    is missing when instantiated.
    """

    def __init__(self) -> None:
        db_url = os.environ.get(DATABASE_URL_ENV, "").strip()
        if not db_url:
            raise ConnectorImportAuditConfigError(
                f"postgres mode requires {DATABASE_URL_ENV} to be set"
            )
        self._db_url = db_url
        self._inner = InMemoryConnectorImportAuditRepository()

    @property
    def mode(self) -> str:
        return "postgres"

    def add_record(self, record: ConnectorImportAuditRecord) -> None:
        self._inner.add_record(record)

    def list_records(
        self,
        *,
        connector_type: ConnectorType | None = None,
        operator_id: str | None = None,
        limit: int = 100,
    ) -> list[ConnectorImportAuditRecord]:
        return self._inner.list_records(
            connector_type=connector_type,
            operator_id=operator_id,
            limit=limit,
        )

    def summary(self) -> ConnectorImportAuditSummary:
        return self._inner.summary()


def build_connector_import_audit_repository() -> ConnectorImportAuditRepository:
    """Factory — returns InMemory or Postgres audit repository based on config."""
    mode = connector_import_audit_mode()
    if mode == ConnectorImportAuditMode.POSTGRES:
        return PostgresConnectorImportAuditRepository()  # type: ignore[return-value]
    return InMemoryConnectorImportAuditRepository()  # type: ignore[return-value]
