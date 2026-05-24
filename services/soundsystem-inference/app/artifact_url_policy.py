"""Artifact URL Policy — S29.

Generates and validates download URLs for artifacts. Supports two modes:

- direct: open access (existing S27 behavior, default for dev)
- signed: HMAC-signed token required on download URLs

The signed mode uses HMAC-SHA256 with a configurable secret and optional
expiry. If no expiry is set, tokens are valid indefinitely (useful for
internal operator tools where session lifetime is controlled elsewhere).

Rules:
- Signing secret is required in signed mode. Missing → fail loud.
- In direct mode, no token is generated or required.
- Tokens encode artifact_id + optional expires_at.
- Expired tokens are rejected with 403.
- Invalid tokens are rejected with 403.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timezone
from uuid import UUID

from app.config import (
    ArtifactAccessConfigError,
    ArtifactAccessMode,
    artifact_access_mode,
    artifact_signing_secret,
)
from app.schemas import ArtifactSignedUrl


# Default token lifetime: 1 hour (3600 seconds). 0 = no expiry.
DEFAULT_TOKEN_LIFETIME_SECONDS = 3600


def _get_signing_secret() -> str:
    """Get the signing secret, failing loudly if in signed mode without one."""
    secret = artifact_signing_secret()
    if secret is None:
        raise ArtifactAccessConfigError(
            "SOUNDSYSTEM_ARTIFACT_ACCESS_MODE=signed requires "
            "SOUNDSYSTEM_ARTIFACT_SIGNING_SECRET to be set."
        )
    return secret


def generate_token(artifact_id: UUID, *, expires_at: int | None = None) -> str:
    """Generate an HMAC token for artifact download.

    Args:
        artifact_id: The UUID of the artifact.
        expires_at: Unix timestamp when the token expires. None = no expiry.

    Returns:
        Hex-encoded HMAC-SHA256 token.
    """
    secret = _get_signing_secret()
    payload = f"{artifact_id}:{expires_at or 'none'}"
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _compute_hmac(secret: str, artifact_id: UUID, expires_at: int | None) -> str:
    """Compute HMAC for the given parameters."""
    payload = f"{artifact_id}:{expires_at or 'none'}"
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_download_url(
    artifact_id: UUID,
    *,
    lifetime_seconds: int = DEFAULT_TOKEN_LIFETIME_SECONDS,
) -> ArtifactSignedUrl:
    """Generate a download URL for an artifact based on the current access mode.

    In direct mode: returns a plain route URL with no token.
    In signed mode: returns a route URL with HMAC token and expiry.
    """
    mode = artifact_access_mode()
    base_url = f"/v1/artifacts/{artifact_id}/download"

    if mode == ArtifactAccessMode.DIRECT:
        return ArtifactSignedUrl(
            artifact_id=artifact_id,
            url=base_url,
            expires_at=None,
            access_mode="direct",
            method="GET",
        )

    # Signed mode
    secret = _get_signing_secret()
    expires_at: int | None = None
    expires_dt: datetime | None = None
    if lifetime_seconds > 0:
        expires_at = int(time.time()) + lifetime_seconds
        expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)

    token = _compute_hmac(secret, artifact_id, expires_at)
    url = f"{base_url}?token={token}&expires={expires_at or ''}"

    return ArtifactSignedUrl(
        artifact_id=artifact_id,
        url=url,
        expires_at=expires_dt,
        access_mode="signed",
        method="GET",
    )


def validate_token(
    artifact_id: UUID,
    token: str | None,
    expires: str | None,
) -> tuple[bool, str]:
    """Validate a download token.

    Returns:
        (is_valid, error_message). error_message is empty string on success.
    """
    mode = artifact_access_mode()

    # Direct mode: always valid, no token needed
    if mode == ArtifactAccessMode.DIRECT:
        return True, ""

    # Signed mode: token is required
    if not token:
        return False, "missing download token"

    secret = artifact_signing_secret()
    if not secret:
        # Misconfigured — should not happen if startup validation passed
        return False, "server signing configuration error"

    # Parse expires
    expires_at: int | None = None
    if expires and expires != "":
        try:
            expires_at = int(expires)
        except ValueError:
            return False, "invalid expires parameter"

    # Check expiry
    if expires_at is not None and expires_at < int(time.time()):
        return False, "token expired"

    # Verify HMAC
    expected = _compute_hmac(secret, artifact_id, expires_at)
    if not hmac.compare_digest(token, expected):
        return False, "invalid token"

    return True, ""
