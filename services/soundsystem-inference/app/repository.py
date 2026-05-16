from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.schemas import (
    ArtifactManifest,
    CompiledPrompt,
    GenerationJob,
    GenerationRequest,
    JobEvent,
    JobEventType,
    JobStatus,
)


class JobNotFoundError(KeyError):
    pass


class GenerationJobRepository(Protocol):
    """Persistence boundary for generation jobs.

    Why: the SQL artifact in db/001_initial_schema.sql is the canonical
    target (soundsystem.generation_jobs + soundsystem.generation_events).
    Until that storage is wired, the FastAPI app talks to this interface so
    swapping in a real Postgres-backed implementation does not require route
    changes.
    """

    def create(
        self, request: GenerationRequest, compiled_prompt: CompiledPrompt
    ) -> GenerationJob: ...

    def get(self, job_id: UUID) -> GenerationJob | None: ...

    def append_event(
        self, job_id: UUID, event_type: JobEventType, detail: str | None = None
    ) -> GenerationJob: ...

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: float,
        event_type: JobEventType | None = None,
    ) -> GenerationJob: ...

    def set_artifacts(
        self, job_id: UUID, artifacts: ArtifactManifest
    ) -> GenerationJob: ...

    def set_error(self, job_id: UUID, error: str) -> GenerationJob: ...


class InMemoryGenerationJobRepository:
    """In-process job repository for local dev and tests.

    Replaceable with a Postgres-backed implementation once the SQL schema in
    db/001_initial_schema.sql is wired up.
    """

    def __init__(self) -> None:
        self._jobs: dict[UUID, GenerationJob] = {}

    def create(
        self, request: GenerationRequest, compiled_prompt: CompiledPrompt
    ) -> GenerationJob:
        now = datetime.now(timezone.utc)
        job = GenerationJob(
            id=uuid4(),
            project_id=request.project_id,
            intent=request.intent,
            engine=request.engine,
            status=JobStatus.QUEUED,
            progress=0,
            created_at=now,
            updated_at=now,
            compiled_prompt=compiled_prompt,
            events=[
                JobEvent(event_type=JobEventType.JOB_CREATED, created_at=now),
                JobEvent(event_type=JobEventType.PROMPT_COMPILED, created_at=now),
                JobEvent(event_type=JobEventType.JOB_QUEUED, created_at=now),
            ],
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> GenerationJob | None:
        return self._jobs.get(job_id)

    def append_event(
        self, job_id: UUID, event_type: JobEventType, detail: str | None = None
    ) -> GenerationJob:
        job = self._require(job_id)
        now = datetime.now(timezone.utc)
        job.events.append(JobEvent(event_type=event_type, detail=detail, created_at=now))
        job.updated_at = now
        return job

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: float,
        event_type: JobEventType | None = None,
    ) -> GenerationJob:
        job = self._require(job_id)
        now = datetime.now(timezone.utc)
        job.status = status
        job.progress = progress
        job.updated_at = now
        if event_type is not None:
            job.events.append(JobEvent(event_type=event_type, created_at=now))
        return job

    def set_artifacts(
        self, job_id: UUID, artifacts: ArtifactManifest
    ) -> GenerationJob:
        job = self._require(job_id)
        job.artifacts = artifacts
        job.updated_at = datetime.now(timezone.utc)
        return job

    def set_error(self, job_id: UUID, error: str) -> GenerationJob:
        job = self._require(job_id)
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        return job

    def _require(self, job_id: UUID) -> GenerationJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise JobNotFoundError(job_id) from exc
