"""Commerce Sync Dashboard read-model — S64.

Pure aggregation over the existing Shopify draft + Printful sync
repositories per merch capsule. Operators see a single surface that
shows draft state per provider, last-known sync IDs, and provider-mode
badges.

Hard rules:
- No provider calls in this module — read-model only.
- No mutations of any kind.
- No tokens, no auth-bearing URLs, no Shopify admin URLs (the operator
  opens the Shopify admin manually via the IDs surfaced here).
- Deterministic status aggregation: identical inputs produce identical
  outputs every time.

The mutator entry point lives in ``main.py`` as the ``sync-both`` route,
which calls the existing operator-triggered Shopify and Printful sync
boundaries sequentially. This module's :func:`combine_sync_results`
helper assembles the post-action result envelope from those raw exports.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import (
    CommerceCapsuleSyncResult,
    CommerceCapsuleSyncState,
    CommerceSyncProvider,
    CommerceSyncProviderState,
    CommerceSyncStatus,
    CommerceSyncSummary,
    MerchCapsule,
    PrintfulProductSync,
    PrintfulSyncExport,
    PrintfulSyncStatus,
    ShopifyDraftExport,
    ShopifyDraftStatus,
    ShopifyProductDraft,
)


# ---------- Per-provider state ----------


def _shopify_provider_id(draft: ShopifyProductDraft) -> str | None:
    payload = draft.provider_payload or {}
    if not isinstance(payload, dict):
        return None
    raw = payload.get("shopify_product_id") or payload.get("shopify_handle")
    if raw is None:
        return None
    return str(raw)


def _printful_provider_id(sync: PrintfulProductSync) -> str | None:
    payload = sync.provider_payload or {}
    if not isinstance(payload, dict):
        return None
    raw = payload.get("printful_sync_product_id") or payload.get("printful_external_id")
    if raw is None:
        return None
    return str(raw)


def _aggregate_status(
    *,
    item_count: int,
    synced_live: int,
    synced_mock: int,
    blocked: int,
    failed: int,
) -> CommerceSyncStatus:
    """Decide the per-provider status. Pure function.

    Order matters:
    - If we have NO items at all: NOT_SYNCED.
    - If anything FAILED: FAILED (most severe).
    - If everything BLOCKED: BLOCKED.
    - If everything LIVE: SYNCED_LIVE.
    - If everything MOCK: SYNCED_MOCK.
    - If we have any LIVE + any MOCK + nothing-not-synced: PARTIAL.
    - If some items are not synced at all: PARTIAL.
    """
    if item_count == 0:
        return CommerceSyncStatus.NOT_SYNCED
    if failed > 0:
        return CommerceSyncStatus.FAILED
    if blocked == item_count:
        return CommerceSyncStatus.BLOCKED
    accounted = synced_live + synced_mock + blocked
    if accounted < item_count:
        # Some items have no record at all.
        if synced_live + synced_mock == 0:
            return CommerceSyncStatus.NOT_SYNCED
        return CommerceSyncStatus.PARTIAL
    if synced_live == item_count:
        return CommerceSyncStatus.SYNCED_LIVE
    if synced_mock == item_count:
        return CommerceSyncStatus.SYNCED_MOCK
    return CommerceSyncStatus.PARTIAL


def build_shopify_provider_state(
    *,
    capsule: MerchCapsule,
    drafts: list[ShopifyProductDraft],
    provider_mode: str,
) -> CommerceSyncProviderState:
    item_count = len(capsule.products)

    synced_live = 0
    synced_mock = 0
    blocked = 0
    failed = 0
    provider_ids: list[str] = []
    warnings: list[str] = []
    last_synced_at: datetime | None = None

    # Aggregate by the latest draft per product (drafts may have been re-built).
    latest_by_product: dict[str, ShopifyProductDraft] = {}
    for d in drafts:
        key = str(d.product_id)
        prev = latest_by_product.get(key)
        if prev is None or d.updated_at > prev.updated_at:
            latest_by_product[key] = d

    for d in latest_by_product.values():
        if d.status == ShopifyDraftStatus.DRAFT:
            synced_live += 1
        elif d.status == ShopifyDraftStatus.EXPORTED_MOCK:
            synced_mock += 1
        elif d.status == ShopifyDraftStatus.BLOCKED:
            blocked += 1
        elif d.status == ShopifyDraftStatus.FAILED:
            failed += 1
        pid = _shopify_provider_id(d)
        if pid:
            provider_ids.append(pid)
        for w in d.warnings:
            if w not in warnings:
                warnings.append(w)
        if last_synced_at is None or d.updated_at > last_synced_at:
            last_synced_at = d.updated_at

    status = _aggregate_status(
        item_count=item_count,
        synced_live=synced_live,
        synced_mock=synced_mock,
        blocked=blocked,
        failed=failed,
    )

    return CommerceSyncProviderState(
        provider=CommerceSyncProvider.SHOPIFY,
        status=status,
        provider_mode=provider_mode,
        item_count=item_count,
        synced_item_count=synced_live + synced_mock,
        blocked_item_count=blocked,
        failed_item_count=failed,
        provider_ids=provider_ids,
        warnings=warnings,
        last_synced_at=last_synced_at,
    )


def build_printful_provider_state(
    *,
    capsule: MerchCapsule,
    syncs: list[PrintfulProductSync],
    provider_mode: str,
) -> CommerceSyncProviderState:
    item_count = len(capsule.products)

    synced_live = 0
    synced_mock = 0
    blocked = 0
    failed = 0
    provider_ids: list[str] = []
    warnings: list[str] = []
    last_synced_at: datetime | None = None

    latest_by_product: dict[str, PrintfulProductSync] = {}
    for s in syncs:
        key = str(s.product_id)
        prev = latest_by_product.get(key)
        if prev is None or s.updated_at > prev.updated_at:
            latest_by_product[key] = s

    for s in latest_by_product.values():
        if s.status == PrintfulSyncStatus.DRAFT:
            synced_live += 1
        elif s.status == PrintfulSyncStatus.EXPORTED_MOCK:
            synced_mock += 1
        elif s.status == PrintfulSyncStatus.BLOCKED:
            blocked += 1
        elif s.status == PrintfulSyncStatus.FAILED:
            failed += 1
        pid = _printful_provider_id(s)
        if pid:
            provider_ids.append(pid)
        for w in s.warnings:
            if w not in warnings:
                warnings.append(w)
        if last_synced_at is None or s.updated_at > last_synced_at:
            last_synced_at = s.updated_at

    status = _aggregate_status(
        item_count=item_count,
        synced_live=synced_live,
        synced_mock=synced_mock,
        blocked=blocked,
        failed=failed,
    )

    return CommerceSyncProviderState(
        provider=CommerceSyncProvider.PRINTFUL,
        status=status,
        provider_mode=provider_mode,
        item_count=item_count,
        synced_item_count=synced_live + synced_mock,
        blocked_item_count=blocked,
        failed_item_count=failed,
        provider_ids=provider_ids,
        warnings=warnings,
        last_synced_at=last_synced_at,
    )


# ---------- Capsule state ----------


def _combine_overall_status(
    shopify: CommerceSyncStatus, printful: CommerceSyncStatus
) -> CommerceSyncStatus:
    """Aggregate the two provider statuses into a single capsule status.

    Order from most-severe to least:
      FAILED > PARTIAL > BLOCKED > SYNCED_LIVE = SYNCED_MOCK > NOT_SYNCED

    LIVE+MOCK across providers is PARTIAL because the capsule isn't
    consistently live yet.
    """
    pair = {shopify, printful}
    if CommerceSyncStatus.FAILED in pair:
        return CommerceSyncStatus.FAILED
    if pair == {CommerceSyncStatus.NOT_SYNCED}:
        return CommerceSyncStatus.NOT_SYNCED
    if CommerceSyncStatus.NOT_SYNCED in pair and pair - {CommerceSyncStatus.NOT_SYNCED} != set():
        # one provider has done something, the other hasn't
        return CommerceSyncStatus.PARTIAL
    if CommerceSyncStatus.PARTIAL in pair:
        return CommerceSyncStatus.PARTIAL
    if pair == {CommerceSyncStatus.BLOCKED}:
        return CommerceSyncStatus.BLOCKED
    if pair == {CommerceSyncStatus.SYNCED_LIVE}:
        return CommerceSyncStatus.SYNCED_LIVE
    if pair == {CommerceSyncStatus.SYNCED_MOCK}:
        return CommerceSyncStatus.SYNCED_MOCK
    # Mixed LIVE / MOCK / BLOCKED — treat as PARTIAL.
    return CommerceSyncStatus.PARTIAL


def build_commerce_capsule_sync_state(
    *,
    capsule: MerchCapsule,
    shopify_drafts: list[ShopifyProductDraft],
    printful_syncs: list[PrintfulProductSync],
    shopify_provider_mode: str,
    printful_provider_mode: str,
) -> CommerceCapsuleSyncState:
    shopify_state = build_shopify_provider_state(
        capsule=capsule, drafts=shopify_drafts, provider_mode=shopify_provider_mode
    )
    printful_state = build_printful_provider_state(
        capsule=capsule, syncs=printful_syncs, provider_mode=printful_provider_mode
    )
    overall = _combine_overall_status(shopify_state.status, printful_state.status)

    warnings: list[str] = []
    if shopify_state.status == CommerceSyncStatus.NOT_SYNCED:
        warnings.append("Shopify: capsule has not been synced yet.")
    if printful_state.status == CommerceSyncStatus.NOT_SYNCED:
        warnings.append("Printful: capsule has not been synced yet.")
    if shopify_state.status == CommerceSyncStatus.FAILED:
        warnings.append("Shopify: most recent sync had failures.")
    if printful_state.status == CommerceSyncStatus.FAILED:
        warnings.append("Printful: most recent sync had failures.")

    return CommerceCapsuleSyncState(
        capsule_id=capsule.capsule_id,
        release_id=capsule.release_id,
        title=capsule.title,
        product_count=len(capsule.products),
        shopify=shopify_state,
        printful=printful_state,
        overall_status=overall,
        warnings=warnings,
    )


# ---------- Summary ----------


def build_commerce_sync_summary(
    states: list[CommerceCapsuleSyncState],
    *,
    shopify_provider_mode: str,
    printful_provider_mode: str,
) -> CommerceSyncSummary:
    counts: dict[CommerceSyncStatus, int] = {s: 0 for s in CommerceSyncStatus}
    for s in states:
        counts[s.overall_status] = counts.get(s.overall_status, 0) + 1

    return CommerceSyncSummary(
        total_capsules=len(states),
        not_synced=counts[CommerceSyncStatus.NOT_SYNCED],
        synced_mock=counts[CommerceSyncStatus.SYNCED_MOCK],
        synced_live=counts[CommerceSyncStatus.SYNCED_LIVE],
        partial=counts[CommerceSyncStatus.PARTIAL],
        blocked=counts[CommerceSyncStatus.BLOCKED],
        failed=counts[CommerceSyncStatus.FAILED],
        shopify_provider_mode=_safe_mode(shopify_provider_mode, ("mock", "shopify")),
        printful_provider_mode=_safe_mode(printful_provider_mode, ("mock", "printful")),
    )


def _safe_mode(value: str, allowed: tuple[str, ...]) -> str:
    return value if value in allowed else allowed[0]


# ---------- Combine sync-both result ----------


def combine_sync_results(
    *,
    capsule: MerchCapsule,
    shopify_export: ShopifyDraftExport | None,
    printful_export: PrintfulSyncExport | None,
    shopify_drafts: list[ShopifyProductDraft],
    printful_syncs: list[PrintfulProductSync],
    shopify_provider_mode: str,
    printful_provider_mode: str,
) -> CommerceCapsuleSyncResult:
    """Build the operator-facing result envelope from sequential provider runs.

    Pure function. The provider calls themselves happen in ``main.py`` —
    this only assembles the result + post-action read-model.
    """
    state = build_commerce_capsule_sync_state(
        capsule=capsule,
        shopify_drafts=shopify_drafts,
        printful_syncs=printful_syncs,
        shopify_provider_mode=shopify_provider_mode,
        printful_provider_mode=printful_provider_mode,
    )

    warnings: list[str] = []
    now = datetime.now(timezone.utc)
    _ = now  # kept for symmetry with other modules — no time-side-effects here
    if shopify_export is None:
        warnings.append("Shopify sync was not invoked for this capsule.")
    if printful_export is None:
        warnings.append("Printful sync was not invoked for this capsule.")

    return CommerceCapsuleSyncResult(
        capsule_id=capsule.capsule_id,
        shopify_result=shopify_export,
        printful_result=printful_export,
        overall_status=state.overall_status,
        state=state,
        warnings=warnings,
    )


__all__ = [
    "build_shopify_provider_state",
    "build_printful_provider_state",
    "build_commerce_capsule_sync_state",
    "build_commerce_sync_summary",
    "combine_sync_results",
]
