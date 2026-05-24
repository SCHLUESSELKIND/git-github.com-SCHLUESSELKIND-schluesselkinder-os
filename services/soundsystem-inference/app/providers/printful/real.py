"""Real Printful Sync Provider (S63 hardening).

Hardened, operator-triggered Printful Catalog/Store API boundary that
creates Printful sync products only. Never publishes the Shopify
storefront. Never sets inventory quantities. Never touches orders,
customers, or webhooks. Never starts background workers.

Activation
----------
Selected when ``SOUNDSYSTEM_PRINTFUL_PROVIDER=printful``. Requires
``PRINTFUL_API_TOKEN`` and ``PRINTFUL_STORE_ID``. Fails loudly at
factory construction time without both.

Security
--------
- The API token is never logged, never included in ``__repr__`` /
  ``__str__``, never returned in any response, never serialized into
  errors.
- Network errors are surfaced as a single short string. The token is
  scrubbed from any raw exception text before it leaves this module.
- The provider holds the token as a private tuple attribute; the only
  public attribute is the human-readable ``name``.

Mutation surface
----------------
This provider performs exactly one type of mutation per product:
  - POST ``/store/products`` (Printful API v1) creating a sync product
    with variants. Sync products only — these stay as drafts inside
    Printful until the operator pushes them through Printful's own UI
    or runs a separate publish step.

It does NOT call:
  - Any orders endpoint (``/orders``).
  - Any inventory endpoint (``/sync/products/{id}/variants/stock`` and
    related).
  - Any webhook endpoint.
  - Any customer endpoint.
  - Any Shopify endpoint at all — Shopify mirroring is handled by
    Printful itself, on Printful's side, with the operator's existing
    Shopify integration.

It does NOT register webhooks, listen for webhooks, schedule background
work, or run any cron-style task.

Vinyl products
--------------
Vinyl-provider-group merch products are NOT POD items. The real
provider blocks any vinyl row with status=BLOCKED and a clear warning,
even when the rest of the capsule syncs successfully.

HTTP
----
Uses stdlib ``urllib.request``. No new pinned dependency. In tests the
network layer is monkeypatched via the ``_transport`` hook — no real
HTTP calls happen in CI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from app.config import (
    printful_api_token,
    printful_store_id,
)
from app.printful_sync_builder import build_all_syncs
from app.schemas import (
    MerchCapsule,
    MerchProviderGroup,
    PrintfulProductSync,
    PrintfulSyncExport,
    PrintfulSyncStatus,
)


# ---------- Constants ----------

PRINTFUL_API_BASE = "https://api.printful.com"
STORE_PRODUCTS_PATH = "/store/products"

# Field name allowlist that may appear in our outgoing JSON payload. Any
# attempt to slip a forbidden field through is caught by tests.
ALLOWED_PAYLOAD_KEYS = frozenset(
    {
        "sync_product",
        "sync_variants",
        "external_id",
        "name",
        "thumbnail",
        "variant_id",
        "retail_price",
        "files",
        "options",
        "url",
        "type",
        "title",
    }
)

# Field names that must never appear anywhere in the outgoing payload.
FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        # Inventory
        "stock",
        "quantity",
        "inventory",
        "inventory_item_id",
        "inventory_quantity",
        "inventory_management",
        # Orders / fulfillment
        "order",
        "orders",
        "shipments",
        "shipment",
        "recipient",
        "items",
        "shipping_service",
        # Customers
        "customer",
        "customer_id",
        # Webhooks
        "webhook",
        "webhook_url",
        "callback_url",
        # Shopify storefront publishing
        "publish",
        "publish_to_shopify",
        "shopify_publish",
        "shopify_status",
        "publishable",
    }
)


# ---------- Transport ----------

TransportResponse = dict[str, Any]
Transport = Callable[[str, dict[str, str], dict[str, Any]], TransportResponse]


def _redact(text: str, token: str | None) -> str:
    """Scrub a token (and obvious bearer headers) from any text."""
    if not text:
        return text
    out = text
    if token:
        out = out.replace(token, "***REDACTED***")
    out = re.sub(r"(?i)(Authorization\s*:\s*Bearer\s+)\S+", r"\1***REDACTED***", out)
    out = re.sub(r"(?i)(X-PF-Store-Id\s*:\s*)\S+", r"\1***REDACTED***", out)
    return out


def _stdlib_transport(
    url: str, headers: dict[str, str], payload: dict[str, Any]
) -> TransportResponse:
    """Default HTTP transport using stdlib urllib. Token never appears in errors."""
    import urllib.error
    import urllib.request

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        token = _extract_bearer(headers)
        scrubbed = _redact(err_body, token)
        raise RuntimeError(f"printful_http_error: status={e.code} body={scrubbed[:500]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"printful_network_error: {type(e).__name__}") from None


def _extract_bearer(headers: dict[str, str]) -> str | None:
    auth = headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[len("Bearer ") :]
    return None


# ---------- Provider ----------


@dataclass(repr=False)
class RealPrintfulSyncProvider:
    """Production-safe Printful Catalog/Store API boundary.

    Only POSTs ``/store/products`` (sync product create). Never publishes
    storefront. Never touches inventory/orders/customers/webhooks. Token
    is held privately and redacted everywhere.
    """

    name: str = "printful"
    _transport: Transport | None = None
    _api_base: str = PRINTFUL_API_BASE
    _store_id: str | None = None
    # Token stored in a tuple so it never appears as a named attribute.
    _token_holder: tuple[str, ...] = ()

    def __init__(
        self,
        *,
        api_token: str | None = None,
        store_id: str | None = None,
        api_base: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.name = "printful"
        token = api_token if api_token is not None else printful_api_token()
        store = store_id if store_id is not None else printful_store_id()
        if not token or not store:
            from app.config import PrintfulProviderConfigError

            raise PrintfulProviderConfigError(
                "RealPrintfulSyncProvider requires PRINTFUL_API_TOKEN and PRINTFUL_STORE_ID."
            )
        self._store_id = store
        self._api_base = api_base or PRINTFUL_API_BASE
        self._token_holder = (token,)
        self._transport = transport or _stdlib_transport

    # --- Redacted __repr__ — never expose token ---

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            "RealPrintfulSyncProvider("
            f"api_base={self._api_base!r}, store_id={self._store_id!r}, "
            "token=***REDACTED***)"
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.__repr__()

    # --- Internal token accessor ---

    def _token(self) -> str:
        if not self._token_holder:
            raise RuntimeError("printful_token_missing")
        return self._token_holder[0]

    # --- Provider protocol surface ---

    def build_product_syncs(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[PrintfulProductSync]:
        """Build local sync payloads. Does NOT call Printful yet."""
        return build_all_syncs(capsule, operator_id=operator_id)

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> PrintfulSyncExport:
        """Read-only export. Does NOT call Printful; matches mock provider shape.

        Use ``sync_products()`` for live sync product creation.
        """
        syncs = self.build_product_syncs(capsule, operator_id=operator_id)
        marked = [
            s.model_copy(
                update={
                    "status": PrintfulSyncStatus.BLOCKED,
                    "warnings": s.warnings
                    + [
                        "export_mock() is read-only when PRINTFUL mode is selected. "
                        "Call sync_products() to create Printful sync products."
                    ],
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            for s in syncs
        ]
        total_warnings = sum(len(s.warnings) for s in marked)
        return PrintfulSyncExport(
            capsule_id=capsule.capsule_id,
            syncs=marked,
            provider_mode="printful",
            total_products=len(marked),
            total_warnings=total_warnings,
        )

    # --- Live sync (S63) ---

    def sync_products(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> PrintfulSyncExport:
        """Create Printful sync products via the Store API.

        Vinyl-provider-group products are blocked at this boundary; they
        are not POD items. Every other product becomes a single POST
        ``/store/products`` call. Failures on one product never abort
        the rest. Token never appears in any warning text.
        """
        syncs = self.build_product_syncs(capsule, operator_id=operator_id)
        capsule_product_lookup = {p.product_id: p for p in capsule.products}

        token = self._token()
        out: list[PrintfulProductSync] = []
        for s in syncs:
            product = capsule_product_lookup.get(s.product_id)
            if product is not None and product.provider_group == MerchProviderGroup.VINYL_PROVIDER:
                out.append(
                    s.model_copy(
                        update={
                            "status": PrintfulSyncStatus.BLOCKED,
                            "warnings": s.warnings
                            + ["vinyl_blocked: vinyl is not a Printful POD item."],
                            "updated_at": datetime.now(timezone.utc),
                        }
                    )
                )
                continue
            out.append(self._create_one_sync_product(s, token=token))

        total_warnings = sum(len(s.warnings) for s in out)
        return PrintfulSyncExport(
            capsule_id=capsule.capsule_id,
            syncs=out,
            provider_mode="printful",
            total_products=len(out),
            total_warnings=total_warnings,
        )

    # --- Internals ---

    def _endpoint(self) -> str:
        return f"{self._api_base}{STORE_PRODUCTS_PATH}"

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "X-PF-Store-Id": self._store_id or "",
        }

    def _payload(self, sync: PrintfulProductSync) -> dict[str, Any]:
        """Build the Printful ``/store/products`` payload.

        Pinned shape — every key is in ALLOWED_PAYLOAD_KEYS. Inventory,
        orders, customers, and storefront publishing fields are
        deliberately absent.
        """
        sync_product: dict[str, Any] = {
            # External id ties this sync product back to our internal product_id.
            "external_id": str(sync.product_id),
            "name": sync.title,
        }

        sync_variants: list[dict[str, Any]] = []
        for v in sync.variants:
            variant_payload: dict[str, Any] = {
                "external_id": f"{sync.product_id}:{v.variant_id}",
                "retail_price": "0.00",
            }
            # Catalog variant_id resolution belongs to the operator on
            # Printful's side. We surface only what we have without
            # guessing IDs.
            if v.sku_suffix:
                variant_payload["external_id"] = f"{sync.product_id}:{v.sku_suffix or v.variant_id}"
            sync_variants.append(variant_payload)

        return {
            "sync_product": sync_product,
            "sync_variants": sync_variants,
        }

    def _create_one_sync_product(
        self, sync: PrintfulProductSync, *, token: str
    ) -> PrintfulProductSync:
        if self._transport is None:
            return sync.model_copy(
                update={
                    "status": PrintfulSyncStatus.FAILED,
                    "warnings": sync.warnings + ["printful_transport_not_configured"],
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        payload = self._payload(sync)

        # Belt-and-braces: enforce the field allowlist before sending.
        violations = _payload_violates_safety(payload)
        if violations:
            return sync.model_copy(
                update={
                    "status": PrintfulSyncStatus.FAILED,
                    "warnings": sync.warnings
                    + [f"printful_payload_safety_violation: {', '.join(sorted(violations))}"],
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        headers = self._headers(token)
        try:
            response = self._transport(self._endpoint(), headers, payload)
        except Exception as exc:
            scrubbed = _redact(str(exc), token)
            return sync.model_copy(
                update={
                    "status": PrintfulSyncStatus.FAILED,
                    "warnings": sync.warnings + [f"printful_transport_error: {scrubbed[:300]}"],
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        return _interpret_response(sync, response, token=token)


def _payload_violates_safety(payload: dict[str, Any]) -> set[str]:
    """Walk the payload and report any forbidden keys / unexpected top-level keys."""
    violations: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                lk = k.lower()
                if lk in FORBIDDEN_PAYLOAD_KEYS:
                    violations.add(k)
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    # Top-level keys must be a subset of the allowlist.
    for k in payload.keys():
        if k not in ALLOWED_PAYLOAD_KEYS:
            violations.add(k)
    walk(payload)
    return violations


def _interpret_response(
    sync: PrintfulProductSync,
    response: dict[str, Any],
    *,
    token: str,
) -> PrintfulProductSync:
    """Map a Printful response to an updated PrintfulProductSync."""
    now = datetime.now(timezone.utc)

    # Printful classic API shape: {"code": 200, "result": {...}} on success,
    # {"code": 4xx, "result": "...", "error": {...}} on failure.
    code = response.get("code")
    if isinstance(code, int) and code >= 400:
        err = response.get("error") or {}
        message = err.get("message") if isinstance(err, dict) else None
        if not message:
            message = response.get("result") if isinstance(response.get("result"), str) else None
        if not message:
            message = "unknown_error"
        return sync.model_copy(
            update={
                "status": PrintfulSyncStatus.FAILED,
                "warnings": sync.warnings
                + [f"printful_api_error: {_redact(str(message), token)[:400]}"],
                "updated_at": now,
            }
        )

    result = response.get("result") or {}
    if not isinstance(result, dict):
        return sync.model_copy(
            update={
                "status": PrintfulSyncStatus.FAILED,
                "warnings": sync.warnings + ["printful_unexpected_response"],
                "updated_at": now,
            }
        )

    sync_product_obj = result.get("sync_product") or result
    pf_id = sync_product_obj.get("id")
    pf_external_id = sync_product_obj.get("external_id")

    if not pf_id:
        return sync.model_copy(
            update={
                "status": PrintfulSyncStatus.FAILED,
                "warnings": sync.warnings + ["printful_missing_sync_product_id"],
                "updated_at": now,
            }
        )

    provider_payload: dict[str, Any] = {
        "printful_sync_product_id": pf_id,
    }
    if pf_external_id:
        provider_payload["printful_external_id"] = pf_external_id
    sync_variants = result.get("sync_variants")
    if isinstance(sync_variants, list):
        provider_payload["printful_sync_variant_count"] = len(sync_variants)

    return sync.model_copy(
        update={
            "status": PrintfulSyncStatus.DRAFT,
            "provider_payload": provider_payload,
            "updated_at": now,
        }
    )


__all__ = [
    "RealPrintfulSyncProvider",
    "PRINTFUL_API_BASE",
    "STORE_PRODUCTS_PATH",
    "ALLOWED_PAYLOAD_KEYS",
    "FORBIDDEN_PAYLOAD_KEYS",
    "_interpret_response",
    "_payload_violates_safety",
    "_redact",
]
