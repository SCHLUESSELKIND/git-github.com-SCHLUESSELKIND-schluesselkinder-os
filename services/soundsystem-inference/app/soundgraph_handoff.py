"""SoundGraph → Music Router Handoff (S15).

Compiles a SoundGraphArrangement into a MusicGenerationRequest and
submits it to the music router. This closes the text-to-production loop:

  Lyrics → SoundGraph → MusicGenerationRequest → Music Router → Artifacts

The handoff is deterministic and rule-based:
- Intent is derived from arrangement characteristics (presence of vocal
  lanes → CREATE_SONG_SKETCH, only loops → CREATE_LOOP, etc.)
- requested_lanes come from the arrangement's lane_assignments
- locked_lanes are sections marked locked in the arrangement
- bpm/key/duration are propagated from the arrangement
- A prompt is compiled from the arrangement regions (energy + roles)

The handoff does NOT call external APIs. It wires existing modules together.
"""

from __future__ import annotations


from app.compliance_repository import ComplianceRepository
from app.music_router import MusicRouterRepository, run_music_job
from app.schemas import (
    CommercialStatus,
    MusicGenerationRequest,
    MusicIntentKind,
    MusicJob,
    RegionRole,
    SoundGraphArrangement,
    StemLaneType,
    VocalEntry,
)


# ---------- Intent resolution from arrangement ----------


def resolve_intent_from_arrangement(
    arrangement: SoundGraphArrangement,
) -> MusicIntentKind:
    """Determine the best music intent from arrangement characteristics.

    Rules:
    - If any region has vocal_entry != NONE → CREATE_SONG_SKETCH
      (full track with vocals)
    - If total_bars <= 16 and no vocals → CREATE_LOOP
    - If arrangement has many percussion/drums regions → BUILD_RIDDIM
    - Default fallback → CREATE_STEM_TRACK (most flexible)
    """
    has_vocals = any(r.vocal_entry != VocalEntry.NONE for r in arrangement.regions)
    has_breakdown = any(r.role == RegionRole.BREAKDOWN for r in arrangement.regions)

    if has_vocals:
        return MusicIntentKind.CREATE_SONG_SKETCH

    if arrangement.total_bars <= 16:
        return MusicIntentKind.CREATE_LOOP

    if has_breakdown and not has_vocals:
        return MusicIntentKind.BUILD_RIDDIM

    return MusicIntentKind.CREATE_STEM_TRACK


# ---------- Prompt compilation from arrangement ----------


def compile_handoff_prompt(arrangement: SoundGraphArrangement) -> str:
    """Build a descriptive prompt from the arrangement structure.

    This is what the music provider sees — a structured text describing
    the energy arc, section roles, and production characteristics.
    """
    lines: list[str] = []
    lines.append(f"{arrangement.bpm} BPM")
    if arrangement.key_signature:
        lines.append(f"Key: {arrangement.key_signature}")
    lines.append(f"Time: {arrangement.time_signature}")
    lines.append(f"Duration: {arrangement.total_bars} bars")
    lines.append("")

    # Energy arc summary
    energy_sequence = [f"{r.role.value}({r.energy.value})" for r in arrangement.regions]
    lines.append(f"Energy arc: {' → '.join(energy_sequence)}")
    lines.append("")

    # Section breakdown
    lines.append("Sections:")
    for region in arrangement.regions:
        vocal_tag = ""
        if region.vocal_entry != VocalEntry.NONE:
            vocal_tag = f" [vocal: {region.vocal_entry.value}]"
        lines.append(
            f"  {region.label} | bars {region.bar_start}–"
            f"{region.bar_start + region.bar_count - 1} | "
            f"energy={region.energy.value}{vocal_tag}"
        )

    return "\n".join(lines)


# ---------- Lane extraction ----------


def extract_requested_lanes(
    arrangement: SoundGraphArrangement,
) -> list[StemLaneType]:
    """Extract the unique set of lanes that play anywhere in the arrangement."""
    lanes: set[StemLaneType] = set()
    for la in arrangement.lane_assignments:
        if la.active_regions:
            lanes.add(la.lane)
    return sorted(lanes, key=lambda lane: lane.value)


def extract_locked_lanes(
    arrangement: SoundGraphArrangement,
) -> list[StemLaneType]:
    """Extract lanes that are in locked regions only.

    A lane is considered locked if ALL regions where it plays are locked.
    """
    # Build: lane → set of regions it plays in
    lane_regions: dict[StemLaneType, set[int]] = {}
    for la in arrangement.lane_assignments:
        lane_regions[la.lane] = set(la.active_regions)

    # Build: set of locked region indices
    locked_regions = {r.region_index for r in arrangement.regions if r.locked}

    locked_lanes: list[StemLaneType] = []
    for lane, regions in lane_regions.items():
        if regions and regions.issubset(locked_regions):
            locked_lanes.append(lane)

    return sorted(locked_lanes, key=lambda lane: lane.value)


# ---------- Duration estimation ----------


def estimate_duration_seconds(arrangement: SoundGraphArrangement) -> float:
    """Estimate track duration from bars and BPM.

    bars * beats_per_bar / bpm * 60
    Assumes 4/4 unless time_signature says otherwise.
    """
    beats_per_bar = 4
    if "/" in arrangement.time_signature:
        parts = arrangement.time_signature.split("/")
        try:
            beats_per_bar = int(parts[0])
        except ValueError:
            beats_per_bar = 4

    total_beats = arrangement.total_bars * beats_per_bar
    return round(total_beats / arrangement.bpm * 60.0, 1)


# ---------- Build request ----------


def build_music_request_from_arrangement(
    arrangement: SoundGraphArrangement,
    *,
    title: str | None = None,
    operator_id: str | None = None,
    commercial_target: CommercialStatus = CommercialStatus.REVIEW_NEEDED,
    intent_override: MusicIntentKind | None = None,
) -> MusicGenerationRequest:
    """Build a MusicGenerationRequest from a SoundGraphArrangement.

    This is the bridge function that the handoff route calls.
    """
    intent = intent_override or resolve_intent_from_arrangement(arrangement)
    prompt = compile_handoff_prompt(arrangement)
    requested_lanes = extract_requested_lanes(arrangement)
    locked_lanes = extract_locked_lanes(arrangement)
    duration = estimate_duration_seconds(arrangement)

    return MusicGenerationRequest(
        intent=intent,
        title=title or f"SoundGraph → {intent.value}",
        prompt=prompt,
        duration_seconds=duration,
        bpm=arrangement.bpm,
        key=arrangement.key_signature,
        requested_lanes=requested_lanes,
        locked_lanes=locked_lanes,
        commercial_target=commercial_target,
        operator_id=operator_id,
    )


# ---------- Full handoff ----------


def execute_handoff(
    arrangement: SoundGraphArrangement,
    music_repo: MusicRouterRepository,
    compliance_repo: ComplianceRepository,
    *,
    title: str | None = None,
    operator_id: str | None = None,
    commercial_target: CommercialStatus = CommercialStatus.REVIEW_NEEDED,
    intent_override: MusicIntentKind | None = None,
) -> MusicJob:
    """Execute the full SoundGraph → Music Router handoff.

    Builds the request from the arrangement and runs it through the
    existing music router pipeline.
    """
    request = build_music_request_from_arrangement(
        arrangement,
        title=title,
        operator_id=operator_id,
        commercial_target=commercial_target,
        intent_override=intent_override,
    )
    return run_music_job(request, music_repo, compliance_repo)
