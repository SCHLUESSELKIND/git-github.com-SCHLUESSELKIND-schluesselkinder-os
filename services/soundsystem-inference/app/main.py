from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI, HTTPException

from app.prompt_engine import compile_prompt
from app.providers.registry import build_default_provider_registry
from app.repository import GenerationJobRepository, InMemoryGenerationJobRepository
from app.schemas import (
    Atmosphere,
    BassPressure,
    CapabilitiesResponse,
    CompiledPrompt,
    CompiledPromptRequest,
    Energy,
    Engine,
    GenerationJob,
    GenerationRequest,
    Intent,
    JobEventType,
    JobStatus,
    ProviderCapability,
    Structure,
    Vocals,
)

app = FastAPI(
    title="SNUFFRAGA SOUNDSYSTEM AI ENGINE",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

job_repository: GenerationJobRepository = InMemoryGenerationJobRepository()
provider_registry = build_default_provider_registry()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "snuffraga-soundsystem-inference"}


@app.get("/v1/capabilities")
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        service="snuffraga-soundsystem-inference",
        engines=[engine for engine in Engine],
        intents=[intent for intent in Intent],
        prompt_modules={
            "energy": [item.value for item in Energy],
            "bass_pressure": [item.value for item in BassPressure],
            "vocals": [item.value for item in Vocals],
            "atmosphere": [item.value for item in Atmosphere],
            "structure": [item.value for item in Structure],
        },
        providers=[
            ProviderCapability(
                name=provider.name,
                engine=provider.engine,
                available=provider.available,
                fallback=provider.fallback,
            )
            for provider in await provider_registry.health_check()
        ],
    )


@app.post("/v1/prompts/compile")
async def compile_prompt_route(request: CompiledPromptRequest) -> CompiledPrompt:
    return compile_prompt(request)


@app.post("/v1/generations")
async def create_generation(request: GenerationRequest) -> GenerationJob:
    compiled = compile_prompt(
        CompiledPromptRequest(
            intent=request.intent,
            prompt_modules=request.prompt_modules,
            character_code=request.character_code,
            lyrics=request.lyrics,
            technical=request.technical,
        )
    )

    job = job_repository.create(request, compiled)

    if request.safety.allow_voice_likeness:
        job_repository.set_error(job.id, "voice_likeness_requires_explicit_clearance")
        return job_repository.update_status(
            job.id,
            JobStatus.PREFLIGHT_BLOCKED,
            progress=0,
            event_type=JobEventType.PREFLIGHT_BLOCKED,
        )

    # MVP scaffold: run the selected provider inline. Real engines should move into workers.
    provider = provider_registry.select(request.engine)
    job_repository.append_event(
        job.id,
        JobEventType.WORKER_ASSIGNED,
        detail=f"provider:{provider.name}",
    )
    job_repository.update_status(
        job.id, JobStatus.RUNNING, 0.35, JobEventType.GENERATION_STARTED
    )

    start_result = await provider.start(request, compiled)
    provider_status = await provider.get_status(start_result.external_job_id)

    if provider_status.status == "failed":
        job_repository.set_error(
            job.id,
            provider_status.error or "provider_generation_failed",
        )
        return job_repository.update_status(
            job.id, JobStatus.FAILED, provider_status.progress, JobEventType.JOB_FAILED
        )

    if provider_status.artifacts is not None:
        job_repository.set_artifacts(job.id, provider_status.artifacts)

    job_repository.update_status(
        job.id, JobStatus.ANALYZING_SAFETY, 0.8, JobEventType.SAFETY_STARTED
    )
    return job_repository.update_status(
        job.id, JobStatus.EXPORT_READY, 1.0, JobEventType.ARTIFACT_READY
    )


@app.get("/v1/generations/{job_id}")
async def get_generation(job_id: UUID) -> GenerationJob:
    job = job_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="generation_not_found")
    return job
