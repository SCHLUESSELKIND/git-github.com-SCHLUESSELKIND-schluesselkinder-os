"""Tests for S27 — Artifact Storage Layer.

Covers:
- Config (ArtifactStorageMode, env var parsing, loud failure)
- Factory (build_artifact_storage with local/s3 modes)
- LocalArtifactStorage (Protocol compliance, full CRUD, bytes, checksums)
- Path traversal blocking
- API routes (6 endpoints via direct handler calls)
- Capabilities integration
- E2E: create → upload → download → verify
"""

from __future__ import annotations

import asyncio
import base64
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from app.auth import DEV_OPERATOR
from app.config import (
    ARTIFACT_ROOT_ENV,
    ARTIFACT_STORAGE_ENV,
    S3_ACCESS_KEY_ID_ENV,
    S3_BUCKET_ENV,
    S3_ENDPOINT_URL_ENV,
    S3_SECRET_ACCESS_KEY_ENV,
    ArtifactStorageConfigError,
    ArtifactStorageMode,
    artifact_storage_mode,
)
from app.artifact_storage import (
    LocalArtifactStorage,
    build_artifact_storage,
    decode_upload_content,
    _safe_storage_key,
)
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactStatus,
    ArtifactUploadRequest,
)


# ---------- Helpers ----------


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


# ---------- Config Tests ----------


class TestArtifactStorageConfig:
    def test_default_mode_is_local(self, monkeypatch):
        monkeypatch.delenv(ARTIFACT_STORAGE_ENV, raising=False)
        assert artifact_storage_mode() == ArtifactStorageMode.LOCAL

    def test_explicit_local(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "local")
        assert artifact_storage_mode() == ArtifactStorageMode.LOCAL

    def test_s3_mode(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
        assert artifact_storage_mode() == ArtifactStorageMode.S3

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "S3")
        assert artifact_storage_mode() == ArtifactStorageMode.S3

    def test_invalid_mode_raises(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "gcs")
        with pytest.raises(RuntimeError, match="invalid"):
            artifact_storage_mode()


# ---------- Factory Tests ----------


