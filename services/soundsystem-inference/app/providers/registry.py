from __future__ import annotations

from dataclasses import dataclass

from app.providers.base import MusicEngineProvider
from app.providers.mock import MockMusicProvider
from app.schemas import Engine


@dataclass(frozen=True)
class ProviderHealth:
    name: str
    engine: Engine
    available: bool
    fallback: bool


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[Engine, MusicEngineProvider] = {}

    def register(self, provider: MusicEngineProvider) -> None:
        self._providers[provider.engine] = provider

    def select(self, engine: Engine | None = None) -> MusicEngineProvider:
        if engine is not None and engine in self._providers:
            return self._providers[engine]

        fallback = self._providers.get(Engine.MOCK)
        if fallback is not None:
            return fallback

        try:
            return sorted(self._providers.values(), key=lambda provider: provider.priority)[0]
        except IndexError as exc:
            raise RuntimeError("no_music_engine_provider_available") from exc

    def list_available_providers(self) -> list[MusicEngineProvider]:
        return sorted(self._providers.values(), key=lambda provider: provider.priority)

    async def health_check(self) -> list[ProviderHealth]:
        results: list[ProviderHealth] = []
        fallback = self.select()

        for provider in self.list_available_providers():
            results.append(
                ProviderHealth(
                    name=provider.name,
                    engine=provider.engine,
                    available=await provider.is_available(),
                    fallback=provider is fallback,
                )
            )

        return results


def build_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(MockMusicProvider())
    return registry
