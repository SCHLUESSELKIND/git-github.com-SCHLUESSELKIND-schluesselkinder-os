"""Dropbox Sync Provider Isolation Layer (S21).

Protocol + factory. Every Dropbox sync provider implementation must satisfy
`DropboxSyncProviderProtocol`. The factory function `build_dropbox_sync_provider()`
reads `SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER` and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic local output, no Dropbox API call.
- "dropbox" — real Dropbox SDK upload. Requires DROPBOX_ACCESS_TOKEN.

Hard rules:
1. Mock remains default — tests never hit Dropbox.
2. No silent fallback — if "dropbox" is selected but token is missing, fail loudly.
3. Real sync writes only files from the ExportPlan — no arbitrary filesystem access.
4. No destructive deletes — upload only, never remove remote files.

Adding a new provider:
1. Implement `DropboxSyncProviderProtocol` in a new submodule.
2. Register the value in `DropboxSyncProviderMode`.
3. Add the construction branch to `build_dropbox_sync_provider()`.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import DropboxExportPlan, DropboxSyncJob


class DropboxSyncProviderProtocol(Protocol):
    """Shared interface for all Dropbox sync providers.

    Each provider takes a READY_FOR_SYNC job + its plan and returns
    the updated job (SYNCED or FAILED). Route handlers never see
    Dropbox SDK types — only this Protocol.
    """

    name: str

    async def execute_sync(self, job: DropboxSyncJob, plan: DropboxExportPlan) -> DropboxSyncJob:
        """Upload files from the plan to the target.

        Precondition: job.status == READY_FOR_SYNC.
        Returns job with status SYNCED (all files uploaded) or FAILED (with error).
        """
        ...


def build_dropbox_sync_provider() -> DropboxSyncProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - DROPBOX: requires dropbox SDK + DROPBOX_ACCESS_TOKEN. Fails loudly if missing.
    """
    from app.config import (
        DropboxSyncProviderConfigError,
        DropboxSyncProviderMode,
        dropbox_access_token,
        dropbox_sync_provider_mode,
    )

    mode = dropbox_sync_provider_mode()

    if mode == DropboxSyncProviderMode.DROPBOX:
        token = dropbox_access_token()
        if not token:
            raise DropboxSyncProviderConfigError(
                "SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER=dropbox requires "
                "DROPBOX_ACCESS_TOKEN to be set. "
                "Service cannot start without a valid token in dropbox mode."
            )

        from app.providers.dropbox.real import RealDropboxSyncProvider

        return RealDropboxSyncProvider(access_token=token)  # type: ignore[return-value]

    # Default: mock
    from app.providers.dropbox.mock import MockDropboxSyncProvider

    return MockDropboxSyncProvider()  # type: ignore[return-value]
