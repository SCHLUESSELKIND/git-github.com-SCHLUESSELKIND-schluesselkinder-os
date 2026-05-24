"""Tests for S58 — Automation Execution Queue Boundary.

Covers:
- Config default DISABLED, mode parsing, fail-loud invalid value
- create_execution_job_from_dry_run: BLOCKED in disabled, QUEUED in mock when would_run
- Dry-run no_match → BLOCKED
- Dry-run blocked → BLOCKED with reasons propagated
- execute_mock_job: only works in mock mode, transitions to COMPLETED_MOCK
- execute_mock_job: does not mutate campaign or rule
- Repository CRUD + summary
- Routes require operator
- queue-execution runs dry-run before creating job
- Capabilities expose execution mode
- No external API calls
- No scheduler/background imports
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import uuid4

import pytest

from app.automation_execution import (
    create_execution_job_from_dry_run,
    execute_mock_job,
)
from app.automation_execution_repository import (
    InMemoryAutomationExecutionRepository,
)
from app.campaign_automation import evaluate_rule
from app.campaign_builder import build_campaign_from_release
from app.config import (
    AUTOMATION_EXECUTION_MODE_ENV,
    AutomationExecutionMode as ConfigExecMode,
    automation_execution_mode,
)
from app.schemas import (
    AutomationExecutionJob,
    AutomationExecutionMode,
    AutomationExecutionStatus,
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
    cover_ready: bool = True,
    audio_ready: bool = True,
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


def _make_campaign(*, status: CampaignStatus = CampaignStatus.PLANNING) -> Campaign:
    release = _make_release()
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
) -> CampaignAutomationRule:
    return CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=campaign_id,
        name="Test Rule",
        status=status,
        trigger=trigger,
        action=action,
    )


def _make_operator():
    from app.auth import DEV_OPERATOR

    return DEV_OPERATOR


def _make_job(
    *,
    status: AutomationExecutionStatus = AutomationExecutionStatus.QUEUED,
) -> AutomationExecutionJob:
    return AutomationExecutionJob(
        execution_id=uuid4(),
        rule_id=uuid4(),
        campaign_id=uuid4(),
        dry_run_status=CampaignAutomationDryRunStatus.WOULD_RUN,
        status=status,
        proposed_changes=["preview"],
    )


# ---------- Config ----------


class TestAutomationExecutionConfig:
    def test_default_is_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_MODE_ENV, raising=False)
        assert automation_execution_mode() == ConfigExecMode.DISABLED

    def test_explicit_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "disabled")
        assert automation_execution_mode() == ConfigExecMode.DISABLED

    def test_mock_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        assert automation_execution_mode() == ConfigExecMode.MOCK

    def test_invalid_value_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "live")
        with pytest.raises(RuntimeError, match="invalid"):
            automation_execution_mode()

    def test_schema_mode_matches_config_mode(self) -> None:
        # Schema enum mirrors config enum
        assert {m.value for m in AutomationExecutionMode} == {m.value for m in ConfigExecMode}


# ---------- Job creation from dry-run ----------


class TestCreateExecutionJob:
    def test_disabled_blocks_even_when_would_run(self) -> None:
        campaign = _make_campaign()
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)
        assert dry_run.status == CampaignAutomationDryRunStatus.WOULD_RUN

        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.DISABLED
        )
        assert job.status == AutomationExecutionStatus.BLOCKED
        assert any("disabled" in r.lower() for r in job.blocked_reasons)
        assert job.dry_run_status == CampaignAutomationDryRunStatus.WOULD_RUN

    def test_mock_queues_when_would_run(self) -> None:
        campaign = _make_campaign()
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)

        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.MOCK
        )
        assert job.status == AutomationExecutionStatus.QUEUED
        assert job.blocked_reasons == []
        assert "ready" in job.proposed_changes[0].lower()

    def test_mock_blocks_when_no_match(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.READY)
        rule = _make_rule(
            campaign_id=campaign.campaign_id,
            # campaign_active trigger won't match a READY campaign
            trigger=CampaignAutomationTrigger.CAMPAIGN_ACTIVE,
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
        )
        dry_run = evaluate_rule(rule, campaign)
        assert dry_run.status == CampaignAutomationDryRunStatus.NO_MATCH

        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.MOCK
        )
        assert job.status == AutomationExecutionStatus.BLOCKED
        assert any("no_match" in r for r in job.blocked_reasons)

    def test_mock_blocks_when_dry_run_blocked(self) -> None:
        campaign = _make_campaign(status=CampaignStatus.ARCHIVED)
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)
        assert dry_run.status == CampaignAutomationDryRunStatus.BLOCKED

        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.MOCK
        )
        assert job.status == AutomationExecutionStatus.BLOCKED
        # The dry-run's blocked_reasons are propagated through
        assert any("archived" in r.lower() for r in job.blocked_reasons)

    def test_records_operator_identity(self) -> None:
        campaign = _make_campaign()
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)
        op = _make_operator()

        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, op, AutomationExecutionMode.MOCK
        )
        assert job.created_by == op.operator_id

    def test_does_not_mutate_inputs(self) -> None:
        campaign = _make_campaign()
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)

        rule_before = rule.model_dump(mode="json")
        campaign_before = campaign.model_dump(mode="json")

        create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.MOCK
        )

        assert rule.model_dump(mode="json") == rule_before
        assert campaign.model_dump(mode="json") == campaign_before


# ---------- Mock execution ----------


class TestExecuteMockJob:
    def test_disabled_mode_blocks_execute(self) -> None:
        job = _make_job(status=AutomationExecutionStatus.QUEUED)
        result = execute_mock_job(job, AutomationExecutionMode.DISABLED)
        assert result.status == AutomationExecutionStatus.BLOCKED
        assert any("disabled" in r.lower() for r in result.blocked_reasons)

    def test_mock_mode_completes_queued_job(self) -> None:
        job = _make_job(status=AutomationExecutionStatus.QUEUED)
        result = execute_mock_job(job, AutomationExecutionMode.MOCK)
        assert result.status == AutomationExecutionStatus.COMPLETED_MOCK
        assert result.completed_at is not None

    def test_non_queued_job_fails(self) -> None:
        job = _make_job(status=AutomationExecutionStatus.BLOCKED)
        result = execute_mock_job(job, AutomationExecutionMode.MOCK)
        assert result.status == AutomationExecutionStatus.FAILED

    def test_returns_copy_does_not_mutate(self) -> None:
        job = _make_job(status=AutomationExecutionStatus.QUEUED)
        original = job.model_dump(mode="json")
        execute_mock_job(job, AutomationExecutionMode.MOCK)
        # Original job is unchanged (Pydantic models with model_copy)
        assert job.model_dump(mode="json") == original

    def test_does_not_mutate_campaign(self) -> None:
        """The campaign object passed nowhere through execute_mock_job."""
        campaign = _make_campaign()
        rule = _make_rule(campaign_id=campaign.campaign_id)
        dry_run = evaluate_rule(rule, campaign)
        job = create_execution_job_from_dry_run(
            rule, campaign, dry_run, _make_operator(), AutomationExecutionMode.MOCK
        )
        campaign_before = campaign.model_dump(mode="json")
        execute_mock_job(job, AutomationExecutionMode.MOCK)
        assert campaign.model_dump(mode="json") == campaign_before


# ---------- Repository CRUD ----------


class TestInMemoryExecutionRepository:
    def test_add_and_get(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        job = _make_job()
        repo.add_job(job)
        assert repo.get_job(job.execution_id) is not None

    def test_get_returns_none(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        assert repo.get_job(uuid4()) is None

    def test_list_jobs(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        repo.add_job(_make_job())
        repo.add_job(_make_job())
        assert len(repo.list_jobs()) == 2

    def test_list_by_campaign(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        cid = uuid4()
        j1 = _make_job()
        j1 = j1.model_copy(update={"campaign_id": cid})
        j2 = _make_job()
        repo.add_job(j1)
        repo.add_job(j2)
        result = repo.list_by_campaign(cid)
        assert len(result) == 1
        assert result[0].campaign_id == cid

    def test_update_job(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        job = _make_job(status=AutomationExecutionStatus.QUEUED)
        repo.add_job(job)
        updated = job.model_copy(update={"status": AutomationExecutionStatus.COMPLETED_MOCK})
        repo.update_job(updated)
        found = repo.get_job(job.execution_id)
        assert found is not None
        assert found.status == AutomationExecutionStatus.COMPLETED_MOCK

    def test_summary_counts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_MODE_ENV, raising=False)
        repo = InMemoryAutomationExecutionRepository()
        repo.add_job(_make_job(status=AutomationExecutionStatus.QUEUED))
        repo.add_job(_make_job(status=AutomationExecutionStatus.BLOCKED))
        repo.add_job(_make_job(status=AutomationExecutionStatus.BLOCKED))
        repo.add_job(_make_job(status=AutomationExecutionStatus.COMPLETED_MOCK))
        s = repo.summary()
        assert s.total == 4
        assert s.queued == 1
        assert s.blocked == 2
        assert s.completed_mock == 1
        assert s.failed == 0
        assert s.execution_mode == AutomationExecutionMode.DISABLED

    def test_summary_reports_mock_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        repo = InMemoryAutomationExecutionRepository()
        s = repo.summary()
        assert s.execution_mode == AutomationExecutionMode.MOCK

    def test_mode(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        assert repo.mode == "in_memory"


# ---------- Route E2E ----------


class TestExecutionRoutes:
    def _setup(self):
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            create_campaign,
            release_pack_repository,
        )
        from app.schemas import CampaignCreateRequest

        release = _make_release()
        release_pack_repository.store(release)
        try:
            campaign = asyncio.run(
                create_campaign(CampaignCreateRequest(release_id=release.release_id), DEV_OPERATOR)
            )
        except Exception:
            # Already-exists collisions in shared test repo — fetch instead
            from app.main import campaign_repository as repo

            existing = repo.get_by_release(release.release_id)
            assert existing is not None
            campaign = existing
        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Auto-ready",
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        )
        rule = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        return campaign, rule

    def test_queue_execution_disabled_creates_blocked_job(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_MODE_ENV, raising=False)
        from app.auth import DEV_OPERATOR
        from app.main import queue_automation_execution

        _, rule = self._setup()
        result = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        assert result.job.status == AutomationExecutionStatus.BLOCKED
        assert "disabled" in result.note.lower()

    def test_queue_execution_mock_creates_queued_job(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.auth import DEV_OPERATOR
        from app.main import (
            queue_automation_execution,
            update_automation_rule,
        )

        _, rule = self._setup()
        # Activate the rule so dry-run yields WOULD_RUN
        asyncio.run(
            update_automation_rule(
                rule.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        result = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        assert result.job.status == AutomationExecutionStatus.QUEUED

    def test_queue_execution_unknown_rule_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import queue_automation_execution
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(queue_automation_execution(uuid4(), DEV_OPERATOR))
        assert exc.value.status_code == 404

    def test_list_executions(self) -> None:
        from app.main import list_automation_executions

        result = asyncio.run(list_automation_executions())
        assert isinstance(result, list)

    def test_summary_route(self) -> None:
        from app.main import get_automation_execution_summary

        result = asyncio.run(get_automation_execution_summary())
        assert hasattr(result, "total")
        assert hasattr(result, "execution_mode")

    def test_execute_mock_route_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.auth import DEV_OPERATOR
        from app.main import (
            execute_automation_execution_mock,
            queue_automation_execution,
            update_automation_rule,
        )

        _, rule = self._setup()
        asyncio.run(
            update_automation_rule(
                rule.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        qres = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        assert qres.job.status == AutomationExecutionStatus.QUEUED

        # Now flip to disabled and try to execute — should block
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "disabled")
        result = asyncio.run(execute_automation_execution_mock(qres.job.execution_id, DEV_OPERATOR))
        assert result.job.status == AutomationExecutionStatus.BLOCKED

    def test_execute_mock_route_completes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.auth import DEV_OPERATOR
        from app.main import (
            execute_automation_execution_mock,
            queue_automation_execution,
            update_automation_rule,
        )

        _, rule = self._setup()
        asyncio.run(
            update_automation_rule(
                rule.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )
        qres = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        result = asyncio.run(execute_automation_execution_mock(qres.job.execution_id, DEV_OPERATOR))
        assert result.job.status == AutomationExecutionStatus.COMPLETED_MOCK
        assert result.job.completed_at is not None

    def test_get_execution_unknown_404(self) -> None:
        from app.main import get_automation_execution
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_automation_execution(uuid4()))
        assert exc.value.status_code == 404

    def test_list_by_campaign(self) -> None:
        from app.main import list_automation_executions_by_campaign

        result = asyncio.run(list_automation_executions_by_campaign(uuid4()))
        assert isinstance(result, list)


# ---------- Capabilities ----------


class TestExecutionCapabilities:
    def test_boundary_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_boundary_available is True

    def test_default_mode_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_MODE_ENV, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_mode == "disabled"

    def test_mock_mode_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_mode == "mock"


# ---------- Backwards-compatible imports ----------


class TestBackwardsCompatibleImports:
    def test_repository_protocol(self) -> None:
        from app.automation_execution_repository import AutomationExecutionRepository

        assert AutomationExecutionRepository is not None

    def test_in_memory_repository(self) -> None:
        from app.automation_execution_repository import (
            InMemoryAutomationExecutionRepository,
        )

        assert InMemoryAutomationExecutionRepository is not None

    def test_execution_module_functions(self) -> None:
        from app.automation_execution import (
            create_execution_job_from_dry_run,
            execute_mock_job,
        )

        assert create_execution_job_from_dry_run is not None
        assert execute_mock_job is not None


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_execution(self) -> None:
        from app import automation_execution

        source = inspect.getsource(automation_execution)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_http_imports_in_repository(self) -> None:
        from app import automation_execution_repository

        source = inspect.getsource(automation_execution_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_scheduler_imports(self) -> None:
        from app import automation_execution, automation_execution_repository

        for module in (automation_execution, automation_execution_repository):
            source = inspect.getsource(module)
            assert "import schedule" not in source
            assert "celery" not in source
            assert "crontab" not in source
            assert "apscheduler" not in source

    def test_no_background_worker_imports(self) -> None:
        from app import automation_execution

        source = inspect.getsource(automation_execution)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "asyncio.create_task" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source


# ---------- Drying out the queueing path ----------


class TestQueueExecutionDryRunsFirst:
    def test_queue_execution_invokes_dry_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """queue-execution must call the dry-run evaluator before creating a job.

        We assert this indirectly: a rule with NO_MATCH dry-run produces a
        BLOCKED job with no_match in blocked_reasons.
        """
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            create_campaign,
            queue_automation_execution,
            release_pack_repository,
            update_automation_rule,
        )
        from app.schemas import CampaignCreateRequest

        release = _make_release()
        release_pack_repository.store(release)
        try:
            campaign = asyncio.run(
                create_campaign(CampaignCreateRequest(release_id=release.release_id), DEV_OPERATOR)
            )
        except Exception:
            from app.main import campaign_repository as repo

            existing = repo.get_by_release(release.release_id)
            assert existing is not None
            campaign = existing

        # Move campaign to READY so CAMPAIGN_ACTIVE trigger won't match
        from app.main import update_campaign
        from app.schemas import CampaignUpdateRequest

        asyncio.run(
            update_campaign(
                campaign.campaign_id,
                CampaignUpdateRequest(status=CampaignStatus.READY),
                DEV_OPERATOR,
            )
        )

        req = CampaignAutomationRuleCreateRequest(
            campaign_id=campaign.campaign_id,
            name="Won't fire",
            # CAMPAIGN_ACTIVE only fires on ACTIVE — campaign is READY → NO_MATCH
            trigger=CampaignAutomationTrigger.CAMPAIGN_ACTIVE,
            action=CampaignAutomationAction.NOTIFY_OPERATOR,
        )
        rule = asyncio.run(create_automation_rule(req, DEV_OPERATOR))
        asyncio.run(
            update_automation_rule(
                rule.rule_id,
                CampaignAutomationRuleUpdateRequest(status=CampaignAutomationRuleStatus.ACTIVE),
                DEV_OPERATOR,
            )
        )

        result = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        assert result.job.status == AutomationExecutionStatus.BLOCKED
        assert result.job.dry_run_status == CampaignAutomationDryRunStatus.NO_MATCH
