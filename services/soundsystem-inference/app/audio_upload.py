"""Audio master upload pipeline — S32.

Validates and stores WAV audio masters through ArtifactStorage,
then attaches the resulting ArtifactRecord to a ReleasePack asset
placeholder.

Hard rules:
- Only WAV accepted (audio/wav, audio/x-wav, audio/wave, audio/vnd.wave).
- MP3, AAC, M4A, FLAC rejected.
- Max 120 MB (base64 JSON upload; chunked upload deferred to future slice).
- WAV header validated via Python stdlib `wave` module.
- Channels: 1 or 2. Mono triggers warning.
- Sample rate >= 44100 Hz. Below 48000 triggers warning.
- Sample width >= 2 bytes (16-bit). 16-bit triggers warning.
- Duration > 0. Duration > 15 min triggers warning.
- No audio generation, no mastering, no provider calls.
"""

from __future__ import annotations

import io
import os
import re
import wave
from uuid import UUID

from app.artifact_storage import ArtifactStorage, decode_upload_content
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    AudioMasterUploadRequest,
    AudioMasterUploadResult,
    AudioValidationWarning,
    ReleasePack,
)

# Maximum upload size: 120 MB
MAX_AUDIO_SIZE_BYTES = 120 * 1024 * 1024

# Accepted content types for WAV
ACCEPTED_CONTENT_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/vnd.wave",
    }
)

# Explicitly rejected content types
REJECTED_CONTENT_TYPES = frozenset(
    {
        "audio/mpeg",
        "audio/mp3",
        "audio/aac",
        "audio/mp4",
        "audio/m4a",
        "audio/x-m4a",
        "audio/flac",
        "audio/x-flac",
        "audio/ogg",
    }
)

# Minimum sample rate
MIN_SAMPLE_RATE = 44100

# Recommended sample rate
RECOMMENDED_SAMPLE_RATE = 48000

# Maximum duration before warning (seconds)
MAX_DURATION_WARN_SECONDS = 15 * 60  # 15 minutes

# Minimum sample width (bytes)
MIN_SAMPLE_WIDTH = 2  # 16-bit

