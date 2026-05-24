"""Tests for S61 — Release-to-Campaign Command Center.

Covers:
- Builder for release without campaign
- Builder for release with existing campaign
- Builder includes merch / distribution / vinyl linked IDs
- Readiness items deterministic and exhaustive
- Recommended templates include core 4 + vinyl when applicable
- Already-attached detection by trigger + action
- Dry-run summary deterministic
- Bootstrap creates campaign once + instantiates recommended templates
- Bootstrap does NOT duplicate campaign on second call
- Bootstrap does NOT re-instantiate templates already attached
- Bootstrap does NOT create execution jobs
- Bootstrap does NOT create audit records
- Bootstrap does NOT mutate merch/distribution/vinyl
- Routes: GET single, GET list, POST bootstrap, unknown 404
- Route POST requires operator
- Capability flag exposed
- No external calls
- No scheduler/background imports
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import uuid4

import pytest

from app.campaign_automation_repository import (
    InMemoryCampaignAutomationRuleRepository,
)
from app.campaign_builder import build_campaign_from_release
from app.campaign_repository import InMemoryCampaignRepository
from app.release_command_center import (
    bootstrap_release_campaign,
    build_release_command_center,
    infer_release_readiness,
    recommend_templates,
)
from app.schemas import (
    CampaignAutomationAction,
    CampaignAutomationDryRunStatus,
    CampaignAutomationRule,
    CampaignAutomationRuleStatus,
    CampaignAutomationTrigger,
    CampaignStatus,
    CommandCenterReadinessStatus,
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    VinylEditionType,
    VinylFormat,
    VinylProviderGroup,
    VinylReleaseObject,
    VinylReleaseStatus,
)


# ---------- Helpers ----------


def _make_release(
    *,
    title: str = "TEST TRACK",
    cover_ready: bool = True,
    audio_ready: bool = True,
    compliance_passed: bool = True,
    status: ReleasePackStatus = ReleasePackStatus.READY,
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
        social_copy=SocialCopy(caption_short="short", caption_long="long", hashtags=["#t"]),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="rights_cleared",
                label="Rights cleared",
                passed=compliance_passed,
            )
        ],
        compliance_passed=compliance_passed,
        assets=assets,
        dropbox_target="/releases/test",
        status=status,
    )


def _make_vinyl(release_id) -> VinylReleaseObject:
    return VinylReleaseObject(
        vinyl_id=uuid4(),
        release_id=release_id,
        title="VINYL TEST",
        artist="Test Artist",
        provider_group=VinylProviderGroup.ELASTIC_STAGE,
        format=VinylFormat.SEVEN_INCH,
        edition_type=VinylEditionType.VINYL_ON_DEMAND,
        status=VinylReleaseStatus.DRAFT,
    )


def _rule(
    *,
    campaign_id,
    trigger: CampaignAutomationTrigger,
    action: CampaignAutomationAction,
    status: CampaignAutomationRuleStatus = CampaignAutomationRuleStatus.ACTIVE,
) -> CampaignAutomationRule:
    return CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=campaign_id,
        name="r",
        status=status,
        trigger=trigger,
        action=action,
    )


def _operator():
    from app.auth import DEV_OPERATOR

    return DEV_OPERATOR


# ---------- Readiness ----------


class TestInferReleaseReadiness:
    def test_full_ready_release(self) -> None:
        rel = _make_release()
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        # release_pack, assets, campaign, distribution, merch, vinyl
        codes = {i.code for i in items}
        assert codes == {"release_pack", "assets", "campaign", "distribution", "merch", "vinyl"}

    def test_release_status_ready_is_ready(self) -> None:
        rel = _make_release(status=ReleasePackStatus.READY)
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        rp = next(i for i in items if i.code == "release_pack")
        assert rp.status == CommandCenterReadinessStatus.READY

    def test_release_compliance_failed_is_blocked(self) -> None:
        rel = _make_release(compliance_passed=False, status=ReleasePackStatus.DRAFT)
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        rp = next(i for i in items if i.code == "release_pack")
        assert rp.status == CommandCenterReadinessStatus.BLOCKED

    def test_missing_assets_blocked(self) -> None:
        rel = _make_release(cover_ready=False, audio_ready=False)
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        assets = next(i for i in items if i.code == "assets")
        assert assets.status == CommandCenterReadinessStatus.BLOCKED

    def test_partial_assets_warning(self) -> None:
        rel = _make_release(cover_ready=True, audio_ready=False)
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        assets = next(i for i in items if i.code == "assets")
        assert assets.status == CommandCenterReadinessStatus.WARNING

    def test_campaign_missing_when_absent(self) -> None:
        rel = _make_release()
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        camp = next(i for i in items if i.code == "campaign")
        assert camp.status == CommandCenterReadinessStatus.MISSING

    def test_campaign_ready_when_present(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        items = infer_release_readiness(
            release=rel,
            campaign=campaign,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        camp = next(i for i in items if i.code == "campaign")
        assert camp.status == CommandCenterReadinessStatus.READY
        assert camp.linked_object_id == campaign.campaign_id

    def test_vinyl_ready_when_present(self) -> None:
        rel = _make_release()
        vinyl = _make_vinyl(rel.release_id)
        items = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=vinyl,
        )
        v = next(i for i in items if i.code == "vinyl")
        assert v.status == CommandCenterReadinessStatus.READY

    def test_deterministic_across_calls(self) -> None:
        rel = _make_release()
        a = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        b = infer_release_readiness(
            release=rel,
            campaign=None,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        assert [i.code for i in a] == [i.code for i in b]
        assert [i.status for i in a] == [i.status for i in b]


# ---------- Recommendations ----------


class TestRecommendTemplates:
    def test_core_recommendations(self) -> None:
        recs = recommend_templates(
            campaign=None,
            existing_rules=[],
            vinyl_release=None,
        )
        slugs = {r.template_slug for r in recs}
        assert "release-ready-mark-campaign-ready" in slugs
        assert "campaign-ready-mark-active" in slugs
        assert "intelligence-heat-notify-operator" in slugs
        # No vinyl
        assert "vinyl-ready-create-handoff-task" not in slugs

    def test_vinyl_recommendation_when_present(self) -> None:
        rel = _make_release()
        vinyl = _make_vinyl(rel.release_id)
        recs = recommend_templates(
            campaign=None,
            existing_rules=[],
            vinyl_release=vinyl,
        )
        slugs = {r.template_slug for r in recs}
        assert "vinyl-ready-create-handoff-task" in slugs

    def test_already_attached_detection(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        existing = [
            _rule(
                campaign_id=campaign.campaign_id,
                trigger=CampaignAutomationTrigger.RELEASE_READY,
                action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            )
        ]
        recs = recommend_templates(
            campaign=campaign,
            existing_rules=existing,
            vinyl_release=None,
        )
        ready = next(r for r in recs if r.template_slug == "release-ready-mark-campaign-ready")
        assert ready.already_attached is True
        # Other recs are not attached
        active = next(r for r in recs if r.template_slug == "campaign-ready-mark-active")
        assert active.already_attached is False


# ---------- Builder ----------


class TestBuildReleaseCommandCenter:
    def test_release_without_campaign(self) -> None:
        rel = _make_release()
        cc = build_release_command_center(
            release=rel,
            campaign=None,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        assert cc.release_id == rel.release_id
        assert cc.release_title == rel.title
        assert cc.campaign_id is None
        assert cc.campaign_status is None
        assert cc.automation_rule_count == 0
        assert cc.dry_run_summary[CampaignAutomationDryRunStatus.WOULD_RUN.value] == 0
        assert "Campaign not yet bootstrapped." in cc.warnings

    def test_release_with_campaign(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        cc = build_release_command_center(
            release=rel,
            campaign=campaign,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        assert cc.campaign_id == campaign.campaign_id
        assert cc.campaign_status == CampaignStatus.PLANNING
        assert "Campaign not yet bootstrapped." not in cc.warnings

    def test_dry_run_summary_counts(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        existing = [
            _rule(
                campaign_id=campaign.campaign_id,
                trigger=CampaignAutomationTrigger.RELEASE_READY,
                action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
            ),
            _rule(
                campaign_id=campaign.campaign_id,
                trigger=CampaignAutomationTrigger.CAMPAIGN_READY,
                action=CampaignAutomationAction.MARK_CAMPAIGN_ACTIVE,
            ),
        ]
        cc = build_release_command_center(
            release=rel,
            campaign=campaign,
            existing_rules=existing,
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
        )
        # release_ready matches PLANNING, campaign_ready doesn't.
        assert cc.dry_run_summary[CampaignAutomationDryRunStatus.WOULD_RUN.value] == 1
        assert cc.dry_run_summary[CampaignAutomationDryRunStatus.NO_MATCH.value] == 1
        assert cc.automation_rule_count == 2


# ---------- Bootstrap ----------


class TestBootstrap:
    def test_bootstrap_creates_campaign_once(self) -> None:
        rel = _make_release()
        campaign_repo = InMemoryCampaignRepository()
        rule_repo = InMemoryCampaignAutomationRuleRepository()

        result = bootstrap_release_campaign(
            release=rel,
            campaign=None,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        assert result.created_campaign is True
        assert result.command_center.campaign_id is not None
        stored = campaign_repo.get_by_release(rel.release_id)
        assert stored is not None

    def test_bootstrap_does_not_duplicate_campaign(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        campaign_repo = InMemoryCampaignRepository()
        campaign_repo.store(campaign)
        rule_repo = InMemoryCampaignAutomationRuleRepository()

        result = bootstrap_release_campaign(
            release=rel,
            campaign=campaign,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        assert result.created_campaign is False
        assert result.command_center.campaign_id == campaign.campaign_id

    def test_bootstrap_instantiates_templates(self) -> None:
        rel = _make_release()
        campaign_repo = InMemoryCampaignRepository()
        rule_repo = InMemoryCampaignAutomationRuleRepository()

        result = bootstrap_release_campaign(
            release=rel,
            campaign=None,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        # 3 recs without vinyl: release-ready, campaign-ready, intelligence-heat
        assert len(result.instantiated_rule_ids) == 3
        assert result.command_center.automation_rule_count == 3

    def test_bootstrap_with_vinyl_adds_vinyl_template(self) -> None:
        rel = _make_release()
        vinyl = _make_vinyl(rel.release_id)
        campaign_repo = InMemoryCampaignRepository()
        rule_repo = InMemoryCampaignAutomationRuleRepository()

        result = bootstrap_release_campaign(
            release=rel,
            campaign=None,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=vinyl,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        # 4 recs with vinyl
        assert len(result.instantiated_rule_ids) == 4
        triggers = {
            r.trigger
            for r in rule_repo.list_by_campaign(
                result.command_center.campaign_id  # type: ignore[arg-type]
            )
        }
        assert CampaignAutomationTrigger.VINYL_READY in triggers

    def test_bootstrap_skips_already_attached(self) -> None:
        rel = _make_release()
        campaign = build_campaign_from_release(rel)
        existing = _rule(
            campaign_id=campaign.campaign_id,
            trigger=CampaignAutomationTrigger.RELEASE_READY,
            action=CampaignAutomationAction.MARK_CAMPAIGN_READY,
        )
        campaign_repo = InMemoryCampaignRepository()
        campaign_repo.store(campaign)
        rule_repo = InMemoryCampaignAutomationRuleRepository()
        rule_repo.add_rule(existing)

        result = bootstrap_release_campaign(
            release=rel,
            campaign=campaign,
            existing_rules=[existing],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        # Only 2 new (campaign-ready + intelligence-heat), not 3
        assert len(result.instantiated_rule_ids) == 2

    def test_bootstrap_records_operator_id(self) -> None:
        rel = _make_release()
        campaign_repo = InMemoryCampaignRepository()
        rule_repo = InMemoryCampaignAutomationRuleRepository()

        result = bootstrap_release_campaign(
            release=rel,
            campaign=None,
            existing_rules=[],
            merch_capsules=[],
            distribution_pack=None,
            vinyl_release=None,
            campaign_repo=campaign_repo,
            rule_repo=rule_repo,
            operator=_operator(),
        )
        op = _operator()
        for rid in result.instantiated_rule_ids:
            rule = rule_repo.get_rule(rid)
            assert rule is not None
            assert rule.created_by == op.operator_id


# ---------- Bootstrap side-effect verification ----------


class TestBootstrapHasNoExecutionSideEffects:
    def _setup_via_main_singletons(self):
        from app.auth import DEV_OPERATOR
        from app.main import (
            release_pack_repository,
        )

        rel = _make_release()
        release_pack_repository.store(rel)
        return rel, DEV_OPERATOR

    def test_no_execution_jobs(self) -> None:
        from app.main import (
            automation_execution_repository,
            bootstrap_command_center_release,
        )

        rel, op = self._setup_via_main_singletons()
        before = len(automation_execution_repository.list_jobs())
        asyncio.run(bootstrap_command_center_release(rel.release_id, op))
        after = len(automation_execution_repository.list_jobs())
        assert after == before

    def test_no_audit_records(self) -> None:
        from app.main import (
            automation_execution_audit_repository,
            bootstrap_command_center_release,
        )

        rel, op = self._setup_via_main_singletons()
        before = len(automation_execution_audit_repository.list_records(limit=10000))
        asyncio.run(bootstrap_command_center_release(rel.release_id, op))
        after = len(automation_execution_audit_repository.list_records(limit=10000))
        assert after == before

    def test_no_merch_mutation(self) -> None:
        from app.main import (
            bootstrap_command_center_release,
            merch_capsule_repository,
        )

        rel, op = self._setup_via_main_singletons()
        before_summary = merch_capsule_repository.summary().model_dump()
        asyncio.run(bootstrap_command_center_release(rel.release_id, op))
        after_summary = merch_capsule_repository.summary().model_dump()
        assert after_summary == before_summary


# ---------- Routes ----------


class TestCommandCenterRoutes:
    def _store_release(self):
        from app.main import release_pack_repository

        rel = _make_release()
        release_pack_repository.store(rel)
        return rel

    def test_get_unknown_release_404(self) -> None:
        from app.main import get_command_center_release
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_command_center_release(uuid4()))
        assert exc.value.status_code == 404

    def test_get_release_command_center(self) -> None:
        from app.main import get_command_center_release

        rel = self._store_release()
        cc = asyncio.run(get_command_center_release(rel.release_id))
        assert cc.release_id == rel.release_id
        assert isinstance(cc.readiness_items, list)
        assert len(cc.readiness_items) >= 4

    def test_list_releases(self) -> None:
        from app.main import list_command_center_releases

        self._store_release()
        result = asyncio.run(list_command_center_releases())
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_bootstrap_route(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import bootstrap_command_center_release

        rel = self._store_release()
        result = asyncio.run(bootstrap_command_center_release(rel.release_id, DEV_OPERATOR))
        # Result type carries campaign_id post-bootstrap
        assert result.command_center.campaign_id is not None

    def test_bootstrap_unknown_release_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import bootstrap_command_center_release
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(bootstrap_command_center_release(uuid4(), DEV_OPERATOR))
        assert exc.value.status_code == 404


# ---------- Capabilities ----------


class TestCapability:
    def test_command_center_flag_in_caps(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.release_command_center_available is True


# ---------- No external calls / no scheduler ----------


class TestNoExternalCalls:
    def test_no_http_imports(self) -> None:
        from app import release_command_center

        source = inspect.getsource(release_command_center)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_scheduler_imports(self) -> None:
        from app import release_command_center

        source = inspect.getsource(release_command_center)
        assert "import schedule" not in source
        assert "celery" not in source
        assert "crontab" not in source
        assert "apscheduler" not in source

    def test_no_background_worker_imports(self) -> None:
        from app import release_command_center

        source = inspect.getsource(release_command_center)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
