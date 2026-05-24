"""Tests for S29 — Artifact Registry + Signed URL Policy.

Covers:
- Config: ArtifactRegistryMode, ArtifactAccessMode, env var parsing, loud failure
- ArtifactRegistry: InMemoryArtifactRegistry CRUD, summary, Protocol compliance
- Artifact storage with registry dependency injection
- Signed URL generation and validation
- Download route: direct mode backward compat, signed mode enforcement
- Capabilities: new registry/access fields
- Existing S27/S28 tests remain green (implicit via full suite)
"""

from __future__ import annotations

import asyncio
import base64
import tempfile
import time
from uuid import uuid4

import pytest

from app.artifact_registry import (
    InMemoryArtifactRegistry,
    build_artifact_registry,
)
from app.artifact_storage import (
    LocalArtifactStorage,
    build_artifact_storage,
)
from app.artifact_url_policy import (
    _compute_hmac,
    generate_download_url,
    validate_token,
)
from app.auth import DEV_OPERATOR
from app.config import (
    ARTIFACT_ACCESS_MODE_ENV,
    ARTIFACT_REGISTRY_ENV,
    ARTIFACT_SIGNING_SECRET_ENV,
    ArtifactAccessConfigError,
    ArtifactAccessMode,
    ArtifactRegistryConfigError,
    ArtifactRegistryMode,
    artifact_access_mode,
    artifact_registry_mode,
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


def _make_storage() -> LocalArtifactStorage:
    tmpdir = tempfile.mkdtemp()
    return LocalArtifactStorage(root=tmpdir)


# ============================================================
# Config tests
# ============================================================


class TestArtifactRegistryConfig:
    def test_default_mode_is_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ARTIFACT_REGISTRY_ENV, raising=False)
        assert artifact_registry_mode() == ArtifactRegistryMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_REGISTRY_ENV, "in_memory")
        assert artifact_registry_mode() == ArtifactRegistryMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_REGISTRY_ENV, "postgres")
        assert artifact_registry_mode() == ArtifactRegistryMode.POSTGRES

    def test_invalid_mode_fails_loud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_REGISTRY_ENV, "redis")
        with pytest.raises(RuntimeError, match="invalid"):
            artifact_registry_mode()

    def test_postgres_without_url_fails_loud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_REGISTRY_ENV, "postgres")
        monkeypatch.delenv("SOUNDSYSTEM_DATABASE_URL", raising=False)
        with pytest.raises(ArtifactRegistryConfigError, match="requires"):
            build_artifact_registry()


class TestArtifactAccessConfig:
    def test_default_mode_is_direct(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ARTIFACT_ACCESS_MODE_ENV, raising=False)
        assert artifact_access_mode() == ArtifactAccessMode.DIRECT

    def test_explicit_direct(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        assert artifact_access_mode() == ArtifactAccessMode.DIRECT

    def test_signed_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        assert artifact_access_mode() == ArtifactAccessMode.SIGNED

    def test_invalid_mode_fails_loud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "magic")
        with pytest.raises(RuntimeError, match="invalid"):
            artifact_access_mode()


# ============================================================
# InMemoryArtifactRegistry tests
# ============================================================


