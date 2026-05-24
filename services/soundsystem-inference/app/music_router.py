"""Music Provider Router — S12.

Intent-driven mock router. Each MusicIntentKind maps to a provider group;
the router selects a mock adapter, runs compliance preflight, produces
deterministic artifact paths, and emits provenance. No real model runs.

The router consults the ComplianceRepository for preflight (blocked prompt
categories) and writes provenance for every completed job. Commercial status
is always review_needed or research_only — mock outputs never reach
approved_release.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Protocol
from uuid import UUID, uuid4

from app.compliance_preflight import evaluate_preflight
from app.compliance_repository import ComplianceRepository
from app.schemas import (
    CommercialStatus,
    CompliancePreflightRequest,
    MusicArtifactManifest,
    MusicArtifactType,
    MusicGenerationRequest,
    MusicIntentKind,
    MusicJob,
    MusicJobStatus,
    MusicProviderGroup,
    MusicRouterDecision,
    MusicRouterReadiness,
    MusicRouterSummary,
    OutputProvenanceCreateRequest,
    RewriteStrategy,
)


# ----- Intent → Provider Group mapping ------------------------------------

_INTENT_TO_GROUP: dict[MusicIntentKind, MusicProviderGroup] = {
    MusicIntentKind.CREATE_LOOP: MusicProviderGroup.MUSIC_LOOP_PROVIDER,
    MusicIntentKind.CREATE_SONG_SKETCH: MusicProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER,
    MusicIntentKind.CREATE_STEM_TRACK: MusicProviderGroup.STEM_GENERATION_PROVIDER,
    MusicIntentKind.BUILD_RIDDIM: MusicProviderGroup.MUSIC_LOOP_PROVIDER,
    MusicIntentKind.DUB_FX_LAB: MusicProviderGroup.DUB_FX_PROVIDER,
    MusicIntentKind.MASTER_TRACK: MusicProviderGroup.MASTERING_PROVIDER,
}

_GROUP_TO_MOCK_ADAPTER: dict[MusicProviderGroup, str] = {
    MusicProviderGroup.MUSIC_LOOP_PROVIDER: "mock_loop_v1",
    MusicProviderGroup.HIGH_FIDELITY_CLIP_PROVIDER: "mock_hifi_clip_v1",
    MusicProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER: "mock_fullsong_v1",
    MusicProviderGroup.STEM_GENERATION_PROVIDER: "mock_stems_v1",
    MusicProviderGroup.DUB_FX_PROVIDER: "mock_dubfx_v1",
    MusicProviderGroup.MASTERING_PROVIDER: "mock_master_v1",
}

_INTENT_TO_ARTIFACT_TYPE: dict[MusicIntentKind, MusicArtifactType] = {
    MusicIntentKind.CREATE_LOOP: MusicArtifactType.LOOP,
    MusicIntentKind.CREATE_SONG_SKETCH: MusicArtifactType.FULL_MIX,
    MusicIntentKind.CREATE_STEM_TRACK: MusicArtifactType.STEM_PACK,
    MusicIntentKind.BUILD_RIDDIM: MusicArtifactType.LOOP,
    MusicIntentKind.DUB_FX_LAB: MusicArtifactType.DUB_FX,
    MusicIntentKind.MASTER_TRACK: MusicArtifactType.MASTER,
}


# ----- Repository ----------------------------------------------------------


MusicRouterRepositoryMode = Literal["in_memory"]


class MusicRouterRepository(Protocol):
    mode: MusicRouterRepositoryMode

    def list_jobs(self) -> list[MusicJob]: ...
    def get_job(self, job_id: UUID) -> MusicJob | None: ...
    def create_job(self, job: MusicJob) -> MusicJob: ...
    def update_job(self, job: MusicJob) -> MusicJob: ...
    def summary(self) -> MusicRouterSummary: ...


class InMemoryMusicRouterRepository:
    mode: MusicRouterRepositoryMode = "in_memory"

    def __init__(self) -> None:
        self._jobs: dict[UUID, MusicJob] = {}

    def list_jobs(self) -> list[MusicJob]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def get_job(self, job_id: UUID) -> MusicJob | None:
        return self._jobs.get(job_id)

    def create_job(self, job: MusicJob) -> MusicJob:
        self._jobs[job.job_id] = job
        return job

    def update_job(self, job: MusicJob) -> MusicJob:
        self._jobs[job.job_id] = job
        return job

    def summary(self) -> MusicRouterSummary:
        jobs = list(self._jobs.values())
        return MusicRouterSummary(
            total_jobs=len(jobs),
            jobs_completed=sum(1 for j in jobs if j.status == MusicJobStatus.COMPLETED),
            jobs_blocked=sum(1 for j in jobs if j.status == MusicJobStatus.PREFLIGHT_BLOCKED),
            jobs_failed=sum(1 for j in jobs if j.status == MusicJobStatus.FAILED),
            available_intents=[intent for intent in MusicIntentKind],
        )


def build_default_music_router_repository() -> MusicRouterRepository:
    return InMemoryMusicRouterRepository()


# ----- Router logic --------------------------------------------------------


def route_intent(intent: MusicIntentKind) -> MusicRouterDecision:
    """Pure routing decision — maps intent to provider group + mock adapter."""
    group = _INTENT_TO_GROUP[intent]
    adapter = _GROUP_TO_MOCK_ADAPTER[group]
    return MusicRouterDecision(
        intent=intent,
        provider_group=group,
        selected_adapter_key=adapter,
        readiness_state=MusicRouterReadiness.MOCK_ONLY,
        reason=f"auto-routed to {group.value} (mock adapter: {adapter})",
    )


def run_music_job(
    request: MusicGenerationRequest,
    music_repo: MusicRouterRepository,
    compliance_repo: ComplianceRepository,
) -> MusicJob:
    """Execute a music generation job through the mock router.

    Flow: create job → route → preflight → mock artifacts → provenance → complete.
    """
    job_id = uuid4()
    now = datetime.now(timezone.utc)

    # Route
    decision = route_intent(request.intent)

    # Create initial job
    job = MusicJob(
        job_id=job_id,
        intent=request.intent,
        title=request.title,
        prompt=request.prompt,
        status=MusicJobStatus.QUEUED,
        router_decision=decision,
        commercial_target=request.commercial_target,
        operator_id=request.operator_id,
        created_at=now,
        updated_at=now,
    )
    music_repo.create_job(job)

    # Compliance preflight
    preflight = evaluate_preflight(
        CompliancePreflightRequest(
            intent_code=request.intent.value,
            prompt=request.prompt,
            consent_required=False,
            requires_commercial=(request.commercial_target is CommercialStatus.APPROVED_RELEASE),
        ),
        consent_records=compliance_repo.list_consent_records(),
    )

    if not preflight.ok:
        decision_blocked = decision.model_copy(
            update={
                "compliance_preflight_ok": False,
                "compliance_preflight_codes": preflight.preflight_codes,
            }
        )
        blocked_job = job.model_copy(
            update={
                "status": MusicJobStatus.PREFLIGHT_BLOCKED,
                "router_decision": decision_blocked,
                "error": "; ".join(preflight.blocking_reasons),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return music_repo.update_job(blocked_job)

    # Mock processing — produce deterministic artifacts
    artifact_type = _INTENT_TO_ARTIFACT_TYPE[request.intent]
    artifacts = [
        MusicArtifactManifest(
            artifact_type=artifact_type,
            path=f"artifacts/music-router/{request.intent.value}/{job_id}.wav",
            duration_seconds=request.duration_seconds or 30.0,
            format="wav",
        ),
        MusicArtifactManifest(
            artifact_type=MusicArtifactType.PROMPT_MANIFEST,
            path=f"artifacts/music-router/{request.intent.value}/{job_id}.prompt.json",
        ),
    ]

    # Emit provenance
    provenance = compliance_repo.create_provenance(
        OutputProvenanceCreateRequest(
            artifact_id=job_id,
            artifact_kind=f"music_{request.intent.value}",
            rewrite_strategy=RewriteStrategy.INITIAL_GENERATION,
            commercial_status=CommercialStatus.REVIEW_NEEDED,
        )
    )

    # Complete
    completed_decision = decision.model_copy(update={"provenance_id": provenance.provenance_id})
    completed_job = job.model_copy(
        update={
            "status": MusicJobStatus.COMPLETED,
            "router_decision": completed_decision,
            "artifacts": artifacts,
            "provenance_id": provenance.provenance_id,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    return music_repo.update_job(completed_job)
