"""Tests for S26 — Async Worker System.

Covers:
- Config (JobQueueMode, env var parsing, loud failure)
- InMemoryJobQueue (Protocol compliance, full CRUD, dequeue, summary)
- Factory (build_job_queue with in_memory/redis modes)
- Worker executor (execute_job, run_once, run_job_by_id)
- API routes (6 endpoints via direct handler calls)
- Capabilities integration
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.auth import DEV_OPERATOR
from app.config import (
    JOB_QUEUE_ENV,
    REDIS_URL_ENV,
    JobQueueConfigError,
    JobQueueMode,
    job_queue_mode,
)
from app.job_queue import (
    InMemoryJobQueue,
    build_job_queue,
)
from app.job_worker import (
    execute_job,
    run_job_by_id,
    run_once,
)
from app.schemas import (
    AsyncJob,
    AsyncJobCreateRequest,
    AsyncJobKind,
    AsyncJobStatus,
)


# ---------- Fixtures ----------


def _make_request(
    kind: AsyncJobKind = AsyncJobKind.GENERIC,
    payload: dict | None = None,
    max_retries: int = 2,
) -> AsyncJobCreateRequest:
    return AsyncJobCreateRequest(
        kind=kind,
        payload=payload or {},
        max_retries=max_retries,
    )


# ---------- Config Tests ----------


class TestJobQueueConfig:
    def test_default_mode_is_in_memory(self, monkeypatch):
        monkeypatch.delenv(JOB_QUEUE_ENV, raising=False)
        assert job_queue_mode() == JobQueueMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "in_memory")
        assert job_queue_mode() == JobQueueMode.IN_MEMORY

    def test_redis_mode(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "redis")
        assert job_queue_mode() == JobQueueMode.REDIS

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "REDIS")
        assert job_queue_mode() == JobQueueMode.REDIS

    def test_invalid_mode_raises(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "rabbitmq")
        with pytest.raises(RuntimeError, match="invalid"):
            job_queue_mode()


# ---------- Factory Tests ----------


class TestBuildJobQueue:
    def test_default_returns_in_memory(self, monkeypatch):
        monkeypatch.delenv(JOB_QUEUE_ENV, raising=False)
        queue = build_job_queue()
        assert isinstance(queue, InMemoryJobQueue)
        assert queue.mode == "in_memory"

    def test_redis_without_url_raises(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "redis")
        monkeypatch.delenv(REDIS_URL_ENV, raising=False)
        with pytest.raises(JobQueueConfigError, match="SOUNDSYSTEM_REDIS_URL"):
            build_job_queue()

    def test_redis_with_url_raises_not_implemented(self, monkeypatch):
        monkeypatch.setenv(JOB_QUEUE_ENV, "redis")
        monkeypatch.setenv(REDIS_URL_ENV, "redis://localhost:6379")
        with pytest.raises(JobQueueConfigError, match="not yet implemented"):
            build_job_queue()


# ---------- InMemoryJobQueue Tests ----------


class TestInMemoryJobQueue:
    def test_enqueue_creates_queued_job(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        assert job.status == AsyncJobStatus.QUEUED
        assert job.kind == AsyncJobKind.GENERIC
        assert len(job.events) == 1
        assert job.events[0].event_type == "job.queued"

    def test_enqueue_preserves_operator(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(), operator_id="op-42")
        assert job.operator_id == "op-42"

    def test_enqueue_preserves_payload(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(payload={"key": "value"}))
        assert job.payload == {"key": "value"}

    def test_get_existing(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        assert queue.get(job.job_id) is not None
        assert queue.get(job.job_id).job_id == job.job_id

    def test_get_nonexistent(self):
        queue = InMemoryJobQueue()
        assert queue.get(uuid4()) is None

    def test_list_all_empty(self):
        queue = InMemoryJobQueue()
        assert queue.list_all() == []

    def test_list_all_returns_all(self):
        queue = InMemoryJobQueue()
        queue.enqueue(_make_request())
        queue.enqueue(_make_request(kind=AsyncJobKind.MUSIC_ROUTER))
        queue.enqueue(_make_request(kind=AsyncJobKind.DROPBOX_SYNC))
        assert len(queue.list_all()) == 3

    def test_list_all_filter_by_kind(self):
        queue = InMemoryJobQueue()
        queue.enqueue(_make_request(kind=AsyncJobKind.GENERIC))
        queue.enqueue(_make_request(kind=AsyncJobKind.MUSIC_ROUTER))
        queue.enqueue(_make_request(kind=AsyncJobKind.GENERIC))
        result = queue.list_all(kind=AsyncJobKind.GENERIC)
        assert len(result) == 2
        assert all(j.kind == AsyncJobKind.GENERIC for j in result)

    def test_list_all_ordered_by_created_desc(self):
        queue = InMemoryJobQueue()
        for _ in range(3):
            queue.enqueue(_make_request())
        jobs = queue.list_all()
        for i in range(len(jobs) - 1):
            assert jobs[i].created_at >= jobs[i + 1].created_at

    def test_update_persists(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        updated = job.model_copy(update={"status": AsyncJobStatus.RUNNING})
        queue.update(updated)
        assert queue.get(job.job_id).status == AsyncJobStatus.RUNNING

    def test_update_nonexistent_raises(self):
        queue = InMemoryJobQueue()
        fake = AsyncJob(
            job_id=uuid4(),
            kind=AsyncJobKind.GENERIC,
        )
        with pytest.raises(ValueError, match="not found"):
            queue.update(fake)

    def test_cancel_queued_job(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        cancelled = queue.cancel(job.job_id)
        assert cancelled is not None
        assert cancelled.status == AsyncJobStatus.CANCELLED
        assert any(e.event_type == "job.cancelled" for e in cancelled.events)

    def test_cancel_succeeded_returns_none(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        succeeded = job.model_copy(update={"status": AsyncJobStatus.SUCCEEDED})
        queue.update(succeeded)
        assert queue.cancel(job.job_id) is None

    def test_cancel_nonexistent_returns_none(self):
        queue = InMemoryJobQueue()
        assert queue.cancel(uuid4()) is None

    def test_dequeue_fifo(self):
        queue = InMemoryJobQueue()
        j1 = queue.enqueue(_make_request())
        j2 = queue.enqueue(_make_request())
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.job_id == j1.job_id
        dequeued2 = queue.dequeue()
        assert dequeued2 is not None
        assert dequeued2.job_id == j2.job_id

    def test_dequeue_empty_returns_none(self):
        queue = InMemoryJobQueue()
        assert queue.dequeue() is None

    def test_dequeue_skips_cancelled(self):
        queue = InMemoryJobQueue()
        j1 = queue.enqueue(_make_request())
        j2 = queue.enqueue(_make_request())
        queue.cancel(j1.job_id)
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.job_id == j2.job_id

    def test_summary(self):
        queue = InMemoryJobQueue()
        queue.enqueue(_make_request())
        queue.enqueue(_make_request())
        j3 = queue.enqueue(_make_request())
        queue.cancel(j3.job_id)
        s = queue.summary()
        assert s.total == 3
        assert s.queued == 2
        assert s.cancelled == 1
        assert s.running == 0

    def test_mode_property(self):
        queue = InMemoryJobQueue()
        assert queue.mode == "in_memory"


# ---------- Worker Executor Tests ----------


class TestJobWorker:
    def test_execute_generic_succeeds(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        result = execute_job(job)
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.progress.progress == 1.0
        assert result.result is not None
        assert result.result.data["kind"] == "generic"
        assert result.result.data["mock"] is True

    def test_execute_music_router(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(kind=AsyncJobKind.MUSIC_ROUTER))
        result = execute_job(job)
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.result.data["kind"] == "music_router"

    def test_execute_soundgraph_handoff(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(kind=AsyncJobKind.SOUNDGRAPH_HANDOFF))
        result = execute_job(job)
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.result.data["kind"] == "soundgraph_handoff"

    def test_execute_dropbox_sync(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(kind=AsyncJobKind.DROPBOX_SYNC))
        result = execute_job(job)
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.result.data["kind"] == "dropbox_sync"

    def test_execute_release_pack(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(kind=AsyncJobKind.RELEASE_PACK))
        result = execute_job(job)
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.result.data["kind"] == "release_pack"

    def test_execute_from_wrong_status_fails(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        # Manually set to SUCCEEDED
        done = job.model_copy(update={"status": AsyncJobStatus.SUCCEEDED})
        result = execute_job(done)
        assert result.status in (AsyncJobStatus.FAILED, AsyncJobStatus.RETRYING)

    def test_execute_preserves_payload_keys_in_result(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(
            _make_request(kind=AsyncJobKind.MUSIC_ROUTER, payload={"track_id": "abc"})
        )
        result = execute_job(job)
        assert "track_id" in result.result.data["payload_keys"]

    def test_execute_events_accumulate(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        result = execute_job(job)
        types = [e.event_type for e in result.events]
        assert "job.queued" in types
        assert "job.running" in types
        assert "job.succeeded" in types

    def test_run_once_processes_and_updates_queue(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        result = run_once(queue)
        assert result is not None
        assert result.status == AsyncJobStatus.SUCCEEDED
        # Queue should be updated too
        stored = queue.get(job.job_id)
        assert stored.status == AsyncJobStatus.SUCCEEDED

    def test_run_once_empty_queue_returns_none(self):
        queue = InMemoryJobQueue()
        assert run_once(queue) is None

    def test_run_job_by_id(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        result = run_job_by_id(queue, job.job_id)
        assert result is not None
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.job_id == job.job_id

    def test_run_job_by_id_nonexistent_returns_none(self):
        queue = InMemoryJobQueue()
        assert run_job_by_id(queue, uuid4()) is None

    def test_run_job_by_id_already_done_returns_none(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request())
        run_job_by_id(queue, job.job_id)  # Runs it
        assert run_job_by_id(queue, job.job_id) is None  # Already done

    def test_retrying_job_can_be_executed(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue(_make_request(max_retries=2))
        # Simulate a retrying job
        retrying = job.model_copy(update={"status": AsyncJobStatus.RETRYING, "retries": 1})
        queue.update(retrying)
        result = execute_job(retrying)
        assert result.status == AsyncJobStatus.SUCCEEDED


# ---------- Route Tests ----------


class TestAsyncJobRoutes:
    def test_create_job(self):
        from app.main import create_async_job as route

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC, payload={"test": True})
        job = asyncio.run(route(req, DEV_OPERATOR))
        assert job.status == AsyncJobStatus.QUEUED
        assert job.kind == AsyncJobKind.GENERIC
        assert job.operator_id == DEV_OPERATOR.operator_id

    def test_list_jobs(self):
        from app.main import create_async_job as route_create, list_async_jobs as route_list

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC)
        asyncio.run(route_create(req, DEV_OPERATOR))
        jobs = asyncio.run(route_list())
        assert len(jobs) >= 1

    def test_list_jobs_filter_by_kind(self):
        from app.main import create_async_job as route_create, list_async_jobs as route_list

        asyncio.run(route_create(AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC), DEV_OPERATOR))
        asyncio.run(
            route_create(AsyncJobCreateRequest(kind=AsyncJobKind.MUSIC_ROUTER), DEV_OPERATOR)
        )
        generic_jobs = asyncio.run(route_list(kind=AsyncJobKind.GENERIC))
        assert all(j.kind == AsyncJobKind.GENERIC for j in generic_jobs)

    def test_get_job(self):
        from app.main import create_async_job as route_create, get_async_job as route_get

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC)
        job = asyncio.run(route_create(req, DEV_OPERATOR))
        retrieved = asyncio.run(route_get(job.job_id))
        assert retrieved.job_id == job.job_id

    def test_get_job_not_found(self):
        from app.main import get_async_job as route_get

        with pytest.raises(Exception, match="async_job_not_found"):
            asyncio.run(route_get(uuid4()))

    def test_cancel_job(self):
        from app.main import (
            cancel_async_job as route_cancel,
            create_async_job as route_create,
        )

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC)
        job = asyncio.run(route_create(req, DEV_OPERATOR))
        cancelled = asyncio.run(route_cancel(job.job_id, DEV_OPERATOR))
        assert cancelled.status == AsyncJobStatus.CANCELLED

    def test_cancel_nonexistent_raises(self):
        from app.main import cancel_async_job as route_cancel

        with pytest.raises(Exception, match="async_job_not_cancellable"):
            asyncio.run(route_cancel(uuid4(), DEV_OPERATOR))

    def test_run_once_route(self):
        from app.main import (
            create_async_job as route_create,
            run_async_job_once as route_run,
        )

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC)
        job = asyncio.run(route_create(req, DEV_OPERATOR))
        result = asyncio.run(route_run(job.job_id, DEV_OPERATOR))
        assert result.status == AsyncJobStatus.SUCCEEDED

    def test_run_once_already_done_raises(self):
        from app.main import (
            create_async_job as route_create,
            run_async_job_once as route_run,
        )

        req = AsyncJobCreateRequest(kind=AsyncJobKind.GENERIC)
        job = asyncio.run(route_create(req, DEV_OPERATOR))
        asyncio.run(route_run(job.job_id, DEV_OPERATOR))
        with pytest.raises(Exception, match="async_job_not_runnable"):
            asyncio.run(route_run(job.job_id, DEV_OPERATOR))

    def test_summary_route(self):
        from app.main import async_job_summary as route_summary

        summary = asyncio.run(route_summary())
        assert summary.total >= 0

    def test_capabilities_includes_job_queue(self):
        from app.main import capabilities as route

        caps = asyncio.run(route())
        assert caps.job_queue_available is True
        assert caps.job_queue_mode == "in_memory"
        assert caps.async_jobs_available is True


# ---------- E2E: Full Lifecycle ----------


class TestAsyncJobE2E:
    """Full flow: enqueue → list → get → run-once → verify succeeded."""

    def test_full_lifecycle(self):
        from app.main import (
            async_job_summary as route_summary,
            create_async_job as route_create,
            get_async_job as route_get,
            list_async_jobs as route_list,
            run_async_job_once as route_run,
        )

        # 1. Enqueue
        req = AsyncJobCreateRequest(
            kind=AsyncJobKind.MUSIC_ROUTER,
            payload={"project_id": "test-e2e"},
        )
        job = asyncio.run(route_create(req, DEV_OPERATOR))
        assert job.status == AsyncJobStatus.QUEUED
        assert job.operator_id == DEV_OPERATOR.operator_id

        # 2. List — should include the job
        jobs = asyncio.run(route_list())
        assert any(j.job_id == job.job_id for j in jobs)

        # 3. Get — verify details
        retrieved = asyncio.run(route_get(job.job_id))
        assert retrieved.kind == AsyncJobKind.MUSIC_ROUTER
        assert retrieved.payload == {"project_id": "test-e2e"}

        # 4. Run once — execute synchronously
        result = asyncio.run(route_run(job.job_id, DEV_OPERATOR))
        assert result.status == AsyncJobStatus.SUCCEEDED
        assert result.result is not None
        assert result.result.data["kind"] == "music_router"
        assert result.progress.progress == 1.0

        # 5. Verify stored state
        stored = asyncio.run(route_get(job.job_id))
        assert stored.status == AsyncJobStatus.SUCCEEDED

        # 6. Summary reflects the completion
        summary = asyncio.run(route_summary())
        assert summary.succeeded >= 1

    def test_cancel_lifecycle(self):
        from app.main import (
            cancel_async_job as route_cancel,
            create_async_job as route_create,
            get_async_job as route_get,
        )

        job = asyncio.run(
            route_create(AsyncJobCreateRequest(kind=AsyncJobKind.DROPBOX_SYNC), DEV_OPERATOR)
        )
        cancelled = asyncio.run(route_cancel(job.job_id, DEV_OPERATOR))
        assert cancelled.status == AsyncJobStatus.CANCELLED

        # Verify stored
        stored = asyncio.run(route_get(job.job_id))
        assert stored.status == AsyncJobStatus.CANCELLED