class TestInMemoryArtifactRegistry:
    def test_mode_is_in_memory(self) -> None:
        reg = InMemoryArtifactRegistry()
        assert reg.mode == "in_memory"

    def test_create_and_get_record(self) -> None:
        reg = InMemoryArtifactRegistry()
        req = _make_create_request()
        record = reg.create_record(req, storage_key="other/test.bin")
        assert record.status == ArtifactStatus.PLANNED
        fetched = reg.get_record(record.artifact_id)
        assert fetched is not None
        assert fetched.artifact_id == record.artifact_id

    def test_update_record(self) -> None:
        reg = InMemoryArtifactRegistry()
        req = _make_create_request()
        record = reg.create_record(req, storage_key="other/test.bin")
        updated = record.model_copy(update={"status": ArtifactStatus.STORED, "size_bytes": 42})
        result = reg.update_record(updated)
        assert result.status == ArtifactStatus.STORED
        fetched = reg.get_record(record.artifact_id)
        assert fetched is not None
        assert fetched.size_bytes == 42

    def test_list_records_all(self) -> None:
        reg = InMemoryArtifactRegistry()
        reg.create_record(
            _make_create_request(kind=ArtifactKind.LYRICS),
            storage_key="lyrics/a.json",
        )
        reg.create_record(
            _make_create_request(kind=ArtifactKind.MANIFEST),
            storage_key="manifest/b.json",
        )
        assert len(reg.list_records()) == 2

    def test_list_records_filtered_by_kind(self) -> None:
        reg = InMemoryArtifactRegistry()
        reg.create_record(
            _make_create_request(kind=ArtifactKind.LYRICS),
            storage_key="lyrics/a.json",
        )
        reg.create_record(
            _make_create_request(kind=ArtifactKind.MANIFEST),
            storage_key="manifest/b.json",
        )
        lyrics = reg.list_records(kind=ArtifactKind.LYRICS)
        assert len(lyrics) == 1
        assert lyrics[0].kind == ArtifactKind.LYRICS

    def test_get_record_returns_none_for_missing(self) -> None:
        reg = InMemoryArtifactRegistry()
        assert reg.get_record(uuid4()) is None

    def test_summary(self) -> None:
        reg = InMemoryArtifactRegistry()
        req = _make_create_request()
        r1 = reg.create_record(req, storage_key="other/1.bin")
        _r2 = reg.create_record(req, storage_key="other/2.bin")
        reg.update_record(
            r1.model_copy(update={"status": ArtifactStatus.STORED, "size_bytes": 100})
        )
        summary = reg.summary()
        assert summary.total == 2
        assert summary.stored == 1
        assert summary.planned == 1
        assert summary.total_size_bytes == 100

    def test_operator_id_propagated(self) -> None:
        reg = InMemoryArtifactRegistry()
        req = _make_create_request()
        record = reg.create_record(req, storage_key="other/test.bin", operator_id="op@test.com")
        assert record.operator_id == "op@test.com"


# ============================================================
# LocalArtifactStorage with registry injection
# ============================================================


class TestStorageWithRegistry:
    def test_storage_uses_injected_registry(self) -> None:
        reg = InMemoryArtifactRegistry()
        tmpdir = tempfile.mkdtemp()
        storage = LocalArtifactStorage(root=tmpdir, registry=reg)
        assert storage.registry is reg

    def test_create_and_store_bytes_roundtrip(self) -> None:
        storage = _make_storage()
        req = _make_create_request(
            kind=ArtifactKind.MANIFEST,
            logical_path="test/manifest.json",
            content_type="application/json",
        )
        record = storage.create_record(req, operator_id="test@test.com")
        assert record.status == ArtifactStatus.PLANNED

        stored = storage.store_bytes(record.artifact_id, b'{"test": true}', "application/json")
        assert stored.status == ArtifactStatus.STORED
        assert stored.size_bytes == 14
        assert stored.checksum_sha256 is not None

        # Verify file exists
        path = storage.get_file_path(stored.artifact_id)
        assert path is not None
        assert path.read_bytes() == b'{"test": true}'

    def test_list_records_delegates_to_registry(self) -> None:
        storage = _make_storage()
        storage.create_record(_make_create_request(kind=ArtifactKind.LYRICS))
        storage.create_record(_make_create_request(kind=ArtifactKind.MANIFEST))
        assert len(storage.list_records()) == 2
        assert len(storage.list_records(kind=ArtifactKind.LYRICS)) == 1

    def test_summary_delegates_to_registry(self) -> None:
        storage = _make_storage()
        req = _make_create_request(kind=ArtifactKind.MANIFEST, logical_path="m.json")
        rec = storage.create_record(req)
        storage.store_bytes(rec.artifact_id, b"data")
        summary = storage.summary()
        assert summary.total == 1
        assert summary.stored == 1
        assert summary.storage_mode == "local"


