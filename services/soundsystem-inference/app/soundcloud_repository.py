"""SoundCloud Publish Job Repository — S36.

In-memory repository for SoundCloud publish jobs. Stores job metadata
and lifecycle status. No Postgres implementation in this slice.

Operations:
- store: insert a new publish job
- get: lookup by job_id
- list_all: all jobs, newest first
- update: overwrite an existing job
- summary: aggregate counts
"""

from __future__ import annotations

from uuid import UUID

from app.schemas import (
    SoundCloudPublishJob,
    SoundCloudPublishStatus,
    SoundCloudPublishSummary,
)


class InMemorySoundCloudPublishRepository:
    """In-memory SoundCloud publish job repository. Data lost on restart."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, SoundCloudPublishJob] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, job: SoundCloudPublishJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: UUID) -> SoundCloudPublishJob | None:
        return self._jobs.get(job_id)

    def list_all(self) -> list[SoundCloudPublishJob]:
        return sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )

    def update(self, job: SoundCloudPublishJob) -> None:
        self._jobs[job.job_id] = job

    def summary(self) -> SoundCloudPublishSummary:
        jobs = list(self._jobs.values())
        return SoundCloudPublishSummary(
            total_jobs=len(jobs),
            drafts=sum(1 for j in jobs if j.status == SoundCloudPublishStatus.DRAFT),
            ready=sum(1 for j in jobs if j.status == SoundCloudPublishStatus.READY),
            published_mock=sum(
                1 for j in jobs if j.status == SoundCloudPublishStatus.PUBLISHED_MOCK
            ),
            failed=sum(1 for j in jobs if j.status == SoundCloudPublishStatus.FAILED),
            blocked=sum(1 for j in jobs if j.status == SoundCloudPublishStatus.BLOCKED),
        )
