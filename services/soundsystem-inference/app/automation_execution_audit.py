"""Automation Execution Audit Log — S59.

Append-only audit log for automation execution state transitions.
Records the intent behind every change on an AutomationExecutionJob.

No automation execution. No external API calls. No mutations of any
other object. No deletes (the application never removes audit rows).

Default in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL and
the db/013_automation_execution.sql migration.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    AUTOMATION_EXECUTION_AUDIT_ENV,
    AutomationExecutionAuditConfigError,
    AutomationExecutionAuditMode,
    DATABASE_URL_ENV,
    automation_execution_audit_mode,
    database_url,
)
from app.schemas import (
    AutomationExecutionAuditRecord,
    AutomationExecutionAuditSummary,
    AutomationExecutionStatus,
)


class AutomationExecutionAuditRepository(Protocol):
    """Persistence boundary for execution audit records."""

    @property
    def mode(self) -> str: ...

    def add_record(self, record: AutomationExecutionAuditRecord) -> None: ...

    def list_records(self, *, limit: int = 100) -> list[AutomationExecutionAuditRecord]: ...

    def list_by_execution(self, execution_id: UUID) -> list[AutomationExecutionAuditRecord]: ...

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionAuditRecord]: ...

    def summary(self) -> AutomationExecutionAuditSummary: ...


class InMemoryAutomationExecutionAuditRepository:
    """In-memory append-only audit log. Data lost on restart."""

    def __init__(self) -> None:
        self._records: list[AutomationExecutionAuditRecord] = []

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_record(self, record: AutomationExecutionAuditRecord) -> None:
        self._records.append(record)

    def list_records(self, *, limit: int = 100) -> list[AutomationExecutionAuditRecord]:
        sorted_records = sorted(self._records, key=lambda r: r.created_at, reverse=True)
        return sorted_records[:limit]

    def list_by_execution(self, execution_id: UUID) -> list[AutomationExecutionAuditRecord]:
        # Ascending by created_at — chronological for a single execution
        return sorted(
            (r for r in self._records if r.execution_id == execution_id),
            key=lambda r: r.created_at,
        )

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionAuditRecord]:
        return sorted(
            (r for r in self._records if r.campaign_id == campaign_id),
            key=lambda r: r.created_at,
            reverse=True,
        )

    def summary(self) -> AutomationExecutionAuditSummary:
        by_to: dict[str, int] = {}
        by_reason: dict[str, int] = {}
        operators: dict[str, int] = {}
        latest = None
        for r in self._records:
            by_to[r.to_status.value] = by_to.get(r.to_status.value, 0) + 1
            if r.reason:
                by_reason[r.reason] = by_reason.get(r.reason, 0) + 1
            if r.operator_id:
                operators[r.operator_id] = operators.get(r.operator_id, 0) + 1
            if latest is None or r.created_at > latest:
                latest = r.created_at
        return AutomationExecutionAuditSummary(
            total_records=len(self._records),
            by_to_status=by_to,
            by_reason=by_reason,
            operator_breakdown=operators,
            latest_record_at=latest,
        )


class PostgresAutomationExecutionAuditRepository:
    """Postgres-backed audit log (S59).

    Uses psycopg_pool. Activated via
    SOUNDSYSTEM_AUTOMATION_EXECUTION_AUDIT=postgres. Requires
    SOUNDSYSTEM_DATABASE_URL and the db/013_automation_execution.sql migration.

    INSERT-only at the application level. No deletes.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise AutomationExecutionAuditConfigError(
                "postgres mode requires the 'postgres' extra. "
                'Install via `pip install -e ".[postgres]"` inside the '
                "inference service."
            ) from exc

        self._pool = ConnectionPool(
            database_url_value,
            min_size=1,
            max_size=4,
            kwargs={"row_factory": _dict_row_factory()},
            open=True,
        )

    def close(self) -> None:
        self._pool.close()

    @property
    def mode(self) -> str:
        return "postgres"

    def add_record(self, record: AutomationExecutionAuditRecord) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO automation_execution_audit "
                    "(audit_id, execution_id, rule_id, campaign_id, "
                    " from_status, to_status, operator_id, reason, details, "
                    " created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        record.audit_id,
                        record.execution_id,
                        record.rule_id,
                        record.campaign_id,
                        record.from_status.value if record.from_status else None,
                        record.to_status.value,
                        record.operator_id,
                        record.reason,
                        Jsonb(dict(record.details)),
                        record.created_at,
                    ),
                )

    def list_records(self, *, limit: int = 100) -> list[AutomationExecutionAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_execution_audit ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def list_by_execution(self, execution_id: UUID) -> list[AutomationExecutionAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_execution_audit "
                    "WHERE execution_id = %s ORDER BY created_at ASC",
                    (execution_id,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_execution_audit "
                    "WHERE campaign_id = %s ORDER BY created_at DESC",
                    (campaign_id,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def summary(self) -> AutomationExecutionAuditSummary:
        # Summary requires aggregations; for moderate audit scale we read all rows
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT to_status, reason, operator_id, created_at "
                    "FROM automation_execution_audit"
                )
                rows = cur.fetchall()

        by_to: dict[str, int] = {}
        by_reason: dict[str, int] = {}
        operators: dict[str, int] = {}
        latest = None
        for r in rows:
            to_status = r["to_status"]
            by_to[to_status] = by_to.get(to_status, 0) + 1
            reason = r["reason"]
            if reason:
                by_reason[reason] = by_reason.get(reason, 0) + 1
            op = r["operator_id"]
            if op:
                operators[op] = operators.get(op, 0) + 1
            ts = r["created_at"]
            if latest is None or ts > latest:
                latest = ts

        return AutomationExecutionAuditSummary(
            total_records=len(rows),
            by_to_status=by_to,
            by_reason=by_reason,
            operator_breakdown=operators,
            latest_record_at=latest,
        )


# ---------- Row mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_record(row: dict[str, Any]) -> AutomationExecutionAuditRecord:
    from_status_raw = row.get("from_status")
    return AutomationExecutionAuditRecord(
        audit_id=row["audit_id"],
        execution_id=row["execution_id"],
        rule_id=row["rule_id"],
        campaign_id=row["campaign_id"],
        from_status=AutomationExecutionStatus(from_status_raw) if from_status_raw else None,
        to_status=AutomationExecutionStatus(row["to_status"]),
        operator_id=row.get("operator_id"),
        reason=row.get("reason"),
        details=row.get("details") or {},
        created_at=row["created_at"],
    )


# ---------- Factory ----------


def build_automation_execution_audit_repository() -> AutomationExecutionAuditRepository:
    """Factory: returns InMemory or Postgres audit repository.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = automation_execution_audit_mode()
    if mode == AutomationExecutionAuditMode.IN_MEMORY:
        return InMemoryAutomationExecutionAuditRepository()
    if mode == AutomationExecutionAuditMode.POSTGRES:
        url = database_url()
        if url is None:
            raise AutomationExecutionAuditConfigError(
                f"{AUTOMATION_EXECUTION_AUDIT_ENV}=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresAutomationExecutionAuditRepository(url)
    raise AutomationExecutionAuditConfigError(f"unhandled audit repository mode: {mode!r}")
