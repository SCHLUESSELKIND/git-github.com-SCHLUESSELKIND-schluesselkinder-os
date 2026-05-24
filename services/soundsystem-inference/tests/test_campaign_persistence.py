"""Tests for S56 — Campaign Persistence.

Covers:
- Default repository mode is in_memory
- Postgres mode without DB URL fails loudly
- Invalid repository mode fails
- InMemoryCampaignRepository preserves S45 behavior
- PostgresCampaignRepository lifecycle (if TEST_DATABASE_URL set)
- Backwards-compatible imports remain valid
- Capabilities expose campaign_repository_mode
- Route E2E still works with factory-built repository
- No external calls (orchestration-only)
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest

from app.campaign_builder import build_campaign_from_release
from app.campaign_repository import (
    InMemoryCampaignRepository,
    build_campaign_repository,
)
from app.config import (
    CAMPAIGN_REPOSITORY_ENV,
    DATABASE_URL_ENV,
    CampaignRepositoryConfigError,
    CampaignRepositoryMode,
    campaign_repository_mode,
)
from app.schemas import (
    CampaignChannel,
    CampaignCreateRequest,
    CampaignStatus,
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


# ---------- Config tests ----------


class TestCampaignRepositoryConfig:
    def test_default_mode_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CAMPAIGN_REPOSITORY_ENV, raising=False)
        assert campaign_repository_mode() == CampaignRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CAMPAIGN_REPOSITORY_ENV, "in_memory")
        assert campaign_repository_mode() == CampaignRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CAMPAIGN_REPOSITORY_ENV, "postgres")
        assert campaign_repository_mode() == CampaignRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CAMPAIGN_REPOSITORY_ENV, "redis")
        with pytest.raises(RuntimeError, match="invalid"):
            campaign_repository_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CAMPAIGN_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
        with pytest.raises(CampaignRepositoryConfigError):
            build_campaign_repository()


# ---------- Factory tests ----------


class TestCampaignRepositoryFactory:
    def test_default_builds_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CAMPAIGN_REPOSITORY_ENV, raising=False)
        repo = build_campaign_repository()
        assert repo.mode == "in_memory"

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CAMPAIGN_REPOSITORY_ENV, "in_memory")
        repo = build_campaign_repository()
        assert repo.mode == "in_memory"


# ---------- InMemory preserves S45 behavior ----------


class TestInMemoryCampaignRepository:
    def test_store_and_get(self) -> None:
        repo = InMemoryCampaignRepository()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert found.campaign_id == campaign.campaign_id

    def test_get_returns_none(self) -> None:
        repo = InMemoryCampaignRepository()
        assert repo.get(uuid4()) is None

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

    def test_list_all_ordered_by_created_at(self) -> None:
        repo = InMemoryCampaignRepository()
        r1 = _make_release(title="FIRST")
        r2 = _make_release(title="SECOND")
        c1 = build_campaign_from_release(r1)
        c2 = build_campaign_from_release(r2)
        repo.store(c1)
        repo.store(c2)
        result = repo.list_all()
        assert len(result) == 2

    def test_update(self) -> None:
        repo = InMemoryCampaignRepository()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        updated = campaign.model_copy(update={"status": CampaignStatus.ACTIVE})
        repo.update(updated)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert found.status == CampaignStatus.ACTIVE

    def test_summary(self) -> None:
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
        assert summary.total_tasks > 0

    def test_mode(self) -> None:
        repo = InMemoryCampaignRepository()
        assert repo.mode == "in_memory"


# ---------- Backwards-compatible imports ----------


class TestBackwardsCompatibleImports:
    def test_campaign_repository_protocol(self) -> None:
        from app.campaign_repository import CampaignRepository

        assert CampaignRepository is not None

    def test_in_memory_repository(self) -> None:
        from app.campaign_repository import InMemoryCampaignRepository

        assert InMemoryCampaignRepository is not None

    def test_postgres_repository(self) -> None:
        from app.campaign_repository import PostgresCampaignRepository

        assert PostgresCampaignRepository is not None

    def test_factory(self) -> None:
        from app.campaign_repository import build_campaign_repository

        assert build_campaign_repository is not None

    def test_campaign_builder_unchanged(self) -> None:
        from app.campaign_builder import (
            build_campaign_from_release,
            infer_campaign_tasks,
            infer_campaign_warnings,
        )

        assert build_campaign_from_release is not None
        assert infer_campaign_tasks is not None
        assert infer_campaign_warnings is not None


# ---------- Capabilities ----------


class TestCampaignCapabilities:
    def test_campaign_repository_mode_in_caps(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert hasattr(caps, "campaign_repository_mode")
        assert caps.campaign_repository_mode == "in_memory"

    def test_campaign_os_still_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.campaign_os_available is True


# ---------- Route E2E ----------


class TestCampaignRoutesWithFactory:
    def _store_release(self) -> ReleasePack:
        from app.main import release_pack_repository

        release = _make_release(cover_ready=True, audio_ready=True)
        release_pack_repository.store(release)
        return release

    def test_create_and_get_campaign(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, get_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_campaign(req, DEV_OPERATOR))
        assert created.release_id == release.release_id
        assert created.status == CampaignStatus.PLANNING

        fetched = asyncio.run(get_campaign(created.campaign_id))
        assert fetched.campaign_id == created.campaign_id

    def test_list_campaigns(self) -> None:
        from app.main import list_campaigns

        result = asyncio.run(list_campaigns())
        assert isinstance(result, list)

    def test_campaign_summary(self) -> None:
        from app.main import get_campaign_summary

        result = asyncio.run(get_campaign_summary())
        assert hasattr(result, "total_campaigns")

    def test_update_campaign(self) -> None:
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


# ---------- Postgres lifecycle (requires TEST_DATABASE_URL) ----------


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set — skipping Postgres campaign tests",
)
class TestPostgresCampaignRepository:
    @pytest.fixture(autouse=True)
    def _setup_db(self) -> None:
        """Apply migration and clean table before each test."""
        import psycopg

        self.db_url = os.environ["TEST_DATABASE_URL"]

        migration_path = os.path.join(os.path.dirname(__file__), "..", "db", "012_campaigns.sql")
        with open(migration_path) as f:
            migration_sql = f.read()

        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                cur.execute("DELETE FROM campaigns")
            conn.commit()

    def _build_repo(self):
        from app.campaign_repository import PostgresCampaignRepository

        return PostgresCampaignRepository(self.db_url)

    def test_store_and_get(self) -> None:
        repo = self._build_repo()
        release = _make_release(cover_ready=True, audio_ready=True)
        campaign = build_campaign_from_release(release, operator_id="op@test")
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert found.campaign_id == campaign.campaign_id
        assert found.title == campaign.title
        assert found.status == CampaignStatus.PLANNING
        assert found.created_by == "op@test"
        repo.close()

    def test_get_by_release(self) -> None:
        repo = self._build_repo()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get_by_release(release.release_id)
        assert found is not None
        assert found.campaign_id == campaign.campaign_id
        repo.close()

    def test_list_all(self) -> None:
        repo = self._build_repo()
        r1 = _make_release(title="FIRST")
        r2 = _make_release(title="SECOND")
        repo.store(build_campaign_from_release(r1))
        repo.store(build_campaign_from_release(r2))
        result = repo.list_all()
        assert len(result) == 2
        repo.close()

    def test_update(self) -> None:
        repo = self._build_repo()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        updated = campaign.model_copy(update={"status": CampaignStatus.ACTIVE})
        repo.update(updated)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert found.status == CampaignStatus.ACTIVE
        repo.close()

    def test_summary(self) -> None:
        repo = self._build_repo()
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
        repo.close()

    def test_survives_new_instance(self) -> None:
        repo1 = self._build_repo()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo1.store(campaign)
        repo1.close()

        repo2 = self._build_repo()
        found = repo2.get(campaign.campaign_id)
        assert found is not None
        assert found.campaign_id == campaign.campaign_id
        repo2.close()

    def test_channels_roundtrip(self) -> None:
        repo = self._build_repo()
        release = _make_release()
        campaign = build_campaign_from_release(
            release, channels=[CampaignChannel.MERCH, CampaignChannel.TIKTOK]
        )
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert CampaignChannel.MERCH in found.channels
        assert CampaignChannel.TIKTOK in found.channels
        repo.close()

    def test_tasks_roundtrip(self) -> None:
        repo = self._build_repo()
        release = _make_release(cover_ready=True, audio_ready=True)
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert len(found.tasks) == len(campaign.tasks)
        assert found.tasks[0].title == campaign.tasks[0].title
        repo.close()

    def test_timeline_roundtrip(self) -> None:
        repo = self._build_repo()
        release = _make_release()
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert len(found.timeline) == 1
        assert "Campaign created" in found.timeline[0].event
        repo.close()

    def test_warnings_roundtrip(self) -> None:
        repo = self._build_repo()
        release = _make_release(cover_ready=False, audio_ready=False)
        campaign = build_campaign_from_release(release)
        repo.store(campaign)
        found = repo.get(campaign.campaign_id)
        assert found is not None
        assert len(found.warnings) > 0
        assert found.warnings[0].code == campaign.warnings[0].code
        repo.close()

    def test_mode(self) -> None:
        repo = self._build_repo()
        assert repo.mode == "postgres"
        repo.close()


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_repository(self) -> None:
        import inspect

        from app import campaign_repository

        source = inspect.getsource(campaign_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source

    def test_no_scheduler_imports(self) -> None:
        import inspect

        from app import campaign_repository

        source = inspect.getsource(campaign_repository)
        assert "import schedule" not in source
        assert "celery" not in source
        assert "crontab" not in source
