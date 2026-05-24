from __future__ import annotations

import hashlib
from typing import Sequence

from app.lyrics_engine import resolve_structure
from app.schemas import (
    LyricsEditRequest,
    LyricsGenerationRequest,
    LyricsLine,
    LyricsRewriteSelectionRequest,
    LyricsRewriteVariant,
    LyricsSection,
    LyricsSectionType,
    LyricsSource,
    LyricsStructure,
)


# Deterministic per-section line templates. Internal scaffold only — real
# generation lands when GPT-5.5 wiring or local model is added.
SECTION_TEMPLATES: dict[LyricsSectionType, tuple[str, ...]] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: (
        "[instrumental — sub only]",
        "[no vocal entry before first verse]",
    ),
    LyricsSectionType.VERSE: (
        "Cold room remembers how the night moved.",
        "Concrete keeps the sound until the room is empty.",
        "Nothing here belongs to me. Nothing I will say.",
        "Black mirror, late hour, slow signal pressure.",
    ),
    LyricsSectionType.PRE_CHORUS: (
        "Pull the line in.",
        "Wait for the pressure to land.",
    ),
    LyricsSectionType.CHORUS: (
        "No bright room.",
        "No soft return.",
        "Night stays material.",
        "Hold the signal until it shakes.",
    ),
    LyricsSectionType.BRIDGE: (
        "Step away from the room.",
        "Wait for the next pressure cycle.",
    ),
    LyricsSectionType.DUB_BREAKDOWN: (
        "[delay throws · vocal off]",
        "[spring reverb · low pulse]",
    ),
    LyricsSectionType.OUTRO: (
        "Concrete keeps the sound.",
        "The room stays cold.",
    ),
}


SECTION_LABELS: dict[LyricsSectionType, str] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: "INTRO (INSTRUMENTAL)",
    LyricsSectionType.VERSE: "VERSE",
    LyricsSectionType.PRE_CHORUS: "PRE-CHORUS",
    LyricsSectionType.CHORUS: "CHORUS",
    LyricsSectionType.BRIDGE: "BRIDGE",
    LyricsSectionType.DUB_BREAKDOWN: "DUB BREAKDOWN",
    LyricsSectionType.OUTRO: "OUTRO",
}


