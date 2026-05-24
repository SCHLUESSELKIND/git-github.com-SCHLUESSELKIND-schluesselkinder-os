"""Lightweight worker executor for the async job system (S26).

Processes queued jobs synchronously — suitable for dev/test and for
the `run-once` API route. Not a background daemon; the caller decides
when to invoke `run_once`.

Hard rules:
- No real audio model calls.
- No external service calls in mock mode.
- Each job kind dispatches to its own handler.
- Failed jobs record the error and optionally retry.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.job_queue import JobQueue
from app.schemas import (
    AsyncJob,
    AsyncJobEvent,
    AsyncJobKind,
    AsyncJobProgress,
    AsyncJobResult,
    AsyncJobStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mark_running(job: AsyncJob) -> AsyncJob:
    """Transition a QUEUED job to RUNNING."""
    return job.model_copy(
        update={
            "status": AsyncJobStatus.RUNNING,
            "progress": AsyncJobProgress(progress=0.0, message="Starting", updated_at=_now()),
            "updated_at": _now(),
            "events": [
                *job.events,
                AsyncJobEvent(
                    event_type="job.running",
                    detail=f"Worker started {job.kind} job",
                    created_at=_now(),
                ),
            ],
        }
    )


def _mark_succeeded(job: AsyncJob, result_data: dict | None = None) -> AsyncJob:
    """Transition a RUNNING job to SUCCEEDED."""
    return job.model_copy(
        update={
            "status": AsyncJobStatus.SUCCEEDED,
            "progress": AsyncJobProgress(progress=1.0, message="Done", updated_at=_now()),
            "result": AsyncJobResult(data=result_data),
            "updated_at": _now(),
            "events": [
                *job.events,
                AsyncJobEvent(
                    event_type="job.succeeded",
                    detail=f"Completed {job.kind} job",
                    created_at=_now(),
                ),
            ],
        }
    )


def _mark_failed(job: AsyncJob, error: str) -> AsyncJob:
    """Transition a job to FAILED or RETRYING."""
    if job.retries < job.max_retries:
        return job.model_copy(
            update={
                "status": AsyncJobStatus.RETRYING,
                "retries": job.retries + 1,
                "result": AsyncJobResult(error=error),
                "updated_at": _now(),
                "events": [
                    *job.events,
                    AsyncJobEvent(
                        event_type="job.retrying",
                        detail=f"Retry {job.retries + 1}/{job.max_retries}: {error}",
                        created_at=_now(),
                    ),
                ],
            }
        )

    return job.model_copy(
        update={
            "status": AsyncJobStatus.FAILED,
            "result": AsyncJobResult(error=error),
            "updated_at": _now(),
            "events": [
                *job.events,
                AsyncJobEvent(
                    event_type="job.failed",
                    detail=f"Failed after {job.retries} retries: {error}",
                    created_at=_now(),
                ),
            ],
        }
    )


# ---------- Job kind handlers ----------


def _handle_generic(job: AsyncJob) -> AsyncJob:
    """Handle a generic job — mock execution that always succeeds."""
    return _mark_succeeded(job, result_data={"kind": "generic", "mock": True})


def _handle_music_router(job: AsyncJob) -> AsyncJob:
    """Handle a music_router job — mock execution."""
    return _mark_succeeded(
        job,
        result_data={
            "kind": "music_router",
            "mock": True,
            "payload_keys": list(job.payload.keys()),
        },
    )


def _handle_soundgraph_handoff(job: AsyncJob) -> AsyncJob:
    """Handle a soundgraph_handoff job — mock execution."""
    return _mark_succeeded(
        job,
        result_data={
            "kind": "soundgraph_handoff",
            "mock": True,
            "payload_keys": list(job.payload.keys()),
        },
    )


def _handle_dropbox_sync(job: AsyncJob) -> AsyncJob:
    """Handle a dropbox_sync job — mock execution."""
    return _mark_succeeded(
        job,
        result_data={
            "kind": "dropbox_sync",
            "mock": True,
            "payload_keys": list(job.payload.keys()),
        },
    )


def _handle_release_pack(job: AsyncJob) -> AsyncJob:
    """Handle a release_pack job — mock execution."""
    return _mark_succeeded(
        job,
        result_data={
            "kind": "release_pack",
            "mock": True,
            "payload_keys": list(job.payload.keys()),
        },
    )


_HANDLERS: dict[AsyncJobKind, callable] = {
    AsyncJobKind.GENERIC: _handle_generic,
    AsyncJobKind.MUSIC_ROUTER: _handle_music_router,
    AsyncJobKind.SOUNDGRAPH_HANDOFF: _handle_soundgraph_handoff,
    AsyncJobKind.DROPBOX_SYNC: _handle_dropbox_sync,
    AsyncJobKind.RELEASE_PACK: _handle_release_pack,
}


def execute_job(job: AsyncJob) -> AsyncJob:
    """Execute a single job synchronously.

    Transitions: QUEUED → RUNNING → SUCCEEDED | FAILED | RETRYING.
    Only runs jobs in QUEUED or RETRYING status.
    """
    if job.status not in (AsyncJobStatus.QUEUED, AsyncJobStatus.RETRYING):
        return _mark_failed(job, f"cannot_execute_from_status_{job.status}")

    running = _mark_running(job)

    handler = _HANDLERS.get(job.kind)
    if handler is None:
        return _mark_failed(running, f"unknown_job_kind_{job.kind}")

    try:
        return handler(running)
    except Exception as exc:
        return _mark_failed(running, str(exc))


def run_once(queue: JobQueue) -> AsyncJob | None:
    """Dequeue and execute one job. Returns the completed job or None.

    This is the main entry point for the worker. Call it from:
    - The `POST /v1/jobs/{job_id}/run-once` route
    - A future background daemon
    """
    job = queue.dequeue()
    if job is None:
        return None

    result = execute_job(job)
    queue.update(result)
    return result


def run_job_by_id(queue: JobQueue, job_id) -> AsyncJob | None:
    """Execute a specific job by ID, regardless of queue order.

    Used by the `POST /v1/jobs/{job_id}/run-once` route.
    """
    job = queue.get(job_id)
    if job is None:
        return None

    if job.status not in (AsyncJobStatus.QUEUED, AsyncJobStatus.RETRYING):
        return None

    result = execute_job(job)
    queue.update(result)
    return result
