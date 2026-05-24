"""Export Pack / Project Library — S17.

Bundles a completed MusicJob with its full lineage (Lyrics, SoundGraph,
Provenance, Artifacts) into a single exportable project pack, and maintains
an in-memory project library for catalogue browsing.

Pure logic — no external calls, no database, fully deterministic.
"""

from __future__ import annotations

import re
from uuid import uuid4

from app.schemas import (
    ExportPack,
    ExportPackComponent,
    ExportPackStatus,
    LyricsVersion,
    MusicJob,
    MusicJobStatus,
    OutputProvenance,
    ProjectLibraryEntry,
    SoundGraphArrangement,
)


def _slugify(title: str) -> str:
    """Convert a title into a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:120] or "untitled"


def build_export_pack(
    music_job: MusicJob,
    *,
    lyrics_version: LyricsVersion | None = None,
    arrangement: SoundGraphArrangement | None = None,
    provenance: OutputProvenance | None = None,
    title: str | None = None,
    operator_id: str | None = None,
    notes: str | None = None,
) -> ExportPack:
    """Build an ExportPack from a completed MusicJob and its lineage.

    The job must be in COMPLETED status. All other inputs are optional —
    the pack includes whatever is available.
    """
    if music_job.status != MusicJobStatus.COMPLETED:
        raise ValueError(f"music_job must be COMPLETED, got {music_job.status.value}")

    pack_title = title or music_job.title
    components: list[ExportPackComponent] = []

    # Always include the music job itself
    components.append(
        ExportPackComponent(
            component_type="music_job",
            component_id=music_job.job_id,
            label=f"Music Job: {music_job.title}",
            path=f"/tmp/snuffraga/export/{_slugify(pack_title)}/music_job.json",
        )
    )

    # Include each artifact
    for i, artifact in enumerate(music_job.artifacts):
        components.append(
            ExportPackComponent(
                component_type=f"artifact_{artifact.artifact_type.value}",
                component_id=music_job.job_id,
                label=f"Artifact: {artifact.artifact_type.value} ({artifact.format})",
                path=artifact.path,
            )
        )

    # Include lyrics version if available
    if lyrics_version is not None:
        components.append(
            ExportPackComponent(
                component_type="lyrics_version",
                component_id=lyrics_version.id,
                label=f"Lyrics v{lyrics_version.version}",
                path=f"/tmp/snuffraga/export/{_slugify(pack_title)}/lyrics.json",
            )
        )

    # Include arrangement if available
    if arrangement is not None:
        components.append(
            ExportPackComponent(
                component_type="soundgraph_arrangement",
                component_id=arrangement.arrangement_id,
                label=f"SoundGraph ({arrangement.total_bars} bars, {arrangement.bpm} BPM)",
                path=f"/tmp/snuffraga/export/{_slugify(pack_title)}/soundgraph.json",
            )
        )

    # Include provenance if available
    if provenance is not None:
        components.append(
            ExportPackComponent(
                component_type="output_provenance",
                component_id=provenance.provenance_id,
                label=f"Provenance ({provenance.commercial_status.value})",
                path=f"/tmp/snuffraga/export/{_slugify(pack_title)}/provenance.json",
            )
        )

    return ExportPack(
        pack_id=uuid4(),
        title=pack_title,
        status=ExportPackStatus.COMPLETE,
        music_job_id=music_job.job_id,
        lyrics_version_id=lyrics_version.id if lyrics_version else None,
        arrangement_id=arrangement.arrangement_id if arrangement else None,
        provenance_id=provenance.provenance_id if provenance else None,
        components=components,
        total_components=len(components),
        estimated_duration_seconds=(arrangement and _estimate_from_arrangement(arrangement))
        or None,
        bpm=arrangement.bpm if arrangement else music_job.router_decision and None,
        key_signature=arrangement.key_signature if arrangement else None,
        intent=music_job.intent,
        operator_id=operator_id or music_job.operator_id,
        notes=notes,
    )


def _estimate_from_arrangement(arrangement: SoundGraphArrangement) -> float:
    """Estimate duration in seconds from arrangement bar count."""
    numerator = int(arrangement.time_signature.split("/")[0])
    return arrangement.total_bars * numerator / arrangement.bpm * 60


def build_library_entry(pack: ExportPack) -> ProjectLibraryEntry:
    """Create a ProjectLibraryEntry from an ExportPack."""
    return ProjectLibraryEntry(
        entry_id=uuid4(),
        pack_id=pack.pack_id,
        title=pack.title,
        slug=_slugify(pack.title),
        intent=pack.intent,
        status=pack.status,
        bpm=pack.bpm,
        key_signature=pack.key_signature,
        estimated_duration_seconds=pack.estimated_duration_seconds,
        component_count=pack.total_components,
        artifact_count=sum(1 for c in pack.components if c.component_type.startswith("artifact_")),
        has_lyrics=pack.lyrics_version_id is not None,
        has_arrangement=pack.arrangement_id is not None,
        has_provenance=pack.provenance_id is not None,
        operator_id=pack.operator_id,
    )


# Backwards-compatible alias — tests and older code import this name.
# The actual implementation now lives in library_repository.py.
from app.library_repository import InMemoryLibraryRepository as ProjectLibraryRepository  # noqa: F401, E402, E501
