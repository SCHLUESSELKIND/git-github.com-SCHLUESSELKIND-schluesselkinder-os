"""Release Pack persistence layer — S23.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
LibraryRepository. Switch via `SOUNDSYSTEM_RELEASE_REPOSITORY=postgres`
with `SOUNDSYSTEM_DATABASE_URL` pointing to the running instance.

The Protocol defines the persistence contract. The in-memory
implementation is the `ReleasePackRepository` from `release_pack.py`,
migrated here. The Postgres implementation uses psycopg_pool with
connection-pooled queries and JSONB for nested structures.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    ReleaseRepositoryMode,
    database_url,
    release_repository_mode,
)
from app.schemas import (
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    ReleasePackSummary,
    SocialCopy,
)


class ReleaseRepositoryConfigError(RuntimeError):
    pass


class ReleaseRepository(Protocol):
    """Persistence boundary for release packs.

    Separates storage concerns from the pure release_pack builder.
    Both in-memory and Postgres implementations satisfy this protocol.
    """

    @property
    def mode(self) -> str: ...

    def store(self, release: ReleasePack) -> None: ...

    def get(self, release_id: UUID) -> ReleasePack | None: ...

    def get_by_pack(self, pack_id: UUID) -> ReleasePack | None: ...

    def list_all(self) -> list[ReleasePack]: ...

    def update(self, release: ReleasePack) -> None: ...

    def summary(self) -> ReleasePackSummary: ...


class InMemoryReleaseRepository:
    """In-memory release repository. Data lost on restart."""

    def __init__(self) -> None:
        self._releases: dict[UUID, ReleasePack] = {}
        self._releases_by_pack: dict[UUID, UUID] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, release: ReleasePack) -> None:
        self._releases[release.release_id] = release
        self._releases_by_pack[release.pack_id] = release.release_id

    def get(self, release_id: UUID) -> ReleasePack | None:
        return self._releases.get(release_id)

    def get_by_pack(self, pack_id: UUID) -> ReleasePack | None:
        release_id = self._releases_by_pack.get(pack_id)
        if release_id is None:
            return None
        return self._releases.get(release_id)

    def list_all(self) -> list[ReleasePack]:
        return sorted(
            self._releases.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )

    def update(self, release: ReleasePack) -> None:
        self._releases[release.release_id] = release

    def summary(self) -> ReleasePackSummary:
        releases = list(self._releases.values())
        return ReleasePackSummary(
            total_releases=len(releases),
            drafts=sum(1 for r in releases if r.status == ReleasePackStatus.DRAFT),
            ready=sum(1 for r in releases if r.status == ReleasePackStatus.READY),
            published=sum(1 for r in releases if r.status == ReleasePackStatus.PUBLISHED),
            compliance_passed=sum(1 for r in releases if r.compliance_passed),
        )


class PostgresReleaseRepository:
    """Postgres-backed release repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_RELEASE_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the `db/005_releases.sql` migration.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise ReleaseRepositoryConfigError(
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

    def store(self, release: ReleasePack) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO release_packs "
                    "(release_id, pack_id, title, artist, status, description, "
                    " social_copy, compliance_checklist, compliance_passed, "
                    " assets, dropbox_target, genre, bpm, key_signature, "
                    " duration_seconds, operator_id, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (release_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, artist=EXCLUDED.artist, "
                    "  status=EXCLUDED.status, description=EXCLUDED.description, "
                    "  social_copy=EXCLUDED.social_copy, "
                    "  compliance_checklist=EXCLUDED.compliance_checklist, "
                    "  compliance_passed=EXCLUDED.compliance_passed, "
                    "  assets=EXCLUDED.assets, "
                    "  dropbox_target=EXCLUDED.dropbox_target, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        release.release_id,
                        release.pack_id,
                        release.title,
                        release.artist,
                        release.status.value,
                        release.description,
                        Jsonb(release.social_copy.model_dump(mode="json")),
                        Jsonb([c.model_dump(mode="json") for c in release.compliance_checklist]),
                        release.compliance_passed,
                        Jsonb([a.model_dump(mode="json") for a in release.assets]),
                        release.dropbox_target,
                        release.genre,
                        release.bpm,
                        release.key_signature,
                        release.duration_seconds,
                        release.operator_id,
                        release.created_at,
                        release.updated_at,
                    ),
                )

    def get(self, release_id: UUID) -> ReleasePack | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM release_packs WHERE release_id = %s",
                    (release_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_release(row)

    def get_by_pack(self, pack_id: UUID) -> ReleasePack | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM release_packs WHERE pack_id = %s",
                    (pack_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_release(row)

    def list_all(self) -> list[ReleasePack]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM release_packs ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_release(row) for row in rows]

    def update(self, release: ReleasePack) -> None:
        # Reuse store with ON CONFLICT DO UPDATE
        self.store(release)

    def summary(self) -> ReleasePackSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_releases, "
                    "  SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS drafts, "
                    "  SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready, "
                    "  SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) AS published, "
                    "  SUM(CASE WHEN compliance_passed THEN 1 ELSE 0 END) AS compliance_passed "
                    "FROM release_packs"
                )
                row = cur.fetchone()
        if row is None:
            return ReleasePackSummary(
                total_releases=0, drafts=0, ready=0, published=0, compliance_passed=0
            )
        return ReleasePackSummary(
            total_releases=int(row["total_releases"]),
            drafts=int(row["drafts"] or 0),
            ready=int(row["ready"] or 0),
            published=int(row["published"] or 0),
            compliance_passed=int(row["compliance_passed"] or 0),
        )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_release(row: dict[str, Any]) -> ReleasePack:
    social_copy_raw = row["social_copy"] or {}
    social_copy = SocialCopy.model_validate(social_copy_raw)

    checklist_raw = row["compliance_checklist"] or []
    checklist = [ComplianceChecklistItem.model_validate(c) for c in checklist_raw]

    assets_raw = row["assets"] or []
    assets = [ReleaseAssetPlaceholder.model_validate(a) for a in assets_raw]

    return ReleasePack(
        release_id=row["release_id"],
        pack_id=row["pack_id"],
        title=row["title"],
        artist=row["artist"],
        status=ReleasePackStatus(row["status"]),
        description=row["description"] or "",
        social_copy=social_copy,
        compliance_checklist=checklist,
        compliance_passed=bool(row["compliance_passed"]),
        assets=assets,
        dropbox_target=row["dropbox_target"],
        genre=row["genre"],
        bpm=row["bpm"],
        key_signature=row["key_signature"],
        duration_seconds=row["duration_seconds"],
        operator_id=row["operator_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_release_repository() -> ReleaseRepository:
    """Construct the release repository selected by SOUNDSYSTEM_RELEASE_REPOSITORY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = release_repository_mode()
    if mode == ReleaseRepositoryMode.IN_MEMORY:
        return InMemoryReleaseRepository()
    if mode == ReleaseRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise ReleaseRepositoryConfigError(
                f"SOUNDSYSTEM_RELEASE_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresReleaseRepository(url)
    raise ReleaseRepositoryConfigError(f"unhandled repository mode: {mode!r}")
