"""Tests for S45 — Campaign OS Foundation.

Covers:
- Campaign creation from release
- Task inference (channels, statuses, dependencies)
- Warning inference (missing cover, audio, compliance, draft status)
- One campaign per release (409 on duplicate)
- Campaign list / get / get-by-release
- Campaign status update (PATCH)
- Archived campaign rejects update (409)
- Campaign summary counts
- Campaign capabilities flag
- Unknown release returns 404
- Unknown campaign returns 404
- Route requires operator identity
- No external API calls (orchestration-only)
- Existing imports unaffected (smoke)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.campaign_builder import (
    build_campaign_from_release,
    infer_campaign_tasks,
    infer_campaign_warnings,
)
from app.campaign_repository import InMemoryCampaignRepository
from app.schemas import (
    CampaignChannel,
    CampaignStatus,
    CampaignTaskStatus,
    CampaignCreateRequest,
    CampaignUpdateRequest,
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
    genre: str | None = "Electronic",
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
        genre=genre,
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


# ---------- Builder tests ----------


class TestCampaignBuilder:
    def test_build_creates_campaign(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        campaign = build_campaign_from_release(release, operator_id="op@test")
        assert campaign.release_id == release.release_id
        assert campaign.status == CampaignStatus.PLANNING
        assert campaign.created_by == "op@test"
        assert len(campaign.tasks) > 0
        assert len(campaign.timeline) == 1
        assert "Campaign created" in campaign.timeline[0].event

    def test_title_includes_release_title(self) -> None:
        release = _make_release(title="MY BANGER")
        campaign = build_campaign_from_release(release)
        assert "MY BANGER" in campaign.title

    def test_default_channels_assigned(self) -> None:
        release = _make_release()
        campaign = build_campaign_from_release(release)
        assert CampaignChannel.SOUNDCLOUD in campaign.channels
        assert CampaignChannel.DISTRIBUTION in campaign.channels
        assert CampaignChannel.MERCH in campaign.channels

    def test_custom_channels(self) -> None:
        release = _make_release()
        campaign = build_campaign_from_release(release, channels=[CampaignChannel.MERCH])
        assert campaign.channels == [CampaignChannel.MERCH]
        # Only merch tasks remain
        for task in campaign.tasks:
            assert task.channel == CampaignChannel.MERCH


# ---------- Task inference ----------


class TestTaskInference:
    def test_generates_distribution_tasks(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        tasks = infer_campaign_tasks(release)
        titles = [t.title for t in tasks]
        assert "Upload cover art" in titles
        assert "Upload audio master" in titles
        assert "Build release export ZIP" in titles

    def test_cover_ready_marks_completed(self) -> None:
        release = _make_release(cover_ready=True)
        tasks = infer_campaign_tasks(release)
        cover_task = next(t for t in tasks if t.title == "Upload cover art")
        assert cover_task.status == CampaignTaskStatus.COMPLETED

    def test_audio_missing_marks_pending(self) -> None:
        release = _make_release(audio_ready=False)
        tasks = infer_campaign_tasks(release)
        audio_task = next(t for t in tasks if t.title == "Upload audio master")
        assert audio_task.status == CampaignTaskStatus.PENDING

    def test_soundcloud_blocked_without_audio(self) -> None:
        release = _make_release(audio_ready=False)
        tasks = infer_campaign_tasks(release)
        sc_publish = next(t for t in tasks if "Publish to SoundCloud" in t.title)
        assert sc_publish.status == CampaignTaskStatus.BLOCKED

    def test_soundcloud_pending_with_audio(self) -> None:
        release = _make_release(audio_ready=True)
        tasks = infer_campaign_tasks(release)
        sc_publish = next(t for t in tasks if "Publish to SoundCloud" in t.title)
        assert sc_publish.status == CampaignTaskStatus.PENDING

    def test_merch_tasks_generated(self) -> None:
        release = _make_release()
        tasks = infer_campaign_tasks(release)
        merch_titles = [t.title for t in tasks if t.channel == CampaignChannel.MERCH]
        assert "Build merch capsule" in merch_titles
        assert "Build Shopify drafts" in merch_titles
        assert "Build Printful syncs" in merch_titles

    def test_tiktok_task_depends_on_merch(self) -> None:
        release = _make_release()
        tasks = infer_campaign_tasks(release)
        tiktok_task = next(t for t in tasks if t.channel == CampaignChannel.TIKTOK)
        assert "Build merch capsule" in tiktok_task.depends_on

    def test_export_zip_has_warnings_when_assets_missing(self) -> None:
        release = _make_release(cover_ready=False, audio_ready=False)
        tasks = infer_campaign_tasks(release)
        zip_task = next(t for t in tasks if "export ZIP" in t.title)
        assert len(zip_task.warnings) > 0

    def test_export_zip_clean_when_assets_ready(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        tasks = infer_campaign_tasks(release)
        zip_task = next(t for t in tasks if "export ZIP" in t.title)
        assert len(zip_task.warnings) == 0


# ---------- Warning inference ----------


class TestWarningInference:
    def test_missing_cover_warning(self) -> None:
        release = _make_release(cover_ready=False)
        warnings = infer_campaign_warnings(release)
        codes = [w.code for w in warnings]
        assert "missing_cover" in codes

    def test_missing_audio_warning(self) -> None:
        release = _make_release(audio_ready=False)
        warnings = infer_campaign_warnings(release)
        codes = [w.code for w in warnings]
        assert "missing_audio" in codes

    def test_compliance_incomplete_warning(self) -> None:
        release = _make_release(compliance_passed=False)
        warnings = infer_campaign_warnings(release)
        codes = [w.code for w in warnings]
        assert "compliance_incomplete" in codes

    def test_draft_status_warning(self) -> None:
        release = _make_release(status=ReleasePackStatus.DRAFT)
        warnings = infer_campaign_warnings(release)
        codes = [w.code for w in warnings]
        assert "release_not_ready" in codes

    def test_no_warnings_when_all_ready(self) -> None:
        release = _make_release(
            cover_ready=True,
            audio_ready=True,
            compliance_passed=True,
            status=ReleasePackStatus.READY,
        )
        warnings = infer_campaign_warnings(release)
        assert len(warnings) == 0


# ---------- Repository ----------


class TestCampaignRepository:
    def test_store_and_get(self) -> None:
        repo = InMemoryCampaignRepository()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        assert repo.get(campaign.campaign_id) is not None

    def test_get_by_release(self) -> None:
        repo = InMemoryCampaignRepository()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get_by_release(release.release_id)
        assert found is not None
        assert found.campaign_id == campaign.campaign_id

    def test_get_by_release_returns_none(self) -> None:
        repo = InMemoryCampaignRepository()
        assert repo.get_by_release(uuid4()) is None

    def test_list_all(self) -> None:
        repo = InMemoryCampaignRepository()
        r1 = _make_release()
        r2 = _make_release(title="SECOND")
        repo.store(build_campaign_from_release(r1))
        repo.store(build_campaign_from_release(r2))
        assert len(repo.list_all()) == 2

    def test_update(self) -> None:
        repo = InMemoryCampaignRepository()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        updated = campaign.model_copy(update={"status": CampaignStatus.ACTIVE})
        repo.update(updated)
        assert repo.get(campaign.campaign_id).status == CampaignStatus.ACTIVE  # type: ignore[union-attr]

    def test_summary_counts(self) -> None:
        repo = InMemoryCampaignRepository()
        r1 = _make_release()
        c1 = build_campaign_from_release(r1)
        repo.store(c1)

        r2 = _make_release(title="SECOND")
        c2 = build_campaign_from_release(r2)
        c2_active = c2.model_copy(update={"status": CampaignStatus.ACTIVE})
        repo.store(c2_active)

        summary = repo.summary()
        assert summary.total_campaigns == 2
        assert summary.planning == 1
        assert summary.active == 1

    def test_mode(self) -> None:
        repo = InMemoryCampaignRepository()
        assert repo.mode == "in_memory"


# ---------- Route tests ----------


class TestCampaignRoutes:
    def _store_release(self) -> ReleasePack:
        from app.main import release_pack_repository

        release = _make_release(cover_ready=True, audio_ready=True)
        release_pack_repository.store(release)
        return release

    def test_create_campaign(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        result = asyncio.run(create_campaign(req, DEV_OPERATOR))
        assert result.release_id == release.release_id
        assert result.status == CampaignStatus.PLANNING

    def test_create_duplicate_409(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        asyncio.run(create_campaign(req, DEV_OPERATOR))
        with pytest.raises(Exception, match="campaign_already_exists"):
            asyncio.run(create_campaign(req, DEV_OPERATOR))

    def test_create_unknown_release_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign

        req = CampaignCreateRequest(release_id=uuid4())
        with pytest.raises(Exception, match="release_not_found"):
            asyncio.run(create_campaign(req, DEV_OPERATOR))

    def test_get_campaign(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, get_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        fetched = asyncio.run(get_campaign(created.campaign_id))
        assert fetched.campaign_id == created.campaign_id

    def test_get_campaign_404(self) -> None:
        from app.main import get_campaign

        with pytest.raises(Exception, match="campaign_not_found"):
            asyncio.run(get_campaign(uuid4()))

    def test_get_by_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, get_campaign_by_release

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        fetched = asyncio.run(get_campaign_by_release(release.release_id))
        assert fetched.campaign_id == created.campaign_id

    def test_get_by_release_404(self) -> None:
        from app.main import get_campaign_by_release

        with pytest.raises(Exception, match="campaign_not_found"):
            asyncio.run(get_campaign_by_release(uuid4()))

    def test_list_campaigns(self) -> None:
        from app.main import list_campaigns

        result = asyncio.run(list_campaigns())
        assert isinstance(result, list)

    def test_campaign_summary(self) -> None:
        from app.main import get_campaign_summary

        result = asyncio.run(get_campaign_summary())
        assert hasattr(result, "total_campaigns")

    def test_update_campaign_status(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, update_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        updated = asyncio.run(
            update_campaign(
                created.campaign_id,
                CampaignUpdateRequest(status=CampaignStatus.READY),
                DEV_OPERATOR,
            )
        )
        assert updated.status == CampaignStatus.READY

    def test_update_archived_campaign_409(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import campaign_repository, create_campaign, update_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        archived = created.model_copy(update={"status": CampaignStatus.ARCHIVED})
        campaign_repository.update(archived)
        with pytest.raises(Exception, match="campaign_archived"):
            asyncio.run(
                update_campaign(
                    created.campaign_id,
                    CampaignUpdateRequest(status=CampaignStatus.ACTIVE),
                    DEV_OPERATOR,
                )
            )

    def test_update_campaign_notes(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, update_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        updated = asyncio.run(
            update_campaign(
                created.campaign_id,
                CampaignUpdateRequest(notes="Updated notes"),
                DEV_OPERATOR,
            )
        )
        assert updated.notes == "Updated notes"

    def test_update_unknown_campaign_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_campaign

        with pytest.raises(Exception, match="campaign_not_found"):
            asyncio.run(
                update_campaign(
                    uuid4(),
                    CampaignUpdateRequest(notes="nope"),
                    DEV_OPERATOR,
                )
            )


# ---------- Capabilities ----------


class TestCampaignCapabilities:
    def test_campaign_os_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_os_available is True


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports(self) -> None:
        import inspect
        from app import campaign_builder

        source = inspect.getsource(campaign_builder)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source


# ---------- Import smoke ----------


class TestImportSmoke:
    def test_existing_imports_still_work(self) -> None:
        from app import campaign_builder as mod

        assert hasattr(mod, "build_campaign_from_release")
        assert hasattr(mod, "infer_campaign_tasks")
        assert hasattr(mod, "infer_campaign_warnings")

    def test_campaign_repository_importable(self) -> None:
        from app import campaign_repository as mod

        assert hasattr(mod, "InMemoryCampaignRepository")
        assert hasattr(mod, "CampaignRepository")
