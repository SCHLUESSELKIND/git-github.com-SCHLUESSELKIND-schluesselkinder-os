from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.prompt_engine import compile_prompt
from app.providers.mock import MockMusicProvider
from app.providers.registry import ProviderRegistry, build_default_provider_registry
from app.repository import InMemoryGenerationJobRepository
from app.schemas import (
    Atmosphere,
    BassPressure,
    CompiledPromptRequest,
    Energy,
    Engine,
    GenerationRequest,
    Intent,
    JobEventType,
    JobStatus,
    PromptModules,
    SafetyOptions,
    Structure,
    Vocals,
)


@pytest.fixture(autouse=True)
def isolated_repository():
    original = inference_main.job_repository
    inference_main.job_repository = InMemoryGenerationJobRepository()
    try:
        yield inference_main.job_repository
    finally:
        inference_main.job_repository = original


@pytest.fixture(autouse=True)
def isolated_provider_registry():
    original = inference_main.provider_registry
    inference_main.provider_registry = build_default_provider_registry()
    try:
        yield inference_main.provider_registry
    finally:
        inference_main.provider_registry = original


def _make_request(*, allow_voice_likeness: bool = False) -> GenerationRequest:
    return GenerationRequest(
        project_id="snuffraga-warehouse-test",
        intent=Intent.CREATE_TRACK,
        engine=Engine.MOCK,
        prompt_modules=PromptModules(
            energy=Energy.WAREHOUSE,
            bass_pressure=BassPressure.CRUSHING,
            vocals=Vocals.HAUNTING,
            atmosphere=Atmosphere.BLACK_CONCRETE,
            structure=Structure.INSTANT_DROP,
        ),
        safety=SafetyOptions(allow_voice_likeness=allow_voice_likeness),
    )


def test_compile_prompt_includes_intent_modules_and_negative_guards():
    request = _make_request()
    compiled = compile_prompt(
        CompiledPromptRequest(
            intent=request.intent,
            prompt_modules=request.prompt_modules,
            character_code=request.character_code,
            lyrics=request.lyrics,
            technical=request.technical,
        )
    )

    assert "CREATE_TRACK" in compiled.prompt_text
    assert "SHIBARI_KAWAII" in compiled.prompt_text
    assert "concrete-room momentum" in compiled.prompt_text
    assert "No named artist imitation" in compiled.negative_prompt
    assert compiled.engine_hints["stems_required"] is True


def test_create_generation_runs_mock_provider_to_export_ready(isolated_repository):
    job = asyncio.run(inference_main.create_generation(_make_request()))

    assert job.status == JobStatus.EXPORT_READY
    assert job.progress == 1.0
    assert job.artifacts.full_mix_wav is not None
    assert job.artifacts.stems

    event_types = [event.event_type for event in job.events]
    assert JobEventType.JOB_CREATED in event_types
    assert JobEventType.WORKER_ASSIGNED in event_types
    assert JobEventType.GENERATION_STARTED in event_types
    assert JobEventType.SAFETY_STARTED in event_types
    assert JobEventType.ARTIFACT_READY in event_types

    assert isolated_repository.get(job.id) is job


def test_voice_likeness_blocks_generation_at_preflight(isolated_repository):
    job = asyncio.run(
        inference_main.create_generation(_make_request(allow_voice_likeness=True))
    )

    assert job.status == JobStatus.PREFLIGHT_BLOCKED
    assert job.error == "voice_likeness_requires_explicit_clearance"
    assert job.artifacts.full_mix_wav is None
    assert job.artifacts.stems == []

    event_types = [event.event_type for event in job.events]
    assert JobEventType.PREFLIGHT_BLOCKED in event_types
    assert JobEventType.GENERATION_STARTED not in event_types

    assert isolated_repository.get(job.id).status == JobStatus.PREFLIGHT_BLOCKED


def test_get_generation_with_unknown_id_returns_404():
    with pytest.raises(HTTPException) as info:
        asyncio.run(inference_main.get_generation(uuid4()))

    assert info.value.status_code == 404
    assert info.value.detail == "generation_not_found"


def test_provider_registry_health_checks_and_falls_back_to_mock():
    registry = ProviderRegistry()
    registry.register(MockMusicProvider())

    provider = registry.select(Engine.ACE_STEP)
    health = asyncio.run(registry.health_check())

    assert provider.name == "mock"
    assert health[0].name == "mock"
    assert health[0].engine == Engine.MOCK
    assert health[0].available is True
    assert health[0].fallback is True