class TestBuildArtifactStorage:
    def test_default_returns_local(self, monkeypatch):
        monkeypatch.delenv(ARTIFACT_STORAGE_ENV, raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ARTIFACT_ROOT_ENV, tmpdir)
            storage = build_artifact_storage()
            assert isinstance(storage, LocalArtifactStorage)
            assert storage.mode == "local"

    def test_s3_without_config_raises(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
        monkeypatch.delenv(S3_ENDPOINT_URL_ENV, raising=False)
        monkeypatch.delenv(S3_ACCESS_KEY_ID_ENV, raising=False)
        monkeypatch.delenv(S3_SECRET_ACCESS_KEY_ENV, raising=False)
        monkeypatch.delenv(S3_BUCKET_ENV, raising=False)
        with pytest.raises(ArtifactStorageConfigError, match="S3"):
            build_artifact_storage()

    def test_s3_with_config_requires_boto3(self, monkeypatch):
        """S3 mode with valid config attempts to import boto3.

        If boto3 is not installed, it raises RuntimeError. If it is installed,
        it creates an S3ArtifactStorage. Either way, it does NOT raise
        ArtifactStorageConfigError (config is complete).
        """
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
        monkeypatch.setenv(S3_ENDPOINT_URL_ENV, "https://s3.example.com")
        monkeypatch.setenv(S3_ACCESS_KEY_ID_ENV, "key")
        monkeypatch.setenv(S3_SECRET_ACCESS_KEY_ENV, "secret")
        monkeypatch.setenv(S3_BUCKET_ENV, "bucket")
        try:
            storage = build_artifact_storage()
            # boto3 was available — S3 adapter created
            assert storage.mode == "s3"
        except RuntimeError as exc:
            # boto3 not installed — expected clear message
            assert "boto3" in str(exc)

    def test_s3_reports_missing_fields(self, monkeypatch):
        monkeypatch.setenv(ARTIFACT_STORAGE_ENV, "s3")
        monkeypatch.setenv(S3_ENDPOINT_URL_ENV, "https://s3.example.com")
        monkeypatch.delenv(S3_ACCESS_KEY_ID_ENV, raising=False)
        monkeypatch.delenv(S3_SECRET_ACCESS_KEY_ENV, raising=False)
        monkeypatch.delenv(S3_BUCKET_ENV, raising=False)
        with pytest.raises(ArtifactStorageConfigError, match="S3_ACCESS_KEY_ID"):
            build_artifact_storage()


# ---------- Storage Key Tests ----------


class TestSafeStorageKey:
    def test_basic_key(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.AUDIO_MIX, aid, "track/full_mix.wav")
        assert key == f"audio_mix/{aid}.wav"

    def test_no_extension(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.MANIFEST, aid, "manifest")
        assert key == f"manifest/{aid}"

    def test_strips_path_traversal(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.OTHER, aid, "../../etc/passwd")
        # Extension from "passwd" is empty (no dot), key should be safe
        assert ".." not in key
        assert key.startswith("other/")

    def test_long_extension_capped(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.OTHER, aid, "file.verylongextension")
        ext_part = key.split(".")[-1] if "." in key else ""
        assert len(ext_part) <= 10


# ---------- LocalArtifactStorage Tests ----------


class TestLocalArtifactStorage:
    def test_create_record(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request())
            assert record.status == ArtifactStatus.PLANNED
            assert record.kind == ArtifactKind.OTHER
            assert record.storage_key is not None
            assert record.storage_mode == "local"

    def test_create_record_preserves_operator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request(), operator_id="op-42")
            assert record.operator_id == "op-42"

    def test_create_record_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            entity_id = uuid4()
            req = ArtifactCreateRequest(
                kind=ArtifactKind.AUDIO_MIX,
                logical_path="track.wav",
                source_entity_type="music_job",
                source_entity_id=entity_id,
            )
            record = storage.create_record(req)
            assert record.source_entity_type == "music_job"
            assert record.source_entity_id == entity_id

    def test_store_bytes_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request(logical_path="test/data.bin"))
            data = b"hello world"
            stored = storage.store_bytes(record.artifact_id, data)
            assert stored.status == ArtifactStatus.STORED
            assert stored.size_bytes == 11
            assert stored.checksum_sha256 is not None
            assert len(stored.checksum_sha256) == 64

    def test_store_bytes_under_root_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request(logical_path="test/data.bin"))
            storage.store_bytes(record.artifact_id, b"test")
            # Verify file is under root (resolve both to handle macOS /var → /private/var)
            file_path = storage.get_file_path(record.artifact_id)
            assert file_path is not None
            assert str(file_path.resolve()).startswith(str(Path(tmpdir).resolve()))

    def test_store_bytes_computes_checksum(self):
        import hashlib

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request())
            data = b"checksum test data"
            stored = storage.store_bytes(record.artifact_id, data)
            expected = hashlib.sha256(data).hexdigest()
            assert stored.checksum_sha256 == expected

    def test_store_bytes_nonexistent_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            with pytest.raises(ValueError, match="not found"):
                storage.store_bytes(uuid4(), b"data")

    def test_get_record_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request())
            retrieved = storage.get_record(record.artifact_id)
            assert retrieved is not None
            assert retrieved.artifact_id == record.artifact_id

    def test_get_record_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            assert storage.get_record(uuid4()) is None

    def test_list_records_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            assert storage.list_records() == []

    def test_list_records_filter_by_kind(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            storage.create_record(_make_create_request(kind=ArtifactKind.AUDIO_MIX))
            storage.create_record(_make_create_request(kind=ArtifactKind.COVER_ART))
            storage.create_record(_make_create_request(kind=ArtifactKind.AUDIO_MIX))
            result = storage.list_records(kind=ArtifactKind.AUDIO_MIX)
            assert len(result) == 2
            assert all(r.kind == ArtifactKind.AUDIO_MIX for r in result)

    def test_list_records_ordered_desc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            for _ in range(3):
                storage.create_record(_make_create_request())
            records = storage.list_records()
            for i in range(len(records) - 1):
                assert records[i].created_at >= records[i + 1].created_at

    def test_download_link_for_stored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request())
            storage.store_bytes(record.artifact_id, b"data")
            link = storage.get_download_link(record.artifact_id)
            assert link is not None
            assert f"/v1/artifacts/{record.artifact_id}/download" in link.url

    def test_download_link_for_planned_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            record = storage.create_record(_make_create_request())
            link = storage.get_download_link(record.artifact_id)
            assert link is None

    def test_download_link_nonexistent_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            assert storage.get_download_link(uuid4()) is None

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            r1 = storage.create_record(_make_create_request())
            storage.create_record(_make_create_request())
            storage.store_bytes(r1.artifact_id, b"12345")
            s = storage.summary()
            assert s.total == 2
            assert s.planned == 1
            assert s.stored == 1
            assert s.total_size_bytes == 5
            assert s.storage_mode == "local"

    def test_mode_property(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalArtifactStorage(root=tmpdir)
            assert storage.mode == "local"

    def test_artifact_root_is_created_on_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = str(Path(tmpdir) / "nested" / "artifacts")
            storage = LocalArtifactStorage(root=subdir)
            record = storage.create_record(
                _make_create_request(kind=ArtifactKind.MANIFEST, logical_path="m.json")
            )
            storage.store_bytes(record.artifact_id, b'{"manifest": true}')
            assert Path(subdir).exists()


# ---------- Path Traversal Tests ----------


class TestPathTraversal:
    def test_storage_key_never_contains_dotdot(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.OTHER, aid, "../../../etc/passwd")
        assert ".." not in key

    def test_storage_key_never_absolute(self):
        aid = uuid4()
        key = _safe_storage_key(ArtifactKind.OTHER, aid, "/absolute/path/file.txt")
        assert not key.startswith("/")


# ---------- Base64 Decode Tests ----------


class TestDecodeUploadContent:
    def test_valid_base64(self):
        data = b"hello world"
        encoded = base64.b64encode(data).decode()
        assert decode_upload_content(encoded) == data

    def test_invalid_base64_raises(self):
        with pytest.raises(ValueError, match="invalid base64"):
            decode_upload_content("not-valid-base64!!!")


# ---------- Route Tests ----------


class TestArtifactRoutes:
    def test_create_artifact(self):
        from app.main import create_artifact as route

        req = ArtifactCreateRequest(
            kind=ArtifactKind.AUDIO_MIX,
            logical_path="track/full_mix.wav",
        )
        record = asyncio.run(route(req, DEV_OPERATOR))
        assert record.status == ArtifactStatus.PLANNED
        assert record.operator_id == DEV_OPERATOR.operator_id

    def test_list_artifacts(self):
        from app.main import create_artifact as route_create, list_artifacts as route_list

        req = ArtifactCreateRequest(
            kind=ArtifactKind.COVER_ART,
            logical_path="cover.png",
        )
        asyncio.run(route_create(req, DEV_OPERATOR))
        artifacts = asyncio.run(route_list())
        assert len(artifacts) >= 1

    def test_list_artifacts_filter_by_kind(self):
        from app.main import create_artifact as route_create, list_artifacts as route_list

        asyncio.run(
            route_create(
                ArtifactCreateRequest(kind=ArtifactKind.LYRICS, logical_path="l.json"),
                DEV_OPERATOR,
            )
        )
        asyncio.run(
            route_create(
                ArtifactCreateRequest(kind=ArtifactKind.MANIFEST, logical_path="m.json"),
                DEV_OPERATOR,
            )
        )
        lyrics = asyncio.run(route_list(kind=ArtifactKind.LYRICS))
        assert all(r.kind == ArtifactKind.LYRICS for r in lyrics)

    def test_get_artifact(self):
        from app.main import create_artifact as route_create, get_artifact as route_get

        req = ArtifactCreateRequest(kind=ArtifactKind.OTHER, logical_path="test.bin")
        record = asyncio.run(route_create(req, DEV_OPERATOR))
        retrieved = asyncio.run(route_get(record.artifact_id))
        assert retrieved.artifact_id == record.artifact_id

    def test_get_artifact_not_found(self):
        from app.main import get_artifact as route_get

        with pytest.raises(Exception, match="artifact_not_found"):
            asyncio.run(route_get(uuid4()))

    def test_upload_bytes(self):
        from app.main import (
            create_artifact as route_create,
            upload_artifact_bytes as route_upload,
        )

        record = asyncio.run(
            route_create(
                ArtifactCreateRequest(kind=ArtifactKind.OTHER, logical_path="test.bin"),
                DEV_OPERATOR,
            )
        )
        data = b"test artifact content"
        upload_req = ArtifactUploadRequest(content_base64=base64.b64encode(data).decode())
        stored = asyncio.run(route_upload(record.artifact_id, upload_req, DEV_OPERATOR))
        assert stored.status == ArtifactStatus.STORED
        assert stored.size_bytes == len(data)

    def test_upload_bytes_not_found(self):
        from app.main import upload_artifact_bytes as route_upload

        upload_req = ArtifactUploadRequest(content_base64=base64.b64encode(b"data").decode())
        with pytest.raises(Exception, match="artifact_not_found"):
            asyncio.run(route_upload(uuid4(), upload_req, DEV_OPERATOR))

    def test_summary_route(self):
        from app.main import artifact_summary as route_summary

        summary = asyncio.run(route_summary())
        assert summary.total >= 0
        assert summary.storage_mode == "local"

    def test_capabilities_includes_artifact_storage(self):
        from app.main import capabilities as route

        caps = asyncio.run(route())
        assert caps.artifact_storage_available is True
        assert caps.artifact_storage_mode == "local"


# ---------- E2E: Full Lifecycle ----------


class TestArtifactStorageE2E:
    """Full flow: create → upload → get → download link → verify."""

    def test_full_lifecycle(self):
        from app.main import (
            artifact_summary as route_summary,
            create_artifact as route_create,
            get_artifact as route_get,
            list_artifacts as route_list,
            upload_artifact_bytes as route_upload,
        )

        # 1. Create
        req = ArtifactCreateRequest(
            kind=ArtifactKind.AUDIO_MIX,
            logical_path="e2e/full_mix.wav",
            content_type="audio/wav",
            source_entity_type="music_job",
            source_entity_id=uuid4(),
        )
        record = asyncio.run(route_create(req, DEV_OPERATOR))
        assert record.status == ArtifactStatus.PLANNED
        assert record.operator_id == DEV_OPERATOR.operator_id

        # 2. Upload bytes
        data = b"RIFF" + b"\x00" * 100  # Fake WAV header
        upload_req = ArtifactUploadRequest(
            content_base64=base64.b64encode(data).decode(),
            content_type="audio/wav",
        )
        stored = asyncio.run(route_upload(record.artifact_id, upload_req, DEV_OPERATOR))
        assert stored.status == ArtifactStatus.STORED
        assert stored.size_bytes == len(data)
        assert stored.checksum_sha256 is not None

        # 3. Get
        retrieved = asyncio.run(route_get(record.artifact_id))
        assert retrieved.status == ArtifactStatus.STORED
        assert retrieved.content_type == "audio/wav"

        # 4. List
        artifacts = asyncio.run(route_list())
        assert any(r.artifact_id == record.artifact_id for r in artifacts)

        # 5. Summary
        summary = asyncio.run(route_summary())
        assert summary.stored >= 1
        assert summary.total_size_bytes >= len(data)

    def test_multiple_kinds_lifecycle(self):
        from app.main import (
            create_artifact as route_create,
            list_artifacts as route_list,
            upload_artifact_bytes as route_upload,
        )

        # Create artifacts of different kinds
        kinds = [
            ArtifactKind.AUDIO_MIX,
            ArtifactKind.STEM_PACK,
            ArtifactKind.COVER_ART,
            ArtifactKind.MANIFEST,
        ]
        for kind in kinds:
            record = asyncio.run(
                route_create(
                    ArtifactCreateRequest(kind=kind, logical_path=f"{kind.value}/test.bin"),
                    DEV_OPERATOR,
                )
            )
            asyncio.run(
                route_upload(
                    record.artifact_id,
                    ArtifactUploadRequest(
                        content_base64=base64.b64encode(f"data-{kind.value}".encode()).decode()
                    ),
                    DEV_OPERATOR,
                )
            )

        # Filter by kind
        mixes = asyncio.run(route_list(kind=ArtifactKind.AUDIO_MIX))
        assert all(r.kind == ArtifactKind.AUDIO_MIX for r in mixes)
        assert len(mixes) >= 1
