"""Tests for S35 — S3/R2 Artifact Storage Adapter.

Covers:
- Config: s3_region, s3_force_path_style env var parsing
- Factory: build_artifact_storage returns S3 adapter when configured
- S3ArtifactStorage: create_record, store_bytes, get_record, download links
- Safety: no delete_object calls, path traversal blocked, keys are safe
- Local mode: boto3 is never imported in default/local mode
- Missing config: loud failure when S3 is selected without required vars
- Presigned URL vs public base URL behavior
- Checksum/size computed before upload
- Integration with release_export._get_artifact_bytes

All tests mock boto3 — no real S3/R2/MinIO required.
"""

from __future__ import annotations

import hashlib
import sys
import types
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.artifact_registry import InMemoryArtifactRegistry
from app.config import (
    ARTIFACT_STORAGE_ENV,
    S3_ACCESS_KEY_ID_ENV,
    S3_BUCKET_ENV,
    S3_ENDPOINT_URL_ENV,
    S3_FORCE_PATH_STYLE_ENV,
    S3_REGION_ENV,
    S3_SECRET_ACCESS_KEY_ENV,
    ArtifactStorageConfigError,
    s3_force_path_style,
    s3_region,
)
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactStatus,
)


# ---------- Helpers ----------


def _s3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set all required S3 env vars."""
    monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
    monkeypatch.setenv(S3_ENDPOINT_URL_ENV, "https://s3.example.com")
    monkeypatch.setenv(S3_ACCESS_KEY_ID_ENV, "test-key-id")
    monkeypatch.setenv(S3_SECRET_ACCESS_KEY_ENV, "test-secret-key")
    monkeypatch.setenv(S3_BUCKET_ENV, "test-bucket")


def _make_mock_boto3() -> tuple[MagicMock, MagicMock]:
    """Create a mock boto3 module and client.

    Returns (mock_boto3_module, mock_s3_client).
    """
    mock_client = MagicMock()
    mock_client.put_object = MagicMock(return_value={})
    mock_client.get_object = MagicMock(
        return_value={"Body": MagicMock(read=MagicMock(return_value=b"mock-content"))}
    )
    mock_client.generate_presigned_url = MagicMock(
        return_value="https://s3.example.com/presigned/test-key"
    )

    mock_boto3 = MagicMock()
    mock_boto3.client = MagicMock(return_value=mock_client)

    mock_botocore_config = MagicMock()
    mock_botocore_config.Config = MagicMock(return_value=MagicMock())

    return mock_boto3, mock_client


def _build_s3_storage(
    *,
    public_base_url: str | None = None,
    registry: InMemoryArtifactRegistry | None = None,
) -> tuple:
    """Build an S3ArtifactStorage with mocked boto3.

    Returns (storage, mock_client, registry).
    """
    mock_boto3, mock_client = _make_mock_boto3()
    reg = registry or InMemoryArtifactRegistry()

    # Patch boto3 and botocore.config in the s3 module's import namespace
    mock_botocore = types.ModuleType("botocore")
    mock_botocore.config = types.ModuleType("botocore.config")
    mock_botocore.config.Config = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]

    with (
        patch.dict(
            sys.modules,
            {
                "boto3": mock_boto3,
                "botocore": mock_botocore,
                "botocore.config": mock_botocore.config,
            },
        ),
    ):
        from app.artifact_storage_s3 import S3ArtifactStorage

        storage = S3ArtifactStorage(
            endpoint_url="https://s3.example.com",
            region="auto",
            access_key_id="test-key-id",
            secret_access_key="test-secret-key",
            bucket="test-bucket",
            force_path_style=True,
            public_base_url=public_base_url,
            registry=reg,
        )

    return storage, mock_client, reg


def _make_create_request(
    kind: ArtifactKind = ArtifactKind.OTHER,
    logical_path: str = "test/artifact.bin",
    content_type: str = "application/octet-stream",
) -> ArtifactCreateRequest:
    return ArtifactCreateRequest(
        kind=kind,
        logical_path=logical_path,
        content_type=content_type,
    )


# ============================================================
# Config tests
# ============================================================


class TestS3Config:
    def test_s3_region_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(S3_REGION_ENV, raising=False)
        assert s3_region() == "auto"

    def test_s3_region_explicit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(S3_REGION_ENV, "us-east-1")
        assert s3_region() == "us-east-1"

    def test_s3_force_path_style_default_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(S3_FORCE_PATH_STYLE_ENV, raising=False)
        assert s3_force_path_style() is True

    def test_s3_force_path_style_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(S3_FORCE_PATH_STYLE_ENV, "false")
        assert s3_force_path_style() is False

    def test_s3_force_path_style_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(S3_FORCE_PATH_STYLE_ENV, "0")
        assert s3_force_path_style() is False

    def test_s3_force_path_style_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(S3_FORCE_PATH_STYLE_ENV, "no")
        assert s3_force_path_style() is False

    def test_s3_force_path_style_true_explicit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(S3_FORCE_PATH_STYLE_ENV, "true")
        assert s3_force_path_style() is True


# ============================================================
# Factory tests — missing config
# ============================================================


class TestFactoryMissingConfig:
    def test_s3_without_endpoint_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _s3_env(monkeypatch)
        monkeypatch.delenv(S3_ENDPOINT_URL_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        with pytest.raises(ArtifactStorageConfigError, match="S3_ENDPOINT_URL"):
            build_artifact_storage()

    def test_s3_without_access_key_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _s3_env(monkeypatch)
        monkeypatch.delenv(S3_ACCESS_KEY_ID_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        with pytest.raises(ArtifactStorageConfigError, match="S3_ACCESS_KEY_ID"):
            build_artifact_storage()

    def test_s3_without_secret_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _s3_env(monkeypatch)
        monkeypatch.delenv(S3_SECRET_ACCESS_KEY_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        with pytest.raises(ArtifactStorageConfigError, match="S3_SECRET_ACCESS_KEY"):
            build_artifact_storage()

    def test_s3_without_bucket_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _s3_env(monkeypatch)
        monkeypatch.delenv(S3_BUCKET_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        with pytest.raises(ArtifactStorageConfigError, match="S3_BUCKET"):
            build_artifact_storage()

    def test_s3_reports_all_missing_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
        monkeypatch.delenv(S3_ENDPOINT_URL_ENV, raising=False)
        monkeypatch.delenv(S3_ACCESS_KEY_ID_ENV, raising=False)
        monkeypatch.delenv(S3_SECRET_ACCESS_KEY_ENV, raising=False)
        monkeypatch.delenv(S3_BUCKET_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        with pytest.raises(ArtifactStorageConfigError, match="S3") as exc_info:
            build_artifact_storage()
        msg = str(exc_info.value)
        assert "ENDPOINT_URL" in msg
        assert "ACCESS_KEY_ID" in msg
        assert "SECRET_ACCESS_KEY" in msg
        assert "BUCKET" in msg


# ============================================================
# Local mode does not import boto3
# ============================================================


class TestLocalModeNoBoto3:
    def test_local_mode_does_not_import_boto3(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default local mode must never import boto3."""
        monkeypatch.delenv(ARTIFACT_STORAGE_ENV, raising=False)
        # Remove boto3 from sys.modules to detect fresh imports
        saved = sys.modules.pop("boto3", None)
        saved_bc = sys.modules.pop("botocore", None)
        saved_bc_config = sys.modules.pop("botocore.config", None)
        try:
            from app.artifact_storage import build_artifact_storage

            storage = build_artifact_storage()
            assert storage.mode == "local"
            # boto3 should NOT have been imported
            assert "boto3" not in sys.modules or sys.modules["boto3"] is saved
        finally:
            # Restore
            if saved is not None:
                sys.modules["boto3"] = saved
            if saved_bc is not None:
                sys.modules["botocore"] = saved_bc
            if saved_bc_config is not None:
                sys.modules["botocore.config"] = saved_bc_config


