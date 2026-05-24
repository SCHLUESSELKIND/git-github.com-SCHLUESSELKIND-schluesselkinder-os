"""Printful Sync Repository (S41).

In-memory repository for Printful product syncs. No Postgres yet.
Stores syncs by sync_id and provides capsule-based lookup.

No real Printful API calls. No product creation. No fulfillment.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas import (
    PrintfulProductSync,
    PrintfulSyncStatus,
    PrintfulSyncSummary,
)


class PrintfulSyncRepository(Protocol):
    """Persistence boundary for Printful product syncs."""

    @property
    def mode(self) -> str: ...

    def store(self, sync: PrintfulProductSync) -> None: ...

    def store_many(self, syncs: list[PrintfulProductSync]) -> None: ...

    def get(self, sync_id: UUID) -> PrintfulProductSync | None: ...

    def list_all(self) -> list[PrintfulProductSync]: ...

    def list_by_capsule(self, capsule_id: UUID) -> list[PrintfulProductSync]: ...

    def summary(self) -> PrintfulSyncSummary: ...


class InMemoryPrintfulSyncRepository:
    """In-memory Printful sync repository. Data lost on restart."""

    def __init__(self) -> None:
        self._syncs: dict[UUID, PrintfulProductSync] = {}
        self._by_capsule: dict[UUID, list[UUID]] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, sync: PrintfulProductSync) -> None:
        self._syncs[sync.sync_id] = sync
        if sync.capsule_id not in self._by_capsule:
            self._by_capsule[sync.capsule_id] = []
        if sync.sync_id not in self._by_capsule[sync.capsule_id]:
            self._by_capsule[sync.capsule_id].append(sync.sync_id)

    def store_many(self, syncs: list[PrintfulProductSync]) -> None:
        for sync in syncs:
            self.store(sync)

    def get(self, sync_id: UUID) -> PrintfulProductSync | None:
        return self._syncs.get(sync_id)

    def list_all(self) -> list[PrintfulProductSync]:
        return sorted(
            self._syncs.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )

    def list_by_capsule(self, capsule_id: UUID) -> list[PrintfulProductSync]:
        sync_ids = self._by_capsule.get(capsule_id, [])
        syncs = [self._syncs[sid] for sid in sync_ids if sid in self._syncs]
        return sorted(syncs, key=lambda s: s.created_at, reverse=True)

    def summary(self) -> PrintfulSyncSummary:
        syncs = list(self._syncs.values())
        return PrintfulSyncSummary(
            total_syncs=len(syncs),
            draft_status=sum(1 for s in syncs if s.status == PrintfulSyncStatus.DRAFT),
            exported_mock=sum(1 for s in syncs if s.status == PrintfulSyncStatus.EXPORTED_MOCK),
            blocked=sum(1 for s in syncs if s.status == PrintfulSyncStatus.BLOCKED),
            failed=sum(1 for s in syncs if s.status == PrintfulSyncStatus.FAILED),
        )
