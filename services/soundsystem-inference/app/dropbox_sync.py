"""Dropbox Export Sync — S20.

Builds a reproducible Dropbox folder structure from an ExportPack,
tracks sync jobs, and provides a mock sync provider. No real Dropbox API
calls — that ships in S21.

The folder plan is deterministic: same pack always produces the same
structure. The sync job tracks planned → ready_for_sync → synced/failed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas import (
    DropboxExportPlan,
    DropboxFolderEntry,
    DropboxSyncJob,
    DropboxSyncStatus,
    DropboxSyncSummary,
    ExportPack,
    ExportPackComponent,
)


# ---------- Folder Plan Builder ----------


DEFAULT_DROPBOX_ROOT = "/SNUFFRAGA/Projects"


def _sanitize_folder_name(title: str) -> str:
    """Convert a title to a safe folder name for Dropbox."""
    safe = title.strip()
    # Replace problematic chars
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        safe = safe.replace(ch, "-")
    safe = safe.strip("-").strip()
    return safe[:100] or "untitled"


def _component_to_filename(component: ExportPackComponent) -> str:
    """Derive a filename from a component type and label."""
    ctype = component.component_type
    if ctype == "music_job":
        return "music_job.json"
    if ctype == "lyrics_version":
        return "lyrics.json"
    if ctype == "soundgraph_arrangement":
        return "soundgraph.json"
    if ctype == "output_provenance":
        return "provenance.json"
    if ctype.startswith("artifact_"):
        # e.g. artifact_full_mix → full_mix.wav, artifact_stem_pack → stems/
        artifact_name = ctype.replace("artifact_", "")
        if "stem" in artifact_name:
            return f"stems/{artifact_name}/"
        # Use the path extension if available from the component
        return f"{artifact_name}.wav"
    return f"{ctype}.json"


def _component_is_directory(component: ExportPackComponent) -> bool:
    """Check if a component maps to a directory rather than a file."""
    return "stem_pack" in component.component_type


def _size_hint_for_component(component: ExportPackComponent) -> str | None:
    """Rough size hint for display."""
    ctype = component.component_type
    if ctype == "music_job":
        return "~2 KB"
    if ctype == "lyrics_version":
        return "~4 KB"
    if ctype == "soundgraph_arrangement":
        return "~8 KB"
    if ctype == "output_provenance":
        return "~1 KB"
    if "full_mix" in ctype:
        return "~30 MB"
    if "stem" in ctype:
        return "~50 MB"
    if "loop" in ctype:
        return "~5 MB"
    return None


def build_export_plan(
    pack: ExportPack,
    target_root_override: str | None = None,
) -> DropboxExportPlan:
    """Build a deterministic Dropbox folder plan from an ExportPack.

    The structure:
      {root}/{sanitized_title}/
        music_job.json
        lyrics.json
        soundgraph.json
        provenance.json
        stems/
        full_mix.wav
        manifest.json (always included — describes the pack itself)
    """
    root = target_root_override or DEFAULT_DROPBOX_ROOT
    folder_name = _sanitize_folder_name(pack.title)
    target_root = f"{root}/{folder_name}"

    entries: list[DropboxFolderEntry] = []

    # Always include the manifest (the pack metadata itself)
    entries.append(
        DropboxFolderEntry(
            relative_path="manifest.json",
            source_component_type="pack_manifest",
            source_label=f"Pack manifest: {pack.title}",
            size_hint="~3 KB",
            is_directory=False,
        )
    )

    # Map each component to a folder entry
    for component in pack.components:
        filename = _component_to_filename(component)
        is_dir = _component_is_directory(component)
        entries.append(
            DropboxFolderEntry(
                relative_path=filename,
                source_component_type=component.component_type,
                source_label=component.label,
                size_hint=_size_hint_for_component(component),
                is_directory=is_dir,
            )
        )

    total_files = sum(1 for e in entries if not e.is_directory)
    total_dirs = sum(1 for e in entries if e.is_directory)

    return DropboxExportPlan(
        plan_id=uuid4(),
        pack_id=pack.pack_id,
        pack_title=pack.title,
        target_root=target_root,
        entries=entries,
        total_files=total_files,
        total_directories=total_dirs,
    )


def create_sync_job(
    plan: DropboxExportPlan,
    operator_id: str | None = None,
) -> DropboxSyncJob:
    """Create a sync job from a plan, initially in PLANNED status."""
    return DropboxSyncJob(
        sync_id=uuid4(),
        pack_id=plan.pack_id,
        plan_id=plan.plan_id,
        status=DropboxSyncStatus.PLANNED,
        target_root=plan.target_root,
        files_planned=plan.total_files,
        files_synced=0,
        operator_id=operator_id,
    )


def mark_ready_for_sync(job: DropboxSyncJob) -> DropboxSyncJob:
    """Transition a sync job to READY_FOR_SYNC.

    In S21, this is where the real Dropbox auth check would happen.
    For now, it always succeeds.
    """
    return job.model_copy(
        update={
            "status": DropboxSyncStatus.READY_FOR_SYNC,
            "updated_at": datetime.now(timezone.utc),
        }
    )


def mock_execute_sync(job: DropboxSyncJob) -> DropboxSyncJob:
    """Mock sync execution — marks all files as synced immediately.

    Real Dropbox upload lands in S21. This mock validates the contract:
    READY_FOR_SYNC → SYNCED with all files counted.
    """
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


# ---------- Repository ----------


class DropboxSyncRepository:
    """In-memory repository for Dropbox export plans and sync jobs."""

    def __init__(self) -> None:
        self._plans: dict[UUID, DropboxExportPlan] = {}
        self._plans_by_pack: dict[UUID, UUID] = {}
        self._jobs: dict[UUID, DropboxSyncJob] = {}
        self._jobs_by_pack: dict[UUID, UUID] = {}

    def store_plan(self, plan: DropboxExportPlan) -> None:
        self._plans[plan.plan_id] = plan
        self._plans_by_pack[plan.pack_id] = plan.plan_id

    def get_plan(self, plan_id: UUID) -> DropboxExportPlan | None:
        return self._plans.get(plan_id)

    def get_plan_by_pack(self, pack_id: UUID) -> DropboxExportPlan | None:
        plan_id = self._plans_by_pack.get(pack_id)
        if plan_id is None:
            return None
        return self._plans.get(plan_id)

    def list_plans(self) -> list[DropboxExportPlan]:
        return sorted(
            self._plans.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )

    def store_job(self, job: DropboxSyncJob) -> None:
        self._jobs[job.sync_id] = job
        self._jobs_by_pack[job.pack_id] = job.sync_id

    def get_job(self, sync_id: UUID) -> DropboxSyncJob | None:
        return self._jobs.get(sync_id)

    def get_job_by_pack(self, pack_id: UUID) -> DropboxSyncJob | None:
        sync_id = self._jobs_by_pack.get(pack_id)
        if sync_id is None:
            return None
        return self._jobs.get(sync_id)

    def update_job(self, job: DropboxSyncJob) -> None:
        self._jobs[job.sync_id] = job

    def list_jobs(self) -> list[DropboxSyncJob]:
        return sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )

    def summary(self) -> DropboxSyncSummary:
        jobs = list(self._jobs.values())
        return DropboxSyncSummary(
            total_plans=len(self._plans),
            total_sync_jobs=len(jobs),
            jobs_planned=sum(1 for j in jobs if j.status == DropboxSyncStatus.PLANNED),
            jobs_ready=sum(1 for j in jobs if j.status == DropboxSyncStatus.READY_FOR_SYNC),
            jobs_synced=sum(1 for j in jobs if j.status == DropboxSyncStatus.SYNCED),
            jobs_failed=sum(1 for j in jobs if j.status == DropboxSyncStatus.FAILED),
        )
