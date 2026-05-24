"""Real TikTok Shop Listing Provider Boundary (S42).

Stub implementation — validates config exists but does NOT call the
TikTok Shop API. All listings return BLOCKED status.

This provider exists as the architectural boundary for future TikTok
Shop integration. No real API calls will be made until the integration
is approved and implemented.

Hard rules:
- No TikTok Shop API calls.
- No product creation on TikTok Shop.
- No publishing. No inventory mutation.
- Listings return BLOCKED with clear message.
- Credentials are never logged or returned in API responses.
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


class RealTikTokShopProvider:
    """Real TikTok Shop provider boundary — no API calls yet.

    Config is validated at factory construction time. This class
    exists as the provider boundary for future TikTok Shop API
    integration.
    """

    name: str = "tiktok_shop"

    def build_listings(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[TikTokShopListing]:
        """Convert capsule products into listings — all marked BLOCKED."""
        listings = build_all_listings(capsule, operator_id=operator_id)
        return [
            listing.model_copy(
                update={
                    "status": TikTokShopListingStatus.BLOCKED,
                    "warnings": listing.warnings
                    + [
                        "Real TikTok Shop provider is selected but listing "
                        "creation is not yet implemented. No TikTok Shop API "
                        "call will be made."
                    ],
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
        """Build export payload — all listings BLOCKED."""
        listings = self.build_listings(capsule, operator_id=operator_id)
        total_warnings = sum(len(listing.warnings) for listing in listings)
        return TikTokShopListingExport(
            capsule_id=capsule.capsule_id,
            listings=listings,
            provider_mode="tiktok_shop",
            total_products=len(listings),
            total_warnings=total_warnings,
        )
