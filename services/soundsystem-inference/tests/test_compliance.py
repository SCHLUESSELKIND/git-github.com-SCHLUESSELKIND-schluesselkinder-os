"""Compliance Foundation tests (S10).

All tests run against the in-memory ComplianceRepository — no Postgres
required. The Postgres-backed variant ships in S10b and will share these
tests by swapping the factory.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app import main as inference_main
from app.compliance_preflight import (
    evaluate_preflight,
    evaluate_release_eligibility,
)
from app.compliance_repository import (
    InMemoryComplianceRepository,
    build_default_compliance_repository,
)
from app.schemas import (
    AuditEventCreateRequest,
    BlockedPromptCategory,
    CommercialStatus,
    CompliancePreflightRequest,
    ConsentRecord,
    ConsentRecordCreateRequest,
    ConsentSourceType,
    LicenseRegistryCreateRequest,
    LicenseRegistryEntry,
    LicenseStatus,
    OutputProvenance,
    OutputProvenanceCreateRequest,
    ProviderGroup,
    RewriteStrategy,
    SafetyReviewStatus,
)


@pytest.fixture(autouse=True)
def isolated_compliance_repository():
    original = inference_main.compliance_repository
    inference_main.compliance_repository = build_default_compliance_repository()
    try:
        yield inference_main.compliance_repository
    finally:
        inference_main.compliance_repository = original


# ----- seed ----------------------------------------------------------------


def test_default_seed_is_populated() -> None:
    repo = InMemoryComplianceRepository()
    models = repo.list_models()
    licenses = repo.list_licenses()
    assert len(models) > 0, "model registry must be seeded"
    assert len(licenses) > 0, "license registry must be seeded"
    # Every seeded provider_group exists at least once.
    groups = {entry.provider_group for entry in models}
    assert ProviderGroup.MUSIC_LOOP_PROVIDER in groups
    assert ProviderGroup.VOICE_TTS_PROVIDER in groups


def test_default_seed_is_idempotent() -> None:
    repo_a = InMemoryComplianceRepository()
    repo_b = InMemoryComplianceRepository()
    ids_a = sorted(str(m.model_id) for m in repo_a.list_models())
    ids_b = sorted(str(m.model_id) for m in repo_b.list_models())
    assert ids_a == ids_b, "stable uuid5 seed must produce identical ids"


def test_no_active_seed_marked_approved_release() -> None:
    repo = InMemoryComplianceRepository()
    for model in repo.list_models():
        assert model.commercial_status is not CommercialStatus.APPROVED_RELEASE, (
            f"{model.adapter_key} seeded with approved_release — no live model is approved"
        )


# ----- license / consent / provenance / audit CRUD -------------------------


def test_create_and_list_license() -> None:
    repo = InMemoryComplianceRepository()
    before = len(repo.list_licenses())
    entry = repo.create_license(
        LicenseRegistryCreateRequest(
            model_or_dataset_id="experimental/test",
            license_name="Test License 1.0",
            permits_commercial=False,
            restrictions=["non-commercial"],
            reviewed_by="qa",
            status=LicenseStatus.NEEDS_REVIEW,
        )
    )
    assert isinstance(entry, LicenseRegistryEntry)
    assert entry.reviewed_at is not None, "reviewed_at must be stamped when reviewed_by present"
    assert len(repo.list_licenses()) == before + 1


def test_create_and_list_consent_record() -> None:
    repo = InMemoryComplianceRepository()
    record = repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="operator-alpha",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["spoken_vocal"],
        )
    )
    assert isinstance(record, ConsentRecord)
    assert record.revoked_at is None
    assert any(c.consent_id == record.consent_id for c in repo.list_consent_records())


def test_create_and_list_provenance_for_artifact() -> None:
    repo = InMemoryComplianceRepository()
    artifact_id = uuid4()
    entry = repo.create_provenance(
        OutputProvenanceCreateRequest(
            artifact_id=artifact_id,
            artifact_kind="lyrics_version",
            rewrite_strategy=RewriteStrategy.PROMPT_EDIT,
        )
    )
    assert entry.commercial_status is CommercialStatus.RESEARCH_ONLY
    assert entry.safety_review_status is SafetyReviewStatus.PENDING
    matches = repo.list_provenance_for_artifact(artifact_id)
    assert len(matches) == 1
    assert matches[0].provenance_id == entry.provenance_id


def test_create_and_list_audit_event() -> None:
    repo = InMemoryComplianceRepository()
    artifact_id = uuid4()
    event = repo.create_audit_event(
        AuditEventCreateRequest(
            operator_id="tom",
            action="lyrics.create",
            entity_type="lyrics_version",
            entity_id=artifact_id,
            payload_summary={"version_number": 1},
        )
    )
    assert event.created_at.tzinfo is not None
    events = repo.list_audit_events()
    assert any(e.event_id == event.event_id for e in events)


def test_summary_reflects_counts() -> None:
    repo = InMemoryComplianceRepository()
    base = repo.summary()
    repo.create_audit_event(
        AuditEventCreateRequest(
            operator_id="tom",
            action="test.action",
            entity_type="test_entity",
        )
    )
    after = repo.summary()
    assert after.audit_events_count == base.audit_events_count + 1
    assert after.repository_mode == "in_memory"


# ----- preflight -----------------------------------------------------------


def test_preflight_blocks_named_artist_imitation() -> None:
    result = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code="create_track",
            prompt="warehouse banger in the style of Aphex Twin",
        ),
        consent_records=[],
    )
    assert result.ok is False
    assert any(
        code.endswith(BlockedPromptCategory.NAMED_ARTIST_IMITATION.value)
        for code in result.preflight_codes
    )


def test_preflight_blocks_voice_clone_without_consent() -> None:
    result = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code="convert_voice",
            consent_required=True,
            consent_record_ids=[],
        ),
        consent_records=[],
    )
    assert result.ok is False
    assert "preflight_block_voice_clone_without_consent" in result.preflight_codes


def test_preflight_passes_clean_prompt() -> None:
    result = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code="create_track",
            prompt="warehouse banger, crushing bass, haunting vocals",
        ),
        consent_records=[],
    )
    assert result.ok is True
    assert result.blocking_reasons == []


def test_preflight_blocks_consent_revoked() -> None:
    repo = InMemoryComplianceRepository()
    consent = repo.create_consent_record(
        ConsentRecordCreateRequest(
            speaker_label="speaker-zero",
            source_type=ConsentSourceType.USER_OWNED,
            permitted_uses=["spoken_vocal"],
        )
    )
    # Mark revoked
    revoked = consent.model_copy(update={"revoked_at": datetime.now(timezone.utc)})
    result = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code="convert_voice",
            consent_required=True,
            consent_record_ids=[consent.consent_id],
        ),
        consent_records=[revoked],
    )
    assert result.ok is False
    assert "preflight_block_voice_clone_consent_revoked" in result.preflight_codes


# ----- release eligibility -------------------------------------------------


def _make_provenance(**overrides):
    base = dict(
        provenance_id=uuid4(),
        artifact_id=uuid4(),
        artifact_kind="lyrics_version",
        rewrite_strategy=RewriteStrategy.PROMPT_EDIT,
        locked_sections_respected=True,
        commercial_status=CommercialStatus.APPROVED_RELEASE,
        safety_review_status=SafetyReviewStatus.APPROVED,
        license_bundle=[],
        consent_records=[],
        consent_required=False,
    )
    base.update(overrides)
    return OutputProvenance(**base)


def test_release_eligibility_blocks_when_license_bundle_empty() -> None:
    provenance = _make_provenance()
    result = evaluate_release_eligibility(provenance, licenses=[], consent_records=[])
    assert result.eligible is False
    assert "license_bundle_empty" in result.blocking_reasons


def test_release_eligibility_blocks_when_commercial_status_not_approved() -> None:
    license_id = uuid4()
    license_entry = LicenseRegistryEntry(
        license_id=license_id,
        model_or_dataset_id="x",
        license_name="x",
        permits_commercial=True,
    )
    provenance = _make_provenance(
        commercial_status=CommercialStatus.RESEARCH_ONLY,
        license_bundle=[license_id],
    )
    result = evaluate_release_eligibility(provenance, licenses=[license_entry], consent_records=[])
    assert result.eligible is False
    assert any(r.startswith("commercial_status:") for r in result.blocking_reasons)


def test_release_eligibility_blocks_when_license_does_not_permit_commercial() -> None:
    license_id = uuid4()
    license_entry = LicenseRegistryEntry(
        license_id=license_id,
        model_or_dataset_id="x",
        license_name="cc-by-nc",
        permits_commercial=False,
    )
    provenance = _make_provenance(license_bundle=[license_id])
    result = evaluate_release_eligibility(provenance, licenses=[license_entry], consent_records=[])
    assert result.eligible is False
    assert any(r.startswith("license_does_not_permit_commercial:") for r in result.blocking_reasons)


def test_release_eligibility_blocks_when_consent_expired() -> None:
    license_id = uuid4()
    license_entry = LicenseRegistryEntry(
        license_id=license_id,
        model_or_dataset_id="x",
        license_name="ok",
        permits_commercial=True,
    )
    consent_id = uuid4()
    expired_consent = ConsentRecord(
        consent_id=consent_id,
        speaker_label="speaker-z",
        source_type=ConsentSourceType.USER_OWNED,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    provenance = _make_provenance(
        license_bundle=[license_id],
        consent_records=[consent_id],
        consent_required=True,
    )
    result = evaluate_release_eligibility(
        provenance, licenses=[license_entry], consent_records=[expired_consent]
    )
    assert result.eligible is False
    assert any(r.startswith("consent_expired:") for r in result.blocking_reasons)


def test_release_eligibility_passes_only_when_all_clear() -> None:
    license_id = uuid4()
    license_entry = LicenseRegistryEntry(
        license_id=license_id,
        model_or_dataset_id="x",
        license_name="permissive",
        permits_commercial=True,
    )
    provenance = _make_provenance(license_bundle=[license_id])
    result = evaluate_release_eligibility(provenance, licenses=[license_entry], consent_records=[])
    assert result.eligible is True
    assert result.blocking_reasons == []


# ----- capabilities --------------------------------------------------------


def test_capabilities_exposes_compliance_fields() -> None:
    response = asyncio.run(inference_main.capabilities())
    assert response.compliance_repository_mode in {"in_memory", "postgres"}
    assert response.compliance_registry_available is True
    assert response.compliance_preflight_available is True
