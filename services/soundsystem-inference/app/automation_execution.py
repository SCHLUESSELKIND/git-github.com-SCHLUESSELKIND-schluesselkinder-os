"""Automation Execution Boundary — S58.

Disabled-by-default execution boundary for Campaign Automation Rules.

This module ONLY creates execution job records. It never:
- mutates the campaign
- mutates the rule
- mutates analytics or any other repository
- calls any provider API
- sends emails, social posts, notifications
- schedules or queues background work
- triggers webhooks

Even in MOCK mode the execution is purely a state transition on the job
itself; no campaign or provider state changes. The job is an audit record
of the operator's intent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.auth import Operator
from app.schemas import (
    AutomationExecutionJob,
    AutomationExecutionMode,
    AutomationExecutionStatus,
    Campaign,
    CampaignAutomationDryRunResult,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
)


# ---------- Public API ----------


def create_execution_job_from_dry_run(
    rule: CampaignAutomationRule,
    campaign: Campaign,
    dry_run: CampaignAutomationDryRunResult,
    operator: Operator,
    mode: AutomationExecutionMode,
) -> AutomationExecutionJob:
    """Create an execution job from a dry-run result.

    Pure function. No side effects. No mutations on campaign or rule.
    Job status is determined by the configured execution mode and the
    dry-run result.

    Rules:
    - mode DISABLED → status = BLOCKED with explanatory reason
    - dry_run.status != WOULD_RUN → status = BLOCKED with dry-run reasons
    - mode MOCK + dry_run WOULD_RUN → status = QUEUED
    """
    now = datetime.now(timezone.utc)
    status, blocked_reasons = _resolve_status(mode, dry_run)

    return AutomationExecutionJob(
        execution_id=uuid4(),
        rule_id=rule.rule_id,
        campaign_id=campaign.campaign_id,
        dry_run_status=dry_run.status,
        status=status,
        proposed_changes=list(dry_run.proposed_changes),
        blocked_reasons=blocked_reasons,
        warnings=list(dry_run.warnings),
        created_by=operator.operator_id,
        created_at=now,
        updated_at=now,
    )


def execute_mock_job(
    job: AutomationExecutionJob,
    mode: AutomationExecutionMode,
) -> AutomationExecutionJob:
    """Transition a queued job to COMPLETED_MOCK. No side effects.

    Pure function. Returns a new job copy. Does not touch the campaign,
    the rule, or any provider. Records the operator's intent that the
    automation "ran" in mock mode.

    Rules:
    - mode must be MOCK; otherwise job is moved to BLOCKED
    - job must be in QUEUED state; otherwise FAILED
    """
    now = datetime.now(timezone.utc)

    if mode != AutomationExecutionMode.MOCK:
        return job.model_copy(
            update={
                "status": AutomationExecutionStatus.BLOCKED,
                "blocked_reasons": [
                    *job.blocked_reasons,
                    "Automation execution is disabled — mock execution refused.",
                ],
                "updated_at": now,
            }
        )

    if job.status != AutomationExecutionStatus.QUEUED:
        return job.model_copy(
            update={
                "status": AutomationExecutionStatus.FAILED,
                "blocked_reasons": [
                    *job.blocked_reasons,
                    f"Cannot execute job in '{job.status.value}' state; expected 'queued'.",
                ],
                "updated_at": now,
            }
        )

    return job.model_copy(
        update={
            "status": AutomationExecutionStatus.COMPLETED_MOCK,
            "updated_at": now,
            "completed_at": now,
        }
    )


# ---------- Internals ----------


def _resolve_status(
    mode: AutomationExecutionMode,
    dry_run: CampaignAutomationDryRunResult,
) -> tuple[AutomationExecutionStatus, list[str]]:
    """Decide initial job status + blocked reasons. Pure function."""
    blocked_reasons: list[str] = []

    if mode == AutomationExecutionMode.DISABLED:
        blocked_reasons.append(
            "Automation execution is disabled. "
            "Set SOUNDSYSTEM_AUTOMATION_EXECUTION_MODE=mock to enable mock execution."
        )

    if dry_run.status != CampaignAutomationDryRunStatus.WOULD_RUN:
        blocked_reasons.append(
            f"Dry-run status is '{dry_run.status.value}' — execution not allowed."
        )
        blocked_reasons.extend(dry_run.blocked_reasons)

    if blocked_reasons:
        return AutomationExecutionStatus.BLOCKED, blocked_reasons

    return AutomationExecutionStatus.QUEUED, []
