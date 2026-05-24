"""TikTok Shop Listing Repository (S42).

In-memory repository for TikTok Shop listing drafts. No Postgres yet.
Stores listings by listing_id and provides capsule-based lookup.

No real TikTok Shop API calls. No product creation. No publishing.
No inventory mutation.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas import (
    TikTokShopListing,
    TikTokShopListingStatus,
    TikTokShopSummary,
)


class TikTokShopRepository(Protocol):
    """Persistence boundary for TikTok Shop listing drafts."""

    @property
    def mode(self) -> str: ...

    def store(self, listing: TikTokShopListing) -> None: ...

    def store_many(self, listings: list[TikTokShopListing]) -> None: ...

    def get(self, listing_id: UUID) -> TikTokShopListing | None: ...

    def list_all(self) -> list[TikTokShopListing]: ...

    def list_by_capsule(self, capsule_id: UUID) -> list[TikTokShopListing]: ...

    def summary(self) -> TikTokShopSummary: ...


class InMemoryTikTokShopRepository:
    """In-memory TikTok Shop listing repository. Data lost on restart."""

    def __init__(self) -> None:
        self._listings: dict[UUID, TikTokShopListing] = {}
        self._by_capsule: dict[UUID, list[UUID]] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, listing: TikTokShopListing) -> None:
        self._listings[listing.listing_id] = listing
        if listing.capsule_id not in self._by_capsule:
            self._by_capsule[listing.capsule_id] = []
        if listing.listing_id not in self._by_capsule[listing.capsule_id]:
            self._by_capsule[listing.capsule_id].append(listing.listing_id)

    def store_many(self, listings: list[TikTokShopListing]) -> None:
        for listing in listings:
            self.store(listing)

    def get(self, listing_id: UUID) -> TikTokShopListing | None:
        return self._listings.get(listing_id)

    def list_all(self) -> list[TikTokShopListing]:
        return sorted(
            self._listings.values(),
            key=lambda entry: entry.created_at,
            reverse=True,
        )

    def list_by_capsule(self, capsule_id: UUID) -> list[TikTokShopListing]:
        listing_ids = self._by_capsule.get(capsule_id, [])
        listings = [self._listings[lid] for lid in listing_ids if lid in self._listings]
        return sorted(listings, key=lambda entry: entry.created_at, reverse=True)

    def summary(self) -> TikTokShopSummary:
        listings = list(self._listings.values())
        return TikTokShopSummary(
            total_listings=len(listings),
            draft_status=sum(
                1 for entry in listings if entry.status == TikTokShopListingStatus.DRAFT
            ),
            exported_mock=sum(
                1 for entry in listings if entry.status == TikTokShopListingStatus.EXPORTED_MOCK
            ),
            blocked=sum(1 for entry in listings if entry.status == TikTokShopListingStatus.BLOCKED),
            failed=sum(1 for entry in listings if entry.status == TikTokShopListingStatus.FAILED),
        )
