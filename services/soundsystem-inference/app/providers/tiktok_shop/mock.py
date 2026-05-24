"""Mock TikTok Shop Listing Provider (S42).

Default provider — no external dependencies, deterministic results.
No real TikTok Shop API calls. No product creation. No publishing.
Safe for tests and local development.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import (
    MerchCapsule,
    TikTokShopListing,
    TikTokShopListingExport,
    TikTokShopListingStatus,
)
from app.tiktok_shop_builder import build_all_listings


class MockTikTokShopProvider:
    """Mock implementation — builds listing payloads without TikTok Shop API calls.

    Supported products get status=exported_mock.
    Blocked products (vinyl) keep status=blocked.
    No product creation. No publishing.
    """

    name: str = "mock"

    def build_listings(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[TikTokShopListing]:
        """Convert capsule products into TikTok Shop listing drafts."""
        listings = build_all_listings(capsule, operator_id=operator_id)
        return [
            listing.model_copy(
                update={
                    "status": TikTokShopListingStatus.EXPORTED_MOCK
                    if listing.status != TikTokShopListingStatus.BLOCKED
                    else TikTokShopListingStatus.BLOCKED,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            for listing in listings
        ]

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> TikTokShopListingExport:
        """Build a complete listing export payload for the capsule."""
        listings = self.build_listings(capsule, operator_id=operator_id)
        total_warnings = sum(len(listing.warnings) for listing in listings)
        return TikTokShopListingExport(
            capsule_id=capsule.capsule_id,
            listings=listings,
            provider_mode="mock",
            total_products=len(listings),
            total_warnings=total_warnings,
        )
