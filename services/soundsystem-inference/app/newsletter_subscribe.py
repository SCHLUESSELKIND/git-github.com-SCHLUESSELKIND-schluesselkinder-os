"""Public newsletter subscribe — S66.

Minimal, privacy-respecting public subscribe endpoint that forwards to a
self-hosted Listmonk instance when configured. Designed for the SNUFFRAGGA
artist page newsletter form.

Hard rules
----------
- The raw email address is never echoed in API responses. We return a
  SHA-256 hash so the client can reconcile state without server-side
  cookies.
- No tracking. No IP capture. No referrer. No cookies.
- No marketing automation. We hand the email to Listmonk and stop.
- No email sending from this module. Listmonk owns delivery and double
  opt-in if the list requires it.
- Listmonk calls go through an injectable transport so CI never makes
  real network calls.
- If Listmonk is not configured: we accept the request, hash the email,
  and return ``status=OFFLINE``. We do NOT fake success.
- Listmonk credentials are never logged, never returned, never serialized
  into error messages. The transport's `Authorization` header is scrubbed
  from any raw exception text before it leaves this module.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from app.config import (
    listmonk_base_url,
    listmonk_is_configured,
    listmonk_list_id,
    listmonk_password,
    listmonk_username,
)
from app.schemas import (
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    NewsletterSubscribeStatus,
)


# ---------- Allowlists ----------


ALLOWED_SOURCES: frozenset[str] = frozenset(
    {
        "snuffragga_artist_page",
        "schluesselkinder_home",
        "shopify_storefront",
        "manual",
    }
)


ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        "snuffragga",
        "signal",
        "gruenlichtbezirk",
        "vinyl",
        "manual",
    }
)


# ---------- Email validation + hashing ----------

# Conservative RFC-5322-ish check. We do not need full RFC compliance —
# Listmonk does its own validation. We just want to reject obviously
# malformed input before paying for an upstream round-trip.
_EMAIL_RE = re.compile(
    r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",
    re.IGNORECASE,
)


def normalize_email(raw: str) -> str:
    """Trim + lowercase. No other transformation."""
    return raw.strip().lower()


def email_is_valid(value: str) -> bool:
    if not value:
        return False
    return bool(_EMAIL_RE.fullmatch(value))


def email_hash(email: str) -> str:
    """SHA-256 hex digest of the normalized email."""
    normalized = normalize_email(email).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def validate_tags(tags: list[str]) -> list[str]:
    """Filter tags through the server-side allowlist. Returns deduped list."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in tags:
        if not isinstance(raw, str):
            continue
        lowered = raw.strip().lower()
        if lowered in ALLOWED_TAGS and lowered not in seen:
            seen.add(lowered)
            out.append(lowered)
    return out


def validate_source(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    return lowered if lowered in ALLOWED_SOURCES else None


# ---------- Token / header redaction ----------


def _redact(text: str, secrets: tuple[str, ...]) -> str:
    """Strip any secret value or Authorization-Basic header from text."""
    out = text
    for s in secrets:
        if s:
            out = out.replace(s, "***REDACTED***")
    out = re.sub(r"(?i)(Authorization\s*:\s*Basic\s+)\S+", r"\1***REDACTED***", out)
    return out


# ---------- Transport ----------

TransportResponse = dict[str, Any]
Transport = Callable[[str, dict[str, str], dict[str, Any]], TransportResponse]


def _stdlib_transport(
    url: str, headers: dict[str, str], payload: dict[str, Any]
) -> TransportResponse:
    """Default HTTP transport using stdlib urllib. No third-party HTTP dep."""
    import urllib.error
    import urllib.request

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return {"status_code": resp.status, "body": json.loads(text)}
            except json.JSONDecodeError:
                return {"status_code": resp.status, "body": {"raw": text}}
    except urllib.error.HTTPError as e:
        try:
            err_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_text = ""
        return {"status_code": e.code, "body": {"raw": err_text}}
    except urllib.error.URLError as e:
        raise RuntimeError(f"listmonk_network_error: {type(e).__name__}") from None


# ---------- Listmonk client ----------


@dataclass(repr=False)
class ListmonkNewsletterClient:
    """Production-safe Listmonk Subscriber API boundary.

    Calls POST ``/api/subscribers`` with Basic Auth. Never calls any
    other Listmonk endpoint. Never sends emails directly — Listmonk owns
    delivery and double opt-in.
    """

    _base_url: str
    _username: str
    _password: str
    _list_id: int
    _transport: Transport

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        list_id: int,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._list_id = list_id
        self._transport = transport or _stdlib_transport

    # Redacted __repr__ — credentials never leak.
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            "ListmonkNewsletterClient("
            f"base_url={self._base_url!r}, list_id={self._list_id}, "
            "credentials=***REDACTED***)"
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.__repr__()

    def _auth_header(self) -> str:
        raw = f"{self._username}:{self._password}".encode("utf-8")
        return f"Basic {base64.b64encode(raw).decode('ascii')}"

    def _endpoint(self) -> str:
        return f"{self._base_url}/api/subscribers"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self._auth_header(),
        }

    def _payload(self, email: str, tags: list[str]) -> dict[str, Any]:
        # ``status: "enabled"`` lets Listmonk decide whether double opt-in
        # is required (configured on the list itself, not here).
        return {
            "email": email,
            "name": "",
            "status": "enabled",
            "lists": [self._list_id],
            "attribs": {
                "source": "schluesselkinder",
                "tags": tags,
            },
        }

    def subscribe(self, email: str, tags: list[str]) -> NewsletterSubscribeStatus:
        """POST the subscriber to Listmonk. Returns the resulting status."""
        secrets = (self._password,)
        try:
            response = self._transport(
                self._endpoint(), self._headers(), self._payload(email, tags)
            )
        except Exception as exc:  # noqa: BLE001 - transport boundary
            scrubbed = _redact(str(exc), secrets)
            # Surface FAILED, never bubble raw secrets.
            del scrubbed  # we never expose the message to the caller
            return NewsletterSubscribeStatus.FAILED

        status_code = response.get("status_code")
        body = response.get("body") or {}

        # Listmonk returns 200 on create + on "already exists with this email".
        if isinstance(status_code, int) and 200 <= status_code < 300:
            # Double opt-in detection: Listmonk returns a `data.subscriber`
            # with status="enabled" (subscribed) or "unconfirmed" (pending).
            data = body.get("data") if isinstance(body, dict) else None
            subscriber = data.get("subscriber") if isinstance(data, dict) else None
            sub_status = subscriber.get("status") if isinstance(subscriber, dict) else None
            if sub_status == "unconfirmed":
                return NewsletterSubscribeStatus.PENDING
            return NewsletterSubscribeStatus.SUBSCRIBED

        # 409 conflict = already-subscribed. Treat as success.
        if status_code == 409:
            return NewsletterSubscribeStatus.SUBSCRIBED

        return NewsletterSubscribeStatus.FAILED


