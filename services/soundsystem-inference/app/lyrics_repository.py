from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

from app.config import (
    DATABASE_URL_ENV,
    LyricsRepositoryMode,
    database_url,
    lyrics_repository_mode,
)
from app.schemas import LyricsProject, LyricsStructure, LyricsVersion


class LyricsNotFoundError(KeyError):
    pass


class LyricsRepositoryConfigError(RuntimeError):
    pass


class LyricsRepository(Protocol):
    """Persistence boundary for lyrics projects and their versioned drafts.

    Why: every lyrics edit must produce a new version, never overwrite. This
    interface enforces the no-destructive-overwrite rule from the engine docs
    and stays storage-agnostic until Postgres lands.
    """

    def create_project(
        self, project_key: str, title: str | None, character_code: str
    ) -> LyricsProject: ...

    def get_project(self, project_id: UUID) -> LyricsProject | None: ...

    def get_project_by_key(self, project_key: str) -> LyricsProject | None: ...

    def list_projects(self) -> list[LyricsProject]: ...

    def add_version(
        self,
        project_id: UUID,
        structure: LyricsStructure,
        parent_version_id: UUID | None,
        edit_summary: str | None,
    ) -> LyricsVersion: ...

    def get_version(self, version_id: UUID) -> LyricsVersion | None: ...

    def list_versions(self, project_id: UUID) -> list[LyricsVersion]: ...


class InMemoryLyricsRepository:
    def __init__(self) -> None:
        self._projects: dict[UUID, LyricsProject] = {}
        self._projects_by_key: dict[str, UUID] = {}
        self._versions: dict[UUID, LyricsVersion] = {}
        self._versions_by_project: dict[UUID, list[UUID]] = {}

    def create_project(
        self, project_key: str, title: str | None, character_code: str
    ) -> LyricsProject:
        existing = self.get_project_by_key(project_key)
        if existing is not None:
            return existing
        project = LyricsProject(
            id=uuid4(),
            project_key=project_key,
            title=title,
            character_code=character_code,
        )
        self._projects[project.id] = project
        self._projects_by_key[project_key] = project.id
        self._versions_by_project[project.id] = []
        return project

    def get_project(self, project_id: UUID) -> LyricsProject | None:
        return self._projects.get(project_id)

    def get_project_by_key(self, project_key: str) -> LyricsProject | None:
        project_id = self._projects_by_key.get(project_key)
        if project_id is None:
            return None
        return self._projects.get(project_id)

    def list_projects(self) -> list[LyricsProject]:
        return sorted(
            self._projects.values(),
            key=lambda project: project.created_at,
            reverse=True,
        )

    def add_version(
        self,
        project_id: UUID,
        structure: LyricsStructure,
        parent_version_id: UUID | None,
        edit_summary: str | None,
    ) -> LyricsVersion:
        if project_id not in self._projects:
            raise LyricsNotFoundError(project_id)
        order = self._versions_by_project.setdefault(project_id, [])
        version = LyricsVersion(
            id=uuid4(),
            project_id=project_id,
            version=len(order) + 1,
            structure=structure,
            parent_version_id=parent_version_id,
            edit_summary=edit_summary,
        )
        self._versions[version.id] = version
        order.append(version.id)
        return version

    def get_version(self, version_id: UUID) -> LyricsVersion | None:
        return self._versions.get(version_id)

    def list_versions(self, project_id: UUID) -> list[LyricsVersion]:
        ids = self._versions_by_project.get(project_id, [])
        return [self._versions[vid] for vid in ids if vid in self._versions]


