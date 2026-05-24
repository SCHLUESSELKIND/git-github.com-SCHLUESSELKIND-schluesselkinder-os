"""GPT-5.5 Lyrics Provider (S13 — First Real Provider Boundary).

This is the first non-mock provider in the SNUFFRAGA SOUNDSYSTEM. It calls
the OpenAI API via the official SDK. Hard rules:

1. Provider Isolation: implements LyricsProviderProtocol; route handlers
   never see OpenAI types.
2. Cost Accounting: every call records prompt_tokens, completion_tokens,
   estimated_cost_usd, latency_ms, raw_provider_trace_id.
3. Hard Timeout: request-level timeout from config; no admin UI freeze.
4. Shadow Prompt Logging: raw_operator_prompt, compiled_prompt,
   system_prompt_version, safety_transformations all persisted.

The provider is instantiated only when SOUNDSYSTEM_LYRICS_PROVIDER=gpt_5_5.
Missing OPENAI_API_KEY fails loudly at startup with LyricsProviderConfigError.
No silent fallback to mock.

The openai SDK is imported lazily so the service can start without it
installed when running in mock mode.
"""

from __future__ import annotations

import time
from typing import Sequence

from app.config import (
    lyrics_provider_max_retries,
    lyrics_provider_timeout_ms,
    openai_api_key,
)
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

# System prompt version — bump when the prompt template changes meaningfully.
# Stored in provenance so we can trace quality drift to prompt changes.
SYSTEM_PROMPT_VERSION = "gpt55-lyrics-v1.0"

_SYSTEM_PROMPT = """You are SNUFFRAGA SOUNDSYSTEM's internal lyrics engine.
You write lyrics for electronic music with warehouse, dub, and dark ambient character.

Rules:
- Write in the target language specified.
- Respect the section structure provided.
- Never reference real artists, real tracks, or real brands.
- Produce only original text.
- Keep lines rhythmically tight — syllable count matters.
- If a section is marked [instrumental], output only a stage direction in brackets.
- Respond in JSON matching the schema provided.
"""

_SECTION_LABELS: dict[LyricsSectionType, str] = {
    LyricsSectionType.INSTRUMENTAL_OPENING: "INTRO (INSTRUMENTAL)",
    LyricsSectionType.VERSE: "VERSE",
    LyricsSectionType.PRE_CHORUS: "PRE-CHORUS",
    LyricsSectionType.CHORUS: "CHORUS",
    LyricsSectionType.BRIDGE: "BRIDGE",
    LyricsSectionType.DUB_BREAKDOWN: "DUB BREAKDOWN",
    LyricsSectionType.OUTRO: "OUTRO",
}


