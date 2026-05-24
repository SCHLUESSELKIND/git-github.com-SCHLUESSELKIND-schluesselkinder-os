"""TikTok Shop Listing Provider Isolation Layer (S42).

Protocol + factory. Every TikTok Shop listing provider must satisfy
`TikTokShopProviderProtocol`. The factory function
`build_tiktok_shop_provider()` reads `SOUNDSYSTEM_TIKTOK_SHOP_PROVIDER`
and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic listing payloads, no TikTok Shop API call.
- "tiktok_shop" — real TikTok Shop API boundary. Requires app key + secret.
  Real listing creation is NOT implemented — always returns BLOCKED status.

Hard rules:
1. Mock remains default — tests never hit TikTok Shop.
2. No silent fallback — if "tiktok_shop" selected without config, fail loudly.
3. No real TikTok Shop API calls in this slice.
4. No product creation. No publishing. No inventory mutation.
5. Credentials never exposed in logs, errors, or API responses.
6. TikTok Shop is top-of-funnel. Vinyl routes elsewhere.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    MerchCapsule,
    TikTokShopListing,
    TikTokShopListingExport,
)


class TikTokShopProviderProtocol(Protocol):
    """Shared interface for all TikTok Shop listing providers.

    Route handlers never see TikTok Shop SDK types — only this Protocol.
    """

    name: str

    def build_listings(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[TikTokShopListing]:
        """Convert capsule products into TikTok Shop listing drafts."""
        ...

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> TikTokShopListingExport:
        """Build a complete listing export payload for the capsule."""
        ...


def build_tiktok_shop_provider() -> TikTokShopProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - TIKTOK_SHOP: requires app key + app secret. Listings return BLOCKED.
    """
    from app.config import (
        TikTokShopProviderConfigError,
        TikTokShopProviderMode,
        tiktok_shop_app_key,
        tiktok_shop_app_secret,
        tiktok_shop_provider_mode,
    )

    mode = tiktok_shop_provider_mode()

    if mode == TikTokShopProviderMode.TIKTOK_SHOP:
        key = tiktok_shop_app_key()
        secret = tiktok_shop_app_secret()
        missing = []
        if not key:
            missing.append("TIKTOK_SHOP_APP_KEY")
        if not secret:
            missing.append("TIKTOK_SHOP_APP_SECRET")
        if missing:
            raise TikTokShopProviderConfigError(
                f"SOUNDSYSTEM_TIKTOK_SHOP_PROVIDER=tiktok_shop requires "
                f"{', '.join(missing)} to be set."
            )
        from app.providers.tiktok_shop.real import RealTikTokShopProvider

        return RealTikTokShopProvider()  # type: ignore[return-value]

    # Default: mock
    from app.providers.tiktok_shop.mock import MockTikTokShopProvider

    return MockTikTokShopProvider()  # type: ignore[return-value]
