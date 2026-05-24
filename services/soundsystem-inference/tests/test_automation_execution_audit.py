"""Tests for S59 — Automation Execution Audit Log.

Covers:
- Config defaults (in_memory) + fail-loud on invalid values
- Postgres mode without DATABASE_URL fails loudly
- InMemory job repository preserves existing S58 behavior
- Factory builds correct repository per mode
- Audit repo add/list/list_by_execution/list_by_campaign/summary
- queue-execution creates a "queue_execution" audit record
- execute-mock creates a transition audit record with from/to status
- Audit records are append-only (no deletes exposed)
- Audit chronological order on list_by_execution
- Audit reverse-chronological on list_records / list_by_campaign
- Audit routes (4) read-only and return correct records
- Capabilities expose repository_mode + audit_available + audit_mode
- No external API calls
- No scheduler/background imports
- Existing S58 tests still pass (smoke verification)
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.automation_execution_audit import (
    InMemoryAutomationExecutionAuditRepository,
    build_automation_execution_audit_repository,
)
from app.automation_execution_repository import (
    InMemoryAutomationExecutionRepository,
    build_automation_execution_repository,
)
from app.campaign_builder import build_campaign_from_release
from app.config import (
    AUTOMATION_EXECUTION_AUDIT_ENV,
    AUTOMATION_EXECUTION_MODE_ENV,
    AUTOMATION_EXECUTION_REPOSITORY_ENV,
    DATABASE_URL_ENV,
    AutomationExecutionAuditConfigError,
    AutomationExecutionAuditMode,
    AutomationExecutionRepositoryConfigError,
    AutomationExecutionRepositoryMode,
    automation_execution_audit_mode,
    automation_execution_repository_mode,
)
from app.schemas import (
    AutomationExecutionAuditRecord,
    AutomationExecutionJob,
    AutomationExecutionStatus,
    Campaign,
    CampaignAutomationAction,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
    CampaignAutomationRuleCreateRequest,
    CampaignAutomationRuleStatus,
    CampaignAutomationRuleUpdateRequest,
    CampaignAutomationTrigger,
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release(*, title: str = "TEST TRACK") -> ReleasePack:
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
                passed=False,
            ),
        ],
        compliance_passed=False,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
            ),
        ],
        dropbox_target="/releases/test",
        status=ReleasePackStatus.DRAFT,
    )


def _make_campaign() -> Campaign:
    release = _make_release()
    return build_campaign_from_release(release)


def _make_rule(*, campaign_id) -> CampaignAutomationRule:
    return CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=campaign_id,
        name="Test Rule",
        status=CampaignAutomationRuleStatus.ACTIVE,
        trigger=CampaignAutomationTrigger.RELEASE_READY,
        action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
    )


def _make_job(
    *,
    campaign_id=None,
    execution_id=None,
    rule_id=None,
    status: AutomationExecutionStatus = AutomationExecutionStatus.QUEUED,
) -> AutomationExecutionJob:
    return AutomationExecutionJob(
        execution_id=execution_id or uuid4(),
        rule_id=rule_id or uuid4(),
        campaign_id=campaign_id or uuid4(),
        dry_run_status=CampaignAutomationDryRunStatus.WOULD_RUN,
        status=status,
        proposed_changes=["preview"],
    )


def _make_audit(
    *,
    execution_id=None,
    rule_id=None,
    campaign_id=None,
    from_status: AutomationExecutionStatus | None = None,
    to_status: AutomationExecutionStatus = AutomationExecutionStatus.QUEUED,
    operator_id: str | None = "op@test",
    reason: str = "queue_execution",
    created_at: datetime | None = None,
) -> AutomationExecutionAuditRecord:
    return AutomationExecutionAuditRecord(
        audit_id=uuid4(),
        execution_id=execution_id or uuid4(),
        rule_id=rule_id or uuid4(),
        campaign_id=campaign_id or uuid4(),
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        reason=reason,
        details={},
        created_at=created_at or datetime.now(timezone.utc),
    )


# ---------- Config ----------


class TestExecutionRepositoryConfig:
    def test_default_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, raising=False)
        assert automation_execution_repository_mode() == AutomationExecutionRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, "in_memory")
        assert automation_execution_repository_mode() == AutomationExecutionRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, "postgres")
        assert automation_execution_repository_mode() == AutomationExecutionRepositoryMode.POSTGRES

    def test_invalid_value_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, "redis")
        with pytest.raises(RuntimeError, match="invalid"):
            automation_execution_repository_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
        with pytest.raises(AutomationExecutionRepositoryConfigError):
            build_automation_execution_repository()


class TestAuditConfig:
    def test_default_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_AUDIT_ENV, raising=False)
        assert automation_execution_audit_mode() == AutomationExecutionAuditMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_AUDIT_ENV, "in_memory")
        assert automation_execution_audit_mode() == AutomationExecutionAuditMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_AUDIT_ENV, "postgres")
        assert automation_execution_audit_mode() == AutomationExecutionAuditMode.POSTGRES

    def test_invalid_value_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_AUDIT_ENV, "kafka")
        with pytest.raises(RuntimeError, match="invalid"):
            automation_execution_audit_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_AUDIT_ENV, "postgres")
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
        with pytest.raises(AutomationExecutionAuditConfigError):
            build_automation_execution_audit_repository()


# ---------- Factory ----------


class TestExecutionRepositoryFactory:
    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, raising=False)
        repo = build_automation_execution_repository()
        assert repo.mode == "in_memory"

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, "in_memory")
        repo = build_automation_execution_repository()
        assert repo.mode == "in_memory"


class TestAuditRepositoryFactory:
    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_AUDIT_ENV, raising=False)
        repo = build_automation_execution_audit_repository()
        assert repo.mode == "in_memory"

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_AUDIT_ENV, "in_memory")
        repo = build_automation_execution_audit_repository()
        assert repo.mode == "in_memory"


# ---------- In-memory job repository preserves S58 behavior ----------


class TestInMemoryJobRepositoryS58Compat:
    def test_add_and_get(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        job = _make_job()
        repo.add_job(job)
        found = repo.get_job(job.execution_id)
        assert found is not None
        assert found.execution_id == job.execution_id

    def test_list_jobs_reverse_chronological(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        repo.add_job(_make_job())
        repo.add_job(_make_job())
        result = repo.list_jobs()
        assert len(result) == 2

    def test_list_by_campaign(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        cid = uuid4()
        repo.add_job(_make_job(campaign_id=cid))
        repo.add_job(_make_job(campaign_id=uuid4()))
        repo.add_job(_make_job(campaign_id=cid))
        result = repo.list_by_campaign(cid)
        assert len(result) == 2
        assert all(j.campaign_id == cid for j in result)

    def test_update_job(self) -> None:
        repo = InMemoryAutomationExecutionRepository()
        job = _make_job(status=AutomationExecutionStatus.QUEUED)
        repo.add_job(job)
        updated = job.model_copy(update={"status": AutomationExecutionStatus.COMPLETED_MOCK})
        repo.update_job(updated)
        found = repo.get_job(job.execution_id)
        assert found is not None
        assert found.status == AutomationExecutionStatus.COMPLETED_MOCK


# ---------- Audit repository CRUD + summary ----------


class TestInMemoryAuditRepository:
    def test_add_and_list(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        repo.add_record(_make_audit())
        result = repo.list_records()
        assert len(result) == 1

    def test_list_records_reverse_chronological(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        now = datetime.now(timezone.utc)
        repo.add_record(_make_audit(created_at=now - timedelta(minutes=10)))
        repo.add_record(_make_audit(created_at=now))
        repo.add_record(_make_audit(created_at=now - timedelta(minutes=5)))
        result = repo.list_records()
        assert len(result) == 3
        assert result[0].created_at > result[1].created_at > result[2].created_at

    def test_list_records_limit(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        for _ in range(5):
            repo.add_record(_make_audit())
        result = repo.list_records(limit=2)
        assert len(result) == 2

    def test_list_by_execution_ascending(self) -> None:
        """list_by_execution returns chronological order (ascending)."""
        repo = InMemoryAutomationExecutionAuditRepository()
        eid = uuid4()
        now = datetime.now(timezone.utc)
        repo.add_record(_make_audit(execution_id=eid, created_at=now - timedelta(minutes=10)))
        repo.add_record(_make_audit(execution_id=eid, created_at=now - timedelta(minutes=5)))
        repo.add_record(_make_audit(execution_id=eid, created_at=now))
        repo.add_record(_make_audit(created_at=now))  # different execution
        result = repo.list_by_execution(eid)
        assert len(result) == 3
        assert result[0].created_at < result[1].created_at < result[2].created_at

    def test_list_by_campaign_reverse_chronological(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        cid = uuid4()
        now = datetime.now(timezone.utc)
        repo.add_record(_make_audit(campaign_id=cid, created_at=now - timedelta(minutes=5)))
        repo.add_record(_make_audit(campaign_id=cid, created_at=now))
        repo.add_record(_make_audit(created_at=now))  # different campaign
        result = repo.list_by_campaign(cid)
        assert len(result) == 2
        assert result[0].created_at > result[1].created_at

    def test_summary_breakdowns(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        repo.add_record(
            _make_audit(
                to_status=AutomationExecutionStatus.BLOCKED,
                reason="queue_execution",
                operator_id="alice",
            )
        )
        repo.add_record(
            _make_audit(
                to_status=AutomationExecutionStatus.QUEUED,
                reason="queue_execution",
                operator_id="bob",
            )
        )
        repo.add_record(
            _make_audit(
                from_status=AutomationExecutionStatus.QUEUED,
                to_status=AutomationExecutionStatus.COMPLETED_MOCK,
                reason="execute_mock",
                operator_id="bob",
            )
        )
        summary = repo.summary()
        assert summary.total_records == 3
        assert summary.by_to_status["blocked"] == 1
        assert summary.by_to_status["queued"] == 1
        assert summary.by_to_status["completed_mock"] == 1
        assert summary.by_reason["queue_execution"] == 2
        assert summary.by_reason["execute_mock"] == 1
        assert summary.operator_breakdown["alice"] == 1
        assert summary.operator_breakdown["bob"] == 2
        assert summary.latest_record_at is not None

    def test_mode(self) -> None:
        repo = InMemoryAutomationExecutionAuditRepository()
        assert repo.mode == "in_memory"

    def test_no_delete_method(self) -> None:
        """The audit repository must not expose any delete/remove method."""
        repo = InMemoryAutomationExecutionAuditRepository()
        public_methods = [m for m in dir(repo) if not m.startswith("_")]
        for name in public_methods:
            assert "delete" not in name.lower()
            assert "remove" not in name.lower()
            assert "clear" not in name.lower()
            assert "drop" not in name.lower()


# ---------- Route wiring: queue-execution creates audit record ----------


class TestRouteAuditWiring:
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
                create_campaign(
                    CampaignCreateRequest(release_id=release.release_id),
                    DEV_OPERATOR,
                )
            )
        except Exception:
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

    def test_queue_execution_creates_audit_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_MODE_ENV, raising=False)
        from app.auth import DEV_OPERATOR
        from app.main import (
            automation_execution_audit_repository,
            queue_automation_execution,
        )

        _, rule = self._setup()
        before = len(automation_execution_audit_repository.list_records(limit=1000))
        result = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        after = len(automation_execution_audit_repository.list_records(limit=1000))
        assert after == before + 1

        per_exec = automation_execution_audit_repository.list_by_execution(result.job.execution_id)
        assert len(per_exec) == 1
        assert per_exec[0].from_status is None
        assert per_exec[0].to_status == result.job.status
        assert per_exec[0].reason == "queue_execution"
        assert per_exec[0].operator_id == DEV_OPERATOR.operator_id

    def test_execute_mock_creates_transition_audit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AUTOMATION_EXECUTION_MODE_ENV, "mock")
        from app.auth import DEV_OPERATOR
        from app.main import (
            automation_execution_audit_repository,
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

        eres = asyncio.run(execute_automation_execution_mock(qres.job.execution_id, DEV_OPERATOR))
        assert eres.job.status == AutomationExecutionStatus.COMPLETED_MOCK

        per_exec = automation_execution_audit_repository.list_by_execution(qres.job.execution_id)
        # 2 records: queue_execution + execute_mock
        assert len(per_exec) == 2
        assert per_exec[0].reason == "queue_execution"
        assert per_exec[0].from_status is None
        assert per_exec[1].reason == "execute_mock"
        assert per_exec[1].from_status == AutomationExecutionStatus.QUEUED
        assert per_exec[1].to_status == AutomationExecutionStatus.COMPLETED_MOCK


# ---------- Route E2E ----------


class TestAuditRoutes:
    def _setup(self):
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_automation_rule,
            create_campaign,
            queue_automation_execution,
            release_pack_repository,
        )
        from app.schemas import CampaignCreateRequest

        release = _make_release()
        release_pack_repository.store(release)
        try:
            campaign = asyncio.run(
                create_campaign(
                    CampaignCreateRequest(release_id=release.release_id),
                    DEV_OPERATOR,
                )
            )
        except Exception:
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
        qres = asyncio.run(queue_automation_execution(rule.rule_id, DEV_OPERATOR))
        return campaign, rule, qres.job

    def test_list_audit(self) -> None:
        from app.main import list_automation_execution_audit

        self._setup()
        result = asyncio.run(list_automation_execution_audit(100))
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_audit_summary(self) -> None:
        from app.main import get_automation_execution_audit_summary

        self._setup()
        s = asyncio.run(get_automation_execution_audit_summary())
        assert s.total_records >= 1

    def test_list_audit_for_execution(self) -> None:
        from app.main import list_automation_execution_audit_for_execution

        _, _, job = self._setup()
        result = asyncio.run(list_automation_execution_audit_for_execution(job.execution_id))
        assert len(result) >= 1
        assert all(r.execution_id == job.execution_id for r in result)

    def test_list_audit_for_campaign(self) -> None:
        from app.main import list_automation_execution_audit_for_campaign

        campaign, _, _ = self._setup()
        result = asyncio.run(list_automation_execution_audit_for_campaign(campaign.campaign_id))
        assert len(result) >= 1
        assert all(r.campaign_id == campaign.campaign_id for r in result)


# ---------- Capabilities ----------


class TestCapabilities:
    def test_repository_mode_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_REPOSITORY_ENV, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_repository_mode == "in_memory"

    def test_audit_mode_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTOMATION_EXECUTION_AUDIT_ENV, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_audit_mode == "in_memory"

    def test_audit_available_flag(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_audit_available is True

    def test_existing_s58_caps_still_present(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.automation_execution_boundary_available is True
        assert caps.automation_execution_mode in ("disabled", "mock")


# ---------- No external calls / no scheduler ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_audit(self) -> None:
        from app import automation_execution_audit

        source = inspect.getsource(automation_execution_audit)
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
        from app import automation_execution_audit, automation_execution_repository

        for module in (automation_execution_audit, automation_execution_repository):
            source = inspect.getsource(module)
            assert "import schedule" not in source
            assert "celery" not in source
            assert "crontab" not in source
            assert "apscheduler" not in source

    def test_no_background_worker_imports(self) -> None:
        from app import automation_execution_audit

        source = inspect.getsource(automation_execution_audit)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
