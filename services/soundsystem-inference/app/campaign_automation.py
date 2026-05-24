"""Campaign Automation Dry-Run Evaluator — S57.

Pure deterministic evaluator. No side effects. No mutations.
No external calls. No scheduling. No background jobs.

Answers the question: "What would happen if this rule ran?"
Does NOT execute automation.
"""

from __future__ import annotations

from app.schemas import (
    Campaign,
    CampaignAutomationAction,
    CampaignAutomationDryRunResult,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
    CampaignAutomationRuleStatus,
    CampaignAutomationTrigger,
    CampaignStatus,
)


# ---------- Context builder ----------


def build_automation_context(campaign: Campaign) -> dict[str, object]:
    """Build a read-only context dict from a Campaign for rule evaluation.

    Pure function. No side effects. No mutations.
    """
    all_tasks = campaign.tasks
    return {
        "campaign_id": str(campaign.campaign_id),
        "release_id": str(campaign.release_id),
        "campaign_status": campaign.status.value,
        "channels": [ch.value for ch in campaign.channels],
        "total_tasks": len(all_tasks),
        "completed_tasks": sum(1 for t in all_tasks if t.status.value == "completed"),
        "blocked_tasks": sum(1 for t in all_tasks if t.status.value == "blocked"),
        "has_warnings": len(campaign.warnings) > 0,
        "warning_count": len(campaign.warnings),
        "has_merch_link": len(campaign.linked_merch_capsule_ids) > 0,
        "has_distribution_link": len(campaign.linked_distribution_pack_ids) > 0,
        "has_soundcloud_link": len(campaign.linked_soundcloud_job_ids) > 0,
    }


# ---------- Trigger matching ----------

# Maps triggers to the campaign status they expect.
_TRIGGER_STATUS_MAP: dict[CampaignAutomationTrigger, CampaignStatus | None] = {
    CampaignAutomationTrigger.CAMPAIGN_READY: CampaignStatus.READY,
    CampaignAutomationTrigger.CAMPAIGN_ACTIVE: CampaignStatus.ACTIVE,
}


def _trigger_matches(
    trigger: CampaignAutomationTrigger,
    context: dict[str, object],
) -> bool:
    """Check whether a trigger condition matches the campaign context.

    Pure function. No side effects.
    """
    # Status-based triggers
    expected_status = _TRIGGER_STATUS_MAP.get(trigger)
    if expected_status is not None:
        return context.get("campaign_status") == expected_status.value

    # Asset / state triggers
    if trigger == CampaignAutomationTrigger.RELEASE_READY:
        return context.get("campaign_status") in (
            CampaignStatus.PLANNING.value,
            CampaignStatus.READY.value,
            CampaignStatus.ACTIVE.value,
        )

    if trigger == CampaignAutomationTrigger.DISTRIBUTION_READY:
        return bool(context.get("has_distribution_link"))

    if trigger == CampaignAutomationTrigger.MERCH_CAPSULE_LOCKED:
        return bool(context.get("has_merch_link"))

    if trigger == CampaignAutomationTrigger.VINYL_READY:
        # Vinyl readiness is inferred from campaign context — a rule using this
        # trigger fires when the campaign has at least planning status and the
        # campaign was built with a vinyl channel.
        return "vinyl" in [str(ch) for ch in (context.get("channels") or [])]

    if trigger == CampaignAutomationTrigger.INTELLIGENCE_HEAT_ABOVE_THRESHOLD:
        # Intelligence-driven triggers require conditions.heat_threshold.
        # Without intelligence data in the campaign context, this never matches.
        return False

    if trigger == CampaignAutomationTrigger.SNAPSHOT_HEAT_DELTA_ABOVE_THRESHOLD:
        return False

    return False


# ---------- Action proposal ----------


