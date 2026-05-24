"""Tests for S66 — Public Newsletter Subscribe.

Covers:
- Email normalization (trim + lowercase)
- Email validation (regex)
- Hash determinism: same email → same hash
- Hash is sha256 hex (64 chars)
- Raw email never appears in any API response
- Tag allowlist filters unknown tags
- Source allowlist filters unknown source
- Source becomes `source:<value>` tag when present
- Offline behaviour when Listmonk env not configured
- Listmonk 200 → SUBSCRIBED
- Listmonk 200 with subscriber.status="unconfirmed" → PENDING (double opt-in)
- Listmonk 409 conflict (already subscribed) → SUBSCRIBED
- Listmonk 4xx/5xx → FAILED
- Listmonk network failure → FAILED + no token leak
- Transport receives correct payload shape (no extra fields)
- Authorization header is Basic (we don't verify the bytes — tests just
  assert the header exists and is not the raw password)
- Token / password redacted in __repr__ / __str__
- Capabilities expose `newsletter_subscribe_available` + `newsletter_listmonk_configured`
- Route honors Pydantic validation (extra fields rejected)
- No cookies, no IP, no referrer, no user-agent captured
- No external API call in any test
- No `requests` / `httpx` / `aiohttp` import in module
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

from app.newsletter_subscribe import (
    ALLOWED_SOURCES,
    ALLOWED_TAGS,
    ListmonkNewsletterClient,
    _redact,
    email_hash,
    email_is_valid,
    normalize_email,
    subscribe_to_newsletter,
    validate_source,
    validate_tags,
)
from app.schemas import (
    NewsletterSubscribeRequest,
    NewsletterSubscribeStatus,
)


# ---------- Constants ----------

SECRET_PASSWORD = "listmonk_super_secret_token_xyz_abc"


# ---------- Helpers ----------


def _client(transport=None) -> ListmonkNewsletterClient:
    return ListmonkNewsletterClient(
        base_url="https://listmonk.example.local",
        username="api_user",
        password=SECRET_PASSWORD,
        list_id=42,
        transport=transport,
    )


def _ok_response(unconfirmed: bool = False) -> dict:
    return {
        "status_code": 200,
        "body": {
            "data": {
                "subscriber": {
                    "id": 999,
                    "email": "x@x.local",
                    "status": "unconfirmed" if unconfirmed else "enabled",
                }
            }
        },
    }


# ---------- Normalization + validation ----------


class TestEmailHelpers:
    def test_normalize_email_trims_and_lowercases(self) -> None:
        assert normalize_email("  Test@Example.com  ") == "test@example.com"

    def test_email_is_valid_accepts_well_formed(self) -> None:
        assert email_is_valid("alice@example.com") is True
        assert email_is_valid("alice.bob+tag@sub.example.co.uk") is True

    def test_email_is_valid_rejects_malformed(self) -> None:
        assert email_is_valid("") is False
        assert email_is_valid("no-at") is False
        assert email_is_valid("a@b") is False
        assert email_is_valid("a@b.") is False
        assert email_is_valid("@example.com") is False

    def test_hash_deterministic(self) -> None:
        a = email_hash("Alice@Example.COM")
        b = email_hash("alice@example.com")
        assert a == b
        assert len(a) == 64

    def test_hash_is_lowercase_hex(self) -> None:
        h = email_hash("alice@example.com")
        assert all(c in "0123456789abcdef" for c in h)


# ---------- Tag + source allowlists ----------


class TestAllowlists:
    def test_validate_tags_filters_unknown(self) -> None:
        result = validate_tags(["snuffragga", "evil", "signal", "snuffragga"])
        # unknown rejected; duplicates deduped
        assert "snuffragga" in result
        assert "signal" in result
        assert "evil" not in result
        # no duplicates
        assert result.count("snuffragga") == 1

    def test_validate_tags_lowercases(self) -> None:
        result = validate_tags(["SNUFFRAGGA"])
        assert result == ["snuffragga"]

    def test_validate_tags_rejects_non_string(self) -> None:
        # Lists with non-string members are silently filtered.
        result = validate_tags([123, None, "signal"])  # type: ignore[list-item]
        assert result == ["signal"]

    def test_validate_source_accepts_allowed(self) -> None:
        assert validate_source("snuffragga_artist_page") == "snuffragga_artist_page"

    def test_validate_source_rejects_unknown(self) -> None:
        assert validate_source("evil_source") is None
        assert validate_source("") is None
        assert validate_source(None) is None


# ---------- Subscribe (offline) ----------


class TestSubscribeOffline:
    def test_offline_when_no_client_and_env_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Ensure env is clean.
        for k in (
            "SOUNDSYSTEM_LISTMONK_BASE_URL",
            "SOUNDSYSTEM_LISTMONK_USERNAME",
            "SOUNDSYSTEM_LISTMONK_PASSWORD",
            "SOUNDSYSTEM_LISTMONK_LIST_ID",
        ):
            monkeypatch.delenv(k, raising=False)

        req = NewsletterSubscribeRequest(email="alice@example.com")
        res = subscribe_to_newsletter(req)
        assert res.ok is False
        assert res.status == NewsletterSubscribeStatus.OFFLINE
        assert res.message == "newsletter_endpoint_unconfigured"
        assert len(res.email_hash) == 64

    def test_offline_response_does_not_echo_email(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for k in (
            "SOUNDSYSTEM_LISTMONK_BASE_URL",
            "SOUNDSYSTEM_LISTMONK_USERNAME",
            "SOUNDSYSTEM_LISTMONK_PASSWORD",
            "SOUNDSYSTEM_LISTMONK_LIST_ID",
        ):
            monkeypatch.delenv(k, raising=False)
        req = NewsletterSubscribeRequest(email="alice@example.com")
        res = subscribe_to_newsletter(req)
        blob = res.model_dump_json()
        assert "alice@example.com" not in blob
        assert "alice" not in blob


# ---------- Subscribe (invalid email) ----------


class TestSubscribeInvalidEmail:
    def test_invalid_email_returns_failed(self) -> None:
        # Email passes the Pydantic shape (≥ 3 chars) but the regex rejects it.
        req = NewsletterSubscribeRequest(email="bad email")
        # Provide a client that, if called, would fail the test.
        called = {"n": 0}

        def boom(*_a, **_k):
            called["n"] += 1
            raise AssertionError("transport must not be called for invalid email")

        client = _client(transport=boom)
        res = subscribe_to_newsletter(req, client=client)
        assert res.ok is False
        assert res.status == NewsletterSubscribeStatus.FAILED
        assert res.message == "invalid_email"
        assert called["n"] == 0


# ---------- Subscribe (configured) ----------


class TestSubscribeConfigured:
    def test_200_enabled_yields_subscribed(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = payload
            return _ok_response()

        client = _client(transport=t)
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(
                email="alice@example.com",
                source="snuffragga_artist_page",
                tags=["snuffragga", "signal"],
            ),
            client=client,
        )
        assert res.ok is True
        assert res.status == NewsletterSubscribeStatus.SUBSCRIBED
        assert res.message == "subscribed"

        # Endpoint shape
        assert captured["url"].endswith("/api/subscribers")
        # Auth header present, password not exposed in headers dump
        auth = captured["headers"]["Authorization"]
        assert auth.startswith("Basic ")
        assert SECRET_PASSWORD not in auth  # base64-encoded, not raw
        # Payload shape
        p = captured["payload"]
        assert p["email"] == "alice@example.com"
        assert p["lists"] == [42]
        assert p["status"] == "enabled"
        assert "tags" in p["attribs"]
        # Source becomes a tag and is allowlisted
        assert "source:snuffragga_artist_page" in p["attribs"]["tags"]

    def test_200_unconfirmed_yields_pending(self) -> None:
        client = _client(transport=lambda *a, **k: _ok_response(unconfirmed=True))
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(email="bob@example.com"),
            client=client,
        )
        assert res.ok is True
        assert res.status == NewsletterSubscribeStatus.PENDING

    def test_409_conflict_yields_subscribed(self) -> None:
        client = _client(
            transport=lambda *a, **k: {"status_code": 409, "body": {"message": "exists"}}
        )
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(email="bob@example.com"),
            client=client,
        )
        assert res.ok is True
        assert res.status == NewsletterSubscribeStatus.SUBSCRIBED

    def test_4xx_yields_failed(self) -> None:
        client = _client(transport=lambda *a, **k: {"status_code": 400, "body": {"message": "bad"}})
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(email="bob@example.com"),
            client=client,
        )
        assert res.ok is False
        assert res.status == NewsletterSubscribeStatus.FAILED

    def test_5xx_yields_failed(self) -> None:
        client = _client(transport=lambda *a, **k: {"status_code": 500, "body": {}})
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(email="bob@example.com"),
            client=client,
        )
        assert res.ok is False
        assert res.status == NewsletterSubscribeStatus.FAILED

    def test_network_failure_yields_failed_without_token_leak(self) -> None:
        def boom(*_a, **_k):
            raise RuntimeError(f"upstream burned with secret {SECRET_PASSWORD}")

        client = _client(transport=boom)
        res = subscribe_to_newsletter(
            NewsletterSubscribeRequest(email="bob@example.com"),
            client=client,
        )
        assert res.status == NewsletterSubscribeStatus.FAILED
        # Response never carries the password.
        assert SECRET_PASSWORD not in res.model_dump_json()
        assert SECRET_PASSWORD not in res.message

    def test_unknown_tags_filtered_out_in_payload(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _ok_response()

        client = _client(transport=t)
        subscribe_to_newsletter(
            NewsletterSubscribeRequest(
                email="alice@example.com",
                tags=["snuffragga", "evil_tag", "signal"],
            ),
            client=client,
        )
        tags = captured["payload"]["attribs"]["tags"]
        assert "snuffragga" in tags
        assert "signal" in tags
        assert "evil_tag" not in tags

    def test_unknown_source_does_not_create_source_tag(self) -> None:
        captured: dict = {}

        def t(url, headers, payload):
            captured["payload"] = payload
            return _ok_response()

        client = _client(transport=t)
        subscribe_to_newsletter(
            NewsletterSubscribeRequest(
                email="alice@example.com",
                source="evil_source",
            ),
            client=client,
        )
        tags = captured["payload"]["attribs"]["tags"]
        for tag in tags:
            assert not tag.startswith("source:")


# ---------- Token safety ----------


class TestTokenSafety:
    def test_repr_does_not_contain_password(self) -> None:
        c = _client()
        rendered = repr(c)
        assert SECRET_PASSWORD not in rendered
        assert "REDACTED" in rendered

    def test_str_does_not_contain_password(self) -> None:
        c = _client()
        assert SECRET_PASSWORD not in str(c)

    def test_no_public_password_attribute(self) -> None:
        c = _client()
        assert not hasattr(c, "password")
        assert not hasattr(c, "api_token")

    def test_redact_helper_scrubs_secret(self) -> None:
        msg = f"oh no: Authorization: Basic {SECRET_PASSWORD}"
        scrubbed = _redact(msg, (SECRET_PASSWORD,))
        assert SECRET_PASSWORD not in scrubbed
        assert "***REDACTED***" in scrubbed


# ---------- Allowlists exported for operator transparency ----------


class TestAllowlistExports:
    def test_sources_include_expected(self) -> None:
        assert "snuffragga_artist_page" in ALLOWED_SOURCES

    def test_tags_include_expected(self) -> None:
        assert "snuffragga" in ALLOWED_TAGS
        assert "signal" in ALLOWED_TAGS


# ---------- Route E2E ----------


class TestPublicRoute:
    def test_route_returns_offline_when_unconfigured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for k in (
            "SOUNDSYSTEM_LISTMONK_BASE_URL",
            "SOUNDSYSTEM_LISTMONK_USERNAME",
            "SOUNDSYSTEM_LISTMONK_PASSWORD",
            "SOUNDSYSTEM_LISTMONK_LIST_ID",
        ):
            monkeypatch.delenv(k, raising=False)
        from app.main import public_newsletter_subscribe

        res = asyncio.run(
            public_newsletter_subscribe(
                NewsletterSubscribeRequest(
                    email="alice@example.com",
                    source="snuffragga_artist_page",
                    tags=["snuffragga", "signal"],
                )
            )
        )
        assert res.status == NewsletterSubscribeStatus.OFFLINE
        assert res.ok is False

    def test_route_rejects_extra_fields_via_pydantic(self) -> None:
        # extra="forbid" — Pydantic raises on unknown keys.
        with pytest.raises(Exception):
            NewsletterSubscribeRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "tracking_id": "evil-cookie-id",
                }
            )


# ---------- Capabilities ----------


class TestCapabilities:
    def test_capabilities_expose_subscribe_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for k in (
            "SOUNDSYSTEM_LISTMONK_BASE_URL",
            "SOUNDSYSTEM_LISTMONK_USERNAME",
            "SOUNDSYSTEM_LISTMONK_PASSWORD",
            "SOUNDSYSTEM_LISTMONK_LIST_ID",
        ):
            monkeypatch.delenv(k, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.newsletter_subscribe_available is True
        assert caps.newsletter_listmonk_configured is False

    def test_capabilities_reflect_configured_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LISTMONK_BASE_URL", "https://listmonk.local")
        monkeypatch.setenv("SOUNDSYSTEM_LISTMONK_USERNAME", "api_user")
        monkeypatch.setenv("SOUNDSYSTEM_LISTMONK_PASSWORD", "secret")
        monkeypatch.setenv("SOUNDSYSTEM_LISTMONK_LIST_ID", "42")
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.newsletter_listmonk_configured is True


# ---------- No forbidden imports ----------


class TestNoForbiddenImports:
    def test_no_third_party_http_imports(self) -> None:
        from app import newsletter_subscribe

        source = inspect.getsource(newsletter_subscribe)
        # stdlib urllib is fine — that's what we use.
        assert "urllib.request" in source
        for forbidden in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "from requests",
            "from httpx",
            "from aiohttp",
        ):
            assert forbidden not in source

    def test_no_scheduler_or_background_imports(self) -> None:
        from app import newsletter_subscribe

        source = inspect.getsource(newsletter_subscribe)
        for forbidden in (
            "threading.Thread",
            "multiprocessing",
            "BackgroundTasks",
            "subprocess",
            "asyncio.create_task",
            "apscheduler",
            "celery",
            "import schedule",
            "crontab",
        ):
            assert forbidden not in source

    def test_no_tracking_imports(self) -> None:
        """No cookie / IP / referrer / user-agent API surface in module code.

        We scan import statements + non-comment lines, not docstrings —
        the module docstring legitimately *negatively* names some of these
        terms (e.g. "no cookies"), and that's the desired guarantee, not
        a violation.
        """
        from app import newsletter_subscribe

        source = inspect.getsource(newsletter_subscribe)
        # Scan import lines + assignment / call sites only.
        suspicious_lines = []
        in_docstring = False
        for line in source.splitlines():
            stripped = line.strip()
            # crude tri-quote scanner — toggles in/out of docstrings
            tri = stripped.count('"""')
            if tri == 1:
                in_docstring = not in_docstring
                continue
            if in_docstring or stripped.startswith("#"):
                continue
            suspicious_lines.append(line)
        scan_blob = "\n".join(suspicious_lines)

        for forbidden in (
            "set_cookie",
            "X-Forwarded-For",
            "request.cookies",
            "response.set_cookie",
            "request.client.host",
            "user_agent_string",
            "track_event",
        ):
            assert forbidden not in scan_blob
