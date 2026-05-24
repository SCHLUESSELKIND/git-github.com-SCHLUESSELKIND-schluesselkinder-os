"""Release-to-Campaign Command Center — S61.

Pure orchestration surface that aggregates state across the existing
release, campaign, automation, merch, distribution, vinyl, and analytics
subsystems into a single read-model. Operators can bootstrap a campaign
+ recommended automation rules from this surface with a single action.

Hard rules:
- No automation execution.
- No scheduler / background workers / cron / webhooks.
- No external API calls.
- No provider mutations.
- Bootstrap may only:
    1. create a Campaign (if none exists yet)
    2. instantiate recommended templates as DRAFT rule definitions

No execution jobs are queued. No audit records are written.
No campaign mutations beyond initial creation.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.auth import Operator
from app.campaign_automation import evaluate_rules_for_campaign
from app.campaign_automation_templates import (
    build_default_automation_templates,
    get_template_by_slug,
    instantiate_template,
)
from app.campaign_builder import build_campaign_from_release
from app.schemas import (
    Campaign,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
    CampaignAutomationRuleTemplate,
    CampaignAutomationTemplateInstantiationRequest,
    CommandCenterReadinessItem,
    CommandCenterReadinessStatus,
    CommandCenterRecommendedTemplate,
    MerchCapsule,
    DistributionPack,
    ReleaseCommandCenter,
    ReleaseCommandCenterBootstrapResult,
    ReleasePack,
    ReleasePackStatus,
    VinylReleaseObject,
)


# ---------- Lightweight repo Protocols (for type-checked builder) ----------


class _ReleaseRepoLike(Protocol):
    def get(self, release_id: UUID) -> ReleasePack | None: ...


class _CampaignRepoLike(Protocol):
    def get_by_release(self, release_id: UUID) -> Campaign | None: ...
    def store(self, campaign: Campaign) -> None: ...


class _RuleRepoLike(Protocol):
    def list_by_campaign(self, campaign_id: UUID) -> list[CampaignAutomationRule]: ...
    def add_rule(self, rule: CampaignAutomationRule) -> None: ...


class _MerchRepoLike(Protocol):
    def list_all(self) -> list[MerchCapsule]: ...


class _DistributionRepoLike(Protocol):
    def get_by_release(self, release_id: UUID) -> DistributionPack | None: ...


class _VinylRepoLike(Protocol):
    def get_by_release(self, release_id: UUID) -> VinylReleaseObject | None: ...


# ---------- Helpers ----------


def _merch_capsules_for_release(merch_repo: _MerchRepoLike, release_id: UUID) -> list[MerchCapsule]:
    return [c for c in merch_repo.list_all() if c.release_id == release_id]


def _has_ready_asset(release: ReleasePack, asset_type: str) -> bool:
    return any(a.asset_type == asset_type and a.ready for a in release.assets)


# ---------- Readiness inference ----------


def infer_release_readiness(
    *,
    release: ReleasePack,
    campaign: Campaign | None,
    merch_capsules: list[MerchCapsule],
    distribution_pack: DistributionPack | None,
    vinyl_release: VinylReleaseObject | None,
) -> list[CommandCenterReadinessItem]:
    """Build the readiness board. Pure function. No side effects."""
    items: list[CommandCenterReadinessItem] = []

    # --- Release / compliance ---
    if release.status == ReleasePackStatus.READY:
        release_status = CommandCenterReadinessStatus.READY
        release_warnings: list[str] = []
    elif release.compliance_passed:
        release_status = CommandCenterReadinessStatus.WARNING
        release_warnings = ["Compliance passed but release pack not marked READY."]
    else:
        release_status = CommandCenterReadinessStatus.BLOCKED
        failed = [c.code for c in release.compliance_checklist if not c.passed]
        release_warnings = [f"Compliance not passed: {', '.join(failed) or 'no items passed'}"]

    items.append(
        CommandCenterReadinessItem(
            code="release_pack",
            label="Release pack",
            status=release_status,
            linked_object_id=release.release_id,
            warnings=release_warnings,
        )
    )

    # --- Assets ---
    cover_ready = _has_ready_asset(release, "cover_art")
    audio_ready = _has_ready_asset(release, "audio_master")
    asset_warnings: list[str] = []
    if not cover_ready:
        asset_warnings.append("Cover art asset not ready.")
    if not audio_ready:
        asset_warnings.append("Audio master asset not ready.")
    if cover_ready and audio_ready:
        asset_status = CommandCenterReadinessStatus.READY
    elif cover_ready or audio_ready:
        asset_status = CommandCenterReadinessStatus.WARNING
    else:
        asset_status = CommandCenterReadinessStatus.BLOCKED
    items.append(
        CommandCenterReadinessItem(
            code="assets",
            label="Cover + audio master",
            status=asset_status,
            warnings=asset_warnings,
        )
    )

    # --- Campaign ---
    if campaign is None:
        items.append(
            CommandCenterReadinessItem(
                code="campaign",
                label="Campaign",
                status=CommandCenterReadinessStatus.MISSING,
                warnings=["No campaign exists for this release yet."],
            )
        )
    else:
        items.append(
            CommandCenterReadinessItem(
                code="campaign",
                label=f"Campaign ({campaign.status.value})",
                status=CommandCenterReadinessStatus.READY,
                linked_object_id=campaign.campaign_id,
            )
        )

    # --- Distribution ---
    if distribution_pack is None:
        items.append(
            CommandCenterReadinessItem(
                code="distribution",
                label="Distribution pack",
                status=CommandCenterReadinessStatus.MISSING,
                warnings=["No distribution pack linked."],
            )
        )
    else:
        items.append(
            CommandCenterReadinessItem(
                code="distribution",
                label=f"Distribution ({distribution_pack.status.value})",
                status=CommandCenterReadinessStatus.READY,
                linked_object_id=distribution_pack.distribution_id,
            )
        )

    # --- Merch ---
    if not merch_capsules:
        items.append(
            CommandCenterReadinessItem(
                code="merch",
                label="Merch capsule",
                status=CommandCenterReadinessStatus.MISSING,
                warnings=["No merch capsule linked."],
            )
        )
    else:
        # Use first capsule as reference; warn if multiple.
        cap = merch_capsules[0]
        extra: list[str] = []
        if len(merch_capsules) > 1:
            extra.append(f"{len(merch_capsules)} merch capsules linked.")
        items.append(
            CommandCenterReadinessItem(
                code="merch",
                label=f"Merch ({cap.status.value})",
                status=CommandCenterReadinessStatus.READY,
                linked_object_id=cap.capsule_id,
                warnings=extra,
            )
        )

    # --- Vinyl (optional channel — never blocking) ---
    if vinyl_release is None:
        items.append(
            CommandCenterReadinessItem(
                code="vinyl",
                label="Vinyl release",
                status=CommandCenterReadinessStatus.MISSING,
                warnings=["No vinyl release linked (optional channel)."],
            )
        )
    else:
        items.append(
            CommandCenterReadinessItem(
                code="vinyl",
                label=f"Vinyl ({vinyl_release.status.value})",
                status=CommandCenterReadinessStatus.READY,
                linked_object_id=vinyl_release.vinyl_id,
            )
        )

    return items


# ---------- Recommendation logic ----------


def _rule_matches_template(
    rule: CampaignAutomationRule, template: CampaignAutomationRuleTemplate
) -> bool:
    """Detect whether a stored rule already covers a template.

    Match key: same trigger + same action. Conditions are not required
    to be identical — operator may have tuned thresholds.
    """
    return rule.trigger == template.trigger and rule.action == template.action


def recommend_templates(
    *,
    campaign: Campaign | None,
    existing_rules: list[CampaignAutomationRule],
    vinyl_release: VinylReleaseObject | None,
) -> list[CommandCenterRecommendedTemplate]:
    """Build the recommended-template panel. Pure function. No side effects."""
    catalogue = build_default_automation_templates()
    catalogue_by_slug = {t.slug: t for t in catalogue}

    recommended_slugs: list[tuple[str, str]] = [
        (
            "release-ready-mark-campaign-ready",
            "Standard auto-ready hook on every release.",
        ),
        (
            "campaign-ready-mark-active",
            "Standard follow-up: move ready campaigns to active.",
        ),
    ]
    if vinyl_release is not None:
        recommended_slugs.append(
            (
                "vinyl-ready-create-handoff-task",
                "Vinyl object linked — handoff task recommended.",
            )
        )
    # Intelligence trigger never matches without intelligence context;
    # but recommend it so the operator opts in with full disclosure.
    recommended_slugs.append(
        (
            "intelligence-heat-notify-operator",
            "Optional: notify on intelligence heat threshold (requires intelligence context).",
        )
    )

    recommendations: list[CommandCenterRecommendedTemplate] = []
    for slug, reason in recommended_slugs:
        tpl = catalogue_by_slug.get(slug)
        if tpl is None:
            continue
        attached = any(_rule_matches_template(r, tpl) for r in existing_rules)
        recommendations.append(
            CommandCenterRecommendedTemplate(
                template_slug=tpl.slug,
                name=tpl.name,
                reason=reason,
                already_attached=attached,
                warnings=list(tpl.warnings),
            )
        )
    return recommendations


# ---------- Dry-run summary ----------


def _summarize_dry_runs(
    campaign: Campaign | None,
    existing_rules: list[CampaignAutomationRule],
) -> dict[str, int]:
    """Count WOULD_RUN / BLOCKED / NO_MATCH across the campaign's rules."""
    summary: dict[str, int] = {
        CampaignAutomationDryRunStatus.WOULD_RUN.value: 0,
        CampaignAutomationDryRunStatus.BLOCKED.value: 0,
        CampaignAutomationDryRunStatus.NO_MATCH.value: 0,
    }
    if campaign is None or not existing_rules:
        return summary
    results = evaluate_rules_for_campaign(existing_rules, campaign)
    for r in results:
        summary[r.status.value] = summary.get(r.status.value, 0) + 1
    return summary


