"""Tests for S15 — SoundGraph → Music Router Handoff.

Verifies:
1. Intent resolution from arrangement characteristics.
2. Prompt compilation from arrangement (energy arc, sections).
3. Lane extraction (requested + locked).
4. Duration estimation from bars/bpm.
5. Full handoff produces a completed MusicJob with artifacts.
6. End-to-end flow: Lyrics → SoundGraph → Handoff → Music Job.
7. Provenance chain is maintained.
8. Route: 404 for missing arrangement, success for valid one.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.compliance_repository import build_default_compliance_repository
from app.music_router import (
    InMemoryMusicRouterRepository,
)
from app.schemas import (
    ArrangementRegion,
    EnergyLevel,
    LaneAssignment,
    LyricsGenerationRequest,
    MusicIntentKind,
    MusicJobStatus,
    RegionRole,
    SoundGraphArrangement,
    SoundGraphHandoffRequest,
    SoundGraphWriteRequest,
    StemLaneType,
    VocalEntry,
)
from app.soundgraph_handoff import (
    compile_handoff_prompt,
    estimate_duration_seconds,
    execute_handoff,
    extract_locked_lanes,
    extract_requested_lanes,
    resolve_intent_from_arrangement,
)


# ---------- Fixtures ----------


def _make_arrangement(
    *,
    regions: list[ArrangementRegion] | None = None,
    bpm: int = 140,
    total_bars: int = 88,
    key_signature: str | None = "Dm",
    lane_assignments: list[LaneAssignment] | None = None,
) -> SoundGraphArrangement:
    if regions is None:
        regions = [
            ArrangementRegion(
                region_index=0,
                section_index=0,
                role=RegionRole.INTRO,
                label="INTRO",
                bar_start=0,
                bar_count=8,
                vocal_entry=VocalEntry.NONE,
                energy=EnergyLevel.LOW,
                lanes_active=[StemLaneType.ATMOSPHERE, StemLaneType.FX],
                lanes_muted=[],
            ),
            ArrangementRegion(
                region_index=1,
                section_index=1,
                role=RegionRole.VERSE,
                label="VERSE 1",
                bar_start=8,
                bar_count=16,
                vocal_entry=VocalEntry.MAIN,
                energy=EnergyLevel.MEDIUM,
                lanes_active=[
                    StemLaneType.KICK,
                    StemLaneType.DRUMS,
                    StemLaneType.BASS,
                    StemLaneType.VOCALS_MAIN,
                ],
                lanes_muted=[],
            ),
            ArrangementRegion(
                region_index=2,
                section_index=2,
                role=RegionRole.CHORUS,
                label="CHORUS 1",
                bar_start=24,
                bar_count=16,
                vocal_entry=VocalEntry.MAIN,
                energy=EnergyLevel.PEAK,
                lanes_active=[
                    StemLaneType.KICK,
                    StemLaneType.DRUMS,
                    StemLaneType.BASS,
                    StemLaneType.MUSIC,
                    StemLaneType.VOCALS_MAIN,
                    StemLaneType.VOCALS_ADLIBS,
                ],
                lanes_muted=[],
                locked=True,
            ),
        ]
    if lane_assignments is None:
        lane_assignments = [
            LaneAssignment(lane=StemLaneType.KICK, active_regions=[1, 2]),
            LaneAssignment(lane=StemLaneType.DRUMS, active_regions=[1, 2]),
            LaneAssignment(lane=StemLaneType.BASS, active_regions=[1, 2]),
            LaneAssignment(lane=StemLaneType.MUSIC, active_regions=[2]),
            LaneAssignment(lane=StemLaneType.VOCALS_MAIN, active_regions=[1, 2]),
            LaneAssignment(lane=StemLaneType.VOCALS_ADLIBS, active_regions=[2]),
            LaneAssignment(lane=StemLaneType.ATMOSPHERE, active_regions=[0]),
            LaneAssignment(lane=StemLaneType.FX, active_regions=[0]),
        ]

    return SoundGraphArrangement(
        arrangement_id=uuid4(),
        lyrics_version_id=uuid4(),
        project_key="test-project",
        bpm=bpm,
        time_signature="4/4",
        key_signature=key_signature,
        total_bars=total_bars,
        regions=regions,
        energy_map=[],
        lane_assignments=lane_assignments,
    )


# ---------- Intent resolution ----------


class TestIntentResolution:
    def test_vocal_arrangement_creates_song_sketch(self) -> None:
        arr = _make_arrangement()  # has vocal regions
        assert resolve_intent_from_arrangement(arr) == MusicIntentKind.CREATE_SONG_SKETCH

    def test_short_no_vocals_creates_loop(self) -> None:
        arr = _make_arrangement(
            regions=[
                ArrangementRegion(
                    region_index=0,
                    section_index=0,
                    role=RegionRole.INTRO,
                    label="LOOP",
                    bar_start=0,
                    bar_count=8,
                    vocal_entry=VocalEntry.NONE,
                    energy=EnergyLevel.MEDIUM,
                    lanes_active=[StemLaneType.KICK, StemLaneType.BASS],
                    lanes_muted=[],
                )
            ],
            total_bars=8,
        )
        assert resolve_intent_from_arrangement(arr) == MusicIntentKind.CREATE_LOOP

    def test_breakdown_no_vocals_builds_riddim(self) -> None:
        arr = _make_arrangement(
            regions=[
                ArrangementRegion(
                    region_index=0,
                    section_index=0,
                    role=RegionRole.VERSE,
                    label="VERSE",
                    bar_start=0,
                    bar_count=16,
                    vocal_entry=VocalEntry.NONE,
                    energy=EnergyLevel.MEDIUM,
                    lanes_active=[StemLaneType.KICK],
                    lanes_muted=[],
                ),
                ArrangementRegion(
                    region_index=1,
                    section_index=1,
                    role=RegionRole.BREAKDOWN,
                    label="BREAKDOWN",
                    bar_start=16,
                    bar_count=8,
                    vocal_entry=VocalEntry.NONE,
                    energy=EnergyLevel.DROP,
                    lanes_active=[StemLaneType.BASS],
                    lanes_muted=[],
                ),
            ],
            total_bars=24,
        )
        assert resolve_intent_from_arrangement(arr) == MusicIntentKind.BUILD_RIDDIM

    def test_long_no_vocals_no_breakdown_creates_stem_track(self) -> None:
        arr = _make_arrangement(
            regions=[
                ArrangementRegion(
                    region_index=0,
                    section_index=0,
                    role=RegionRole.VERSE,
                    label="VERSE",
                    bar_start=0,
                    bar_count=32,
                    vocal_entry=VocalEntry.NONE,
                    energy=EnergyLevel.MEDIUM,
                    lanes_active=[StemLaneType.KICK],
                    lanes_muted=[],
                ),
            ],
            total_bars=32,
        )
        assert resolve_intent_from_arrangement(arr) == MusicIntentKind.CREATE_STEM_TRACK


# ---------- Prompt compilation ----------


class TestPromptCompilation:
    def test_prompt_contains_bpm(self) -> None:
        arr = _make_arrangement(bpm=145)
        prompt = compile_handoff_prompt(arr)
        assert "145 BPM" in prompt

    def test_prompt_contains_key(self) -> None:
        arr = _make_arrangement(key_signature="Am")
        prompt = compile_handoff_prompt(arr)
        assert "Key: Am" in prompt

    def test_prompt_contains_energy_arc(self) -> None:
        arr = _make_arrangement()
        prompt = compile_handoff_prompt(arr)
        assert "Energy arc:" in prompt
        assert "intro(low)" in prompt
        assert "chorus(peak)" in prompt

    def test_prompt_contains_sections(self) -> None:
        arr = _make_arrangement()
        prompt = compile_handoff_prompt(arr)
        assert "Sections:" in prompt
        assert "VERSE 1" in prompt


# ---------- Lane extraction ----------


class TestLaneExtraction:
    def test_requested_lanes(self) -> None:
        arr = _make_arrangement()
        lanes = extract_requested_lanes(arr)
        assert StemLaneType.KICK in lanes
        assert StemLaneType.VOCALS_MAIN in lanes
        assert StemLaneType.ATMOSPHERE in lanes

    def test_locked_lanes(self) -> None:
        # In our fixture, region 2 (chorus) is locked.
        # MUSIC and VOCALS_ADLIBS only appear in region 2,
        # so they should be considered locked.
        arr = _make_arrangement()
        locked = extract_locked_lanes(arr)
        assert StemLaneType.MUSIC in locked
        assert StemLaneType.VOCALS_ADLIBS in locked

    def test_non_locked_lanes(self) -> None:
        arr = _make_arrangement()
        locked = extract_locked_lanes(arr)
        # KICK plays in regions 1 and 2, only region 2 is locked → not locked
        assert StemLaneType.KICK not in locked


# ---------- Duration estimation ----------


class TestDurationEstimation:
    def test_basic_duration(self) -> None:
        # 88 bars * 4 beats / 140 bpm * 60 = ~150.9 seconds
        arr = _make_arrangement(total_bars=88, bpm=140)
        duration = estimate_duration_seconds(arr)
        expected = round(88 * 4 / 140 * 60, 1)
        assert duration == expected

    def test_fast_bpm(self) -> None:
        arr = _make_arrangement(total_bars=64, bpm=180)
        duration = estimate_duration_seconds(arr)
        expected = round(64 * 4 / 180 * 60, 1)
        assert duration == expected


# ---------- Full handoff ----------


class TestExecuteHandoff:
    def test_handoff_produces_completed_job(self) -> None:
        arr = _make_arrangement()
        music_repo = InMemoryMusicRouterRepository()
        compliance_repo = build_default_compliance_repository()

        job = execute_handoff(arr, music_repo, compliance_repo)
        assert job.status == MusicJobStatus.COMPLETED
        assert len(job.artifacts) > 0
        assert job.provenance_id is not None

    def test_handoff_uses_resolved_intent(self) -> None:
        arr = _make_arrangement()  # has vocals → CREATE_SONG_SKETCH
        music_repo = InMemoryMusicRouterRepository()
        compliance_repo = build_default_compliance_repository()

        job = execute_handoff(arr, music_repo, compliance_repo)
        assert job.intent == MusicIntentKind.CREATE_SONG_SKETCH

    def test_handoff_with_intent_override(self) -> None:
        arr = _make_arrangement()
        music_repo = InMemoryMusicRouterRepository()
        compliance_repo = build_default_compliance_repository()

        job = execute_handoff(
            arr,
            music_repo,
            compliance_repo,
            intent_override=MusicIntentKind.BUILD_RIDDIM,
        )
        assert job.intent == MusicIntentKind.BUILD_RIDDIM

    def test_handoff_propagates_bpm_in_prompt(self) -> None:
        arr = _make_arrangement(bpm=145)
        music_repo = InMemoryMusicRouterRepository()
        compliance_repo = build_default_compliance_repository()

        job = execute_handoff(arr, music_repo, compliance_repo)
        assert "145 BPM" in job.prompt

    def test_handoff_sets_operator_id(self) -> None:
        arr = _make_arrangement()
        music_repo = InMemoryMusicRouterRepository()
        compliance_repo = build_default_compliance_repository()

        job = execute_handoff(arr, music_repo, compliance_repo, operator_id="op-test-42")
        assert job.operator_id == "op-test-42"


# ---------- Route tests ----------


class TestHandoffRoute:
    def test_handoff_route_404_for_missing_arrangement(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                inference_main.soundgraph_handoff_route(
                    SoundGraphHandoffRequest(arrangement_id=uuid4()),
                    DEV_OPERATOR,
                )
            )
        assert exc_info.value.status_code == 404

    def test_handoff_route_success(self) -> None:
        # First create a lyrics version
        lyrics_version = asyncio.run(
            inference_main.create_lyrics(
                LyricsGenerationRequest(
                    project_key="handoff-test",
                    prompt="deep dub warehouse track",
                    character_code="SHIBARI_KAWAII",
                    target_language="en",
                ),
                DEV_OPERATOR,
            )
        )

        # Compile soundgraph
        sg_result = asyncio.run(
            inference_main.compile_soundgraph_route(
                SoundGraphWriteRequest(
                    lyrics_version_id=lyrics_version.id,
                    bpm=138,
                ),
                DEV_OPERATOR,
            )
        )

        # Execute handoff
        handoff_result = asyncio.run(
            inference_main.soundgraph_handoff_route(
                SoundGraphHandoffRequest(
                    arrangement_id=sg_result.arrangement.arrangement_id,
                ),
                DEV_OPERATOR,
            )
        )

        assert handoff_result.music_job.status == MusicJobStatus.COMPLETED
        assert len(handoff_result.music_job.artifacts) > 0
        assert handoff_result.music_job.provenance_id is not None
        assert handoff_result.estimated_duration_seconds > 0
        assert "138 BPM" in handoff_result.compiled_prompt
        assert len(handoff_result.requested_lanes) > 0
        assert handoff_result.resolved_intent in MusicIntentKind


# ---------- End-to-end flow ----------


class TestEndToEndFlow:
    def test_lyrics_to_soundgraph_to_music_job(self) -> None:
        """The complete text-to-production-plan-to-mock-track flow.

        Lyrics erzeugen → SoundGraph bauen → Music Router Job starten
        """
        # Step 1: Generate lyrics
        lyrics_version = asyncio.run(
            inference_main.create_lyrics(
                LyricsGenerationRequest(
                    project_key="e2e-flow",
                    prompt="dark industrial anthem, crushing bass, whisper hook",
                    character_code="SHIBARI_KAWAII",
                    target_language="en",
                ),
                DEV_OPERATOR,
            )
        )
        assert lyrics_version.structure.sections is not None
        assert len(lyrics_version.structure.sections) > 0

        # Step 2: Compile SoundGraph
        sg_result = asyncio.run(
            inference_main.compile_soundgraph_route(
                SoundGraphWriteRequest(
                    lyrics_version_id=lyrics_version.id,
                    bpm=142,
                    energy_profile="standard",
                    key_signature="Cm",
                ),
                DEV_OPERATOR,
            )
        )
        assert sg_result.section_count > 0
        assert sg_result.total_bars > 0
        assert sg_result.arrangement.bpm == 142

        # Step 3: Hand off to Music Router
        handoff_result = asyncio.run(
            inference_main.soundgraph_handoff_route(
                SoundGraphHandoffRequest(
                    arrangement_id=sg_result.arrangement.arrangement_id,
                    title="E2E Test Track",
                    operator_id="test-operator",
                ),
                DEV_OPERATOR,
            )
        )

        # Verify the complete chain
        job = handoff_result.music_job
        assert job.status == MusicJobStatus.COMPLETED
        assert job.title == "E2E Test Track"
        assert job.operator_id == DEV_OPERATOR.operator_id
        assert len(job.artifacts) >= 1
        assert job.provenance_id is not None

        # Verify provenance exists in compliance repo
        provenance = inference_main.compliance_repository.get_provenance(job.provenance_id)
        assert provenance is not None
        assert provenance.artifact_kind.startswith("music_")

        # Verify we can look up the music job
        found_job = asyncio.run(inference_main.get_music_job(job.job_id))
        assert found_job.job_id == job.job_id
        assert found_job.status == MusicJobStatus.COMPLETED
