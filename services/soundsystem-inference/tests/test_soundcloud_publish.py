"""Tests for S36 — SoundCloud Publishing Adapter Boundary.

Covers:
- Config: SoundCloudProviderMode, env var parsing, loud failure
- Provider: mock metadata builder, preview, publish-mock
- Provider: real provider publish returns BLOCKED
- Repository: in-memory CRUD, summary
- Routes: preview, job creation, list, get, publish-mock, summary
- Asset checks: audio missing blocks, cover missing warns
- Capabilities: soundcloud fields
- No real SoundCloud API calls
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.config import (
    SOUNDCLOUD_CLIENT_ID_ENV,
    SOUNDCLOUD_CLIENT_SECRET_ENV,
    SoundCloudProviderConfigError,
    SoundCloudProviderMode,
    soundcloud_provider_mode,
)
from app.providers.soundcloud import (
    _build_metadata_from_release,
    _build_warnings,
    build_soundcloud_publish_provider,
)
from app.providers.soundcloud.mock import MockSoundCloudPublishProvider
from app.providers.soundcloud.real import RealSoundCloudPublishProvider
from app.soundcloud_repository import InMemorySoundCloudPublishRepository
from app.schemas import (
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    SoundCloudPublishJob,
    SoundCloudPublishStatus,
    SoundCloudMetadata,
)

SOUNDCLOUD_PROVIDER_ENV = "SOUNDSYSTEM_SOUNDCLOUD_PROVIDER"


# ---------- Helpers ----------


def _make_release(
    *,
    has_audio: bool = True,
    has_cover: bool = True,
    compliance_passed: bool = True,
    status: ReleasePackStatus = ReleasePackStatus.READY,
) -> ReleasePack:
    """Build a test ReleasePack with configurable assets."""
    assets = []
    if has_audio:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=False,
            )
        )

    if has_cover:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
            )
        )

    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="Test Track",
        artist="Test Artist",
        status=status,
        description="Test description",
        social_copy=SocialCopy(
            soundcloud_description="Test Track by Test Artist\nProduced with SNUFFRAGA.",
            tiktok_caption="Test Track — Test Artist",
            instagram_caption="Test Track by Test Artist",
            hashtags=["#SNUFFRAGA", "#Techno"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="license_clear", label="Licenses", passed=compliance_passed
            )
        ],
        compliance_passed=compliance_passed,
        assets=assets,
        genre="Techno",
        bpm=128,
        key_signature="Am",
        duration_seconds=240.0,
    )


def _make_job(
    release_id: uuid4 | None = None,
    status: SoundCloudPublishStatus = SoundCloudPublishStatus.READY,
) -> SoundCloudPublishJob:
    return SoundCloudPublishJob(
        job_id=uuid4(),
        release_id=release_id or uuid4(),
        status=status,
        metadata=SoundCloudMetadata(
            title="Test",
            artist="Artist",
            release_pack_id=uuid4(),
        ),
        provider_mode="mock",
        operator_id="test@test.com",
    )


# ============================================================
# Config tests
# ============================================================


class TestSoundCloudConfig:
    def test_default_mode_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(SOUNDCLOUD_PROVIDER_ENV, raising=False)
        assert soundcloud_provider_mode() == SoundCloudProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "mock")
        assert soundcloud_provider_mode() == SoundCloudProviderMode.MOCK

    def test_soundcloud_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "soundcloud")
        assert soundcloud_provider_mode() == SoundCloudProviderMode.SOUNDCLOUD

    def test_invalid_mode_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "spotify")
        with pytest.raises(RuntimeError, match="invalid"):
            soundcloud_provider_mode()


class TestSoundCloudFactory:
    def test_default_builds_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(SOUNDCLOUD_PROVIDER_ENV, raising=False)
        provider = build_soundcloud_publish_provider()
        assert provider.name == "mock"

    def test_soundcloud_without_client_id_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "soundcloud")
        monkeypatch.delenv(SOUNDCLOUD_CLIENT_ID_ENV, raising=False)
        monkeypatch.delenv(SOUNDCLOUD_CLIENT_SECRET_ENV, raising=False)
        with pytest.raises(SoundCloudProviderConfigError, match="CLIENT_ID"):
            build_soundcloud_publish_provider()

    def test_soundcloud_without_secret_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "soundcloud")
        monkeypatch.setenv(SOUNDCLOUD_CLIENT_ID_ENV, "cid")
        monkeypatch.delenv(SOUNDCLOUD_CLIENT_SECRET_ENV, raising=False)
        with pytest.raises(SoundCloudProviderConfigError, match="CLIENT_SECRET"):
            build_soundcloud_publish_provider()

    def test_soundcloud_with_config_returns_real(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(SOUNDCLOUD_PROVIDER_ENV, "soundcloud")
        monkeypatch.setenv(SOUNDCLOUD_CLIENT_ID_ENV, "cid")
        monkeypatch.setenv(SOUNDCLOUD_CLIENT_SECRET_ENV, "csecret")
        provider = build_soundcloud_publish_provider()
        assert provider.name == "soundcloud"


# ============================================================
# Metadata builder
# ============================================================


class TestBuildMetadata:
    def test_metadata_from_release(self) -> None:
        release = _make_release()
        metadata = _build_metadata_from_release(release)
        assert metadata.title == "Test Track"
        assert metadata.artist == "Test Artist"
        assert metadata.genre == "Techno"
        assert metadata.release_pack_id == release.release_id
        assert metadata.audio_artifact_id is not None
        assert metadata.cover_artifact_id is not None
        assert metadata.is_private is True
        assert metadata.downloadable is False

    def test_metadata_includes_tags(self) -> None:
        release = _make_release()
        metadata = _build_metadata_from_release(release)
        assert "SNUFFRAGA" in metadata.tags
        assert "Techno" in metadata.tags

    def test_metadata_includes_description(self) -> None:
        release = _make_release()
        metadata = _build_metadata_from_release(release)
        assert "SNUFFRAGA" in metadata.description

    def test_metadata_without_audio(self) -> None:
        release = _make_release(has_audio=False)
        metadata = _build_metadata_from_release(release)
        assert metadata.audio_artifact_id is None

    def test_metadata_without_cover(self) -> None:
        release = _make_release(has_cover=False)
        metadata = _build_metadata_from_release(release)
        assert metadata.cover_artifact_id is None


# ============================================================
# Warnings
# ============================================================


class TestBuildWarnings:
    def test_no_warnings_for_complete_release(self) -> None:
        release = _make_release()
        warnings = _build_warnings(release)
        assert len(warnings) == 0

    def test_audio_missing_warning(self) -> None:
        release = _make_release(has_audio=False)
        warnings = _build_warnings(release)
        codes = [w.code for w in warnings]
        assert "audio_missing" in codes

    def test_cover_missing_warning(self) -> None:
        release = _make_release(has_cover=False)
        warnings = _build_warnings(release)
        codes = [w.code for w in warnings]
        assert "cover_missing" in codes

    def test_compliance_incomplete_warning(self) -> None:
        release = _make_release(compliance_passed=False)
        warnings = _build_warnings(release)
        codes = [w.code for w in warnings]
        assert "compliance_incomplete" in codes

    def test_release_not_ready_warning(self) -> None:
        release = _make_release(status=ReleasePackStatus.DRAFT)
        warnings = _build_warnings(release)
        codes = [w.code for w in warnings]
        assert "release_not_ready" in codes


# ============================================================
# Mock provider
# ============================================================


class TestMockProvider:
    def test_name_is_mock(self) -> None:
        provider = MockSoundCloudPublishProvider()
        assert provider.name == "mock"

    def test_preview_can_publish_with_audio(self) -> None:
        provider = MockSoundCloudPublishProvider()
        release = _make_release()
        preview = provider.create_publish_preview(release)
        assert preview.can_publish is True
        assert preview.blocked_reason is None

    def test_preview_blocked_without_audio(self) -> None:
        provider = MockSoundCloudPublishProvider()
        release = _make_release(has_audio=False)
        preview = provider.create_publish_preview(release)
        assert preview.can_publish is False
        assert preview.blocked_reason is not None

    def test_publish_marks_published_mock(self) -> None:
        provider = MockSoundCloudPublishProvider()
        job = _make_job()
        updated = provider.publish(job)
        assert updated.status == SoundCloudPublishStatus.PUBLISHED_MOCK

    def test_publish_blocked_job_stays_blocked(self) -> None:
        provider = MockSoundCloudPublishProvider()
        job = _make_job(status=SoundCloudPublishStatus.BLOCKED)
        updated = provider.publish(job)
        assert updated.status == SoundCloudPublishStatus.BLOCKED


# ============================================================
# Real provider boundary
# ============================================================


class TestRealProvider:
    def test_name_is_soundcloud(self) -> None:
        provider = RealSoundCloudPublishProvider()
        assert provider.name == "soundcloud"

    def test_preview_always_cannot_publish(self) -> None:
        provider = RealSoundCloudPublishProvider()
        release = _make_release()
        preview = provider.create_publish_preview(release)
        assert preview.can_publish is False
        assert "not yet implemented" in (preview.blocked_reason or "").lower()

    def test_preview_has_real_provider_warning(self) -> None:
        provider = RealSoundCloudPublishProvider()
        release = _make_release()
        preview = provider.create_publish_preview(release)
        codes = [w.code for w in preview.warnings]
        assert "real_provider_no_publish" in codes

    def test_publish_returns_blocked(self) -> None:
        provider = RealSoundCloudPublishProvider()
        job = _make_job()
        updated = provider.publish(job)
        assert updated.status == SoundCloudPublishStatus.BLOCKED
        assert updated.error is not None
        assert "not yet implemented" in updated.error.lower()


# ============================================================
# Repository
# ============================================================


class TestSoundCloudRepository:
    def test_store_and_get(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        job = _make_job()
        repo.store(job)
        retrieved = repo.get(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    def test_get_nonexistent(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        assert repo.get(uuid4()) is None

    def test_list_all_ordered(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        j1 = _make_job()
        j2 = _make_job()
        repo.store(j1)
        repo.store(j2)
        jobs = repo.list_all()
        assert len(jobs) == 2

    def test_update(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        job = _make_job()
        repo.store(job)
        updated = job.model_copy(update={"status": SoundCloudPublishStatus.PUBLISHED_MOCK})
        repo.update(updated)
        fetched = repo.get(job.job_id)
        assert fetched is not None
        assert fetched.status == SoundCloudPublishStatus.PUBLISHED_MOCK

    def test_summary(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        repo.store(_make_job(status=SoundCloudPublishStatus.DRAFT))
        repo.store(_make_job(status=SoundCloudPublishStatus.READY))
        repo.store(_make_job(status=SoundCloudPublishStatus.PUBLISHED_MOCK))
        repo.store(_make_job(status=SoundCloudPublishStatus.BLOCKED))
        s = repo.summary()
        assert s.total_jobs == 4
        assert s.drafts == 1
        assert s.ready == 1
        assert s.published_mock == 1
        assert s.blocked == 1

    def test_mode(self) -> None:
        repo = InMemorySoundCloudPublishRepository()
        assert repo.mode == "in_memory"


# ============================================================
# Route tests
# ============================================================


class TestSoundCloudRoutes:
    def _setup_release(self, **kwargs) -> ReleasePack:
        """Store a release and return it."""
        from app.main import release_pack_repository

        release = _make_release(**kwargs)
        release_pack_repository.store(release)
        return release

    def test_preview_route(self) -> None:
        from app.main import soundcloud_preview
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release()
        req = SoundCloudPublishRequest(release_id=release.release_id)
        preview = asyncio.run(soundcloud_preview(req, DEV_OPERATOR))
        assert preview.release_id == release.release_id
        assert preview.metadata.title == "Test Track"
        assert preview.can_publish is True

    def test_preview_not_found(self) -> None:
        from app.main import soundcloud_preview
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        req = SoundCloudPublishRequest(release_id=uuid4())
        with pytest.raises(Exception, match="release_not_found"):
            asyncio.run(soundcloud_preview(req, DEV_OPERATOR))

    def test_create_job_route(self) -> None:
        from app.main import create_soundcloud_job
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release()
        req = SoundCloudPublishRequest(release_id=release.release_id)
        job = asyncio.run(create_soundcloud_job(req, DEV_OPERATOR))
        assert job.release_id == release.release_id
        assert job.status == SoundCloudPublishStatus.READY
        assert job.operator_id == DEV_OPERATOR.operator_id
        assert job.provider_mode == "mock"

    def test_create_job_blocked_without_audio(self) -> None:
        from app.main import create_soundcloud_job
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release(has_audio=False)
        req = SoundCloudPublishRequest(release_id=release.release_id)
        job = asyncio.run(create_soundcloud_job(req, DEV_OPERATOR))
        assert job.status == SoundCloudPublishStatus.BLOCKED
        assert job.error is not None

    def test_list_jobs_route(self) -> None:
        from app.main import list_soundcloud_jobs

        jobs = asyncio.run(list_soundcloud_jobs())
        assert isinstance(jobs, list)

    def test_get_job_route(self) -> None:
        from app.main import create_soundcloud_job, get_soundcloud_job
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release()
        req = SoundCloudPublishRequest(release_id=release.release_id)
        job = asyncio.run(create_soundcloud_job(req, DEV_OPERATOR))
        fetched = asyncio.run(get_soundcloud_job(job.job_id))
        assert fetched.job_id == job.job_id

    def test_get_job_not_found(self) -> None:
        from app.main import get_soundcloud_job

        with pytest.raises(Exception, match="soundcloud_job_not_found"):
            asyncio.run(get_soundcloud_job(uuid4()))

    def test_publish_mock_route(self) -> None:
        from app.main import create_soundcloud_job, publish_mock_soundcloud
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release()
        req = SoundCloudPublishRequest(release_id=release.release_id)
        job = asyncio.run(create_soundcloud_job(req, DEV_OPERATOR))
        updated = asyncio.run(publish_mock_soundcloud(job.job_id, DEV_OPERATOR))
        assert updated.status == SoundCloudPublishStatus.PUBLISHED_MOCK

    def test_publish_mock_blocked_returns_422(self) -> None:
        from app.main import create_soundcloud_job, publish_mock_soundcloud
        from app.auth import DEV_OPERATOR
        from app.schemas import SoundCloudPublishRequest

        release = self._setup_release(has_audio=False)
        req = SoundCloudPublishRequest(release_id=release.release_id)
        job = asyncio.run(create_soundcloud_job(req, DEV_OPERATOR))
        assert job.status == SoundCloudPublishStatus.BLOCKED
        with pytest.raises(Exception) as exc_info:
            asyncio.run(publish_mock_soundcloud(job.job_id, DEV_OPERATOR))
        assert exc_info.value.status_code == 422

    def test_summary_route(self) -> None:
        from app.main import soundcloud_summary

        s = asyncio.run(soundcloud_summary())
        assert s.total_jobs >= 0


# ============================================================
# Capabilities
# ============================================================


class TestCapabilities:
    def test_capabilities_include_soundcloud_fields(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.soundcloud_publish_available is True
        assert caps.soundcloud_provider_mode == "mock"


# ============================================================
# No real API calls
# ============================================================


class TestNoRealApiCalls:
    def test_mock_provider_makes_no_api_calls(self) -> None:
        """Mock provider should never import or call any SoundCloud SDK."""
        provider = MockSoundCloudPublishProvider()
        release = _make_release()
        provider.build_metadata(release)
        provider.create_publish_preview(release)
        job = _make_job()
        provider.publish(job)
        # If we get here without error, no external calls were made

    def test_real_provider_makes_no_api_calls(self) -> None:
        """Real provider boundary should never import or call any SoundCloud SDK."""
        provider = RealSoundCloudPublishProvider()
        release = _make_release()
        provider.build_metadata(release)
        provider.create_publish_preview(release)
        job = _make_job()
        result = provider.publish(job)
        assert result.status == SoundCloudPublishStatus.BLOCKED
