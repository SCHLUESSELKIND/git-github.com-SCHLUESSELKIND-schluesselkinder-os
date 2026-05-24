"""Stem pack upload pipeline — S33.

Validates and stores stem pack ZIP archives through ArtifactStorage,
then attaches the resulting ArtifactRecord to a ReleasePack asset
placeholder.

Hard rules:
- Only ZIP accepted (application/zip, application/x-zip-compressed).
- RAR, 7z, TAR rejected.
- Max 250 MB (base64 JSON upload; multipart/chunked upload deferred).
- ZIP validated via Python stdlib `zipfile` module.
- No path traversal entries (../).
- No absolute paths.
- No empty archives.
- No encrypted entries.
- Max 64 files inside.
- Max 1 GB uncompressed size.
- Allowed internal extensions: .wav, .aiff, .aif, .txt, .json, .md.
- Warn if no audio stems (.wav/.aiff/.aif).
- Warn if no manifest (manifest.json, stems.json, readme.txt).
- Warn if very large uncompressed size (>500 MB).
- No stem generation, no extraction UI, no provider calls.
"""

from __future__ import annotations

import os
import re
import zipfile
from io import BytesIO
from uuid import UUID

from app.artifact_storage import ArtifactStorage, decode_upload_content
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    ReleasePack,
    StemPackManifestEntry,
    StemPackUploadRequest,
    StemPackUploadResult,
    StemPackValidationWarning,
)

# Maximum upload size: 250 MB
MAX_STEM_PACK_SIZE_BYTES = 250 * 1024 * 1024

# Maximum number of files inside the ZIP
MAX_FILES_IN_ZIP = 64

# Maximum uncompressed size: 1 GB
MAX_UNCOMPRESSED_SIZE_BYTES = 1 * 1024 * 1024 * 1024

# Uncompressed size warning threshold: 500 MB
WARN_UNCOMPRESSED_SIZE_BYTES = 500 * 1024 * 1024

# Accepted content types for ZIP
ACCEPTED_CONTENT_TYPES = frozenset(
    {
        "application/zip",
        "application/x-zip-compressed",
    }
)

# Explicitly rejected content types
REJECTED_CONTENT_TYPES = frozenset(
    {
        "application/x-rar-compressed",
        "application/vnd.rar",
        "application/x-7z-compressed",
        "application/x-tar",
        "application/gzip",
        "application/x-gzip",
        "application/x-bzip2",
    }
)

# Allowed file extensions inside the ZIP
ALLOWED_EXTENSIONS = frozenset(
    {
        ".wav",
        ".aiff",
        ".aif",
        ".txt",
        ".json",
        ".md",
    }
)

# Audio extensions (for "no audio stems" warning)
AUDIO_EXTENSIONS = frozenset({".wav", ".aiff", ".aif"})

