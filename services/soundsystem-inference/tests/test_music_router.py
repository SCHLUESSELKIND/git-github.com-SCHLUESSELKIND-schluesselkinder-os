"""Music Provider Router tests (S12).

Verifies:
- Each intent maps to the correct provider group.
- Mock jobs complete and create artifact manifests.
- Completed jobs create output provenance.
- commercial_status is never approved_release by default.
- Capabilities expose music_router_available.
- Job listing returns created jobs.
- Artifact route returns deterministic paths.
- No external service required.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.compliance_repository import build_default_compliance_repository
from app.music_router import (
    InMemoryMusicRouterRepository,
    build_default_music_router_repository,
    route_intent,
    run_music_job,
)
from app.schemas import (
    CommercialStatus,
    MusicGenerationRequest,
    MusicIntentKind,
    MusicJobStatus,
    MusicProviderGroup,
    MusicRouterReadiness,
)


@pytest.fixture(autouse=True)
def isolated_music_router():
    original = inference_main.music_router_repository
    inference_main.music_router_repository = build_default_music_router_repository()
    try:
        yield inference_main.music_router_repository
    finally:
        inference_main.music_router_repository = original


@pytest.fixture(autouse=True)
def isolated_compliance():
    original = inference_main.compliance_repository
    inference_main.compliance_repository = build_default_compliance_repository()
    try:
        yield inference_main.compliance_repository
    finally:
        inference_main.compliance_repository = original


# ----- intent routing ------------------------------------------------------


def test_create_loop_routes_to_music_loop_provider() -> None:
    decision = route_intent(MusicIntentKind.CREATE_LOOP)
    assert decision.provider_group == MusicProviderGroup.MUSIC_LOOP_PROVIDER
    assert decision.readiness_state == MusicRouterReadiness.MOCK_ONLY


def test_create_song_sketch_routes_to_full_song_provider() -> None:
    decision = route_intent(MusicIntentKind.CREATE_SONG_SKETCH)
    assert decision.provider_group == MusicProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER


def test_create_stem_track_routes_to_stem_provider() -> None:
    decision = route_intent(MusicIntentKind.CREATE_STEM_TRACK)
    assert decision.provider_group == MusicProviderGroup.STEM_GENERATION_PROVIDER


def test_build_riddim_routes_to_loop_provider() -> None:
    decision = route_intent(MusicIntentKind.BUILD_RIDDIM)
    assert decision.provider_group == MusicProviderGroup.MUSIC_LOOP_PROVIDER


def test_dub_fx_lab_routes_to_dub_fx_provider() -> None:
    decision = route_intent(MusicIntentKind.DUB_FX_LAB)
    assert decision.provider_group == MusicProviderGroup.DUB_FX_PROVIDER


def test_master_track_routes_to_mastering_provider() -> None:
    decision = route_intent(MusicIntentKind.MASTER_TRACK)
    assert decision.provider_group == MusicProviderGroup.MASTERING_PROVIDER


# ----- mock job completion -------------------------------------------------


def _make_request(
    intent: MusicIntentKind = MusicIntentKind.CREATE_LOOP,
    **kwargs,
) -> MusicGenerationRequest:
    defaults = dict(
        intent=intent,
        title="test job",
        prompt="warehouse banger, crushing bass",
    )
    defaults.update(kwargs)
    return MusicGenerationRequest(**defaults)


def test_mock_job_completes_with_artifacts() -> None:
    music_repo = InMemoryMusicRouterRepository()
    compliance_repo = build_default_compliance_repository()

    job = run_music_job(
        _make_request(MusicIntentKind.CREATE_LOOP),
        music_repo,
        compliance_repo,
    )
    assert job.status == MusicJobStatus.COMPLETED
    assert len(job.artifacts) == 2
    assert job.artifacts[0].path.endswith(".wav")
    assert job.artifacts[1].path.endswith(".prompt.json")


def test_mock_job_creates_provenance() -> None:
    music_repo = InMemoryMusicRouterRepository()
    compliance_repo = build_default_compliance_repository()

    job = run_music_job(
        _make_request(MusicIntentKind.CREATE_SONG_SKETCH),
        music_repo,
        compliance_repo,
    )
    assert job.provenance_id is not None
    provenance = compliance_repo.get_provenance(job.provenance_id)
    assert provenance is not None
    assert provenance.artifact_id == job.job_id
    assert provenance.commercial_status is CommercialStatus.REVIEW_NEEDED


def test_commercial_status_never_approved_release_by_default() -> None:
    music_repo = InMemoryMusicRouterRepository()
    compliance_repo = build_default_compliance_repository()

    for intent in MusicIntentKind:
        job = run_music_job(
            _make_request(intent),
            music_repo,
            compliance_repo,
        )
        if job.provenance_id:
            prov = compliance_repo.get_provenance(job.provenance_id)
            assert prov is not None
            assert prov.commercial_status is not CommercialStatus.APPROVED_RELEASE


def test_preflight_blocks_named_artist_in_music_prompt() -> None:
    music_repo = InMemoryMusicRouterRepository()
    compliance_repo = build_default_compliance_repository()

    job = run_music_job(
        _make_request(
            MusicIntentKind.CREATE_LOOP,
            prompt="in the style of Aphex Twin",
        ),
        music_repo,
        compliance_repo,
    )
    assert job.status == MusicJobStatus.PREFLIGHT_BLOCKED
    assert job.error is not None
    assert "named_artist_imitation" in job.error


def test_artifacts_have_deterministic_paths() -> None:
    music_repo = InMemoryMusicRouterRepository()
    compliance_repo = build_default_compliance_repository()

    job = run_music_job(
        _make_request(MusicIntentKind.DUB_FX_LAB),
        music_repo,
        compliance_repo,
    )
    assert f"dub_fx_lab/{job.job_id}.wav" in job.artifacts[0].path


# ----- routes / capabilities -----------------------------------------------


def test_capabilities_exposes_music_router() -> None:
    response = asyncio.run(inference_main.capabilities())
    assert response.music_router_available is True
    assert response.music_router_mode == "mock"
    assert "create_loop" in response.available_music_intents


def test_job_listing_returns_created_jobs() -> None:
    request = _make_request(MusicIntentKind.BUILD_RIDDIM)
    job = asyncio.run(inference_main.create_music_job(request, DEV_OPERATOR))
    jobs = asyncio.run(inference_main.list_music_jobs())
    assert any(j.job_id == job.job_id for j in jobs)


def test_get_job_returns_404_for_missing() -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(inference_main.get_music_job(uuid4()))
    assert exc_info.value.status_code == 404


def test_artifact_route_returns_artifacts() -> None:
    request = _make_request(MusicIntentKind.MASTER_TRACK)
    job = asyncio.run(inference_main.create_music_job(request, DEV_OPERATOR))
    artifacts = asyncio.run(inference_main.get_music_job_artifacts(job.job_id))
    assert len(artifacts) == 2
    assert "master_track" in artifacts[0].path
