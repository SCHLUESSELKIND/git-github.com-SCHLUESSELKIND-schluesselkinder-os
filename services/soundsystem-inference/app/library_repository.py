"""Project Library persistence layer — S19.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
LyricsRepository. Switch via `SOUNDSYSTEM_LIBRARY_REPOSITORY=postgres`
with `SOUNDSYSTEM_DATABASE_URL` pointing to the running instance.

The Protocol defines the persistence contract. The in-memory
implementation is the previous `ProjectLibraryRepository` from
`export_pack.py`, migrated here. The Postgres implementation uses
psycopg_pool with connection-pooled queries.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    LibraryRepositoryMode,
    database_url,
    library_repository_mode,
)
from app.schemas import (
    ExportPack,
    ExportPackComponent,
    ExportPackStatus,
    MusicIntentKind,
    ProjectLibraryEntry,
    ProjectLibrarySummary,
)


class LibraryRepositoryConfigError(RuntimeError):
    pass


class LibraryRepository(Protocol):
    """Persistence boundary for export packs and library entries.

    Separates storage concerns from the pure export_pack compiler.
    Both in-memory and Postgres implementations satisfy this protocol.
    """

    @property
    def mode(self) -> str: ...

    def store_pack(self, pack: ExportPack) -> None: ...

    def get_pack(self, pack_id: UUID) -> ExportPack | None: ...

    def list_packs(self) -> list[ExportPack]: ...

    def store_entry(self, entry: ProjectLibraryEntry) -> None: ...

    def get_entry(self, entry_id: UUID) -> ProjectLibraryEntry | None: ...

    def get_entry_by_pack(self, pack_id: UUID) -> ProjectLibraryEntry | None: ...

    def list_entries(self) -> list[ProjectLibraryEntry]: ...

    def summary(self) -> ProjectLibrarySummary: ...

    @property
    def count(self) -> int: ...


class InMemoryLibraryRepository:
    """In-memory library repository. Data lost on restart."""

    def __init__(self) -> None:
        self._packs: dict[UUID, ExportPack] = {}
        self._entries: dict[UUID, ProjectLibraryEntry] = {}
        self._pack_to_entry: dict[UUID, UUID] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store_pack(self, pack: ExportPack) -> None:
        self._packs[pack.pack_id] = pack

    def get_pack(self, pack_id: UUID) -> ExportPack | None:
        return self._packs.get(pack_id)

    def list_packs(self) -> list[ExportPack]:
        return sorted(
            self._packs.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )

    def store_entry(self, entry: ProjectLibraryEntry) -> None:
        self._entries[entry.entry_id] = entry
        self._pack_to_entry[entry.pack_id] = entry.entry_id

    def get_entry(self, entry_id: UUID) -> ProjectLibraryEntry | None:
        return self._entries.get(entry_id)

    def get_entry_by_pack(self, pack_id: UUID) -> ProjectLibraryEntry | None:
        entry_id = self._pack_to_entry.get(pack_id)
        if entry_id is None:
            return None
        return self._entries.get(entry_id)

    def list_entries(self) -> list[ProjectLibraryEntry]:
        return sorted(
            self._entries.values(),
            key=lambda e: e.created_at,
            reverse=True,
        )

    def summary(self) -> ProjectLibrarySummary:
        entries = list(self._entries.values())
        return ProjectLibrarySummary(
            total_entries=len(entries),
            total_packs=len(self._packs),
            entries_with_lyrics=sum(1 for e in entries if e.has_lyrics),
            entries_with_arrangements=sum(1 for e in entries if e.has_arrangement),
            entries_with_provenance=sum(1 for e in entries if e.has_provenance),
        )

    @property
    def count(self) -> int:
        return len(self._entries)


class PostgresLibraryRepository:
    """Postgres-backed library repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_LIBRARY_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the `db/004_library.sql` migration.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise LibraryRepositoryConfigError(
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

    def store_pack(self, pack: ExportPack) -> None:
        from psycopg.types.json import Jsonb

        components_json = [c.model_dump(mode="json") for c in pack.components]
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO library_packs "
                    "(pack_id, title, status, music_job_id, lyrics_version_id, "
                    " arrangement_id, provenance_id, components, total_components, "
                    " estimated_duration_seconds, bpm, key_signature, intent, "
                    " operator_id, notes, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (pack_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, status=EXCLUDED.status, "
                    "  components=EXCLUDED.components, total_components=EXCLUDED.total_components, "
                    "  notes=EXCLUDED.notes",
                    (
                        pack.pack_id,
                        pack.title,
                        pack.status.value,
                        pack.music_job_id,
                        pack.lyrics_version_id,
                        pack.arrangement_id,
                        pack.provenance_id,
                        Jsonb(components_json),
                        pack.total_components,
                        pack.estimated_duration_seconds,
                        pack.bpm,
                        pack.key_signature,
                        pack.intent.value if pack.intent else None,
                        pack.operator_id,
                        pack.notes,
                        pack.created_at,
                    ),
                )

    def get_pack(self, pack_id: UUID) -> ExportPack | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM library_packs WHERE pack_id = %s",
                    (pack_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_pack(row)

    def list_packs(self) -> list[ExportPack]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM library_packs ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_pack(row) for row in rows]

    def store_entry(self, entry: ProjectLibraryEntry) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO library_entries "
                    "(entry_id, pack_id, title, slug, intent, status, bpm, "
                    " key_signature, estimated_duration_seconds, component_count, "
                    " artifact_count, has_lyrics, has_arrangement, has_provenance, "
                    " operator_id, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (entry_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, status=EXCLUDED.status",
                    (
                        entry.entry_id,
                        entry.pack_id,
                        entry.title,
                        entry.slug,
                        entry.intent.value if entry.intent else None,
                        entry.status.value,
                        entry.bpm,
                        entry.key_signature,
                        entry.estimated_duration_seconds,
                        entry.component_count,
                        entry.artifact_count,
                        entry.has_lyrics,
                        entry.has_arrangement,
                        entry.has_provenance,
                        entry.operator_id,
                        entry.created_at,
                    ),
                )

    def get_entry(self, entry_id: UUID) -> ProjectLibraryEntry | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM library_entries WHERE entry_id = %s",
                    (entry_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_entry(row)

    def get_entry_by_pack(self, pack_id: UUID) -> ProjectLibraryEntry | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM library_entries WHERE pack_id = %s",
                    (pack_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_entry(row)

    def list_entries(self) -> list[ProjectLibraryEntry]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM library_entries ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_entry(row) for row in rows]

    def summary(self) -> ProjectLibrarySummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_entries, "
                    "  SUM(CASE WHEN has_lyrics THEN 1 ELSE 0 END) AS entries_with_lyrics, "
                    "  SUM(CASE WHEN has_arrangement THEN 1 ELSE 0 END) AS entries_with_arrangements, "
                    "  SUM(CASE WHEN has_provenance THEN 1 ELSE 0 END) AS entries_with_provenance "
                    "FROM library_entries"
                )
                row = cur.fetchone()
                cur.execute("SELECT COUNT(*) AS total_packs FROM library_packs")
                packs_row = cur.fetchone()
        return ProjectLibrarySummary(
            total_entries=int(row["total_entries"]) if row else 0,
            total_packs=int(packs_row["total_packs"]) if packs_row else 0,
            entries_with_lyrics=int(row["entries_with_lyrics"] or 0) if row else 0,
            entries_with_arrangements=int(row["entries_with_arrangements"] or 0) if row else 0,
            entries_with_provenance=int(row["entries_with_provenance"] or 0) if row else 0,
        )

    @property
    def count(self) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM library_entries")
                row = cur.fetchone()
        return int(row["cnt"]) if row else 0


