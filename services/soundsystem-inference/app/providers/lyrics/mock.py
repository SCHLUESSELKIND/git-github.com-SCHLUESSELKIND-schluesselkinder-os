"""Mock lyrics provider — re-export from the original module.

This file exists so that `from app.providers.lyrics.mock import
MockLyricsProvider` works alongside the legacy `from app.lyrics_provider
import MockLyricsProvider`. The single source of truth for the mock
implementation remains `app/lyrics_provider.py` until the original
module is retired.
"""

from app.lyrics_provider import MockLyricsProvider

__all__ = ["MockLyricsProvider"]