def _propose_action(
    action: CampaignAutomationAction,
    action_payload: dict[str, object],
    context: dict[str, object],
) -> list[str]:
    """Describe what the action would do. Pure description — no mutations."""
    campaign_id = context.get("campaign_id", "?")

    if action == CampaignAutomationAction.MARK_CAMPAIGN_READY:
        return [f"Set campaign {campaign_id} status to 'ready'"]

    if action == CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE:
        return [f"Set campaign {campaign_id} status to 'active'"]

    if action == CampaignAutomationAction.CREATE_TASK:
        task_title = action_payload.get("task_title", "Untitled task")
        return [f"Create task '{task_title}' on campaign {campaign_id}"]

    if action == CampaignAutomationAction.ADD_WARNING:
        warning_msg = action_payload.get("warning_message", "Warning")
        return [f"Add warning to campaign {campaign_id}: {warning_msg}"]

    if action == CampaignAutomationAction.NOTIFY_OPERATOR:
        message = action_payload.get("message", "Notification")
        return [f"Notify operator: {message}"]

    if action == CampaignAutomationAction.NO_OP:
        return ["No operation — rule matched but no action defined"]

    return [f"Unknown action: {action.value}"]


# ---------- Blocked checks ----------


def _check_blocked(
    rule: CampaignAutomationRule,
    context: dict[str, object],
) -> list[str]:
    """Return blocked reasons. Empty list = not blocked. Pure function."""
    reasons: list[str] = []

    if rule.status != CampaignAutomationRuleStatus.ACTIVE:
        reasons.append(f"Rule status is '{rule.status.value}', must be 'active' to run")

    campaign_status = context.get("campaign_status")
    if campaign_status == CampaignStatus.ARCHIVED.value:
        reasons.append("Campaign is archived — no automation allowed")

    # Status transition guards
    if rule.action == CampaignAutomationAction.MARK_CAMPAIGN_READY:
        if campaign_status != CampaignStatus.PLANNING.value:
            reasons.append(
                f"Cannot mark as ready: campaign status is '{campaign_status}', expected 'planning'"
            )

    if rule.action == CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE:
        if campaign_status != CampaignStatus.READY.value:
            reasons.append(
                f"Cannot mark as active: campaign status is '{campaign_status}', expected 'ready'"
            )

    return reasons


# ---------- Single-rule evaluator ----------


def evaluate_rule(
    rule: CampaignAutomationRule,
    campaign: Campaign,
) -> CampaignAutomationDryRunResult:
    """Evaluate a single rule against a campaign. Pure function.

    Returns what *would* happen. No mutations. No side effects.
    No external calls. No scheduling. No execution.
    """
    context = build_automation_context(campaign)

    # Hard block: archived campaigns never allow automation, regardless of trigger
    if context.get("campaign_status") == CampaignStatus.ARCHIVED.value:
        return CampaignAutomationDryRunResult(
            rule_id=rule.rule_id,
            campaign_id=campaign.campaign_id,
            status=CampaignAutomationDryRunStatus.BLOCKED,
            matched=False,
            blocked_reasons=["Campaign is archived — no automation allowed"],
        )

    matched = _trigger_matches(rule.trigger, context)

    if not matched:
        return CampaignAutomationDryRunResult(
            rule_id=rule.rule_id,
            campaign_id=campaign.campaign_id,
            status=CampaignAutomationDryRunStatus.NO_MATCH,
            matched=False,
        )

    blocked_reasons = _check_blocked(rule, context)
    if blocked_reasons:
        return CampaignAutomationDryRunResult(
            rule_id=rule.rule_id,
            campaign_id=campaign.campaign_id,
            status=CampaignAutomationDryRunStatus.BLOCKED,
            matched=True,
            blocked_reasons=blocked_reasons,
            warnings=list(rule.warnings),
        )

    proposed = _propose_action(rule.action, rule.action_payload, context)

    return CampaignAutomationDryRunResult(
        rule_id=rule.rule_id,
        campaign_id=campaign.campaign_id,
        status=CampaignAutomationDryRunStatus.WOULD_RUN,
        matched=True,
        proposed_changes=proposed,
        warnings=list(rule.warnings),
    )


# ---------- Multi-rule evaluator ----------


def evaluate_rules_for_campaign(
    rules: list[CampaignAutomationRule],
    campaign: Campaign,
) -> list[CampaignAutomationDryRunResult]:
    """Evaluate multiple rules against a campaign. Pure function.

    No mutations. No side effects. No external calls.
    """
    return [evaluate_rule(rule, campaign) for rule in rules]
