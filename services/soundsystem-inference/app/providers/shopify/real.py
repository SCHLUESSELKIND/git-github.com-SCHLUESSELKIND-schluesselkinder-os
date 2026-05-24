"""Real Shopify Draft Provider (S62 hardening).

Hardened, operator-triggered Shopify Admin GraphQL boundary that creates
products with status=DRAFT only. Never publishes. Never mutates inventory,
orders, customers, or webhooks. Never starts background workers.

Activation
----------
Selected when SOUNDSYSTEM_SHOPIFY_PROVIDER=shopify. Requires
SHOPIFY_SHOP_DOMAIN and SHOPIFY_ADMIN_ACCESS_TOKEN. Fails loudly at factory
time without both.

Security
--------
- The admin access token is never logged, never included in __repr__,
  never returned in any response, never serialized into errors.
- Network errors are surfaced as a single short string. The token is
  scrubbed from any raw exception text before it leaves this module.
- The provider holds the token as a private attribute and exposes only a
  redacted `__repr__`.

Mutation surface
----------------
This provider performs exactly one type of mutation per draft:
  - `productCreate` GraphQL mutation with `input.status = DRAFT`.

It does NOT call:
  - publishablePublish / publishablePublishToCurrentChannel
  - productPublish (deprecated; not used either)
  - inventoryAdjustQuantity / inventorySetOnHandQuantities
  - draftOrderCreate / orderCreate / refundCreate
  - customerCreate / customerUpdate
  - webhookSubscriptionCreate / appSubscriptionCreate

It does NOT register webhooks, listen for webhooks, schedule background
work, or run any cron-style task.

HTTP
----
Uses `httpx` if already available in the runtime; otherwise falls back
to `urllib.request` from the standard library. No new pinned dependency.

In tests the network layer is monkeypatched via the `_transport` hook —
no real HTTP calls happen in CI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from app.config import (
    DEFAULT_SHOPIFY_API_VERSION,
    shopify_admin_access_token,
    shopify_api_version,
    shopify_shop_domain,
)
from app.schemas import (
    MerchCapsule,
    ShopifyDraftExport,
    ShopifyDraftStatus,
    ShopifyProductDraft,
)
from app.shopify_draft_builder import build_all_drafts


# ---------- GraphQL constants ----------

PRODUCT_CREATE_MUTATION = """
mutation snuffraga_productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product {
      id
      handle
      title
      status
      onlineStoreUrl
      vendor
      productType
      tags
    }
    userErrors {
      field
      message
    }
  }
}
""".strip()


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
    # Also strip anything that looks like a Shopify-Access-Token header value
    out = re.sub(r"(?i)(X-Shopify-Access-Token\s*:\s*)\S+", r"\1***REDACTED***", out)
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
        # Read body if any; redact before surfacing.
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        token = headers.get("X-Shopify-Access-Token")
        scrubbed = _redact(err_body, token)
        raise RuntimeError(
            f"shopify_admin_http_error: status={e.code} body={scrubbed[:500]}"
        ) from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"shopify_admin_network_error: {type(e).__name__}") from None


# ---------- Provider ----------


@dataclass(repr=False)
class RealShopifyDraftProvider:
    """Production-safe Shopify Admin GraphQL boundary.

    Only creates `productCreate` drafts. Never publishes. Never touches
    inventory/orders/customers/webhooks. Token is held privately and
    redacted everywhere.
    """

    name: str = "shopify"
    _transport: Transport | None = None
    _shop_domain: str | None = None
    _api_version: str = DEFAULT_SHOPIFY_API_VERSION
    # Token is stored under a deliberately-obscure name so it never appears
    # in tab-completion or default __repr__. We also override __repr__ below.
    _token_holder: tuple[str, ...] = ()

    def __init__(
        self,
        *,
        shop_domain: str | None = None,
        access_token: str | None = None,
        api_version: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.name = "shopify"
        domain = shop_domain if shop_domain is not None else shopify_shop_domain()
        token = access_token if access_token is not None else shopify_admin_access_token()
        if not domain or not token:
            from app.config import ShopifyProviderConfigError

            raise ShopifyProviderConfigError(
                "RealShopifyDraftProvider requires SHOPIFY_SHOP_DOMAIN and "
                "SHOPIFY_ADMIN_ACCESS_TOKEN."
            )
        self._shop_domain = domain
        self._api_version = api_version or shopify_api_version()
        # Hold the token inside a tuple so accidental repr/str doesn't show
        # it as a named attribute.
        self._token_holder = (token,)
        self._transport = transport or _stdlib_transport

    # --- Redacted __repr__ — never expose token ---

    def __repr__(self) -> str:  # pragma: no cover - trivial
        domain = self._shop_domain or "?"
        return (
            f"RealShopifyDraftProvider(shop_domain={domain!r}, "
            f"api_version={self._api_version!r}, token=***REDACTED***)"
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.__repr__()

    # --- Internal token accessor (single point of truth) ---

    def _token(self) -> str:
        if not self._token_holder:
            raise RuntimeError("shopify_admin_token_missing")
        return self._token_holder[0]

    # --- Provider protocol surface ---

    def build_product_drafts(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> list[ShopifyProductDraft]:
        """Build local draft payloads. Does NOT call Shopify yet."""
        return build_all_drafts(capsule, operator_id=operator_id)

    def export_mock(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> ShopifyDraftExport:
        """Read-only export. Does NOT call Shopify; matches mock provider shape.

        Use ``sync_drafts()`` for live draft creation.
        """
        drafts = self.build_product_drafts(capsule, operator_id=operator_id)
        marked = [
            d.model_copy(
                update={
                    "status": ShopifyDraftStatus.BLOCKED,
                    "warnings": d.warnings
                    + [
                        "export_mock() is read-only when SHOPIFY mode is selected. "
                        "Call sync_drafts() to create draft products via the Admin API."
                    ],
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            for d in drafts
        ]
        total_warnings = sum(len(d.warnings) for d in marked)
        return ShopifyDraftExport(
            capsule_id=capsule.capsule_id,
            drafts=marked,
            provider_mode="shopify",
            total_products=len(marked),
            total_warnings=total_warnings,
        )

    # --- Live draft creation (S62) ---

    def sync_drafts(
        self,
        capsule: MerchCapsule,
        *,
        operator_id: str | None = None,
    ) -> ShopifyDraftExport:
        """Create Shopify products with status=DRAFT via Admin GraphQL.

        Never publishes. Never sets inventory. Never touches orders/customers.
        Each draft is created independently; a failure on one does not abort
        the rest. Errors are recorded on the failed draft's `warnings` and
        `status=FAILED`. The token is never exposed in any warning text.
        """
        drafts = self.build_product_drafts(capsule, operator_id=operator_id)
        out: list[ShopifyProductDraft] = []
        token = self._token()
        for d in drafts:
            updated = self._create_one_draft(d, token=token)
            out.append(updated)

        total_warnings = sum(len(d.warnings) for d in out)
        return ShopifyDraftExport(
            capsule_id=capsule.capsule_id,
            drafts=out,
            provider_mode="shopify",
            total_products=len(out),
            total_warnings=total_warnings,
        )

    # --- Internals ---

    def _endpoint(self) -> str:
        return f"https://{self._shop_domain}/admin/api/{self._api_version}/graphql.json"

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Shopify-Access-Token": token,
        }

    def _payload(self, draft: ShopifyProductDraft) -> dict[str, Any]:
        """Build the GraphQL `productCreate` input. Status is DRAFT always."""
        # NOTE: We deliberately exclude:
        #   - publishedAt / publishedScope / publishToCurrentChannel
        #   - inventoryItem / inventoryQuantities
        #   - variants[].inventoryPolicy (kept default; never set to CONTINUE)
        product_input: dict[str, Any] = {
            "title": draft.title,
            "bodyHtml": draft.body_html,
            "vendor": draft.vendor,
            "productType": draft.product_type,
            "tags": list(draft.tags),
            "status": "DRAFT",
        }
        if draft.variants:
            product_input["variants"] = [
                {
                    "title": v.title,
                    "price": v.price,
                    "requiresShipping": v.requires_shipping,
                    "options": [v.option1],
                    # Inventory is deliberately not set.
                }
                for v in draft.variants
            ]
        return {
            "query": PRODUCT_CREATE_MUTATION,
            "variables": {"input": product_input},
        }

    def _create_one_draft(self, draft: ShopifyProductDraft, *, token: str) -> ShopifyProductDraft:
        if self._transport is None:
            return draft.model_copy(
                update={
                    "status": ShopifyDraftStatus.FAILED,
                    "warnings": draft.warnings + ["shopify_transport_not_configured"],
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        payload = self._payload(draft)
        headers = self._headers(token)
        try:
            response = self._transport(self._endpoint(), headers, payload)
        except Exception as exc:
            scrubbed = _redact(str(exc), token)
            return draft.model_copy(
                update={
                    "status": ShopifyDraftStatus.FAILED,
                    "warnings": draft.warnings + [f"shopify_transport_error: {scrubbed[:300]}"],
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        return _interpret_response(draft, response, token=token)


def _interpret_response(
    draft: ShopifyProductDraft,
    response: dict[str, Any],
    *,
    token: str,
) -> ShopifyProductDraft:
    """Map a Shopify GraphQL response to an updated ShopifyProductDraft."""
    now = datetime.now(timezone.utc)

    # 1. GraphQL top-level errors (auth, throttled, invalid query, etc.)
    if isinstance(response.get("errors"), list) and response["errors"]:
        msgs: list[str] = []
        for e in response["errors"]:
            msg = e.get("message") if isinstance(e, dict) else str(e)
            if msg:
                msgs.append(_redact(str(msg), token))
        return draft.model_copy(
            update={
                "status": ShopifyDraftStatus.FAILED,
                "warnings": draft.warnings + [f"shopify_graphql_error: {' · '.join(msgs)[:400]}"],
                "updated_at": now,
            }
        )

    data = response.get("data") or {}
    pc = data.get("productCreate") or {}
    user_errors = pc.get("userErrors") or []
    product = pc.get("product")

    # 2. userErrors — validation/permission/etc.
    if user_errors:
        msgs = []
        for e in user_errors:
            field = ".".join(e.get("field") or [])
            message = e.get("message") or ""
            msgs.append(f"{field}: {message}" if field else message)
        return draft.model_copy(
            update={
                "status": ShopifyDraftStatus.FAILED,
                "warnings": draft.warnings + [f"shopify_user_error: {' · '.join(msgs)[:400]}"],
                "updated_at": now,
            }
        )

    if not product:
        return draft.model_copy(
            update={
                "status": ShopifyDraftStatus.FAILED,
                "warnings": draft.warnings + ["shopify_unexpected_response"],
                "updated_at": now,
            }
        )

    # 3. Safety check: status must be DRAFT.
    status = (product.get("status") or "").upper()
    safety_warnings = list(draft.warnings)
    if status != "DRAFT":
        # Should never happen because we pin input.status to DRAFT, but if
        # Shopify ever returns something else, surface it loud and mark
        # FAILED rather than success.
        safety_warnings.append(
            f"shopify_unexpected_status: server returned {status!r}, expected DRAFT"
        )
        return draft.model_copy(
            update={
                "status": ShopifyDraftStatus.FAILED,
                "warnings": safety_warnings,
                "updated_at": now,
            }
        )

    # 4. Success — store admin identifiers in provider_payload (no token).
    payload: dict[str, Any] = {
        "shopify_product_id": product.get("id"),
        "shopify_handle": product.get("handle"),
        "shopify_status": status,
    }
    if product.get("onlineStoreUrl"):
        payload["shopify_online_store_url"] = product["onlineStoreUrl"]

    return draft.model_copy(
        update={
            "status": ShopifyDraftStatus.DRAFT,
            "provider_payload": payload,
            "warnings": safety_warnings,
            "updated_at": now,
        }
    )


# ---------- Used by tests to manufacture failure responses cleanly ----------

__all__ = [
    "RealShopifyDraftProvider",
    "PRODUCT_CREATE_MUTATION",
    "_interpret_response",
    "_redact",
    "uuid4",
]
