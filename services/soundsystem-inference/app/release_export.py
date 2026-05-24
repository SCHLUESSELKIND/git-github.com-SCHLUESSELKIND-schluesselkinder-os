"""Release Export ZIP Builder — S34.

Builds a deterministic, distributable ZIP bundle from a ReleasePack's
uploaded assets (cover art, audio master, stem pack) plus release
metadata, social copy, and a manifest.

The export ZIP has a fixed folder structure:

    release/
      cover/
        <cover filename>
      audio/
        <master filename>
      stems/
        <stems filename>
      metadata/
        release.json
        social-copy.json
        manifest.json

Hard rules:
- No provider calls.
- No stem extraction — stems.zip is included as-is.
- No arbitrary filesystem access.
- No path traversal in export filenames.
- Export allowed with partial assets (warnings issued).
- Export fails if ALL assets are missing.
- Manifest includes artifact checksums and sizes.
- Stored via ArtifactStorage as export_pack kind.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID, uuid4

from app.artifact_storage import ArtifactStorage
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    ArtifactStatus,
    ReleaseAssetPlaceholder,
    ReleaseExportEntry,
    ReleaseExportResult,
    ReleaseExportStatus,
    ReleaseExportWarning,
    ReleasePack,
)


def _sanitize_export_filename(filename: str) -> str:
    """Sanitize a filename for inclusion in the export ZIP.

    Strips path components, keeps only safe characters.
    """
    base = os.path.basename(filename)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return safe[:200] if safe else "file"


def _asset_by_type(release: ReleasePack, asset_type: str) -> ReleaseAssetPlaceholder | None:
    """Find a ready asset placeholder by type."""
    for asset in release.assets:
        if asset.asset_type == asset_type and asset.ready and asset.artifact_id:
            return asset
    return None


def _get_artifact_bytes(
    storage: ArtifactStorage, artifact_id: UUID
) -> tuple[bytes, ArtifactRecord] | None:
    """Load artifact bytes from storage. Returns None if not found/stored.

    Supports LocalArtifactStorage (get_file_path) and S3ArtifactStorage
    (get_bytes). Falls back gracefully if neither method is available.
    """
    record = storage.get_record(artifact_id)
    if record is None or record.status != ArtifactStatus.STORED:
        return None

    # Try LocalArtifactStorage.get_file_path first
    get_file_path = getattr(storage, "get_file_path", None)
    if get_file_path is not None:
        file_path = get_file_path(artifact_id)
        if file_path is not None and file_path.exists():
            return file_path.read_bytes(), record

    # Try S3ArtifactStorage.get_bytes
    get_bytes = getattr(storage, "get_bytes", None)
    if get_bytes is not None:
        data = get_bytes(artifact_id)
        if data is not None:
            return data, record

    return None


def _extension_from_content_type(content_type: str) -> str:
    """Map content type to file extension."""
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/wave": ".wav",
        "audio/vnd.wave": ".wav",
        "application/zip": ".zip",
        "application/x-zip-compressed": ".zip",
    }
    return mapping.get(content_type, "")


def collect_release_assets(
    release: ReleasePack,
    storage: ArtifactStorage,
) -> tuple[
    dict[str, tuple[bytes, ArtifactRecord, str]],
    list[ReleaseExportWarning],
]:
    """Collect all available release assets from storage.

    Returns:
        (collected_assets, warnings)

    collected_assets: dict mapping asset_type to (bytes, record, zip_path).
    warnings: list of warnings for missing assets.
    """
    warnings: list[ReleaseExportWarning] = []
    collected: dict[str, tuple[bytes, ArtifactRecord, str]] = {}

    # Cover art
    cover_asset = _asset_by_type(release, "cover_art")
    if cover_asset and cover_asset.artifact_id:
        result = _get_artifact_bytes(storage, cover_asset.artifact_id)
        if result:
            data, record = result
            ext = _extension_from_content_type(record.content_type) or ".png"
            collected["cover_art"] = (data, record, f"release/cover/cover{ext}")
        else:
            warnings.append(
                ReleaseExportWarning(
                    code="cover_bytes_missing",
                    message="Cover art artifact exists but bytes could not be loaded.",
                )
            )
    else:
        warnings.append(
            ReleaseExportWarning(
                code="cover_missing",
                message="No cover art uploaded. Export will not include cover artwork.",
            )
        )

    # Audio master
    audio_asset = _asset_by_type(release, "audio_master")
    if audio_asset and audio_asset.artifact_id:
        result = _get_artifact_bytes(storage, audio_asset.artifact_id)
        if result:
            data, record = result
            collected["audio_master"] = (data, record, "release/audio/master.wav")
        else:
            warnings.append(
                ReleaseExportWarning(
                    code="audio_bytes_missing",
                    message="Audio master artifact exists but bytes could not be loaded.",
                )
            )
    else:
        warnings.append(
            ReleaseExportWarning(
                code="audio_missing",
                message="No audio master uploaded. Export will not include audio master.",
            )
        )

    # Stem pack
    stems_asset = _asset_by_type(release, "stems_archive")
    if stems_asset and stems_asset.artifact_id:
        result = _get_artifact_bytes(storage, stems_asset.artifact_id)
        if result:
            data, record = result
            collected["stems_archive"] = (data, record, "release/stems/stems.zip")
        else:
            warnings.append(
                ReleaseExportWarning(
                    code="stems_bytes_missing",
                    message="Stem pack artifact exists but bytes could not be loaded.",
                )
            )
    else:
        warnings.append(
            ReleaseExportWarning(
                code="stems_missing",
                message="No stem pack uploaded. Export will not include stems.",
            )
        )

    return collected, warnings


def build_release_manifest(
    release: ReleasePack,
    entries: list[ReleaseExportEntry],
) -> dict:
    """Build the manifest.json content for the export ZIP."""
    return {
        "version": "1.0",
        "release_id": str(release.release_id),
        "pack_id": str(release.pack_id),
        "title": release.title,
        "artist": release.artist,
        "status": release.status.value,
        "genre": release.genre,
        "bpm": release.bpm,
        "key_signature": release.key_signature,
        "duration_seconds": release.duration_seconds,
        "compliance_passed": release.compliance_passed,
        "created_at": release.created_at.isoformat(),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "entries": [
            {
                "path": e.path,
                "source_asset_type": e.source_asset_type,
                "size_bytes": e.size_bytes,
                "checksum_sha256": e.checksum_sha256,
                "content_type": e.content_type,
            }
            for e in entries
        ],
    }


def build_release_export_zip(
    release: ReleasePack,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> ReleaseExportResult:
    """Build a release export ZIP from a ReleasePack's uploaded assets.

    1. Collect available assets from ArtifactStorage
    2. Build ZIP in memory with deterministic folder structure
    3. Include release metadata + social copy + manifest
    4. Store export ZIP as an ArtifactRecord (kind=export_pack)
    5. Return result with entries, warnings, artifact reference

    Raises ValueError if all assets are missing (nothing to export).
    """
    export_id = uuid4()

    # 1. Collect assets
    collected, warnings = collect_release_assets(release, storage)

    if len(collected) == 0:
        raise ValueError(
            "Cannot build release export: no assets uploaded. "
            "Upload at least one asset (cover, audio master, or stem pack) first."
        )

    # 2. Build ZIP
    zip_buf = BytesIO()
    entries: list[ReleaseExportEntry] = []

    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add collected asset files
        for asset_type, (data, record, zip_path) in collected.items():
            zf.writestr(zip_path, data)
            checksum = hashlib.sha256(data).hexdigest()
            entries.append(
                ReleaseExportEntry(
                    path=zip_path,
                    source_asset_type=asset_type,
                    size_bytes=len(data),
                    checksum_sha256=checksum,
                    content_type=record.content_type,
                )
            )

        # 3. Add metadata files
        # release.json
        release_json = json.dumps(
            {
                "release_id": str(release.release_id),
                "pack_id": str(release.pack_id),
                "title": release.title,
                "artist": release.artist,
                "status": release.status.value,
                "description": release.description,
                "genre": release.genre,
                "bpm": release.bpm,
                "key_signature": release.key_signature,
                "duration_seconds": release.duration_seconds,
                "compliance_passed": release.compliance_passed,
                "operator_id": release.operator_id,
                "created_at": release.created_at.isoformat(),
                "updated_at": release.updated_at.isoformat(),
            },
            indent=2,
        )
        release_json_bytes = release_json.encode("utf-8")
        zf.writestr("release/metadata/release.json", release_json_bytes)
        entries.append(
            ReleaseExportEntry(
                path="release/metadata/release.json",
                source_asset_type="metadata",
                size_bytes=len(release_json_bytes),
                checksum_sha256=hashlib.sha256(release_json_bytes).hexdigest(),
                content_type="application/json",
            )
        )

        # social-copy.json
        social_copy_json = json.dumps(
            release.social_copy.model_dump(mode="json"),
            indent=2,
        )
        social_copy_bytes = social_copy_json.encode("utf-8")
        zf.writestr("release/metadata/social-copy.json", social_copy_bytes)
        entries.append(
            ReleaseExportEntry(
                path="release/metadata/social-copy.json",
                source_asset_type="metadata",
                size_bytes=len(social_copy_bytes),
                checksum_sha256=hashlib.sha256(social_copy_bytes).hexdigest(),
                content_type="application/json",
            )
        )

        # manifest.json (built last, includes all entries so far)
        manifest = build_release_manifest(release, entries)
        manifest_json = json.dumps(manifest, indent=2)
        manifest_bytes = manifest_json.encode("utf-8")
        zf.writestr("release/metadata/manifest.json", manifest_bytes)
        entries.append(
            ReleaseExportEntry(
                path="release/metadata/manifest.json",
                source_asset_type="manifest",
                size_bytes=len(manifest_bytes),
                checksum_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                content_type="application/json",
            )
        )

    zip_data = zip_buf.getvalue()

    # 4. Store export ZIP
    safe_title = _sanitize_export_filename(release.title)
    artifact_request = ArtifactCreateRequest(
        kind=ArtifactKind.EXPORT_PACK,
        logical_path=f"releases/{release.release_id}/export/{safe_title}.zip",
        content_type="application/zip",
        source_entity_type="release_pack",
        source_entity_id=str(release.release_id),
    )
    record = storage.create_record(artifact_request, operator_id=operator_id)
    stored_record: ArtifactRecord = storage.store_bytes(
        record.artifact_id,
        zip_data,
        content_type="application/zip",
    )

    total_size = sum(e.size_bytes for e in entries)

    return ReleaseExportResult(
        export_id=export_id,
        release_id=release.release_id,
        artifact=stored_record,
        status=ReleaseExportStatus.COMPLETED,
        entries=entries,
        warnings=warnings,
        total_files=len(entries),
        total_size_bytes=total_size,
    )
