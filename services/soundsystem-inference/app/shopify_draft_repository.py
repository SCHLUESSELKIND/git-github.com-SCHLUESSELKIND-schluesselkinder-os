"""Shopify Draft Repository (S40).

In-memory repository for Shopify product drafts. No Postgres yet.
Stores drafts by draft_id and provides capsule-based lookup.

No real Shopify API calls. No publishing. No inventory mutation.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas import (
    ShopifyDraftStatus,
    ShopifyDraftSummary,
    ShopifyProductDraft,
)


class ShopifyDraftRepository(Protocol):
    """Persistence boundary for Shopify product drafts."""

    @property
    def mode(self) -> str: ...

    def store(self, draft: ShopifyProductDraft) -> None: ...

    def store_many(self, drafts: list[ShopifyProductDraft]) -> None: ...

    def get(self, draft_id: UUID) -> ShopifyProductDraft | None: ...

    def list_all(self) -> list[ShopifyProductDraft]: ...

    def list_by_capsule(self, capsule_id: UUID) -> list[ShopifyProductDraft]: ...

    def summary(self) -> ShopifyDraftSummary: ...


class InMemoryShopifyDraftRepository:
    """In-memory Shopify draft repository. Data lost on restart."""

    def __init__(self) -> None:
        self._drafts: dict[UUID, ShopifyProductDraft] = {}
        self._by_capsule: dict[UUID, list[UUID]] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, draft: ShopifyProductDraft) -> None:
        self._drafts[draft.draft_id] = draft
        if draft.capsule_id not in self._by_capsule:
            self._by_capsule[draft.capsule_id] = []
        if draft.draft_id not in self._by_capsule[draft.capsule_id]:
            self._by_capsule[draft.capsule_id].append(draft.draft_id)

    def store_many(self, drafts: list[ShopifyProductDraft]) -> None:
        for draft in drafts:
            self.store(draft)

    def get(self, draft_id: UUID) -> ShopifyProductDraft | None:
        return self._drafts.get(draft_id)

    def list_all(self) -> list[ShopifyProductDraft]:
        return sorted(
            self._drafts.values(),
            key=lambda d: d.created_at,
            reverse=True,
        )

    def list_by_capsule(self, capsule_id: UUID) -> list[ShopifyProductDraft]:
        draft_ids = self._by_capsule.get(capsule_id, [])
        drafts = [self._drafts[did] for did in draft_ids if did in self._drafts]
        return sorted(drafts, key=lambda d: d.created_at, reverse=True)

    def summary(self) -> ShopifyDraftSummary:
        drafts = list(self._drafts.values())
        return ShopifyDraftSummary(
            total_drafts=len(drafts),
            draft_status=sum(1 for d in drafts if d.status == ShopifyDraftStatus.DRAFT),
            exported_mock=sum(1 for d in drafts if d.status == ShopifyDraftStatus.EXPORTED_MOCK),
            blocked=sum(1 for d in drafts if d.status == ShopifyDraftStatus.BLOCKED),
            failed=sum(1 for d in drafts if d.status == ShopifyDraftStatus.FAILED),
        )
