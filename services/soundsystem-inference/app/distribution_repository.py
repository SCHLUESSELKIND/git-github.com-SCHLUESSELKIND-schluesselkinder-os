"""Distribution Pack Repository — S37 contract, S38 persistence.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
ReleaseRepository and MerchRepository. Switch via
``SOUNDSYSTEM_DISTRIBUTION_REPOSITORY=postgres`` with
``SOUNDSYSTEM_DATABASE_URL`` pointing to the running instance.

The Protocol defines the persistence contract. The in-memory
implementation preserves all S37 behaviour. The Postgres implementation
uses psycopg_pool with connection-pooled queries and JSONB for nested
structures.

No real Ditto API calls. No auto-publishing. No OAuth.
Distribution status remains manually tracked by the operator.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    DistributionRepositoryMode,
    database_url,
    distribution_repository_mode,
)
from app.schemas import (
    DistributionPack,
    DistributionPackStatus,
    DistributionPackSummary,
    DistributionProvider,
    DistributionReadinessItem,
    DistributionStore,
    DittoDistributionMetadata,
)


class DistributionRepositoryConfigError(RuntimeError):
    pass


class DistributionRepository(Protocol):
    """Persistence boundary for distribution packs.

    Both in-memory and Postgres implementations satisfy this protocol.
    """

    @property
    def mode(self) -> str: ...

    def store(self, pack: DistributionPack) -> None: ...

    def get(self, distribution_id: UUID) -> DistributionPack | None: ...

    def get_by_release(self, release_id: UUID) -> DistributionPack | None: ...

    def list_all(self) -> list[DistributionPack]: ...

    def update(self, pack: DistributionPack) -> None: ...

    def summary(self) -> DistributionPackSummary: ...


class InMemoryDistributionRepository:
    """In-memory distribution pack repository. Data lost on restart."""

    def __init__(self) -> None:
        self._packs: dict[UUID, DistributionPack] = {}
        self._packs_by_release: dict[UUID, UUID] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, pack: DistributionPack) -> None:
        self._packs[pack.distribution_id] = pack
        self._packs_by_release[pack.release_id] = pack.distribution_id

    def get(self, distribution_id: UUID) -> DistributionPack | None:
        return self._packs.get(distribution_id)

    def get_by_release(self, release_id: UUID) -> DistributionPack | None:
        dist_id = self._packs_by_release.get(release_id)
        if dist_id is None:
            return None
        return self._packs.get(dist_id)

    def list_all(self) -> list[DistributionPack]:
        return sorted(
            self._packs.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )

    def update(self, pack: DistributionPack) -> None:
        self._packs[pack.distribution_id] = pack

    def summary(self) -> DistributionPackSummary:
        packs = list(self._packs.values())
        return DistributionPackSummary(
            total_packs=len(packs),
            drafts=sum(1 for p in packs if p.status == DistributionPackStatus.DRAFT),
            ready=sum(1 for p in packs if p.status == DistributionPackStatus.READY),
            submitted=sum(1 for p in packs if p.status == DistributionPackStatus.SUBMITTED),
            live=sum(1 for p in packs if p.status == DistributionPackStatus.LIVE),
            rejected=sum(1 for p in packs if p.status == DistributionPackStatus.REJECTED),
            takedown=sum(1 for p in packs if p.status == DistributionPackStatus.TAKEDOWN),
        )


class PostgresDistributionRepository:
    """Postgres-backed distribution pack repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_DISTRIBUTION_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the ``db/008_distribution.sql`` migration.

    No real Ditto API calls. No auto-publishing. No OAuth.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise DistributionRepositoryConfigError(
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

    def store(self, pack: DistributionPack) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO distribution_packs "
                    "(distribution_id, release_id, provider, status, "
                    " metadata, readiness_checklist, readiness_passed, "
                    " store_targets, operator_notes, created_by, "
                    " created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (distribution_id) DO UPDATE SET "
                    "  status=EXCLUDED.status, "
                    "  metadata=EXCLUDED.metadata, "
                    "  readiness_checklist=EXCLUDED.readiness_checklist, "
                    "  readiness_passed=EXCLUDED.readiness_passed, "
                    "  store_targets=EXCLUDED.store_targets, "
                    "  operator_notes=EXCLUDED.operator_notes, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        pack.distribution_id,
                        pack.release_id,
                        pack.provider.value,
                        pack.status.value,
                        Jsonb(pack.metadata.model_dump(mode="json")),
                        Jsonb([i.model_dump(mode="json") for i in pack.readiness_checklist]),
                        pack.readiness_passed,
                        Jsonb([s.value for s in pack.store_targets]),
                        pack.operator_notes,
                        pack.created_by,
                        pack.created_at,
                        pack.updated_at,
                    ),
                )

    def get(self, distribution_id: UUID) -> DistributionPack | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM distribution_packs WHERE distribution_id = %s",
                    (distribution_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_pack(row)

    def get_by_release(self, release_id: UUID) -> DistributionPack | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM distribution_packs WHERE release_id = %s "
                    "ORDER BY created_at DESC LIMIT 1",
                    (release_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_pack(row)

    def list_all(self) -> list[DistributionPack]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM distribution_packs ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_pack(row) for row in rows]

    def update(self, pack: DistributionPack) -> None:
        # Reuse store with ON CONFLICT DO UPDATE
        self.store(pack)

    def summary(self) -> DistributionPackSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_packs, "
                    "  SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS drafts, "
                    "  SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready, "
                    "  SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) AS submitted, "
                    "  SUM(CASE WHEN status = 'live' THEN 1 ELSE 0 END) AS live, "
                    "  SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected, "
                    "  SUM(CASE WHEN status = 'takedown' THEN 1 ELSE 0 END) AS takedown "
                    "FROM distribution_packs"
                )
                row = cur.fetchone()

        if row is None:
            return DistributionPackSummary()

        return DistributionPackSummary(
            total_packs=int(row["total_packs"]),
            drafts=int(row["drafts"] or 0),
            ready=int(row["ready"] or 0),
            submitted=int(row["submitted"] or 0),
            live=int(row["live"] or 0),
            rejected=int(row["rejected"] or 0),
            takedown=int(row["takedown"] or 0),
        )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_pack(row: dict[str, Any]) -> DistributionPack:
    metadata_raw = row["metadata"] or {}
    metadata = DittoDistributionMetadata.model_validate(metadata_raw)

    readiness_raw = row["readiness_checklist"] or []
    readiness = [DistributionReadinessItem.model_validate(i) for i in readiness_raw]

    store_targets_raw = row["store_targets"] or []
    store_targets = [DistributionStore(s) for s in store_targets_raw]

    return DistributionPack(
        distribution_id=row["distribution_id"],
        release_id=row["release_id"],
        provider=DistributionProvider(row["provider"]),
        status=DistributionPackStatus(row["status"]),
        metadata=metadata,
        readiness_checklist=readiness,
        readiness_passed=bool(row["readiness_passed"]),
        store_targets=store_targets,
        operator_notes=row["operator_notes"] or "",
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_distribution_repository() -> DistributionRepository:
    """Construct the distribution repository selected by env config.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = distribution_repository_mode()
    if mode == DistributionRepositoryMode.IN_MEMORY:
        return InMemoryDistributionRepository()
    if mode == DistributionRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise DistributionRepositoryConfigError(
                f"SOUNDSYSTEM_DISTRIBUTION_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresDistributionRepository(url)
    raise DistributionRepositoryConfigError(f"unhandled repository mode: {mode!r}")