# ---------- Builder ----------


def build_release_command_center(
    *,
    release: ReleasePack,
    campaign: Campaign | None,
    existing_rules: list[CampaignAutomationRule],
    merch_capsules: list[MerchCapsule],
    distribution_pack: DistributionPack | None,
    vinyl_release: VinylReleaseObject | None,
) -> ReleaseCommandCenter:
    """Compose a Command Center snapshot. Pure function. No side effects."""
    readiness = infer_release_readiness(
        release=release,
        campaign=campaign,
        merch_capsules=merch_capsules,
        distribution_pack=distribution_pack,
        vinyl_release=vinyl_release,
    )
    recommendations = recommend_templates(
        campaign=campaign,
        existing_rules=existing_rules,
        vinyl_release=vinyl_release,
    )
    dry_run = _summarize_dry_runs(campaign, existing_rules)

    warnings: list[str] = []
    if campaign is None:
        warnings.append("Campaign not yet bootstrapped.")
    if not merch_capsules and not distribution_pack and vinyl_release is None:
        warnings.append(
            "No downstream objects (merch / distribution / vinyl) linked — "
            "Command Center will be sparse until linked objects exist."
        )

    return ReleaseCommandCenter(
        release_id=release.release_id,
        release_title=release.title,
        campaign_id=campaign.campaign_id if campaign else None,
        campaign_status=campaign.status if campaign else None,
        readiness_items=readiness,
        recommended_templates=recommendations,
        linked_merch_capsule_ids=[c.capsule_id for c in merch_capsules],
        linked_distribution_pack_ids=(
            [distribution_pack.distribution_id] if distribution_pack else []
        ),
        linked_vinyl_ids=([vinyl_release.vinyl_id] if vinyl_release else []),
        automation_rule_count=len(existing_rules),
        dry_run_summary=dry_run,
        warnings=warnings,
    )


