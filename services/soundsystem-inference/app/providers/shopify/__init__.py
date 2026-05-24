"""Shopify Draft Provider Isolation Layer (S40).

Protocol + factory. Every Shopify draft provider must satisfy
`ShopifyDraftProviderProtocol`. The factory function
`build_shopify_draft_provider()` reads `SOUNDSYSTEM_SHOPIFY_PROVIDER`
and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic draft payloads, no Shopify API call.
- "shopify" — real Shopify Admin API boundary. Requires shop domain + token.
  Real draft creation is NOT implemented — always returns BLOCKED status.

Hard rules:
1. Mock remains default — tests never hit Shopify.
2. No silent fallback — if "shopify" selected without config, fail loudly.
3. No real Shopify API calls in this slice.
4. No product publishing. No inventory mutation.
5. No checkout/payment.
6. Credentials never exposed in logs, errors, or API responses.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    MerchCapsule,
    ShopifyDraftExport,
    ShopifyProductDraft,
)


class ShopifyDraftProviderProtocol(Protocol):
    """Shared interface for all Shopify draft providers.

    Route handlers never see Shopify SDK types — only this Protocol.
    """

    name: str

    def build_product_drafts(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[ShopifyProductDraft]:
        """Convert capsule products into Shopify product drafts."""
        ...

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> ShopifyDraftExport:
        """Build a complete draft export payload for the capsule."""
        ...


def supports_live_sync(provider: ShopifyDraftProviderProtocol) -> bool:
    """Return True iff the provider implements `sync_drafts` (live Shopify mode)."""
    return callable(getattr(provider, "sync_drafts", None))


def build_shopify_draft_provider() -> ShopifyDraftProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - SHOPIFY: requires shop domain + admin access token. Drafts return BLOCKED.
    """
    from app.config import (
        ShopifyProviderConfigError,
        ShopifyProviderMode,
        shopify_admin_access_token,
        shopify_provider_mode,
        shopify_shop_domain,
    )

    mode = shopify_provider_mode()

    if mode == ShopifyProviderMode.SHOPIFY:
        domain = shopify_shop_domain()
        token = shopify_admin_access_token()
        missing = []
        if not domain:
            missing.append("SHOPIFY_SHOP_DOMAIN")
        if not token:
            missing.append("SHOPIFY_ADMIN_ACCESS_TOKEN")
        if missing:
            raise ShopifyProviderConfigError(
                f"SOUNDSYSTEM_SHOPIFY_PROVIDER=shopify requires {', '.join(missing)} to be set."
            )
        from app.providers.shopify.real import RealShopifyDraftProvider

        return RealShopifyDraftProvider()  # type: ignore[return-value]

    # Default: mock
    from app.providers.shopify.mock import MockShopifyDraftProvider

    return MockShopifyDraftProvider()  # type: ignore[return-value]
