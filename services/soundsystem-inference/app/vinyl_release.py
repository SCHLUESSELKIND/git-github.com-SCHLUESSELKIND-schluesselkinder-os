"""Vinyl Release Builder Logic (S46).

Builds a VinylReleaseObject from a ReleasePack by inferring provider group,
evaluating readiness, and building export payloads for manual handoff.

Vinyl is not normal merch. It is a collector artifact.
elasticStage is for SoundCloud vinyl-on-demand / scalable VOD.
DISC_ARCHIVE / lathe-cut vendors are for hand-cut collector editions.
The OS remains source of truth. External vendors are destinations.

No real elasticStage API calls.
No real DISC_ARCHIVE/Vinylograph order placement.
No payment/checkout. No automatic manufacturing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    ReleasePack,
    VinylEditionType,
    VinylExportPayload,
    VinylFormat,
    VinylProviderGroup,
    VinylReadinessItem,
    VinylReleaseObject,
    VinylReleaseStatus,
    VinylTrackListing,
)


# ---------- Provider inference ----------


def infer_provider_group(
    format: VinylFormat,
    edition_type: VinylEditionType,
) -> VinylProviderGroup:
    """Infer the default provider group from format and edition type.

    - dubplate/lathe_cut → disc_archive
    - limited_numbered / collector_box → manual_collector
    - vinyl_on_demand / white_label → elastic_stage
    """
    if format in (VinylFormat.DUBPLATE, VinylFormat.LATHE_CUT):
        return VinylProviderGroup.DISC_ARCHIVE

    if edition_type in (VinylEditionType.LIMITED_NUMBERED, VinylEditionType.COLLECTOR_BOX):
        return VinylProviderGroup.MANUAL_COLLECTOR

    return VinylProviderGroup.ELASTIC_STAGE


# ---------- Readiness evaluation ----------


def evaluate_vinyl_readiness(
    release: ReleasePack,
    vinyl: VinylReleaseObject,
) -> list[VinylReadinessItem]:
    """Evaluate readiness checks for a vinyl release."""
    items: list[VinylReadinessItem] = []

    # Cover exists
    cover_ready = any(a.asset_type == "cover_art" and a.ready for a in release.assets)
    items.append(
        VinylReadinessItem(
            code="cover_exists",
            label="Cover artwork uploaded",
            passed=cover_ready,
            warning="" if cover_ready else "Cover art required for vinyl sleeve.",
        )
    )

    # Audio master exists
    audio_ready = any(a.asset_type == "audio_master" and a.ready for a in release.assets)
    items.append(
        VinylReadinessItem(
            code="audio_master_exists",
            label="Audio master uploaded",
            passed=audio_ready,
            warning="" if audio_ready else "Audio master required for vinyl cutting.",
        )
    )

    # Release title
    title_ok = bool(release.title and len(release.title.strip()) >= 2)
    items.append(
        VinylReadinessItem(
            code="title_exists",
            label="Release title set",
            passed=title_ok,
            warning="" if title_ok else "Release title required.",
        )
    )

    # Artist
    artist_ok = bool(release.artist and len(release.artist.strip()) >= 1)
    items.append(
        VinylReadinessItem(
            code="artist_exists",
            label="Artist name set",
            passed=artist_ok,
            warning="" if artist_ok else "Artist name required.",
        )
    )

    # Duration warning
    has_duration = release.duration_seconds is not None
    items.append(
        VinylReadinessItem(
            code="duration_known",
            label="Duration known",
            passed=has_duration,
            warning="" if has_duration else "Duration unknown. Verify runtime fits vinyl format.",
        )
    )

    # Pressing quantity for limited editions
    needs_quantity = vinyl.edition_type in (
        VinylEditionType.LIMITED_NUMBERED,
        VinylEditionType.COLLECTOR_BOX,
    )
    quantity_ok = not needs_quantity or (
        vinyl.pressing_quantity is not None and vinyl.pressing_quantity > 0
    )
    items.append(
        VinylReadinessItem(
            code="pressing_quantity",
            label="Pressing quantity set",
            passed=quantity_ok,
            warning=""
            if quantity_ok
            else "Pressing quantity required for limited/collector editions.",
        )
    )

    # Export ZIP
    has_export = any(a.asset_type == "stems_archive" and a.ready for a in release.assets)
    items.append(
        VinylReadinessItem(
            code="export_available",
            label="Export archive available",
            passed=has_export,
            warning="" if has_export else "Export archive missing. Build release export first.",
        )
    )

    # Compliance / provenance
    compliance_ok = release.compliance_passed
    items.append(
        VinylReadinessItem(
            code="compliance_passed",
            label="Compliance checklist passed",
            passed=compliance_ok,
            warning="" if compliance_ok else "Copyright/provenance not cleared.",
        )
    )

    return items


# ---------- Builder ----------


def build_vinyl_release_from_release(
    release: ReleasePack,
    *,
    format: VinylFormat = VinylFormat.TWELVE_INCH,
    edition_type: VinylEditionType = VinylEditionType.VINYL_ON_DEMAND,
    pressing_quantity: int | None = None,
    numbered: bool = False,
    operator_id: str | None = None,
    notes: str = "",
) -> VinylReleaseObject:
    """Build a vinyl release object from a ReleasePack.

    Infers provider group, builds default track listing, evaluates readiness.
    No manufacturing. No vendor API calls. Manual handoff only.
    """
    provider = infer_provider_group(format, edition_type)

    # Build default Side A track listing from release title
    side_a = [
        VinylTrackListing(
            position=1,
            title=release.title,
            duration_seconds=release.duration_seconds,
        )
    ]

    # Find artifact IDs from release assets
    cover_artifact_id = None
    audio_master_artifact_id = None
    for asset in release.assets:
        if asset.asset_type == "cover_art" and asset.artifact_id:
            cover_artifact_id = asset.artifact_id
        if asset.asset_type == "audio_master" and asset.artifact_id:
            audio_master_artifact_id = asset.artifact_id

    vinyl = VinylReleaseObject(
        vinyl_id=uuid4(),
        release_id=release.release_id,
        title=release.title,
        artist=release.artist,
        provider_group=provider,
        status=VinylReleaseStatus.DRAFT,
        format=format,
        edition_type=edition_type,
        pressing_quantity=pressing_quantity,
        numbered=numbered,
        side_a_tracks=side_a,
        side_b_tracks=[],
        cover_artifact_id=cover_artifact_id,
        audio_master_artifact_id=audio_master_artifact_id,
        notes=notes,
        created_by=operator_id,
    )

    # Evaluate readiness
    readiness = evaluate_vinyl_readiness(release, vinyl)
    warnings = [item.warning for item in readiness if not item.passed and item.warning]

    vinyl = vinyl.model_copy(update={"readiness_items": readiness, "warnings": warnings})

    return vinyl


# ---------- Export payload ----------


def build_vinyl_export_payload(vinyl: VinylReleaseObject) -> VinylExportPayload:
    """Build an export payload for manual provider handoff.

    No real API calls. No order placement. This is a read-model export
    for operator copy/paste or future automation.
    """
    passed = sum(1 for r in vinyl.readiness_items if r.passed)
    total = len(vinyl.readiness_items)
    readiness_summary = f"{passed}/{total} checks passed"

    return VinylExportPayload(
        vinyl_id=vinyl.vinyl_id,
        release_id=vinyl.release_id,
        title=vinyl.title,
        artist=vinyl.artist,
        provider_group=vinyl.provider_group,
        format=vinyl.format,
        edition_type=vinyl.edition_type,
        pressing_quantity=vinyl.pressing_quantity,
        numbered=vinyl.numbered,
        side_a_tracks=vinyl.side_a_tracks,
        side_b_tracks=vinyl.side_b_tracks,
        cover_artifact_id=vinyl.cover_artifact_id,
        audio_master_artifact_id=vinyl.audio_master_artifact_id,
        readiness_summary=readiness_summary,
        warnings=vinyl.warnings,
    )


# ---------- Status update ----------


def update_vinyl_status(
    vinyl: VinylReleaseObject,
    new_status: VinylReleaseStatus,
) -> VinylReleaseObject:
    """Update vinyl release status with timestamp.

    No real vendor notifications. Status is local only.
    """
    return vinyl.model_copy(
        update={
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
        }
    )
