"""Merch Capsule Repository — S37 contract, S38 persistence.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
ReleaseRepository. Switch via ``SOUNDSYSTEM_MERCH_REPOSITORY=postgres``
with ``SOUNDSYSTEM_DATABASE_URL`` pointing to the running instance.

The Protocol defines the persistence contract. The in-memory
implementation preserves all S37 behaviour. The Postgres implementation
uses psycopg_pool with connection-pooled queries and JSONB for nested
structures.

No real commerce API calls. No Printful, TikTok Shop, or Shopify calls.
Provider export remains mock-only.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    MerchRepositoryMode,
    database_url,
    merch_repository_mode,
)
from app.schemas import (
    MerchCapsule,
    MerchCapsuleStatus,
    MerchCapsuleSummary,
    MerchCapsuleWarning,
    MerchProduct,
    MerchProviderGroup,
)


class MerchRepositoryConfigError(RuntimeError):
    pass


class MerchRepository(Protocol):
    """Persistence boundary for merch capsules.

    Both in-memory and Postgres implementations satisfy this protocol.
    """

    @property
    def mode(self) -> str: ...

    def store(self, capsule: MerchCapsule) -> None: ...

    def get(self, capsule_id: UUID) -> MerchCapsule | None: ...

    def list_all(self) -> list[MerchCapsule]: ...

    def update(self, capsule: MerchCapsule) -> None: ...

    def summary(self) -> MerchCapsuleSummary: ...


class InMemoryMerchCapsuleRepository:
    """In-memory merch capsule repository. Data lost on restart."""

    def __init__(self) -> None:
        self._capsules: dict[UUID, MerchCapsule] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, capsule: MerchCapsule) -> None:
        self._capsules[capsule.capsule_id] = capsule

    def get(self, capsule_id: UUID) -> MerchCapsule | None:
        return self._capsules.get(capsule_id)

    def list_all(self) -> list[MerchCapsule]:
        return sorted(
            self._capsules.values(),
            key=lambda c: c.created_at,
            reverse=True,
        )

    def update(self, capsule: MerchCapsule) -> None:
        self._capsules[capsule.capsule_id] = capsule

    def summary(self) -> MerchCapsuleSummary:
        capsules = list(self._capsules.values())
        all_products = [p for c in capsules for p in c.products]
        return MerchCapsuleSummary(
            total_capsules=len(capsules),
            drafts=sum(1 for c in capsules if c.status == MerchCapsuleStatus.DRAFT),
            locked=sum(1 for c in capsules if c.status == MerchCapsuleStatus.LOCKED),
            exported_mock=sum(1 for c in capsules if c.status == MerchCapsuleStatus.EXPORTED_MOCK),
            archived=sum(1 for c in capsules if c.status == MerchCapsuleStatus.ARCHIVED),
            total_products=len(all_products),
            total_active_products=sum(1 for p in all_products if p.active),
        )


class PostgresMerchCapsuleRepository:
    """Postgres-backed merch capsule repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_MERCH_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the ``db/007_merch.sql`` migration.

    No real commerce API calls. No Printful/TikTok Shop/Shopify calls.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise MerchRepositoryConfigError(
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

    def store(self, capsule: MerchCapsule) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO merch_capsules "
                    "(capsule_id, release_id, title, artist, status, "
                    " availability_strategy, products, max_active_products, "
                    " provider_groups, drop_window_start, drop_window_end, "
                    " notes, warnings, created_by, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (capsule_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, artist=EXCLUDED.artist, "
                    "  status=EXCLUDED.status, "
                    "  availability_strategy=EXCLUDED.availability_strategy, "
                    "  products=EXCLUDED.products, "
                    "  max_active_products=EXCLUDED.max_active_products, "
                    "  provider_groups=EXCLUDED.provider_groups, "
                    "  drop_window_start=EXCLUDED.drop_window_start, "
                    "  drop_window_end=EXCLUDED.drop_window_end, "
                    "  notes=EXCLUDED.notes, "
                    "  warnings=EXCLUDED.warnings, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        capsule.capsule_id,
                        capsule.release_id,
                        capsule.title,
                        capsule.artist,
                        capsule.status.value,
                        capsule.availability_strategy,
                        Jsonb([p.model_dump(mode="json") for p in capsule.products]),
                        capsule.max_active_products,
                        Jsonb([g.value for g in capsule.provider_groups]),
                        capsule.drop_window_start,
                        capsule.drop_window_end,
                        capsule.notes,
                        Jsonb([w.model_dump(mode="json") for w in capsule.warnings]),
                        capsule.created_by,
                        capsule.created_at,
                        capsule.updated_at,
                    ),
                )

    def get(self, capsule_id: UUID) -> MerchCapsule | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM merch_capsules WHERE capsule_id = %s",
                    (capsule_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_capsule(row)

    def list_all(self) -> list[MerchCapsule]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM merch_capsules ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_capsule(row) for row in rows]

    def update(self, capsule: MerchCapsule) -> None:
        # Reuse store with ON CONFLICT DO UPDATE
        self.store(capsule)

    def summary(self) -> MerchCapsuleSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_capsules, "
                    "  SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS drafts, "
                    "  SUM(CASE WHEN status = 'locked' THEN 1 ELSE 0 END) AS locked, "
                    "  SUM(CASE WHEN status = 'exported_mock' THEN 1 ELSE 0 END) AS exported_mock, "
                    "  SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) AS archived "
                    "FROM merch_capsules"
                )
                row = cur.fetchone()

        if row is None:
            return MerchCapsuleSummary(
                total_capsules=0,
                drafts=0,
                locked=0,
                exported_mock=0,
                archived=0,
                total_products=0,
                total_active_products=0,
            )

        # For product counts, we need to read all capsules (JSONB aggregation)
        total_products = 0
        total_active = 0
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT products FROM merch_capsules")
                for prow in cur:
                    products_raw = prow["products"] or []
                    total_products += len(products_raw)
                    total_active += sum(1 for p in products_raw if p.get("active", False))

        return MerchCapsuleSummary(
            total_capsules=int(row["total_capsules"]),
            drafts=int(row["drafts"] or 0),
            locked=int(row["locked"] or 0),
            exported_mock=int(row["exported_mock"] or 0),
            archived=int(row["archived"] or 0),
            total_products=total_products,
            total_active_products=total_active,
        )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_capsule(row: dict[str, Any]) -> MerchCapsule:
    products_raw = row["products"] or []
    products = [MerchProduct.model_validate(p) for p in products_raw]

    provider_groups_raw = row["provider_groups"] or []
    provider_groups = [MerchProviderGroup(g) for g in provider_groups_raw]

    warnings_raw = row["warnings"] or []
    warnings = [MerchCapsuleWarning.model_validate(w) for w in warnings_raw]

    return MerchCapsule(
        capsule_id=row["capsule_id"],
        release_id=row["release_id"],
        title=row["title"],
        artist=row["artist"],
        status=MerchCapsuleStatus(row["status"]),
        availability_strategy=row["availability_strategy"],
        products=products,
        max_active_products=int(row["max_active_products"]),
        provider_groups=provider_groups,
        drop_window_start=row["drop_window_start"],
        drop_window_end=row["drop_window_end"],
        notes=row["notes"] or "",
        warnings=warnings,
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_merch_repository() -> MerchRepository:
    """Construct the merch repository selected by SOUNDSYSTEM_MERCH_REPOSITORY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = merch_repository_mode()
    if mode == MerchRepositoryMode.IN_MEMORY:
        return InMemoryMerchCapsuleRepository()
    if mode == MerchRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise MerchRepositoryConfigError(
                f"SOUNDSYSTEM_MERCH_REPOSITORY=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresMerchCapsuleRepository(url)
    raise MerchRepositoryConfigError(f"unhandled repository mode: {mode!r}")
