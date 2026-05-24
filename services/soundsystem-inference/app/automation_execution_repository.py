"""Automation Execution Repository — S58 contract, S59 persistence.

Dual-mode repository: in-memory (default) or Postgres. Matches the
established pattern used by Campaign, Snapshot, Analytics, etc.

No execution happens here — this is persistence. No external API calls.
No scheduler. No background workers. No provider mutations.

Switch to Postgres via ``SOUNDSYSTEM_AUTOMATION_EXECUTION_REPOSITORY=postgres``
with ``SOUNDSYSTEM_DATABASE_URL`` pointing to the running instance and
``db/013_automation_execution.sql`` applied.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    AUTOMATION_EXECUTION_REPOSITORY_ENV,
    AutomationExecutionRepositoryConfigError,
    AutomationExecutionRepositoryMode,
    DATABASE_URL_ENV,
    automation_execution_mode,
    automation_execution_repository_mode,
    database_url,
)
from app.schemas import (
    AutomationExecutionJob,
    AutomationExecutionStatus,
    AutomationExecutionSummary,
)


class AutomationExecutionRepository(Protocol):
    """Persistence boundary for automation execution jobs."""

    @property
    def mode(self) -> str: ...

    def add_job(self, job: AutomationExecutionJob) -> None: ...

    def get_job(self, execution_id: UUID) -> AutomationExecutionJob | None: ...

    def list_jobs(self) -> list[AutomationExecutionJob]: ...

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionJob]: ...

    def update_job(self, job: AutomationExecutionJob) -> None: ...

    def summary(self) -> AutomationExecutionSummary: ...


class InMemoryAutomationExecutionRepository:
    """In-memory execution job repository. Data lost on restart."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, AutomationExecutionJob] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_job(self, job: AutomationExecutionJob) -> None:
        self._jobs[job.execution_id] = job

    def get_job(self, execution_id: UUID) -> AutomationExecutionJob | None:
        return self._jobs.get(execution_id)

    def list_jobs(self) -> list[AutomationExecutionJob]:
        return sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionJob]:
        return sorted(
            (j for j in self._jobs.values() if j.campaign_id == campaign_id),
            key=lambda j: j.created_at,
            reverse=True,
        )

    def update_job(self, job: AutomationExecutionJob) -> None:
        self._jobs[job.execution_id] = job

    def summary(self) -> AutomationExecutionSummary:
        from app.schemas import AutomationExecutionMode as ExecMode

        jobs = list(self._jobs.values())
        mode_value = automation_execution_mode().value
        return AutomationExecutionSummary(
            total=len(jobs),
            queued=sum(1 for j in jobs if j.status == AutomationExecutionStatus.QUEUED),
            blocked=sum(1 for j in jobs if j.status == AutomationExecutionStatus.BLOCKED),
            completed_mock=sum(
                1 for j in jobs if j.status == AutomationExecutionStatus.COMPLETED_MOCK
            ),
            failed=sum(1 for j in jobs if j.status == AutomationExecutionStatus.FAILED),
            execution_mode=ExecMode(mode_value),
        )


class PostgresAutomationExecutionRepository:
    """Postgres-backed execution job repository (S59).

    Uses psycopg_pool. Activated via
    SOUNDSYSTEM_AUTOMATION_EXECUTION_REPOSITORY=postgres. Requires
    SOUNDSYSTEM_DATABASE_URL and the db/013_automation_execution.sql
    migration. No real execution. No side effects.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise AutomationExecutionRepositoryConfigError(
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

    def add_job(self, job: AutomationExecutionJob) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO automation_execution_jobs "
                    "(execution_id, rule_id, campaign_id, dry_run_status, status, "
                    " proposed_changes, blocked_reasons, warnings, created_by, "
                    " created_at, updated_at, completed_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        job.execution_id,
                        job.rule_id,
                        job.campaign_id,
                        job.dry_run_status.value,
                        job.status.value,
                        Jsonb(list(job.proposed_changes)),
                        Jsonb(list(job.blocked_reasons)),
                        Jsonb(list(job.warnings)),
                        job.created_by,
                        job.created_at,
                        job.updated_at,
                        job.completed_at,
                    ),
                )

    def get_job(self, execution_id: UUID) -> AutomationExecutionJob | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_execution_jobs WHERE execution_id = %s",
                    (execution_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_job(row)

    def list_jobs(self) -> list[AutomationExecutionJob]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_execution_jobs ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_job(r) for r in rows]

    def list_by_campaign(self, campaign_id: UUID) -> list[AutomationExecutionJob]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_execution_jobs "
                    "WHERE campaign_id = %s ORDER BY created_at DESC",
                    (campaign_id,),
                )
                rows = cur.fetchall()
        return [_row_to_job(r) for r in rows]

    def update_job(self, job: AutomationExecutionJob) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE automation_execution_jobs SET "
                    "  status=%s, "
                    "  proposed_changes=%s, "
                    "  blocked_reasons=%s, "
                    "  warnings=%s, "
                    "  updated_at=%s, "
                    "  completed_at=%s "
                    "WHERE execution_id=%s",
                    (
                        job.status.value,
                        Jsonb(list(job.proposed_changes)),
                        Jsonb(list(job.blocked_reasons)),
                        Jsonb(list(job.warnings)),
                        job.updated_at,
                        job.completed_at,
                        job.execution_id,
                    ),
                )

    def summary(self) -> AutomationExecutionSummary:
        from app.schemas import AutomationExecutionMode as ExecMode

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total, "
                    "  SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued, "
                    "  SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) AS blocked, "
                    "  SUM(CASE WHEN status = 'completed_mock' THEN 1 ELSE 0 END) "
                    "    AS completed_mock, "
                    "  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed "
                    "FROM automation_execution_jobs"
                )
                row = cur.fetchone()

        mode_value = automation_execution_mode().value
        if row is None:
            return AutomationExecutionSummary(execution_mode=ExecMode(mode_value))
        return AutomationExecutionSummary(
            total=int(row["total"] or 0),
            queued=int(row["queued"] or 0),
            blocked=int(row["blocked"] or 0),
            completed_mock=int(row["completed_mock"] or 0),
            failed=int(row["failed"] or 0),
            execution_mode=ExecMode(mode_value),
        )


# ---------- Row mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_job(row: dict[str, Any]) -> AutomationExecutionJob:
    from app.schemas import CampaignAutomationDryRunStatus

    return AutomationExecutionJob(
        execution_id=row["execution_id"],
        rule_id=row["rule_id"],
        campaign_id=row["campaign_id"],
        dry_run_status=CampaignAutomationDryRunStatus(row["dry_run_status"]),
        status=AutomationExecutionStatus(row["status"]),
        proposed_changes=row["proposed_changes"] or [],
        blocked_reasons=row["blocked_reasons"] or [],
        warnings=row["warnings"] or [],
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


# ---------- Factory ----------


def build_automation_execution_repository() -> AutomationExecutionRepository:
    """Factory: returns InMemory or Postgres execution job repository.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = automation_execution_repository_mode()
    if mode == AutomationExecutionRepositoryMode.IN_MEMORY:
        return InMemoryAutomationExecutionRepository()
    if mode == AutomationExecutionRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise AutomationExecutionRepositoryConfigError(
                f"{AUTOMATION_EXECUTION_REPOSITORY_ENV}=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresAutomationExecutionRepository(url)
    raise AutomationExecutionRepositoryConfigError(f"unhandled execution repository mode: {mode!r}")
