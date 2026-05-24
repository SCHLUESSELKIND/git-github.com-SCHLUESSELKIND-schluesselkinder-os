"""Merch Capsule Builder Logic (S37).

Converts a ReleasePack into merch capsule planning objects.
No real commerce API calls. No Printful, TikTok Shop, or Shopify calls.

Core product philosophy:
- 70% unavailable / 20% limited / 10% always available
- Max 5 active products per capsule
- No POD spam
- No fake scarcity
- Release-linked artifacts only

Functions:
- build_merch_capsule_from_release: scaffold a capsule from a ReleasePack
- suggest_products_for_release: default product suggestions
- enforce_merch_capsule_rules: validate and warn
- build_mock_provider_export: produce mock export payload
"""

from __future__ import annotations

from uuid import UUID, uuid4

from datetime import datetime, timezone

from app.schemas import (
    MerchAvailability,
    MerchCapsule,
    MerchCapsuleStatus,
    MerchCapsuleWarning,
    MerchExportPayload,
    MerchProduct,
    MerchProductType,
    MerchProductUpdateRequest,
    MerchProductUpdateResult,
    MerchProviderExportNotes,
    MerchProviderGroup,
    ReleasePack,
)


# ---------- Provider routing ----------

_PRODUCT_PROVIDER_MAP: dict[MerchProductType, MerchProviderGroup] = {
    MerchProductType.HEAVYWEIGHT_TEE: MerchProviderGroup.APPAREL_PROVIDER,
    MerchProductType.OVERSIZED_HOODIE: MerchProviderGroup.APPAREL_PROVIDER,
    MerchProductType.LONGSLEEVE: MerchProviderGroup.APPAREL_PROVIDER,
    MerchProductType.BEANIE: MerchProviderGroup.APPAREL_PROVIDER,
    MerchProductType.TOTE: MerchProviderGroup.APPAREL_PROVIDER,
    MerchProductType.POSTER: MerchProviderGroup.PREMIUM_DROP_PROVIDER,
    MerchProductType.STICKER_PACK: MerchProviderGroup.PREMIUM_DROP_PROVIDER,
    MerchProductType.VINYL_OBJECT: MerchProviderGroup.VINYL_PROVIDER,
}


def _provider_for(product_type: MerchProductType) -> MerchProviderGroup:
    return _PRODUCT_PROVIDER_MAP.get(product_type, MerchProviderGroup.APPAREL_PROVIDER)


# ---------- Product suggestions ----------


def suggest_products_for_release(release: ReleasePack) -> list[MerchProduct]:
    """Suggest default products based on release metadata.

    Default set:
    - heavyweight tee (limited)
    - oversized hoodie (limited)
    - sticker pack (always_on — the one always-on item)
    - poster (limited)
    - vinyl object if genre/metadata suggests vinyl relevance

    Returns at most 5 products. No more than 1 always_on.
    """
    products: list[MerchProduct] = []

    # Cover artifact for artwork linking
    cover_artifact_id: UUID | None = None
    for asset in release.assets:
        if asset.asset_type == "cover_art" and asset.ready and asset.artifact_id:
            cover_artifact_id = asset.artifact_id
            break

    # 1. Heavyweight Tee — limited
    products.append(
        MerchProduct(
            product_id=uuid4(),
            title=f"{release.title} — Heavyweight Tee",
            product_type=MerchProductType.HEAVYWEIGHT_TEE,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.APPAREL_PROVIDER,
            price_positioning="mid",
            artwork_artifact_id=cover_artifact_id,
            active=True,
        )
    )

    # 2. Oversized Hoodie — limited
    products.append(
        MerchProduct(
            product_id=uuid4(),
            title=f"{release.title} — Oversized Hoodie",
            product_type=MerchProductType.OVERSIZED_HOODIE,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.APPAREL_PROVIDER,
            price_positioning="premium",
            artwork_artifact_id=cover_artifact_id,
            active=True,
        )
    )

    # 3. Sticker Pack — always_on (the single always-on item)
    products.append(
        MerchProduct(
            product_id=uuid4(),
            title=f"{release.title} — Sticker Pack",
            product_type=MerchProductType.STICKER_PACK,
            availability=MerchAvailability.ALWAYS_ON,
            provider_group=MerchProviderGroup.PREMIUM_DROP_PROVIDER,
            price_positioning="entry",
            artwork_artifact_id=cover_artifact_id,
            active=True,
        )
    )

    # 4. Poster — limited
    products.append(
        MerchProduct(
            product_id=uuid4(),
            title=f"{release.title} — Poster",
            product_type=MerchProductType.POSTER,
            availability=MerchAvailability.LIMITED,
            provider_group=MerchProviderGroup.PREMIUM_DROP_PROVIDER,
            price_positioning="mid",
            artwork_artifact_id=cover_artifact_id,
            active=True,
        )
    )

    # 5. Vinyl Object — only if genre/metadata suggests relevance
    genre_lower = (release.genre or "").lower()
    description_lower = release.description.lower()
    vinyl_keywords = {"vinyl", "techno", "house", "electronic", "dub", "analog"}
    has_vinyl_signal = any(kw in genre_lower or kw in description_lower for kw in vinyl_keywords)

    # Also check if there's a SoundCloud description mentioning vinyl
    sc_desc_lower = release.social_copy.soundcloud_description.lower()
    if not has_vinyl_signal:
        has_vinyl_signal = any(kw in sc_desc_lower for kw in vinyl_keywords)

    if has_vinyl_signal:
        products.append(
            MerchProduct(
                product_id=uuid4(),
                title=f"{release.title} — Vinyl Object",
                product_type=MerchProductType.VINYL_OBJECT,
                availability=MerchAvailability.LIMITED,
                provider_group=MerchProviderGroup.VINYL_PROVIDER,
                price_positioning="cult",
                artwork_artifact_id=cover_artifact_id,
                active=True,
            )
        )

    return products[:5]


