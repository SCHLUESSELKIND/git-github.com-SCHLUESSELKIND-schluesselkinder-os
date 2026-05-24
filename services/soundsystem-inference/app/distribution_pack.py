"""Ditto Music Distribution Pack Builder Logic (S37).

Converts a ReleasePack into a distribution handoff pack for Ditto Music.
No real Ditto API calls. No auto-publishing. No OAuth. No store submission.

The operator manually uploads to Ditto using the metadata and checklist
produced here.

Functions:
- build_distribution_pack_from_release: scaffold a pack from a ReleasePack
- build_readiness_checklist: generate readiness checks from release state
- evaluate_readiness: re-evaluate all checklist items
- default_store_targets: return the default set of target stores
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.schemas import (
    DistributionPack,
    DistributionPackStatus,
    DistributionReadinessItem,
    DistributionStore,
    DittoDistributionMetadata,
    ReleasePack,
)


# ---------- Default store targets ----------

_DEFAULT_STORE_TARGETS: list[DistributionStore] = [
    DistributionStore.SPOTIFY,
    DistributionStore.APPLE_MUSIC,
    DistributionStore.YOUTUBE_MUSIC,
    DistributionStore.TIKTOK,
    DistributionStore.INSTAGRAM_FACEBOOK,
    DistributionStore.DEEZER,
    DistributionStore.TIDAL,
    DistributionStore.AMAZON_MUSIC,
]


def default_store_targets() -> list[DistributionStore]:
    """Return the default set of distribution store targets."""
    return list(_DEFAULT_STORE_TARGETS)


# ---------- Readiness checklist ----------


def build_readiness_checklist(release: ReleasePack) -> list[DistributionReadinessItem]:
    """Build readiness checklist items from release state.

    Each item is auto-evaluated based on the ReleasePack's current data.
    Items that cannot be auto-evaluated start as not passed.
    """
    items: list[DistributionReadinessItem] = []

    # Cover artifact
    cover_ready = _has_ready_asset(release, "cover_art")
    items.append(
        DistributionReadinessItem(
            code="cover_artifact",
            label="Cover art uploaded and ready",
            passed=cover_ready,
            notes="Found ready cover_art asset" if cover_ready else None,
        )
    )

    # Audio master
    audio_ready = _has_ready_asset(release, "audio_master")
    items.append(
        DistributionReadinessItem(
            code="audio_master",
            label="Audio master uploaded and ready",
            passed=audio_ready,
            notes="Found ready audio_master asset" if audio_ready else None,
        )
    )

    # Artist name
    has_artist = bool(release.artist and len(release.artist.strip()) > 0)
    items.append(
        DistributionReadinessItem(
            code="artist_name",
            label="Artist name set",
            passed=has_artist,
        )
    )

    # Title
    has_title = bool(release.title and len(release.title.strip()) > 0)
    items.append(
        DistributionReadinessItem(
            code="title",
            label="Release title set",
            passed=has_title,
        )
    )

    # Release date — manual, starts unchecked
    items.append(
        DistributionReadinessItem(
            code="release_date",
            label="Release date confirmed",
            passed=False,
            notes="Set release date before submitting to Ditto",
        )
    )

    # Explicit flag — always passes (defaults to False, which is a valid choice)
    items.append(
        DistributionReadinessItem(
            code="explicit_flag",
            label="Explicit content flag reviewed",
            passed=True,
            notes="Defaults to non-explicit. Review before submission.",
        )
    )

    # Copyright line — manual
    items.append(
        DistributionReadinessItem(
            code="copyright_line",
            label="Copyright line set",
            passed=False,
            notes="Add copyright holder and year before submission",
        )
    )

    # Genre
    has_genre = bool(release.genre and len(release.genre.strip()) > 0)
    items.append(
        DistributionReadinessItem(
            code="genre",
            label="Genre set",
            passed=has_genre,
        )
    )

    # Language — always passes (defaults to 'en')
    items.append(
        DistributionReadinessItem(
            code="language",
            label="Language set",
            passed=True,
            notes="Defaults to English (en)",
        )
    )

    # Provenance — check if compliance passed on release
    items.append(
        DistributionReadinessItem(
            code="provenance",
            label="Provenance chain documented",
            passed=release.compliance_passed,
            notes="Release compliance checklist must pass"
            if not release.compliance_passed
            else None,
        )
    )

    # Compliance
    items.append(
        DistributionReadinessItem(
            code="compliance",
            label="Compliance checklist passed",
            passed=release.compliance_passed,
        )
    )

    return items


# ---------- Metadata builder ----------


def _build_metadata(release: ReleasePack) -> DittoDistributionMetadata:
    """Extract Ditto-compatible metadata from a ReleasePack."""
    cover_artifact_id: UUID | None = None
    audio_master_artifact_id: UUID | None = None

    for asset in release.assets:
        if asset.asset_type == "cover_art" and asset.ready and asset.artifact_id:
            cover_artifact_id = asset.artifact_id
        if asset.asset_type == "audio_master" and asset.ready and asset.artifact_id:
            audio_master_artifact_id = asset.artifact_id

    return DittoDistributionMetadata(
        artist=release.artist,
        title=release.title,
        genre=release.genre,
        language="en",
        explicit=False,
        copyright_line="",
        cover_artifact_id=cover_artifact_id,
        audio_master_artifact_id=audio_master_artifact_id,
    )


# ---------- Pack builder ----------


def build_distribution_pack_from_release(
    release: ReleasePack,
    *,
    store_targets: list[DistributionStore] | None = None,
    operator_id: str | None = None,
    notes: str = "",
) -> DistributionPack:
    """Build a distribution pack scaffold from a ReleasePack.

    Pre-populates metadata, readiness checklist, and store targets.
    No real Ditto API calls.
    """
    targets = store_targets if store_targets else default_store_targets()
    metadata = _build_metadata(release)
    metadata = metadata.model_copy(update={"store_targets": targets})

    checklist = build_readiness_checklist(release)
    all_passed = all(item.passed for item in checklist)

    return DistributionPack(
        distribution_id=uuid4(),
        release_id=release.release_id,
        status=DistributionPackStatus.DRAFT,
        metadata=metadata,
        readiness_checklist=checklist,
        readiness_passed=all_passed,
        store_targets=targets,
        operator_notes=notes,
        created_by=operator_id,
    )


def evaluate_readiness(pack: DistributionPack) -> DistributionPack:
    """Re-evaluate readiness_passed from current checklist state."""
    all_passed = all(item.passed for item in pack.readiness_checklist)
    return pack.model_copy(update={"readiness_passed": all_passed})


# ---------- Helpers ----------


def _has_ready_asset(release: ReleasePack, asset_type: str) -> bool:
    """Check if a release has a ready asset of the given type."""
    return any(a.asset_type == asset_type and a.ready for a in release.assets)
