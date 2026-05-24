"""Campaign Automation Rule Templates — S60.

Definition-only template library. Operators can instantiate templates
onto a campaign to create a CampaignAutomationRule record.

No automation execution. No scheduler. No background workers. No webhooks.
No external API calls. No provider mutations.

Template IDs are deterministic (UUID5 over a fixed namespace + slug) so
they remain stable across restarts even though the catalogue is built
from in-process data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from app.schemas import (
    CampaignAutomationAction,
    CampaignAutomationRule,
    CampaignAutomationRuleStatus,
    CampaignAutomationRuleTemplate,
    CampaignAutomationTemplateCategory,
    CampaignAutomationTemplateInstantiationRequest,
    CampaignAutomationTemplateSummary,
    CampaignAutomationTrigger,
)


# ---------- Stable template IDs ----------

# Use a fixed URL-namespace so template_id stays the same across restarts.
_TEMPLATE_NAMESPACE = uuid5(
    NAMESPACE_URL, "https://schluesselkinder.local/campaign-automation/templates"
)


def _stable_template_id(slug: str) -> UUID:
    """Return a deterministic UUID5 for a given template slug."""
    return uuid5(_TEMPLATE_NAMESPACE, slug)


# ---------- Default template definitions ----------


def build_default_automation_templates() -> list[CampaignAutomationRuleTemplate]:
    """Return the curated catalogue of automation rule templates.

    Pure function. No side effects. No mutations. No external calls.
    """
    return [
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("release-ready-mark-campaign-ready"),
            slug="release-ready-mark-campaign-ready",
            name="Mark campaign ready when release is ready",
            description=(
                "When the release pack is ready, transition the campaign "
                "from PLANNING to READY. Dry-run preview only."
            ),
            category=CampaignAutomationTemplateCategory.RELEASE_OPS,
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        ),
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("campaign-ready-mark-active"),
            slug="campaign-ready-mark-active",
            name="Activate campaign once it is READY",
            description=(
                "When a campaign is in READY state, propose moving it to "
                "ACTIVE. No external posting. No provider calls."
            ),
            category=CampaignAutomationTemplateCategory.RELEASE_OPS,
            trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE,
        ),
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("merch-locked-add-warning"),
            slug="merch-locked-add-warning",
            name="Warn when merch capsule locks",
            description=(
                "Add a campaign warning when a merch capsule has been locked "
                "so the operator double-checks downstream channels."
            ),
            category=CampaignAutomationTemplateCategory.MERCH_OPS,
            trigger=CampaignAutomationTrigger.MERCH_CAPSULE_LOCKED,
            action=CampaignAutomationAction.ADD_WARNING,
            default_action_payload={
                "warning_message": "Merch capsule locked — verify capsule snapshot."
            },
        ),
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("vinyl-ready-create-handoff-task"),
            slug="vinyl-ready-create-handoff-task",
            name="Create vinyl manual-handoff task",
            description=(
                "When a vinyl release is ready, create a handoff task on the "
                "campaign. No order placement, no manufacturer API."
            ),
            category=CampaignAutomationTemplateCategory.VINYL_OPS,
            trigger=CampaignAutomationTrigger.VINYL_READY,
            action=CampaignAutomationAction.CREATE_TASK,
            default_action_payload={"task_title": "Vinyl manual handoff to selected provider"},
        ),
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("intelligence-heat-notify-operator"),
            slug="intelligence-heat-notify-operator",
            name="Notify operator on intelligence heat threshold",
            description=(
                "Notify the operator when intelligence heat exceeds a "
                "configurable threshold. Notification is recorded; no email "
                "or external delivery."
            ),
            category=CampaignAutomationTemplateCategory.INTELLIGENCE_OPS,
            trigger=CampaignAutomationTrigger.INTELLIGENCE_HEAT_ABOVE_THRESHOLD,
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
            default_conditions={"threshold": 75},
            default_action_payload={
                "message": "Intelligence heat above threshold — review trends."
            },
            warnings=[
                "Intelligence triggers do not match by default — requires "
                "intelligence-context wiring in a future slice."
            ],
        ),
        CampaignAutomationRuleTemplate(
            template_id=_stable_template_id("snapshot-delta-notify-operator"),
            slug="snapshot-delta-notify-operator",
            name="Notify operator on snapshot heat delta",
            description=(
                "Notify the operator when the heat delta between two "
                "intelligence snapshots exceeds the configured threshold."
            ),
            category=CampaignAutomationTemplateCategory.INTELLIGENCE_OPS,
            trigger=(CampaignAutomationTrigger.SNAPSHOT_HEAT_DELTA_ABOVE_THRESHOLD),
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
            default_conditions={"threshold": 10},
            default_action_payload={"message": "Snapshot heat delta above threshold — review."},
            warnings=[
                "Snapshot delta triggers do not match by default — requires "
                "snapshot-context wiring in a future slice."
            ],
        ),
    ]


# ---------- Lookup ----------


def get_template_by_slug(
    slug: str,
    *,
    templates: list[CampaignAutomationRuleTemplate] | None = None,
) -> CampaignAutomationRuleTemplate | None:
    """Return the template with the given slug, or None.

    Pure function. No side effects.
    """
    catalogue = templates if templates is not None else build_default_automation_templates()
    for tpl in catalogue:
        if tpl.slug == slug:
            return tpl
    return None


# ---------- Instantiation ----------


def instantiate_template(
    template: CampaignAutomationRuleTemplate,
    request: CampaignAutomationTemplateInstantiationRequest,
    operator_id: str | None,
) -> CampaignAutomationRule:
    """Build a CampaignAutomationRule from a template + operator request.

    Pure function. No side effects. No execution. No audit records.
    No provider mutations. Caller is responsible for storing the rule.
    """
    conditions: dict[str, object] = dict(template.default_conditions)
    conditions.update(request.condition_overrides)

    action_payload: dict[str, object] = dict(template.default_action_payload)
    action_payload.update(request.action_payload_overrides)

    now = datetime.now(timezone.utc)
    return CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=request.campaign_id,
        name=request.override_name or template.name,
        status=CampaignAutomationRuleStatus.DRAFT,
        trigger=template.trigger,
        action=template.action,
        conditions=conditions,
        action_payload=action_payload,
        warnings=list(template.warnings),
        created_by=operator_id,
        created_at=now,
        updated_at=now,
    )


# ---------- Summary helper ----------


def summarize_templates(
    templates: list[CampaignAutomationRuleTemplate],
) -> CampaignAutomationTemplateSummary:
    """Build a deterministic summary of the catalogue. Pure function."""
    by_category: dict[str, int] = {}
    enabled = 0
    for tpl in templates:
        by_category[tpl.category.value] = by_category.get(tpl.category.value, 0) + 1
        if tpl.enabled:
            enabled += 1
    return CampaignAutomationTemplateSummary(
        total_templates=len(templates),
        enabled_templates=enabled,
        by_category=by_category,
    )
