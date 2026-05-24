"""Tests for S25 — Auth + Operator Identity.

Covers:
- API key enforcement (enabled, disabled, invalid)
- Operator resolution (from registry, from header, dev fallback)
- Role-based access control (require_role factory)
- Config: api_key(), load_operators()
- Capabilities: auth_enabled / auth_mode fields
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app.auth import (
    DEV_OPERATOR,
    Operator,
    OperatorRole,
    require_api_key,
    require_operator,
    require_role,
)
from app.config import (
    API_KEY_ENV,
    OPERATORS_ENV,
    api_key,
    load_operators,
)


# ---------- Config ----------


class TestApiKeyConfig:
    def test_unset_returns_none(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV, raising=False)
        assert api_key() is None

    def test_empty_returns_none(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "  ")
        assert api_key() is None

    def test_set_returns_value(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "test-secret-key")
        assert api_key() == "test-secret-key"

    def test_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "  my-key  ")
        assert api_key() == "my-key"


class TestLoadOperators:
    def test_unset_returns_empty(self, monkeypatch):
        monkeypatch.delenv(OPERATORS_ENV, raising=False)
        assert load_operators() == {}

    def test_single_operator(self, monkeypatch):
        monkeypatch.setenv(OPERATORS_ENV, "admin@test.de:owner:Admin")
        ops = load_operators()
        assert "admin@test.de" in ops
        assert ops["admin@test.de"].role == OperatorRole.OWNER
        assert ops["admin@test.de"].display_name == "Admin"

    def test_multiple_operators(self, monkeypatch):
        monkeypatch.setenv(
            OPERATORS_ENV,
            "a@test.de:owner:A,b@test.de:operator:B,c@test.de:viewer:C",
        )
        ops = load_operators()
        assert len(ops) == 3
        assert ops["a@test.de"].role == OperatorRole.OWNER
        assert ops["b@test.de"].role == OperatorRole.OPERATOR
        assert ops["c@test.de"].role == OperatorRole.VIEWER

    def test_unknown_role_defaults_to_viewer(self, monkeypatch):
        monkeypatch.setenv(OPERATORS_ENV, "x@test.de:superadmin:X")
        ops = load_operators()
        assert ops["x@test.de"].role == OperatorRole.VIEWER

    def test_no_name_field(self, monkeypatch):
        monkeypatch.setenv(OPERATORS_ENV, "y@test.de:operator")
        ops = load_operators()
        assert ops["y@test.de"].display_name is None

    def test_invalid_entry_skipped(self, monkeypatch):
        monkeypatch.setenv(OPERATORS_ENV, "nocolon,valid@test.de:owner:V")
        ops = load_operators()
        assert len(ops) == 1
        assert "valid@test.de" in ops


# ---------- require_api_key ----------


class TestRequireApiKey:
    def test_no_key_configured_passes(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV, raising=False)
        # Should not raise
        asyncio.run(require_api_key(request=None, authorization=None))

    def test_key_configured_no_header_rejects(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_api_key(request=None, authorization=None))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "authorization_required"

    def test_key_configured_wrong_format_rejects(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_api_key(request=None, authorization="Basic xxx"))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "bearer_token_required"

    def test_key_configured_wrong_value_rejects(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_api_key(request=None, authorization="Bearer wrong"))
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "invalid_api_key"

    def test_key_configured_correct_value_passes(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        asyncio.run(require_api_key(request=None, authorization="Bearer secret"))


# ---------- require_operator ----------


class TestRequireOperator:
    def test_no_key_returns_dev_operator(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV, raising=False)
        op = asyncio.run(require_operator(_api_key=None))
        assert op == DEV_OPERATOR

    def test_key_set_no_operator_header_rejects(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_operator(_api_key=None, x_operator_id=None))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "operator_identity_required"

    def test_key_set_registered_operator_resolved(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        monkeypatch.setenv(OPERATORS_ENV, "admin@sk.de:owner:Admin")
        op = asyncio.run(require_operator(_api_key=None, x_operator_id="admin@sk.de"))
        assert op.operator_id == "admin@sk.de"
        assert op.role == OperatorRole.OWNER
        assert op.display_name == "Admin"

    def test_key_set_unknown_operator_gets_viewer(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        monkeypatch.delenv(OPERATORS_ENV, raising=False)
        op = asyncio.run(require_operator(_api_key=None, x_operator_id="unknown@sk.de"))
        assert op.operator_id == "unknown@sk.de"
        assert op.role == OperatorRole.VIEWER

    def test_key_set_unknown_operator_with_role_header(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "secret")
        monkeypatch.delenv(OPERATORS_ENV, raising=False)
        op = asyncio.run(
            require_operator(
                _api_key=None,
                x_operator_id="someone@sk.de",
                x_operator_role="operator",
            )
        )
        assert op.role == OperatorRole.OPERATOR


# ---------- require_role ----------


class TestRequireRole:
    def test_allowed_role_passes(self):
        check = require_role(OperatorRole.OWNER, OperatorRole.OPERATOR)
        owner = Operator(operator_id="test", role=OperatorRole.OWNER)
        result = asyncio.run(check(operator=owner))
        assert result == owner

    def test_disallowed_role_rejects(self):
        check = require_role(OperatorRole.OWNER)
        viewer = Operator(operator_id="test", role=OperatorRole.VIEWER)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(check(operator=viewer))
        assert exc_info.value.status_code == 403
        assert "viewer" in exc_info.value.detail


# ---------- Capabilities ----------


class TestAuthCapabilities:
    def test_auth_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV, raising=False)
        from app import main as inference_main

        caps = asyncio.run(inference_main.capabilities())
        assert caps.auth_enabled is False
        assert caps.auth_mode == "open"

    def test_auth_enabled_when_key_set(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV, "test-key")
        from app import main as inference_main

        caps = asyncio.run(inference_main.capabilities())
        assert caps.auth_enabled is True
        assert caps.auth_mode == "api_key"
