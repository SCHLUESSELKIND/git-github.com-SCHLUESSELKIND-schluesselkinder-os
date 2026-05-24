"""Compliance preflight + release-eligibility evaluators.

Pure functions over a ComplianceRepository read interface. Live model
adapters never see a request that hasn't passed preflight; release
candidates never leave the system without a green eligibility result.

The codified preflight error strings mirror
docs/soundsystem/compliance-foundation.md §8 so callers (UI + adapters)
can match on stable codes instead of free-text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.schemas import (
    BlockedPromptCategory,
    CommercialStatus,
    CompliancePreflightRequest,
    CompliancePreflightResult,
    ConsentRecord,
    LicenseRegistryEntry,
    OutputProvenance,
    ReleaseEligibilityResult,
    SafetyReviewStatus,
)


# Conservative starter set. The list grows under the compliance-foundation
# rules; matches are case-insensitive substring checks. False positives are
# acceptable — risky intent should fail closed.
_BLOCKED_PROMPT_PATTERNS: dict[BlockedPromptCategory, tuple[str, ...]] = {
    BlockedPromptCategory.NAMED_ARTIST_IMITATION: (
        "in the style of",
        "sounds exactly like",
        "imitate ",
        "imitating ",
        "voice clone of ",
    ),
    BlockedPromptCategory.NAMED_TRACK_CLONING: (
        "remake of",
        "clone of",
        "exact cover of",
    ),
}


def detect_blocked_prompt_categories(
    prompt: str | None,
) -> list[BlockedPromptCategory]:
    if prompt is None:
        return []
    haystack = prompt.lower()
    matched: list[BlockedPromptCategory] = []
    for category, patterns in _BLOCKED_PROMPT_PATTERNS.items():
        if any(pattern in haystack for pattern in patterns):
            matched.append(category)
    return matched


def _preflight_block_code(category: BlockedPromptCategory) -> str:
    return f"preflight_block_{category.value}"


def evaluate_preflight(
    request: CompliancePreflightRequest,
    consent_records: Iterable[ConsentRecord],
) -> CompliancePreflightResult:
    blockers: list[str] = []
    warnings: list[str] = []
    codes: list[str] = []

    consent_index = {record.consent_id: record for record in consent_records}

    blocked = detect_blocked_prompt_categories(request.prompt)
    for category in blocked:
        codes.append(_preflight_block_code(category))
        blockers.append(f"prompt_blocked:{category.value}")

    if request.consent_required:
        if not request.consent_record_ids:
            codes.append("preflight_block_voice_clone_without_consent")
            blockers.append("consent_required_but_missing")
        now = datetime.now(timezone.utc)
        for consent_id in request.consent_record_ids:
            record = consent_index.get(consent_id)
            if record is None:
                codes.append("preflight_block_voice_clone_without_consent")
                blockers.append(f"consent_record_missing:{consent_id}")
                continue
            if record.revoked_at is not None:
                codes.append("preflight_block_voice_clone_consent_revoked")
                blockers.append(f"consent_revoked:{record.speaker_label}")
                continue
            if record.expires_at is not None and record.expires_at < now:
                codes.append("preflight_block_voice_clone_consent_expired")
                blockers.append(f"consent_expired:{record.speaker_label}")

    if request.requires_commercial and not blockers:
        warnings.append("commercial_use_requires_license_bundle_at_release")

    return CompliancePreflightResult(
        ok=len(blockers) == 0,
        blocking_reasons=blockers,
        warning_reasons=warnings,
        preflight_codes=codes,
    )


def evaluate_release_eligibility(
    provenance: OutputProvenance,
    licenses: Iterable[LicenseRegistryEntry],
    consent_records: Iterable[ConsentRecord],
) -> ReleaseEligibilityResult:
    blockers: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []

    if provenance.commercial_status is not CommercialStatus.APPROVED_RELEASE:
        blockers.append(f"commercial_status:{provenance.commercial_status.value}")
        actions.append("promote provenance.commercial_status to approved_release")

    if provenance.safety_review_status is not SafetyReviewStatus.APPROVED:
        blockers.append(f"safety_review_status:{provenance.safety_review_status.value}")
        actions.append("attach approved SafetyReviewStatus")

    if not provenance.locked_sections_respected:
        blockers.append("locked_sections_not_respected")
        actions.append("regenerate without violating locked sections")

    license_index = {entry.license_id: entry for entry in licenses}
    if not provenance.license_bundle:
        blockers.append("license_bundle_empty")
        actions.append("attach LicenseRegistry references for every contributing model/dataset")
    else:
        for license_id in provenance.license_bundle:
            entry = license_index.get(license_id)
            if entry is None:
                blockers.append(f"license_missing:{license_id}")
                actions.append(f"register license {license_id}")
                continue
            if not entry.permits_commercial:
                blockers.append(f"license_does_not_permit_commercial:{entry.license_name}")
                actions.append(f"swap or relicense {entry.license_name} for commercial use")

    consent_index = {record.consent_id: record for record in consent_records}
    if provenance.consent_required and not provenance.consent_records:
        blockers.append("consent_required_but_missing")
        actions.append("attach a non-revoked ConsentRecord")
    now = datetime.now(timezone.utc)
    for consent_id in provenance.consent_records:
        record = consent_index.get(consent_id)
        if record is None:
            blockers.append(f"consent_record_missing:{consent_id}")
            continue
        if record.revoked_at is not None:
            blockers.append(f"consent_revoked:{record.speaker_label}")
        elif record.expires_at is not None and record.expires_at < now:
            blockers.append(f"consent_expired:{record.speaker_label}")

    return ReleaseEligibilityResult(
        artifact_id=provenance.artifact_id,
        provenance_id=provenance.provenance_id,
        eligible=len(blockers) == 0,
        blocking_reasons=blockers,
        warning_reasons=warnings,
        required_actions=actions,
    )
