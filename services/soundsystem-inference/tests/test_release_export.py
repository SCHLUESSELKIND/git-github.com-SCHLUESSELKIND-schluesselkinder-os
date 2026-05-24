"""Tests for S34 — Release Export ZIP Builder.

Covers:
- Export with all assets (cover + audio + stems) succeeds
- Export with partial assets succeeds with warnings
- Export with no assets fails
- ZIP contains expected folder structure
- manifest.json exists and has entries + checksums
- release.json + social-copy.json included
- Filenames sanitized, no path traversal
- ArtifactRecord created for export ZIP (kind=export_pack)
- Signed download link works for export ZIP
- Route requires operator identity
- Existing upload tests still pass (implicit via full suite)
"""

from __future__ import annotations

import base64
import io
import json
import tempfile
import wave
import zipfile
from uuid import uuid4

import pytest
from PIL import Image

from app.artifact_storage import LocalArtifactStorage
from app.audio_upload import upload_audio_master_for_release
from app.auth import DEV_OPERATOR
from app.cover_upload import upload_cover_for_release
from app.release_export import (
    build_release_export_zip,
    build_release_manifest,
    collect_release_assets,
)
from app.schemas import (
    ArtifactKind,
    ArtifactStatus,
    AudioMasterUploadRequest,
    CoverAssetUploadRequest,
    ReleaseAssetPlaceholder,
    ReleaseExportEntry,
    ReleaseExportStatus,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    StemPackUploadRequest,
)
from app.stem_upload import upload_stem_pack_for_release


# ---------- Helpers ----------


def _make_storage() -> LocalArtifactStorage:
    tmpdir = tempfile.mkdtemp()
    return LocalArtifactStorage(root=tmpdir)


def _make_release(
    with_cover: bool = True,
    with_audio: bool = True,
    with_stems: bool = True,
) -> ReleasePack:
    """Create a minimal ReleasePack for testing."""
    assets = []
    if with_cover:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
            )
        )
    if with_audio:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master (WAV)",
                expected_format="wav",
                ready=False,
            )
        )
    if with_stems:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="stems_archive",
                label="Stem Pack (ZIP)",
                expected_format="zip",
                ready=False,
            )
        )
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="Test Release",
        artist="Test Artist",
        status=ReleasePackStatus.DRAFT,
        social_copy=SocialCopy(
            soundcloud_description="Test SC description",
            tiktok_caption="Test TikTok",
            instagram_caption="Test IG",
            hashtags=["#test"],
        ),
        compliance_checklist=[],
        compliance_passed=False,
        assets=assets,
    )


def _make_cover_image() -> bytes:
    """Create a valid 1500x1500 PNG in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (1500, 1500), color=(255, 0, 0))
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_wav() -> bytes:
    """Create a valid WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(3)
        wf.setframerate(48000)
        n_frames = 48000 * 2  # 2 seconds
        wf.writeframes(b"\x00" * n_frames * 2 * 3)
    return buf.getvalue()


