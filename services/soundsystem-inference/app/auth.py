"""Operator authentication and authorization for the inference service.

Three-layer auth model:

1. **API Key** — shared secret between the Next.js proxy and this service.
   Set via `SOUNDSYSTEM_API_KEY`. When set, every request must carry
   `Authorization: Bearer <key>`. When unset (local dev), auth is disabled
   and all requests get a default dev operator.

2. **Operator Identity** — the proxy sets `X-Operator-Id` after verifying
   the browser-side Basic Auth. The inference service trusts this header
   because the API key proves the request came from the proxy.

3. **Operator Role** — resolved from the operator registry. Roles control
   what actions are allowed.

Hard rules:
- No silent degradation. If API key is set but missing/wrong, reject.
- Read routes (GET) do not require auth — the admin gate on the proxy
  already protects browser access.
- Mutating routes (POST) require a resolved operator.
- Tests use `app.dependency_overrides` to inject a test operator.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import api_key as get_api_key, load_operators


class OperatorRole(StrEnum):
    OWNER = "owner"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Operator(BaseModel):
    """Resolved operator identity for the current request."""

    operator_id: str = Field(max_length=200)
    role: OperatorRole = OperatorRole.OPERATOR
    display_name: str | None = None


# ---------- Default dev operator ----------

DEV_OPERATOR = Operator(
    operator_id="dev@localhost",
    role=OperatorRole.OWNER,
    display_name="Local Dev",
)


# ---------- Dependencies ----------


async def require_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Validate the API key if one is configured.

    When SOUNDSYSTEM_API_KEY is unset (local dev), this is a no-op.
    When set, the request must carry `Authorization: Bearer <key>`.
    """
    expected = get_api_key()
    if expected is None:
        # No API key configured — local dev mode, skip auth.
        return

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="authorization_required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="bearer_token_required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:].strip()
    if token != expected:
        raise HTTPException(
            status_code=403,
            detail="invalid_api_key",
        )


async def require_operator(
    _api_key: Annotated[None, Depends(require_api_key)],
    x_operator_id: Annotated[str | None, Header()] = None,
    x_operator_role: Annotated[str | None, Header()] = None,
) -> Operator:
    """Resolve the operator for a mutating request.

    If SOUNDSYSTEM_API_KEY is not set (local dev), returns DEV_OPERATOR.
    If set, requires X-Operator-Id header (injected by proxy).
    """
    expected_key = get_api_key()
    if expected_key is None:
        # Local dev — return dev operator.
        return DEV_OPERATOR

    if not x_operator_id:
        raise HTTPException(
            status_code=401,
            detail="operator_identity_required",
        )

    # Look up operator in registry
    operators = load_operators()
    registered = operators.get(x_operator_id)

    if registered:
        return registered

    # If operator has a role header from the proxy, trust it
    if x_operator_role:
        try:
            role = OperatorRole(x_operator_role.lower())
        except ValueError:
            role = OperatorRole.VIEWER
    else:
        role = OperatorRole.VIEWER

    return Operator(
        operator_id=x_operator_id,
        role=role,
    )


def require_role(*allowed: OperatorRole):
    """Factory for role-checking dependencies.

    Usage:
        @app.post("/v1/releases/{id}/ready")
        async def mark_ready(
            operator: Annotated[Operator, Depends(require_role(OperatorRole.OWNER, OperatorRole.OPERATOR))],
        ): ...
    """

    async def _check(
        operator: Annotated[Operator, Depends(require_operator)],
    ) -> Operator:
        if operator.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"role_{operator.role}_not_permitted",
            )
        return operator

    return _check
