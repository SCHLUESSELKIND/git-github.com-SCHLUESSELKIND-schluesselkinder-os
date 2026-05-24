"""Vinyl Release Repository — S46 contract, S47 persistence.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
MerchRepository. Switch via ``SOUNDSYSTEM_VINYL_REPOSITORY=postgres``
with ``SOUNDSYSTEM_DATABASE_URL`` pointing to the running instance.

No real elasticStage API calls. No manufacturing.
No order placement. Manual handoff only.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    VinylRepositoryConfigError,
    VinylRepositoryMode,
    database_url,
    vinyl_repository_mode,
)
from app.schemas import (
    VinylEditionType,
    VinylFormat,
    VinylProviderGroup,
    VinylReadinessItem,
    VinylReleaseObject,
    VinylReleaseStatus,
    VinylReleaseSummary,
    VinylTrackListing,
)


class VinylRepository(Protocol):
    """Persistence boundary for vinyl releases."""

    @property
    def mode(self) -> str: ...

    def store(self, vinyl: VinylReleaseObject) -> None: ...

    def get(self, vinyl_id: UUID) -> VinylReleaseObject | None: ...

    def get_by_release(self, release_id: UUID) -> VinylReleaseObject | None: ...

    def list_all(self) -> list[VinylReleaseObject]: ...

    def update(self, vinyl: VinylReleaseObject) -> None: ...

    def summary(self) -> VinylReleaseSummary: ...


class InMemoryVinylRepository:
    """In-memory vinyl repository. Data lost on restart."""

    def __init__(self) -> None:
        self._vinyls: dict[UUID, VinylReleaseObject] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, vinyl: VinylReleaseObject) -> None:
        self._vinyls[vinyl.vinyl_id] = vinyl

    def get(self, vinyl_id: UUID) -> VinylReleaseObject | None:
        return self._vinyls.get(vinyl_id)

    def get_by_release(self, release_id: UUID) -> VinylReleaseObject | None:
        for vinyl in self._vinyls.values():
            if vinyl.release_id == release_id:
                return vinyl
        return None

    def list_all(self) -> list[VinylReleaseObject]:
        return sorted(
            self._vinyls.values(),
            key=lambda v: v.created_at,
            reverse=True,
        )

    def update(self, vinyl: VinylReleaseObject) -> None:
        self._vinyls[vinyl.vinyl_id] = vinyl

    def summary(self) -> VinylReleaseSummary:
        vinyls = list(self._vinyls.values())
        return VinylReleaseSummary(
            total_releases=len(vinyls),
            draft=sum(1 for v in vinyls if v.status == VinylReleaseStatus.DRAFT),
            ready=sum(1 for v in vinyls if v.status == VinylReleaseStatus.READY),
            submitted=sum(1 for v in vinyls if v.status == VinylReleaseStatus.SUBMITTED),
            test_pressing=sum(1 for v in vinyls if v.status == VinylReleaseStatus.TEST_PRESSING),
            approved=sum(1 for v in vinyls if v.status == VinylReleaseStatus.APPROVED),
            live=sum(1 for v in vinyls if v.status == VinylReleaseStatus.LIVE),
            archived=sum(1 for v in vinyls if v.status == VinylReleaseStatus.ARCHIVED),
            blocked=sum(1 for v in vinyls if v.status == VinylReleaseStatus.BLOCKED),
        )


class PostgresVinylRepository:
    """Postgres-backed vinyl repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_VINYL_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the ``db/009_vinyl.sql`` migration.

    No real elasticStage API calls. No manufacturing.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise VinylRepositoryConfigError(
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

    def store(self, vinyl: VinylReleaseObject) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO vinyl_releases "
                    "(vinyl_id, release_id, title, artist, provider_group, "
                    " status, format, edition_type, pressing_quantity, numbered, "
                    " side_a_tracks, side_b_tracks, cover_artifact_id, "
                    " audio_master_artifact_id, export_artifact_id, "
                    " soundcloud_job_id, readiness_items, warnings, "
                    " notes, created_by, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (vinyl_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, artist=EXCLUDED.artist, "
                    "  provider_group=EXCLUDED.provider_group, "
                    "  status=EXCLUDED.status, format=EXCLUDED.format, "
                    "  edition_type=EXCLUDED.edition_type, "
                    "  pressing_quantity=EXCLUDED.pressing_quantity, "
                    "  numbered=EXCLUDED.numbered, "
                    "  side_a_tracks=EXCLUDED.side_a_tracks, "
                    "  side_b_tracks=EXCLUDED.side_b_tracks, "
                    "  cover_artifact_id=EXCLUDED.cover_artifact_id, "
                    "  audio_master_artifact_id=EXCLUDED.audio_master_artifact_id, "
                    "  export_artifact_id=EXCLUDED.export_artifact_id, "
                    "  soundcloud_job_id=EXCLUDED.soundcloud_job_id, "
                    "  readiness_items=EXCLUDED.readiness_items, "
                    "  warnings=EXCLUDED.warnings, "
                    "  notes=EXCLUDED.notes, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        vinyl.vinyl_id,
                        vinyl.release_id,
                        vinyl.title,
                        vinyl.artist,
                        vinyl.provider_group.value,
                        vinyl.status.value,
                        vinyl.format.value,
                        vinyl.edition_type.value,
                        vinyl.pressing_quantity,
                        vinyl.numbered,
                        Jsonb([t.model_dump(mode="json") for t in vinyl.side_a_tracks]),
                        Jsonb([t.model_dump(mode="json") for t in vinyl.side_b_tracks]),
                        vinyl.cover_artifact_id,
                        vinyl.audio_master_artifact_id,
                        vinyl.export_artifact_id,
                        vinyl.soundcloud_job_id,
                        Jsonb([r.model_dump(mode="json") for r in vinyl.readiness_items]),
                        Jsonb(vinyl.warnings),
                        vinyl.notes,
                        vinyl.created_by,
                        vinyl.created_at,
                        vinyl.updated_at,
                    ),
                )

    def get(self, vinyl_id: UUID) -> VinylReleaseObject | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM vinyl_releases WHERE vinyl_id = %s",
                    (vinyl_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_vinyl(row)

    def get_by_release(self, release_id: UUID) -> VinylReleaseObject | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM vinyl_releases WHERE release_id = %s LIMIT 1",
                    (release_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_vinyl(row)

    def list_all(self) -> list[VinylReleaseObject]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM vinyl_releases ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_vinyl(row) for row in rows]

    def update(self, vinyl: VinylReleaseObject) -> None:
        self.store(vinyl)

    def summary(self) -> VinylReleaseSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_releases, "
                    "  SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS draft, "
                    "  SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready, "
                    "  SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) AS submitted, "
                    "  SUM(CASE WHEN status = 'test_pressing' THEN 1 ELSE 0 END) AS test_pressing, "
                    "  SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved, "
                    "  SUM(CASE WHEN status = 'live' THEN 1 ELSE 0 END) AS live, "
                    "  SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) AS archived, "
                    "  SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) AS blocked "
                    "FROM vinyl_releases"
                )
                row = cur.fetchone()

        if row is None:
            return VinylReleaseSummary()

        return VinylReleaseSummary(
            total_releases=int(row["total_releases"]),
            draft=int(row["draft"] or 0),
            ready=int(row["ready"] or 0),
            submitted=int(row["submitted"] or 0),
            test_pressing=int(row["test_pressing"] or 0),
            approved=int(row["approved"] or 0),
            live=int(row["live"] or 0),
            archived=int(row["archived"] or 0),
            blocked=int(row["blocked"] or 0),
        )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_vinyl(row: dict[str, Any]) -> VinylReleaseObject:
    side_a_raw = row["side_a_tracks"] or []
    side_a = [VinylTrackListing.model_validate(t) for t in side_a_raw]

    side_b_raw = row["side_b_tracks"] or []
    side_b = [VinylTrackListing.model_validate(t) for t in side_b_raw]

    readiness_raw = row["readiness_items"] or []
    readiness = [VinylReadinessItem.model_validate(r) for r in readiness_raw]

    warnings_raw = row["warnings"] or []

    return VinylReleaseObject(
        vinyl_id=row["vinyl_id"],
        release_id=row["release_id"],
        title=row["title"],
        artist=row["artist"],
        provider_group=VinylProviderGroup(row["provider_group"]),
        status=VinylReleaseStatus(row["status"]),
        format=VinylFormat(row["format"]),
        edition_type=VinylEditionType(row["edition_type"]),
        pressing_quantity=row["pressing_quantity"],
        numbered=row["numbered"],
        side_a_tracks=side_a,
        side_b_tracks=side_b,
        cover_artifact_id=row["cover_artifact_id"],
        audio_master_artifact_id=row["audio_master_artifact_id"],
        export_artifact_id=row["export_artifact_id"],
        soundcloud_job_id=row["soundcloud_job_id"],
        readiness_items=readiness,
        warnings=warnings_raw,
        notes=row["notes"] or "",
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_vinyl_repository() -> VinylRepository:
    """Construct the vinyl repository selected by SOUNDSYSTEM_VINYL_REPOSITORY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = vinyl_repository_mode()
    if mode == VinylRepositoryMode.IN_MEMORY:
        return InMemoryVinylRepository()
    if mode == VinylRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise VinylRepositoryConfigError(
                f"SOUNDSYSTEM_VINYL_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresVinylRepository(url)
    raise VinylRepositoryConfigError(f"unhandled repository mode: {mode!r}")
