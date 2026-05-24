"""Artifact Bridge — S28.

Connects existing mock artifact producers (ExportPack, MusicRouter,
SoundGraph, ReleasePack) to the ArtifactStorage layer from S27.

Each bridge function:
- Creates ArtifactRecord(s) for the generated contract artifacts.
- Stores JSON manifests as real bytes when applicable.
- Preserves the original component/mock path as the logical_path.
- Returns a list of ArtifactRecords created.
- Never deletes anything.

Hard rules:
- No fake stored audio — only JSON metadata/manifests get real bytes.
- Mock paths (e.g. /tmp/snuffraga/...) are recorded as logical_path but
  never written to disk as audio.
- All functions are synchronous, pure (except storage side-effects), and
  independently testable.
"""

from __future__ import annotations

import json

from app.artifact_storage import ArtifactStorage
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    ExportPack,
    MusicJob,
    MusicJobStatus,
    ReleasePack,
    SoundGraphArrangement,
)


def record_artifacts_for_export_pack(
    pack: ExportPack,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> list[ArtifactRecord]:
    """Create ArtifactRecords for every component in an ExportPack.

    For each component:
    - Creates a PLANNED record with the component's mock path as logical_path.
    - For JSON-serialisable metadata components (music_job, lyrics_version,
      soundgraph_arrangement, output_provenance), stores the pack manifest
      as real bytes.

    The pack-level manifest JSON is always stored as a real artifact.
    """
    records: list[ArtifactRecord] = []

    # 1. Register each component as a planned artifact
    for comp in pack.components:
        kind = _component_type_to_kind(comp.component_type)
        record = storage.create_record(
            ArtifactCreateRequest(
                kind=kind,
                logical_path=comp.path,
                content_type=_content_type_for_component(comp.component_type),
                source_entity_type="export_pack",
                source_entity_id=pack.pack_id,
                provenance_id=pack.provenance_id,
            ),
            operator_id=operator_id,
        )
        records.append(record)

    # 2. Store the pack manifest itself as a real JSON artifact
    manifest_json = pack.model_dump_json(indent=2).encode("utf-8")
    manifest_record = storage.create_record(
        ArtifactCreateRequest(
            kind=ArtifactKind.MANIFEST,
            logical_path=f"export-pack/{pack.pack_id}/manifest.json",
            content_type="application/json",
            source_entity_type="export_pack",
            source_entity_id=pack.pack_id,
            provenance_id=pack.provenance_id,
        ),
        operator_id=operator_id,
    )
    stored_manifest = storage.store_bytes(
        manifest_record.artifact_id,
        manifest_json,
        content_type="application/json",
    )
    records.append(stored_manifest)

    return records


def record_artifact_for_soundgraph(
    arrangement: SoundGraphArrangement,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> list[ArtifactRecord]:
    """Create an ArtifactRecord for a compiled SoundGraph arrangement.

    Stores the full arrangement JSON as real bytes.
    """
    records: list[ArtifactRecord] = []

    arrangement_json = arrangement.model_dump_json(indent=2).encode("utf-8")
    record = storage.create_record(
        ArtifactCreateRequest(
            kind=ArtifactKind.SOUNDGRAPH,
            logical_path=f"soundgraph/{arrangement.arrangement_id}/arrangement.json",
            content_type="application/json",
            source_entity_type="soundgraph_arrangement",
            source_entity_id=arrangement.arrangement_id,
        ),
        operator_id=operator_id,
    )
    stored = storage.store_bytes(
        record.artifact_id,
        arrangement_json,
        content_type="application/json",
    )
    records.append(stored)

    return records


def record_artifacts_for_music_job(
    job: MusicJob,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> list[ArtifactRecord]:
    """Create ArtifactRecords for a completed MusicJob's artifacts.

    For each MusicArtifactManifest on the job:
    - Audio artifacts (*.wav) → PLANNED only (no fake audio stored).
    - JSON manifests (*.json) → PLANNED only (mock path recorded).

    Additionally stores a job-level manifest JSON with real bytes.

    Only processes COMPLETED jobs — returns empty list otherwise.
    """
    if job.status != MusicJobStatus.COMPLETED:
        return []

    records: list[ArtifactRecord] = []

    for artifact in job.artifacts:
        kind = _music_artifact_type_to_kind(artifact.artifact_type.value)
        record = storage.create_record(
            ArtifactCreateRequest(
                kind=kind,
                logical_path=artifact.path,
                content_type=_content_type_for_path(artifact.path),
                source_entity_type="music_job",
                source_entity_id=job.job_id,
                provenance_id=job.provenance_id,
            ),
            operator_id=operator_id,
        )
        records.append(record)

    # Store job manifest as real JSON bytes
    job_manifest = {
        "job_id": str(job.job_id),
        "intent": job.intent.value,
        "title": job.title,
        "status": job.status.value,
        "artifact_count": len(job.artifacts),
        "artifacts": [
            {
                "type": a.artifact_type.value,
                "path": a.path,
                "format": a.format,
                "duration_seconds": a.duration_seconds,
            }
            for a in job.artifacts
        ],
        "provenance_id": str(job.provenance_id) if job.provenance_id else None,
    }
    manifest_bytes = json.dumps(job_manifest, indent=2).encode("utf-8")
    manifest_record = storage.create_record(
        ArtifactCreateRequest(
            kind=ArtifactKind.MANIFEST,
            logical_path=f"music-job/{job.job_id}/manifest.json",
            content_type="application/json",
            source_entity_type="music_job",
            source_entity_id=job.job_id,
            provenance_id=job.provenance_id,
        ),
        operator_id=operator_id,
    )
    stored_manifest = storage.store_bytes(
        manifest_record.artifact_id,
        manifest_bytes,
        content_type="application/json",
    )
    records.append(stored_manifest)

    return records


def record_artifacts_for_release_pack(
    release: ReleasePack,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> list[ArtifactRecord]:
    """Create ArtifactRecords for a ReleasePack.

    Stores the full release manifest JSON as real bytes.
    Asset placeholders are registered as PLANNED artifacts.
    """
    records: list[ArtifactRecord] = []

    # 1. Register each asset placeholder
    for asset in release.assets:
        kind = _release_asset_to_kind(asset.asset_type)
        logical_path = (
            asset.path
            if asset.path
            else f"release/{release.release_id}/{asset.asset_type}.{asset.expected_format}"
        )
        record = storage.create_record(
            ArtifactCreateRequest(
                kind=kind,
                logical_path=logical_path,
                content_type=_content_type_for_format(asset.expected_format),
                source_entity_type="release_pack",
                source_entity_id=release.release_id,
            ),
            operator_id=operator_id,
        )
        records.append(record)

    # 2. Store the release manifest as real JSON bytes
    release_json = release.model_dump_json(indent=2).encode("utf-8")
    manifest_record = storage.create_record(
        ArtifactCreateRequest(
            kind=ArtifactKind.MANIFEST,
            logical_path=f"release/{release.release_id}/manifest.json",
            content_type="application/json",
            source_entity_type="release_pack",
            source_entity_id=release.release_id,
        ),
        operator_id=operator_id,
    )
    stored_manifest = storage.store_bytes(
        manifest_record.artifact_id,
        release_json,
        content_type="application/json",
    )
    records.append(stored_manifest)

    return records


# ---------- Private helpers ----------


def _component_type_to_kind(component_type: str) -> ArtifactKind:
    """Map ExportPackComponent.component_type to ArtifactKind."""
    mapping: dict[str, ArtifactKind] = {
        "music_job": ArtifactKind.MUSIC_JOB,
        "lyrics_version": ArtifactKind.LYRICS,
        "soundgraph_arrangement": ArtifactKind.SOUNDGRAPH,
        "output_provenance": ArtifactKind.PROVENANCE,
    }
    # artifact_* types from music router artifacts
    if component_type.startswith("artifact_"):
        sub = component_type.removeprefix("artifact_")
        sub_mapping: dict[str, ArtifactKind] = {
            "loop": ArtifactKind.AUDIO_MIX,
            "full_mix": ArtifactKind.AUDIO_MIX,
            "stem_pack": ArtifactKind.STEM_PACK,
            "dub_fx": ArtifactKind.AUDIO_MIX,
            "master": ArtifactKind.AUDIO_MIX,
            "prompt_manifest": ArtifactKind.MANIFEST,
        }
        return sub_mapping.get(sub, ArtifactKind.OTHER)
    return mapping.get(component_type, ArtifactKind.OTHER)


def _music_artifact_type_to_kind(artifact_type: str) -> ArtifactKind:
    """Map MusicArtifactType value to ArtifactKind."""
    mapping: dict[str, ArtifactKind] = {
        "loop": ArtifactKind.AUDIO_MIX,
        "full_mix": ArtifactKind.AUDIO_MIX,
        "stem_pack": ArtifactKind.STEM_PACK,
        "dub_fx": ArtifactKind.AUDIO_MIX,
        "master": ArtifactKind.AUDIO_MIX,
        "prompt_manifest": ArtifactKind.MANIFEST,
    }
    return mapping.get(artifact_type, ArtifactKind.OTHER)


def _release_asset_to_kind(asset_type: str) -> ArtifactKind:
    """Map ReleaseAssetPlaceholder.asset_type to ArtifactKind."""
    mapping: dict[str, ArtifactKind] = {
        "cover_art": ArtifactKind.COVER_ART,
        "audio_master": ArtifactKind.AUDIO_MIX,
        "audio_preview": ArtifactKind.AUDIO_MIX,
        "stems_archive": ArtifactKind.STEM_PACK,
    }
    return mapping.get(asset_type, ArtifactKind.OTHER)


def _content_type_for_component(component_type: str) -> str:
    """Return a sensible content-type for a component type."""
    if component_type.startswith("artifact_"):
        sub = component_type.removeprefix("artifact_")
        if sub == "prompt_manifest":
            return "application/json"
        return "audio/wav"
    json_types = {"music_job", "lyrics_version", "soundgraph_arrangement", "output_provenance"}
    if component_type in json_types:
        return "application/json"
    return "application/octet-stream"


def _content_type_for_path(path: str) -> str:
    """Infer content-type from file path."""
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".wav"):
        return "audio/wav"
    if path.endswith(".mp3"):
        return "audio/mpeg"
    return "application/octet-stream"


def _content_type_for_format(fmt: str) -> str:
    """Infer content-type from expected format string."""
    mapping: dict[str, str] = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "zip": "application/zip",
        "json": "application/json",
    }
    return mapping.get(fmt.lower(), "application/octet-stream")
