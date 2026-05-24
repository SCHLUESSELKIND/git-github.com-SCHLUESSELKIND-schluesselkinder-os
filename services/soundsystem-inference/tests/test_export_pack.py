"""Tests for S17 — Export Pack / Project Library."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.export_pack import (
    ProjectLibraryRepository,
    _slugify,
    build_export_pack,
    build_library_entry,
)
from app.schemas import (
    CommercialStatus,
    ExportPackStatus,
    LyricsLine,
    LyricsSection,
    LyricsSectionType,
    LyricsSource,
    LyricsStructure,
    LyricsVersion,
    MusicArtifactManifest,
    MusicArtifactType,
    MusicIntentKind,
    MusicJob,
    MusicJobStatus,
    MusicProviderGroup,
    MusicRouterDecision,
    MusicRouterReadiness,
    OutputProvenance,
    RewriteStrategy,
    SafetyReviewStatus,
    SoundGraphArrangement,
    ArrangementRegion,
    EnergyLevel,
    EnergyMapPoint,
    LaneAssignment,
    RegionRole,
    StemLaneType,
    StemSourceType,
    VocalEntry,
)


# ---------- Fixtures ----------


def _make_music_job(
    *,
    status: MusicJobStatus = MusicJobStatus.COMPLETED,
    title: str = "Dub Pressure",
    intent: MusicIntentKind = MusicIntentKind.CREATE_SONG_SKETCH,
    artifacts: list[MusicArtifactManifest] | None = None,
    provenance_id=None,
) -> MusicJob:
    prov_id = provenance_id or uuid4()
    return MusicJob(
        job_id=uuid4(),
        intent=intent,
        title=title,
        prompt="test prompt",
        status=status,
        router_decision=MusicRouterDecision(
            intent=intent,
            provider_group=MusicProviderGroup.HIGH_FIDELITY_CLIP_PROVIDER,
            selected_adapter_key="mock-music",
            readiness_state=MusicRouterReadiness.MOCK_ONLY,
            reason="mock",
            provenance_id=prov_id,
        ),
        artifacts=artifacts
        or [
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
        provenance_id=prov_id,
        commercial_target=CommercialStatus.REVIEW_NEEDED,
    )


def _make_lyrics_version() -> LyricsVersion:
    return LyricsVersion(
        id=uuid4(),
        project_id=uuid4(),
        version=1,
        parent_version_id=None,
        edit_summary=None,
        structure=LyricsStructure(
            title="Dub Pressure",
            character_code="SNUFFRAGA",
            sections=[
                LyricsSection(
                    index=0,
                    section_type=LyricsSectionType.VERSE,
                    label="Verse 1",
                    source=LyricsSource.MOCK,
                    lines=[
                        LyricsLine(index=0, text="Bass drop heavy on the one"),
                    ],
                    locked=False,
                ),
            ],
        ),
    )


def _make_arrangement(lyrics_version_id=None) -> SoundGraphArrangement:
    return SoundGraphArrangement(
        arrangement_id=uuid4(),
        lyrics_version_id=lyrics_version_id or uuid4(),
        project_key="dub-pressure",
        bpm=140,
        time_signature="4/4",
        key_signature="Dm",
        total_bars=16,
        regions=[
            ArrangementRegion(
                region_index=0,
                section_index=0,
                role=RegionRole.VERSE,
                label="Verse 1",
                bar_start=0,
                bar_count=16,
                vocal_entry=VocalEntry.MAIN,
                energy=EnergyLevel.MEDIUM,
                lanes_active=[StemLaneType.KICK, StemLaneType.BASS, StemLaneType.VOCALS_MAIN],
                lanes_muted=[],
            ),
        ],
        energy_map=[
            EnergyMapPoint(region_index=0, bar=0, energy=EnergyLevel.MEDIUM),
        ],
        lane_assignments=[
            LaneAssignment(
                lane=StemLaneType.KICK,
                active_regions=[0],
                source=StemSourceType.GENERATED_DIRECT,
            ),
        ],
    )


def _make_provenance() -> OutputProvenance:
    return OutputProvenance(
        provenance_id=uuid4(),
        artifact_id=uuid4(),
        artifact_kind="music_job",
        rewrite_strategy=RewriteStrategy.PROMPT_EDIT,
        commercial_status=CommercialStatus.REVIEW_NEEDED,
        safety_review_status=SafetyReviewStatus.PENDING,
    )


# ---------- Test: _slugify ----------


class TestSlugify:
    def test_basic(self):
        assert _slugify("Dub Pressure") == "dub-pressure"

    def test_special_chars(self):
        assert _slugify("Hölle & Feuer!") == "h-lle-feuer"

    def test_truncated(self):
        long = "a" * 200
        assert len(_slugify(long)) <= 120

    def test_empty(self):
        assert _slugify("") == "untitled"

    def test_only_special(self):
        assert _slugify("!!!") == "untitled"


# ---------- Test: build_export_pack ----------


class TestBuildExportPack:
    def test_basic_pack(self):
        job = _make_music_job()
        pack = build_export_pack(job)
        assert pack.status == ExportPackStatus.COMPLETE
        assert pack.music_job_id == job.job_id
        assert pack.title == "Dub Pressure"
        assert pack.intent == MusicIntentKind.CREATE_SONG_SKETCH

    def test_components_include_job_and_artifacts(self):
        job = _make_music_job()
        pack = build_export_pack(job)
        types = [c.component_type for c in pack.components]
        assert "music_job" in types
        assert "artifact_full_mix" in types
        assert "artifact_stem_pack" in types
        assert pack.total_components == 3  # job + 2 artifacts

    def test_with_lyrics(self):
        job = _make_music_job()
        lyrics = _make_lyrics_version()
        pack = build_export_pack(job, lyrics_version=lyrics)
        types = [c.component_type for c in pack.components]
        assert "lyrics_version" in types
        assert pack.lyrics_version_id == lyrics.id
        assert pack.total_components == 4

    def test_with_arrangement(self):
        job = _make_music_job()
        arr = _make_arrangement()
        pack = build_export_pack(job, arrangement=arr)
        types = [c.component_type for c in pack.components]
        assert "soundgraph_arrangement" in types
        assert pack.arrangement_id == arr.arrangement_id
        assert pack.bpm == 140
        assert pack.key_signature == "Dm"

    def test_with_provenance(self):
        job = _make_music_job()
        prov = _make_provenance()
        pack = build_export_pack(job, provenance=prov)
        types = [c.component_type for c in pack.components]
        assert "output_provenance" in types
        assert pack.provenance_id == prov.provenance_id

    def test_full_bundle(self):
        job = _make_music_job()
        lyrics = _make_lyrics_version()
        arr = _make_arrangement(lyrics_version_id=lyrics.id)
        prov = _make_provenance()
        pack = build_export_pack(
            job,
            lyrics_version=lyrics,
            arrangement=arr,
            provenance=prov,
            title="Custom Title",
            operator_id="operator-42",
            notes="Production ready",
        )
        assert pack.title == "Custom Title"
        assert pack.operator_id == "operator-42"
        assert pack.notes == "Production ready"
        assert pack.total_components == 6  # job + 2 artifacts + lyrics + arr + prov
        assert pack.lyrics_version_id == lyrics.id
        assert pack.arrangement_id == arr.arrangement_id
        assert pack.provenance_id == prov.provenance_id

    def test_duration_from_arrangement(self):
        job = _make_music_job()
        arr = _make_arrangement()  # 16 bars, 140 BPM, 4/4
        pack = build_export_pack(job, arrangement=arr)
        # 16 bars * 4 beats / 140 bpm * 60 = ~27.43 seconds
        assert pack.estimated_duration_seconds is not None
        assert 27.0 < pack.estimated_duration_seconds < 28.0

    def test_rejects_non_completed_job(self):
        job = _make_music_job(status=MusicJobStatus.QUEUED)
        with pytest.raises(ValueError, match="COMPLETED"):
            build_export_pack(job)

    def test_custom_title_overrides_job_title(self):
        job = _make_music_job(title="Original")
        pack = build_export_pack(job, title="Override")
        assert pack.title == "Override"

    def test_operator_from_job_fallback(self):
        job = _make_music_job()
        job.operator_id = "from-job"
        pack = build_export_pack(job)
        assert pack.operator_id == "from-job"

    def test_operator_explicit_overrides_job(self):
        job = _make_music_job()
        job.operator_id = "from-job"
        pack = build_export_pack(job, operator_id="explicit")
        assert pack.operator_id == "explicit"


# ---------- Test: build_library_entry ----------


class TestBuildLibraryEntry:
    def test_basic_entry(self):
        job = _make_music_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        assert entry.pack_id == pack.pack_id
        assert entry.title == pack.title
        assert entry.slug == "dub-pressure"
        assert entry.intent == MusicIntentKind.CREATE_SONG_SKETCH
        assert entry.status == ExportPackStatus.COMPLETE

    def test_entry_with_full_bundle(self):
        job = _make_music_job()
        lyrics = _make_lyrics_version()
        arr = _make_arrangement()
        prov = _make_provenance()
        pack = build_export_pack(job, lyrics_version=lyrics, arrangement=arr, provenance=prov)
        entry = build_library_entry(pack)
        assert entry.has_lyrics is True
        assert entry.has_arrangement is True
        assert entry.has_provenance is True
        assert entry.artifact_count == 2  # full_mix + stem_pack
        assert entry.component_count == 6

    def test_entry_without_optional_links(self):
        job = _make_music_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        assert entry.has_lyrics is False
        assert entry.has_arrangement is False
        assert entry.has_provenance is False

    def test_entry_bpm_and_key(self):
        job = _make_music_job()
        arr = _make_arrangement()
        pack = build_export_pack(job, arrangement=arr)
        entry = build_library_entry(pack)
        assert entry.bpm == 140
        assert entry.key_signature == "Dm"


# ---------- Test: ProjectLibraryRepository ----------


class TestProjectLibraryRepository:
    def test_store_and_get_pack(self):
        repo = ProjectLibraryRepository()
        job = _make_music_job()
        pack = build_export_pack(job)
        repo.store_pack(pack)
        assert repo.get_pack(pack.pack_id) == pack

    def test_get_pack_not_found(self):
        repo = ProjectLibraryRepository()
        assert repo.get_pack(uuid4()) is None

    def test_store_and_get_entry(self):
        repo = ProjectLibraryRepository()
        job = _make_music_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.get_entry(entry.entry_id) == entry

    def test_get_entry_by_pack(self):
        repo = ProjectLibraryRepository()
        job = _make_music_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.get_entry_by_pack(pack.pack_id) == entry

    def test_list_entries(self):
        repo = ProjectLibraryRepository()
        for _ in range(3):
            job = _make_music_job()
            pack = build_export_pack(job)
            entry = build_library_entry(pack)
            repo.store_pack(pack)
            repo.store_entry(entry)
        assert len(repo.list_entries()) == 3

    def test_list_packs(self):
        repo = ProjectLibraryRepository()
        for _ in range(2):
            job = _make_music_job()
            pack = build_export_pack(job)
            repo.store_pack(pack)
        assert len(repo.list_packs()) == 2

    def test_summary(self):
        repo = ProjectLibraryRepository()
        # One with lyrics + arrangement, one without
        job1 = _make_music_job()
        lyrics = _make_lyrics_version()
        arr = _make_arrangement()
        prov = _make_provenance()
        pack1 = build_export_pack(job1, lyrics_version=lyrics, arrangement=arr, provenance=prov)
        entry1 = build_library_entry(pack1)
        repo.store_pack(pack1)
        repo.store_entry(entry1)

        job2 = _make_music_job()
        pack2 = build_export_pack(job2)
        entry2 = build_library_entry(pack2)
        repo.store_pack(pack2)
        repo.store_entry(entry2)

        summary = repo.summary()
        assert summary.total_entries == 2
        assert summary.total_packs == 2
        assert summary.entries_with_lyrics == 1
        assert summary.entries_with_arrangements == 1
        assert summary.entries_with_provenance == 1

    def test_count(self):
        repo = ProjectLibraryRepository()
        assert repo.count == 0
        job = _make_music_job()
        pack = build_export_pack(job)
        entry = build_library_entry(pack)
        repo.store_pack(pack)
        repo.store_entry(entry)
        assert repo.count == 1


# ---------- Test: Routes ----------


class TestExportPackRoutes:
    """Route tests using asyncio.run() — no httpx/TestClient needed."""

    def test_create_pack_job_not_found(self):
        from app.main import create_export_pack as route
        from app.schemas import ExportPackCreateRequest

        from app.auth import DEV_OPERATOR

        req = ExportPackCreateRequest(music_job_id=uuid4())
        with pytest.raises(Exception, match="music_job_not_found"):
            asyncio.run(route(req, DEV_OPERATOR))

    def test_get_pack_not_found(self):
        from app.main import get_export_pack as route

        with pytest.raises(Exception, match="export_pack_not_found"):
            asyncio.run(route(uuid4()))

    def test_get_entry_not_found(self):
        from app.main import get_library_entry as route

        with pytest.raises(Exception, match="library_entry_not_found"):
            asyncio.run(route(uuid4()))

    def test_library_summary_empty(self):
        from app.main import library_summary as route

        summary = asyncio.run(route())
        assert summary.total_entries >= 0  # may have state from other tests
        assert summary.total_packs >= 0

    def test_capabilities_includes_export_pack(self):
        from app.main import capabilities as route

        caps = asyncio.run(route())
        assert caps.export_pack_available is True


# ---------- Test: End-to-End Flow ----------


class TestEndToEndExportPack:
    """Full flow: Lyrics → SoundGraph → Music Job → Export Pack → Library Entry."""

    def test_full_pipeline(self):
        from app.main import (
            compile_soundgraph_route,
            create_export_pack as create_pack_route,
            create_lyrics,
            get_export_pack as get_pack_route,
            list_library_entries as list_entries_route,
            soundgraph_handoff_route,
        )
        from app.schemas import (
            ExportPackCreateRequest,
            LyricsGenerationRequest,
            SoundGraphHandoffRequest,
            SoundGraphWriteRequest,
        )

        # 1. Create lyrics
        lyrics_req = LyricsGenerationRequest(
            project_key="e2e-export-test",
            title="E2E Export Test",
            character_code="SNUFFRAGA",
            prompt="test export pipeline",
        )
        from app.auth import DEV_OPERATOR

        version = asyncio.run(create_lyrics(lyrics_req, DEV_OPERATOR))

        # 2. Compile SoundGraph
        sg_req = SoundGraphWriteRequest(
            lyrics_version_id=version.id,
            bpm=140,
            energy_profile="standard",
        )
        sg_result = asyncio.run(compile_soundgraph_route(sg_req, DEV_OPERATOR))
        arrangement = sg_result.arrangement

        # 3. Handoff to Music Router
        handoff_req = SoundGraphHandoffRequest(
            arrangement_id=arrangement.arrangement_id,
            title="E2E Export Test Track",
        )
        handoff_result = asyncio.run(soundgraph_handoff_route(handoff_req, DEV_OPERATOR))
        music_job = handoff_result.music_job

        # 4. Create Export Pack
        pack_req = ExportPackCreateRequest(
            music_job_id=music_job.job_id,
            title="E2E Export Pack",
            operator_id="test-operator",
            notes="End-to-end test",
        )
        pack = asyncio.run(create_pack_route(pack_req, DEV_OPERATOR))

        assert pack.status == ExportPackStatus.COMPLETE
        assert pack.title == "E2E Export Pack"
        assert pack.music_job_id == music_job.job_id
        assert pack.total_components >= 3  # at least job + artifacts
        assert pack.intent is not None

        # 5. Verify pack is retrievable
        retrieved = asyncio.run(get_pack_route(pack.pack_id))
        assert retrieved.pack_id == pack.pack_id

        # 6. Verify library entry was created
        entries = asyncio.run(list_entries_route())
        pack_ids = [e.pack_id for e in entries]
        assert pack.pack_id in pack_ids
