"""Tests for S47 — Vinyl Persistence + Campaign Linking.

Covers:
- Default repository mode is in_memory
- Postgres mode without DB URL fails loudly
- Invalid repository mode fails
- InMemoryVinylRepository preserves S46 behavior
- Backwards-compatible imports
- Capabilities expose vinyl_repository_mode
- Route E2E still works with factory-built repository
- Campaign tasks include vinyl build/check/export/handoff tasks
- Existing vinyl release linked into campaign tasks
- No vendor calls
- Postgres lifecycle (if TEST_DATABASE_URL set)
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest

from app.config import (
    VINYL_REPOSITORY_ENV,
    VinylRepositoryConfigError,
    VinylRepositoryMode,
    vinyl_repository_mode,
)
from app.campaign_builder import (
    build_campaign_from_release,
    infer_campaign_tasks,
)
from app.vinyl_release import build_vinyl_release_from_release
from app.vinyl_repository import (
    InMemoryVinylRepository,
    VinylRepository,
    build_vinyl_repository,
)
from app.schemas import (
    CampaignCreateRequest,
    CampaignTaskStatus,
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    VinylReleaseCreateRequest,
    VinylReleaseStatus,
)


# ---------- Helpers ----------


def _make_release(
    *,
    title: str = "TEST TRACK",
    cover_ready: bool = False,
    audio_ready: bool = False,
    compliance_passed: bool = False,
    duration_seconds: float | None = None,
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
        bpm=128,
        key_signature="Am",
        duration_seconds=duration_seconds,
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
        status=ReleasePackStatus.DRAFT,
    )


# ---------- Config tests ----------


class TestVinylConfig:
    def test_default_mode_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(VINYL_REPOSITORY_ENV, raising=False)
        assert vinyl_repository_mode() == VinylRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(VINYL_REPOSITORY_ENV, "in_memory")
        assert vinyl_repository_mode() == VinylRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(VINYL_REPOSITORY_ENV, "postgres")
        assert vinyl_repository_mode() == VinylRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(VINYL_REPOSITORY_ENV, "redis")
        with pytest.raises(RuntimeError, match="invalid"):
            vinyl_repository_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(VINYL_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(VinylRepositoryConfigError, match="requires"):
            build_vinyl_repository()

    def test_factory_returns_in_memory_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(VINYL_REPOSITORY_ENV, raising=False)
        repo = build_vinyl_repository()
        assert repo.mode == "in_memory"


# ---------- InMemory preserves S46 ----------


class TestInMemoryPreservesS46:
    def test_store_and_get(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        assert repo.get(vinyl.vinyl_id) is not None

    def test_get_by_release(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        assert repo.get_by_release(release.release_id) is not None

    def test_list_all(self) -> None:
        repo = InMemoryVinylRepository()
        for _ in range(3):
            r = _make_release()
            repo.store(build_vinyl_release_from_release(r))
        assert len(repo.list_all()) == 3

    def test_update(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        updated = vinyl.model_copy(update={"status": VinylReleaseStatus.LIVE})
        repo.update(updated)
        assert repo.get(vinyl.vinyl_id).status == VinylReleaseStatus.LIVE  # type: ignore[union-attr]

    def test_summary(self) -> None:
        repo = InMemoryVinylRepository()
        r = _make_release()
        repo.store(build_vinyl_release_from_release(r))
        summary = repo.summary()
        assert summary.total_releases == 1
        assert summary.draft == 1


# ---------- Backwards-compatible imports ----------


class TestBackwardsCompatibleImports:
    def test_vinyl_repository_protocol_importable(self) -> None:

        assert VinylRepository is not None

    def test_in_memory_importable(self) -> None:
        from app.vinyl_repository import InMemoryVinylRepository

        assert InMemoryVinylRepository is not None

    def test_postgres_importable(self) -> None:
        from app.vinyl_repository import PostgresVinylRepository

        assert PostgresVinylRepository is not None

    def test_factory_importable(self) -> None:
        from app.vinyl_repository import build_vinyl_repository

        assert build_vinyl_repository is not None


# ---------- Campaign vinyl integration ----------


class TestCampaignVinylIntegration:
    def test_campaign_tasks_include_vinyl_without_release(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        tasks = infer_campaign_tasks(release, vinyl_release=None)
        titles = [t.title for t in tasks]
        assert "Build vinyl release object" in titles

    def test_vinyl_blocked_without_assets(self) -> None:
        release = _make_release(cover_ready=False, audio_ready=False)
        tasks = infer_campaign_tasks(release, vinyl_release=None)
        vinyl_task = next(t for t in tasks if t.title == "Build vinyl release object")
        assert vinyl_task.status == CampaignTaskStatus.BLOCKED

    def test_vinyl_pending_with_assets(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        tasks = infer_campaign_tasks(release, vinyl_release=None)
        vinyl_task = next(t for t in tasks if t.title == "Build vinyl release object")
        assert vinyl_task.status == CampaignTaskStatus.PENDING

    def test_existing_vinyl_creates_four_tasks(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        tasks = infer_campaign_tasks(release, vinyl_release=vinyl)
        vinyl_titles = [t.title for t in tasks if "vinyl" in t.title.lower()]
        assert "Build vinyl release object" in vinyl_titles
        assert "Check vinyl readiness" in vinyl_titles
        assert "Build vinyl export payload" in vinyl_titles
        assert "Submit manual vinyl handoff" in vinyl_titles

    def test_existing_vinyl_linked_object_id(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        tasks = infer_campaign_tasks(release, vinyl_release=vinyl)
        vinyl_task = next(t for t in tasks if t.title == "Build vinyl release object")
        assert vinyl_task.linked_object_id == vinyl.vinyl_id

    def test_submitted_vinyl_handoff_completed(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        vinyl_submitted = vinyl.model_copy(update={"status": VinylReleaseStatus.SUBMITTED})
        tasks = infer_campaign_tasks(release, vinyl_release=vinyl_submitted)
        handoff = next(t for t in tasks if t.title == "Submit manual vinyl handoff")
        assert handoff.status == CampaignTaskStatus.COMPLETED

    def test_draft_vinyl_handoff_blocked(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        tasks = infer_campaign_tasks(release, vinyl_release=vinyl)
        handoff = next(t for t in tasks if t.title == "Submit manual vinyl handoff")
        assert handoff.status == CampaignTaskStatus.BLOCKED

    def test_campaign_builder_passes_vinyl(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        campaign = build_campaign_from_release(release, vinyl_release=vinyl)
        vinyl_titles = [t.title for t in campaign.tasks if "vinyl" in t.title.lower()]
        assert len(vinyl_titles) == 4

    def test_campaign_builder_no_vinyl(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        campaign = build_campaign_from_release(release)
        vinyl_titles = [t.title for t in campaign.tasks if "vinyl" in t.title.lower()]
        assert len(vinyl_titles) == 1  # Just "Build vinyl release object"


# ---------- Campaign route with vinyl ----------


class TestCampaignRouteWithVinyl:
    def _store_release(self) -> ReleasePack:
        from app.main import release_pack_repository

        release = _make_release(cover_ready=True, audio_ready=True)
        release_pack_repository.store(release)
        return release

    def test_campaign_includes_vinyl_tasks(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign

        release = self._store_release()
        req = CampaignCreateRequest(release_id=release.release_id)
        result = asyncio.run(create_campaign(req, DEV_OPERATOR))
        vinyl_titles = [t.title for t in result.tasks if "vinyl" in t.title.lower()]
        assert len(vinyl_titles) >= 1

    def test_campaign_with_existing_vinyl(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_campaign, create_vinyl_release

        release = self._store_release()

        # Create vinyl first
        vinyl_req = VinylReleaseCreateRequest(release_id=release.release_id)
        asyncio.run(create_vinyl_release(vinyl_req, DEV_OPERATOR))

        # Now create campaign — should pick up vinyl
        campaign_req = CampaignCreateRequest(release_id=release.release_id)
        campaign = asyncio.run(create_campaign(campaign_req, DEV_OPERATOR))
        vinyl_titles = [t.title for t in campaign.tasks if "vinyl" in t.title.lower()]
        # Should have 4 vinyl tasks (build, check, export, handoff)
        assert len(vinyl_titles) == 4


# ---------- Capabilities ----------


class TestVinylCapabilities:
    def test_vinyl_repository_mode_exposed(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.vinyl_repository_mode == "in_memory"


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports_in_repository(self) -> None:
        import inspect
        from app import vinyl_repository

        source = inspect.getsource(vinyl_repository)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source

    def test_no_http_imports_in_builder(self) -> None:
        import inspect
        from app import campaign_builder

        source = inspect.getsource(campaign_builder)
        assert "httpx" not in source
        assert "requests" not in source


# ---------- Postgres lifecycle (conditional) ----------


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL not set — skip Postgres lifecycle tests",
)
class TestPostgresLifecycle:
    """Postgres-backed vinyl repository lifecycle.

    Only runs when TEST_DATABASE_URL is set. Applies migration and
    exercises full CRUD.
    """

    def _apply_migration(self) -> None:
        import psycopg

        with psycopg.connect(TEST_DATABASE_URL) as conn:  # type: ignore[arg-type]
            with conn.cursor() as cur:
                migration = open(
                    "db/009_vinyl.sql",
                ).read()
                cur.execute(migration)
            conn.commit()

    def _cleanup(self) -> None:
        import psycopg

        with psycopg.connect(TEST_DATABASE_URL) as conn:  # type: ignore[arg-type]
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS vinyl_releases CASCADE")
            conn.commit()

    def setup_method(self) -> None:
        self._cleanup()
        self._apply_migration()

    def teardown_method(self) -> None:
        self._cleanup()

    def test_full_lifecycle(self) -> None:
        from app.vinyl_repository import PostgresVinylRepository

        repo = PostgresVinylRepository(TEST_DATABASE_URL)  # type: ignore[arg-type]
        try:
            release = _make_release(cover_ready=True, audio_ready=True)
            vinyl = build_vinyl_release_from_release(release, operator_id="test@op")

            # Store
            repo.store(vinyl)

            # Get
            fetched = repo.get(vinyl.vinyl_id)
            assert fetched is not None
            assert fetched.title == vinyl.title
            assert fetched.artist == vinyl.artist

            # Get by release
            by_release = repo.get_by_release(release.release_id)
            assert by_release is not None
            assert by_release.vinyl_id == vinyl.vinyl_id

            # List
            all_vinyls = repo.list_all()
            assert len(all_vinyls) == 1

            # Update
            updated = vinyl.model_copy(update={"status": VinylReleaseStatus.READY})
            repo.update(updated)
            refetched = repo.get(vinyl.vinyl_id)
            assert refetched is not None
            assert refetched.status == VinylReleaseStatus.READY

            # Summary
            summary = repo.summary()
            assert summary.total_releases == 1
            assert summary.ready == 1

            # Survives new instance
            repo2 = PostgresVinylRepository(TEST_DATABASE_URL)  # type: ignore[arg-type]
            try:
                assert repo2.get(vinyl.vinyl_id) is not None
            finally:
                repo2.close()
        finally:
            repo.close()
