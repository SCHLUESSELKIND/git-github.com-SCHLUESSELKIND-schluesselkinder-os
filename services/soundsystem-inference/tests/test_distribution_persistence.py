"""Tests for S38 — Distribution Pack Persistence.

Covers:
- Default repository mode is in_memory
- Postgres mode without DB URL fails loudly
- Factory produces correct repository type
- In-memory repository preserves S37 behaviour
- Backwards-compatible InMemoryDistributionRepository import
- Protocol importable
- Capabilities expose distribution_repository_mode
- Invalid config mode raises RuntimeError
- Routes still work through factory
- Postgres lifecycle if TEST_DATABASE_URL set (skip otherwise)
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest

from app.config import (
    DISTRIBUTION_REPOSITORY_ENV,
    DistributionRepositoryMode,
    distribution_repository_mode,
)
from app.distribution_pack import build_distribution_pack_from_release
from app.distribution_repository import (
    DistributionRepositoryConfigError,
    InMemoryDistributionRepository,
    build_distribution_repository,
)
from app.schemas import (
    ComplianceChecklistItem,
    DistributionPackCreateRequest,
    DistributionPackStatus,
    DistributionPackStatusUpdateRequest,
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
    compliance_passed: bool = False,
) -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="TEST ARTIST",
        status=ReleasePackStatus.DRAFT,
        genre=genre,
        social_copy=SocialCopy(
            soundcloud_description="sc",
            tiktok_caption="tk",
            instagram_caption="ig",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="license_clear", label="Licenses", passed=compliance_passed
            ),
        ],
        compliance_passed=compliance_passed,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio",
                expected_format="wav",
                ready=True,
                artifact_id=uuid4(),
            ),
        ],
    )


# ---------- Config ----------


class TestDistributionConfig:
    def test_default_mode_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(DISTRIBUTION_REPOSITORY_ENV, raising=False)
        assert distribution_repository_mode() == DistributionRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DISTRIBUTION_REPOSITORY_ENV, "in_memory")
        assert distribution_repository_mode() == DistributionRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DISTRIBUTION_REPOSITORY_ENV, "postgres")
        assert distribution_repository_mode() == DistributionRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DISTRIBUTION_REPOSITORY_ENV, "sqlite")
        with pytest.raises(RuntimeError, match="invalid"):
            distribution_repository_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DISTRIBUTION_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(DistributionRepositoryConfigError, match="requires"):
            build_distribution_repository()


# ---------- Factory ----------


class TestDistributionFactory:
    def test_factory_default_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(DISTRIBUTION_REPOSITORY_ENV, raising=False)
        repo = build_distribution_repository()
        assert repo.mode == "in_memory"
        assert isinstance(repo, InMemoryDistributionRepository)

    def test_factory_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DISTRIBUTION_REPOSITORY_ENV, "in_memory")
        repo = build_distribution_repository()
        assert repo.mode == "in_memory"


# ---------- Backward Compatibility ----------


class TestDistributionBackwardCompat:
    def test_in_memory_class_importable(self) -> None:
        """InMemoryDistributionRepository must remain importable (S37 compat)."""
        from app.distribution_repository import InMemoryDistributionRepository as Cls

        repo = Cls()
        assert repo.mode == "in_memory"

    def test_protocol_importable(self) -> None:
        """DistributionRepository protocol must be importable."""
        from app.distribution_repository import DistributionRepository as Proto

        assert Proto is not None


# ---------- In-Memory Repository (S37 behaviour preserved) ----------


class TestInMemoryPreservesS37:
    def test_store_get(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)
        got = repo.get(pack.distribution_id)
        assert got is not None
        assert got.distribution_id == pack.distribution_id

    def test_get_by_release(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)
        got = repo.get_by_release(release.release_id)
        assert got is not None
        assert got.release_id == release.release_id

    def test_list_all(self) -> None:
        repo = InMemoryDistributionRepository()
        for _ in range(3):
            release = _make_release()
            pack = build_distribution_pack_from_release(release)
            repo.store(pack)
        assert len(repo.list_all()) == 3

    def test_update(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)
        updated = pack.model_copy(update={"status": DistributionPackStatus.READY})
        repo.update(updated)
        got = repo.get(pack.distribution_id)
        assert got is not None
        assert got.status == DistributionPackStatus.READY

    def test_summary(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)
        summary = repo.summary()
        assert summary.total_packs == 1
        assert summary.drafts == 1

    def test_get_nonexistent(self) -> None:
        repo = InMemoryDistributionRepository()
        assert repo.get(uuid4()) is None
        assert repo.get_by_release(uuid4()) is None

    def test_mode(self) -> None:
        repo = InMemoryDistributionRepository()
        assert repo.mode == "in_memory"


# ---------- Capabilities ----------


class TestDistributionPersistenceCapabilities:
    def test_capabilities_expose_distribution_repository_mode(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.distribution_repository_mode in ("in_memory", "postgres")

    def test_capabilities_default_in_memory(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.distribution_repository_mode == "in_memory"


# ---------- Routes still work ----------


class TestDistributionRoutesStillWork:
    def test_create_and_fetch(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            get_distribution_pack,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))
        fetched = asyncio.run(get_distribution_pack(pack.distribution_id))
        assert fetched.distribution_id == pack.distribution_id

    def test_update_status(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            release_pack_repository,
            update_distribution_pack_status,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))
        status_req = DistributionPackStatusUpdateRequest(
            status=DistributionPackStatus.READY,
            notes="ready for upload",
        )
        updated = asyncio.run(
            update_distribution_pack_status(pack.distribution_id, status_req, DEV_OPERATOR)
        )
        assert updated.status == DistributionPackStatus.READY

    def test_get_by_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            get_distribution_pack_by_release,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))
        found = asyncio.run(get_distribution_pack_by_release(release.release_id))
        assert found.distribution_id == pack.distribution_id

    def test_summary(self) -> None:
        from app.main import distribution_summary

        summary = asyncio.run(distribution_summary())
        assert summary.total_packs >= 0


# ---------- Postgres (conditional) ----------

_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    _TEST_DB_URL is None,
    reason="TEST_DATABASE_URL not set — Postgres tests skipped",
)
class TestPostgresDistributionRepository:
    """Integration tests that require a running Postgres instance.

    Set TEST_DATABASE_URL to run these. The migration in db/008_distribution.sql
    must be applied before running.
    """

    def _make_repo(self):
        from app.distribution_repository import PostgresDistributionRepository

        return PostgresDistributionRepository(_TEST_DB_URL)

    def test_store_and_get(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            pack = build_distribution_pack_from_release(release, operator_id="test")
            repo.store(pack)
            got = repo.get(pack.distribution_id)
            assert got is not None
            assert got.distribution_id == pack.distribution_id
            assert got.provider == "ditto"
            assert got.status == DistributionPackStatus.DRAFT
            assert got.metadata.artist == "TEST ARTIST"
            assert len(got.readiness_checklist) == len(pack.readiness_checklist)
            assert len(got.store_targets) == len(pack.store_targets)
        finally:
            repo.close()

    def test_get_by_release(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            pack = build_distribution_pack_from_release(release)
            repo.store(pack)
            got = repo.get_by_release(release.release_id)
            assert got is not None
            assert got.release_id == release.release_id
        finally:
            repo.close()

    def test_list_all(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            pack = build_distribution_pack_from_release(release)
            repo.store(pack)
            all_packs = repo.list_all()
            assert len(all_packs) >= 1
        finally:
            repo.close()

    def test_update(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            pack = build_distribution_pack_from_release(release)
            repo.store(pack)
            updated = pack.model_copy(update={"status": DistributionPackStatus.SUBMITTED})
            repo.update(updated)
            got = repo.get(pack.distribution_id)
            assert got is not None
            assert got.status == DistributionPackStatus.SUBMITTED
        finally:
            repo.close()

    def test_summary(self) -> None:
        repo = self._make_repo()
        try:
            summary = repo.summary()
            assert summary.total_packs >= 0
        finally:
            repo.close()

    def test_mode(self) -> None:
        repo = self._make_repo()
        try:
            assert repo.mode == "postgres"
        finally:
            repo.close()

    def test_survives_new_instance(self) -> None:
        """Data stored via one instance is visible from a new one."""
        repo1 = self._make_repo()
        try:
            release = _make_release()
            pack = build_distribution_pack_from_release(release)
            repo1.store(pack)
        finally:
            repo1.close()

        repo2 = self._make_repo()
        try:
            got = repo2.get(pack.distribution_id)
            assert got is not None
            assert got.distribution_id == pack.distribution_id
        finally:
            repo2.close()
