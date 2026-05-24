"""Tests for S20 — Dropbox Export Sync."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.dropbox_sync import (
    DEFAULT_DROPBOX_ROOT,
    DropboxSyncRepository,
    _sanitize_folder_name,
    build_export_plan,
    create_sync_job,
    mark_ready_for_sync,
    mock_execute_sync,
)
from app.export_pack import build_export_pack
from app.schemas import (
    DropboxSyncStatus,
    MusicArtifactManifest,
    MusicArtifactType,
    MusicIntentKind,
    MusicJob,
    MusicJobStatus,
    MusicProviderGroup,
    MusicRouterDecision,
    MusicRouterReadiness,
)


# ---------- Fixtures ----------


def _make_completed_job(title: str = "Dub Pressure") -> MusicJob:
    return MusicJob(
        job_id=uuid4(),
        intent=MusicIntentKind.CREATE_SONG_SKETCH,
        title=title,
        prompt="test",
        status=MusicJobStatus.COMPLETED,
        router_decision=MusicRouterDecision(
            intent=MusicIntentKind.CREATE_SONG_SKETCH,
            provider_group=MusicProviderGroup.HIGH_FIDELITY_CLIP_PROVIDER,
            selected_adapter_key="mock",
            readiness_state=MusicRouterReadiness.MOCK_ONLY,
            reason="mock",
        ),
        artifacts=[
            MusicArtifactManifest(
                artifact_type=MusicArtifactType.FULL_MIX,
                path="/tmp/snuffraga/mock/full_mix.wav",
                duration_seconds=180.0,
            ),
            MusicArtifactManifest(
                artifact_type=MusicArtifactType.STEM_PACK,
                path="/tmp/snuffraga/mock/stems/",
            ),
        ],
        provenance_id=uuid4(),
    )


def _make_pack(title: str = "Dub Pressure"):
    job = _make_completed_job(title=title)
    return build_export_pack(job)


# ---------- Test: _sanitize_folder_name ----------


class TestSanitizeFolderName:
    def test_basic(self):
        assert _sanitize_folder_name("Dub Pressure") == "Dub Pressure"

    def test_slashes(self):
        assert _sanitize_folder_name("A/B\\C") == "A-B-C"

    def test_special_chars(self):
        assert _sanitize_folder_name('Test: "file"') == "Test- -file"

    def test_truncated(self):
        long = "x" * 200
        assert len(_sanitize_folder_name(long)) <= 100

    def test_empty(self):
        assert _sanitize_folder_name("") == "untitled"


# ---------- Test: build_export_plan ----------


class TestBuildExportPlan:
    def test_basic_plan(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        assert plan.pack_id == pack.pack_id
        assert plan.pack_title == pack.title
        assert plan.target_root == f"{DEFAULT_DROPBOX_ROOT}/Dub Pressure"

    def test_entries_include_manifest(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        types = [e.source_component_type for e in plan.entries]
        assert "pack_manifest" in types

    def test_entries_include_all_components(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        # pack has 3 components (job + 2 artifacts), plan adds manifest = 4
        assert len(plan.entries) == pack.total_components + 1

    def test_total_files_count(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        assert plan.total_files > 0
        assert plan.total_files + plan.total_directories == len(plan.entries)

    def test_custom_target_root(self):
        pack = _make_pack()
        plan = build_export_plan(pack, target_root_override="/Custom/Path")
        assert plan.target_root == "/Custom/Path/Dub Pressure"

    def test_deterministic(self):
        pack = _make_pack()
        plan1 = build_export_plan(pack)
        plan2 = build_export_plan(pack)
        # Same entries (different plan_id is OK)
        paths1 = [e.relative_path for e in plan1.entries]
        paths2 = [e.relative_path for e in plan2.entries]
        assert paths1 == paths2

    def test_stem_pack_is_directory(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        stem_entries = [e for e in plan.entries if "stem" in e.source_component_type]
        assert any(e.is_directory for e in stem_entries)

    def test_size_hints_present(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        hints = [e.size_hint for e in plan.entries if e.size_hint is not None]
        assert len(hints) > 0


# ---------- Test: Sync Job Lifecycle ----------


class TestSyncJobLifecycle:
    def test_create_sync_job(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        assert job.status == DropboxSyncStatus.PLANNED
        assert job.pack_id == pack.pack_id
        assert job.plan_id == plan.plan_id
        assert job.files_planned == plan.total_files
        assert job.files_synced == 0

    def test_mark_ready(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        ready = mark_ready_for_sync(job)
        assert ready.status == DropboxSyncStatus.READY_FOR_SYNC
        assert ready.sync_id == job.sync_id

    def test_mock_execute_success(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        ready = mark_ready_for_sync(job)
        synced = mock_execute_sync(ready)
        assert synced.status == DropboxSyncStatus.SYNCED
        assert synced.files_synced == synced.files_planned

    def test_mock_execute_from_wrong_status_fails(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)  # Still PLANNED, not READY
        result = mock_execute_sync(job)
        assert result.status == DropboxSyncStatus.FAILED
        assert result.error is not None

    def test_operator_id_propagated(self):
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan, operator_id="op-42")
        assert job.operator_id == "op-42"


# ---------- Test: DropboxSyncRepository ----------


class TestDropboxSyncRepository:
    def test_store_and_get_plan(self):
        repo = DropboxSyncRepository()
        pack = _make_pack()
        plan = build_export_plan(pack)
        repo.store_plan(plan)
        assert repo.get_plan(plan.plan_id) == plan

    def test_get_plan_by_pack(self):
        repo = DropboxSyncRepository()
        pack = _make_pack()
        plan = build_export_plan(pack)
        repo.store_plan(plan)
        assert repo.get_plan_by_pack(pack.pack_id) == plan

    def test_plan_not_found(self):
        repo = DropboxSyncRepository()
        assert repo.get_plan(uuid4()) is None

    def test_store_and_get_job(self):
        repo = DropboxSyncRepository()
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        repo.store_plan(plan)
        repo.store_job(job)
        assert repo.get_job(job.sync_id) == job

    def test_get_job_by_pack(self):
        repo = DropboxSyncRepository()
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        repo.store_plan(plan)
        repo.store_job(job)
        assert repo.get_job_by_pack(pack.pack_id) == job

    def test_update_job(self):
        repo = DropboxSyncRepository()
        pack = _make_pack()
        plan = build_export_plan(pack)
        job = create_sync_job(plan)
        repo.store_job(job)
        ready = mark_ready_for_sync(job)
        repo.update_job(ready)
        assert repo.get_job(job.sync_id).status == DropboxSyncStatus.READY_FOR_SYNC

    def test_list_jobs(self):
        repo = DropboxSyncRepository()
        for _ in range(3):
            pack = _make_pack()
            plan = build_export_plan(pack)
            job = create_sync_job(plan)
            repo.store_plan(plan)
            repo.store_job(job)
        assert len(repo.list_jobs()) == 3

    def test_summary(self):
        repo = DropboxSyncRepository()
        # One planned, one synced
        pack1 = _make_pack("Pack A")
        plan1 = build_export_plan(pack1)
        job1 = create_sync_job(plan1)
        repo.store_plan(plan1)
        repo.store_job(job1)

        pack2 = _make_pack("Pack B")
        plan2 = build_export_plan(pack2)
        job2 = create_sync_job(plan2)
        job2_ready = mark_ready_for_sync(job2)
        job2_synced = mock_execute_sync(job2_ready)
        repo.store_plan(plan2)
        repo.store_job(job2_synced)

        summary = repo.summary()
        assert summary.total_plans == 2
        assert summary.total_sync_jobs == 2
        assert summary.jobs_planned == 1
        assert summary.jobs_synced == 1


# ---------- Test: Routes ----------


class TestDropboxRoutes:
    def test_create_plan_pack_not_found(self):
        from app.main import create_dropbox_export_plan as route
        from app.schemas import DropboxExportPlanCreateRequest

        from app.auth import DEV_OPERATOR

        req = DropboxExportPlanCreateRequest(pack_id=uuid4())
        with pytest.raises(Exception, match="export_pack_not_found"):
            asyncio.run(route(req, DEV_OPERATOR))

    def test_get_plan_not_found(self):
        from app.main import get_dropbox_plan as route

        with pytest.raises(Exception, match="dropbox_plan_not_found"):
            asyncio.run(route(uuid4()))

    def test_get_job_not_found(self):
        from app.main import get_dropbox_job as route

        with pytest.raises(Exception, match="dropbox_sync_job_not_found"):
            asyncio.run(route(uuid4()))

    def test_capabilities_includes_dropbox_sync(self):
        from app.main import capabilities as route

        caps = asyncio.run(route())
        assert caps.dropbox_sync_available is True

    def test_summary_route(self):
        from app.main import dropbox_sync_summary as route

        summary = asyncio.run(route())
        assert summary.total_plans >= 0


# ---------- Test: End-to-End ----------


class TestEndToEndDropboxSync:
    """Full flow: Lyrics → SoundGraph → Music Job → Export Pack → Dropbox Plan → Sync."""

    def test_full_pipeline(self):
        from app.main import (
            compile_soundgraph_route,
            create_dropbox_export_plan as create_plan_route,
            create_export_pack as create_pack_route,
            create_lyrics,
            execute_dropbox_sync as execute_route,
            mark_dropbox_job_ready as ready_route,
            soundgraph_handoff_route,
        )
        from app.schemas import (
            DropboxExportPlanCreateRequest,
            ExportPackCreateRequest,
            LyricsGenerationRequest,
            SoundGraphHandoffRequest,
            SoundGraphWriteRequest,
        )

        from app.auth import DEV_OPERATOR

        # 1. Full flow to get a pack
        version = asyncio.run(
            create_lyrics(
                LyricsGenerationRequest(
                    project_key="s20-dropbox-test",
                    title="Dropbox Test",
                    character_code="SNUFFRAGA",
                    prompt="test dropbox sync",
                ),
                DEV_OPERATOR,
            )
        )
        sg = asyncio.run(
            compile_soundgraph_route(
                SoundGraphWriteRequest(lyrics_version_id=version.id, bpm=138),
                DEV_OPERATOR,
            )
        )
        handoff = asyncio.run(
            soundgraph_handoff_route(
                SoundGraphHandoffRequest(
                    arrangement_id=sg.arrangement.arrangement_id,
                    title="Dropbox Test Track",
                ),
                DEV_OPERATOR,
            )
        )
        pack = asyncio.run(
            create_pack_route(
                ExportPackCreateRequest(
                    music_job_id=handoff.music_job.job_id,
                    title="Dropbox Sync Test Pack",
                ),
                DEV_OPERATOR,
            )
        )

        # 2. Create Dropbox export plan
        plan = asyncio.run(
            create_plan_route(DropboxExportPlanCreateRequest(pack_id=pack.pack_id), DEV_OPERATOR)
        )
        assert plan.pack_id == pack.pack_id
        assert plan.total_files > 0
        assert "Dropbox Sync Test Pack" in plan.target_root

        # 3. Find the auto-created sync job
        from app.main import dropbox_sync_repository

        job = dropbox_sync_repository.get_job_by_pack(pack.pack_id)
        assert job is not None
        assert job.status == DropboxSyncStatus.PLANNED

        # 4. Mark ready
        ready = asyncio.run(ready_route(job.sync_id, DEV_OPERATOR))
        assert ready.status == DropboxSyncStatus.READY_FOR_SYNC

        # 5. Execute (mock)
        synced = asyncio.run(execute_route(job.sync_id, DEV_OPERATOR))
        assert synced.status == DropboxSyncStatus.SYNCED
        assert synced.files_synced == synced.files_planned
