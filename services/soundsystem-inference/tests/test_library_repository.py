"""Tests for S19 — Persistent Project Library repository layer."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.auth import DEV_OPERATOR
from app.config import (
    LIBRARY_REPOSITORY_ENV,
    LibraryRepositoryMode,
    library_repository_mode,
)
from app.export_pack import (
    ProjectLibraryRepository,
    build_export_pack,
    build_library_entry,
)
from app.library_repository import (
    InMemoryLibraryRepository,
    LibraryRepositoryConfigError,
    build_library_repository,
)
from app.schemas import (
    ExportPackStatus,
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


def _make_completed_job() -> MusicJob:
    return MusicJob(
        job_id=uuid4(),
        intent=MusicIntentKind.CREATE_SONG_SKETCH,
        title="Repo Test Track",
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
                path="/tmp/test.wav",
                duration_seconds=60.0,
            ),
        ],
        provenance_id=uuid4(),
    )


# ---------- Test: Config ----------


class TestLibraryConfig:
    def test_default_mode_is_in_memory(self, monkeypatch):
        monkeypatch.delenv(LIBRARY_REPOSITORY_ENV, raising=False)
        assert library_repository_mode() == LibraryRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch):
        monkeypatch.setenv(LIBRARY_REPOSITORY_ENV, "in_memory")
        assert library_repository_mode() == LibraryRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch):
        monkeypatch.setenv(LIBRARY_REPOSITORY_ENV, "postgres")
        assert library_repository_mode() == LibraryRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch):
        monkeypatch.setenv(LIBRARY_REPOSITORY_ENV, "sqlite")
        with pytest.raises(RuntimeError, match="invalid"):
            library_repository_mode()

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(LIBRARY_REPOSITORY_ENV, "POSTGRES")
        assert library_repository_mode() == LibraryRepositoryMode.POSTGRES


# ---------- Test: Factory ----------


class TestBuildLibraryRepository:
    def test_default_returns_in_memory(self, monkeypatch):
        monkeypatch.delenv(LIBRARY_REPOSITORY_ENV, raising=False)
        repo = build_library_repository()
        assert isinstance(repo, InMemoryLibraryRepository)
        assert repo.mode == "in_memory"

    def test_postgres_without_url_raises(self, monkeypatch):
        monkeypatch.setenv(LIBRARY_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(LibraryRepositoryConfigError, match="DATABASE_URL"):
            build_library_repository()


# ---------- Test: InMemoryLibraryRepository (Protocol conformance) ----------


class TestInMemoryLibraryRepository:
    def test_store_and_get_pack(self):
        repo = InMemoryLibraryRepository()
        job = _make_completed_job()
        pack = build_export_pack(job)
        repo.store_pack(pack)
        assert repo.get_pack(pack.pack_id) == pack

    def test_get_pack_not_found(self):
        repo = InMemoryLibraryRepository()
        assert repo.get_pack(uuid4()) is None

    def test_list_packs(self):
        repo = InMemoryLibraryRepository()
        for _ in range(3):
            pack = build_export_pack(_make_completed_job())
            repo.store_pack(pack)
        assert len(repo.list_packs()) == 3

    def test_store_and_get_entry(self):
        repo = InMemoryLibraryRepository()
        job = _make_completed_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.get_entry(entry.entry_id) == entry

    def test_get_entry_by_pack(self):
        repo = InMemoryLibraryRepository()
        pack = build_export_pack(_make_completed_job())
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.get_entry_by_pack(pack.pack_id) == entry

    def test_list_entries(self):
        repo = InMemoryLibraryRepository()
        for _ in range(2):
            pack = build_export_pack(_make_completed_job())
            entry = build_library_entry(pack)
            repo.store_pack(pack)
            repo.store_entry(entry)
        assert len(repo.list_entries()) == 2

    def test_summary(self):
        repo = InMemoryLibraryRepository()
        pack = build_export_pack(_make_completed_job())
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        summary = repo.summary()
        assert summary.total_entries == 1
        assert summary.total_packs == 1

    def test_count(self):
        repo = InMemoryLibraryRepository()
        assert repo.count == 0
        pack = build_export_pack(_make_completed_job())
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.count == 1

    def test_mode_property(self):
        repo = InMemoryLibraryRepository()
        assert repo.mode == "in_memory"


# ---------- Test: Backwards-compat alias ----------


class TestBackwardsCompatAlias:
    """ProjectLibraryRepository from export_pack.py should still work."""

    def test_alias_is_in_memory(self):
        repo = ProjectLibraryRepository()
        assert repo.mode == "in_memory"

    def test_alias_store_and_get(self):
        repo = ProjectLibraryRepository()
        pack = build_export_pack(_make_completed_job())
        repo.store_pack(pack)
        assert repo.get_pack(pack.pack_id) is not None


# ---------- Test: Routes with repository ----------


class TestLibraryRoutes:
    def test_capabilities_reports_library_mode(self):
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.library_repository_mode == "in_memory"

    def test_summary_route(self):
        from app.main import library_summary

        summary = asyncio.run(library_summary())
        assert summary.total_entries >= 0
        assert summary.total_packs >= 0

    def test_create_pack_end_to_end(self):
        """Full flow through new repository layer."""
        from app.main import (
            compile_soundgraph_route,
            create_export_pack as create_pack_route,
            create_lyrics,
            list_library_entries as list_entries_route,
            soundgraph_handoff_route,
        )
        from app.schemas import (
            ExportPackCreateRequest,
            LyricsGenerationRequest,
            SoundGraphHandoffRequest,
            SoundGraphWriteRequest,
        )

        # Create lyrics → soundgraph → handoff → export pack
        version = asyncio.run(
            create_lyrics(
                LyricsGenerationRequest(
                    project_key="s19-repo-test",
                    title="S19 Repo Test",
                    character_code="SNUFFRAGA",
                    prompt="test persistent library",
                ),
                DEV_OPERATOR,
            )
        )
        sg = asyncio.run(
            compile_soundgraph_route(
                SoundGraphWriteRequest(lyrics_version_id=version.id, bpm=130),
                DEV_OPERATOR,
            )
        )
        handoff = asyncio.run(
            soundgraph_handoff_route(
                SoundGraphHandoffRequest(
                    arrangement_id=sg.arrangement.arrangement_id,
                    title="S19 Test",
                ),
                DEV_OPERATOR,
            )
        )
        pack = asyncio.run(
            create_pack_route(
                ExportPackCreateRequest(
                    music_job_id=handoff.music_job.job_id,
                    title="S19 Repo Pack",
                ),
                DEV_OPERATOR,
            )
        )

        assert pack.status == ExportPackStatus.COMPLETE
        assert pack.title == "S19 Repo Pack"

        # Verify it shows in the list
        entries = asyncio.run(list_entries_route())
        pack_ids = [e.pack_id for e in entries]
        assert pack.pack_id in pack_ids
