"""Artifact storage abstraction for the inference service (S27, S29, S35).

Provides a Protocol-based interface for registering, storing, and retrieving
binary artifacts. Ships with a local filesystem adapter and an in-memory
metadata registry. An S3-compatible adapter is in `artifact_storage_s3.py`.

S29 additions:
- Registry dependency injection (InMemory or Postgres).
- Signed URL policy for download links.
- `build_artifact_storage()` now creates registry via factory.

S35 additions:
- S3ArtifactStorage adapter in `artifact_storage_s3.py`.
- Factory returns S3 adapter when `SOUNDSYSTEM_ARTIFACT_STORAGE=s3`.
- boto3 is never imported unless S3 mode is selected.

Hard rules:
- Local mode restricts writes to the configured artifact root (path traversal blocked).
- S3 mode fails loudly if required config is missing.
- No destructive deletes in this slice.
- No arbitrary filesystem access.
- Registry can be in-memory or Postgres — file bytes are never stored in Postgres.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.artifact_registry import (
    ArtifactRegistry,
    InMemoryArtifactRegistry,
    build_artifact_registry,
)
from app.config import (
    ArtifactStorageConfigError,
    ArtifactStorageMode,
    artifact_root,
    artifact_storage_mode,
    s3_access_key_id,
    s3_bucket,
    s3_endpoint_url,
    s3_force_path_style,
    s3_public_base_url,
    s3_region,
    s3_secret_access_key,
)
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactDownloadLink,
    ArtifactKind,
    ArtifactRecord,
    ArtifactStatus,
    ArtifactStorageSummary,
)


def _safe_storage_key(kind: ArtifactKind, artifact_id: UUID, logical_path: str) -> str:
    """Build a deterministic, safe storage key from the artifact metadata.

    The key is always relative and never contains '..' or absolute path components.
    """
    # Extract file extension from logical path
    ext = ""
    base = os.path.basename(logical_path)
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1][:10]  # cap extension length
    # Sanitize extension
    ext = re.sub(r"[^a-zA-Z0-9.]", "", ext)
    return f"{kind.value}/{artifact_id}{ext}"


def _validate_within_root(root: Path, target: Path) -> None:
    """Ensure target path is within root — blocks path traversal."""
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError(f"path traversal blocked: {target} is not within artifact root {root}")


@runtime_checkable
class ArtifactStorage(Protocol):
    """Protocol for artifact storage implementations."""

    @property
    def mode(self) -> str: ...

    def create_record(
        self,
        request: ArtifactCreateRequest,
        operator_id: str | None = None,
    ) -> ArtifactRecord: ...

    def store_bytes(
        self,
        artifact_id: UUID,
        data: bytes,
        content_type: str | None = None,
    ) -> ArtifactRecord: ...

    def get_record(self, artifact_id: UUID) -> ArtifactRecord | None: ...

    def list_records(self, *, kind: ArtifactKind | None = None) -> list[ArtifactRecord]: ...

    def get_download_link(self, artifact_id: UUID) -> ArtifactDownloadLink | None: ...

    def summary(self) -> ArtifactStorageSummary: ...


class LocalArtifactStorage:
    """Local filesystem artifact storage with pluggable metadata registry.

    Stores binary content under the configured artifact root directory.
    Metadata is delegated to an ArtifactRegistry (in-memory or Postgres).
    Storage keys are deterministic and safe (no path traversal).
    """

    def __init__(
        self,
        root: str | None = None,
        registry: ArtifactRegistry | None = None,
    ) -> None:
        self._root = Path(root or artifact_root()).resolve()
        self._registry: ArtifactRegistry = registry or InMemoryArtifactRegistry()

    @property
    def mode(self) -> str:
        return "local"

    @property
    def root(self) -> Path:
        return self._root

    @property
    def registry(self) -> ArtifactRegistry:
        return self._registry

    def create_record(
        self,
        request: ArtifactCreateRequest,
        operator_id: str | None = None,
    ) -> ArtifactRecord:
        # Generate a temporary UUID to compute the storage key
        from uuid import uuid4

        temp_id = uuid4()
        storage_key = _safe_storage_key(request.kind, temp_id, request.logical_path)
        record = self._registry.create_record(
            request,
            storage_key=storage_key,
            storage_mode="local",
            operator_id=operator_id,
        )
        # The registry assigned a new UUID, recompute storage key with it
        real_key = _safe_storage_key(request.kind, record.artifact_id, request.logical_path)
        if real_key != record.storage_key:
            updated = record.model_copy(update={"storage_key": real_key})
            return self._registry.update_record(updated)
        return record

    def store_bytes(
        self,
        artifact_id: UUID,
        data: bytes,
        content_type: str | None = None,
    ) -> ArtifactRecord:
        record = self._registry.get_record(artifact_id)
        if record is None:
            raise ValueError(f"artifact {artifact_id} not found in registry")

        storage_key = record.storage_key
        if storage_key is None:
            raise ValueError(f"artifact {artifact_id} has no storage_key")

        target = self._root / storage_key
        _validate_within_root(self._root, target)

        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Write bytes
        target.write_bytes(data)

        # Compute checksum and size
        checksum = hashlib.sha256(data).hexdigest()
        size = len(data)

        now = datetime.now(timezone.utc)
        updated = record.model_copy(
            update={
                "status": ArtifactStatus.STORED,
                "size_bytes": size,
                "checksum_sha256": checksum,
                "content_type": content_type or record.content_type,
                "updated_at": now,
            }
        )
        return self._registry.update_record(updated)

    def get_record(self, artifact_id: UUID) -> ArtifactRecord | None:
        return self._registry.get_record(artifact_id)

    def list_records(self, *, kind: ArtifactKind | None = None) -> list[ArtifactRecord]:
        return self._registry.list_records(kind=kind)

    def get_download_link(self, artifact_id: UUID) -> ArtifactDownloadLink | None:
        record = self._registry.get_record(artifact_id)
        if record is None:
            return None
        if record.status != ArtifactStatus.STORED:
            return None
        # Return a route-based URL, not a raw filesystem path
        return ArtifactDownloadLink(
            artifact_id=artifact_id,
            url=f"/v1/artifacts/{artifact_id}/download",
            expires_at=None,
        )

    def get_file_path(self, artifact_id: UUID) -> Path | None:
        """Return the physical file path for a stored artifact (internal use)."""
        record = self._registry.get_record(artifact_id)
        if record is None or record.storage_key is None:
            return None
        if record.status != ArtifactStatus.STORED:
            return None
        path = self._root / record.storage_key
        if path.exists():
            return path
        return None

    def summary(self) -> ArtifactStorageSummary:
        return self._registry.summary(storage_mode=self.mode)


def decode_upload_content(content_base64: str) -> bytes:
    """Decode base64-encoded upload content.

    Raises ValueError if the content is not valid base64.
    """
    try:
        return base64.b64decode(content_base64)
    except Exception as exc:
        raise ValueError(f"invalid base64 content: {exc}")


def build_artifact_storage() -> ArtifactStorage:
    """Factory: build artifact storage based on the configured mode.

    Defaults to local filesystem. S3 mode requires endpoint, credentials,
    and bucket — fails loudly when any are missing. boto3 is only imported
    when S3 mode is selected.

    S29: Registry is selected via SOUNDSYSTEM_ARTIFACT_REGISTRY.
    S35: S3 adapter is wired up when SOUNDSYSTEM_ARTIFACT_STORAGE=s3.
    """
    mode = artifact_storage_mode()

    if mode == ArtifactStorageMode.LOCAL:
        registry = build_artifact_registry()
        return LocalArtifactStorage(registry=registry)

    if mode == ArtifactStorageMode.S3:
        # Validate required S3 config
        missing = []
        if not s3_endpoint_url():
            missing.append("SOUNDSYSTEM_S3_ENDPOINT_URL")
        if not s3_access_key_id():
            missing.append("SOUNDSYSTEM_S3_ACCESS_KEY_ID")
        if not s3_secret_access_key():
            missing.append("SOUNDSYSTEM_S3_SECRET_ACCESS_KEY")
        if not s3_bucket():
            missing.append("SOUNDSYSTEM_S3_BUCKET")
        if missing:
            raise ArtifactStorageConfigError(f"S3 artifact storage requires: {', '.join(missing)}")

        # Lazy import — S3 adapter imports boto3 at construction time
        from app.artifact_storage_s3 import S3ArtifactStorage

        registry = build_artifact_registry()
        return S3ArtifactStorage(
            endpoint_url=s3_endpoint_url(),  # type: ignore[arg-type]
            region=s3_region(),
            access_key_id=s3_access_key_id(),  # type: ignore[arg-type]
            secret_access_key=s3_secret_access_key(),  # type: ignore[arg-type]
            bucket=s3_bucket(),  # type: ignore[arg-type]
            force_path_style=s3_force_path_style(),
            public_base_url=s3_public_base_url(),
            registry=registry,
        )

    raise ArtifactStorageConfigError(f"unsupported artifact storage mode: {mode}")
