"""Voice Lab tests (S11).

Tests the consent-gated voice job flow end-to-end:
- A consent-less voice job blocks at preflight.
- A revoked consent record immediately blocks new jobs citing it.
- A valid consent record allows the job to complete and emit provenance.
- Existing lyrics engine flows are unaffected (covered by test_lyrics.py).
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.compliance_repository import (
    InMemoryComplianceRepository,
    build_default_compliance_repository,
)
from app.schemas import (
    ConsentRecordCreateRequest,
    ConsentSourceType,
    VoiceJobCreateRequest,
    VoiceJobKind,
    VoiceJobStatus,
    VoiceTagCreateRequest,
)
from app.voice_lab_repository import (
    InMemoryVoiceLabRepository,
    build_default_voice_lab_repository,
)
from app.voice_provider import run_voice_job


@pytest.fixture(autouse=True)
def isolated_voice_lab():
    original = inference_main.voice_lab_repository
    inference_main.voice_lab_repository = build_default_voice_lab_repository()
    try:
        yield inference_main.voice_lab_repository
    finally:
        inference_main.voice_lab_repository = original


@pytest.fixture(autouse=True)
def isolated_compliance():
    original = inference_main.compliance_repository
    inference_main.compliance_repository = build_default_compliance_repository()
    try:
        yield inference_main.compliance_repository
    finally:
        inference_main.compliance_repository = original


# ----- acceptance gates (from S11 spec) ------------------------------------


def test_consent_less_voice_job_blocks_at_preflight() -> None:
    """A consent-less voice job blocks at preflight with a codified error."""
    voice_repo = InMemoryVoiceLabRepository()
    compliance_repo = InMemoryComplianceRepository()

    job = run_voice_job(
        VoiceJobCreateRequest(
            kind=VoiceJobKind.CREATE_SPOKEN_VOCAL,
            prompt="test spoken line",
        ),
        voice_repo,
        compliance_repo,
    )
    assert job.status == VoiceJobStatus.PREFLIGHT_BLOCKED
    assert job.error is not None
    assert "consent_required_but_missing" in job.error


def test_revoked_consent_blocks_new_jobs() -> None:
    """A revoked consent record immediately blocks new jobs that cite it."""
    voice_repo = InMemoryVoiceLabRepository()
    compliance_repo = InMemoryComplianceRepository()

    # Create consent, then revoke it
    consent = compliance_repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="speaker-alpha",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["spoken_vocal"],
        )
    )
    compliance_repo.revoke_consent_record(consent.consent_id)

    # Now try a voice job citing that revoked consent
    job = run_voice_job(
        VoiceJobCreateRequest(
            kind=VoiceJobKind.CREATE_SPOKEN_VOCAL,
            consent_id=consent.consent_id,
            prompt="test line",
        ),
        voice_repo,
        compliance_repo,
    )
    assert job.status == VoiceJobStatus.PREFLIGHT_BLOCKED
    assert "consent_revoked" in (job.error or "")


def test_valid_consent_allows_completion_with_provenance() -> None:
    """Valid consent allows job to complete and emit provenance."""
    voice_repo = InMemoryVoiceLabRepository()
    compliance_repo = InMemoryComplianceRepository()

    consent = compliance_repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="speaker-beta",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["spoken_vocal"],
        )
    )

    job = run_voice_job(
        VoiceJobCreateRequest(
            kind=VoiceJobKind.CREATE_SPOKEN_VOCAL,
            consent_id=consent.consent_id,
            prompt="hello world vocal",
        ),
        voice_repo,
        compliance_repo,
    )
    assert job.status == VoiceJobStatus.COMPLETE
    assert job.output_artifact_path is not None
    assert job.provenance_id is not None

    # Verify provenance was stored
    provenance = compliance_repo.get_provenance(job.provenance_id)
    assert provenance is not None
    assert consent.consent_id in provenance.consent_records
    assert provenance.consent_required is True
    assert provenance.artifact_id == job.job_id


def test_voice_tag_resolves_consent_from_tag() -> None:
    """Voice tag creation resolves consent_id from the tag."""
    voice_repo = InMemoryVoiceLabRepository()
    compliance_repo = InMemoryComplianceRepository()

    consent = compliance_repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="speaker-gamma",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["spoken_vocal", "voice_tag"],
        )
    )

    tag = voice_repo.create_tag(
        VoiceTagCreateRequest(
            label="gamma-character",
            consent_id=consent.consent_id,
        )
    )

    # Job using tag (no explicit consent_id) should still pass
    job = run_voice_job(
        VoiceJobCreateRequest(
            kind=VoiceJobKind.CREATE_VOICE_TAG,
            voice_tag_id=tag.tag_id,
            prompt="voice tag test",
        ),
        voice_repo,
        compliance_repo,
    )
    assert job.status == VoiceJobStatus.COMPLETE


def test_convert_voice_with_valid_consent() -> None:
    """CONVERT_APPROVED_VOICE succeeds with valid consent."""
    voice_repo = InMemoryVoiceLabRepository()
    compliance_repo = InMemoryComplianceRepository()

    consent = compliance_repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="speaker-delta",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["voice_clone"],
        )
    )

    job = run_voice_job(
        VoiceJobCreateRequest(
            kind=VoiceJobKind.CONVERT_APPROVED_VOICE,
            consent_id=consent.consent_id,
            prompt="convert to warehouse character",
        ),
        voice_repo,
        compliance_repo,
    )
    assert job.status == VoiceJobStatus.COMPLETE
    assert "convert_approved_voice" in (job.output_artifact_path or "")


# ----- voice lab repository CRUD -------------------------------------------


def test_voice_lab_summary() -> None:
    voice_repo = InMemoryVoiceLabRepository()
    summary = voice_repo.summary()
    assert summary.voice_tag_count == 0
    assert summary.voice_job_count == 0


def test_create_voice_tag_route() -> None:
    """Route-level tag creation validates consent exists."""
    compliance = inference_main.compliance_repository
    consent = compliance.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="route-test",
            source_type=ConsentSourceType.USER_OWNED,
        )
    )
    tag = asyncio.run(
        inference_main.create_voice_tag(
            VoiceTagCreateRequest(
                label="route-tag",
                consent_id=consent.consent_id,
            ),
            DEV_OPERATOR,
        )
    )
    assert tag.label == "route-tag"
    assert tag.consent_id == consent.consent_id


def test_create_voice_tag_rejects_missing_consent() -> None:
    """Route rejects tag creation with nonexistent consent_id."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            inference_main.create_voice_tag(
                VoiceTagCreateRequest(
                    label="bad-tag",
                    consent_id=uuid4(),
                ),
                DEV_OPERATOR,
            )
        )
    assert exc_info.value.status_code == 404


def test_create_voice_tag_rejects_revoked_consent() -> None:
    """Route rejects tag creation with revoked consent."""
    from fastapi import HTTPException

    compliance = inference_main.compliance_repository
    consent = compliance.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="revoked-speaker",
            source_type=ConsentSourceType.USER_OWNED,
        )
    )
    compliance.revoke_consent_record(consent.consent_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            inference_main.create_voice_tag(
                VoiceTagCreateRequest(
                    label="should-fail",
                    consent_id=consent.consent_id,
                ),
                DEV_OPERATOR,
            )
        )
    assert exc_info.value.status_code == 409


def test_capabilities_reports_voice_lab_available() -> None:
    response = asyncio.run(inference_main.capabilities())
    assert response.voice_lab_available is True