# ---------- Rule enforcement ----------


def enforce_merch_capsule_rules(
    capsule: MerchCapsule,
) -> list[MerchCapsuleWarning]:
    """Validate capsule against merch rules and return warnings.

    Rules enforced:
    1. Max 5 active products
    2. No more than 1 always_on product by default
    3. Limited products require drop window warning if missing
    4. vinyl_object routes to vinyl_provider
    5. apparel routes to apparel_provider
    6. poster/sticker can route to premium_drop_provider
    """
    warnings: list[MerchCapsuleWarning] = []

    active_products = [p for p in capsule.products if p.active]

    # Rule 1: max active products
    if len(active_products) > capsule.max_active_products:
        warnings.append(
            MerchCapsuleWarning(
                code="too_many_active",
                message=(
                    f"Capsule has {len(active_products)} active products, "
                    f"max is {capsule.max_active_products}. "
                    "Reduce active count to maintain scarcity posture."
                ),
            )
        )

    # Rule 2: no more than 1 always_on
    always_on_count = sum(
        1 for p in active_products if p.availability == MerchAvailability.ALWAYS_ON
    )
    if always_on_count > 1:
        warnings.append(
            MerchCapsuleWarning(
                code="too_many_always_on",
                message=(
                    f"{always_on_count} always-on products found. "
                    "Limit to 1 to maintain 70/20/10 availability rule."
                ),
            )
        )

    # Rule 3: limited products need drop window
    limited_products = [p for p in active_products if p.availability == MerchAvailability.LIMITED]
    if limited_products and not capsule.drop_window_start:
        warnings.append(
            MerchCapsuleWarning(
                code="limited_no_drop_window",
                message=(
                    f"{len(limited_products)} limited product(s) but no drop "
                    "window set. Set drop_window_start/end before locking."
                ),
            )
        )

    # Rule 4-6: provider routing validation
    for product in capsule.products:
        expected_provider = _provider_for(product.product_type)
        if product.provider_group != expected_provider:
            warnings.append(
                MerchCapsuleWarning(
                    code="provider_mismatch",
                    message=(
                        f"Product '{product.title}' ({product.product_type}) "
                        f"expected provider {expected_provider}, "
                        f"got {product.provider_group}."
                    ),
                )
            )

    return warnings


# ---------- Capsule builder ----------


def build_merch_capsule_from_release(
    release: ReleasePack,
    *,
    operator_id: str | None = None,
    notes: str = "",
) -> MerchCapsule:
    """Build a merch capsule scaffold from a ReleasePack.

    Pre-populates product suggestions, enforces rules, sets warnings.
    """
    products = suggest_products_for_release(release)

    # Collect unique provider groups from products
    provider_groups = sorted({p.provider_group for p in products}, key=lambda g: g.value)

    capsule = MerchCapsule(
        capsule_id=uuid4(),
        release_id=release.release_id,
        title=f"{release.title} — Merch Capsule",
        artist=release.artist,
        products=products,
        provider_groups=provider_groups,
        notes=notes,
        created_by=operator_id,
    )

    # Enforce rules and attach warnings
    warnings = enforce_merch_capsule_rules(capsule)
    capsule = capsule.model_copy(update={"warnings": warnings})

    return capsule


# ---------- Product update ----------