# ============================================================
# Factory tests
# ============================================================


class TestBuildArtifactRegistry:
    def test_default_builds_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ARTIFACT_REGISTRY_ENV, raising=False)
        reg = build_artifact_registry()
        assert reg.mode == "in_memory"

    def test_build_storage_with_default_registry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ARTIFACT_REGISTRY_ENV, raising=False)
        storage = build_artifact_storage()
        assert storage.mode == "local"
        assert storage.registry.mode == "in_memory"


# ============================================================
# Signed URL Policy tests
# ============================================================


class TestSignedUrlPolicy:
    def test_direct_mode_returns_plain_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        aid = uuid4()
        result = generate_download_url(aid)
        assert result.access_mode == "direct"
        assert f"/v1/artifacts/{aid}/download" == result.url
        assert result.expires_at is None
        assert "token" not in result.url

    def test_signed_mode_returns_signed_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "test-secret-key")
        aid = uuid4()
        result = generate_download_url(aid)
        assert result.access_mode == "signed"
        assert "token=" in result.url
        assert "expires=" in result.url
        assert result.expires_at is not None

    def test_signed_mode_without_secret_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.delenv(ARTIFACT_SIGNING_SECRET_ENV, raising=False)
        with pytest.raises(ArtifactAccessConfigError, match="requires"):
            generate_download_url(uuid4())


class TestTokenValidation:
    def test_direct_mode_always_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        is_valid, msg = validate_token(uuid4(), None, None)
        assert is_valid
        assert msg == ""

    def test_signed_mode_rejects_missing_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "secret")
        is_valid, msg = validate_token(uuid4(), None, None)
        assert not is_valid
        assert "missing" in msg

    def test_signed_mode_rejects_invalid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "secret")
        is_valid, msg = validate_token(uuid4(), "bad-token", None)
        assert not is_valid
        assert "invalid" in msg

    def test_signed_mode_accepts_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "secret")
        aid = uuid4()
        expires = str(int(time.time()) + 3600)
        token = _compute_hmac("secret", aid, int(expires))
        is_valid, msg = validate_token(aid, token, expires)
        assert is_valid
        assert msg == ""

    def test_signed_mode_rejects_expired_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "secret")
        aid = uuid4()
        expires = str(int(time.time()) - 100)
        token = _compute_hmac("secret", aid, int(expires))
        is_valid, msg = validate_token(aid, token, expires)
        assert not is_valid
        assert "expired" in msg

    def test_signed_mode_token_with_no_expiry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "my-secret")
        aid = uuid4()
        token = _compute_hmac("my-secret", aid, None)
        is_valid, msg = validate_token(aid, token, "")
        assert is_valid

    def test_token_for_wrong_artifact_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "secret")
        aid1 = uuid4()
        aid2 = uuid4()
        token = _compute_hmac("secret", aid1, None)
        is_valid, msg = validate_token(aid2, token, "")
        assert not is_valid


# ============================================================
# Route integration tests
# ============================================================