# ---------- Row Mappers ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_pack(row: dict[str, Any]) -> ExportPack:
    components_raw = row["components"] or []
    components = [ExportPackComponent.model_validate(c) for c in components_raw]
    return ExportPack(
        pack_id=row["pack_id"],
        title=row["title"],
        status=ExportPackStatus(row["status"]),
        music_job_id=row["music_job_id"],
        lyrics_version_id=row["lyrics_version_id"],
        arrangement_id=row["arrangement_id"],
        provenance_id=row["provenance_id"],
        components=components,
        total_components=int(row["total_components"]),
        estimated_duration_seconds=row["estimated_duration_seconds"],
        bpm=row["bpm"],
        key_signature=row["key_signature"],
        intent=MusicIntentKind(row["intent"]) if row["intent"] else None,
        operator_id=row["operator_id"],
        notes=row["notes"],
        created_at=row["created_at"],
    )


def _row_to_entry(row: dict[str, Any]) -> ProjectLibraryEntry:
    return ProjectLibraryEntry(
        entry_id=row["entry_id"],
        pack_id=row["pack_id"],
        title=row["title"],
        slug=row["slug"],
        intent=MusicIntentKind(row["intent"]) if row["intent"] else None,
        status=ExportPackStatus(row["status"]),
        bpm=row["bpm"],
        key_signature=row["key_signature"],
        estimated_duration_seconds=row["estimated_duration_seconds"],
        component_count=int(row["component_count"]),
        artifact_count=int(row["artifact_count"]),
        has_lyrics=bool(row["has_lyrics"]),
        has_arrangement=bool(row["has_arrangement"]),
        has_provenance=bool(row["has_provenance"]),
        operator_id=row["operator_id"],
        created_at=row["created_at"],
    )


# ---------- Factory ----------


def build_library_repository() -> LibraryRepository:
    """Construct the library repository selected by SOUNDSYSTEM_LIBRARY_REPOSITORY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = library_repository_mode()
    if mode == LibraryRepositoryMode.IN_MEMORY:
        return InMemoryLibraryRepository()
    if mode == LibraryRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise LibraryRepositoryConfigError(
                f"SOUNDSYSTEM_LIBRARY_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresLibraryRepository(url)
    raise LibraryRepositoryConfigError(f"unhandled repository mode: {mode!r}")
