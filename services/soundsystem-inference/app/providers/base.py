from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from app.schemas import ArtifactManifest, CompiledPrompt, Engine, GenerationRequest, Intent


@dataclass(frozen=True)
class ProviderStart:
    external_job_id: str


@dataclass(frozen=True)
class ProviderStatus:
    status: Literal["processing", "completed", "failed"]
    progress: float
    artifacts: ArtifactManifest | None = None
    error: str | None = None


class MusicEngineProvider(Protocol):
    name: str
    engine: Engine
    supported_intents: tuple[Intent, ...]
    max_duration_seconds: int
    priority: int

    async def start(
        self, request: GenerationRequest, compiled_prompt: CompiledPrompt
    ) -> ProviderStart:
        """Start generation and return the provider-native job id."""
        ...

    async def get_status(self, external_job_id: str) -> ProviderStatus:
        """Return current provider status for a previously started job."""
        ...

    async def is_available(self) -> bool:
        """Report whether the provider is configured and reachable."""
        ...

    def estimate_cost(self, duration_seconds: int) -> float:
        """Estimate provider cost for routing and future UI display."""
        ...
