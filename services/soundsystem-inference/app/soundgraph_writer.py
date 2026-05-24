"""SoundGraph Manifest Writer (S14).

Compiles a LyricsVersion into a SoundGraphArrangement — the editable
production structure that bridges text lyrics and audio generation.

The writer is deterministic and pure: given the same lyrics + config, it
always produces the same arrangement. No external calls, no randomness.

Pipeline:
  LyricsVersion → Sections → Regions → Vocal Entry → Lane Assignments
  → Energy Map → SoundGraphArrangement

Rules:
- Every LyricsSection maps to exactly one ArrangementRegion.
- Instrumental sections get VocalEntry.NONE.
- Vocal sections get VocalEntry.MAIN (default) or WHISPER for dub_breakdown.
- Lane assignments follow genre conventions for warehouse/dub/dark ambient.
- Energy map is derived from section roles + energy_profile preset.
- The writer never calls external APIs.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.schemas import (
    ArrangementRegion,
    EnergyLevel,
    EnergyMapPoint,
    LaneAssignment,
    LyricsSectionType,
    LyricsStructure,
    LyricsVersion,
    RegionRole,
    SoundGraphArrangement,
    SoundGraphWriteRequest,
    SoundGraphWriteResult,
    StemLaneType,
    StemSourceType,
    VocalEntry,
)


# ---------- Section → Region Role mapping ----------

_SECTION_TO_ROLE: dict[LyricsSectionType, RegionRole] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: RegionRole.INTRO,
    LyricsSectionType.VERSE: RegionRole.VERSE,
    LyricsSectionType.PRE_CHORUS: RegionRole.PRE_CHORUS,
    LyricsSectionType.CHORUS: RegionRole.CHORUS,
    LyricsSectionType.BRIDGE: RegionRole.BRIDGE,
    LyricsSectionType.DUB_BREAKDOWN: RegionRole.BREAKDOWN,
    LyricsSectionType.OUTRO: RegionRole.OUTRO,
}

# ---------- Default bar counts per section type ----------

_DEFAULT_BARS: dict[LyricsSectionType, int] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: 8,
    LyricsSectionType.VERSE: 16,
    LyricsSectionType.PRE_CHORUS: 8,
    LyricsSectionType.CHORUS: 16,
    LyricsSectionType.BRIDGE: 8,
    LyricsSectionType.DUB_BREAKDOWN: 8,
    LyricsSectionType.OUTRO: 8,
}

# ---------- Vocal entry mapping ----------

_SECTION_VOCAL_ENTRY: dict[LyricsSectionType, VocalEntry] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: VocalEntry.NONE,
    LyricsSectionType.VERSE: VocalEntry.MAIN,
    LyricsSectionType.PRE_CHORUS: VocalEntry.MAIN,
    LyricsSectionType.CHORUS: VocalEntry.MAIN,
    LyricsSectionType.BRIDGE: VocalEntry.MAIN,
    LyricsSectionType.DUB_BREAKDOWN: VocalEntry.WHISPER,
    LyricsSectionType.OUTRO: VocalEntry.NONE,
}

# ---------- Energy profiles ----------

# Maps (role) → energy level for each named profile
_ENERGY_PROFILES: dict[str, dict[RegionRole, EnergyLevel]] = {
    "standard": {
        RegionRole.INTRO: EnergyLevel.LOW,
        RegionRole.VERSE: EnergyLevel.MEDIUM,
        RegionRole.PRE_CHORUS: EnergyLevel.HIGH,
        RegionRole.CHORUS: EnergyLevel.PEAK,
        RegionRole.BRIDGE: EnergyLevel.MEDIUM,
        RegionRole.BREAKDOWN: EnergyLevel.DROP,
        RegionRole.DROP: EnergyLevel.PEAK,
        RegionRole.OUTRO: EnergyLevel.LOW,
    },
    "slow_build": {
        RegionRole.INTRO: EnergyLevel.LOW,
        RegionRole.VERSE: EnergyLevel.LOW,
        RegionRole.PRE_CHORUS: EnergyLevel.MEDIUM,
        RegionRole.CHORUS: EnergyLevel.HIGH,
        RegionRole.BRIDGE: EnergyLevel.MEDIUM,
        RegionRole.BREAKDOWN: EnergyLevel.LOW,
        RegionRole.DROP: EnergyLevel.PEAK,
        RegionRole.OUTRO: EnergyLevel.MEDIUM,
    },
    "peak_early": {
        RegionRole.INTRO: EnergyLevel.MEDIUM,
        RegionRole.VERSE: EnergyLevel.HIGH,
        RegionRole.PRE_CHORUS: EnergyLevel.PEAK,
        RegionRole.CHORUS: EnergyLevel.PEAK,
        RegionRole.BRIDGE: EnergyLevel.MEDIUM,
        RegionRole.BREAKDOWN: EnergyLevel.DROP,
        RegionRole.DROP: EnergyLevel.HIGH,
        RegionRole.OUTRO: EnergyLevel.LOW,
    },
    "flat": {
        RegionRole.INTRO: EnergyLevel.MEDIUM,
        RegionRole.VERSE: EnergyLevel.MEDIUM,
        RegionRole.PRE_CHORUS: EnergyLevel.MEDIUM,
        RegionRole.CHORUS: EnergyLevel.MEDIUM,
        RegionRole.BRIDGE: EnergyLevel.MEDIUM,
        RegionRole.BREAKDOWN: EnergyLevel.MEDIUM,
        RegionRole.DROP: EnergyLevel.MEDIUM,
        RegionRole.OUTRO: EnergyLevel.MEDIUM,
    },
}

# ---------- Lane assignment rules (warehouse/dub genre convention) ----------

# Which lanes are active for each region role
_LANES_BY_ROLE: dict[RegionRole, list[StemLaneType]] = {
    RegionRole.INTRO: [
        StemLaneType.ATMOSPHERE,
        StemLaneType.FX,
        StemLaneType.RETURN_REVERB,
    ],
    RegionRole.VERSE: [
        StemLaneType.KICK,
        StemLaneType.DRUMS,
        StemLaneType.BASS,
        StemLaneType.MUSIC,
        StemLaneType.VOCALS_MAIN,
        StemLaneType.ATMOSPHERE,
        StemLaneType.RETURN_DELAY,
    ],
    RegionRole.PRE_CHORUS: [
        StemLaneType.KICK,
        StemLaneType.DRUMS,
        StemLaneType.PERCUSSION,
        StemLaneType.BASS,
        StemLaneType.MUSIC,
        StemLaneType.LEAD,
        StemLaneType.VOCALS_MAIN,
        StemLaneType.FX,
        StemLaneType.RETURN_DELAY,
    ],
    RegionRole.CHORUS: [
        StemLaneType.KICK,
        StemLaneType.DRUMS,
        StemLaneType.PERCUSSION,
        StemLaneType.BASS,
        StemLaneType.MUSIC,
        StemLaneType.LEAD,
        StemLaneType.VOCALS_MAIN,
        StemLaneType.VOCALS_ADLIBS,
        StemLaneType.FX,
        StemLaneType.ATMOSPHERE,
        StemLaneType.RETURN_DELAY,
        StemLaneType.RETURN_REVERB,
    ],
    RegionRole.BRIDGE: [
        StemLaneType.DRUMS,
        StemLaneType.BASS,
        StemLaneType.MUSIC,
        StemLaneType.VOCALS_MAIN,
        StemLaneType.ATMOSPHERE,
        StemLaneType.RETURN_REVERB,
    ],
    RegionRole.BREAKDOWN: [
        StemLaneType.BASS,
        StemLaneType.ATMOSPHERE,
        StemLaneType.FX,
        StemLaneType.VOCALS_MAIN,
        StemLaneType.RETURN_DELAY,
        StemLaneType.RETURN_REVERB,
    ],
    RegionRole.DROP: [
        StemLaneType.KICK,
        StemLaneType.DRUMS,
        StemLaneType.PERCUSSION,
        StemLaneType.BASS,
        StemLaneType.MUSIC,
        StemLaneType.LEAD,
        StemLaneType.FX,
        StemLaneType.ATMOSPHERE,
        StemLaneType.RETURN_DELAY,
        StemLaneType.RETURN_REVERB,
    ],
    RegionRole.OUTRO: [
        StemLaneType.ATMOSPHERE,
        StemLaneType.FX,
        StemLaneType.RETURN_REVERB,
    ],
}

# All 12 lanes for mute-complement calculation
_ALL_LANES = list(StemLaneType)


def _resolve_bars(
    section_type: LyricsSectionType,
    overrides: dict[str, int] | None,
) -> int:
    """Resolve bar count for a section, respecting overrides."""
    if overrides and section_type.value in overrides:
        return max(1, min(64, overrides[section_type.value]))
    return _DEFAULT_BARS.get(section_type, 8)


def _resolve_energy(role: RegionRole, profile_name: str) -> EnergyLevel:
    """Resolve energy level for a role using the named profile."""
    profile = _ENERGY_PROFILES.get(profile_name, _ENERGY_PROFILES["standard"])
    return profile.get(role, EnergyLevel.MEDIUM)


def _build_regions(
    structure: LyricsStructure,
    bars_override: dict[str, int] | None,
    energy_profile: str,
) -> list[ArrangementRegion]:
    """Build arrangement regions from lyrics sections."""
    regions: list[ArrangementRegion] = []
    current_bar = 0

    for section in structure.sections:
        role = _SECTION_TO_ROLE.get(section.section_type, RegionRole.VERSE)
        bar_count = _resolve_bars(section.section_type, bars_override)
        vocal_entry = _SECTION_VOCAL_ENTRY.get(section.section_type, VocalEntry.NONE)

        # If avoid_intro_singing and this is the first vocal section, strip vocals
        if structure.avoid_intro_singing and vocal_entry != VocalEntry.NONE:
            if (
                all(
                    _SECTION_VOCAL_ENTRY.get(s.section_type, VocalEntry.NONE) == VocalEntry.NONE
                    for s in structure.sections[: section.index]
                )
                and section.index == 0
            ):
                vocal_entry = VocalEntry.NONE

        lanes_active = _LANES_BY_ROLE.get(role, [StemLaneType.ATMOSPHERE])
        # Remove vocal lanes if no vocal entry
        if vocal_entry == VocalEntry.NONE:
            lanes_active = [
                lane
                for lane in lanes_active
                if lane not in (StemLaneType.VOCALS_MAIN, StemLaneType.VOCALS_ADLIBS)
            ]

        lanes_muted = [lane for lane in _ALL_LANES if lane not in lanes_active]
        energy = _resolve_energy(role, energy_profile)

        regions.append(
            ArrangementRegion(
                region_index=len(regions),
                section_index=section.index,
                role=role,
                label=section.label,
                bar_start=current_bar,
                bar_count=bar_count,
                vocal_entry=vocal_entry,
                energy=energy,
                lanes_active=lanes_active,
                lanes_muted=lanes_muted,
                locked=section.locked,
                notes=section.notes,
            )
        )
        current_bar += bar_count

    return regions


def _build_energy_map(regions: list[ArrangementRegion]) -> list[EnergyMapPoint]:
    """Build energy map from region energy levels."""
    return [
        EnergyMapPoint(
            region_index=region.region_index,
            bar=region.bar_start,
            energy=region.energy,
        )
        for region in regions
    ]


def _build_lane_assignments(
    regions: list[ArrangementRegion],
) -> list[LaneAssignment]:
    """Build lane assignments showing which lanes play in which regions."""
    lane_regions: dict[StemLaneType, list[int]] = {lane: [] for lane in _ALL_LANES}

    for region in regions:
        for lane in region.lanes_active:
            lane_regions[lane].append(region.region_index)

    return [
        LaneAssignment(
            lane=lane,
            active_regions=region_indices,
            source=StemSourceType.GENERATED_DIRECT,
        )
        for lane, region_indices in lane_regions.items()
        if region_indices  # Only include lanes that actually play somewhere
    ]


def compile_soundgraph(
    version: LyricsVersion,
    request: SoundGraphWriteRequest,
) -> SoundGraphWriteResult:
    """Compile a LyricsVersion into a SoundGraphArrangement.

    Pure, deterministic, no external calls.
    """
    structure = version.structure
    warnings: list[str] = []

    # Validate energy profile
    if request.energy_profile not in _ENERGY_PROFILES:
        warnings.append(
            f"Unknown energy_profile '{request.energy_profile}', falling back to 'standard'."
        )

    # Build regions
    regions = _build_regions(
        structure,
        request.bars_per_section_override,
        request.energy_profile,
    )

    if not regions:
        warnings.append("No sections in lyrics — arrangement is empty.")

    total_bars = sum(r.bar_count for r in regions)
    energy_map = _build_energy_map(regions)
    lane_assignments = _build_lane_assignments(regions)

    vocal_regions = sum(1 for r in regions if r.vocal_entry != VocalEntry.NONE)
    instrumental_regions = len(regions) - vocal_regions

    arrangement = SoundGraphArrangement(
        arrangement_id=uuid4(),
        lyrics_version_id=version.id,
        project_key=request.lyrics_version_id.hex[:12],  # placeholder
        bpm=request.bpm,
        time_signature=request.time_signature,
        key_signature=request.key_signature,
        total_bars=total_bars,
        regions=regions,
        energy_map=energy_map,
        lane_assignments=lane_assignments,
    )

    return SoundGraphWriteResult(
        arrangement=arrangement,
        warnings=warnings,
        section_count=len(regions),
        total_bars=total_bars,
        vocal_regions=vocal_regions,
        instrumental_regions=instrumental_regions,
    )


# ---------- Repository for persisting arrangements ----------


class SoundGraphRepository:
    """In-memory repository for SoundGraph arrangements."""

    def __init__(self) -> None:
        self._arrangements: dict[UUID, SoundGraphArrangement] = {}
        # Index: lyrics_version_id → arrangement_id
        self._by_lyrics_version: dict[UUID, UUID] = {}

    def store(self, arrangement: SoundGraphArrangement) -> SoundGraphArrangement:
        self._arrangements[arrangement.arrangement_id] = arrangement
        self._by_lyrics_version[arrangement.lyrics_version_id] = arrangement.arrangement_id
        return arrangement

    def get(self, arrangement_id: UUID) -> SoundGraphArrangement | None:
        return self._arrangements.get(arrangement_id)

    def get_by_lyrics_version(self, lyrics_version_id: UUID) -> SoundGraphArrangement | None:
        arr_id = self._by_lyrics_version.get(lyrics_version_id)
        if arr_id is None:
            return None
        return self._arrangements.get(arr_id)

    def list_all(self) -> list[SoundGraphArrangement]:
        return sorted(
            self._arrangements.values(),
            key=lambda a: a.created_at,
            reverse=True,
        )

    def count(self) -> int:
        return len(self._arrangements)
