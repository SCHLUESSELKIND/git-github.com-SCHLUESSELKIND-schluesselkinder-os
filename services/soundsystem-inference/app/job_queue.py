"""Job queue abstraction for the async worker system (S26).

Provides a Protocol-based interface for enqueueing, dequeuing, and managing
async jobs. Ships with an in-memory implementation for dev/test; a Redis
adapter boundary is defined but not implemented (future slice).

Hard rules:
- In-memory mode must pass all tests without external services.
- Redis mode, when selected, must fail loudly if SOUNDSYSTEM_REDIS_URL is unset.
- No silent fallbacks in production.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from app.config import (
    JobQueueConfigError,
    JobQueueMode,
    job_queue_mode,
    job_queue_redis_url,
)
from app.schemas import (
    AsyncJob,
    AsyncJobCreateRequest,
    AsyncJobEvent,
    AsyncJobKind,
    AsyncJobStatus,
    AsyncJobSummary,
)


@runtime_checkable
class JobQueue(Protocol):
    """Protocol for async job queue implementations."""

    @property
    def mode(self) -> str: ...

    def enqueue(
        self,
        request: AsyncJobCreateRequest,
        operator_id: str | None = None,
    ) -> AsyncJob: ...

    def get(self, job_id: UUID) -> AsyncJob | None: ...

    def list_all(self, *, kind: AsyncJobKind | None = None) -> list[AsyncJob]: ...

    def update(self, job: AsyncJob) -> None: ...

    def cancel(self, job_id: UUID) -> AsyncJob | None: ...

    def dequeue(self) -> AsyncJob | None:
        """Pop the next QUEUED job for execution. Returns None when empty."""
        ...

    def summary(self) -> AsyncJobSummary: ...


class InMemoryJobQueue:
    """In-memory job queue for dev and test environments."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, AsyncJob] = {}
        self._queue: list[UUID] = []  # FIFO order for dequeue

    @property
    def mode(self) -> str:
        return "in_memory"

    def enqueue(
        self,
        request: AsyncJobCreateRequest,
        operator_id: str | None = None,
    ) -> AsyncJob:
        now = datetime.now(timezone.utc)
        job = AsyncJob(
            job_id=uuid4(),
            kind=request.kind,
            status=AsyncJobStatus.QUEUED,
            payload=request.payload,
            max_retries=request.max_retries,
            operator_id=operator_id,
            created_at=now,
            updated_at=now,
            events=[
                AsyncJobEvent(
                    event_type="job.queued",
                    detail=f"Enqueued {request.kind} job",
                    created_at=now,
                ),
            ],
        )
        self._jobs[job.job_id] = job
        self._queue.append(job.job_id)
        return job

    def get(self, job_id: UUID) -> AsyncJob | None:
        return self._jobs.get(job_id)

    def list_all(self, *, kind: AsyncJobKind | None = None) -> list[AsyncJob]:
        jobs = list(self._jobs.values())
        if kind is not None:
            jobs = [j for j in jobs if j.kind == kind]
        # Most recent first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    def update(self, job: AsyncJob) -> None:
        if job.job_id not in self._jobs:
            raise ValueError(f"job {job.job_id} not found in queue")
        self._jobs[job.job_id] = job

    def cancel(self, job_id: UUID) -> AsyncJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status in (AsyncJobStatus.SUCCEEDED, AsyncJobStatus.FAILED):
            return None  # Terminal states cannot be cancelled
        now = datetime.now(timezone.utc)
        cancelled = job.model_copy(
            update={
                "status": AsyncJobStatus.CANCELLED,
                "updated_at": now,
                "events": [
                    *job.events,
                    AsyncJobEvent(
                        event_type="job.cancelled",
                        detail="Cancelled by operator",
                        created_at=now,
                    ),
                ],
            }
        )
        self._jobs[job_id] = cancelled
        # Remove from pending queue
        if job_id in self._queue:
            self._queue.remove(job_id)
        return cancelled

    def dequeue(self) -> AsyncJob | None:
        while self._queue:
            job_id = self._queue.pop(0)
            job = self._jobs.get(job_id)
            if job is not None and job.status == AsyncJobStatus.QUEUED:
                return job
        return None

    def summary(self) -> AsyncJobSummary:
        jobs = list(self._jobs.values())
        return AsyncJobSummary(
            total=len(jobs),
            queued=sum(1 for j in jobs if j.status == AsyncJobStatus.QUEUED),
            running=sum(1 for j in jobs if j.status == AsyncJobStatus.RUNNING),
            succeeded=sum(1 for j in jobs if j.status == AsyncJobStatus.SUCCEEDED),
            failed=sum(1 for j in jobs if j.status == AsyncJobStatus.FAILED),
            cancelled=sum(1 for j in jobs if j.status == AsyncJobStatus.CANCELLED),
            retrying=sum(1 for j in jobs if j.status == AsyncJobStatus.RETRYING),
        )


def build_job_queue() -> InMemoryJobQueue:
    """Factory: build a job queue based on the configured mode.

    Defaults to in-memory. If redis is configured, fails loudly when
    the Redis URL is missing.
    """
    mode = job_queue_mode()

    if mode == JobQueueMode.IN_MEMORY:
        return InMemoryJobQueue()

    if mode == JobQueueMode.REDIS:
        url = job_queue_redis_url()
        if not url:
            raise JobQueueConfigError(
                f"{JobQueueMode.REDIS} mode requires SOUNDSYSTEM_REDIS_URL to be set"
            )
        # Redis adapter not yet implemented — fail loudly
        raise JobQueueConfigError(
            "Redis job queue adapter is not yet implemented. "
            "Use SOUNDSYSTEM_JOB_QUEUE=in_memory for now."
        )

    # Unreachable — job_queue_mode() validates the value
    raise JobQueueConfigError(f"unsupported job queue mode: {mode}")
