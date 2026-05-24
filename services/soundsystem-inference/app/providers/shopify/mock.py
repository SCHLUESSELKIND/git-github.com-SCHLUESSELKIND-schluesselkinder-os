"""Mock Shopify Draft Provider (S40).

Default provider — no external dependencies, deterministic results.
No real Shopify API calls. No publishing. No inventory mutation.
Safe for tests and local development.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import (
    MerchCapsule,
    ShopifyDraftExport,
    ShopifyDraftStatus,
    ShopifyProductDraft,
)
from app.shopify_draft_builder import build_all_drafts


class MockShopifyDraftProvider:
    """Mock implementation — builds draft payloads without Shopify API calls.

    All drafts get status=exported_mock. No product creation. No publishing.
    """

    name: str = "mock"

    def build_product_drafts(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[ShopifyProductDraft]:
        """Convert capsule products into Shopify product drafts."""
        drafts = build_all_drafts(capsule, operator_id=operator_id)
        # Mark as exported_mock in mock mode
        return [
            d.model_copy(
                update={
                    "status": ShopifyDraftStatus.EXPORTED_MOCK,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            for d in drafts
        ]

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> ShopifyDraftExport:
        """Build a complete draft export payload for the capsule."""
        drafts = self.build_product_drafts(capsule, operator_id=operator_id)
        total_warnings = sum(len(d.warnings) for d in drafts)
        return ShopifyDraftExport(
            capsule_id=capsule.capsule_id,
            drafts=drafts,
            provider_mode="mock",
            total_products=len(drafts),
            total_warnings=total_warnings,
        )
