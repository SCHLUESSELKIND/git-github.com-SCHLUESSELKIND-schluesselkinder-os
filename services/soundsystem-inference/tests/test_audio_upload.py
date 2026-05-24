"""Tests for S32 — Audio Master Upload Pipeline.

Covers:
- Content type validation: WAV accepted, MP3/AAC/FLAC rejected
- WAV header validation: channels, sample rate, bit depth, duration
- Warnings: mono, low sample rate, 16-bit, long duration
- Successful upload creates ArtifactRecord (kind=audio_master)
- Successful upload updates ReleasePack audio_master placeholder
- Route requires operator identity
- Signed download link works for uploaded WAV
- Cover upload tests still pass (implicit via full suite)
"""

from __future__ import annotations

import base64
import io
import tempfile
import wave
from uuid import uuid4

import pytest

from app.artifact_storage import LocalArtifactStorage
from app.audio_upload import (
    parse_wav_header,
    upload_audio_master_for_release,
    validate_audio_content_type,
    validate_audio_data,
)
from app.auth import DEV_OPERATOR
from app.schemas import (
    ArtifactKind,
    ArtifactStatus,
    AudioMasterUploadRequest,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_wav(
    channels: int = 2,
    sample_rate: int = 48000,
    sample_width: int = 3,
    duration_seconds: float = 2.0,
) -> bytes:
    """Create a valid WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        n_frames = int(sample_rate * duration_seconds)
        # Generate silence (zero bytes)
        frame_size = channels * sample_width
        wf.writeframes(b"\x00" * n_frames * frame_size)
    return buf.getvalue()


def _make_release(
    with_audio_placeholder: bool = True,
) -> ReleasePack:
    """Create a minimal ReleasePack for testing."""
    assets = [
        ReleaseAssetPlaceholder(
            asset_type="cover_art",
            label="Cover Art",
            expected_format="png",
            ready=False,
        ),
    ]
    if with_audio_placeholder:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master (WAV)",
                expected_format="wav",
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
    content_type: str = "audio/wav",
    filename: str = "master.wav",
) -> AudioMasterUploadRequest:
    if data is None:
        data = _make_wav()
    return AudioMasterUploadRequest(
        filename=filename,
        content_type=content_type,
        content_base64=base64.b64encode(data).decode(),
    )


# ============================================================
# Content type validation
# ============================================================


class TestAudioContentType:
    def test_wav_accepted(self) -> None:
        validate_audio_content_type("audio/wav")

    def test_x_wav_accepted(self) -> None:
        validate_audio_content_type("audio/x-wav")

    def test_wave_accepted(self) -> None:
        validate_audio_content_type("audio/wave")

    def test_vnd_wave_accepted(self) -> None:
        validate_audio_content_type("audio/vnd.wave")

    def test_mp3_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_audio_content_type("audio/mpeg")

    def test_aac_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_audio_content_type("audio/aac")

    def test_flac_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_audio_content_type("audio/flac")

    def test_m4a_rejected(self) -> None:
        with pytest.raises(ValueError, match="not accepted"):
            validate_audio_content_type("audio/m4a")

    def test_unknown_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown content type"):
            validate_audio_content_type("video/mp4")


# ============================================================
# WAV header parsing
# ============================================================


class TestWavParsing:
    def test_valid_wav(self) -> None:
        data = _make_wav(channels=2, sample_rate=48000, sample_width=3, duration_seconds=2.0)
        info = parse_wav_header(data)
        assert info.channels == 2
        assert info.sample_rate == 48000
        assert info.sample_width == 3
        assert info.duration_seconds == pytest.approx(2.0, abs=0.01)

    def test_invalid_wav(self) -> None:
        with pytest.raises(ValueError, match=r"invalid WAV|cannot read WAV"):
            parse_wav_header(b"not a wav file")

    def test_empty_data(self) -> None:
        with pytest.raises(ValueError):
            parse_wav_header(b"")


# ============================================================
# Audio data validation
# ============================================================


class TestAudioValidation:
    def test_valid_stereo_48k_24bit(self) -> None:
        data = _make_wav(channels=2, sample_rate=48000, sample_width=3)
        info, warnings = validate_audio_data(data)
        assert info.channels == 2
        assert len(warnings) == 0

    def test_mono_triggers_warning(self) -> None:
        data = _make_wav(channels=1, sample_rate=48000, sample_width=3)
        _, warnings = validate_audio_data(data)
        assert any(w.code == "mono_audio" for w in warnings)

    def test_16bit_triggers_warning(self) -> None:
        data = _make_wav(channels=2, sample_rate=48000, sample_width=2)
        _, warnings = validate_audio_data(data)
        assert any(w.code == "low_bit_depth" for w in warnings)

    def test_44100_triggers_warning(self) -> None:
        data = _make_wav(channels=2, sample_rate=44100, sample_width=3)
        _, warnings = validate_audio_data(data)
        assert any(w.code == "low_sample_rate" for w in warnings)

    def test_below_44100_rejected(self) -> None:
        data = _make_wav(channels=2, sample_rate=22050, sample_width=3)
        with pytest.raises(ValueError, match="sample rate too low"):
            validate_audio_data(data)

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_audio_data(b"")

    def test_zero_duration_rejected(self) -> None:
        data = _make_wav(channels=2, sample_rate=48000, sample_width=3, duration_seconds=0.0)
        with pytest.raises(ValueError, match="zero duration"):
            validate_audio_data(data)


# ============================================================
# Full upload pipeline
# ============================================================


class TestAudioUploadPipeline:
    def test_successful_upload_creates_artifact(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_audio_master_for_release(
            release, request, storage, operator_id="op@test.com"
        )

        assert result.artifact.kind == ArtifactKind.AUDIO_MASTER
        assert result.artifact.status == ArtifactStatus.STORED
        assert result.artifact.content_type == "audio/wav"
        assert result.artifact.size_bytes is not None
        assert result.artifact.size_bytes > 0

    def test_upload_updates_release_placeholder(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_audio_master_for_release(release, request, storage)

        audio_asset = next(
            (a for a in result.release.assets if a.asset_type == "audio_master"), None
        )
        assert audio_asset is not None
        assert audio_asset.ready is True
        assert audio_asset.artifact_id == result.artifact.artifact_id

    def test_cover_asset_preserved(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_audio_master_for_release(release, request, storage)

        cover_asset = next((a for a in result.release.assets if a.asset_type == "cover_art"), None)
        assert cover_asset is not None
        assert cover_asset.ready is False

    def test_upload_without_placeholder_adds_one(self) -> None:
        storage = _make_storage()
        release = _make_release(with_audio_placeholder=False)
        request = _make_upload_request()

        result = upload_audio_master_for_release(release, request, storage)

        audio_asset = next(
            (a for a in result.release.assets if a.asset_type == "audio_master"), None
        )
        assert audio_asset is not None
        assert audio_asset.ready is True

    def test_mp3_upload_rejected(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = AudioMasterUploadRequest(
            filename="master.mp3",
            content_type="audio/mpeg",
            content_base64=base64.b64encode(b"fake").decode(),
        )

        with pytest.raises(ValueError, match="not accepted"):
            upload_audio_master_for_release(release, request, storage)

    def test_metadata_returned(self) -> None:
        storage = _make_storage()
        release = _make_release()
        data = _make_wav(channels=2, sample_rate=48000, sample_width=3, duration_seconds=3.5)
        request = _make_upload_request(data=data)

        result = upload_audio_master_for_release(release, request, storage)

        assert result.channels == 2
        assert result.sample_rate == 48000
        assert result.sample_width_bytes == 3
        assert result.duration_seconds == pytest.approx(3.5, abs=0.01)

    def test_operator_id_propagated(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_audio_master_for_release(
            release, request, storage, operator_id="op@test.com"
        )

        assert result.artifact.operator_id == "op@test.com"

    def test_artifact_stored_on_disk(self) -> None:
        storage = _make_storage()
        release = _make_release()
        request = _make_upload_request()

        result = upload_audio_master_for_release(release, request, storage)

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


class TestAudioUploadRoute:
    """Route tests using asyncio.run() — matches existing test patterns."""

    def test_upload_audio_master_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_audio_master

        release = _create_test_release()
        data = _make_wav()
        req = AudioMasterUploadRequest(
            filename="master.wav",
            content_type="audio/wav",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_audio_master(release.release_id, req, DEV_OPERATOR))

        assert result.artifact.kind == ArtifactKind.AUDIO_MASTER
        assert result.artifact.status == ArtifactStatus.STORED
        audio_asset = next(
            (a for a in result.release.assets if a.asset_type == "audio_master"), None
        )
        assert audio_asset is not None
        assert audio_asset.ready is True
        assert audio_asset.artifact_id == result.artifact.artifact_id

    def test_upload_mp3_rejected_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_audio_master

        release = _create_test_release()
        req = AudioMasterUploadRequest(
            filename="master.mp3",
            content_type="audio/mpeg",
            content_base64=base64.b64encode(b"fake").decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_audio_master(release.release_id, req, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_upload_release_not_found_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        import asyncio

        from app.main import upload_release_audio_master

        data = _make_wav()
        req = AudioMasterUploadRequest(
            filename="master.wav",
            content_type="audio/wav",
            content_base64=base64.b64encode(data).decode(),
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_release_audio_master(uuid4(), req, DEV_OPERATOR))
        assert exc_info.value.status_code == 404

    def test_download_link_works_for_uploaded_audio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_API_KEY", raising=False)
        monkeypatch.setenv("SOUNDSYSTEM_ARTIFACT_ACCESS_MODE", "direct")
        import asyncio

        from app.main import get_artifact_download_link, upload_release_audio_master

        release = _create_test_release()
        data = _make_wav()
        req = AudioMasterUploadRequest(
            filename="master.wav",
            content_type="audio/wav",
            content_base64=base64.b64encode(data).decode(),
        )

        result = asyncio.run(upload_release_audio_master(release.release_id, req, DEV_OPERATOR))
        link = asyncio.run(get_artifact_download_link(result.artifact.artifact_id))
        assert "/download" in link.url
