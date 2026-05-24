"""Voice Lab repository — storage boundary for voice tags and voice jobs.

Default implementation is in-memory. Mirrors the ComplianceRepository
pattern: a Protocol for the swap point, an in-memory implementation for
tests and local dev, and a factory function that route handlers consult.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Protocol
from uuid import UUID, uuid4

from app.schemas import (
    VoiceJob,
    VoiceJobCreateRequest,
    VoiceJobStatus,
    VoiceLabSummary,
    VoiceTag,
    VoiceTagCreateRequest,
)


VoiceLabRepositoryMode = Literal["in_memory", "postgres"]


class VoiceLabRepository(Protocol):
    mode: VoiceLabRepositoryMode

    # --- voice tags --------------------------------------------------------
    def list_tags(self) -> list[VoiceTag]: ...

    def get_tag(self, tag_id: UUID) -> VoiceTag | None: ...

    def create_tag(self, request: VoiceTagCreateRequest) -> VoiceTag: ...

    # --- voice jobs --------------------------------------------------------
    def list_jobs(self) -> list[VoiceJob]: ...

    def get_job(self, job_id: UUID) -> VoiceJob | None: ...

    def create_job(self, request: VoiceJobCreateRequest) -> VoiceJob: ...

    def set_job_status(
        self, job_id: UUID, status: VoiceJobStatus, **fields: object
    ) -> VoiceJob: ...

    # --- summary -----------------------------------------------------------
    def summary(self) -> VoiceLabSummary: ...


class InMemoryVoiceLabRepository:
    mode: VoiceLabRepositoryMode = "in_memory"

    def __init__(self) -> None:
        self._tags: dict[UUID, VoiceTag] = {}
        self._jobs: dict[UUID, VoiceJob] = {}

    # ---- voice tags -------------------------------------------------------

    def list_tags(self) -> list[VoiceTag]:
        return sorted(self._tags.values(), key=lambda t: t.created_at, reverse=True)

    def get_tag(self, tag_id: UUID) -> VoiceTag | None:
        return self._tags.get(tag_id)

    def create_tag(self, request: VoiceTagCreateRequest) -> VoiceTag:
        tag = VoiceTag(
            tag_id=uuid4(),
            label=request.label,
            consent_id=request.consent_id,
            provider_group=request.provider_group,
            notes=request.notes,
            created_at=datetime.now(timezone.utc),
        )
        self._tags[tag.tag_id] = tag
        return tag

    # ---- voice jobs -------------------------------------------------------

    def list_jobs(self) -> list[VoiceJob]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def get_job(self, job_id: UUID) -> VoiceJob | None:
        return self._jobs.get(job_id)

    def create_job(self, request: VoiceJobCreateRequest) -> VoiceJob:
        job = VoiceJob(
            job_id=uuid4(),
            kind=request.kind,
            status=VoiceJobStatus.DRAFT,
            voice_tag_id=request.voice_tag_id,
            consent_id=request.consent_id,
            prompt=request.prompt,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._jobs[job.job_id] = job
        return job

    def set_job_status(self, job_id: UUID, status: VoiceJobStatus, **fields: object) -> VoiceJob:
        job = self._require(job_id)
        updated = job.model_copy(
            update={"status": status, "updated_at": datetime.now(timezone.utc), **fields}
        )
        self._jobs[job_id] = updated
        return updated

    def _require(self, job_id: UUID) -> VoiceJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"voice_job_not_found:{job_id}")
        return job

    # ---- summary ----------------------------------------------------------

    def summary(self) -> VoiceLabSummary:
        jobs = list(self._jobs.values())
        return VoiceLabSummary(
            voice_tag_count=len(self._tags),
            voice_job_count=len(jobs),
            jobs_complete=sum(1 for j in jobs if j.status == VoiceJobStatus.COMPLETE),
            jobs_blocked=sum(1 for j in jobs if j.status == VoiceJobStatus.PREFLIGHT_BLOCKED),
        )


def build_default_voice_lab_repository() -> VoiceLabRepository:
    """Phase 1: in-memory only."""
    return InMemoryVoiceLabRepository()
