from __future__ import annotations

from uuid import uuid4

from app.providers.base import ProviderStart, ProviderStatus
from app.schemas import (
    ArtifactManifest,
    CompiledPrompt,
    Engine,
    GenerationRequest,
    Intent,
    StemArtifact,
    StemLaneType,
    StemSourceType,
)


class MockMusicProvider:
    name = "mock"
    engine = Engine.MOCK
    supported_intents = tuple(Intent)
    max_duration_seconds = 600
    priority = 999

    def __init__(self) -> None:
        self._results: dict[str, ArtifactManifest] = {}

    async def start(
        self, request: GenerationRequest, compiled_prompt: CompiledPrompt
    ) -> ProviderStart:
        external_job_id = f"mock-{uuid4()}"
        self._results[external_job_id] = self._build_manifest(request, compiled_prompt)
        return ProviderStart(external_job_id=external_job_id)

    async def get_status(self, external_job_id: str) -> ProviderStatus:
        artifacts = self._results.get(external_job_id)
        if artifacts is None:
            return ProviderStatus(
                status="failed",
                progress=0,
                error="mock_generation_not_found",
            )

        return ProviderStatus(status="completed", progress=1, artifacts=artifacts)

    async def is_available(self) -> bool:
        return True

    def estimate_cost(self, duration_seconds: int) -> float:
        return 0

    def _build_manifest(
        self, request: GenerationRequest, compiled_prompt: CompiledPrompt
    ) -> ArtifactManifest:
        base = f"/tmp/snuffraga/{request.project_id}"
        stem_lanes = [
            StemArtifact(
                lane=lane,
                path=f"{base}/stems/{lane.value}.wav",
                source=StemSourceType.GENERATED_DIRECT,
                sample_rate=48000,
                bit_depth=24,
            )
            for lane in StemLaneType
        ]
        return ArtifactManifest(
            full_mix_wav=f"{base}/full_mix.wav",
            stems=[stem.path for stem in stem_lanes],
            stem_lanes=stem_lanes,
            soundgraph_manifest_json=f"{base}/soundgraph.json",
            lyrics=f"{base}/lyrics.txt",
            prompt_json=f"{base}/prompt.json",
            metadata_json=f"{base}/metadata.json",
            cover_image=f"{base}/cover.png",
            safety_report_json=f"{base}/safety_report.json",
            generation_history_json=f"{base}/generation_history.json",
        )
