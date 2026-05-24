"""Printful Sync Provider Isolation Layer (S41).

Protocol + factory. Every Printful sync provider must satisfy
`PrintfulSyncProviderProtocol`. The factory function
`build_printful_sync_provider()` reads `SOUNDSYSTEM_PRINTFUL_PROVIDER`
and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic sync payloads, no Printful API call.
- "printful" — real Printful API boundary. Requires API token.
  Real sync is NOT implemented — always returns BLOCKED status.

Hard rules:
1. Mock remains default — tests never hit Printful.
2. No silent fallback — if "printful" selected without config, fail loudly.
3. No real Printful API calls in this slice.
4. No product creation. No fulfillment. No inventory sync.
5. Credentials never exposed in logs, errors, or API responses.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    MerchCapsule,
    PrintfulProductSync,
    PrintfulSyncExport,
)


class PrintfulSyncProviderProtocol(Protocol):
    """Shared interface for all Printful sync providers.

    Route handlers never see Printful SDK types — only this Protocol.
    """

    name: str

    def build_product_syncs(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[PrintfulProductSync]:
        """Convert capsule products into Printful sync payloads."""
        ...

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> PrintfulSyncExport:
        """Build a complete sync export payload for the capsule."""
        ...


def build_printful_sync_provider() -> PrintfulSyncProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - PRINTFUL: requires PRINTFUL_API_TOKEN + PRINTFUL_STORE_ID.
      Exposes ``sync_products()`` for live sync product creation.
    """
    from app.config import (
        PrintfulProviderConfigError,
        PrintfulProviderMode,
        printful_api_token,
        printful_provider_mode,
        printful_store_id,
    )

    mode = printful_provider_mode()

    if mode == PrintfulProviderMode.PRINTFUL:
        token = printful_api_token()
        store_id = printful_store_id()
        missing: list[str] = []
        if not token:
            missing.append("PRINTFUL_API_TOKEN")
        if not store_id:
            missing.append("PRINTFUL_STORE_ID")
        if missing:
            raise PrintfulProviderConfigError(
                f"SOUNDSYSTEM_PRINTFUL_PROVIDER=printful requires {', '.join(missing)} to be set."
            )
        from app.providers.printful.real import RealPrintfulSyncProvider

        return RealPrintfulSyncProvider()  # type: ignore[return-value]

    # Default: mock
    from app.providers.printful.mock import MockPrintfulSyncProvider

    return MockPrintfulSyncProvider()  # type: ignore[return-value]


def supports_live_sync(provider: PrintfulSyncProviderProtocol) -> bool:
    """Return True iff the provider implements ``sync_products`` (live mode)."""
    return callable(getattr(provider, "sync_products", None))
