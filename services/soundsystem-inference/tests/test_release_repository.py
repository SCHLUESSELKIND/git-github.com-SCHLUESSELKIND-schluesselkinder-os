"""Tests for S23 — Release Pack Persistence (dual-mode repository).

Covers:
- Config (ReleaseRepositoryMode, env var parsing)
- Factory (build_release_repository with in_memory/postgres modes)
- InMemoryReleaseRepository (Protocol compliance, full CRUD)
- Backwards-compat alias (ReleasePackRepository in release_pack.py)
- Route integration (release_repository_mode in capabilities)
- Full e2e: build → store → update → checklist → ready → retrieve
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.auth import DEV_OPERATOR
from app.config import (
    DATABASE_URL_ENV,
    RELEASE_REPOSITORY_ENV,
    ReleaseRepositoryMode,
    release_repository_mode,
)
from app.release_pack import (
    build_release_pack,
    mark_release_ready,
    update_checklist_item,
)
from app.release_repository import (
    InMemoryReleaseRepository,
    ReleaseRepositoryConfigError,
    build_release_repository,
)
from app.schemas import (
    ExportPack,
    ExportPackComponent,
    ExportPackStatus,
    MusicIntentKind,
    ReleasePackCreateRequest,
    ReleasePackStatus,
)


# ---------- Fixtures ----------


def _make_pack(**overrides) -> ExportPack:
    defaults = dict(
        pack_id=uuid4(),
        title="Persistence Test",
        slug="persistence-test",
        status=ExportPackStatus.COMPLETE,
        music_job_id=uuid4(),
        lyrics_version_id=uuid4(),
        arrangement_id=uuid4(),
        provenance_id=uuid4(),
        intent=MusicIntentKind.BUILD_RIDDIM,
        bpm=140,
        key_signature="D minor",
        estimated_duration_seconds=195.0,
        total_components=1,
        components=[
            ExportPackComponent(
                component_type="music_job",
                component_id=uuid4(),
                label="MusicJob",
                path="/jobs/test",
            ),
        ],
        operator_id="operator-test",
    )
    defaults.update(overrides)
    return ExportPack(**defaults)


def _make_release(pack=None):
    p = pack or _make_pack()
    req = ReleasePackCreateRequest(pack_id=p.pack_id, artist="SNUFFRAGA", genre="Dancehall")
    return build_release_pack(p, req), p


# ---------- Config Tests ----------


class TestReleaseRepositoryConfig:
    def test_default_mode_is_in_memory(self, monkeypatch):
        monkeypatch.delenv(RELEASE_REPOSITORY_ENV, raising=False)
        assert release_repository_mode() == ReleaseRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch):
        monkeypatch.setenv(RELEASE_REPOSITORY_ENV, "in_memory")
        assert release_repository_mode() == ReleaseRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch):
        monkeypatch.setenv(RELEASE_REPOSITORY_ENV, "postgres")
        assert release_repository_mode() == ReleaseRepositoryMode.POSTGRES

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(RELEASE_REPOSITORY_ENV, "POSTGRES")
        assert release_repository_mode() == ReleaseRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch):
        monkeypatch.setenv(RELEASE_REPOSITORY_ENV, "sqlite")
        with pytest.raises(RuntimeError, match="invalid"):
            release_repository_mode()


# ---------- Factory Tests ----------


class TestBuildReleaseRepository:
    def test_default_returns_in_memory(self, monkeypatch):
        monkeypatch.delenv(RELEASE_REPOSITORY_ENV, raising=False)
        repo = build_release_repository()
        assert isinstance(repo, InMemoryReleaseRepository)
        assert repo.mode == "in_memory"

    def test_postgres_without_url_raises(self, monkeypatch):
        monkeypatch.setenv(RELEASE_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
        with pytest.raises(ReleaseRepositoryConfigError, match=DATABASE_URL_ENV):
            build_release_repository()


# ---------- InMemoryReleaseRepository Tests ----------


class TestInMemoryReleaseRepository:
    def test_store_and_get(self):
        repo = InMemoryReleaseRepository()
        release, _ = _make_release()
        repo.store(release)
        assert repo.get(release.release_id) is not None

    def test_get_nonexistent_returns_none(self):
        repo = InMemoryReleaseRepository()
        assert repo.get(uuid4()) is None

    def test_get_by_pack(self):
        repo = InMemoryReleaseRepository()
        release, pack = _make_release()
        repo.store(release)
        by_pack = repo.get_by_pack(pack.pack_id)
        assert by_pack is not None
        assert by_pack.release_id == release.release_id

    def test_get_by_pack_nonexistent(self):
        repo = InMemoryReleaseRepository()
        assert repo.get_by_pack(uuid4()) is None

    def test_list_all_empty(self):
        repo = InMemoryReleaseRepository()
        assert repo.list_all() == []

    def test_list_all_ordered_by_created(self):
        repo = InMemoryReleaseRepository()
        releases = []
        for _ in range(3):
            release, _ = _make_release()
            repo.store(release)
            releases.append(release)
        listed = repo.list_all()
        assert len(listed) == 3
        # Most recent first
        for i in range(len(listed) - 1):
            assert listed[i].created_at >= listed[i + 1].created_at

    def test_update(self):
        repo = InMemoryReleaseRepository()
        release, _ = _make_release()
        repo.store(release)
        updated = release.model_copy(update={"artist": "Updated Artist"})
        repo.update(updated)
        retrieved = repo.get(release.release_id)
        assert retrieved is not None
        assert retrieved.artist == "Updated Artist"

    def test_summary(self):
        repo = InMemoryReleaseRepository()
        release, _ = _make_release()
        repo.store(release)
        s = repo.summary()
        assert s.total_releases == 1
        assert s.drafts == 1
        assert s.ready == 0
        assert s.compliance_passed == 0

    def test_summary_with_ready(self):
        repo = InMemoryReleaseRepository()
        release, _ = _make_release()
        # Pass all compliance items
        for item in release.compliance_checklist:
            release = update_checklist_item(release, item.code, True)
        release = mark_release_ready(release)
        repo.store(release)
        s = repo.summary()
        assert s.total_releases == 1
        assert s.drafts == 0
        assert s.ready == 1
        assert s.compliance_passed == 1

    def test_mode_property(self):
        repo = InMemoryReleaseRepository()
        assert repo.mode == "in_memory"


# ---------- Backwards-compat Alias Tests ----------


class TestBackwardsCompatAlias:
    def test_release_pack_repository_is_in_memory(self):
        from app.release_pack import ReleasePackRepository

        repo = ReleasePackRepository()
        assert isinstance(repo, InMemoryReleaseRepository)

    def test_alias_works_for_store_and_get(self):
        from app.release_pack import ReleasePackRepository

        repo = ReleasePackRepository()
        release, _ = _make_release()
        repo.store(release)
        assert repo.get(release.release_id) is not None


# ---------- Route Integration Tests ----------


class TestReleaseRepositoryRoutes:
    def test_capabilities_shows_repository_mode(self):
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.release_repository_mode == "in_memory"
        assert caps.release_pack_available is True

    def test_release_survives_in_repository(self):
        """Create via route, then retrieve — proves repository wiring works."""
        from app.main import (
            create_release_pack as route_create,
            get_release as route_get,
            project_library,
        )

        pack = _make_pack()
        project_library.store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test", genre="Electronic")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        retrieved = asyncio.run(route_get(release.release_id))
        assert retrieved.release_id == release.release_id
        assert retrieved.artist == "Test"

    def test_checklist_update_persists(self):
        """Update checklist via route, retrieve — proves update wiring works."""
        from app.main import (
            create_release_pack as route_create,
            get_release as route_get,
            project_library,
            update_release_checklist as route_checklist,
        )

        pack = _make_pack()
        project_library.store_pack(pack)
        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test")
        release = asyncio.run(route_create(req, DEV_OPERATOR))

        # Update one item
        asyncio.run(route_checklist(release.release_id, "license_clear", DEV_OPERATOR, True, "OK"))

        # Retrieve and verify persisted
        retrieved = asyncio.run(route_get(release.release_id))
        item = next(i for i in retrieved.compliance_checklist if i.code == "license_clear")
        assert item.passed is True
        assert item.notes == "OK"


# ---------- E2E: Full Persistence Lifecycle ----------


class TestReleaseRepositoryE2E:
    def test_full_lifecycle_through_routes(self):
        """Build → store → checklist pass → ready → retrieve from repo."""
        from app.main import (
            create_release_pack as route_create,
            get_release as route_get,
            get_release_by_pack as route_by_pack,
            mark_release_pack_ready as route_ready,
            project_library,
            release_summary as route_summary,
            update_release_checklist as route_checklist,
        )

        pack = _make_pack()
        project_library.store_pack(pack)

        # Create release
        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="SNUFFRAGA", genre="Dancehall")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        assert release.status == ReleasePackStatus.DRAFT

        # Pass all compliance items
        for item in release.compliance_checklist:
            release = asyncio.run(
                route_checklist(release.release_id, item.code, DEV_OPERATOR, True, "Verified")
            )
        assert release.compliance_passed is True

        # Mark ready
        ready = asyncio.run(route_ready(release.release_id, DEV_OPERATOR))
        assert ready.status == ReleasePackStatus.READY

        # Verify via get
        retrieved = asyncio.run(route_get(ready.release_id))
        assert retrieved.status == ReleasePackStatus.READY
        assert retrieved.compliance_passed is True

        # Verify via by-pack
        by_pack = asyncio.run(route_by_pack(pack.pack_id))
        assert by_pack.release_id == ready.release_id

        # Check summary
        summary = asyncio.run(route_summary())
        assert summary.ready >= 1
        assert summary.compliance_passed >= 1
