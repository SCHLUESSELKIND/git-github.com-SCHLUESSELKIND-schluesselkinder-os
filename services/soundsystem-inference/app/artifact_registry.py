"""Artifact Registry — S29.

Persistent metadata registry for artifact records. Separates metadata
persistence from file-bytes storage (which remains in local filesystem
or future S3).

Dual-mode: in-memory (default) or Postgres. Same pattern as
LibraryRepository / ReleaseRepository.

Switch via `SOUNDSYSTEM_ARTIFACT_REGISTRY=postgres`
with `SOUNDSYSTEM_DATABASE_URL` pointing to the running instance.

Operations:
- create_record: insert new metadata row
- update_record: overwrite metadata (e.g. status → stored)
- get_record: lookup by artifact_id
- list_records: filtered list
- summary: aggregate counts/sizes
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

from app.config import (
    DATABASE_URL_ENV,
    ArtifactRegistryConfigError,
    ArtifactRegistryMode,
    artifact_registry_mode,
    database_url,
)
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    ArtifactStatus,
    ArtifactStorageSummary,
)


class ArtifactRegistry(Protocol):
    """Protocol for artifact metadata persistence."""

    @property
    def mode(self) -> str: ...

    def create_record(
        self,
        request: ArtifactCreateRequest,
        *,
        storage_key: str,
        storage_mode: str = "local",
        operator_id: str | None = None,
    ) -> ArtifactRecord: ...

    def update_record(self, record: ArtifactRecord) -> ArtifactRecord: ...

    def get_record(self, artifact_id: UUID) -> ArtifactRecord | None: ...

    def list_records(self, *, kind: ArtifactKind | None = None) -> list[ArtifactRecord]: ...

    def summary(self, *, storage_mode: str = "local") -> ArtifactStorageSummary: ...


class InMemoryArtifactRegistry:
    """In-memory artifact metadata registry. Data lost on restart."""

    def __init__(self) -> None:
        self._records: dict[UUID, ArtifactRecord] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def create_record(
        self,
        request: ArtifactCreateRequest,
        *,
        storage_key: str,
        storage_mode: str = "local",
        operator_id: str | None = None,
    ) -> ArtifactRecord:
        now = datetime.now(timezone.utc)
        aid = uuid4()
        record = ArtifactRecord(
            artifact_id=aid,
            kind=request.kind,
            status=ArtifactStatus.PLANNED,
            storage_mode=storage_mode,
            logical_path=request.logical_path,
            storage_key=storage_key,
            content_type=request.content_type,
            operator_id=operator_id,
            source_entity_type=request.source_entity_type,
            source_entity_id=request.source_entity_id,
            provenance_id=request.provenance_id,
            created_at=now,
            updated_at=now,
        )
        self._records[aid] = record
        return record

    def update_record(self, record: ArtifactRecord) -> ArtifactRecord:
        self._records[record.artifact_id] = record
        return record

    def get_record(self, artifact_id: UUID) -> ArtifactRecord | None:
        return self._records.get(artifact_id)

    def list_records(self, *, kind: ArtifactKind | None = None) -> list[ArtifactRecord]:
        records = list(self._records.values())
        if kind is not None:
            records = [r for r in records if r.kind == kind]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def summary(self, *, storage_mode: str = "local") -> ArtifactStorageSummary:
        records = list(self._records.values())
        total_size = sum(r.size_bytes or 0 for r in records)
        return ArtifactStorageSummary(
            total=len(records),
            planned=sum(1 for r in records if r.status == ArtifactStatus.PLANNED),
            stored=sum(1 for r in records if r.status == ArtifactStatus.STORED),
            missing=sum(1 for r in records if r.status == ArtifactStatus.MISSING),
            deleted=sum(1 for r in records if r.status == ArtifactStatus.DELETED),
            failed=sum(1 for r in records if r.status == ArtifactStatus.FAILED),
            total_size_bytes=total_size,
            storage_mode=storage_mode,
        )


class PostgresArtifactRegistry:
    """Postgres-backed artifact metadata registry.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_ARTIFACT_REGISTRY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the `db/006_artifacts.sql` migration.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise ArtifactRegistryConfigError(
                "postgres mode requires the 'postgres' extra. "
                'Install via `pip install -e ".[postgres]"` inside the inference service.'
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

    def create_record(
        self,
        request: ArtifactCreateRequest,
        *,
        storage_key: str,
        storage_mode: str = "local",
        operator_id: str | None = None,
    ) -> ArtifactRecord:
        now = datetime.now(timezone.utc)
        aid = uuid4()
        record = ArtifactRecord(
            artifact_id=aid,
            kind=request.kind,
            status=ArtifactStatus.PLANNED,
            storage_mode=storage_mode,
            logical_path=request.logical_path,
            storage_key=storage_key,
            content_type=request.content_type,
            operator_id=operator_id,
            source_entity_type=request.source_entity_type,
            source_entity_id=request.source_entity_id,
            provenance_id=request.provenance_id,
            created_at=now,
            updated_at=now,
        )
        self._insert_record(record)
        return record

    def update_record(self, record: ArtifactRecord) -> ArtifactRecord:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE artifact_records SET "
                    "  status=%s, size_bytes=%s, checksum_sha256=%s, "
                    "  content_type=%s, updated_at=%s "
                    "WHERE artifact_id=%s",
                    (
                        record.status.value,
                        record.size_bytes or 0,
                        record.checksum_sha256,
                        record.content_type,
                        record.updated_at,
                        record.artifact_id,
                    ),
                )
        return record

    def get_record(self, artifact_id: UUID) -> ArtifactRecord | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM artifact_records WHERE artifact_id = %s",
                    (artifact_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_records(self, *, kind: ArtifactKind | None = None) -> list[ArtifactRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if kind is not None:
                    cur.execute(
                        "SELECT * FROM artifact_records WHERE kind = %s ORDER BY created_at DESC",
                        (kind.value,),
                    )
                else:
                    cur.execute("SELECT * FROM artifact_records ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_record(row) for row in rows]

    def summary(self, *, storage_mode: str = "local") -> ArtifactStorageSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total, "
                    "  SUM(CASE WHEN status='planned' THEN 1 ELSE 0 END) AS planned, "
                    "  SUM(CASE WHEN status='stored' THEN 1 ELSE 0 END) AS stored, "
                    "  SUM(CASE WHEN status='missing' THEN 1 ELSE 0 END) AS missing, "
                    "  SUM(CASE WHEN status='deleted' THEN 1 ELSE 0 END) AS deleted, "
                    "  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed, "
                    "  COALESCE(SUM(size_bytes), 0) AS total_size_bytes "
                    "FROM artifact_records"
                )
                row = cur.fetchone()
        if row is None:
            return ArtifactStorageSummary(
                total=0,
                planned=0,
                stored=0,
                missing=0,
                deleted=0,
                failed=0,
                total_size_bytes=0,
                storage_mode=storage_mode,
            )
        return ArtifactStorageSummary(
            total=int(row["total"]),
            planned=int(row["planned"] or 0),
            stored=int(row["stored"] or 0),
            missing=int(row["missing"] or 0),
            deleted=int(row["deleted"] or 0),
            failed=int(row["failed"] or 0),
            total_size_bytes=int(row["total_size_bytes"] or 0),
            storage_mode=storage_mode,
        )

    def _insert_record(self, record: ArtifactRecord) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO artifact_records "
                    "(artifact_id, kind, status, storage_mode, logical_path, "
                    " storage_key, content_type, size_bytes, checksum_sha256, "
                    " operator_id, source_entity_type, source_entity_id, "
                    " provenance_id, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (artifact_id) DO UPDATE SET "
                    "  status=EXCLUDED.status, size_bytes=EXCLUDED.size_bytes, "
                    "  checksum_sha256=EXCLUDED.checksum_sha256, "
                    "  content_type=EXCLUDED.content_type, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        record.artifact_id,
                        record.kind.value,
                        record.status.value,
                        record.storage_mode,
                        record.logical_path,
                        record.storage_key,
                        record.content_type,
                        record.size_bytes or 0,
                        record.checksum_sha256,
                        record.operator_id,
                        record.source_entity_type,
                        str(record.source_entity_id) if record.source_entity_id else None,
                        record.provenance_id,
                        record.created_at,
                        record.updated_at,
                    ),
                )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_record(row: dict[str, Any]) -> ArtifactRecord:
    source_entity_id = row.get("source_entity_id")
    if source_entity_id and isinstance(source_entity_id, str):
        from uuid import UUID as _UUID

        try:
            source_entity_id = _UUID(source_entity_id)
        except ValueError:
            source_entity_id = None

    return ArtifactRecord(
        artifact_id=row["artifact_id"],
        kind=ArtifactKind(row["kind"]),
        status=ArtifactStatus(row["status"]),
        storage_mode=row["storage_mode"],
        logical_path=row["logical_path"],
        storage_key=row["storage_key"],
        content_type=row["content_type"],
        size_bytes=int(row["size_bytes"]) if row["size_bytes"] else None,
        checksum_sha256=row["checksum_sha256"],
        operator_id=row["operator_id"],
        source_entity_type=row["source_entity_type"],
        source_entity_id=source_entity_id,
        provenance_id=row["provenance_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_artifact_registry() -> ArtifactRegistry:
    """Construct the artifact registry selected by SOUNDSYSTEM_ARTIFACT_REGISTRY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = artifact_registry_mode()
    if mode == ArtifactRegistryMode.IN_MEMORY:
        return InMemoryArtifactRegistry()
    if mode == ArtifactRegistryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise ArtifactRegistryConfigError(
                f"SOUNDSYSTEM_ARTIFACT_REGISTRY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresArtifactRegistry(url)
    raise ArtifactRegistryConfigError(f"unhandled artifact registry mode: {mode!r}")
