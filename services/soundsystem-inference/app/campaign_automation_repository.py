"""Campaign Automation Rules Repository — S57 rule persistence.

In-memory only. Same Protocol pattern as other repositories.
Stores rule definitions. No automation execution. No scheduling.
No background jobs. No external calls. Orchestration-only.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas import (
    CampaignAutomationRule,
    CampaignAutomationRuleStatus,
    CampaignAutomationRuleSummary,
)


class CampaignAutomationRuleRepository(Protocol):
    """Persistence boundary for automation rule definitions."""

    @property
    def mode(self) -> str: ...

    def add_rule(self, rule: CampaignAutomationRule) -> None: ...

    def get_rule(self, rule_id: UUID) -> CampaignAutomationRule | None: ...

    def list_rules(self) -> list[CampaignAutomationRule]: ...

    def list_by_campaign(self, campaign_id: UUID) -> list[CampaignAutomationRule]: ...

    def update_rule(self, rule: CampaignAutomationRule) -> None: ...

    def summary(self) -> CampaignAutomationRuleSummary: ...


class InMemoryCampaignAutomationRuleRepository:
    """In-memory automation rule repository. Data lost on restart."""

    def __init__(self) -> None:
        self._rules: dict[UUID, CampaignAutomationRule] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_rule(self, rule: CampaignAutomationRule) -> None:
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: UUID) -> CampaignAutomationRule | None:
        return self._rules.get(rule_id)

    def list_rules(self) -> list[CampaignAutomationRule]:
        return sorted(
            self._rules.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )

    def list_by_campaign(self, campaign_id: UUID) -> list[CampaignAutomationRule]:
        return sorted(
            (r for r in self._rules.values() if r.campaign_id == campaign_id),
            key=lambda r: r.created_at,
            reverse=True,
        )

    def update_rule(self, rule: CampaignAutomationRule) -> None:
        self._rules[rule.rule_id] = rule

    def summary(self) -> CampaignAutomationRuleSummary:
        rules = list(self._rules.values())
        return CampaignAutomationRuleSummary(
            total_rules=len(rules),
            draft=sum(1 for r in rules if r.status == CampaignAutomationRuleStatus.DRAFT),
            active=sum(1 for r in rules if r.status == CampaignAutomationRuleStatus.ACTIVE),
            paused=sum(1 for r in rules if r.status == CampaignAutomationRuleStatus.PAUSED),
            archived=sum(1 for r in rules if r.status == CampaignAutomationRuleStatus.ARCHIVED),
        )