# Recommended sample width (bytes)
RECOMMENDED_SAMPLE_WIDTH = 3  # 24-bit


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename: strip path components, keep only safe chars."""
    base = os.path.basename(filename)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return safe[:200] if safe else "master.wav"


def validate_audio_content_type(content_type: str) -> None:
    """Validate content type is an accepted audio format.

    Raises ValueError for rejected or unknown types.
    """
    if content_type in REJECTED_CONTENT_TYPES:
        raise ValueError(
            f"content type {content_type} is not accepted for audio master. "
            f"Only WAV files are accepted."
        )
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise ValueError(
            f"unknown content type {content_type}. "
            f"Accepted: audio/wav, audio/x-wav, audio/wave, audio/vnd.wave."
        )


class WavInfo:
    """Parsed WAV header information."""

    def __init__(
        self,
        channels: int,
        sample_rate: int,
        sample_width: int,
        n_frames: int,
        duration_seconds: float,
    ) -> None:
        self.channels = channels
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.n_frames = n_frames
        self.duration_seconds = duration_seconds


def parse_wav_header(data: bytes) -> WavInfo:
    """Parse WAV header and extract audio metadata.

    Raises ValueError if the data is not a valid WAV file.
    """
    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            duration = n_frames / sample_rate if sample_rate > 0 else 0.0
    except wave.Error as exc:
        raise ValueError(f"invalid WAV file: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"cannot read WAV header: {exc}") from exc

    return WavInfo(
        channels=channels,
        sample_rate=sample_rate,
        sample_width=sample_width,
        n_frames=n_frames,
        duration_seconds=duration,
    )


def validate_audio_data(data: bytes) -> tuple[WavInfo, list[AudioValidationWarning]]:
    """Validate audio master data: size, WAV header, channels, sample rate.

    Returns (wav_info, warnings). Raises ValueError for fatal failures.
    """
    warnings: list[AudioValidationWarning] = []

    # Size check
    if len(data) > MAX_AUDIO_SIZE_BYTES:
        size_mb = len(data) / (1024 * 1024)
        raise ValueError(
            f"audio master too large: {size_mb:.1f} MB "
            f"(max {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB). "
            f"Chunked upload for large files is not yet available."
        )

    if len(data) == 0:
        raise ValueError("audio master is empty (0 bytes)")

    # Parse WAV header
    wav_info = parse_wav_header(data)

    # Channel validation
    if wav_info.channels < 1 or wav_info.channels > 2:
        raise ValueError(
            f"unsupported channel count: {wav_info.channels}. "
            f"Only mono (1) and stereo (2) are accepted."
        )
    if wav_info.channels == 1:
        warnings.append(
            AudioValidationWarning(
                code="mono_audio",
                message="Audio master is mono (1 channel). Stereo is recommended for distribution.",
            )
        )

    # Sample rate validation
    if wav_info.sample_rate < MIN_SAMPLE_RATE:
        raise ValueError(
            f"sample rate too low: {wav_info.sample_rate} Hz (minimum {MIN_SAMPLE_RATE} Hz)"
        )
    if wav_info.sample_rate < RECOMMENDED_SAMPLE_RATE:
        warnings.append(
            AudioValidationWarning(
                code="low_sample_rate",
                message=(
                    f"Sample rate is {wav_info.sample_rate} Hz. "
                    f"48000 Hz or higher is recommended for distribution."
                ),
            )
        )

    # Sample width validation
    if wav_info.sample_width < MIN_SAMPLE_WIDTH:
        raise ValueError(f"sample width too low: {wav_info.sample_width * 8}-bit (minimum 16-bit)")
    if wav_info.sample_width < RECOMMENDED_SAMPLE_WIDTH:
        warnings.append(
            AudioValidationWarning(
                code="low_bit_depth",
                message=(
                    f"Audio is {wav_info.sample_width * 8}-bit. "
                    f"24-bit or higher is recommended for distribution masters."
                ),
            )
        )

    # Duration validation
    if wav_info.duration_seconds <= 0:
        raise ValueError("audio master has zero duration")

    if wav_info.duration_seconds > MAX_DURATION_WARN_SECONDS:
        minutes = wav_info.duration_seconds / 60
        warnings.append(
            AudioValidationWarning(
                code="long_duration",
                message=f"Audio master is {minutes:.1f} minutes. Verify this is intentional.",
            )
        )

    return wav_info, warnings


def upload_audio_master_for_release(
    release: ReleasePack,
    request: AudioMasterUploadRequest,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> AudioMasterUploadResult:
    """Upload audio master WAV and attach to a release pack.

    1. Validate content type
    2. Decode base64
    3. Validate WAV data (size, header, channels, sample rate, etc.)
    4. Create ArtifactRecord (kind=audio_master)
    5. Store bytes
    6. Update release pack audio_master placeholder

    Returns AudioMasterUploadResult with the updated release, artifact, and metadata.
    Raises ValueError for validation failures.
    """
    # 1. Content type
    validate_audio_content_type(request.content_type)

    # 2. Decode
    data = decode_upload_content(request.content_base64)

    # 3. Validate WAV
    wav_info, warnings = validate_audio_data(data)

    # 4. Create artifact record
    safe_filename = _sanitize_filename(request.filename)
    artifact_request = ArtifactCreateRequest(
        kind=ArtifactKind.AUDIO_MASTER,
        logical_path=f"releases/{release.release_id}/audio/{safe_filename}",
        content_type=request.content_type,
        source_entity_type="release_pack",
        source_entity_id=str(release.release_id),
    )
    record = storage.create_record(artifact_request, operator_id=operator_id)

    # 5. Store bytes
    stored_record: ArtifactRecord = storage.store_bytes(
        record.artifact_id,
        data,
        content_type=request.content_type,
    )

    # 6. Update release asset placeholder
    updated_release = _attach_audio_master_to_release(release, stored_record.artifact_id)

    return AudioMasterUploadResult(
        release=updated_release,
        artifact=stored_record,
        warnings=warnings,
        channels=wav_info.channels,
        sample_rate=wav_info.sample_rate,
        sample_width_bytes=wav_info.sample_width,
        duration_seconds=wav_info.duration_seconds,
    )


def _attach_audio_master_to_release(
    release: ReleasePack,
    artifact_id: UUID,
) -> ReleasePack:
    """Update the audio_master asset placeholder with the artifact reference."""
    updated_assets = []
    found = False
    for asset in release.assets:
        if asset.asset_type == "audio_master":
            updated_assets.append(
                asset.model_copy(
                    update={
                        "ready": True,
                        "artifact_id": artifact_id,
                    }
                )
            )
            found = True
        else:
            updated_assets.append(asset)

    if not found:
        from app.schemas import ReleaseAssetPlaceholder

        updated_assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master (WAV)",
                expected_format="wav",
                ready=True,
                artifact_id=artifact_id,
            )
        )

    from datetime import datetime, timezone

    return release.model_copy(
        update={
            "assets": updated_assets,
            "updated_at": datetime.now(timezone.utc),
        }
    )
