"""Commerce Sync Audit Log — S65.

Append-only audit log for operator-triggered Shopify + Printful sync
actions. Records intent and resulting per-provider summary state.

No automation execution. No external API calls. No mutations of any
other object. No deletes (the application never removes audit rows).
Token never appears in any field — ``details`` may carry Shopify
product IDs / handles and Printful sync product IDs only.

Default in-memory. Postgres mode requires ``SOUNDSYSTEM_DATABASE_URL``
and the ``db/014_commerce_sync_audit.sql`` migration.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    COMMERCE_SYNC_AUDIT_ENV,
    CommerceSyncAuditConfigError,
    CommerceSyncAuditMode,
    DATABASE_URL_ENV,
    commerce_sync_audit_mode,
    database_url,
)
from app.schemas import (
    CommerceSyncAuditAction,
    CommerceSyncAuditRecord,
    CommerceSyncAuditSummary,
    CommerceSyncStatus,
)


class CommerceSyncAuditRepository(Protocol):
    """Persistence boundary for commerce-sync audit records."""

    @property
    def mode(self) -> str: ...

    def add_record(self, record: CommerceSyncAuditRecord) -> None: ...

    def list_records(self, *, limit: int = 100) -> list[CommerceSyncAuditRecord]: ...

    def list_by_capsule(self, capsule_id: UUID) -> list[CommerceSyncAuditRecord]: ...

    def list_by_release(self, release_id: UUID) -> list[CommerceSyncAuditRecord]: ...

    def summary(self) -> CommerceSyncAuditSummary: ...


class InMemoryCommerceSyncAuditRepository:
    """In-memory append-only audit log. Data lost on restart."""

    def __init__(self) -> None:
        self._records: list[CommerceSyncAuditRecord] = []

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_record(self, record: CommerceSyncAuditRecord) -> None:
        self._records.append(record)

    def list_records(self, *, limit: int = 100) -> list[CommerceSyncAuditRecord]:
        sorted_records = sorted(self._records, key=lambda r: r.created_at, reverse=True)
        return sorted_records[:limit]

    def list_by_capsule(self, capsule_id: UUID) -> list[CommerceSyncAuditRecord]:
        # Ascending — chronological for a single capsule.
        return sorted(
            (r for r in self._records if r.capsule_id == capsule_id),
            key=lambda r: r.created_at,
        )

    def list_by_release(self, release_id: UUID) -> list[CommerceSyncAuditRecord]:
        return sorted(
            (r for r in self._records if r.release_id == release_id),
            key=lambda r: r.created_at,
            reverse=True,
        )

    def summary(self) -> CommerceSyncAuditSummary:
        by_action: dict[str, int] = {}
        by_status: dict[str, int] = {}
        latest = None
        total_shopify = 0
        total_printful = 0
        for r in self._records:
            by_action[r.action.value] = by_action.get(r.action.value, 0) + 1
            by_status[r.overall_status.value] = by_status.get(r.overall_status.value, 0) + 1
            total_shopify += r.shopify_item_count
            total_printful += r.printful_item_count
            if latest is None or r.created_at > latest:
                latest = r.created_at
        return CommerceSyncAuditSummary(
            total_records=len(self._records),
            records_by_action=by_action,
            records_by_status=by_status,
            latest_record_at=latest,
            total_shopify_items=total_shopify,
            total_printful_items=total_printful,
        )


class PostgresCommerceSyncAuditRepository:
    """Postgres-backed audit log (S65).

    Uses ``psycopg_pool``. Activated via
    ``SOUNDSYSTEM_COMMERCE_SYNC_AUDIT=postgres``. Requires
    ``SOUNDSYSTEM_DATABASE_URL`` and the
    ``db/014_commerce_sync_audit.sql`` migration.

    INSERT-only at the application layer. No delete method exists.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise CommerceSyncAuditConfigError(
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

    def add_record(self, record: CommerceSyncAuditRecord) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO commerce_sync_audit "
                    "(audit_id, capsule_id, release_id, operator_id, action, "
                    " overall_status, shopify_status, printful_status, "
                    " shopify_item_count, printful_item_count, "
                    " warnings, details, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        record.audit_id,
                        record.capsule_id,
                        record.release_id,
                        record.operator_id,
                        record.action.value,
                        record.overall_status.value,
                        record.shopify_status.value if record.shopify_status else None,
                        record.printful_status.value if record.printful_status else None,
                        record.shopify_item_count,
                        record.printful_item_count,
                        Jsonb(list(record.warnings)),
                        Jsonb(dict(record.details)),
                        record.created_at,
                    ),
                )

    def list_records(self, *, limit: int = 100) -> list[CommerceSyncAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM commerce_sync_audit ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def list_by_capsule(self, capsule_id: UUID) -> list[CommerceSyncAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM commerce_sync_audit "
                    "WHERE capsule_id = %s ORDER BY created_at ASC",
                    (capsule_id,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def list_by_release(self, release_id: UUID) -> list[CommerceSyncAuditRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM commerce_sync_audit "
                    "WHERE release_id = %s ORDER BY created_at DESC",
                    (release_id,),
                )
                rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def summary(self) -> CommerceSyncAuditSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT action, overall_status, shopify_item_count, "
                    "       printful_item_count, created_at "
                    "FROM commerce_sync_audit"
                )
                rows = cur.fetchall()

        by_action: dict[str, int] = {}
        by_status: dict[str, int] = {}
        latest = None
        total_shopify = 0
        total_printful = 0
        for r in rows:
            a = r["action"]
            by_action[a] = by_action.get(a, 0) + 1
            s = r["overall_status"]
            by_status[s] = by_status.get(s, 0) + 1
            total_shopify += int(r["shopify_item_count"] or 0)
            total_printful += int(r["printful_item_count"] or 0)
            ts = r["created_at"]
            if latest is None or ts > latest:
                latest = ts
        return CommerceSyncAuditSummary(
            total_records=len(rows),
            records_by_action=by_action,
            records_by_status=by_status,
            latest_record_at=latest,
            total_shopify_items=total_shopify,
            total_printful_items=total_printful,
        )


# ---------- Row mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_record(row: dict[str, Any]) -> CommerceSyncAuditRecord:
    shopify_status_raw = row.get("shopify_status")
    printful_status_raw = row.get("printful_status")
    return CommerceSyncAuditRecord(
        audit_id=row["audit_id"],
        capsule_id=row["capsule_id"],
        release_id=row.get("release_id"),
        operator_id=row.get("operator_id"),
        action=CommerceSyncAuditAction(row["action"]),
        overall_status=CommerceSyncStatus(row["overall_status"]),
        shopify_status=CommerceSyncStatus(shopify_status_raw) if shopify_status_raw else None,
        printful_status=CommerceSyncStatus(printful_status_raw) if printful_status_raw else None,
        shopify_item_count=int(row.get("shopify_item_count") or 0),
        printful_item_count=int(row.get("printful_item_count") or 0),
        warnings=row.get("warnings") or [],
        details=row.get("details") or {},
        created_at=row["created_at"],
    )


# ---------- Factory ----------


def build_commerce_sync_audit_repository() -> CommerceSyncAuditRepository:
    """Factory — returns InMemory or Postgres audit repository.

    Defaults to in-memory. Postgres requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = commerce_sync_audit_mode()
    if mode == CommerceSyncAuditMode.IN_MEMORY:
        return InMemoryCommerceSyncAuditRepository()
    if mode == CommerceSyncAuditMode.POSTGRES:
        url = database_url()
        if url is None:
            raise CommerceSyncAuditConfigError(
                f"{COMMERCE_SYNC_AUDIT_ENV}=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresCommerceSyncAuditRepository(url)
    raise CommerceSyncAuditConfigError(f"unhandled commerce sync audit mode: {mode!r}")
