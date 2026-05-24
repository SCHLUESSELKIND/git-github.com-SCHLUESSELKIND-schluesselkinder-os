from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.schemas import (
    MasterBusJob,
    MasterBusManifest,
    MasterBusRequest,
    MasterJobStatus,
)


class MasterJobNotFoundError(KeyError):
    pass


class MasterBusRepository(Protocol):
    """Persistence boundary for SNUFFRAGA MASTER BUS jobs.

    Why: mastering produces its own audit trail (modes used, export profiles
    rendered, reference clearance state). It is a distinct concern from
    generation and gets its own repository for the same reason GenerationJob
    does — to keep the FastAPI app storage-agnostic until Postgres lands.
    """

    def create(self, request: MasterBusRequest) -> MasterBusJob: ...

    def get(self, job_id: UUID) -> MasterBusJob | None: ...

    def update_status(
        self, job_id: UUID, status: MasterJobStatus, progress: float
    ) -> MasterBusJob: ...

    def set_manifest(self, job_id: UUID, manifest: MasterBusManifest) -> MasterBusJob: ...

    def set_error(self, job_id: UUID, error: str) -> MasterBusJob: ...


class InMemoryMasterBusRepository:
    def __init__(self) -> None:
        self._jobs: dict[UUID, MasterBusJob] = {}

    def create(self, request: MasterBusRequest) -> MasterBusJob:
        now = datetime.now(timezone.utc)
        job = MasterBusJob(
            id=uuid4(),
            generation_id=request.generation_id,
            mode=request.mode,
            profiles=list(request.profiles),
            status=MasterJobStatus.QUEUED,
            progress=0,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> MasterBusJob | None:
        return self._jobs.get(job_id)

    def update_status(self, job_id: UUID, status: MasterJobStatus, progress: float) -> MasterBusJob:
        job = self._require(job_id)
        job.status = status
        job.progress = progress
        job.updated_at = datetime.now(timezone.utc)
        return job

    def set_manifest(self, job_id: UUID, manifest: MasterBusManifest) -> MasterBusJob:
        job = self._require(job_id)
        job.manifest = manifest
        job.updated_at = datetime.now(timezone.utc)
        return job

    def set_error(self, job_id: UUID, error: str) -> MasterBusJob:
        job = self._require(job_id)
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        return job

    def _require(self, job_id: UUID) -> MasterBusJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise MasterJobNotFoundError(job_id) from exc
