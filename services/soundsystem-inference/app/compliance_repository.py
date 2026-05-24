"""Compliance repository — storage boundary for license/model/consent/
provenance/audit data.

Default implementation is in-memory. A Postgres-backed implementation is
planned for S10b once the routes and surfaces are exercised end-to-end via
the in-memory path. The Protocol below is the shared swap point so that
slice does not have to touch any route handler.

All entries are seeded once from compliance_seed.py and the seed is
idempotent via stable UUIDs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Literal, Protocol
from uuid import UUID, uuid4

from app.compliance_seed import default_license_seed, default_model_seed
from app.schemas import (
    AuditEvent,
    AuditEventCreateRequest,
    CommercialStatus,
    ComplianceRegistrySummary,
    ConsentRecord,
    ConsentRecordCreateRequest,
    LicenseRegistryCreateRequest,
    LicenseRegistryEntry,
    LicenseStatus,
    ModelRegistryEntry,
    OutputProvenance,
    OutputProvenanceCreateRequest,
    ProviderGroup,
)


ComplianceRepositoryMode = Literal["in_memory", "postgres"]


class ComplianceRepository(Protocol):
    mode: ComplianceRepositoryMode

    # --- model registry ---------------------------------------------------
    def list_models(self) -> list[ModelRegistryEntry]: ...

    def get_model(self, model_id: UUID) -> ModelRegistryEntry | None: ...

    def list_models_by_group(self, group: ProviderGroup) -> list[ModelRegistryEntry]: ...

    # --- license registry -------------------------------------------------
    def list_licenses(self) -> list[LicenseRegistryEntry]: ...

    def get_license(self, license_id: UUID) -> LicenseRegistryEntry | None: ...

    def create_license(self, request: LicenseRegistryCreateRequest) -> LicenseRegistryEntry: ...

    # --- consent records --------------------------------------------------
    def list_consent_records(self) -> list[ConsentRecord]: ...

    def get_consent_record(self, consent_id: UUID) -> ConsentRecord | None: ...

    def create_consent_record(self, request: ConsentRecordCreateRequest) -> ConsentRecord: ...

    def revoke_consent_record(self, consent_id: UUID) -> ConsentRecord | None: ...

    # --- provenance -------------------------------------------------------
    def list_provenance(self) -> list[OutputProvenance]: ...

    def get_provenance(self, provenance_id: UUID) -> OutputProvenance | None: ...

    def list_provenance_for_artifact(self, artifact_id: UUID) -> list[OutputProvenance]: ...

    def create_provenance(self, request: OutputProvenanceCreateRequest) -> OutputProvenance: ...

    # --- audit ------------------------------------------------------------
    def list_audit_events(self) -> list[AuditEvent]: ...

    def create_audit_event(self, request: AuditEventCreateRequest) -> AuditEvent: ...

    # --- summary ----------------------------------------------------------
    def summary(self) -> ComplianceRegistrySummary: ...


class InMemoryComplianceRepository:
    mode: ComplianceRepositoryMode = "in_memory"

    def __init__(self) -> None:
        self._licenses: dict[UUID, LicenseRegistryEntry] = {}
        self._models: dict[UUID, ModelRegistryEntry] = {}
        self._consent: dict[UUID, ConsentRecord] = {}
        self._provenance: dict[UUID, OutputProvenance] = {}
        self._audit: list[AuditEvent] = []
        self._seed_default_registry()

    def _seed_default_registry(self) -> None:
        for entry in default_license_seed():
            self._licenses[entry.license_id] = entry
        for entry in default_model_seed(list(self._licenses.values())):
            self._models[entry.model_id] = entry

    # ---- model registry --------------------------------------------------

    def list_models(self) -> list[ModelRegistryEntry]:
        return sorted(
            self._models.values(),
            key=lambda m: (m.provider_group.value, m.display_name_internal),
        )

    def get_model(self, model_id: UUID) -> ModelRegistryEntry | None:
        return self._models.get(model_id)

    def list_models_by_group(self, group: ProviderGroup) -> list[ModelRegistryEntry]:
        return [m for m in self.list_models() if m.provider_group is group]

    # ---- license registry ------------------------------------------------

    def list_licenses(self) -> list[LicenseRegistryEntry]:
        return sorted(
            self._licenses.values(),
            key=lambda lic: (lic.model_or_dataset_id, lic.license_name),
        )

    def get_license(self, license_id: UUID) -> LicenseRegistryEntry | None:
        return self._licenses.get(license_id)

    def create_license(self, request: LicenseRegistryCreateRequest) -> LicenseRegistryEntry:
        entry = LicenseRegistryEntry(
            license_id=uuid4(),
            model_or_dataset_id=request.model_or_dataset_id,
            license_name=request.license_name,
            license_url=request.license_url,
            permits_commercial=request.permits_commercial,
            restrictions=list(request.restrictions),
            reviewed_by=request.reviewed_by,
            reviewed_at=datetime.now(timezone.utc) if request.reviewed_by else None,
            status=request.status,
            notes=request.notes,
            created_at=datetime.now(timezone.utc),
        )
        self._licenses[entry.license_id] = entry
        return entry

    # ---- consent records -------------------------------------------------

    def list_consent_records(self) -> list[ConsentRecord]:
        return sorted(self._consent.values(), key=lambda c: c.created_at, reverse=True)

    def get_consent_record(self, consent_id: UUID) -> ConsentRecord | None:
        return self._consent.get(consent_id)

    def create_consent_record(self, request: ConsentRecordCreateRequest) -> ConsentRecord:
        record = ConsentRecord(
            consent_id=uuid4(),
            speaker_label=request.speaker_label,
            source_type=request.source_type,
            permitted_uses=list(request.permitted_uses),
            revoked_at=None,
            expires_at=request.expires_at,
            notes=request.notes,
            created_at=datetime.now(timezone.utc),
        )
        self._consent[record.consent_id] = record
        return record

    def revoke_consent_record(self, consent_id: UUID) -> ConsentRecord | None:
        record = self._consent.get(consent_id)
        if record is None:
            return None
        revoked = record.model_copy(update={"revoked_at": datetime.now(timezone.utc)})
        self._consent[consent_id] = revoked
        return revoked

    # ---- provenance ------------------------------------------------------

    def list_provenance(self) -> list[OutputProvenance]:
        return sorted(
            self._provenance.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )

    def get_provenance(self, provenance_id: UUID) -> OutputProvenance | None:
        return self._provenance.get(provenance_id)

    def list_provenance_for_artifact(self, artifact_id: UUID) -> list[OutputProvenance]:
        return [entry for entry in self.list_provenance() if entry.artifact_id == artifact_id]

    def create_provenance(self, request: OutputProvenanceCreateRequest) -> OutputProvenance:
        entry = OutputProvenance(
            provenance_id=uuid4(),
            artifact_id=request.artifact_id,
            artifact_kind=request.artifact_kind,
            parent_provenance_id=request.parent_provenance_id,
            provider=request.provider,
            model=request.model,
            model_version=request.model_version,
            prompt=request.prompt,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            estimated_cost_usd=request.estimated_cost_usd,
            latency_ms=request.latency_ms,
            safety_notes=list(request.safety_notes),
            rewrite_strategy=request.rewrite_strategy,
            locked_sections_respected=request.locked_sections_respected,
            raw_provider_trace_id=request.raw_provider_trace_id,
            raw_operator_prompt=request.raw_operator_prompt,
            system_prompt_version=request.system_prompt_version,
            safety_transformations=list(request.safety_transformations),
            license_bundle=list(request.license_bundle),
            consent_records=list(request.consent_records),
            consent_required=request.consent_required,
            commercial_status=request.commercial_status,
            safety_review_status=request.safety_review_status,
            created_at=datetime.now(timezone.utc),
        )
        self._provenance[entry.provenance_id] = entry
        return entry

    # ---- audit -----------------------------------------------------------

    def list_audit_events(self) -> list[AuditEvent]:
        return sorted(self._audit, key=lambda e: e.created_at, reverse=True)

    def create_audit_event(self, request: AuditEventCreateRequest) -> AuditEvent:
        event = AuditEvent(
            event_id=uuid4(),
            operator_id=request.operator_id,
            action=request.action,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            payload_summary=dict(request.payload_summary),
            created_at=datetime.now(timezone.utc),
        )
        self._audit.append(event)
        return event

    # ---- summary ---------------------------------------------------------

    def summary(self) -> ComplianceRegistrySummary:
        return ComplianceRegistrySummary(
            model_registry_count=len(self._models),
            license_registry_count=len(self._licenses),
            consent_records_count=len(self._consent),
            output_provenance_count=len(self._provenance),
            audit_events_count=len(self._audit),
            repository_mode=self.mode,
        )


# Helpers consumed by the route handlers -------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def list_license_bundles_active(
    repo: ComplianceRepository,
) -> list[LicenseRegistryEntry]:
    return [
        entry
        for entry in repo.list_licenses()
        if entry.status != LicenseStatus.REJECTED and entry.status != LicenseStatus.SUPERSEDED
    ]


def build_release_eligibility_inputs(
    repo: ComplianceRepository, provenance: OutputProvenance
) -> tuple[Iterable[LicenseRegistryEntry], Iterable[ConsentRecord]]:
    return (
        [
            repo.get_license(license_id)
            for license_id in provenance.license_bundle
            if repo.get_license(license_id) is not None
        ],  # type: ignore[misc]
        [
            repo.get_consent_record(consent_id)
            for consent_id in provenance.consent_records
            if repo.get_consent_record(consent_id) is not None
        ],  # type: ignore[misc]
    )


def known_commercial_status_values() -> list[str]:
    return [status.value for status in CommercialStatus]


def build_default_compliance_repository() -> ComplianceRepository:
    """Phase 1: in-memory only.

    Postgres variant lands in S10b; the route handlers consult this single
    factory so the swap stays local.
    """
    return InMemoryComplianceRepository()
