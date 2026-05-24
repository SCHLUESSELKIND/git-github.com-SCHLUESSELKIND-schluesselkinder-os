"""Tests for S14 — SoundGraph Manifest Writer.

Verifies:
1. Lyrics → Regions mapping (every section becomes one region).
2. Vocal entry rules (instrumental=none, verse/chorus=main, dub_breakdown=whisper).
3. Lane assignments follow genre conventions.
4. Energy map derived from profile presets.
5. Bar counting and section overrides.
6. Routes: compile, get, list, get-by-lyrics-version.
7. Edge cases: empty lyrics, unknown energy profile fallback.
8. Repository CRUD.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.schemas import (
    EnergyLevel,
    LyricsGenerationRequest,
    LyricsLine,
    LyricsSection,
    LyricsSectionType,
    LyricsSource,
    LyricsStructure,
    LyricsVersion,
    SoundGraphWriteRequest,
    StemLaneType,
    VocalEntry,
)
from app.soundgraph_writer import (
    SoundGraphRepository,
    compile_soundgraph,
)


# ---------- Fixtures ----------


def _make_lyrics_version(
    sections: list[LyricsSectionType] | None = None,
    avoid_intro_singing: bool = False,
) -> LyricsVersion:
    """Create a minimal LyricsVersion for testing."""
    if sections is None:
        sections = [
            LyricsSectionType.INSTRUMENTAL_OPENING,
            LyricsSectionType.VERSE,
            LyricsSectionType.PRE_CHORUS,
            LyricsSectionType.CHORUS,
            LyricsSectionType.DUB_BREAKDOWN,
            LyricsSectionType.VERSE,
            LyricsSectionType.CHORUS,
            LyricsSectionType.OUTRO,
        ]

    lyrics_sections = []
    for i, st in enumerate(sections):
        lyrics_sections.append(
            LyricsSection(
                index=i,
                section_type=st,
                label=f"{st.value.upper()} {i}",
                lines=[LyricsLine(index=0, text="test line", syllables=4)],
                locked=False,
                manually_edited=False,
                source=LyricsSource.MOCK,
            )
        )

    return LyricsVersion(
        id=uuid4(),
        project_id=uuid4(),
        version=1,
        structure=LyricsStructure(
            sections=lyrics_sections,
            avoid_intro_singing=avoid_intro_singing,
            target_language="en",
        ),
    )


# ---------- Core compilation tests ----------


class TestCompileSoundgraph:
    def test_basic_compilation(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(
            lyrics_version_id=version.id,
            bpm=140,
        )
        result = compile_soundgraph(version, request)

        assert result.section_count == 8
        assert result.total_bars > 0
        assert result.vocal_regions > 0
        assert result.instrumental_regions > 0
        assert len(result.arrangement.regions) == 8
        assert result.arrangement.bpm == 140

    def test_regions_match_sections(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)

        for i, region in enumerate(result.arrangement.regions):
            assert region.region_index == i
            assert region.section_index == i

    def test_total_bars_sum(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)

        expected_total = sum(r.bar_count for r in result.arrangement.regions)
        assert result.total_bars == expected_total
        assert result.arrangement.total_bars == expected_total

    def test_bar_start_sequential(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)

        current = 0
        for region in result.arrangement.regions:
            assert region.bar_start == current
            current += region.bar_count


# ---------- Vocal entry tests ----------


class TestVocalEntry:
    def test_instrumental_opening_no_vocal(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.INSTRUMENTAL_OPENING])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].vocal_entry == VocalEntry.NONE

    def test_verse_has_main_vocal(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].vocal_entry == VocalEntry.MAIN

    def test_chorus_has_main_vocal(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.CHORUS])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].vocal_entry == VocalEntry.MAIN

    def test_dub_breakdown_has_whisper(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.DUB_BREAKDOWN])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].vocal_entry == VocalEntry.WHISPER

    def test_outro_no_vocal(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.OUTRO])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].vocal_entry == VocalEntry.NONE

    def test_vocal_count(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        # INSTRUMENTAL_OPENING + OUTRO = 2 instrumental
        assert result.instrumental_regions == 2
        # VERSE + PRE_CHORUS + CHORUS + DUB_BREAKDOWN + VERSE + CHORUS = 6 vocal
        assert result.vocal_regions == 6


# ---------- Lane assignment tests ----------


class TestLaneAssignments:
    def test_vocal_lanes_absent_in_instrumental(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.INSTRUMENTAL_OPENING])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        region = result.arrangement.regions[0]
        assert StemLaneType.VOCALS_MAIN not in region.lanes_active
        assert StemLaneType.VOCALS_ADLIBS not in region.lanes_active

    def test_vocal_lanes_present_in_verse(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        region = result.arrangement.regions[0]
        assert StemLaneType.VOCALS_MAIN in region.lanes_active

    def test_chorus_has_adlibs(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.CHORUS])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        region = result.arrangement.regions[0]
        assert StemLaneType.VOCALS_ADLIBS in region.lanes_active

    def test_muted_complement(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        region = result.arrangement.regions[0]
        # Active + muted should cover all 12 lanes
        all_lanes = set(region.lanes_active) | set(region.lanes_muted)
        assert len(all_lanes) == 12

    def test_lane_assignments_non_empty(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert len(result.arrangement.lane_assignments) > 0
        # Every assignment should reference at least one region
        for la in result.arrangement.lane_assignments:
            assert len(la.active_regions) > 0


# ---------- Energy map tests ----------


class TestEnergyMap:
    def test_energy_map_count_matches_regions(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert len(result.arrangement.energy_map) == len(result.arrangement.regions)

    def test_standard_profile_intro_low(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.INSTRUMENTAL_OPENING])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id, energy_profile="standard")
        result = compile_soundgraph(version, request)
        assert result.arrangement.energy_map[0].energy == EnergyLevel.LOW

    def test_standard_profile_chorus_peak(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.CHORUS])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id, energy_profile="standard")
        result = compile_soundgraph(version, request)
        assert result.arrangement.energy_map[0].energy == EnergyLevel.PEAK

    def test_flat_profile_all_medium(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id, energy_profile="flat")
        result = compile_soundgraph(version, request)
        for point in result.arrangement.energy_map:
            assert point.energy == EnergyLevel.MEDIUM

    def test_unknown_profile_warns(self) -> None:
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id, energy_profile="nonexistent")
        result = compile_soundgraph(version, request)
        assert any("Unknown energy_profile" in w for w in result.warnings)


# ---------- Bar override tests ----------


class TestBarOverrides:
    def test_default_bars(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].bar_count == 16  # default for verse

    def test_override_bars(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(
            lyrics_version_id=version.id,
            bars_per_section_override={"verse": 32},
        )
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].bar_count == 32

    def test_override_clamped_to_64(self) -> None:
        version = _make_lyrics_version(sections=[LyricsSectionType.VERSE])
        request = SoundGraphWriteRequest(
            lyrics_version_id=version.id,
            bars_per_section_override={"verse": 128},
        )
        result = compile_soundgraph(version, request)
        assert result.arrangement.regions[0].bar_count == 64


# ---------- Repository tests ----------


class TestSoundGraphRepository:
    def test_store_and_get(self) -> None:
        repo = SoundGraphRepository()
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)

        stored = repo.store(result.arrangement)
        assert repo.get(stored.arrangement_id) is not None

    def test_get_by_lyrics_version(self) -> None:
        repo = SoundGraphRepository()
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        repo.store(result.arrangement)

        found = repo.get_by_lyrics_version(version.id)
        assert found is not None
        assert found.lyrics_version_id == version.id

    def test_not_found(self) -> None:
        repo = SoundGraphRepository()
        assert repo.get(uuid4()) is None
        assert repo.get_by_lyrics_version(uuid4()) is None

    def test_count(self) -> None:
        repo = SoundGraphRepository()
        assert repo.count() == 0
        version = _make_lyrics_version()
        request = SoundGraphWriteRequest(lyrics_version_id=version.id)
        result = compile_soundgraph(version, request)
        repo.store(result.arrangement)
        assert repo.count() == 1


# ---------- Route tests ----------


class TestSoundGraphRoutes:
    def test_compile_requires_valid_lyrics_version(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                inference_main.compile_soundgraph_route(
                    SoundGraphWriteRequest(lyrics_version_id=uuid4(), bpm=140),
                    DEV_OPERATOR,
                )
            )
        assert exc_info.value.status_code == 404

    def test_compile_end_to_end(self) -> None:
        # Create a lyrics version via the route function
        lyrics_version = asyncio.run(
            inference_main.create_lyrics(
                LyricsGenerationRequest(
                    project_key="soundgraph-test-e2e",
                    prompt="dark warehouse anthem with heavy drops",
                    character_code="SHIBARI_KAWAII",
                    target_language="en",
                ),
                DEV_OPERATOR,
            )
        )

        # Now compile the soundgraph
        result = asyncio.run(
            inference_main.compile_soundgraph_route(
                SoundGraphWriteRequest(
                    lyrics_version_id=lyrics_version.id,
                    bpm=145,
                    energy_profile="standard",
                ),
                DEV_OPERATOR,
            )
        )
        assert result.section_count > 0
        assert result.total_bars > 0
        assert result.arrangement.bpm == 145
        assert len(result.arrangement.regions) > 0
        assert len(result.arrangement.energy_map) > 0
        assert len(result.arrangement.lane_assignments) > 0

        # Verify we can retrieve it
        arr = asyncio.run(
            inference_main.get_soundgraph_arrangement(result.arrangement.arrangement_id)
        )
        assert arr.arrangement_id == result.arrangement.arrangement_id

        # By lyrics version
        by_version = asyncio.run(inference_main.get_soundgraph_by_lyrics_version(lyrics_version.id))
        assert by_version.lyrics_version_id == lyrics_version.id

        # List
        all_arr = asyncio.run(inference_main.list_soundgraph_arrangements())
        assert len(all_arr) >= 1

    def test_arrangement_not_found(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(inference_main.get_soundgraph_arrangement(uuid4()))
        assert exc_info.value.status_code == 404

    def test_by_lyrics_version_not_found(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(inference_main.get_soundgraph_by_lyrics_version(uuid4()))
        assert exc_info.value.status_code == 404

    def test_capabilities_includes_soundgraph(self) -> None:
        caps = asyncio.run(inference_main.capabilities())
        assert caps.soundgraph_writer_available is True
