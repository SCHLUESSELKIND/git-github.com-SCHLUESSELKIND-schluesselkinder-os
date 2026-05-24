"""Mock voice provider — S11 Voice Lab.

Produces deterministic artifact paths and emits OutputProvenance with
consent citations. No real TTS / voice-clone model runs; all audio
output is a placeholder path. The contract shape is what matters here:
every voice job must pass compliance preflight, cite its consent record,
and produce provenance before completing.
"""

from __future__ import annotations

from uuid import UUID

from app.compliance_preflight import evaluate_preflight
from app.compliance_repository import ComplianceRepository
from app.schemas import (
    CommercialStatus,
    CompliancePreflightRequest,
    OutputProvenanceCreateRequest,
    RewriteStrategy,
    VoiceJob,
    VoiceJobCreateRequest,
    VoiceJobKind,
    VoiceJobStatus,
)
from app.voice_lab_repository import VoiceLabRepository


def _intent_code_for_kind(kind: VoiceJobKind) -> str:
    return {
        VoiceJobKind.CREATE_VOICE_TAG: "character_voice",
        VoiceJobKind.CREATE_SPOKEN_VOCAL: "create_vocals",
        VoiceJobKind.CONVERT_APPROVED_VOICE: "character_voice",
    }[kind]


def _rewrite_strategy_for_kind(kind: VoiceJobKind) -> RewriteStrategy:
    return {
        VoiceJobKind.CREATE_VOICE_TAG: RewriteStrategy.INITIAL_GENERATION,
        VoiceJobKind.CREATE_SPOKEN_VOCAL: RewriteStrategy.INITIAL_GENERATION,
        VoiceJobKind.CONVERT_APPROVED_VOICE: RewriteStrategy.PROVIDER_REGEN,
    }[kind]


def run_voice_job(
    request: VoiceJobCreateRequest,
    voice_repo: VoiceLabRepository,
    compliance_repo: ComplianceRepository,
) -> VoiceJob:
    """Create a voice job, run preflight, and (if clear) produce output + provenance.

    This is a synchronous mock — a real provider would be async with
    status polling, matching the MasterBus / Generation patterns.
    """
    # Resolve consent
    consent_id: UUID | None = request.consent_id
    if consent_id is None and request.voice_tag_id is not None:
        tag = voice_repo.get_tag(request.voice_tag_id)
        if tag is not None:
            consent_id = tag.consent_id

    consent_ids = [consent_id] if consent_id is not None else []

    # Preflight
    preflight = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code=_intent_code_for_kind(request.kind),
            prompt=request.prompt,
            consent_required=True,
            consent_record_ids=consent_ids,
        ),
        consent_records=compliance_repo.list_consent_records(),
    )

    job = voice_repo.create_job(request)

    if not preflight.ok:
        return voice_repo.set_job_status(
            job.job_id,
            VoiceJobStatus.PREFLIGHT_BLOCKED,
            error="; ".join(preflight.blocking_reasons),
        )

    # "Processing" — mock provider immediately completes.
    job = voice_repo.set_job_status(job.job_id, VoiceJobStatus.PROCESSING)

    # Deterministic mock artifact path
    artifact_path = f"artifacts/voice-lab/{job.kind.value}/{job.job_id}.wav"

    # Emit provenance
    provenance = compliance_repo.create_provenance(
        OutputProvenanceCreateRequest(
            artifact_id=job.job_id,
            artifact_kind=f"voice_{job.kind.value}",
            rewrite_strategy=_rewrite_strategy_for_kind(job.kind),
            consent_records=consent_ids,
            consent_required=True,
            commercial_status=CommercialStatus.RESEARCH_ONLY,
        )
    )

    return voice_repo.set_job_status(
        job.job_id,
        VoiceJobStatus.COMPLETE,
        output_artifact_path=artifact_path,
        provenance_id=provenance.provenance_id,
    )