# ---------- Public entrypoint ----------


def subscribe_to_newsletter(
    request: NewsletterSubscribeRequest,
    *,
    client: ListmonkNewsletterClient | None = None,
) -> NewsletterSubscribeResponse:
    """Public subscribe handler. Pure orchestration; no side effects beyond
    the optional Listmonk POST.

    If ``client`` is None we read env via :func:`_build_client_or_offline`.
    Tests inject a client with a mocked transport so no real network IO
    happens.
    """
    normalized = normalize_email(request.email)
    if not email_is_valid(normalized):
        # Schema-level shape passed but the regex didn't — invalid email.
        # We still hash the normalized value so the client can reconcile.
        return NewsletterSubscribeResponse(
            ok=False,
            status=NewsletterSubscribeStatus.FAILED,
            message="invalid_email",
            email_hash=email_hash(normalized),
        )

    tags = validate_tags(request.tags)
    source = validate_source(request.source)
    if source:
        # Encode source as a tag for the operator's downstream filtering.
        source_tag = f"source:{source}"
        if source_tag not in tags:
            tags.append(source_tag)

    # If Listmonk is not configured we accept the request honestly and
    # return OFFLINE. We do NOT pretend we subscribed.
    if client is None:
        client = _build_client_or_offline()
    if client is None:
        return NewsletterSubscribeResponse(
            ok=False,
            status=NewsletterSubscribeStatus.OFFLINE,
            message="newsletter_endpoint_unconfigured",
            email_hash=email_hash(normalized),
        )

    status = client.subscribe(normalized, tags)

    if status == NewsletterSubscribeStatus.SUBSCRIBED:
        return NewsletterSubscribeResponse(
            ok=True,
            status=status,
            message="subscribed",
            email_hash=email_hash(normalized),
        )
    if status == NewsletterSubscribeStatus.PENDING:
        return NewsletterSubscribeResponse(
            ok=True,
            status=status,
            message="pending_double_optin",
            email_hash=email_hash(normalized),
        )
    return NewsletterSubscribeResponse(
        ok=False,
        status=NewsletterSubscribeStatus.FAILED,
        message="upstream_failed",
        email_hash=email_hash(normalized),
    )


def _build_client_or_offline() -> ListmonkNewsletterClient | None:
    """Construct a real Listmonk client iff every env var is set."""
    if not listmonk_is_configured():
        return None
    return ListmonkNewsletterClient(
        base_url=listmonk_base_url() or "",
        username=listmonk_username() or "",
        password=listmonk_password() or "",
        list_id=listmonk_list_id() or 0,
    )


__all__ = [
    "ALLOWED_SOURCES",
    "ALLOWED_TAGS",
    "ListmonkNewsletterClient",
    "_build_client_or_offline",
    "_redact",
    "email_hash",
    "email_is_valid",
    "normalize_email",
    "subscribe_to_newsletter",
    "validate_source",
    "validate_tags",
]