def _seed_from(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _label_for(section_type: LyricsSectionType, occurrence: int) -> str:
    base = SECTION_LABELS[section_type]
    if section_type in (
        LyricsSectionType.INSTRUMENTAL_OPENING,
        LyricsSectionType.DUB_BREAKDOWN,
        LyricsSectionType.OUTRO,
        LyricsSectionType.BRIDGE,
    ):
        return base
    return f"{base} {occurrence}"


def _build_lines(section_type: LyricsSectionType, seed: int, offset: int = 0) -> list[LyricsLine]:
    template = SECTION_TEMPLATES[section_type]
    rotation = (seed + offset) % len(template)
    rotated = template[rotation:] + template[:rotation]
    lines: list[LyricsLine] = []
    for index, text in enumerate(rotated):
        lines.append(
            LyricsLine(
                index=index,
                text=text,
                syllables=_estimate_syllables(text),
                rhyme_group=_rhyme_group(section_type, index),
            )
        )
    return lines


def _estimate_syllables(text: str) -> int:
    # Internal stub. Honest estimate for tests: count vowel clusters in word chars.
    cleaned = "".join(ch.lower() if ch.isalpha() else " " for ch in text)
    count = 0
    in_vowel = False
    for ch in cleaned:
        is_vowel = ch in "aeiouy"
        if is_vowel and not in_vowel:
            count += 1
        in_vowel = is_vowel
    return max(count, 1)


def _rhyme_group(section_type: LyricsSectionType, index: int) -> str | None:
    if section_type in (
        LyricsSectionType.INSTRUMENTAL_OPENING,
        LyricsSectionType.DUB_BREAKDOWN,
    ):
        return None
    return chr(ord("A") + (index % 2))


def _find_template_rotation(section_type: LyricsSectionType, lines: list[LyricsLine]) -> int | None:
    template = SECTION_TEMPLATES[section_type]
    if not lines:
        return None
    first_text = lines[0].text
    for rotation, template_line in enumerate(template):
        if template_line == first_text:
            return rotation
    return None


def _build_edit_lines(
    section_type: LyricsSectionType,
    current_lines: list[LyricsLine],
    seed: int,
) -> list[LyricsLine]:
    """Pick a rotation that is guaranteed to differ from the current one.

    Why: the mock provider's lines come from a small per-section template;
    a pure (seed + offset) rotation can coincidentally hit the same index
    that produced the current text, which would make an edit a no-op for
    tests that assert "verse changed". This helper inspects the current
    section content to find its rotation and then advances by a seed-derived
    non-zero delta.
    """
    template = SECTION_TEMPLATES[section_type]
    n = len(template)
    if n < 2:
        # Single-entry templates cannot rotate. Return the template verbatim.
        return [
            LyricsLine(
                index=line_index,
                text=text,
                syllables=_estimate_syllables(text),
                rhyme_group=_rhyme_group(section_type, line_index),
            )
            for line_index, text in enumerate(template)
        ]
    current_rotation = _find_template_rotation(section_type, current_lines)
    if current_rotation is None:
        # Manually-edited content; no template match. Seed picks any rotation.
        new_rotation = seed % n
    else:
        delta = (seed % (n - 1)) + 1  # always in [1, n - 1]
        new_rotation = (current_rotation + delta) % n
    rotated = template[new_rotation:] + template[:new_rotation]
    return [
        LyricsLine(
            index=line_index,
            text=text,
            syllables=_estimate_syllables(text),
            rhyme_group=_rhyme_group(section_type, line_index),
        )
        for line_index, text in enumerate(rotated)
    ]


class MockLyricsProvider:
    """Deterministic lyrics provider for internal scaffolding.

    Produces stable line content per (section_type, seed) so test assertions
    can rely on byte-for-byte equality. Does not call any external service.
    """

    name = "mock-lyrics"

    async def generate(self, request: LyricsGenerationRequest) -> LyricsStructure:
        structure_types = resolve_structure(request)
        seed = _seed_from(f"{request.project_key}|{request.prompt}|{request.character_code}")
        occurrence_counts: dict[LyricsSectionType, int] = {}
        sections: list[LyricsSection] = []
        for absolute_index, section_type in enumerate(structure_types):
            occurrence_counts[section_type] = occurrence_counts.get(section_type, 0) + 1
            sections.append(
                LyricsSection(
                    index=absolute_index,
                    section_type=section_type,
                    label=_label_for(section_type, occurrence_counts[section_type]),
                    lines=_build_lines(section_type, seed, offset=absolute_index),
                    locked=False,
                    manually_edited=False,
                    source=LyricsSource.MOCK,
                )
            )
        return LyricsStructure(
            sections=sections,
            avoid_intro_singing=request.avoid_intro_singing,
            target_language=request.target_language,
        )

    async def edit(self, current: LyricsStructure, request: LyricsEditRequest) -> LyricsStructure:
        seed = _seed_from(f"{request.version_id}|{request.edit_prompt}")
        new_sections: list[LyricsSection] = []
        for section in current.sections:
            if section.locked:
                new_sections.append(section.model_copy(deep=True))
                continue
            should_regen = self._matches_target(section, request)
            if not should_regen:
                new_sections.append(section.model_copy(deep=True))
                continue
            regenerated = section.model_copy(deep=True)
            regenerated.lines = _build_edit_lines(
                section.section_type, section.lines, seed + section.index
            )
            regenerated.manually_edited = False
            regenerated.source = LyricsSource.MOCK
            new_sections.append(regenerated)
        return LyricsStructure(
            sections=new_sections,
            avoid_intro_singing=current.avoid_intro_singing,
            target_language=current.target_language,
        )

    @staticmethod
    def _matches_target(section: LyricsSection, request: LyricsEditRequest) -> bool:
        if (
            request.target_section_index is not None
            and section.index == request.target_section_index
        ):
            return True
        if request.target_section is not None and section.section_type is request.target_section:
            return True
        if request.target_section_index is None and request.target_section is None:
            return True
        return False

    async def rewrite_selection(
        self, current: LyricsStructure, request: LyricsRewriteSelectionRequest
    ) -> list[LyricsRewriteVariant]:
        section = current.sections[request.section_index]
        original = section.lines[request.line_start_index : request.line_end_index + 1]
        if not original:
            return []
        base_seed = _seed_from(f"{request.version_id}|{request.rewrite_prompt}")
        variants: list[LyricsRewriteVariant] = []
        for variant_index in range(request.variant_count):
            seed = base_seed + variant_index
            variants.append(
                LyricsRewriteVariant(
                    index=variant_index,
                    lines=_rewrite_lines(original, seed, variant_index),
                    summary=f"variant {variant_index + 1}",
                )
            )
        return variants

    def apply_selection_rewrite(
        self,
        current: LyricsStructure,
        section_index: int,
        new_lines: Sequence[str],
        lock: bool,
    ) -> LyricsStructure:
        new_sections: list[LyricsSection] = []
        for section in current.sections:
            if section.index != section_index:
                new_sections.append(section.model_copy(deep=True))
                continue
            updated = section.model_copy(deep=True)
            updated.lines = [
                LyricsLine(
                    index=line_index,
                    text=text,
                    syllables=_estimate_syllables(text),
                    rhyme_group=_rhyme_group(updated.section_type, line_index),
                )
                for line_index, text in enumerate(new_lines)
            ]
            # Source stays MOCK (provider produced the variant); manually_edited
            # stays False because the operator did not type these lines.
            updated.source = LyricsSource.MOCK
            updated.manually_edited = False
            if lock:
                updated.locked = True
            new_sections.append(updated)
        return LyricsStructure(
            sections=new_sections,
            avoid_intro_singing=current.avoid_intro_singing,
            target_language=current.target_language,
        )

    def apply_lock_toggle(
        self, current: LyricsStructure, section_index: int, locked: bool
    ) -> LyricsStructure:
        new_sections: list[LyricsSection] = []
        for section in current.sections:
            if section.index != section_index:
                new_sections.append(section.model_copy(deep=True))
                continue
            updated = section.model_copy(deep=True)
            updated.locked = locked
            new_sections.append(updated)
        return LyricsStructure(
            sections=new_sections,
            avoid_intro_singing=current.avoid_intro_singing,
            target_language=current.target_language,
        )

    def apply_manual_update(
        self,
        current: LyricsStructure,
        section_index: int,
        new_lines: Sequence[str],
        lock: bool,
        notes: str | None,
    ) -> LyricsStructure:
        new_sections: list[LyricsSection] = []
        for section in current.sections:
            if section.index != section_index:
                new_sections.append(section.model_copy(deep=True))
                continue
            updated = section.model_copy(deep=True)
            updated.lines = [
                LyricsLine(
                    index=line_index,
                    text=text,
                    syllables=_estimate_syllables(text),
                    rhyme_group=_rhyme_group(updated.section_type, line_index),
                )
                for line_index, text in enumerate(new_lines)
            ]
            updated.manually_edited = True
            updated.source = LyricsSource.USER
            updated.locked = lock
            if notes is not None:
                updated.notes = notes
            new_sections.append(updated)
        return LyricsStructure(
            sections=new_sections,
            avoid_intro_singing=current.avoid_intro_singing,
            target_language=current.target_language,
        )


def _rewrite_lines(
    original: Sequence[LyricsLine], seed: int, variant_index: int
) -> list[LyricsLine]:
    rotation = (seed + variant_index) % max(len(original), 1)
    rotated = list(original[rotation:]) + list(original[:rotation])
    rewritten: list[LyricsLine] = []
    for index, line in enumerate(rotated):
        rewritten.append(
            LyricsLine(
                index=index,
                text=line.text,
                syllables=line.syllables,
                rhyme_group=line.rhyme_group,
                vocal_note=line.vocal_note,
            )
        )
    return rewritten
