"""Release Pack Builder & Repository — S22.

Converts a Library ExportPack into a release-ready package with:
- Title / Artist / Description
- SoundCloud description + TikTok/Instagram copy
- Compliance checklist (from provenance chain)
- Asset placeholders (cover art, audio master, etc.)
- Dropbox target folder

No real SoundCloud/TikTok API calls — that ships later.
The builder is pure/deterministic: same pack + same request = same output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    ComplianceChecklistItem,
    ExportPack,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackCreateRequest,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Pure Builder ----------


_DEFAULT_CHECKLIST_ITEMS = [
    ("license_clear", "All licenses cleared for distribution"),
    ("model_attribution", "AI model attribution documented"),
    ("consent_verified", "Voice/sample consent records verified"),
    ("provenance_complete", "Full provenance chain documented"),
    ("master_approved", "Master audio approved by operator"),
    ("metadata_complete", "Release metadata complete (title, artist, genre)"),
]

_DEFAULT_ASSETS = [
    ("cover_art", "Cover Art", "png"),
    ("audio_master", "Audio Master (WAV)", "wav"),
    ("audio_preview", "Audio Preview (MP3)", "mp3"),
    ("stems_archive", "Stems Archive (ZIP)", "zip"),
]


def build_release_pack(
    pack: ExportPack,
    request: ReleasePackCreateRequest,
) -> ReleasePack:
    """Build a release pack from an ExportPack and creation request.

    Deterministic: same inputs → same structure (except release_id UUID).
    Generates default compliance checklist, asset placeholders, and
    social copy scaffolding.
    """
    title = request.title or pack.title
    description = request.description or _generate_description(pack, request.artist)

    # Build compliance checklist — starts unchecked
    checklist = _build_compliance_checklist(pack)

    # Build asset placeholders
    assets = _build_asset_placeholders(pack)

    # Build social copy scaffold
    social_copy = _build_social_copy(pack, title, request.artist, request.genre)

    # Dropbox target from existing plan or default
    dropbox_target = f"/SNUFFRAGA/Releases/{_sanitize_name(title)}"

    return ReleasePack(
        release_id=uuid4(),
        pack_id=pack.pack_id,
        title=title,
        artist=request.artist,
        status=ReleasePackStatus.DRAFT,
        description=description,
        social_copy=social_copy,
        compliance_checklist=checklist,
        compliance_passed=False,
        assets=assets,
        dropbox_target=dropbox_target,
        genre=request.genre,
        bpm=pack.bpm,
        key_signature=pack.key_signature,
        duration_seconds=pack.estimated_duration_seconds,
        operator_id=request.operator_id or pack.operator_id,
    )


def mark_release_ready(release: ReleasePack) -> ReleasePack:
    """Transition a release pack from DRAFT → READY.

    Only succeeds if compliance_passed is True.
    """
    if not release.compliance_passed:
        raise ValueError("Cannot mark release as ready — compliance checklist not fully passed.")
    return release.model_copy(
        update={
            "status": ReleasePackStatus.READY,
            "updated_at": datetime.now(timezone.utc),
        }
    )


def update_checklist_item(
    release: ReleasePack, code: str, passed: bool, notes: str | None = None
) -> ReleasePack:
    """Update a single compliance checklist item by code.

    Recalculates compliance_passed after update.
    """
    updated_items: list[ComplianceChecklistItem] = []
    found = False
    for item in release.compliance_checklist:
        if item.code == code:
            found = True
            updated_items.append(item.model_copy(update={"passed": passed, "notes": notes}))
        else:
            updated_items.append(item)

    if not found:
        raise ValueError(f"Checklist item '{code}' not found in release pack.")

    all_passed = all(i.passed for i in updated_items)
    return release.model_copy(
        update={
            "compliance_checklist": updated_items,
            "compliance_passed": all_passed,
            "updated_at": datetime.now(timezone.utc),
        }
    )


# ---------- Repository (backwards-compat alias — S23 moved to release_repository.py) ----------

from app.release_repository import InMemoryReleaseRepository as ReleasePackRepository  # noqa: F401, E402, E501


# ---------- Private Helpers ----------


def _sanitize_name(title: str) -> str:
    """Convert title to folder-safe name."""
    safe = title.strip()
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        safe = safe.replace(ch, "-")
    safe = safe.strip("-").strip()
    return safe[:100] or "untitled"


def _generate_description(pack: ExportPack, artist: str) -> str:
    """Generate a default release description from pack metadata."""
    parts = [f'"{pack.title}" by {artist}.']
    if pack.bpm:
        parts.append(f"{pack.bpm} BPM")
    if pack.key_signature:
        parts.append(f"in {pack.key_signature}")
    if pack.intent:
        parts.append(f"— {pack.intent.value.replace('_', ' ')}")
    if pack.estimated_duration_seconds:
        mins = int(pack.estimated_duration_seconds // 60)
        secs = int(pack.estimated_duration_seconds % 60)
        parts.append(f"({mins}:{secs:02d})")
    return " ".join(parts)


def _build_compliance_checklist(pack: ExportPack) -> list[ComplianceChecklistItem]:
    """Build default compliance checklist items.

    Items start unchecked. Provenance-related items get auto-notes
    if the pack has provenance data.
    """
    items: list[ComplianceChecklistItem] = []
    for code, label in _DEFAULT_CHECKLIST_ITEMS:
        notes = None
        if code == "provenance_complete" and pack.provenance_id:
            notes = f"Provenance ID: {pack.provenance_id}"
        items.append(ComplianceChecklistItem(code=code, label=label, passed=False, notes=notes))
    return items


def _build_asset_placeholders(pack: ExportPack) -> list[ReleaseAssetPlaceholder]:
    """Build default asset placeholders for a release."""
    assets: list[ReleaseAssetPlaceholder] = []
    for asset_type, label, fmt in _DEFAULT_ASSETS:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type=asset_type,
                label=label,
                expected_format=fmt,
                ready=False,
                path=None,
            )
        )
    return assets


def _build_social_copy(
    pack: ExportPack,
    title: str,
    artist: str,
    genre: str | None,
) -> SocialCopy:
    """Build scaffolded social copy for all platforms."""
    # SoundCloud description
    sc_parts = [f"{title} by {artist}"]
    if pack.bpm:
        sc_parts.append(f"\n{pack.bpm} BPM")
    if pack.key_signature:
        sc_parts.append(f" | {pack.key_signature}")
    if pack.intent:
        sc_parts.append(f"\nIntent: {pack.intent.value.replace('_', ' ')}")
    sc_parts.append("\n\nProduced with SNUFFRAGA SOUNDSYSTEM.")
    soundcloud_description = "".join(sc_parts)

    # TikTok — short, punchy
    tiktok_caption = f"{title} — {artist}"
    if genre:
        tiktok_caption += f" #{genre.replace(' ', '')}"

    # Instagram — slightly longer
    insta_parts = [f"{title} by {artist}"]
    if genre:
        insta_parts.append(f"Genre: {genre}")
    insta_parts.append("Produced with SNUFFRAGA SOUNDSYSTEM.")
    instagram_caption = "\n".join(insta_parts)

    # Hashtags
    hashtags = ["#SNUFFRAGA", "#SOUNDSYSTEM"]
    if genre:
        hashtags.append(f"#{genre.replace(' ', '')}")

    return SocialCopy(
        soundcloud_description=soundcloud_description,
        tiktok_caption=tiktok_caption,
        instagram_caption=instagram_caption,
        hashtags=hashtags,
    )
