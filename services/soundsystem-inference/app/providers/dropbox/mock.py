"""Mock Dropbox Sync Provider (S21).

Default provider — no external dependencies, deterministic results.
Replicates the S20 mock_execute_sync logic behind the Provider Protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import DropboxExportPlan, DropboxSyncJob, DropboxSyncStatus


class MockDropboxSyncProvider:
    """Mock implementation — marks all files as synced immediately.

    No real Dropbox API calls. Safe for tests and local development.
    """

    name: str = "mock"

    async def execute_sync(self, job: DropboxSyncJob, plan: DropboxExportPlan) -> DropboxSyncJob:
        """Mock sync: READY_FOR_SYNC → SYNCED with all files counted."""
        if job.status != DropboxSyncStatus.READY_FOR_SYNC:
            return job.model_copy(
                update={
                    "status": DropboxSyncStatus.FAILED,
                    "error": f"cannot sync from status {job.status.value}",
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        return job.model_copy(
            update={
                "status": DropboxSyncStatus.SYNCED,
                "files_synced": job.files_planned,
                "updated_at": datetime.now(timezone.utc),
            }
        )