# Manifest filenames (case-insensitive check)
MANIFEST_FILENAMES = frozenset(
    {
        "manifest.json",
        "stems.json",
        "readme.txt",
    }
)


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename: strip path components, keep only safe chars."""
    base = os.path.basename(filename)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return safe[:200] if safe else "stems.zip"


def validate_stem_content_type(content_type: str) -> None:
    """Validate content type is an accepted archive format.

    Raises ValueError for rejected or unknown types.
    """
    if content_type in REJECTED_CONTENT_TYPES:
        raise ValueError(
            f"content type {content_type} is not accepted for stem packs. "
            f"Only ZIP archives are accepted."
        )
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise ValueError(
            f"unknown content type {content_type}. "
            f"Accepted: application/zip, application/x-zip-compressed."
        )


def validate_stem_pack_data(
    data: bytes,
) -> tuple[list[StemPackManifestEntry], list[StemPackValidationWarning], int]:
    """Validate stem pack ZIP data.

    Returns (entries, warnings, total_uncompressed_bytes).
    Raises ValueError for fatal failures.
    """
    warnings: list[StemPackValidationWarning] = []
    entries: list[StemPackManifestEntry] = []

    # Size check
    if len(data) > MAX_STEM_PACK_SIZE_BYTES:
        size_mb = len(data) / (1024 * 1024)
        raise ValueError(
            f"stem pack too large: {size_mb:.1f} MB "
            f"(max {MAX_STEM_PACK_SIZE_BYTES // (1024 * 1024)} MB). "
            f"Multipart/chunked upload for large packs is not yet available."
        )

    if len(data) == 0:
        raise ValueError("stem pack is empty (0 bytes)")

    # Validate ZIP
    buf = BytesIO(data)
    if not zipfile.is_zipfile(buf):
        raise ValueError("data is not a valid ZIP archive")

    buf.seek(0)
    try:
        zf = zipfile.ZipFile(buf, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid ZIP archive: {exc}") from exc

    with zf:
        info_list = zf.infolist()

        # Filter out directory entries
        file_entries = [info for info in info_list if not info.is_dir()]

        # Empty archive check
        if len(file_entries) == 0:
            raise ValueError("stem pack ZIP is empty (no files)")

        # Max files check
        if len(file_entries) > MAX_FILES_IN_ZIP:
            raise ValueError(
                f"stem pack contains {len(file_entries)} files (max {MAX_FILES_IN_ZIP})"
            )

        total_uncompressed = 0
        has_audio = False
        has_manifest = False

        for info in file_entries:
            fname = info.filename

            # Path traversal check
            if ".." in fname:
                raise ValueError(f"path traversal detected in ZIP entry: {fname}")

            # Absolute path check
            if fname.startswith("/") or fname.startswith("\\"):
                raise ValueError(f"absolute path detected in ZIP entry: {fname}")

            # Drive letter check (Windows paths)
            if len(fname) >= 2 and fname[1] == ":":
                raise ValueError(f"absolute path detected in ZIP entry: {fname}")

            # Encrypted entry check
            if info.flag_bits & 0x1:
                raise ValueError(f"encrypted entries are not supported: {fname}")

            # Extension check
            base = os.path.basename(fname)
            ext = ""
            if "." in base:
                ext = "." + base.rsplit(".", 1)[-1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"disallowed file type in stem pack: {fname} ({ext or 'no extension'}). "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                )

            # Track uncompressed size
            total_uncompressed += info.file_size

            # Track audio presence
            is_audio = ext in AUDIO_EXTENSIONS
            if is_audio:
                has_audio = True

            # Track manifest presence
            if base.lower() in MANIFEST_FILENAMES:
                has_manifest = True

            entries.append(
                StemPackManifestEntry(
                    filename=fname,
                    size_bytes=info.file_size,
                    extension=ext,
                    is_audio=is_audio,
                )
            )

        # Max uncompressed size check
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
            size_mb = total_uncompressed / (1024 * 1024)
            raise ValueError(
                f"stem pack uncompressed size too large: {size_mb:.0f} MB "
                f"(max {MAX_UNCOMPRESSED_SIZE_BYTES // (1024 * 1024)} MB)"
            )

        # Warning: no audio stems
        if not has_audio:
            warnings.append(
                StemPackValidationWarning(
                    code="no_audio_stems",
                    message=(
                        "Stem pack contains no audio files (.wav, .aiff, .aif). "
                        "Verify this is the correct archive."
                    ),
                )
            )

        # Warning: no manifest
        if not has_manifest:
            warnings.append(
                StemPackValidationWarning(
                    code="no_manifest",
                    message=(
                        "Stem pack does not contain a manifest file "
                        "(manifest.json, stems.json, readme.txt). "
                        "Consider adding one for documentation."
                    ),
                )
            )

        # Warning: very large uncompressed size
        if total_uncompressed > WARN_UNCOMPRESSED_SIZE_BYTES:
            size_mb = total_uncompressed / (1024 * 1024)
            warnings.append(
                StemPackValidationWarning(
                    code="large_uncompressed",
                    message=(
                        f"Stem pack uncompresses to {size_mb:.0f} MB. Verify this is intentional."
                    ),
                )
            )

    return entries, warnings, total_uncompressed


def upload_stem_pack_for_release(
    release: ReleasePack,
    request: StemPackUploadRequest,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> StemPackUploadResult:
    """Upload stem pack ZIP and attach to a release pack.

    1. Validate content type
    2. Decode base64
    3. Validate ZIP data (size, structure, extensions, etc.)
    4. Create ArtifactRecord (kind=stem_pack)
    5. Store bytes
    6. Update release pack stems_archive placeholder

    Returns StemPackUploadResult with the updated release, artifact, and metadata.
    Raises ValueError for validation failures.

    Note: This uses base64 JSON upload suitable for small/medium ZIP files.
    Large stem packs will require a future multipart/chunked upload endpoint.
    """
    # 1. Content type
    validate_stem_content_type(request.content_type)

    # 2. Decode
    data = decode_upload_content(request.content_base64)

    # 3. Validate ZIP
    entries, warnings, total_uncompressed = validate_stem_pack_data(data)

    # 4. Create artifact record
    safe_filename = _sanitize_filename(request.filename)
    artifact_request = ArtifactCreateRequest(
        kind=ArtifactKind.STEM_PACK,
        logical_path=f"releases/{release.release_id}/stems/{safe_filename}",
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
    updated_release = _attach_stem_pack_to_release(release, stored_record.artifact_id)

    return StemPackUploadResult(
        release=updated_release,
        artifact=stored_record,
        warnings=warnings,
        entries=entries,
        total_files=len(entries),
        total_uncompressed_bytes=total_uncompressed,
    )


def _attach_stem_pack_to_release(
    release: ReleasePack,
    artifact_id: UUID,
) -> ReleasePack:
    """Update the stems_archive asset placeholder with the artifact reference."""
    updated_assets = []
    found = False
    for asset in release.assets:
        if asset.asset_type == "stems_archive":
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
                asset_type="stems_archive",
                label="Stem Pack (ZIP)",
                expected_format="zip",
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
