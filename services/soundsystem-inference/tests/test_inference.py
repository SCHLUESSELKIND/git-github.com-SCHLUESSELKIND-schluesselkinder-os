from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.master_repository import InMemoryMasterBusRepository
from app.prompt_engine import compile_prompt
from app.providers.mock import MockMusicProvider
from app.providers.registry import ProviderRegistry, build_default_provider_registry
from app.repository import InMemoryGenerationJobRepository
from app.schemas import (
    Atmosphere,
    BassPressure,
    CompiledPromptRequest,
    DruckControls,
    DruckPreset,
    EffectDeviceType,
    Energy,
    Engine,
    ExportProfile,
    GenerationJob,
    GenerationRequest,
    Intent,
    JobEventType,
    JobStatus,
    MasterBusRequest,
    MasterJobStatus,
    MasteringMode,
    PromptModules,
    SafetyOptions,
    StemLaneType,
    Structure,
    TempoControls,
    TempoFeel,
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


@pytest.fixture(autouse=True)
def isolated_master_repository():
    original = inference_main.master_repository
    inference_main.master_repository = InMemoryMasterBusRepository()
    try:
        yield inference_main.master_repository
    finally:
        inference_main.master_repository = original


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


def _compiled_request(request: GenerationRequest) -> CompiledPromptRequest:
    return CompiledPromptRequest(
        intent=request.intent,
        prompt_modules=request.prompt_modules,
        character_code=request.character_code,
        lyrics=request.lyrics,
        technical=request.technical,
        tempo=request.tempo,
        druck=request.druck,
        requested_effects=request.requested_effects,
        target_lane=request.target_lane,
        locked_lanes=request.locked_lanes,
    )


def _make_generation() -> GenerationJob:
    return asyncio.run(inference_main.create_generation(_make_request(), DEV_OPERATOR))


def test_compile_prompt_includes_intent_modules_and_negative_guards():
    request = _make_request()
    compiled = compile_prompt(_compiled_request(request))

    assert "CREATE_TRACK" in compiled.prompt_text
    assert "SHIBARI_KAWAII" in compiled.prompt_text
    assert "concrete-room momentum" in compiled.prompt_text
    assert "No named artist imitation" in compiled.negative_prompt
    assert compiled.engine_hints["stems_required"] is True


def test_compile_prompt_default_stem_plan_contains_all_required_lanes():
    compiled = compile_prompt(_compiled_request(_make_request()))

    planned_lanes = {lane.lane for lane in compiled.stem_plan.lanes}
    assert planned_lanes == set(StemLaneType)
    assert len(compiled.stem_plan.lanes) == 12
    assert all(not lane.locked for lane in compiled.stem_plan.lanes)
    assert compiled.stem_plan.target_lane is None


def test_compile_prompt_carries_tempo_druck_and_effect_devices():
    base = _make_request()
    request = base.model_copy(
        update={
            "tempo": TempoControls(bpm=142, feel=TempoFeel.HALF_TIME_PRESSURE, swing=0.08),
            "druck": DruckControls(preset=DruckPreset.SOUNDSYSTEM, sub_pressure=4),
            "requested_effects": [
                EffectDeviceType.DUB_DELAY,
                EffectDeviceType.SPRING_REVERB,
            ],
        }
    )

    compiled = compile_prompt(_compiled_request(request))

    assert compiled.tempo.bpm == 142
    assert compiled.tempo.feel is TempoFeel.HALF_TIME_PRESSURE
    assert compiled.tempo.swing == pytest.approx(0.08)
    assert compiled.druck.preset is DruckPreset.SOUNDSYSTEM
    assert compiled.druck.sub_pressure == 4
    assert EffectDeviceType.DUB_DELAY in compiled.requested_effects
    assert EffectDeviceType.SPRING_REVERB in compiled.requested_effects

    vocals_rack = next(
        rack for rack in compiled.effect_racks if rack.lane is StemLaneType.VOCALS_MAIN
    )
    rack_devices = [device.device for device in vocals_rack.devices]
    assert EffectDeviceType.DUB_DELAY in rack_devices
    assert EffectDeviceType.SPRING_REVERB in rack_devices

    assert "Target BPM 142" in compiled.prompt_text
    assert "soundsystem" in compiled.prompt_text.lower()
    assert compiled.engine_hints["bpm"] == 142
    assert compiled.engine_hints["druck_preset"] == "soundsystem"


def test_locked_lanes_are_accepted_in_request_schema_and_flow_through():
    request = GenerationRequest(
        project_id="snuffraga-warehouse-test",
        intent=Intent.STEM_REMIX,
        engine=Engine.MOCK,
        prompt_modules=PromptModules(
            energy=Energy.WAREHOUSE,
            bass_pressure=BassPressure.DEEP,
            vocals=Vocals.WHISPER,
            atmosphere=Atmosphere.DUB_SMOKE,
            structure=Structure.STEM_HEAVY,
        ),
        locked_lanes=[StemLaneType.KICK, StemLaneType.BASS],
        target_lane=StemLaneType.PERCUSSION,
    )

    assert request.locked_lanes == [StemLaneType.KICK, StemLaneType.BASS]
    assert request.target_lane is StemLaneType.PERCUSSION

    compiled = compile_prompt(_compiled_request(request))
    lane_locked = {lane.lane: lane.locked for lane in compiled.stem_plan.lanes}
    assert lane_locked[StemLaneType.KICK] is True
    assert lane_locked[StemLaneType.BASS] is True
    assert lane_locked[StemLaneType.VOCALS_MAIN] is False
    assert compiled.stem_plan.target_lane is StemLaneType.PERCUSSION
    assert "Locked lanes:" in compiled.prompt_text


def test_create_generation_runs_mock_provider_to_export_ready(isolated_repository):
    job = _make_generation()

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


def test_mock_generation_returns_all_required_stem_paths():
    job = _make_generation()

    lane_set = {stem.lane for stem in job.artifacts.stem_lanes}
    assert lane_set == set(StemLaneType)
    assert len(job.artifacts.stems) == 12
    assert job.artifacts.soundgraph_manifest_json is not None
    for stem in job.artifacts.stem_lanes:
        assert stem.path.endswith(f"/stems/{stem.lane.value}.wav")
        assert stem.sample_rate == 48000
        assert stem.bit_depth == 24


def test_voice_likeness_blocks_generation_at_preflight(isolated_repository):
    job = asyncio.run(
        inference_main.create_generation(_make_request(allow_voice_likeness=True), DEV_OPERATOR)
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


def test_capabilities_exposes_lanes_modes_profiles_and_mock_provider():
    response = asyncio.run(inference_main.capabilities())

    assert any(p.name == "mock" and p.available for p in response.providers)
    assert set(response.stem_lanes) == set(StemLaneType)
    assert MasteringMode.CLUB_PRESSURE in response.mastering_modes
    assert MasteringMode.REFERENCE_MATCH in response.mastering_modes
    assert ExportProfile.HD_MASTER_WAV_24_96 in response.export_profiles
    assert ExportProfile.PREMASTER_WAV_32_FLOAT in response.export_profiles
    assert EffectDeviceType.DUB_DELAY in response.effect_devices


def test_master_bus_creates_export_ready_job_for_all_profiles(isolated_master_repository):
    generation = _make_generation()
    request = MasterBusRequest(
        generation_id=generation.id,
        mode=MasteringMode.CLUB_PRESSURE,
        profiles=[
            ExportProfile.STREAMING_READY_WAV_24_441,
            ExportProfile.CLUB_MASTER_WAV_24_48,
            ExportProfile.HD_MASTER_WAV_24_96,
            ExportProfile.PREMASTER_WAV_32_FLOAT,
            ExportProfile.STEM_PACK_WAV_24_48,
        ],
    )

    job = asyncio.run(inference_main.create_master(request, DEV_OPERATOR))

    assert job.status is MasterJobStatus.EXPORT_READY
    assert job.progress == 1.0
    assert job.manifest is not None
    assert {master.profile for master in job.manifest.masters} == set(request.profiles)

    sample_rates = {master.sample_rate for master in job.manifest.masters}
    assert {44100, 48000, 96000}.issubset(sample_rates)

    premaster = next(
        master
        for master in job.manifest.masters
        if master.profile is ExportProfile.PREMASTER_WAV_32_FLOAT
    )
    assert premaster.bit_depth == 32
    assert premaster.is_float is True

    assert isolated_master_repository.get(job.id).status is MasterJobStatus.EXPORT_READY


def test_master_bus_reference_match_without_uri_blocks():
    generation = _make_generation()
    request = MasterBusRequest(
        generation_id=generation.id,
        mode=MasteringMode.REFERENCE_MATCH,
        profiles=[ExportProfile.CLUB_MASTER_WAV_24_48],
    )

    job = asyncio.run(inference_main.create_master(request, DEV_OPERATOR))

    assert job.status is MasterJobStatus.REFERENCE_BLOCKED
    assert job.error == "reference_track_uri_required"
    assert job.manifest is None


def test_master_bus_returns_404_for_unknown_generation_id():
    request = MasterBusRequest(
        generation_id=uuid4(),
        mode=MasteringMode.CLUB_PRESSURE,
    )

    with pytest.raises(HTTPException) as info:
        asyncio.run(inference_main.create_master(request, DEV_OPERATOR))

    assert info.value.status_code == 404
    assert info.value.detail == "generation_not_found"


def test_master_lookup_with_unknown_id_returns_404():
    with pytest.raises(HTTPException) as info:
        asyncio.run(inference_main.get_master(uuid4()))

    assert info.value.status_code == 404
    assert info.value.detail == "master_not_found"
