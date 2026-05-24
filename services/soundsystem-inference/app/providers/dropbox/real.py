"""Real Dropbox Sync Provider (S21).

Uploads files from an ExportPlan to Dropbox via the official SDK.
Gated behind SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER=dropbox + DROPBOX_ACCESS_TOKEN.

Hard rules:
- Only uploads files listed in the ExportPlan — no arbitrary filesystem access.
- Never deletes remote files — upload only.
- Fails with FAILED status (not exception) if upload encounters errors.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.schemas import (
    DropboxExportPlan,
    DropboxFolderEntry,
    DropboxSyncJob,
    DropboxSyncStatus,
)

logger = logging.getLogger(__name__)


class RealDropboxSyncProvider:
    """Real Dropbox implementation using the official Dropbox SDK.

    Only writes files from the ExportPlan. Never deletes.
    Requires `dropbox` package to be installed.
    """

    name: str = "dropbox"

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token
        self._dropbox_module = self._import_sdk()
        self._client = self._dropbox_module.Dropbox(self._access_token)

    @staticmethod
    def _import_sdk():  # noqa: ANN205
        """Import the Dropbox SDK at construction time.

        Raises ImportError if the dropbox SDK is not installed.
        """
        try:
            import dropbox  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "The 'dropbox' package is required for real Dropbox sync. "
                "Install it with: pip install dropbox"
            ) from exc
        return dropbox

    async def execute_sync(self, job: DropboxSyncJob, plan: DropboxExportPlan) -> DropboxSyncJob:
        """Upload all files from the plan to Dropbox.

        For each non-directory entry in the plan, we upload a placeholder
        JSON file (since the real binary content lives in the generation
        pipeline and isn't materialized to disk yet). In future slices,
        this will stream actual artifact bytes.

        Returns SYNCED on success, FAILED on any Dropbox API error.
        """
        if job.status != DropboxSyncStatus.READY_FOR_SYNC:
            return job.model_copy(
                update={
                    "status": DropboxSyncStatus.FAILED,
                    "error": f"cannot sync from status {job.status.value}",
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        files_synced = 0
        try:
            for entry in plan.entries:
                if entry.is_directory:
                    # Dropbox auto-creates directories on file upload
                    continue
                self._upload_entry(plan.target_root, entry)
                files_synced += 1

            return job.model_copy(
                update={
                    "status": DropboxSyncStatus.SYNCED,
                    "files_synced": files_synced,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        except Exception as exc:
            logger.error(
                "Dropbox sync failed for job %s: %s",
                job.sync_id,
                exc,
                exc_info=True,
            )
            return job.model_copy(
                update={
                    "status": DropboxSyncStatus.FAILED,
                    "files_synced": files_synced,
                    "error": f"dropbox_upload_error: {exc}",
                    "updated_at": datetime.now(timezone.utc),
                }
            )

    def _upload_entry(self, target_root: str, entry: DropboxFolderEntry) -> None:
        """Upload a single entry to Dropbox.

        Creates a JSON stub for metadata entries and a placeholder for
        binary artifacts (the real bytes will come from the artifact store
        in a future slice).
        """
        remote_path = f"{target_root}/{entry.relative_path}"

        # For now, all entries get a JSON stub describing what they represent.
        # Binary content (WAV, stems) will be streamed from artifact storage
        # once that integration is built.
        content = json.dumps(
            {
                "source_component_type": entry.source_component_type,
                "source_label": entry.source_label,
                "size_hint": entry.size_hint,
                "placeholder": True,
                "note": "Real binary content will be uploaded when artifact storage is integrated.",
            },
            indent=2,
        ).encode("utf-8")

        self._client.files_upload(
            content,
            remote_path,
            mode=self._dropbox_module.files.WriteMode.overwrite,
            mute=True,
        )
        logger.debug("Uploaded %s (%d bytes)", remote_path, len(content))
