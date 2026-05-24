"""Lyrics Provider Isolation Layer (S13).

Protocol + factory. Every lyrics provider implementation must satisfy
`LyricsProviderProtocol`. The factory function `build_lyrics_provider()`
reads `SOUNDSYSTEM_LYRICS_PROVIDER` and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic local output, no API call.
- "gpt_5_5" — OpenAI GPT-5.5 via the official SDK. Requires OPENAI_API_KEY.

Adding a new provider:
1. Implement `LyricsProviderProtocol` in a new submodule.
2. Register the value in `LyricsProviderMode`.
3. Add the construction branch to `build_lyrics_provider()`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, Sequence

from app.schemas import (
    LyricsEditRequest,
    LyricsGenerationRequest,
    LyricsRewriteSelectionRequest,
    LyricsRewriteVariant,
    LyricsStructure,
)


class LyricsProviderMode(StrEnum):
    MOCK = "mock"
    GPT_5_5 = "gpt_5_5"


class LyricsProviderProtocol(Protocol):
    """Shared interface for all lyrics providers.

    Each method corresponds to one operator action. The Protocol
    guarantees that swapping providers does not touch route handlers.
    """

    name: str

    async def generate(self, request: LyricsGenerationRequest) -> LyricsStructure: ...

    async def edit(
        self, current: LyricsStructure, request: LyricsEditRequest
    ) -> LyricsStructure: ...

    async def rewrite_selection(
        self, current: LyricsStructure, request: LyricsRewriteSelectionRequest
    ) -> list[LyricsRewriteVariant]: ...

    def apply_selection_rewrite(
        self,
        current: LyricsStructure,
        section_index: int,
        new_lines: Sequence[str],
        lock: bool,
    ) -> LyricsStructure: ...

    def apply_lock_toggle(
        self, current: LyricsStructure, section_index: int, locked: bool
    ) -> LyricsStructure: ...

    def apply_manual_update(
        self,
        current: LyricsStructure,
        section_index: int,
        new_lines: Sequence[str],
        lock: bool,
        notes: str | None,
    ) -> LyricsStructure: ...


def build_lyrics_provider() -> LyricsProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - GPT_5_5: requires openai SDK + OPENAI_API_KEY. Fails loudly if missing.
    """
    from app.config import lyrics_provider_mode, LyricsProviderMode

    mode = lyrics_provider_mode()

    if mode == LyricsProviderMode.GPT_5_5:
        from app.providers.lyrics.gpt_5_5 import Gpt55LyricsProvider

        return Gpt55LyricsProvider()  # type: ignore[return-value]

    # Default: mock
    from app.lyrics_provider import MockLyricsProvider

    return MockLyricsProvider()  # type: ignore[return-value]