class Gpt55LyricsProvider:
    """OpenAI GPT-5.5 lyrics provider with cost tracking and timeout policy."""

    name = "gpt-5.5-lyrics"

    def __init__(self) -> None:
        key = openai_api_key()
        if not key:
            from app.config import LyricsProviderConfigError

            raise LyricsProviderConfigError(
                "OPENAI_API_KEY is required when SOUNDSYSTEM_LYRICS_PROVIDER=gpt_5_5. "
                "Set the environment variable or switch to mock mode."
            )

        # Lazy import — openai SDK only required when this provider is active
        try:
            import openai  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "openai SDK required for gpt_5_5 lyrics provider. Install with: pip install openai"
            ) from e

        self._client = openai.OpenAI(
            api_key=key,
            timeout=lyrics_provider_timeout_ms() / 1000.0,
            max_retries=lyrics_provider_max_retries(),
        )
        self._timeout_ms = lyrics_provider_timeout_ms()
        self._max_retries = lyrics_provider_max_retries()

        # Accumulates per-call metadata for the route layer to read
        self.last_call_meta: dict | None = None

    def _call_chat(self, system: str, user: str, *, temperature: float = 0.85) -> tuple[str, dict]:
        """Make a chat completion call, returning (content, metadata).

        Metadata includes prompt_tokens, completion_tokens, latency_ms,
        estimated_cost_usd, raw_provider_trace_id.
        """
        start = time.monotonic()
        response = self._client.chat.completions.create(
            model="gpt-5.5",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        # Estimated cost (GPT-5.5 pricing approximate — update when known)
        # Placeholder: $0.01/1K input, $0.03/1K output
        estimated_cost = (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000.0

        content = response.choices[0].message.content or ""
        meta = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
            "latency_ms": latency_ms,
            "raw_provider_trace_id": response.id,
            "system_prompt_version": SYSTEM_PROMPT_VERSION,
        }
        self.last_call_meta = meta
        return content, meta

    def _parse_sections_json(
        self, raw: str, structure_types: list[LyricsSectionType]
    ) -> list[LyricsSection]:
        """Parse the JSON response into typed sections."""
        import json

        data = json.loads(raw)
        sections_data = data.get("sections", [])
        sections: list[LyricsSection] = []

        for idx, section_type in enumerate(structure_types):
            section_data = sections_data[idx] if idx < len(sections_data) else {}
            lines_data = section_data.get("lines", [])
            lines = [
                LyricsLine(
                    index=i,
                    text=line if isinstance(line, str) else line.get("text", ""),
                    syllables=line.get("syllables", 4) if isinstance(line, dict) else 4,
                    rhyme_group=None,
                )
                for i, line in enumerate(lines_data)
            ]
            occurrence = sum(1 for s in structure_types[: idx + 1] if s == section_type)
            label = _SECTION_LABELS[section_type]
            if section_type not in (
                LyricsSectionType.INSTRUMENTAL_OPENING,
                LyricsSectionType.DUB_BREAKDOWN,
                LyricsSectionType.OUTRO,
                LyricsSectionType.BRIDGE,
            ):
                label = f"{label} {occurrence}"

            sections.append(
                LyricsSection(
                    index=idx,
                    section_type=section_type,
                    label=label,
                    lines=lines,
                    locked=False,
                    manually_edited=False,
                    source=LyricsSource.GPT_5_5,
                )
            )
        return sections

    async def generate(self, request: LyricsGenerationRequest) -> LyricsStructure:
        structure_types = resolve_structure(request)

        user_prompt = (
            f"Project: {request.project_key}\n"
            f"Character: {request.character_code}\n"
            f"Language: {request.target_language}\n"
            f"Prompt: {request.prompt}\n\n"
            f"Structure: {[st.value for st in structure_types]}\n\n"
            f'Return JSON: {{"sections": [{{"lines": ["line1", ...]}}]}}\n'
            f"One section object per structure entry. Lines as string array."
        )

        raw, _meta = self._call_chat(_SYSTEM_PROMPT, user_prompt)
        sections = self._parse_sections_json(raw, structure_types)

        return LyricsStructure(
            sections=sections,
            avoid_intro_singing=request.avoid_intro_singing,
            target_language=request.target_language,
        )

    async def edit(self, current: LyricsStructure, request: LyricsEditRequest) -> LyricsStructure:
        # Serialize current for context
        current_text = "\n\n".join(
            f"[{s.label}]\n" + "\n".join(line.text for line in s.lines) for s in current.sections
        )
        target_hint = ""
        if request.target_section_index is not None:
            target_hint = f"\nFocus edit on section index {request.target_section_index}."
        elif request.target_section is not None:
            target_hint = f"\nFocus edit on section type: {request.target_section.value}."

        user_prompt = (
            f"Current lyrics:\n{current_text}\n\n"
            f"Edit instruction: {request.edit_prompt}{target_hint}\n\n"
            f"Locked sections (DO NOT CHANGE): "
            f"{[s.index for s in current.sections if s.locked]}\n\n"
            f'Return JSON: {{"sections": [{{"lines": ["line1", ...]}}]}}\n'
            f"Same section count. Respect locked sections verbatim."
        )

        raw, _meta = self._call_chat(_SYSTEM_PROMPT, user_prompt)
        structure_types = [s.section_type for s in current.sections]
        new_sections = self._parse_sections_json(raw, structure_types)

        # Enforce locked sections
        for i, section in enumerate(current.sections):
            if section.locked:
                new_sections[i] = section.model_copy(deep=True)

        return LyricsStructure(
            sections=new_sections,
            avoid_intro_singing=current.avoid_intro_singing,
            target_language=current.target_language,
        )

    async def rewrite_selection(
        self, current: LyricsStructure, request: LyricsRewriteSelectionRequest
    ) -> list[LyricsRewriteVariant]:
        section = current.sections[request.section_index]
        original = section.lines[request.line_start_index : request.line_end_index + 1]
        original_text = "\n".join(line.text for line in original)

        variants: list[LyricsRewriteVariant] = []
        for variant_index in range(request.variant_count):
            user_prompt = (
                f"Rewrite these lyrics lines (variant {variant_index + 1}):\n"
                f"{original_text}\n\n"
                f"Rewrite instruction: {request.rewrite_prompt}\n\n"
                f'Return JSON: {{"lines": ["line1", ...]}}'
            )
            raw, _meta = self._call_chat(
                _SYSTEM_PROMPT, user_prompt, temperature=0.9 + variant_index * 0.05
            )
            import json

            data = json.loads(raw)
            lines_data = data.get("lines", [])
            lines = [
                LyricsLine(
                    index=i,
                    text=line if isinstance(line, str) else "",
                    syllables=4,
                    rhyme_group=None,
                )
                for i, line in enumerate(lines_data)
            ]
            variants.append(
                LyricsRewriteVariant(
                    index=variant_index,
                    lines=lines,
                    summary=f"GPT-5.5 variant {variant_index + 1}",
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
        # Pure data operation — same as mock
        new_sections: list[LyricsSection] = []
        for section in current.sections:
            if section.index != section_index:
                new_sections.append(section.model_copy(deep=True))
                continue
            updated = section.model_copy(deep=True)
            updated.lines = [
                LyricsLine(index=i, text=text, syllables=4, rhyme_group=None)
                for i, text in enumerate(new_lines)
            ]
            updated.source = LyricsSource.GPT_5_5
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
                LyricsLine(index=i, text=text, syllables=4, rhyme_group=None)
                for i, text in enumerate(new_lines)
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