# ============================================================
# S3ArtifactStorage with mocked boto3
# ============================================================


class TestS3ArtifactStorageBasic:
    def test_mode_is_s3(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.mode == "s3"

    def test_bucket_property(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.bucket == "test-bucket"

    def test_create_record(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        assert record.status == ArtifactStatus.PLANNED
        assert record.storage_mode == "s3"
        assert record.storage_key is not None
        assert ".." not in record.storage_key

    def test_create_record_preserves_operator(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(), operator_id="op@test.com")
        assert record.operator_id == "op@test.com"


class TestS3StoreBytes:
    def test_store_bytes_calls_put_object(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(logical_path="test/data.bin"))
        data = b"hello world s3"
        storage.store_bytes(record.artifact_id, data)

        # Verify put_object was called
        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args
        assert call_kwargs.kwargs["Bucket"] == "test-bucket"
        assert call_kwargs.kwargs["Body"] == data
        assert call_kwargs.kwargs["Key"] == record.storage_key

    def test_store_bytes_computes_checksum_before_upload(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        data = b"checksum test data"
        stored = storage.store_bytes(record.artifact_id, data)

        expected_checksum = hashlib.sha256(data).hexdigest()
        assert stored.checksum_sha256 == expected_checksum
        assert stored.size_bytes == len(data)

        # Verify checksum was sent as metadata
        call_kwargs = mock_client.put_object.call_args
        assert call_kwargs.kwargs["Metadata"]["checksum-sha256"] == expected_checksum

    def test_store_bytes_updates_status_to_stored(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        stored = storage.store_bytes(record.artifact_id, b"data")
        assert stored.status == ArtifactStatus.STORED

    def test_store_bytes_nonexistent_raises(self) -> None:
        storage, _, _ = _build_s3_storage()
        with pytest.raises(ValueError, match="not found"):
            storage.store_bytes(uuid4(), b"data")

    def test_store_bytes_uses_safe_key(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(
            _make_create_request(
                kind=ArtifactKind.COVER_ART,
                logical_path="../../etc/passwd",
            )
        )
        storage.store_bytes(record.artifact_id, b"data")
        call_kwargs = mock_client.put_object.call_args
        key = call_kwargs.kwargs["Key"]
        assert ".." not in key
        assert not key.startswith("/")
        assert key.startswith("cover_art/")

    def test_store_bytes_content_type_propagated(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(content_type="image/png"))
        storage.store_bytes(record.artifact_id, b"PNG data", content_type="image/png")
        call_kwargs = mock_client.put_object.call_args
        assert call_kwargs.kwargs["ContentType"] == "image/png"


class TestS3GetRecord:
    def test_get_record_existing(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        retrieved = storage.get_record(record.artifact_id)
        assert retrieved is not None
        assert retrieved.artifact_id == record.artifact_id

    def test_get_record_nonexistent(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.get_record(uuid4()) is None


class TestS3ListRecords:
    def test_list_records_empty(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.list_records() == []

    def test_list_records_filter_by_kind(self) -> None:
        storage, _, _ = _build_s3_storage()
        storage.create_record(_make_create_request(kind=ArtifactKind.AUDIO_MIX))
        storage.create_record(_make_create_request(kind=ArtifactKind.COVER_ART))
        result = storage.list_records(kind=ArtifactKind.AUDIO_MIX)
        assert len(result) == 1
        assert result[0].kind == ArtifactKind.AUDIO_MIX


# ============================================================
# Download links
# ============================================================


class TestS3DownloadLinks:
    def test_presigned_url_when_no_public_base(self) -> None:
        storage, mock_client, _ = _build_s3_storage(public_base_url=None)
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"data")

        link = storage.get_download_link(record.artifact_id)
        assert link is not None
        assert "presigned" in link.url
        mock_client.generate_presigned_url.assert_called_once()

    def test_public_url_when_base_configured(self) -> None:
        storage, mock_client, _ = _build_s3_storage(
            public_base_url="https://cdn.example.com/artifacts"
        )
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"data")

        link = storage.get_download_link(record.artifact_id)
        assert link is not None
        assert link.url.startswith("https://cdn.example.com/artifacts/")
        assert record.storage_key in link.url
        # presigned URL should NOT have been generated
        mock_client.generate_presigned_url.assert_not_called()

    def test_public_url_strips_trailing_slash(self) -> None:
        storage, _, _ = _build_s3_storage(public_base_url="https://cdn.example.com/")
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"data")

        link = storage.get_download_link(record.artifact_id)
        assert link is not None
        # Should not have double slash
        assert "//" not in link.url.replace("https://", "")

    def test_download_link_returns_none_for_planned(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        assert storage.get_download_link(record.artifact_id) is None

    def test_download_link_returns_none_for_nonexistent(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.get_download_link(uuid4()) is None


# ============================================================
# get_bytes (S3 download for internal use)
# ============================================================


class TestS3GetBytes:
    def test_get_bytes_returns_content(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"original")

        data = storage.get_bytes(record.artifact_id)
        assert data == b"mock-content"
        mock_client.get_object.assert_called_once()

    def test_get_bytes_returns_none_for_planned(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        assert storage.get_bytes(record.artifact_id) is None

    def test_get_bytes_returns_none_for_nonexistent(self) -> None:
        storage, _, _ = _build_s3_storage()
        assert storage.get_bytes(uuid4()) is None

    def test_get_bytes_returns_none_on_s3_error(self) -> None:
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"data")
        mock_client.get_object.side_effect = Exception("S3 network error")

        data = storage.get_bytes(record.artifact_id)
        assert data is None


# ============================================================
# Summary
# ============================================================


class TestS3Summary:
    def test_summary_reflects_s3_mode(self) -> None:
        storage, _, _ = _build_s3_storage()
        s = storage.summary()
        assert s.storage_mode == "s3"
        assert s.total == 0

    def test_summary_counts_stored(self) -> None:
        storage, _, _ = _build_s3_storage()
        r1 = storage.create_record(_make_create_request())
        storage.create_record(_make_create_request())
        storage.store_bytes(r1.artifact_id, b"12345")
        s = storage.summary()
        assert s.total == 2
        assert s.stored == 1
        assert s.planned == 1
        assert s.total_size_bytes == 5


# ============================================================
# No delete_object
# ============================================================


class TestNoDeleteBehavior:
    def test_no_delete_object_method(self) -> None:
        """S3ArtifactStorage must not have a delete method."""
        storage, _, _ = _build_s3_storage()
        assert not hasattr(storage, "delete")
        assert not hasattr(storage, "delete_object")
        assert not hasattr(storage, "remove")

    def test_client_delete_object_never_called(self) -> None:
        """The boto3 client's delete_object should never be invoked."""
        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        storage.store_bytes(record.artifact_id, b"data")
        storage.get_record(record.artifact_id)
        storage.get_download_link(record.artifact_id)
        storage.list_records()
        storage.summary()

        # delete_object should never have been called
        mock_client.delete_object.assert_not_called()


# ============================================================
# Path traversal / key safety
# ============================================================


class TestS3KeySafety:
    def test_key_never_contains_dotdot(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(logical_path="../../../etc/passwd"))
        assert ".." not in record.storage_key

    def test_key_never_absolute(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(logical_path="/absolute/path/file.txt"))
        assert not record.storage_key.startswith("/")

    def test_key_follows_kind_prefix(self) -> None:
        storage, _, _ = _build_s3_storage()
        record = storage.create_record(
            _make_create_request(
                kind=ArtifactKind.AUDIO_MASTER,
                logical_path="track/master.wav",
            )
        )
        assert record.storage_key.startswith("audio_master/")
        assert record.storage_key.endswith(".wav")


# ============================================================
# Credentials not exposed
# ============================================================


class TestCredentialsNotExposed:
    def test_repr_does_not_contain_secret(self) -> None:
        storage, _, _ = _build_s3_storage()
        r = repr(storage)
        assert "test-secret-key" not in r
        assert "test-key-id" not in r

    def test_str_does_not_contain_secret(self) -> None:
        storage, _, _ = _build_s3_storage()
        s = str(storage)
        assert "test-secret-key" not in s


# ============================================================
# Integration: _get_artifact_bytes with S3 storage
# ============================================================


class TestReleaseExportS3Integration:
    def test_get_artifact_bytes_uses_get_bytes(self) -> None:
        """release_export._get_artifact_bytes should use get_bytes for S3."""
        from app.release_export import _get_artifact_bytes

        storage, mock_client, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request(content_type="image/png"))
        storage.store_bytes(record.artifact_id, b"png-data")

        result = _get_artifact_bytes(storage, record.artifact_id)
        assert result is not None
        data, rec = result
        assert data == b"mock-content"  # from mock get_object
        assert rec.artifact_id == record.artifact_id

    def test_get_artifact_bytes_returns_none_for_planned(self) -> None:
        from app.release_export import _get_artifact_bytes

        storage, _, _ = _build_s3_storage()
        record = storage.create_record(_make_create_request())
        assert _get_artifact_bytes(storage, record.artifact_id) is None


# ============================================================
# Normal test suite passes without S3 config
# ============================================================


class TestNoS3Required:
    def test_default_storage_is_local_without_s3(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ARTIFACT_STORAGE_ENV, raising=False)
        monkeypatch.delenv(S3_ENDPOINT_URL_ENV, raising=False)
        from app.artifact_storage import build_artifact_storage

        storage = build_artifact_storage()
        assert storage.mode == "local"