# ---------- Bootstrap (only mutator entry point) ----------


def bootstrap_release_campaign(
    *,
    release: ReleasePack,
    campaign: Campaign | None,
    existing_rules: list[CampaignAutomationRule],
    merch_capsules: list[MerchCapsule],
    distribution_pack: DistributionPack | None,
    vinyl_release: VinylReleaseObject | None,
    campaign_repo: _CampaignRepoLike,
    rule_repo: _RuleRepoLike,
    operator: Operator,
) -> ReleaseCommandCenterBootstrapResult:
    """Create campaign (if missing) + instantiate recommended templates.

    Bootstrap NEVER:
    - queues an execution job
    - writes an audit record
    - mutates merch / distribution / vinyl / analytics / providers
    - calls any external API
    - mutates a campaign beyond initial creation

    Bootstrap MAY:
    - create one new Campaign (only if none exists)
    - instantiate template-backed DRAFT rules that are not yet attached
    """
    bootstrap_warnings: list[str] = []
    created_campaign = False

    # 1. Ensure campaign exists.
    if campaign is None:
        campaign = build_campaign_from_release(
            release,
            operator_id=operator.operator_id,
            vinyl_release=vinyl_release,
        )
        campaign_repo.store(campaign)
        created_campaign = True

    # 2. Recompute recommendations against the post-create state.
    recs = recommend_templates(
        campaign=campaign,
        existing_rules=existing_rules,
        vinyl_release=vinyl_release,
    )

    instantiated: list[UUID] = []
    for rec in recs:
        if rec.already_attached:
            continue
        tpl = get_template_by_slug(rec.template_slug)
        if tpl is None or not tpl.enabled:
            bootstrap_warnings.append(f"Template '{rec.template_slug}' is unavailable; skipped.")
            continue
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=campaign.campaign_id),
            operator_id=operator.operator_id,
        )
        rule_repo.add_rule(rule)
        instantiated.append(rule.rule_id)

    # 3. Rebuild the command center from the post-bootstrap state.
    updated_rules = rule_repo.list_by_campaign(campaign.campaign_id)
    command_center = build_release_command_center(
        release=release,
        campaign=campaign,
        existing_rules=updated_rules,
        merch_capsules=merch_capsules,
        distribution_pack=distribution_pack,
        vinyl_release=vinyl_release,
    )

    return ReleaseCommandCenterBootstrapResult(
        command_center=command_center,
        created_campaign=created_campaign,
        instantiated_rule_ids=instantiated,
        warnings=bootstrap_warnings,
    )
