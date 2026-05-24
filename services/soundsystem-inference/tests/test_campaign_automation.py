"""Tests for S57 — Campaign Automation Rules Boundary.

Covers:
- InMemory rule repository CRUD
- Rule creation via route
- Rule update via route
- Dry-run evaluation: no_match, would_run, blocked
- Trigger matching logic
- Proposed-change descriptions
- No-mutation verification (campaign unchanged after dry-run)
- Routes require operator identity
- Capabilities expose campaign_automation_rules_available
- No external calls (orchestration-only)
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import uuid4

from app.campaign_automation import (
    build_automation_context,
    evaluate_rule,
    evaluate_rules_for_campaign,
)
from app.campaign_automation_repository import InMemoryCampaignAutomationRuleRepository
from app.campaign_builder import build_campaign_from_release
from app.schemas import (
    Campaign,
    CampaignAutomationAction,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
    CampaignAutomationRuleCreateRequest,
    CampaignAutomationRuleStatus,
    CampaignAutomationRuleUpdateRequest,
    CampaignAutomationTrigger,
    CampaignStatus,
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release(
    *,
    title: str = "TEST TRACK",
    cover_ready: bool = False,
    audio_ready: bool = False,
    compliance_passed: bool = False,
    status: ReleasePackStatus = ReleasePackStatus.DRAFT,
) -> ReleasePack:
    assets: list[ReleaseAssetPlaceholder] = []
    if cover_ready:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
            )
        )
    if audio_ready:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
            )
        )

    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="Test Artist",
        genre="Electronic",
        bpm=128,
        key_signature="Am",
        social_copy=SocialCopy(
            caption_short="short",
            caption_long="long",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="rights_cleared",
                label="Rights cleared",
                passed=compliance_passed,
            ),
        ],
        compliance_passed=compliance_passed,
        assets=assets,
        dropbox_target="/releases/test",
        status=status,
    )


def _make_campaign(
    *,
    status: CampaignStatus = CampaignStatus.PLANNING,
    cover_ready: bool = True,
    audio_ready: bool = True,
) -> Campaign:
    release = _make_release(cover_ready=cover_ready, audio_ready=audio_ready)
    campaign = build_campaign_from_release(release)
    if status != CampaignStatus.PLANNING:
        campaign = campaign.model_copy(update={"status": status})
    return campaign


def _make_rule(
    *,
    campaign_id=None,
    trigger: CampaignAutomationTrigger = CampaignAutomationTrigger.RELEASE_READY,
    action: CampaignAutomationAction = CampaignAutomationAction.MARK_CAMPAIGN_READY,
    status: CampaignAutomationRuleStatus = CampaignAutomationRuleStatus.ACTIVE,
    conditions: dict | None = None,
    action_payload: dict | None = None,
    warnings: list[str] | None = None,
) -> CampaignAutomationRule:
    return CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=campaign_id,
        name="Test Rule",
        status=status,
        trigger=trigger,
        action=action,
        conditions=conditions or {},
        action_payload=action_payload or {},
        warnings=warnings or [],
    )


# ---------- Repository CRUD ----------


class TestInMemoryAutomationRuleRepository:
    def test_add_and_get(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        rule = _make_rule()
        repo.add_rule(rule)
        found = repo.get_rule(rule.rule_id)
        assert found is not None
        assert found.rule_id == rule.rule_id

    def test_get_returns_none(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        assert repo.get_rule(uuid4()) is None

    def test_list_rules(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        r1 = _make_rule()
        r2 = _make_rule()
        repo.add_rule(r1)
        repo.add_rule(r2)
        result = repo.list_rules()
        assert len(result) == 2

    def test_list_by_campaign(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        cid = uuid4()
        r1 = _make_rule(campaign_id=cid)
        r2 = _make_rule(campaign_id=uuid4())
        r3 = _make_rule(campaign_id=cid)
        repo.add_rule(r1)
        repo.add_rule(r2)
        repo.add_rule(r3)
        result = repo.list_by_campaign(cid)
        assert len(result) == 2
        assert all(r.campaign_id == cid for r in result)

    def test_update_rule(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        rule = _make_rule()
        repo.add_rule(rule)
        updated = rule.model_copy(update={"status": CampaignAutomationRuleStatus.PAUSED})
        repo.update_rule(updated)
        found = repo.get_rule(rule.rule_id)
        assert found is not None
        assert found.status == CampaignAutomationRuleStatus.PAUSED

    def test_summary(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        repo.add_rule(_make_rule(status=CampaignAutomationRuleStatus.DRAFT))
        repo.add_rule(_make_rule(status=CampaignAutomationRuleStatus.ACTIVE))
        repo.add_rule(_make_rule(status=CampaignAutomationRuleStatus.ACTIVE))
        repo.add_rule(_make_rule(status=CampaignAutomationRuleStatus.PAUSED))
        summary = repo.summary()
        assert summary.total_rules == 4
        assert summary.draft == 1
        assert summary.active == 2
        assert summary.paused == 1
        assert summary.archived == 0

    def test_mode(self) -> None:
        repo = InMemoryCampaignAutomationRuleRepository()
        assert repo.mode == "in_memory"


# ---------- Context builder ----------


class TestBuildAutomationContext:
    def test_context_fields(self) -> None:
        campaign = _make_campaign()
        ctx = build_automation_context(campaign)
        assert ctx["campaign_status"] == "planning"
        assert isinstance(ctx["channels"], list)
        assert isinstance(ctx["total_tasks"], int)
        assert isinstance(ctx["has_warnings"], bool)

    def test_context_is_read_only_dict(self) -> None:
        campaign = _make_campaign()
        ctx = build_automation_context(campaign)
        assert isinstance(ctx, dict)
        # Modifying context must not affect campaign
        ctx["campaign_status"] = "archived"
        assert campaign.status == CampaignStatus.PLANNING


# ---------- Dry-run evaluation ----------


class TestEvaluateRule:
    def test_no_match(self) -> None:
        """Rule with campaign_ready trigger should not match a planning campaign."""
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.NO_MATCH
        assert result.matched is False
        assert result.proposed_changes == []

    def test_would_run(self) -> None:
        """Active rule matching release_ready on a planning campaign → would_run."""
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert result.matched is True
        assert len(result.proposed_changes) > 0
        assert "ready" in result.proposed_changes[0].lower()

    def test_blocked_draft_rule(self) -> None:
        """Draft rule that matches → blocked because status is not active."""
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            status=CampaignAutomationRuleStatus.DRAFT,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.BLOCKED
        assert result.matched is True
        assert any("draft" in r.lower() for r in result.blocked_reasons)

    def test_blocked_archived_campaign(self) -> None:
        """Active rule on archived campaign → blocked."""
        campaign = _make_campaign(status=CampaignStatus.ARCHIVED)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.NO_OP,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.BLOCKED
        assert any("archived" in r.lower() for r in result.blocked_reasons)

    def test_blocked_invalid_transition(self) -> None:
        """mark_campaign_ready on a campaign already in ready status → blocked."""
        campaign = _make_campaign(status=CampaignStatus.READY)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.BLOCKED
        assert any("planning" in r.lower() for r in result.blocked_reasons)

    def test_proposed_changes_create_task(self) -> None:
        """create_task action proposes a task creation."""
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.CREATE_TASK,
            action_payload={"task_title": "Upload to SoundCloud"},
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert "Upload to SoundCloud" in result.proposed_changes[0]

    def test_proposed_changes_add_warning(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.ADD_WARNING,
            action_payload={"warning_message": "Missing cover art"},
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert "Missing cover art" in result.proposed_changes[0]

    def test_proposed_changes_notify_operator(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
            action_payload={"message": "Campaign ready for review"},
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert "Campaign ready for review" in result.proposed_changes[0]

    def test_no_op_action(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.NO_OP,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert "no operation" in result.proposed_changes[0].lower()

    def test_rule_warnings_propagated(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            status=CampaignAutomationRuleStatus.ACTIVE,
            warnings=["experimental rule"],
        )
        result = evaluate_rule(rule, campaign)
        assert "experimental rule" in result.warnings


# ---------- Trigger matching ----------


class TestTriggerMatching:
    def test_campaign_ready_trigger(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.READY)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.matched is True

    def test_campaign_active_trigger(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.ACTIVE)
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.CAMPAIGN_ACTIVE,
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
            action_payload={"message": "Campaign is live"},
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.matched is True
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN

    def test_intelligence_heat_never_matches(self) -> None:
        """Intelligence triggers require external data not in campaign context."""
        campaign = _make_campaign()
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.INTELLIGENCE_HEAT_ABOVE_THRESHOLD,
            action=CampaignAutomationAction.NO_OP,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.NO_MATCH

    def test_snapshot_heat_delta_never_matches(self) -> None:
        campaign = _make_campaign()
        rule = _make_rule(
            trigger=CampaignAutomationTrigger.SNAPSHOT_HEAT_DELTA_ABOVE_THRESHOLD,
            action=CampaignAutomationAction.NO_OP,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        result = evaluate_rule(rule, campaign)
        assert result.status == CampaignAutomationDryRunStatus.NO_MATCH


# ---------- Multi-rule evaluation ----------


class TestEvaluateRulesForCampaign:
    def test_multiple_rules(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        rules = [
            _make_rule(
                trigger=CampaignAutomationTrigger.RELEASE_READY,
                action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
                status=CampaignAutomationRuleStatus.ACTIVE,
            ),
            _make_rule(
                trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
                action=CampaignAutomationAction.NOTIFY_OPERATOR,
                status=CampaignAutomationRuleStatus.ACTIVE,
            ),
        ]
        results = evaluate_rules_for_campaign(rules, campaign)
        assert len(results) == 2
        assert results[0].status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert results[1].status == CampaignAutomationDryRunStatus.NO_MATCH

    def test_empty_rules(self) -> None:
        campaign = _make_campaign()
        results = evaluate_rules_for_campaign([], campaign)
        assert results == []


# ---------- No-mutation verification ----------


class TestNoMutations:
    def test_dry_run_does_not_mutate_campaign(self) -> None:
        """The campaign object must remain unchanged after dry-run evaluation."""
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        original_status = campaign.status
        original_tasks = len(campaign.tasks)
        original_warnings = len(campaign.warnings)

        rule = _make_rule(
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            status=CampaignAutomationRuleStatus.ACTIVE,
        )
        evaluate_rule(rule, campaign)

        assert campaign.status == original_status
        assert len(campaign.tasks) == original_tasks
        assert len(campaign.warnings) == original_warnings

    def test_multi_dry_run_does_not_mutate(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.PLANNING)
        original_dict = campaign.model_dump(mode="json")

        rules = [
            _make_rule(
                trigger=CampaignAutomationTrigger.RELEASE_READY,
                action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
                status=CampaignAutomationRuleStatus.ACTIVE,
            ),
            _make_rule(
                trigger=CampaignAutomationTrigger.RELEASE_READY,
                action=CampaignAutomationAction.CREATE_TASK,
                action_payload={"task_title": "Do something"},
                status=CampaignAutomationRuleStatus.ACTIVE,
            ),
        ]
        evaluate_rules_for_campaign(rules, campaign)

        assert campaign.model_dump(mode="json") == original_dict


# ---------- Route E2E ----------


class TestAutomationRoutes:
    def _store_release_and_campaign(self):
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, release_pack_repository
        from app.schemas import CampaignCreateRequest

        release = _make_release(cover_ready=True, audio_ready=True)
        release_pack_repository.store(release)
        campaign = asyncio.run(
            create_campaign(CampaignCreateRequest(release_id=release.release_id), DEV_OPERATOR)
        )
        return release, campaign

    def test_create_and_get_rule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_automation_rule, get_automation_rule

        _, campaign = self._store_release_and_campaign()
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Auto-ready on release",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        )
        created = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        assert created.name == "Auto-ready on release"
        assert created.created_by == DEV_OPERATOR.operator_id

        fetched = asyncio.run(get_automation_rule(created.rule_id))
        assert fetched.rule_id == created.rule_id

    def test_list_rules(self) -> None:
        from app.main import list_automation_rules

        result = asyncio.run(list_automation_rules())
        assert isinstance(result, list)

    def test_summary(self) -> None:
        from app.main import get_automation_rule_summary

        result = asyncio.run(get_automation_rule_summary())
        assert hasattr(result, "total_rules")

    def test_update_rule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_automation_rule, update_automation_rule

        _, campaign = self._store_release_and_campaign()
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Rule to update",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.NO_OP,
        )
        created = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        updated = asyncio.run(
            update_automation_rule(
                created.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        assert updated.status == CampaignAutomationRuleStatus.ACTIVE

    def test_list_by_campaign(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            list_automation_rules_by_campaign,
        )

        _, campaign = self._store_release_and_campaign()
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Campaign-scoped rule",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.NO_OP,
        )
        asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        result = asyncio.run(list_automation_rules_by_campaign(campaign.campaign_id))
        assert len(result) >= 1
        assert all(r.campaign_id == campaign.campaign_id for r in result)

    def test_dry_run_single_rule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            dry_run_automation_rule,
            update_automation_rule,
        )

        _, campaign = self._store_release_and_campaign()
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Dry run test",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        )
        created = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        # Activate the rule
        asyncio.run(
            update_automation_rule(
                created.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        result = asyncio.run(dry_run_automation_rule(created.rule_id, DEV_OPERATOR))
        assert result.status == CampaignAutomationDryRunStatus.WOULD_RUN
        assert result.matched is True

    def test_dry_run_campaign(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            dry_run_campaign_automation,
            update_automation_rule,
        )

        _, campaign = self._store_release_and_campaign()
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Campaign dry-run test",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        )
        created = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        asyncio.run(
            update_automation_rule(
                created.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        results = asyncio.run(dry_run_campaign_automation(campaign.campaign_id, DEV_OPERATOR))
        assert isinstance(results, list)
        assert len(results) >= 1
        assert results[0].campaign_id == campaign.campaign_id


# ---------- Capabilities ----------


class TestAutomationCapabilities:
    def test_automation_rules_in_caps(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_automation_rules_available is True

    def test_campaign_os_still_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_os_available is True


# ---------- Backwards-compatible imports ----------


class TestBackwardsCompatibleImports:
    def test_automation_repository_protocol(self) -> None:
        from app.campaign_automation_repository import CampaignAutomationRuleRepository

        assert CampaignAutomationRuleRepository is not None

    def test_in_memory_automation_repository(self) -> None:
        from app.campaign_automation_repository import (
            InMemoryCampaignAutomationRuleRepository,
        )

        assert InMemoryCampaignAutomationRuleRepository is not None

    def test_evaluator_functions(self) -> None:
        from app.campaign_automation import (
            build_automation_context,
            evaluate_rule,
            evaluate_rules_for_campaign,
        )

        assert build_automation_context is not None
        assert evaluate_rule is not None
        assert evaluate_rules_for_campaign is not None


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_repository(self) -> None:
        from app import campaign_automation_repository

        source = inspect.getsource(campaign_automation_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_http_imports_in_evaluator(self) -> None:
        from app import campaign_automation

        source = inspect.getsource(campaign_automation)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_scheduler_imports_in_repository(self) -> None:
        from app import campaign_automation_repository

        source = inspect.getsource(campaign_automation_repository)
        assert "import schedule" not in source
        assert "celery" not in source
        assert "crontab" not in source

    def test_no_scheduler_imports_in_evaluator(self) -> None:
        from app import campaign_automation

        source = inspect.getsource(campaign_automation)
        assert "import schedule" not in source
        assert "celery" not in source
        assert "crontab" not in source
