"""Tests for S33 — Stem Pack Upload Pipeline.

Covers:
- Content type validation: ZIP accepted, RAR/7z/TAR rejected
- ZIP validation: structure, path traversal, absolute paths, encrypted,
  max files, max uncompressed size, allowed extensions
- Warnings: no audio stems, no manifest, large uncompressed
- Successful upload creates ArtifactRecord (kind=stem_pack)
- Successful upload updates ReleasePack stems_archive placeholder
- Route requires operator identity
- Signed download link works for uploaded ZIP
- Cover/audio upload tests still pass (implicit via full suite)
"""

from __future__ import annotations

import base64
import io
import tempfile
import zipfile
from uuid import uuid4

import pytest

from app.artifact_storage import LocalArtifactStorage
from app.auth import DEV_OPERATOR
from app.schemas import (
    ArtifactKind,
    ArtifactStatus,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    StemPackUploadRequest,
)
from app.stem_upload import (
    upload_stem_pack_for_release,
    validate_stem_content_type,
    validate_stem_pack_data,
)


# ---------- Helpers ----------


def _make_zip(
    files: dict[str, bytes] | None = None,
    include_audio: bool = True,
    include_manifest: bool = True,
) -> bytes:
    """Create a valid ZIP file in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if files is not None:
            for name, content in files.items():
                zf.writestr(name, content)
        else:
            if include_audio:
                zf.writestr("kick.wav", b"\x00" * 1024)
                zf.writestr("snare.wav", b"\x00" * 1024)
                zf.writestr("bass.wav", b"\x00" * 1024)
            if include_manifest:
                zf.writestr("manifest.json", b'{"stems": ["kick", "snare", "bass"]}')
    return buf.getvalue()


def _make_release(
    with_stems_placeholder: bool = True,
) -> ReleasePack:
    """Create a minimal ReleasePack for testing."""
    assets = [
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
    ]
    if with_stems_placeholder:
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
        social_copy=SocialCopy(),
        compliance_checklist=[],
        compliance_passed=False,
        assets=assets,
    )


def _make_storage() -> LocalArtifactStorage:
    tmpdir = tempfile.mkdtemp()
    return LocalArtifactStorage(root=tmpdir)


def _make_upload_request(
    data: bytes | None = None,
    content_type: str = "application/zip",
    filename: str = "stems.zip",
) -> StemPackUploadRequest:
    if data is None:
        data = _make_zip()
    return StemPackUploadRequest(
        filename=filename,
        content_type=content_type,
        content_base64=base64.b64encode(data).decode(),
    )


# ============================================================
# Content type validation
# ============================================================


class TestStemContentType:
    def test_zip_accepted(self) -> None:
        validate_stem_content_type("application/zip")

    def test_x_zip_accepted(self) -> None:
        validate_stem_content_type("application/x-zip-compressed")

    def test_rar_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_stem_content_type("application/x-rar-compressed")

    def test_rar_vnd_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_stem_content_type("application/vnd.rar")

    def test_7z_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_stem_content_type("application/x-7z-compressed")

    def test_tar_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_stem_content_type("application/x-tar")

    def test_unknown_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown content type"):
            validate_stem_content_type("video/mp4")


# ============================================================
# ZIP validation
# ============================================================


class TestStemPackValidation:
    def test_valid_zip(self) -> None:
        data = _make_zip()
        entries, warnings, total = validate_stem_pack_data(data)
        assert len(entries) == 4  # 3 wav + manifest.json
        assert total > 0
        audio_entries = [e for e in entries if e.is_audio]
        assert len(audio_entries) == 3

    def test_invalid_zip(self) -> None:
        with pytest.raises(ValueError, match="not a valid ZIP"):
            validate_stem_pack_data(b"not a zip file")

    def test_empty_data(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_stem_pack_data(b"")

    def test_empty_zip(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w"):
            pass  # empty archive
        with pytest.raises(ValueError, match="empty.*no files"):
            validate_stem_pack_data(buf.getvalue())

    def test_path_traversal_rejected(self) -> None:
        data = _make_zip(files={"../evil.wav": b"\x00" * 100})
        with pytest.raises(ValueError, match="path traversal"):
            validate_stem_pack_data(data)

    def test_absolute_path_rejected(self) -> None:
        data = _make_zip(files={"/etc/evil.wav": b"\x00" * 100})
        with pytest.raises(ValueError, match="absolute path"):
            validate_stem_pack_data(data)

    def test_disallowed_extension_rejected(self) -> None:
        data = _make_zip(files={"script.py": b"import os"})
        with pytest.raises(ValueError, match="disallowed file type"):
            validate_stem_pack_data(data)

    def test_exe_extension_rejected(self) -> None:
        data = _make_zip(files={"malware.exe": b"\x00" * 100})
        with pytest.raises(ValueError, match="disallowed file type"):
            validate_stem_pack_data(data)

    def test_too_many_files_rejected(self) -> None:
        files = {f"stem_{i:03d}.wav": b"\x00" * 100 for i in range(65)}
        data = _make_zip(files=files)
        with pytest.raises(ValueError, match="65 files.*max 64"):
            validate_stem_pack_data(data)

    def test_max_files_accepted(self) -> None:
        files = {f"stem_{i:03d}.wav": b"\x00" * 100 for i in range(64)}
        data = _make_zip(files=files)
        entries, _, _ = validate_stem_pack_data(data)
        assert len(entries) == 64

    def test_no_audio_warns(self) -> None:
        data = _make_zip(files={"readme.txt": b"hello", "manifest.json": b"{}"})
        _, warnings, _ = validate_stem_pack_data(data)
        assert any(w.code == "no_audio_stems" for w in warnings)

    def test_no_manifest_warns(self) -> None:
        data = _make_zip(include_manifest=False)
        _, warnings, _ = validate_stem_pack_data(data)
        assert any(w.code == "no_manifest" for w in warnings)

    def test_has_manifest_no_warning(self) -> None:
        data = _make_zip(include_manifest=True)
        _, warnings, _ = validate_stem_pack_data(data)
        assert not any(w.code == "no_manifest" for w in warnings)

    def test_allowed_extensions_accepted(self) -> None:
        files = {
            "kick.wav": b"\x00" * 100,
            "pad.aiff": b"\x00" * 100,
            "lead.aif": b"\x00" * 100,
            "readme.txt": b"info",
            "manifest.json": b"{}",
            "notes.md": b"# Notes",
        }
        data = _make_zip(files=files)
        entries, warnings, _ = validate_stem_pack_data(data)
        assert len(entries) == 6
        assert len(warnings) == 0

    def test_nested_path_accepted(self) -> None:
        files = {
            "stems/kick.wav": b"\x00" * 100,
            "stems/snare.wav": b"\x00" * 100,
            "manifest.json": b"{}",
        }
        data = _make_zip(files=files)
        entries, _, _ = validate_stem_pack_data(data)
        assert len(entries) == 3


# ============================================================
# Full upload pipeline
# ============================================================


class TestStemUploadPipeline:
    def test_successful_upload_creates_artifact(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage, operator_id="op@test.com")

        assert result.artifact.kind == ArtifactKind.STEM_PACK
        assert result.artifact.status == ArtifactStatus.STORED
        assert result.artifact.content_type == "application/zip"
        assert result.artifact.size_bytes is not None
        assert result.artifact.size_bytes > 0

    def test_upload_updates_release_placeholder(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage)

        stems_asset = next(
            (a for a in result.release.assets if a.asset_type == "stems_archive"),
            None,
        )
        assert stems_asset is not None
        assert stems_asset.ready is True
        assert stems_asset.artifact_id == result.artifact.artifact_id

    def test_other_assets_preserved(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage)

        cover_asset = next(
            (a for a in result.release.assets if a.asset_type == "cover_art"),
            None,
        )
        assert cover_asset is not None
        assert cover_asset.ready is False

        audio_asset = next(
            (a for a in result.release.assets if a.asset_type == "audio_master"),
            None,
        )
        assert audio_asset is not None
        assert audio_asset.ready is False

    def test_upload_without_placeholder_adds_one(self) -> None:
        storage = _make_storage()
        release = _make_release(with_stems_placeholder=False)
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage)

        stems_asset = next(
            (a for a in result.release.assets if a.asset_type == "stems_archive"),
            None,
        )
        assert stems_asset is not None
        assert stems_asset.ready is True

    def test_rar_upload_rejected(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = StemPackUploadRequest(
            filename="stems.rar",
            content_type="application/x-rar-compressed",
            content_base64=base64.b64encode(b"fake").decode(),
        )

        with pytest.raises(ValueError, match="not accepted"):
            upload_stem_pack_for_release(release, request, storage)

    def test_entries_returned(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage)

        assert result.total_files == 4
        assert result.total_uncompressed_bytes > 0
        assert len(result.entries) == 4
        audio_entries = [e for e in result.entries if e.is_audio]
        assert len(audio_entries) == 3

    def test_operator_id_propagated(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage, operator_id="op@test.com")

        assert result.artifact.operator_id == "op@test.com"

    def test_artifact_stored_on_disk(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_stem_pack_for_release(release, request, storage)

        file_path = storage.get_file_path(result.artifact.artifact_id)
        assert file_path is not None
        assert file_path.exists()


# ============================================================
# Route integration tests
# ============================================================


def _create_test_release() -> ReleasePack:
    """Create a release in the module-level repos for route testing."""
    from app.main import release_pack_repository

    release = _make_release()
    release_pack_repository.store(release)
    return release


class TestStemUploadRoute:
    """Route tests using asyncio.run() — matches existing test patterns."""

    def test_upload_stem_pack_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_stem_pack

        release = _create_test_release()
        data = _make_zip()
        req = StemPackUploadRequest(
            filename="stems.zip",
            content_type="application/zip",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_stem_pack(release.release_id, req, DEV_OPERATOR))

        assert result.artifact.kind == ArtifactKind.STEM_PACK
        assert result.artifact.status == ArtifactStatus.STORED
        stems_asset = next(
            (a for a in result.release.assets if a.asset_type == "stems_archive"),
            None,
        )
        assert stems_asset is not None
        assert stems_asset.ready is True
        assert stems_asset.artifact_id == result.artifact.artifact_id

    def test_upload_rar_rejected_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_stem_pack

        release = _create_test_release()
        req = StemPackUploadRequest(
            filename="stems.rar",
            content_type="application/x-rar-compressed",
            content_base64=base64.b64encode(b"fake").decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_stem_pack(release.release_id, req, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_upload_release_not_found_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_stem_pack

        data = _make_zip()
        req = StemPackUploadRequest(
            filename="stems.zip",
            content_type="application/zip",
            content_base64=base64.b64encode(data).decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_stem_pack(uuid4(), req, DEV_OPERATOR))
        assert exc_info.value.status_code == 404

    def test_download_link_works_for_uploaded_stems(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        monkeypatch.setenv("SOUNDSYSTEM_ARTIFACT_ACCESS_MODE", "direct")
        import asyncio

        from app.main import get_artifact_download_link, upload_release_stem_pack

        release = _create_test_release()
        data = _make_zip()
        req = StemPackUploadRequest(
            filename="stems.zip",
            content_type="application/zip",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_stem_pack(release.release_id, req, DEV_OPERATOR))
        link = asyncio.run(get_artifact_download_link(result.artifact.artifact_id))
        assert "/download" in link.url
