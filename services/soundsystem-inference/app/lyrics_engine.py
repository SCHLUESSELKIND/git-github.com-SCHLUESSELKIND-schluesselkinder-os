from __future__ import annotations

from app.schemas import (
    CompiledLyricsPrompt,
    LyricsGenerationRequest,
    LyricsSectionType,
)


DEFAULT_STRUCTURE: tuple[LyricsSectionType, ...] = (
    LyricsSectionType.VERSE,
    LyricsSectionType.PRE_CHORUS,
    LyricsSectionType.CHORUS,
    LyricsSectionType.VERSE,
    LyricsSectionType.CHORUS,
    LyricsSectionType.BRIDGE,
    LyricsSectionType.DUB_BREAKDOWN,
    LyricsSectionType.CHORUS,
    LyricsSectionType.OUTRO,
)


# Filler patterns Suno-style models tend to insert for an "instant emotional hook"
# but that contradict SCHLUESSELKINDER tone. Detected so the compiler can warn
# and the negative prompt can suppress them.
RISKY_FILLER_PATTERNS: tuple[str, ...] = (
    "oh oh oh",
    "na na na",
    "da da da",
    "la la la",
    "yeah yeah yeah",
    "whoa oh",
    "woah oh",
)


def detect_risky_filler(text: str) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in RISKY_FILLER_PATTERNS if pattern in lowered]


def resolve_structure(request: LyricsGenerationRequest) -> list[LyricsSectionType]:
    structure = list(request.structure) if request.structure else list(DEFAULT_STRUCTURE)
    if request.avoid_intro_singing:
        if not structure or structure[0] is not LyricsSectionType.INSTRUMENTAL_OPENING:
            structure.insert(0, LyricsSectionType.INSTRUMENTAL_OPENING)
    return structure


def compile_lyrics_prompt(request: LyricsGenerationRequest) -> CompiledLyricsPrompt:
    structure = resolve_structure(request)

    rhyme_clause = (
        " Preserve rhyme groups across verses." if request.preserve_rhyme else " Rhyme is optional."
    )
    syllable_clause = (
        " Preserve syllable length per line so existing vocal phrasing still fits."
        if request.preserve_syllable_length
        else ""
    )
    intro_clause = (
        " First section is instrumental — no vocal entry before the first verse."
        if request.avoid_intro_singing
        else ""
    )

    instruction = (
        f"Write {request.target_language} lyrics for character {request.character_code}. "
        f"Brief: {request.prompt.strip()}."
        f" Structure: {', '.join(section.value for section in structure)}."
        f"{rhyme_clause}{syllable_clause}{intro_clause}"
    )

    negative_prompt = (
        "No 'Oh oh oh' or 'Na na na' intros. No filler ad-libs. "
        "No named-artist references. No third-party song quotes. "
        "No festival affirmation cliches. No cheerful SaaS-pop vocabulary."
    )

    safety_notes = [
        "Reject lyrics that reference living artists by name.",
        "Reject lyrics that copy lines from known commercial songs.",
        "Voice-likeness performance still requires explicit clearance downstream.",
    ]

    risky_found = detect_risky_filler(request.prompt)
    if risky_found:
        safety_notes.append(
            "Brief contains filler intro patterns: "
            + ", ".join(risky_found)
            + ". Treat as red flag; the brief was rewritten before compilation."
        )

    suno_compat_notes = [
        "Suno-style export uses uppercase bracket tags such as [VERSE], [CHORUS].",
        "Adlib hints in parentheses '(oh)' map to vocals_adlibs lane on SoundGraph export.",
        "Suno bias toward 'oh oh oh' openings is suppressed by the negative prompt above.",
    ]

    soundgraph_compat_notes = [
        "Vocal lanes split into vocals_main and vocals_adlibs on SoundGraph export.",
        "Each section maps to a SoundGraph arrangement region addressable for stem regeneration.",
        "Locked sections are preserved byte-for-byte across edit requests.",
    ]

    return CompiledLyricsPrompt(
        instruction=instruction,
        negative_prompt=negative_prompt,
        safety_notes=safety_notes,
        suno_compat_notes=suno_compat_notes,
        soundgraph_compat_notes=soundgraph_compat_notes,
        structure=structure,
        risky_filler_patterns=risky_found,
    )