class TestDownloadRouteDirectMode:
    """Download route in direct mode (backward compatible)."""

    def test_download_stored_artifact(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        from app.main import artifact_storage, download_artifact, upload_artifact_bytes

        req = _make_create_request(
            kind=ArtifactKind.MANIFEST,
            logical_path="test/dl.json",
            content_type="application/json",
        )
        record = artifact_storage.create_record(req, operator_id="test@test.com")
        upload = ArtifactUploadRequest(
            content_base64=base64.b64encode(b'{"ok": true}').decode(),
            content_type="application/json",
        )
        asyncio.run(upload_artifact_bytes(record.artifact_id, upload, DEV_OPERATOR))

        response = asyncio.run(download_artifact(record.artifact_id))
        assert response.status_code == 200

    def test_download_planned_artifact_returns_409(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        from app.main import artifact_storage, download_artifact

        req = _make_create_request()
        record = artifact_storage.create_record(req)

        with pytest.raises(Exception) as exc_info:
            asyncio.run(download_artifact(record.artifact_id))
        assert "409" in str(exc_info.value.status_code)


class TestDownloadRouteSignedMode:
    """Download route in signed mode."""

    def test_download_without_token_returns_403(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "test-secret")
        from app.main import download_artifact

        aid = uuid4()
        with pytest.raises(Exception) as exc_info:
            asyncio.run(download_artifact(aid, token=None, expires=None))
        assert exc_info.value.status_code == 403

    def test_download_with_invalid_token_returns_403(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "test-secret")
        from app.main import download_artifact

        aid = uuid4()
        with pytest.raises(Exception) as exc_info:
            asyncio.run(download_artifact(aid, token="bad", expires=None))
        assert exc_info.value.status_code == 403


class TestDownloadLinkRoute:
    """GET /v1/artifacts/{artifact_id}/download-link"""

    def test_download_link_direct_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        from app.main import (
            artifact_storage,
            get_artifact_download_link,
            upload_artifact_bytes,
        )

        req = _make_create_request(
            kind=ArtifactKind.MANIFEST,
            logical_path="test/link.json",
            content_type="application/json",
        )
        record = artifact_storage.create_record(req)
        upload = ArtifactUploadRequest(
            content_base64=base64.b64encode(b"test").decode(),
        )
        asyncio.run(upload_artifact_bytes(record.artifact_id, upload, DEV_OPERATOR))

        result = asyncio.run(get_artifact_download_link(record.artifact_id))
        assert result.access_mode == "direct"
        assert "token" not in result.url

    def test_download_link_signed_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "signed")
        monkeypatch.setenv(ARTIFACT_SIGNING_SECRET_ENV, "link-secret")
        from app.main import (
            artifact_storage,
            get_artifact_download_link,
            upload_artifact_bytes,
        )

        req = _make_create_request(
            kind=ArtifactKind.MANIFEST,
            logical_path="test/slink.json",
            content_type="application/json",
        )
        record = artifact_storage.create_record(req)
        upload = ArtifactUploadRequest(
            content_base64=base64.b64encode(b"test").decode(),
        )
        asyncio.run(upload_artifact_bytes(record.artifact_id, upload, DEV_OPERATOR))

        result = asyncio.run(get_artifact_download_link(record.artifact_id))
        assert result.access_mode == "signed"
        assert "token=" in result.url

    def test_download_link_planned_artifact_returns_409(self) -> None:
        from app.main import artifact_storage, get_artifact_download_link

        req = _make_create_request()
        record = artifact_storage.create_record(req)
        with pytest.raises(Exception) as exc_info:
            asyncio.run(get_artifact_download_link(record.artifact_id))
        assert exc_info.value.status_code == 409

    def test_download_link_missing_artifact_returns_404(self) -> None:
        from app.main import get_artifact_download_link

        with pytest.raises(Exception) as exc_info:
            asyncio.run(get_artifact_download_link(uuid4()))
        assert exc_info.value.status_code == 404


# ============================================================
# Capabilities tests
# ============================================================


class TestCapabilities:
    def test_capabilities_expose_registry_and_access_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ARTIFACT_ACCESS_MODE_ENV, "direct")
        monkeypatch.delenv(ARTIFACT_REGISTRY_ENV, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.artifact_registry_mode == "in_memory"
        assert caps.artifact_access_mode == "direct"
        assert caps.artifact_storage_available is True


# ============================================================
# No S3 required
# ============================================================


class TestNoS3Required:
    def test_default_storage_is_local_without_s3(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_ARTIFACT_STORAGE", raising=False)
        monkeypatch.delenv("SOUNDSYSTEM_S3_ENDPOINT_URL", raising=False)
        storage = build_artifact_storage()
        assert storage.mode == "local"