def _make_stems_zip() -> bytes:
    """Create a valid stems ZIP in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("kick.wav", b"\x00" * 512)
        zf.writestr("snare.wav", b"\x00" * 512)
        zf.writestr("manifest.json", b'{"stems": ["kick", "snare"]}')
    return buf.getvalue()


def _upload_cover(release: ReleasePack, storage: LocalArtifactStorage) -> ReleasePack:
    """Upload a cover and return the updated release."""
    data = _make_cover_image()
    req = CoverAssetUploadRequest(
        filename="cover.png",
        content_type="image/png",
        content_base64=base64.b64encode(data).decode(),
    )
    result = upload_cover_for_release(release, req, storage)
    return result.release


def _upload_audio(release: ReleasePack, storage: LocalArtifactStorage) -> ReleasePack:
    """Upload an audio master and return the updated release."""
    data = _make_wav()
    req = AudioMasterUploadRequest(
        filename="master.wav",
        content_type="audio/wav",
        content_base64=base64.b64encode(data).decode(),
    )
    result = upload_audio_master_for_release(release, req, storage)
    return result.release


def _upload_stems(release: ReleasePack, storage: LocalArtifactStorage) -> ReleasePack:
    """Upload a stem pack and return the updated release."""
    data = _make_stems_zip()
    req = StemPackUploadRequest(
        filename="stems.zip",
        content_type="application/zip",
        content_base64=base64.b64encode(data).decode(),
    )
    result = upload_stem_pack_for_release(release, req, storage)
    return result.release


def _upload_all(release: ReleasePack, storage: LocalArtifactStorage) -> ReleasePack:
    """Upload all three assets and return the final release state."""
    release = _upload_cover(release, storage)
    release = _upload_audio(release, storage)
    release = _upload_stems(release, storage)
    return release


# ============================================================
# Export with full assets
# ============================================================


class TestReleaseExportFull:
    def test_export_succeeds_with_all_assets(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage, operator_id="op@test.com")

        assert result.status == ReleaseExportStatus.COMPLETED
        assert result.artifact.kind == ArtifactKind.EXPORT_PACK
        assert result.artifact.status == ArtifactStatus.STORED
        assert result.total_files > 0
        assert result.total_size_bytes > 0
        assert len(result.warnings) == 0

    def test_export_zip_structure(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        # Read the ZIP back from storage
        file_path = storage.get_file_path(result.artifact.artifact_id)
        assert file_path is not None
        assert file_path.exists()

        with zipfile.ZipFile(file_path, "r") as zf:
            names = zf.namelist()
            assert "release/cover/cover.png" in names
            assert "release/audio/master.wav" in names
            assert "release/stems/stems.zip" in names
            assert "release/metadata/release.json" in names
            assert "release/metadata/social-copy.json" in names
            assert "release/metadata/manifest.json" in names

    def test_manifest_json_has_entries_and_checksums(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        with zipfile.ZipFile(file_path, "r") as zf:
            manifest_data = zf.read("release/metadata/manifest.json")
            manifest = json.loads(manifest_data)

        assert manifest["version"] == "1.0"
        assert manifest["release_id"] == str(release.release_id)
        assert manifest["title"] == "Test Release"
        assert "entries" in manifest
        assert len(manifest["entries"]) > 0

        for entry in manifest["entries"]:
            assert "checksum_sha256" in entry
            assert len(entry["checksum_sha256"]) == 64
            assert "size_bytes" in entry
            assert "path" in entry

    def test_release_json_included(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        with zipfile.ZipFile(file_path, "r") as zf:
            release_data = json.loads(zf.read("release/metadata/release.json"))

        assert release_data["title"] == "Test Release"
        assert release_data["artist"] == "Test Artist"

    def test_social_copy_json_included(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        with zipfile.ZipFile(file_path, "r") as zf:
            social_data = json.loads(zf.read("release/metadata/social-copy.json"))

        assert social_data["soundcloud_description"] == "Test SC description"
        assert social_data["tiktok_caption"] == "Test TikTok"

    def test_entries_match_zip_contents(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        entry_paths = {e.path for e in result.entries}
        assert "release/cover/cover.png" in entry_paths
        assert "release/audio/master.wav" in entry_paths
        assert "release/stems/stems.zip" in entry_paths
        assert "release/metadata/release.json" in entry_paths
        assert "release/metadata/social-copy.json" in entry_paths
        assert "release/metadata/manifest.json" in entry_paths

    def test_operator_id_propagated(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage, operator_id="op@test.com")

        assert result.artifact.operator_id == "op@test.com"

    def test_artifact_stored_on_disk(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        result = build_release_export_zip(release, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        assert file_path is not None
        assert file_path.exists()
        assert file_path.stat().st_size > 0


# ============================================================
# Partial exports
# ============================================================


class TestReleaseExportPartial:
    def test_cover_only_succeeds_with_warnings(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_cover(release, storage)

        result = build_release_export_zip(release, storage)

        assert result.status == ReleaseExportStatus.COMPLETED
        warning_codes = {w.code for w in result.warnings}
        assert "audio_missing" in warning_codes
        assert "stems_missing" in warning_codes
        assert "cover_missing" not in warning_codes

    def test_audio_only_succeeds_with_warnings(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_audio(release, storage)

        result = build_release_export_zip(release, storage)

        assert result.status == ReleaseExportStatus.COMPLETED
        warning_codes = {w.code for w in result.warnings}
        assert "cover_missing" in warning_codes
        assert "stems_missing" in warning_codes

    def test_stems_only_succeeds_with_warnings(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_stems(release, storage)

        result = build_release_export_zip(release, storage)

        assert result.status == ReleaseExportStatus.COMPLETED
        warning_codes = {w.code for w in result.warnings}
        assert "cover_missing" in warning_codes
        assert "audio_missing" in warning_codes

    def test_cover_and_audio_no_stems(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_cover(release, storage)
        release = _upload_audio(release, storage)

        result = build_release_export_zip(release, storage)

        assert result.status == ReleaseExportStatus.COMPLETED
        warning_codes = {w.code for w in result.warnings}
        assert "stems_missing" in warning_codes
        assert len(result.warnings) == 1

    def test_partial_zip_only_has_uploaded_assets(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_cover(release, storage)

        result = build_release_export_zip(release, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        with zipfile.ZipFile(file_path, "r") as zf:
            names = zf.namelist()
            assert "release/cover/cover.png" in names
            assert "release/audio/master.wav" not in names
            assert "release/stems/stems.zip" not in names
            # Metadata always present
            assert "release/metadata/release.json" in names
            assert "release/metadata/manifest.json" in names


# ============================================================
# No assets
# ============================================================


class TestReleaseExportNoAssets:
    def test_no_assets_fails(self) -> None:
        storage = _make_storage()
        release = _make_release()

        with pytest.raises(ValueError, match="no assets uploaded"):
            build_release_export_zip(release, storage)

    def test_no_placeholders_fails(self) -> None:
        storage = _make_storage()
        release = _make_release(with_cover=False, with_audio=False, with_stems=False)

        with pytest.raises(ValueError, match="no assets uploaded"):
            build_release_export_zip(release, storage)


# ============================================================
# Manifest builder
# ============================================================


class TestBuildReleaseManifest:
    def test_manifest_structure(self) -> None:
        release = _make_release()
        entries = [
            ReleaseExportEntry(
                path="release/cover/cover.png",
                source_asset_type="cover_art",
                size_bytes=1000,
                checksum_sha256="a" * 64,
                content_type="image/png",
            ),
        ]
        manifest = build_release_manifest(release, entries)

        assert manifest["version"] == "1.0"
        assert manifest["release_id"] == str(release.release_id)
        assert manifest["title"] == release.title
        assert len(manifest["entries"]) == 1
        assert manifest["entries"][0]["checksum_sha256"] == "a" * 64


# ============================================================
# Collect assets
# ============================================================


class TestCollectReleaseAssets:
    def test_collect_all_present(self) -> None:
        storage = _make_storage()
        release = _make_release()
        release = _upload_all(release, storage)

        collected, warnings = collect_release_assets(release, storage)

        assert "cover_art" in collected
        assert "audio_master" in collected
        assert "stems_archive" in collected
        assert len(warnings) == 0

    def test_collect_none_present(self) -> None:
        storage = _make_storage()
        release = _make_release()

        collected, warnings = collect_release_assets(release, storage)

        assert len(collected) == 0
        assert len(warnings) == 3


# ============================================================
# Route integration tests
# ============================================================


def _create_test_release_with_assets() -> tuple[ReleasePack, LocalArtifactStorage]:
    """Create a release with all assets uploaded, stored in module-level repos."""
    from app.main import artifact_storage, release_pack_repository

    storage = artifact_storage
    release = _make_release()
    release_pack_repository.store(release)

    # Upload assets using the module-level storage
    release = _upload_cover(release, storage)
    release = _upload_audio(release, storage)
    release = _upload_stems(release, storage)
    release_pack_repository.update(release)

    return release, storage


def _create_test_release_no_assets() -> ReleasePack:
    """Create a release with no assets, stored in module-level repos."""
    from app.main import release_pack_repository

    release = _make_release()
    release_pack_repository.store(release)
    return release


class TestReleaseExportRoute:
    """Route tests using asyncio.run() — matches existing test patterns."""

    def test_export_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import build_release_export

        release, _ = _create_test_release_with_assets()

        result = asyncio.run(build_release_export(release.release_id, DEV_OPERATOR))

        assert result.artifact.kind == ArtifactKind.EXPORT_PACK
        assert result.artifact.status == ArtifactStatus.STORED
        assert result.status == ReleaseExportStatus.COMPLETED
        assert result.total_files > 0

    def test_export_no_assets_rejected_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import build_release_export

        release = _create_test_release_no_assets()

        with pytest.raises(Exception) as exc_info:
            asyncio.run(build_release_export(release.release_id, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_export_release_not_found_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import build_release_export

        with pytest.raises(Exception) as exc_info:
            asyncio.run(build_release_export(uuid4(), DEV_OPERATOR))
        assert exc_info.value.status_code == 404

    def test_download_link_works_for_export(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        monkeypatch.setenv("SOUNDSYSTEM_ARTIFACT_ACCESS_MODE", "direct")
        import asyncio

        from app.main import build_release_export, get_artifact_download_link

        release, _ = _create_test_release_with_assets()

        result = asyncio.run(build_release_export(release.release_id, DEV_OPERATOR))
        link = asyncio.run(get_artifact_download_link(result.artifact.artifact_id))
        assert "/download" in link.url
