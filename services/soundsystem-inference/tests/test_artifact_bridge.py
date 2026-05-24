"""Tests for S28 — Artifact Integration Pass (artifact_bridge).

Covers:
- Bridge helpers: export pack, soundgraph, music job, release pack
- JSON manifests stored as real bytes
- No fake audio stored (audio artifacts stay PLANNED)
- Component-type-to-kind mapping
- Content-type inference
- Integration with route handlers (music-router, soundgraph, library, releases)
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from app.artifact_bridge import (
    _component_type_to_kind,
    _content_type_for_component,
    _content_type_for_format,
    _content_type_for_path,
    _music_artifact_type_to_kind,
    _release_asset_to_kind,
    record_artifact_for_soundgraph,
    record_artifacts_for_export_pack,
    record_artifacts_for_music_job,
    record_artifacts_for_release_pack,
)
from app.artifact_storage import LocalArtifactStorage
from app.auth import DEV_OPERATOR
from app.schemas import (
    ArtifactKind,
    ArtifactStatus,
    ComplianceChecklistItem,
    ExportPack,
    ExportPackComponent,
    ExportPackStatus,
    MusicArtifactManifest,
    MusicArtifactType,
    MusicIntentKind,
    MusicJob,
    MusicJobStatus,
    MusicProviderGroup,
    MusicRouterDecision,
    MusicRouterReadiness,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    SoundGraphArrangement,
)


# ---------- Fixtures ----------


def _make_storage() -> LocalArtifactStorage:
    """Create a fresh LocalArtifactStorage in a temp directory."""
    tmpdir = tempfile.mkdtemp()
    return LocalArtifactStorage(root=tmpdir)


def _make_music_job(*, status: MusicJobStatus = MusicJobStatus.COMPLETED) -> MusicJob:
    """Create a minimal completed MusicJob for testing."""
    job_id = uuid4()
    return MusicJob(
        job_id=job_id,
        intent=MusicIntentKind.CREATE_LOOP,
        title="Test Loop",
        prompt="dark warehouse loop 130 bpm",
        status=status,
        router_decision=MusicRouterDecision(
            intent=MusicIntentKind.CREATE_LOOP,
            provider_group=MusicProviderGroup.MUSIC_LOOP_PROVIDER,
            selected_adapter_key="mock_loop_v1",
            readiness_state=MusicRouterReadiness.MOCK_ONLY,
            reason="test routing",
        ),
        artifacts=[
            MusicArtifactManifest(
                artifact_type=MusicArtifactType.LOOP,
                path=f"artifacts/music-router/create_loop/{job_id}.wav",
                duration_seconds=30.0,
                format="wav",
            ),
            MusicArtifactManifest(
                artifact_type=MusicArtifactType.PROMPT_MANIFEST,
                path=f"artifacts/music-router/create_loop/{job_id}.prompt.json",
            ),
        ],
        provenance_id=uuid4(),
        operator_id="test@test.com",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_arrangement() -> SoundGraphArrangement:
    """Create a minimal SoundGraphArrangement for testing."""
    return SoundGraphArrangement(
        arrangement_id=uuid4(),
        lyrics_version_id=uuid4(),
        project_key="test12345678",
        bpm=130,
        time_signature="4/4",
        key_signature="Dm",
        total_bars=64,
        regions=[],
        energy_map=[],
        lane_assignments=[],
    )


def _make_export_pack() -> ExportPack:
    """Create a minimal ExportPack with components for testing."""
    pack_id = uuid4()
    job_id = uuid4()
    return ExportPack(
        pack_id=pack_id,
        title="Test Pack",
        status=ExportPackStatus.COMPLETE,
        music_job_id=job_id,
        components=[
            ExportPackComponent(
                component_type="music_job",
                component_id=job_id,
                label="Music Job: Test",
                path="/tmp/snuffraga/export/test-pack/music_job.json",
            ),
            ExportPackComponent(
                component_type="artifact_loop",
                component_id=job_id,
                label="Artifact: loop (wav)",
                path=f"artifacts/music-router/create_loop/{job_id}.wav",
            ),
            ExportPackComponent(
                component_type="artifact_prompt_manifest",
                component_id=job_id,
                label="Artifact: prompt_manifest (json)",
                path=f"artifacts/music-router/create_loop/{job_id}.prompt.json",
            ),
        ],
        total_components=3,
        intent=MusicIntentKind.CREATE_LOOP,
        operator_id="test@test.com",
    )


def _make_release_pack() -> ReleasePack:
    """Create a minimal ReleasePack for testing."""
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="Test Release",
        artist="Test Artist",
        status=ReleasePackStatus.DRAFT,
        description="Test release description",
        social_copy=SocialCopy(
            soundcloud_description="Test on SC",
            tiktok_caption="Test on TikTok",
            instagram_caption="Test on IG",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="license_clear",
                label="All licenses cleared",
                passed=False,
            ),
        ],
        compliance_passed=False,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master (WAV)",
                expected_format="wav",
                ready=False,
            ),
        ],
        dropbox_target="/SNUFFRAGA/Releases/Test-Release",
    )


# ============================================================
# Component-type mapping tests
# ============================================================


class TestComponentTypeMapping:
    def test_music_job_maps_to_music_job_kind(self) -> None:
        assert _component_type_to_kind("music_job") == ArtifactKind.MUSIC_JOB

    def test_lyrics_version_maps_to_lyrics_kind(self) -> None:
        assert _component_type_to_kind("lyrics_version") == ArtifactKind.LYRICS

    def test_soundgraph_arrangement_maps_to_soundgraph_kind(self) -> None:
        assert _component_type_to_kind("soundgraph_arrangement") == ArtifactKind.SOUNDGRAPH

    def test_output_provenance_maps_to_provenance_kind(self) -> None:
        assert _component_type_to_kind("output_provenance") == ArtifactKind.PROVENANCE

    def test_artifact_loop_maps_to_audio_mix(self) -> None:
        assert _component_type_to_kind("artifact_loop") == ArtifactKind.AUDIO_MIX

    def test_artifact_full_mix_maps_to_audio_mix(self) -> None:
        assert _component_type_to_kind("artifact_full_mix") == ArtifactKind.AUDIO_MIX

    def test_artifact_stem_pack_maps_to_stem_pack(self) -> None:
        assert _component_type_to_kind("artifact_stem_pack") == ArtifactKind.STEM_PACK

    def test_artifact_prompt_manifest_maps_to_manifest(self) -> None:
        assert _component_type_to_kind("artifact_prompt_manifest") == ArtifactKind.MANIFEST

    def test_unknown_type_maps_to_other(self) -> None:
        assert _component_type_to_kind("unknown_thing") == ArtifactKind.OTHER

    def test_artifact_unknown_subtype_maps_to_other(self) -> None:
        assert _component_type_to_kind("artifact_unknown") == ArtifactKind.OTHER


class TestMusicArtifactTypeMapping:
    def test_loop(self) -> None:
        assert _music_artifact_type_to_kind("loop") == ArtifactKind.AUDIO_MIX

    def test_stem_pack(self) -> None:
        assert _music_artifact_type_to_kind("stem_pack") == ArtifactKind.STEM_PACK

    def test_prompt_manifest(self) -> None:
        assert _music_artifact_type_to_kind("prompt_manifest") == ArtifactKind.MANIFEST

    def test_unknown(self) -> None:
        assert _music_artifact_type_to_kind("alien_format") == ArtifactKind.OTHER


class TestReleaseAssetMapping:
    def test_cover_art(self) -> None:
        assert _release_asset_to_kind("cover_art") == ArtifactKind.COVER_ART

    def test_audio_master(self) -> None:
        assert _release_asset_to_kind("audio_master") == ArtifactKind.AUDIO_MIX

    def test_stems_archive(self) -> None:
        assert _release_asset_to_kind("stems_archive") == ArtifactKind.STEM_PACK

    def test_unknown(self) -> None:
        assert _release_asset_to_kind("unknown") == ArtifactKind.OTHER


# ============================================================
# Content-type inference tests
# ============================================================


class TestContentTypeInference:
    def test_component_music_job_is_json(self) -> None:
        assert _content_type_for_component("music_job") == "application/json"

    def test_component_artifact_loop_is_wav(self) -> None:
        assert _content_type_for_component("artifact_loop") == "audio/wav"

    def test_component_artifact_prompt_manifest_is_json(self) -> None:
        assert _content_type_for_component("artifact_prompt_manifest") == "application/json"

    def test_component_unknown_is_octet_stream(self) -> None:
        assert _content_type_for_component("some_other") == "application/octet-stream"

    def test_path_wav(self) -> None:
        assert _content_type_for_path("foo/bar.wav") == "audio/wav"

    def test_path_json(self) -> None:
        assert _content_type_for_path("foo/bar.json") == "application/json"

    def test_path_mp3(self) -> None:
        assert _content_type_for_path("foo/bar.mp3") == "audio/mpeg"

    def test_path_unknown(self) -> None:
        assert _content_type_for_path("foo/bar.xyz") == "application/octet-stream"

    def test_format_png(self) -> None:
        assert _content_type_for_format("png") == "image/png"

    def test_format_zip(self) -> None:
        assert _content_type_for_format("zip") == "application/zip"

    def test_format_unknown(self) -> None:
        assert _content_type_for_format("abc") == "application/octet-stream"


# ============================================================
# Bridge helper: ExportPack
# ============================================================


class TestRecordArtifactsForExportPack:
    def test_creates_records_for_all_components_plus_manifest(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage, operator_id="op@test.com")
        # 3 components + 1 manifest = 4
        assert len(records) == 4

    def test_manifest_is_stored_with_real_bytes(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        manifest_records = [r for r in records if r.kind == ArtifactKind.MANIFEST]
        # At least the pack-level manifest
        stored_manifests = [r for r in manifest_records if r.status == ArtifactStatus.STORED]
        assert len(stored_manifests) >= 1

    def test_manifest_bytes_are_valid_json(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        stored = [r for r in records if r.status == ArtifactStatus.STORED]
        assert len(stored) >= 1
        for rec in stored:
            file_path = storage.get_file_path(rec.artifact_id)
            assert file_path is not None
            data = file_path.read_bytes()
            parsed = json.loads(data)
            assert isinstance(parsed, dict)

    def test_component_records_are_planned(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        # First 3 are component records (PLANNED), last is manifest (STORED)
        component_records = records[:3]
        for rec in component_records:
            assert rec.status == ArtifactStatus.PLANNED

    def test_audio_artifacts_not_stored_as_bytes(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        audio_records = [r for r in records if r.kind == ArtifactKind.AUDIO_MIX]
        for rec in audio_records:
            assert rec.status == ArtifactStatus.PLANNED
            assert rec.size_bytes is None

    def test_source_entity_links_to_pack(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        for rec in records:
            assert rec.source_entity_type in ("export_pack",)
            assert rec.source_entity_id == pack.pack_id

    def test_operator_id_propagated(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage, operator_id="admin@test.com")
        for rec in records:
            assert rec.operator_id == "admin@test.com"

    def test_manifest_has_checksum(self) -> None:
        storage = _make_storage()
        pack = _make_export_pack()
        records = record_artifacts_for_export_pack(pack, storage)
        stored = [r for r in records if r.status == ArtifactStatus.STORED]
        for rec in stored:
            assert rec.checksum_sha256 is not None
            assert len(rec.checksum_sha256) == 64


# ============================================================
# Bridge helper: SoundGraph
# ============================================================


class TestRecordArtifactForSoundgraph:
    def test_creates_single_stored_record(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        assert len(records) == 1
        assert records[0].status == ArtifactStatus.STORED

    def test_kind_is_soundgraph(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        assert records[0].kind == ArtifactKind.SOUNDGRAPH

    def test_stored_bytes_are_valid_json(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        file_path = storage.get_file_path(records[0].artifact_id)
        assert file_path is not None
        data = json.loads(file_path.read_bytes())
        assert data["arrangement_id"] == str(arr.arrangement_id)

    def test_content_type_is_json(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        assert records[0].content_type == "application/json"

    def test_source_entity_links_to_arrangement(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        assert records[0].source_entity_type == "soundgraph_arrangement"
        assert records[0].source_entity_id == arr.arrangement_id

    def test_logical_path_includes_arrangement_id(self) -> None:
        storage = _make_storage()
        arr = _make_arrangement()
        records = record_artifact_for_soundgraph(arr, storage)
        assert str(arr.arrangement_id) in records[0].logical_path


# ============================================================
# Bridge helper: MusicJob
# ============================================================


class TestRecordArtifactsForMusicJob:
    def test_completed_job_creates_records(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        # 2 artifacts + 1 manifest = 3
        assert len(records) == 3

    def test_non_completed_job_returns_empty(self) -> None:
        storage = _make_storage()
        job = _make_music_job(status=MusicJobStatus.QUEUED)
        records = record_artifacts_for_music_job(job, storage)
        assert records == []

    def test_preflight_blocked_job_returns_empty(self) -> None:
        storage = _make_storage()
        job = _make_music_job(status=MusicJobStatus.PREFLIGHT_BLOCKED)
        records = record_artifacts_for_music_job(job, storage)
        assert records == []

    def test_audio_artifacts_are_planned_not_stored(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        audio = [r for r in records if r.kind == ArtifactKind.AUDIO_MIX]
        assert len(audio) >= 1
        for rec in audio:
            assert rec.status == ArtifactStatus.PLANNED

    def test_manifest_is_stored_with_real_bytes(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        manifests = [r for r in records if r.kind == ArtifactKind.MANIFEST]
        stored = [r for r in manifests if r.status == ArtifactStatus.STORED]
        assert len(stored) == 1

    def test_manifest_json_contains_job_id(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        stored = [r for r in records if r.status == ArtifactStatus.STORED][0]
        file_path = storage.get_file_path(stored.artifact_id)
        assert file_path is not None
        data = json.loads(file_path.read_bytes())
        assert data["job_id"] == str(job.job_id)
        assert data["intent"] == job.intent.value
        assert data["artifact_count"] == len(job.artifacts)

    def test_provenance_id_propagated(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        for rec in records:
            assert rec.provenance_id == job.provenance_id

    def test_source_entity_links_to_music_job(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)
        for rec in records:
            assert rec.source_entity_type == "music_job"
            assert rec.source_entity_id == job.job_id


# ============================================================
# Bridge helper: ReleasePack
# ============================================================


class TestRecordArtifactsForReleasePack:
    def test_creates_records_for_assets_plus_manifest(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        # 2 assets + 1 manifest = 3
        assert len(records) == 3

    def test_asset_records_are_planned(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        asset_records = records[:2]
        for rec in asset_records:
            assert rec.status == ArtifactStatus.PLANNED

    def test_manifest_is_stored(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        manifest = records[-1]
        assert manifest.status == ArtifactStatus.STORED
        assert manifest.kind == ArtifactKind.MANIFEST

    def test_manifest_bytes_are_valid_json(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        stored = [r for r in records if r.status == ArtifactStatus.STORED][0]
        file_path = storage.get_file_path(stored.artifact_id)
        assert file_path is not None
        data = json.loads(file_path.read_bytes())
        assert data["release_id"] == str(release.release_id)
        assert data["title"] == release.title

    def test_cover_art_has_correct_kind(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        cover = [r for r in records if r.kind == ArtifactKind.COVER_ART]
        assert len(cover) == 1

    def test_audio_master_has_correct_kind(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        audio = [r for r in records if r.kind == ArtifactKind.AUDIO_MIX]
        assert len(audio) == 1

    def test_asset_without_path_gets_generated_path(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        # Assets have path=None, so logical_path should be generated
        for rec in records[:2]:
            assert str(release.release_id) in rec.logical_path

    def test_source_entity_links_to_release(self) -> None:
        storage = _make_storage()
        release = _make_release_pack()
        records = record_artifacts_for_release_pack(release, storage)
        for rec in records:
            assert rec.source_entity_type == "release_pack"
            assert rec.source_entity_id == release.release_id


# ============================================================
# Route integration tests
# ============================================================


class TestMusicRouterBridgeIntegration:
    """Test that POST /v1/music-router/jobs creates artifact records."""

    def test_music_job_creates_artifact_records(self) -> None:
        from app.main import (
            artifact_storage,
            create_music_job,
        )
        from app.schemas import MusicGenerationRequest

        request = MusicGenerationRequest(
            intent=MusicIntentKind.CREATE_LOOP,
            title="Bridge Test Loop",
            prompt="dark warehouse loop 130 bpm",
        )
        job = asyncio.run(create_music_job(request, DEV_OPERATOR))
        assert job.status == MusicJobStatus.COMPLETED

        # Check artifact storage has records linked to this job
        records = artifact_storage.list_records()
        job_records = [
            r
            for r in records
            if r.source_entity_type == "music_job" and r.source_entity_id == job.job_id
        ]
        assert len(job_records) >= 3  # 2 artifacts + 1 manifest


class TestSoundgraphBridgeIntegration:
    """Test that POST /v1/soundgraph/compile creates artifact records."""

    def test_soundgraph_compile_creates_artifact_record(self) -> None:
        from app.main import (
            artifact_storage,
            compile_soundgraph_route,
            lyrics_repository,
        )
        from app.schemas import (
            LyricsLine,
            LyricsSection,
            LyricsSectionType,
            LyricsSource,
            LyricsStructure,
            SoundGraphWriteRequest,
        )

        # Create a lyrics project + version directly
        project = lyrics_repository.create_project(
            "bridge-sg-test", "Bridge SG Test", "SHIBARI_KAWAII"
        )
        structure = LyricsStructure(
            sections=[
                LyricsSection(
                    index=0,
                    section_type=LyricsSectionType.VERSE,
                    label="VERSE 0",
                    lines=[LyricsLine(index=0, text="test line", syllables=4)],
                    locked=False,
                    manually_edited=False,
                    source=LyricsSource.MOCK,
                ),
            ],
            avoid_intro_singing=False,
            target_language="en",
        )
        version = lyrics_repository.add_version(
            project.id, structure, parent_version_id=None, edit_summary=None
        )

        sg_req = SoundGraphWriteRequest(
            lyrics_version_id=version.id,
            bpm=130,
            energy_profile="standard",
        )
        result = asyncio.run(compile_soundgraph_route(sg_req, DEV_OPERATOR))

        # Check artifact storage has a record for this arrangement
        records = artifact_storage.list_records()
        sg_records = [
            r
            for r in records
            if r.source_entity_type == "soundgraph_arrangement"
            and r.source_entity_id == result.arrangement.arrangement_id
        ]
        assert len(sg_records) >= 1
        assert sg_records[0].kind == ArtifactKind.SOUNDGRAPH
        assert sg_records[0].status == ArtifactStatus.STORED


class TestExportPackBridgeIntegration:
    """Test that POST /v1/library/packs creates artifact records."""

    def test_export_pack_creates_artifact_records(self) -> None:
        from app.main import (
            artifact_storage,
            create_export_pack as create_export_pack_route,
            create_music_job,
        )
        from app.schemas import (
            ExportPackCreateRequest,
            MusicGenerationRequest,
        )

        # Create a music job first
        music_req = MusicGenerationRequest(
            intent=MusicIntentKind.CREATE_LOOP,
            title="Export Bridge Test",
            prompt="dark warehouse loop",
        )
        job = asyncio.run(create_music_job(music_req, DEV_OPERATOR))

        # Create export pack
        pack_req = ExportPackCreateRequest(
            music_job_id=job.job_id,
            title="Export Bridge Test Pack",
        )
        pack = asyncio.run(create_export_pack_route(pack_req, DEV_OPERATOR))

        # Check artifact storage has records linked to this pack
        records = artifact_storage.list_records()
        pack_records = [
            r
            for r in records
            if r.source_entity_type == "export_pack" and r.source_entity_id == pack.pack_id
        ]
        assert len(pack_records) >= 2  # at least components + manifest
        # At least one stored manifest
        stored = [r for r in pack_records if r.status == ArtifactStatus.STORED]
        assert len(stored) >= 1


class TestReleasePackBridgeIntegration:
    """Test that POST /v1/releases creates artifact records."""

    def test_release_pack_creates_artifact_records(self) -> None:
        from app.main import (
            artifact_storage,
            create_export_pack as create_export_pack_route,
            create_music_job,
            create_release_pack as create_release_route,
        )
        from app.schemas import (
            ExportPackCreateRequest,
            MusicGenerationRequest,
            ReleasePackCreateRequest,
        )

        # Create music job → export pack → release pack
        music_req = MusicGenerationRequest(
            intent=MusicIntentKind.CREATE_LOOP,
            title="Release Bridge Test",
            prompt="dark warehouse loop",
        )
        job = asyncio.run(create_music_job(music_req, DEV_OPERATOR))

        pack_req = ExportPackCreateRequest(
            music_job_id=job.job_id,
            title="Release Bridge Test Pack",
        )
        pack = asyncio.run(create_export_pack_route(pack_req, DEV_OPERATOR))

        release_req = ReleasePackCreateRequest(
            pack_id=pack.pack_id,
            artist="Test Artist",
        )
        release = asyncio.run(create_release_route(release_req, DEV_OPERATOR))

        # Check artifact storage has records linked to this release
        records = artifact_storage.list_records()
        release_records = [
            r
            for r in records
            if r.source_entity_type == "release_pack" and r.source_entity_id == release.release_id
        ]
        assert len(release_records) >= 2  # assets + manifest
        # Manifest stored
        stored = [r for r in release_records if r.status == ArtifactStatus.STORED]
        assert len(stored) >= 1


# ============================================================
# Storage summary after bridge operations
# ============================================================


class TestStorageSummaryAfterBridge:
    def test_summary_reflects_bridge_records(self) -> None:
        storage = _make_storage()
        job = _make_music_job()
        records = record_artifacts_for_music_job(job, storage)

        summary = storage.summary()
        assert summary.total == len(records)
        assert summary.stored >= 1  # at least the manifest
        assert summary.planned >= 1  # at least the audio artifact
        assert summary.total_size_bytes > 0  # manifest has real bytes