def update_merch_product(
    capsule: MerchCapsule,
    product_id: UUID,
    request: MerchProductUpdateRequest,
) -> MerchProductUpdateResult:
    """Apply a partial update to a single product within a capsule.

    Rules:
    - Locked/archived capsules reject updates (caller must enforce via HTTP 409).
    - Unknown product_id returns None (caller raises 404).
    - After update, re-validates capsule rules and attaches warnings.
    - updated_at is refreshed on the capsule.

    Returns the updated capsule, the updated product, and fresh warnings.
    Does NOT auto-rebuild Shopify/Printful/TikTok payloads.
    """
    # Find the product
    product_index: int | None = None
    for idx, product in enumerate(capsule.products):
        if product.product_id == product_id:
            product_index = idx
            break

    if product_index is None:
        return None  # type: ignore[return-value]

    # Build update dict from non-None fields
    update_fields: dict = {}
    if request.title is not None:
        update_fields["title"] = request.title
    if request.active is not None:
        update_fields["active"] = request.active
    if request.availability is not None:
        update_fields["availability"] = request.availability
    if request.price_positioning is not None:
        update_fields["price_positioning"] = request.price_positioning
    if request.artwork_artifact_id is not None:
        update_fields["artwork_artifact_id"] = request.artwork_artifact_id
    if request.mockup_artifact_id is not None:
        update_fields["mockup_artifact_id"] = request.mockup_artifact_id

    # Apply update to the product
    updated_product = capsule.products[product_index].model_copy(update=update_fields)

    # Replace in products list
    updated_products = list(capsule.products)
    updated_products[product_index] = updated_product

    # Re-validate rules
    updated_capsule = capsule.model_copy(
        update={
            "products": updated_products,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    warnings = enforce_merch_capsule_rules(updated_capsule)
    updated_capsule = updated_capsule.model_copy(update={"warnings": warnings})

    return MerchProductUpdateResult(
        capsule=updated_capsule,
        product=updated_product,
        warnings=warnings,
    )


# ---------- Mock export ----------


def build_mock_provider_export(capsule: MerchCapsule) -> MerchExportPayload:
    """Build a mock export payload for future provider integration.

    No real API calls. No secrets. Provider notes describe what
    each adapter would do when connected.
    """
    # Group products by provider
    provider_product_counts: dict[MerchProviderGroup, int] = {}
    for product in capsule.products:
        if product.active:
            provider_product_counts[product.provider_group] = (
                provider_product_counts.get(product.provider_group, 0) + 1
            )

    provider_exports: list[MerchProviderExportNotes] = []

    if MerchProviderGroup.APPAREL_PROVIDER in provider_product_counts:
        provider_exports.append(
            MerchProviderExportNotes(
                provider_group=MerchProviderGroup.APPAREL_PROVIDER,
                product_count=provider_product_counts[MerchProviderGroup.APPAREL_PROVIDER],
                notes=(
                    "Printful adapter not connected. Would sync "
                    f"{provider_product_counts[MerchProviderGroup.APPAREL_PROVIDER]} "
                    "product(s) as draft catalog items. No inventory mutation."
                ),
            )
        )

    if MerchProviderGroup.PREMIUM_DROP_PROVIDER in provider_product_counts:
        provider_exports.append(
            MerchProviderExportNotes(
                provider_group=MerchProviderGroup.PREMIUM_DROP_PROVIDER,
                product_count=provider_product_counts[MerchProviderGroup.PREMIUM_DROP_PROVIDER],
                notes=(
                    "Gelato/premium adapter not connected. Would sync "
                    f"{provider_product_counts[MerchProviderGroup.PREMIUM_DROP_PROVIDER]} "
                    "product(s) for limited drop fulfillment. No inventory mutation."
                ),
            )
        )

    if MerchProviderGroup.VINYL_PROVIDER in provider_product_counts:
        provider_exports.append(
            MerchProviderExportNotes(
                provider_group=MerchProviderGroup.VINYL_PROVIDER,
                product_count=provider_product_counts[MerchProviderGroup.VINYL_PROVIDER],
                notes=(
                    "Vinyl adapter not connected. Would submit "
                    f"{provider_product_counts[MerchProviderGroup.VINYL_PROVIDER]} "
                    "vinyl object(s) to pressing service. No order placed."
                ),
            )
        )

    # Warnings
    warnings = enforce_merch_capsule_rules(capsule)

    if capsule.status != MerchCapsuleStatus.LOCKED:
        warnings.append(
            MerchCapsuleWarning(
                code="not_locked",
                message="Capsule is not locked. Lock before real provider export.",
            )
        )

    return MerchExportPayload(
        capsule_id=capsule.capsule_id,
        release_id=capsule.release_id,
        title=capsule.title,
        artist=capsule.artist,
        status=capsule.status,
        products=[p for p in capsule.products if p.active],
        provider_exports=provider_exports,
        warnings=warnings,
    )