class PostgresLyricsRepository:
    """Postgres-backed lyrics repository.

    psycopg + psycopg_pool are loaded lazily so the module imports cleanly
    in environments where the postgres extra is not installed. Activate via
    `SOUNDSYSTEM_LYRICS_REPOSITORY=postgres` and `SOUNDSYSTEM_DATABASE_URL`.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise LyricsRepositoryConfigError(
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

    # --- LyricsRepository implementation -----------------------------------

    def create_project(
        self, project_key: str, title: str | None, character_code: str
    ) -> LyricsProject:
        existing = self.get_project_by_key(project_key)
        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)
        project_id = uuid4()
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO lyrics_projects "
                    "(id, project_key, title, character_code, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (project_id, project_key, title, character_code, now, now),
                )
        return LyricsProject(
            id=project_id,
            project_key=project_key,
            title=title,
            character_code=character_code,
            created_at=now,
        )

    def get_project(self, project_id: UUID) -> LyricsProject | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, project_key, title, character_code, created_at "
                    "FROM lyrics_projects WHERE id = %s",
                    (project_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_project(row)

    def get_project_by_key(self, project_key: str) -> LyricsProject | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, project_key, title, character_code, created_at "
                    "FROM lyrics_projects WHERE project_key = %s",
                    (project_key,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_project(row)

    def list_projects(self) -> list[LyricsProject]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, project_key, title, character_code, created_at "
                    "FROM lyrics_projects ORDER BY created_at DESC"
                )
                rows = cur.fetchall()
        return [_row_to_project(row) for row in rows]

    def add_version(
        self,
        project_id: UUID,
        structure: LyricsStructure,
        parent_version_id: UUID | None,
        edit_summary: str | None,
    ) -> LyricsVersion:
        from psycopg.types.json import Jsonb

        now = datetime.now(timezone.utc)
        version_id = uuid4()
        structure_payload = structure.model_dump(mode="json")
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM lyrics_projects WHERE id = %s",
                    (project_id,),
                )
                if cur.fetchone() is None:
                    raise LyricsNotFoundError(project_id)

                cur.execute(
                    "SELECT COALESCE(MAX(version_number), 0) AS max_version "
                    "FROM lyrics_versions WHERE project_id = %s",
                    (project_id,),
                )
                row = cur.fetchone()
                next_version = int(row["max_version"]) + 1 if row is not None else 1

                cur.execute(
                    "INSERT INTO lyrics_versions "
                    "(id, project_id, version_number, parent_version_id, "
                    " structure, edit_summary, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        version_id,
                        project_id,
                        next_version,
                        parent_version_id,
                        Jsonb(structure_payload),
                        edit_summary,
                        now,
                    ),
                )
                # Maintain the cached head pointer + updated_at on the project.
                cur.execute(
                    "UPDATE lyrics_projects "
                    "SET current_version_id = %s, updated_at = %s "
                    "WHERE id = %s",
                    (version_id, now, project_id),
                )
        return LyricsVersion(
            id=version_id,
            project_id=project_id,
            version=next_version,
            structure=structure,
            created_at=now,
            parent_version_id=parent_version_id,
            edit_summary=edit_summary,
        )

    def get_version(self, version_id: UUID) -> LyricsVersion | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, project_id, version_number, parent_version_id, "
                    "       structure, edit_summary, created_at "
                    "FROM lyrics_versions WHERE id = %s",
                    (version_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_version(row)

    def list_versions(self, project_id: UUID) -> list[LyricsVersion]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, project_id, version_number, parent_version_id, "
                    "       structure, edit_summary, created_at "
                    "FROM lyrics_versions WHERE project_id = %s "
                    "ORDER BY version_number ASC",
                    (project_id,),
                )
                rows = cur.fetchall()
        return [_row_to_version(row) for row in rows]


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_project(row: dict[str, Any]) -> LyricsProject:
    return LyricsProject(
        id=row["id"],
        project_key=row["project_key"],
        title=row["title"],
        character_code=row["character_code"],
        created_at=row["created_at"],
    )


def _row_to_version(row: dict[str, Any]) -> LyricsVersion:
    structure_payload = row["structure"]
    structure = LyricsStructure.model_validate(structure_payload)
    return LyricsVersion(
        id=row["id"],
        project_id=row["project_id"],
        version=int(row["version_number"]),
        structure=structure,
        parent_version_id=row["parent_version_id"],
        edit_summary=row["edit_summary"],
        created_at=row["created_at"],
    )


def build_lyrics_repository() -> LyricsRepository:
    """Construct the repository selected by SOUNDSYSTEM_LYRICS_REPOSITORY.

    Defaults to the in-memory repository. Postgres mode requires
    SOUNDSYSTEM_DATABASE_URL; otherwise this raises a clear error so the
    service fails loudly at startup.
    """
    mode = lyrics_repository_mode()
    if mode == LyricsRepositoryMode.IN_MEMORY:
        return InMemoryLyricsRepository()
    if mode == LyricsRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise LyricsRepositoryConfigError(
                f"SOUNDSYSTEM_LYRICS_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresLyricsRepository(url)
    raise LyricsRepositoryConfigError(f"unhandled repository mode: {mode!r}")
