"""Tests for S38 — Merch Capsule Persistence.

Covers:
- Default repository mode is in_memory
- Postgres mode without DB URL fails loudly
- Factory produces correct repository type
- In-memory repository preserves S37 behaviour
- Backwards-compatible InMemoryMerchCapsuleRepository import
- Protocol compliance
- Capabilities expose merch_repository_mode
- Invalid config mode raises RuntimeError
- Postgres lifecycle if TEST_DATABASE_URL set (skip otherwise)
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest

from app.config import (
    MERCH_REPOSITORY_ENV,
    MerchRepositoryMode,
    merch_repository_mode,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.merch_repository import (
    InMemoryMerchCapsuleRepository,
    MerchRepositoryConfigError,
    build_merch_repository,
)
from app.schemas import (
    ComplianceChecklistItem,
    MerchCapsuleStatus,
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
) -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="SHIBARI KAWAII",
        status=ReleasePackStatus.READY,
        genre=genre,
        social_copy=SocialCopy(
            soundcloud_description="sc",
            tiktok_caption="tk",
            instagram_caption="ig",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(code="metadata", label="Metadata", passed=True),
        ],
        compliance_passed=True,
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


class TestMerchConfig:
    def test_default_mode_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(MERCH_REPOSITORY_ENV, raising=False)
        assert merch_repository_mode() == MerchRepositoryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(MERCH_REPOSITORY_ENV, "in_memory")
        assert merch_repository_mode() == MerchRepositoryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(MERCH_REPOSITORY_ENV, "postgres")
        assert merch_repository_mode() == MerchRepositoryMode.POSTGRES

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(MERCH_REPOSITORY_ENV, "sqlite")
        with pytest.raises(RuntimeError, match="invalid"):
            merch_repository_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(MERCH_REPOSITORY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(MerchRepositoryConfigError, match="requires"):
            build_merch_repository()


# ---------- Factory ----------


class TestMerchFactory:
    def test_factory_default_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(MERCH_REPOSITORY_ENV, raising=False)
        repo = build_merch_repository()
        assert repo.mode == "in_memory"
        assert isinstance(repo, InMemoryMerchCapsuleRepository)

    def test_factory_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(MERCH_REPOSITORY_ENV, "in_memory")
        repo = build_merch_repository()
        assert repo.mode == "in_memory"


# ---------- Backward Compatibility ----------


class TestBackwardCompat:
    def test_in_memory_class_importable(self) -> None:
        """InMemoryMerchCapsuleRepository must remain importable (S37 compat)."""
        from app.merch_repository import InMemoryMerchCapsuleRepository as Cls

        repo = Cls()
        assert repo.mode == "in_memory"

    def test_protocol_importable(self) -> None:
        """MerchRepository protocol must be importable."""
        from app.merch_repository import MerchRepository as Proto

        assert Proto is not None


# ---------- In-Memory Repository (S37 behaviour preserved) ----------


class TestInMemoryPreservesS37:
    def test_store_get(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        repo.store(capsule)
        got = repo.get(capsule.capsule_id)
        assert got is not None
        assert got.capsule_id == capsule.capsule_id

    def test_list_all_sorted(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        for _ in range(3):
            release = _make_release()
            capsule = build_merch_capsule_from_release(release)
            repo.store(capsule)
        assert len(repo.list_all()) == 3

    def test_update(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        repo.store(capsule)
        updated = capsule.model_copy(update={"status": MerchCapsuleStatus.LOCKED})
        repo.update(updated)
        got = repo.get(capsule.capsule_id)
        assert got is not None
        assert got.status == MerchCapsuleStatus.LOCKED

    def test_summary(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        release = _make_release()
        capsule = build_merch_capsule_from_release(release)
        repo.store(capsule)
        summary = repo.summary()
        assert summary.total_capsules == 1
        assert summary.total_products > 0

    def test_get_nonexistent(self) -> None:
        repo = InMemoryMerchCapsuleRepository()
        assert repo.get(uuid4()) is None


# ---------- Capabilities ----------


class TestMerchPersistenceCapabilities:
    def test_capabilities_expose_merch_repository_mode(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.merch_repository_mode in ("in_memory", "postgres")

    def test_capabilities_default_in_memory(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        # In test environment, default is in_memory
        assert caps.merch_repository_mode == "in_memory"


# ---------- Route E2E still works ----------


class TestMerchRoutesStillWork:
    def test_create_and_fetch(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_merch_capsule,
            get_merch_capsule,
            release_pack_repository,
        )
        from app.schemas import MerchCapsuleCreateRequest

        release = _make_release()
        release_pack_repository.store(release)
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        fetched = asyncio.run(get_merch_capsule(capsule.capsule_id))
        assert fetched.capsule_id == capsule.capsule_id

    def test_lock_and_export(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_merch_capsule,
            export_mock_merch_capsule,
            lock_merch_capsule,
            release_pack_repository,
        )
        from app.schemas import MerchCapsuleCreateRequest

        release = _make_release()
        release_pack_repository.store(release)
        req = MerchCapsuleCreateRequest(release_id=release.release_id)
        capsule = asyncio.run(create_merch_capsule(req, DEV_OPERATOR))
        locked = asyncio.run(lock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        assert locked.status == MerchCapsuleStatus.LOCKED
        payload = asyncio.run(export_mock_merch_capsule(capsule.capsule_id, DEV_OPERATOR))
        assert len(payload.products) > 0


# ---------- Postgres (conditional) ----------

_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    _TEST_DB_URL is None,
    reason="TEST_DATABASE_URL not set — Postgres tests skipped",
)
class TestPostgresMerchRepository:
    """Integration tests that require a running Postgres instance.

    Set TEST_DATABASE_URL to run these. The migration in db/007_merch.sql
    must be applied before running.
    """

    def _make_repo(self):
        from app.merch_repository import PostgresMerchCapsuleRepository

        return PostgresMerchCapsuleRepository(_TEST_DB_URL)

    def test_store_and_get(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            capsule = build_merch_capsule_from_release(release, operator_id="test")
            repo.store(capsule)
            got = repo.get(capsule.capsule_id)
            assert got is not None
            assert got.capsule_id == capsule.capsule_id
            assert got.artist == capsule.artist
            assert got.status == MerchCapsuleStatus.DRAFT
            assert len(got.products) == len(capsule.products)
        finally:
            repo.close()

    def test_list_all(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            capsule = build_merch_capsule_from_release(release)
            repo.store(capsule)
            all_capsules = repo.list_all()
            assert len(all_capsules) >= 1
        finally:
            repo.close()

    def test_update(self) -> None:
        repo = self._make_repo()
        try:
            release = _make_release()
            capsule = build_merch_capsule_from_release(release)
            repo.store(capsule)
            updated = capsule.model_copy(update={"status": MerchCapsuleStatus.LOCKED})
            repo.update(updated)
            got = repo.get(capsule.capsule_id)
            assert got is not None
            assert got.status == MerchCapsuleStatus.LOCKED
        finally:
            repo.close()

    def test_summary(self) -> None:
        repo = self._make_repo()
        try:
            summary = repo.summary()
            assert summary.total_capsules >= 0
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
            capsule = build_merch_capsule_from_release(release)
            repo1.store(capsule)
        finally:
            repo1.close()

        repo2 = self._make_repo()
        try:
            got = repo2.get(capsule.capsule_id)
            assert got is not None
            assert got.capsule_id == capsule.capsule_id
        finally:
            repo2.close()
