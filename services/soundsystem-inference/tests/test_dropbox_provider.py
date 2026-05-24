"""Tests for S21 — Dropbox Sync Provider Isolation Layer.

Covers:
- Config (DropboxSyncProviderMode, env var parsing, fail-loud)
- Factory (build_dropbox_sync_provider with mock/dropbox modes)
- MockDropboxSyncProvider (execute_sync contract)
- RealDropboxSyncProvider (boundary tests with patched SDK)
- Integration: route uses provider instead of direct mock_execute_sync
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.config import (
    DROPBOX_ACCESS_TOKEN_ENV,
    DROPBOX_SYNC_PROVIDER_ENV,
    DropboxSyncProviderConfigError,
    DropboxSyncProviderMode,
    dropbox_access_token,
    dropbox_sync_provider_mode,
)
from app.providers.dropbox import build_dropbox_sync_provider
from app.providers.dropbox.mock import MockDropboxSyncProvider
from app.schemas import (
    DropboxExportPlan,
    DropboxFolderEntry,
    DropboxSyncJob,
    DropboxSyncStatus,
)


# ---------- Fixtures ----------


def _make_plan(pack_id=None, entries=None) -> DropboxExportPlan:
    return DropboxExportPlan(
        plan_id=uuid4(),
        pack_id=pack_id or uuid4(),
        pack_title="Test Pack",
        target_root="/SNUFFRAGA/Projects/Test-Pack",
        entries=entries
        or [
            DropboxFolderEntry(
                relative_path="manifest.json",
                source_component_type="pack_manifest",
                source_label="Pack manifest: Test Pack",
                size_hint="~3 KB",
                is_directory=False,
            ),
            DropboxFolderEntry(
                relative_path="music_job.json",
                source_component_type="music_job",
                source_label="MusicJob",
                size_hint="~2 KB",
                is_directory=False,
            ),
            DropboxFolderEntry(
                relative_path="stems/stem_pack/",
                source_component_type="artifact_stem_pack",
                source_label="Stems",
                size_hint="~50 MB",
                is_directory=True,
            ),
        ],
        total_files=2,
        total_directories=1,
    )


def _make_job(plan=None, status=DropboxSyncStatus.READY_FOR_SYNC) -> DropboxSyncJob:
    p = plan or _make_plan()
    return DropboxSyncJob(
        sync_id=uuid4(),
        pack_id=p.pack_id,
        plan_id=p.plan_id,
        status=status,
        target_root=p.target_root,
        files_planned=p.total_files,
        files_synced=0,
    )


# ---------- Config Tests ----------


class TestDropboxSyncProviderConfig:
    """Config env var parsing."""

    def test_default_mode_is_mock(self, monkeypatch):
        monkeypatch.delenv(DROPBOX_SYNC_PROVIDER_ENV, raising=False)
        assert dropbox_sync_provider_mode() == DropboxSyncProviderMode.MOCK

    def test_empty_string_is_mock(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "  ")
        assert dropbox_sync_provider_mode() == DropboxSyncProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "mock")
        assert dropbox_sync_provider_mode() == DropboxSyncProviderMode.MOCK

    def test_explicit_dropbox(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "dropbox")
        assert dropbox_sync_provider_mode() == DropboxSyncProviderMode.DROPBOX

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "DROPBOX")
        assert dropbox_sync_provider_mode() == DropboxSyncProviderMode.DROPBOX

    def test_invalid_mode_raises(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "google_drive")
        with pytest.raises(RuntimeError, match="invalid"):
            dropbox_sync_provider_mode()

    def test_access_token_returns_value(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_ACCESS_TOKEN_ENV, "sl.test-token-123")
        assert dropbox_access_token() == "sl.test-token-123"

    def test_access_token_returns_none_when_empty(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_ACCESS_TOKEN_ENV, "  ")
        assert dropbox_access_token() is None

    def test_access_token_returns_none_when_unset(self, monkeypatch):
        monkeypatch.delenv(DROPBOX_ACCESS_TOKEN_ENV, raising=False)
        assert dropbox_access_token() is None


# ---------- Factory Tests ----------


class TestBuildDropboxSyncProvider:
    """Factory function tests."""

    def test_default_returns_mock(self, monkeypatch):
        monkeypatch.delenv(DROPBOX_SYNC_PROVIDER_ENV, raising=False)
        provider = build_dropbox_sync_provider()
        assert provider.name == "mock"
        assert isinstance(provider, MockDropboxSyncProvider)

    def test_dropbox_mode_without_token_fails_loudly(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "dropbox")
        monkeypatch.delenv(DROPBOX_ACCESS_TOKEN_ENV, raising=False)
        with pytest.raises(DropboxSyncProviderConfigError, match="DROPBOX_ACCESS_TOKEN"):
            build_dropbox_sync_provider()

    def test_dropbox_mode_with_empty_token_fails_loudly(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "dropbox")
        monkeypatch.setenv(DROPBOX_ACCESS_TOKEN_ENV, "   ")
        with pytest.raises(DropboxSyncProviderConfigError, match="DROPBOX_ACCESS_TOKEN"):
            build_dropbox_sync_provider()

    def test_dropbox_mode_with_token_succeeds(self, monkeypatch):
        monkeypatch.setenv(DROPBOX_SYNC_PROVIDER_ENV, "dropbox")
        monkeypatch.setenv(DROPBOX_ACCESS_TOKEN_ENV, "sl.valid-token")
        # Patch the Dropbox SDK import so tests don't require it installed
        mock_dropbox_module = MagicMock()
        mock_dropbox_module.Dropbox.return_value = MagicMock()
        with patch.dict("sys.modules", {"dropbox": mock_dropbox_module}):
            provider = build_dropbox_sync_provider()
            assert provider.name == "dropbox"


# ---------- Mock Provider Tests ----------


class TestMockDropboxSyncProvider:
    """MockDropboxSyncProvider execute_sync contract."""

    def test_syncs_ready_job(self):
        provider = MockDropboxSyncProvider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)
        result = asyncio.run(provider.execute_sync(job, plan))
        assert result.status == DropboxSyncStatus.SYNCED
        assert result.files_synced == plan.total_files

    def test_fails_if_not_ready(self):
        provider = MockDropboxSyncProvider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.PLANNED)
        result = asyncio.run(provider.execute_sync(job, plan))
        assert result.status == DropboxSyncStatus.FAILED
        assert "cannot sync from status" in (result.error or "")

    def test_fails_if_already_synced(self):
        provider = MockDropboxSyncProvider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.SYNCED)
        result = asyncio.run(provider.execute_sync(job, plan))
        assert result.status == DropboxSyncStatus.FAILED

    def test_provider_name(self):
        assert MockDropboxSyncProvider().name == "mock"


# ---------- Real Provider Boundary Tests ----------


class TestRealDropboxSyncProvider:
    """RealDropboxSyncProvider boundary — SDK patched, no real API calls."""

    def _build_provider(self):
        """Build real provider with patched Dropbox SDK."""
        mock_dropbox_module = MagicMock()
        mock_client = MagicMock()
        mock_dropbox_module.Dropbox.return_value = mock_client
        mock_dropbox_module.files.WriteMode.overwrite = "overwrite"
        with patch.dict("sys.modules", {"dropbox": mock_dropbox_module}):
            # Force re-import so the patched module is picked up at init
            import importlib

            import app.providers.dropbox.real as real_mod

            importlib.reload(real_mod)
            provider = real_mod.RealDropboxSyncProvider(access_token="sl.test-token")
            return provider, mock_client

    def test_uploads_non_directory_entries(self):
        provider, mock_client = self._build_provider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        result = asyncio.run(provider.execute_sync(job, plan))

        assert result.status == DropboxSyncStatus.SYNCED
        assert result.files_synced == 2  # manifest.json + music_job.json (not the dir)
        # Verify upload was called for each non-directory entry
        assert mock_client.files_upload.call_count == 2

    def test_skips_directory_entries(self):
        provider, mock_client = self._build_provider()
        plan = _make_plan(
            entries=[
                DropboxFolderEntry(
                    relative_path="stems/",
                    source_component_type="artifact_stem_pack",
                    source_label="Stems",
                    size_hint="~50 MB",
                    is_directory=True,
                ),
            ]
        )
        plan = plan.model_copy(update={"total_files": 0, "total_directories": 1})
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        result = asyncio.run(provider.execute_sync(job, plan))

        assert result.status == DropboxSyncStatus.SYNCED
        assert result.files_synced == 0
        mock_client.files_upload.assert_not_called()

    def test_upload_path_is_target_root_plus_relative(self):
        provider, mock_client = self._build_provider()
        plan = _make_plan(
            entries=[
                DropboxFolderEntry(
                    relative_path="lyrics.json",
                    source_component_type="lyrics_version",
                    source_label="Lyrics",
                    size_hint="~4 KB",
                    is_directory=False,
                ),
            ]
        )
        plan = plan.model_copy(update={"total_files": 1, "total_directories": 0})
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        asyncio.run(provider.execute_sync(job, plan))

        call_args = mock_client.files_upload.call_args
        remote_path = call_args[0][1]  # second positional arg
        assert remote_path == "/SNUFFRAGA/Projects/Test-Pack/lyrics.json"

    def test_upload_content_is_json_stub(self):
        provider, mock_client = self._build_provider()
        plan = _make_plan(
            entries=[
                DropboxFolderEntry(
                    relative_path="manifest.json",
                    source_component_type="pack_manifest",
                    source_label="Pack manifest",
                    size_hint="~3 KB",
                    is_directory=False,
                ),
            ]
        )
        plan = plan.model_copy(update={"total_files": 1, "total_directories": 0})
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        asyncio.run(provider.execute_sync(job, plan))

        call_args = mock_client.files_upload.call_args
        content = json.loads(call_args[0][0])
        assert content["source_component_type"] == "pack_manifest"
        assert content["placeholder"] is True

    def test_sdk_error_returns_failed_not_raises(self):
        provider, mock_client = self._build_provider()
        mock_client.files_upload.side_effect = Exception("API rate limit")
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        result = asyncio.run(provider.execute_sync(job, plan))

        assert result.status == DropboxSyncStatus.FAILED
        assert "dropbox_upload_error" in (result.error or "")
        assert "API rate limit" in (result.error or "")

    def test_fails_if_not_ready(self):
        provider, mock_client = self._build_provider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.PLANNED)

        result = asyncio.run(provider.execute_sync(job, plan))

        assert result.status == DropboxSyncStatus.FAILED
        mock_client.files_upload.assert_not_called()

    def test_provider_name(self):
        provider, _ = self._build_provider()
        assert provider.name == "dropbox"

    def test_no_delete_operations(self):
        """Real provider never calls files_delete or any destructive operation."""
        provider, mock_client = self._build_provider()
        plan = _make_plan()
        job = _make_job(plan, status=DropboxSyncStatus.READY_FOR_SYNC)

        asyncio.run(provider.execute_sync(job, plan))

        # Assert no delete-related methods were called
        assert not mock_client.files_delete_v2.called
        assert not mock_client.files_delete.called
        assert not mock_client.files_permanently_delete.called


# ---------- Route Integration Test ----------


class TestDropboxProviderRouteIntegration:
    """Route uses provider.execute_sync instead of direct mock_execute_sync."""

    def test_execute_route_uses_provider(self):
        """Full route test: plan → job → ready → execute via provider."""
        from app.main import (
            create_dropbox_export_plan,
            execute_dropbox_sync,
            list_dropbox_jobs,
            mark_dropbox_job_ready,
            project_library,
        )
        from app.schemas import (
            DropboxExportPlanCreateRequest,
            ExportPack,
            ExportPackComponent,
            ExportPackStatus,
        )

        pack_id = uuid4()
        pack = ExportPack(
            pack_id=pack_id,
            title="Route Test Pack",
            slug="route-test-pack",
            status=ExportPackStatus.COMPLETE,
            music_job_id=str(uuid4()),
            lyrics_version_id=None,
            arrangement_id=None,
            provenance_id=None,
            intent="create_loop",
            bpm=120,
            key_signature="C minor",
            estimated_duration_seconds=180.0,
            total_components=1,
            components=[
                ExportPackComponent(
                    component_type="music_job",
                    component_id=uuid4(),
                    label="MusicJob",
                    path="/jobs/test",
                )
            ],
            operator_id="test-operator",
        )
        project_library.store_pack(pack)

        # Create plan
        req = DropboxExportPlanCreateRequest(pack_id=pack_id)
        from app.auth import DEV_OPERATOR

        plan = asyncio.run(create_dropbox_export_plan(req, DEV_OPERATOR))
        assert plan.pack_id == pack_id

        # Get the auto-created job
        jobs = asyncio.run(list_dropbox_jobs())
        job = next(j for j in jobs if j.pack_id == pack_id)
        assert job.status == DropboxSyncStatus.PLANNED

        # Mark ready
        ready_job = asyncio.run(mark_dropbox_job_ready(job.sync_id, DEV_OPERATOR))
        assert ready_job.status == DropboxSyncStatus.READY_FOR_SYNC

        # Execute sync via provider
        synced_job = asyncio.run(execute_dropbox_sync(job.sync_id, DEV_OPERATOR))
        assert synced_job.status == DropboxSyncStatus.SYNCED
        assert synced_job.files_synced == synced_job.files_planned

    def test_capabilities_shows_provider_mode(self):
        """Capabilities endpoint reports the provider mode."""
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.dropbox_sync_available is True
        assert caps.dropbox_sync_provider_mode == "mock"
