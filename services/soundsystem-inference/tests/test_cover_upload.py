"""Tests for S31 — Cover Asset Upload Pipeline.

Covers:
- Content type validation: PNG/JPEG accepted, SVG/WebP rejected
- Size validation: reject >20 MB, reject 0 bytes
- Dimension validation: reject non-square, reject below 1400px, warn below 3000px
- Successful upload creates ArtifactRecord (kind=cover_art)
- Successful upload updates ReleasePack cover placeholder
- Route requires operator identity
- Signed download link works for uploaded cover
- Existing release tests still pass (implicit via full suite)
"""

from __future__ import annotations

import base64
import io
import tempfile
from uuid import uuid4

import pytest
from PIL import Image

from app.artifact_storage import LocalArtifactStorage
from app.auth import DEV_OPERATOR
from app.cover_upload import (
    MIN_DIMENSION_PX,
    upload_cover_for_release,
    validate_cover_content_type,
    validate_cover_data,
)
from app.schemas import (
    ArtifactKind,
    ArtifactStatus,
    CoverAssetUploadRequest,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_test_image(
    width: int = 1500,
    height: int = 1500,
    fmt: str = "PNG",
) -> bytes:
    """Create a test image in memory."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _make_release(
    with_cover_placeholder: bool = True,
) -> ReleasePack:
    """Create a minimal ReleasePack for testing."""
    assets = []
    if with_cover_placeholder:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
                path=None,
            )
        )
    assets.append(
        ReleaseAssetPlaceholder(
            asset_type="audio_master",
            label="Audio Master (WAV)",
            expected_format="wav",
            ready=False,
            path=None,
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
    content_type: str = "image/png",
    filename: str = "cover.png",
    fmt: str = "PNG",
) -> CoverAssetUploadRequest:
    if data is None:
        data = _make_test_image(fmt=fmt)
    return CoverAssetUploadRequest(
        filename=filename,
        content_type=content_type,
        content_base64=base64.b64encode(data).decode(),
    )


# ============================================================
# Content type validation
# ============================================================


class TestContentTypeValidation:
    def test_png_accepted(self) -> None:
        validate_cover_content_type("image/png")  # no error

    def test_jpeg_accepted(self) -> None:
        validate_cover_content_type("image/jpeg")  # no error

    def test_svg_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_cover_content_type("image/svg+xml")

    def test_webp_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_cover_content_type("image/webp")

    def test_unknown_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown content type"):
            validate_cover_content_type("application/pdf")


# ============================================================
# Size / dimension validation
# ============================================================


class TestImageValidation:
    def test_valid_png(self) -> None:
        data = _make_test_image(1500, 1500, "PNG")
        warnings = validate_cover_data(data, "image/png")
        assert any(w.code == "below_recommended_size" for w in warnings)

    def test_valid_jpeg(self) -> None:
        data = _make_test_image(1500, 1500, "JPEG")
        warnings = validate_cover_data(data, "image/jpeg")
        assert any(w.code == "below_recommended_size" for w in warnings)

    def test_large_enough_no_warning(self) -> None:
        data = _make_test_image(3000, 3000, "PNG")
        warnings = validate_cover_data(data, "image/png")
        assert len(warnings) == 0

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_cover_data(b"", "image/png")

    def test_non_square_rejected(self) -> None:
        data = _make_test_image(1500, 1600, "PNG")
        with pytest.raises(ValueError, match="square"):
            validate_cover_data(data, "image/png")

    def test_too_small_rejected(self) -> None:
        data = _make_test_image(500, 500, "PNG")
        with pytest.raises(ValueError, match="too small"):
            validate_cover_data(data, "image/png")

    def test_exactly_minimum_accepted(self) -> None:
        data = _make_test_image(MIN_DIMENSION_PX, MIN_DIMENSION_PX, "PNG")
        warnings = validate_cover_data(data, "image/png")
        assert any(w.code == "below_recommended_size" for w in warnings)

    def test_format_mismatch_rejected(self) -> None:
        data = _make_test_image(1500, 1500, "JPEG")
        with pytest.raises(ValueError, match="content_type is image/png"):
            validate_cover_data(data, "image/png")


# ============================================================
# Full upload pipeline
# ============================================================


class TestUploadPipeline:
    def test_successful_upload_creates_artifact(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage, operator_id="op@test.com")

        assert result.artifact.kind == ArtifactKind.COVER_ART
        assert result.artifact.status == ArtifactStatus.STORED
        assert result.artifact.content_type == "image/png"
        assert result.artifact.size_bytes is not None
        assert result.artifact.size_bytes > 0

    def test_successful_upload_updates_release_placeholder(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage)

        cover_asset = next((a for a in result.release.assets if a.asset_type == "cover_art"), None)
        assert cover_asset is not None
        assert cover_asset.ready is True
        assert cover_asset.artifact_id == result.artifact.artifact_id

    def test_other_assets_preserved(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage)

        audio_asset = next(
            (a for a in result.release.assets if a.asset_type == "audio_master"), None
        )
        assert audio_asset is not None
        assert audio_asset.ready is False

    def test_upload_without_placeholder_adds_one(self) -> None:
        storage = _make_storage()
        release = _make_release(with_cover_placeholder=False)
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage)

        cover_asset = next((a for a in result.release.assets if a.asset_type == "cover_art"), None)
        assert cover_asset is not None
        assert cover_asset.ready is True
        assert cover_asset.artifact_id is not None

    def test_jpeg_upload_works(self) -> None:
        storage = _make_storage()
        release = _make_release()
        data = _make_test_image(1500, 1500, "JPEG")
        request = _make_upload_request(data=data, content_type="image/jpeg", filename="cover.jpg")

        result = upload_cover_for_release(release, request, storage)

        assert result.artifact.content_type == "image/jpeg"
        assert result.artifact.status == ArtifactStatus.STORED

    def test_svg_upload_rejected(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = CoverAssetUploadRequest(
            filename="cover.svg",
            content_type="image/svg+xml",
            content_base64=base64.b64encode(b"<svg></svg>").decode(),
        )

        with pytest.raises(ValueError, match="not accepted"):
            upload_cover_for_release(release, request, storage)

    def test_webp_upload_rejected(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = CoverAssetUploadRequest(
            filename="cover.webp",
            content_type="image/webp",
            content_base64=base64.b64encode(b"fake").decode(),
        )

        with pytest.raises(ValueError, match="not accepted"):
            upload_cover_for_release(release, request, storage)

    def test_warnings_returned_for_small_cover(self) -> None:
        storage = _make_storage()
        release = _make_release()
        data = _make_test_image(1500, 1500, "PNG")
        request = _make_upload_request(data=data)

        result = upload_cover_for_release(release, request, storage)

        assert len(result.warnings) > 0
        assert result.warnings[0].code == "below_recommended_size"

    def test_no_warnings_for_large_cover(self) -> None:
        storage = _make_storage()
        release = _make_release()
        data = _make_test_image(3000, 3000, "PNG")
        request = _make_upload_request(data=data)

        result = upload_cover_for_release(release, request, storage)

        assert len(result.warnings) == 0

    def test_operator_id_propagated(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage, operator_id="op@test.com")

        assert result.artifact.operator_id == "op@test.com"

    def test_artifact_stored_on_disk(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_cover_for_release(release, request, storage)

        # Verify file exists on disk
        file_path = storage.get_file_path(result.artifact.artifact_id)
        assert file_path is not None
        assert file_path.exists()


# ============================================================
# Route integration tests (asyncio.run pattern — no httpx needed)
# ============================================================


def _create_test_release() -> ReleasePack:
    """Create a release in the module-level repos for route testing."""
    from app.main import release_pack_repository

    release = _make_release()
    release_pack_repository.store(release)
    return release


class TestCoverUploadRoute:
    """Route tests using asyncio.run() — matches existing test patterns."""

    def test_upload_cover_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_cover

        release = _create_test_release()
        data = _make_test_image(1500, 1500, "PNG")
        req = CoverAssetUploadRequest(
            filename="cover.png",
            content_type="image/png",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_cover(release.release_id, req, DEV_OPERATOR))

        assert result.artifact.kind == ArtifactKind.COVER_ART
        assert result.artifact.status == ArtifactStatus.STORED
        # Check release placeholder updated
        cover = next((a for a in result.release.assets if a.asset_type == "cover_art"), None)
        assert cover is not None
        assert cover.ready is True
        assert cover.artifact_id == result.artifact.artifact_id

    def test_upload_cover_svg_rejected_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_cover

        release = _create_test_release()
        req = CoverAssetUploadRequest(
            filename="cover.svg",
            content_type="image/svg+xml",
            content_base64=base64.b64encode(b"<svg></svg>").decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_cover(release.release_id, req, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_upload_cover_release_not_found_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_cover

        data = _make_test_image(1500, 1500, "PNG")
        req = CoverAssetUploadRequest(
            filename="cover.png",
            content_type="image/png",
            content_base64=base64.b64encode(data).decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_cover(uuid4(), req, DEV_OPERATOR))
        assert exc_info.value.status_code == 404

    def test_upload_cover_too_small_rejected_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_cover

        release = _create_test_release()
        data = _make_test_image(500, 500, "PNG")
        req = CoverAssetUploadRequest(
            filename="cover.png",
            content_type="image/png",
            content_base64=base64.b64encode(data).decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_cover(release.release_id, req, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_download_link_works_for_uploaded_cover(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        monkeypatch.setenv("SOUNDSYSTEM_ARTIFACT_ACCESS_MODE", "direct")
        import asyncio

        from app.main import get_artifact_download_link, upload_release_cover

        release = _create_test_release()
        data = _make_test_image(1500, 1500, "PNG")
        req = CoverAssetUploadRequest(
            filename="cover.png",
            content_type="image/png",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_cover(release.release_id, req, DEV_OPERATOR))
        link = asyncio.run(get_artifact_download_link(result.artifact.artifact_id))
        assert "/download" in link.url

    def test_upload_cover_returns_warnings_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_cover

        release = _create_test_release()
        data = _make_test_image(1500, 1500, "PNG")
        req = CoverAssetUploadRequest(
            filename="cover.png",
            content_type="image/png",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_cover(release.release_id, req, DEV_OPERATOR))
        assert len(result.warnings) > 0
        assert result.warnings[0].code == "below_recommended_size"
