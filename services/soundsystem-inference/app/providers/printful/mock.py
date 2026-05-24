"""Mock Printful Sync Provider (S41).

Default provider — no external dependencies, deterministic results.
No real Printful API calls. No product creation. No fulfillment.
Safe for tests and local development.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.printful_sync_builder import build_all_syncs
from app.schemas import (
    MerchCapsule,
    PrintfulProductSync,
    PrintfulSyncExport,
    PrintfulSyncStatus,
)


class MockPrintfulSyncProvider:
    """Mock implementation — builds sync payloads without Printful API calls.

    Supported products get status=exported_mock.
    Unsupported products (vinyl) keep status=blocked.
    No product creation. No fulfillment.
    """

    name: str = "mock"

    def build_product_syncs(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[PrintfulProductSync]:
        """Convert capsule products into Printful sync payloads."""
        syncs = build_all_syncs(capsule, operator_id=operator_id)
        # Mark supported products as exported_mock; blocked stays blocked
        return [
            s.model_copy(
                update={
                    "status": PrintfulSyncStatus.EXPORTED_MOCK
                    if s.status != PrintfulSyncStatus.BLOCKED
                    else PrintfulSyncStatus.BLOCKED,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            for s in syncs
        ]

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> PrintfulSyncExport:
        """Build a complete sync export payload for the capsule."""
        syncs = self.build_product_syncs(capsule, operator_id=operator_id)
        total_warnings = sum(len(s.warnings) for s in syncs)
        return PrintfulSyncExport(
            capsule_id=capsule.capsule_id,
            syncs=syncs,
            provider_mode="mock",
            total_products=len(syncs),
            total_warnings=total_warnings,
        )
