"""Intelligence Snapshot Repository — S54 persistence.

Protocol + InMemory + Postgres factory. Stores frozen IntelligenceOverview
snapshots over time. Created only by explicit operator POST.
No automation. No scheduler. No background workers.
"""

from __future__ import annotations

import os
from typing import Protocol
from uuid import UUID

from app.config import (
    DATABASE_URL_ENV,
    IntelligenceSnapshotRepositoryConfigError,
    IntelligenceSnapshotRepositoryMode,
    intelligence_snapshot_repository_mode,
)
from app.schemas import (
    IntelligenceSnapshot,
    IntelligenceSnapshotStatus,
    IntelligenceSnapshotSummary,
)


class IntelligenceSnapshotRepository(Protocol):
    """Persistence boundary for intelligence snapshots."""

    @property
    def mode(self) -> str: ...

    def add_snapshot(self, snapshot: IntelligenceSnapshot) -> None: ...

    def get_snapshot(self, snapshot_id: UUID) -> IntelligenceSnapshot | None: ...

    def list_snapshots(
        self,
        *,
        status: IntelligenceSnapshotStatus | None = None,
        limit: int = 50,
    ) -> list[IntelligenceSnapshot]: ...

    def summary(self) -> IntelligenceSnapshotSummary: ...


class InMemoryIntelligenceSnapshotRepository:
    """In-memory snapshot repository. Data lost on restart."""

    def __init__(self) -> None:
        self._snapshots: list[IntelligenceSnapshot] = []

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_snapshot(self, snapshot: IntelligenceSnapshot) -> None:
        # Mark previous 'created' snapshots as superseded
        for existing in self._snapshots:
            if existing.status == IntelligenceSnapshotStatus.CREATED:
                existing.status = IntelligenceSnapshotStatus.SUPERSEDED
        self._snapshots.append(snapshot)

    def get_snapshot(self, snapshot_id: UUID) -> IntelligenceSnapshot | None:
        for snapshot in self._snapshots:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None

    def list_snapshots(
        self,
        *,
        status: IntelligenceSnapshotStatus | None = None,
        limit: int = 50,
    ) -> list[IntelligenceSnapshot]:
        result = self._snapshots
        if status is not None:
            result = [s for s in result if s.status == status]
        result = sorted(result, key=lambda s: s.created_at, reverse=True)
        return result[:limit]

    def summary(self) -> IntelligenceSnapshotSummary:
        total = len(self._snapshots)
        active = sum(
            1
            for s in self._snapshots
            if s.status
            in (IntelligenceSnapshotStatus.CREATED, IntelligenceSnapshotStatus.SUPERSEDED)
        )
        archived = sum(
            1 for s in self._snapshots if s.status == IntelligenceSnapshotStatus.ARCHIVED
        )

        sorted_snaps = sorted(self._snapshots, key=lambda s: s.created_at, reverse=True)
        latest_at = sorted_snaps[0].created_at if sorted_snaps else None
        latest_heat = sorted_snaps[0].overview.total_heat if sorted_snaps else 0.0

        heat_delta: float | None = None
        if len(sorted_snaps) >= 2:
            heat_delta = round(
                sorted_snaps[0].overview.total_heat - sorted_snaps[1].overview.total_heat,
                2,
            )

        return IntelligenceSnapshotSummary(
            total_snapshots=total,
            active_snapshots=active,
            archived_snapshots=archived,
            latest_snapshot_at=latest_at,
            latest_total_heat=latest_heat,
            heat_delta_from_previous=heat_delta,
        )


class PostgresIntelligenceSnapshotRepository:
    """Postgres-backed snapshot repository. S54.

    Placeholder — delegates to InMemory until a real connection pool
    is wired. Raises IntelligenceSnapshotRepositoryConfigError if
    DATABASE_URL is missing when instantiated.
    """

    def __init__(self) -> None:
        db_url = os.environ.get(DATABASE_URL_ENV, "").strip()
        if not db_url:
            raise IntelligenceSnapshotRepositoryConfigError(
                f"postgres mode requires {DATABASE_URL_ENV} to be set"
            )
        self._db_url = db_url
        self._inner = InMemoryIntelligenceSnapshotRepository()

    @property
    def mode(self) -> str:
        return "postgres"

    def add_snapshot(self, snapshot: IntelligenceSnapshot) -> None:
        self._inner.add_snapshot(snapshot)

    def get_snapshot(self, snapshot_id: UUID) -> IntelligenceSnapshot | None:
        return self._inner.get_snapshot(snapshot_id)

    def list_snapshots(
        self,
        *,
        status: IntelligenceSnapshotStatus | None = None,
        limit: int = 50,
    ) -> list[IntelligenceSnapshot]:
        return self._inner.list_snapshots(status=status, limit=limit)

    def summary(self) -> IntelligenceSnapshotSummary:
        return self._inner.summary()


def build_intelligence_snapshot_repository() -> IntelligenceSnapshotRepository:
    """Factory — returns InMemory or Postgres snapshot repository based on config."""
    mode = intelligence_snapshot_repository_mode()
    if mode == IntelligenceSnapshotRepositoryMode.POSTGRES:
        return PostgresIntelligenceSnapshotRepository()  # type: ignore[return-value]
    return InMemoryIntelligenceSnapshotRepository()  # type: ignore[return-value]
