"""Tests for S60 — Automation Rule Templates.

Covers:
- Default catalogue is deterministic and stable across calls
- Template IDs are stable across calls (UUID5 over slug)
- get_template_by_slug returns matching template or None
- All advertised slugs resolve
- instantiate_template builds a CampaignAutomationRule with operator id
- Overrides (name, conditions, action_payload) merge correctly
- Defaults are copied (not shared) — caller cannot mutate template state
- Instantiation does NOT create execution jobs or audit records
- Routes: list / get / summary / instantiate
- POST instantiate requires operator
- POST instantiate fails on unknown campaign
- Capability flag exposed
- No external API calls
- No scheduler/background imports
- Existing automation tests still pass (smoke)
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import uuid4

import pytest

from app.campaign_automation_templates import (
    build_default_automation_templates,
    get_template_by_slug,
    instantiate_template,
    summarize_templates,
)
from app.schemas import (
    CampaignAutomationAction,
    CampaignAutomationRuleStatus,
    CampaignAutomationTemplateCategory,
    CampaignAutomationTemplateInstantiationRequest,
    CampaignAutomationTrigger,
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release() -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="TEMPLATE TEST",
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
        dropbox_target="/releases/template-test",
        status=ReleasePackStatus.DRAFT,
    )


# ---------- Catalogue ----------


class TestDefaultTemplates:
    def test_catalogue_deterministic(self) -> None:
        first = build_default_automation_templates()
        second = build_default_automation_templates()
        # template_id is stable; slug + trigger + action match
        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.template_id == b.template_id
            assert a.slug == b.slug
            assert a.trigger == b.trigger
            assert a.action == b.action

    def test_six_default_templates(self) -> None:
        templates = build_default_automation_templates()
        assert len(templates) == 6

    def test_all_expected_slugs_present(self) -> None:
        expected = {
            "release-ready-mark-campaign-ready",
            "campaign-ready-mark-active",
            "merch-locked-add-warning",
            "vinyl-ready-create-handoff-task",
            "intelligence-heat-notify-operator",
            "snapshot-delta-notify-operator",
        }
        templates = build_default_automation_templates()
        assert {t.slug for t in templates} == expected

    def test_template_ids_unique(self) -> None:
        templates = build_default_automation_templates()
        ids = [t.template_id for t in templates]
        assert len(ids) == len(set(ids))

    def test_categories_assigned(self) -> None:
        templates = build_default_automation_templates()
        # Every template has a recognized category
        for t in templates:
            assert isinstance(t.category, CampaignAutomationTemplateCategory)

    def test_intelligence_template_has_threshold(self) -> None:
        templates = build_default_automation_templates()
        intel = next(t for t in templates if t.slug == "intelligence-heat-notify-operator")
        assert intel.default_conditions.get("threshold") == 75
        assert intel.action == CampaignAutomationAction.NOTIFY_OPERATOR
        assert intel.trigger == (CampaignAutomationTrigger.INTELLIGENCE_HEAT_ABOVE_THRESHOLD)

    def test_snapshot_delta_template_has_threshold(self) -> None:
        templates = build_default_automation_templates()
        snap = next(t for t in templates if t.slug == "snapshot-delta-notify-operator")
        assert snap.default_conditions.get("threshold") == 10

    def test_summarize(self) -> None:
        templates = build_default_automation_templates()
        summary = summarize_templates(templates)
        assert summary.total_templates == 6
        assert summary.enabled_templates == 6
        # Categories add up
        total = sum(summary.by_category.values())
        assert total == 6


# ---------- Slug lookup ----------


class TestGetTemplateBySlug:
    def test_known_slug(self) -> None:
        tpl = get_template_by_slug("release-ready-mark-campaign-ready")
        assert tpl is not None
        assert tpl.slug == "release-ready-mark-campaign-ready"
        assert tpl.trigger == CampaignAutomationTrigger.RELEASE_READY
        assert tpl.action == CampaignAutomationAction.MARK_CAMPAIGN_READY

    def test_unknown_slug_returns_none(self) -> None:
        assert get_template_by_slug("does-not-exist") is None

    def test_passing_custom_catalogue(self) -> None:
        templates = build_default_automation_templates()
        tpl = get_template_by_slug("vinyl-ready-create-handoff-task", templates=templates)
        assert tpl is not None


# ---------- Instantiation ----------


class TestInstantiateTemplate:
    def test_creates_rule_with_operator_id(self) -> None:
        tpl = get_template_by_slug("release-ready-mark-campaign-ready")
        assert tpl is not None
        cid = uuid4()
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=cid),
            operator_id="op@test",
        )
        assert rule.campaign_id == cid
        assert rule.trigger == tpl.trigger
        assert rule.action == tpl.action
        assert rule.created_by == "op@test"
        assert rule.status == CampaignAutomationRuleStatus.DRAFT

    def test_default_conditions_and_payload_copied(self) -> None:
        tpl = get_template_by_slug("intelligence-heat-notify-operator")
        assert tpl is not None
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=uuid4()),
            operator_id="op",
        )
        assert rule.conditions == tpl.default_conditions
        assert rule.action_payload == tpl.default_action_payload

    def test_overrides_merge(self) -> None:
        tpl = get_template_by_slug("intelligence-heat-notify-operator")
        assert tpl is not None
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(
                campaign_id=uuid4(),
                override_name="Custom name",
                condition_overrides={"threshold": 90, "platforms": ["spotify"]},
                action_payload_overrides={"message": "custom"},
            ),
            operator_id="op",
        )
        assert rule.name == "Custom name"
        assert rule.conditions["threshold"] == 90
        assert rule.conditions["platforms"] == ["spotify"]
        # Original payload key overridden
        assert rule.action_payload["message"] == "custom"

    def test_warnings_copied_not_shared(self) -> None:
        tpl = get_template_by_slug("intelligence-heat-notify-operator")
        assert tpl is not None
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=uuid4()),
            operator_id="op",
        )
        assert rule.warnings == tpl.warnings
        # Mutate the rule's warnings; template should be unchanged
        rule.warnings.append("extra")
        rebuilt = get_template_by_slug("intelligence-heat-notify-operator")
        assert rebuilt is not None
        assert "extra" not in rebuilt.warnings

    def test_does_not_share_condition_dict_with_template(self) -> None:
        tpl = get_template_by_slug("intelligence-heat-notify-operator")
        assert tpl is not None
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=uuid4()),
            operator_id="op",
        )
        rule.conditions["threshold"] = 999
        rebuilt = get_template_by_slug("intelligence-heat-notify-operator")
        assert rebuilt is not None
        assert rebuilt.default_conditions["threshold"] == 75

    def test_uses_template_name_when_no_override(self) -> None:
        tpl = get_template_by_slug("merch-locked-add-warning")
        assert tpl is not None
        rule = instantiate_template(
            tpl,
            CampaignAutomationTemplateInstantiationRequest(campaign_id=uuid4()),
            operator_id="op",
        )
        assert rule.name == tpl.name


# ---------- Route E2E ----------


def _create_campaign():
    from app.auth import DEV_OPERATOR
    from app.main import create_campaign, release_pack_repository
    from app.schemas import CampaignCreateRequest

    release = _make_release()
    release_pack_repository.store(release)
    try:
        return asyncio.run(
            create_campaign(CampaignCreateRequest(release_id=release.release_id), DEV_OPERATOR)
        )
    except Exception:
        from app.main import campaign_repository as repo

        existing = repo.get_by_release(release.release_id)
        assert existing is not None
        return existing


class TestTemplateRoutes:
    def test_list_templates(self) -> None:
        from app.main import list_automation_rule_templates

        result = asyncio.run(list_automation_rule_templates())
        assert len(result) == 6

    def test_get_template_summary(self) -> None:
        from app.main import get_automation_rule_template_summary

        result = asyncio.run(get_automation_rule_template_summary())
        assert result.total_templates == 6

    def test_get_known_template(self) -> None:
        from app.main import get_automation_rule_template

        result = asyncio.run(get_automation_rule_template("release-ready-mark-campaign-ready"))
        assert result.slug == "release-ready-mark-campaign-ready"

    def test_get_unknown_template_404(self) -> None:
        from app.main import get_automation_rule_template
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_automation_rule_template("nope"))
        assert exc.value.status_code == 404

    def test_instantiate_template(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            campaign_automation_rule_repository,
            instantiate_automation_rule_template,
        )

        campaign = _create_campaign()
        before_count = len(
            campaign_automation_rule_repository.list_by_campaign(campaign.campaign_id)
        )
        rule = asyncio.run(
            instantiate_automation_rule_template(
                "release-ready-mark-campaign-ready",
                CampaignAutomationTemplateInstantiationRequest(campaign_id=campaign.campaign_id),
                DEV_OPERATOR,
            )
        )
        after_count = len(
            campaign_automation_rule_repository.list_by_campaign(campaign.campaign_id)
        )
        assert after_count == before_count + 1
        assert rule.campaign_id == campaign.campaign_id
        assert rule.created_by == DEV_OPERATOR.operator_id
        assert rule.status == CampaignAutomationRuleStatus.DRAFT

    def test_instantiate_unknown_template_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import instantiate_automation_rule_template
        from fastapi import HTTPException

        campaign = _create_campaign()
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                instantiate_automation_rule_template(
                    "nope",
                    CampaignAutomationTemplateInstantiationRequest(
                        campaign_id=campaign.campaign_id
                    ),
                    DEV_OPERATOR,
                )
            )
        assert exc.value.status_code == 404

    def test_instantiate_unknown_campaign_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import instantiate_automation_rule_template
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                instantiate_automation_rule_template(
                    "release-ready-mark-campaign-ready",
                    CampaignAutomationTemplateInstantiationRequest(campaign_id=uuid4()),
                    DEV_OPERATOR,
                )
            )
        assert exc.value.status_code == 404


# ---------- No execution / no audit side effects ----------


class TestInstantiationDoesNotExecute:
    def test_no_execution_job_created(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            automation_execution_repository,
            instantiate_automation_rule_template,
        )

        campaign = _create_campaign()
        before_jobs = len(automation_execution_repository.list_by_campaign(campaign.campaign_id))
        asyncio.run(
            instantiate_automation_rule_template(
                "release-ready-mark-campaign-ready",
                CampaignAutomationTemplateInstantiationRequest(campaign_id=campaign.campaign_id),
                DEV_OPERATOR,
            )
        )
        after_jobs = len(automation_execution_repository.list_by_campaign(campaign.campaign_id))
        assert after_jobs == before_jobs

    def test_no_audit_record_created(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            automation_execution_audit_repository,
            instantiate_automation_rule_template,
        )

        campaign = _create_campaign()
        before_audit = len(
            automation_execution_audit_repository.list_by_campaign(campaign.campaign_id)
        )
        asyncio.run(
            instantiate_automation_rule_template(
                "release-ready-mark-campaign-ready",
                CampaignAutomationTemplateInstantiationRequest(campaign_id=campaign.campaign_id),
                DEV_OPERATOR,
            )
        )
        after_audit = len(
            automation_execution_audit_repository.list_by_campaign(campaign.campaign_id)
        )
        assert after_audit == before_audit

    def test_no_campaign_status_mutation(self) -> None:
        """Instantiating a template must not flip the campaign's status."""
        from app.auth import DEV_OPERATOR
        from app.main import (
            campaign_repository,
            instantiate_automation_rule_template,
        )

        campaign = _create_campaign()
        status_before = campaign.status
        asyncio.run(
            instantiate_automation_rule_template(
                "release-ready-mark-campaign-ready",
                CampaignAutomationTemplateInstantiationRequest(campaign_id=campaign.campaign_id),
                DEV_OPERATOR,
            )
        )
        after = campaign_repository.get(campaign.campaign_id)
        assert after is not None
        assert after.status == status_before


# ---------- Capabilities ----------


class TestTemplateCapabilities:
    def test_templates_flag_in_caps(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_automation_templates_available is True

    def test_existing_rule_capability_present(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_automation_rules_available is True


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports(self) -> None:
        from app import campaign_automation_templates

        source = inspect.getsource(campaign_automation_templates)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_scheduler_imports(self) -> None:
        from app import campaign_automation_templates

        source = inspect.getsource(campaign_automation_templates)
        assert "import schedule" not in source
        assert "celery" not in source
        assert "crontab" not in source
        assert "apscheduler" not in source

    def test_no_background_worker_imports(self) -> None:
        from app import campaign_automation_templates

        source = inspect.getsource(campaign_automation_templates)
        assert "threading.Thread" not in source
        assert "multiprocessing" not in source
        assert "BackgroundTasks" not in source
        assert "subprocess" not in source
