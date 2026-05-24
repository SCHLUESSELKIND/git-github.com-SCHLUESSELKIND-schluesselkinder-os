"""Cover artwork upload pipeline — S31.

Validates and stores cover artwork PNG/JPG through ArtifactStorage,
then attaches the resulting ArtifactRecord to a ReleasePack asset
placeholder.

Hard rules:
- Only image/png and image/jpeg accepted.
- SVG and WebP rejected.
- Max 20 MB.
- Minimum 1400x1400 px, square required.
- Warning if below 3000x3000 px (recommended).
- Pillow used for dimension validation.
- No arbitrary filesystem access.
"""

from __future__ import annotations

import io
import os
import re
from uuid import UUID

from PIL import Image

from app.artifact_storage import ArtifactStorage, decode_upload_content
from app.schemas import (
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    CoverAssetUploadRequest,
    CoverAssetUploadResult,
    CoverValidationWarning,
    ReleasePack,
)

# Maximum upload size: 20 MB
MAX_COVER_SIZE_BYTES = 20 * 1024 * 1024

# Minimum dimension: 1400x1400 px
MIN_DIMENSION_PX = 1400

# Recommended dimension: 3000x3000 px
RECOMMENDED_DIMENSION_PX = 3000

# Accepted content types
ACCEPTED_CONTENT_TYPES = frozenset({"image/png", "image/jpeg"})

# Rejected content types (explicit block)
REJECTED_CONTENT_TYPES = frozenset({"image/svg+xml", "image/webp"})


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename: strip path components, keep only safe chars."""
    base = os.path.basename(filename)
    # Keep only alphanumeric, dash, underscore, dot
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return safe[:200] if safe else "cover"


def validate_cover_content_type(content_type: str) -> None:
    """Validate content type is an accepted image format.

    Raises ValueError for rejected or unknown types.
    """
    if content_type in REJECTED_CONTENT_TYPES:
        raise ValueError(
            f"content type {content_type} is not accepted for cover art. "
            f"Use image/png or image/jpeg."
        )
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise ValueError(f"unknown content type {content_type}. Accepted: image/png, image/jpeg.")


def validate_cover_data(
    data: bytes,
    content_type: str,
) -> list[CoverValidationWarning]:
    """Validate cover image data: size, dimensions, aspect ratio.

    Returns a list of warnings (non-fatal). Raises ValueError for
    fatal validation failures.
    """
    warnings: list[CoverValidationWarning] = []

    # Size check
    if len(data) > MAX_COVER_SIZE_BYTES:
        size_mb = len(data) / (1024 * 1024)
        raise ValueError(
            f"cover image too large: {size_mb:.1f} MB "
            f"(max {MAX_COVER_SIZE_BYTES // (1024 * 1024)} MB)"
        )

    if len(data) == 0:
        raise ValueError("cover image is empty (0 bytes)")

    # Pillow dimension validation
    try:
        img = Image.open(io.BytesIO(data))
        width, height = img.size
    except Exception as exc:
        raise ValueError(f"cannot read image dimensions: {exc}") from exc

    # Format cross-check
    pillow_format = (img.format or "").upper()
    if content_type == "image/png" and pillow_format not in ("PNG",):
        raise ValueError(f"content_type is image/png but image format is {pillow_format}")
    if content_type == "image/jpeg" and pillow_format not in ("JPEG", "MPO"):
        raise ValueError(f"content_type is image/jpeg but image format is {pillow_format}")

    # Square check
    if width != height:
        raise ValueError(f"cover art must be square: got {width}x{height} px")

    # Minimum dimension
    if width < MIN_DIMENSION_PX:
        raise ValueError(
            f"cover art too small: {width}x{height} px "
            f"(minimum {MIN_DIMENSION_PX}x{MIN_DIMENSION_PX} px)"
        )

    # Recommended dimension warning
    if width < RECOMMENDED_DIMENSION_PX:
        warnings.append(
            CoverValidationWarning(
                code="below_recommended_size",
                message=(
                    f"Cover is {width}x{height} px. "
                    f"Recommended minimum is {RECOMMENDED_DIMENSION_PX}x{RECOMMENDED_DIMENSION_PX} px "
                    f"for distribution platforms."
                ),
            )
        )

    return warnings


def upload_cover_for_release(
    release: ReleasePack,
    request: CoverAssetUploadRequest,
    storage: ArtifactStorage,
    operator_id: str | None = None,
) -> CoverAssetUploadResult:
    """Upload cover artwork and attach to a release pack.

    1. Validate content type
    2. Decode base64
    3. Validate image data (size, dimensions, aspect)
    4. Create ArtifactRecord (kind=cover_art)
    5. Store bytes
    6. Update release pack asset placeholder

    Returns CoverAssetUploadResult with the updated release and artifact.
    Raises ValueError for validation failures.
    """
    # 1. Content type
    validate_cover_content_type(request.content_type)

    # 2. Decode
    data = decode_upload_content(request.content_base64)

    # 3. Validate image
    warnings = validate_cover_data(data, request.content_type)

    # 4. Create artifact record
    safe_filename = _sanitize_filename(request.filename)
    artifact_request = ArtifactCreateRequest(
        kind=ArtifactKind.COVER_ART,
        logical_path=f"releases/{release.release_id}/cover/{safe_filename}",
        content_type=request.content_type,
        source_entity_type="release_pack",
        source_entity_id=str(release.release_id),
    )
    record = storage.create_record(artifact_request, operator_id=operator_id)

    # 5. Store bytes
    stored_record: ArtifactRecord = storage.store_bytes(
        record.artifact_id,
        data,
        content_type=request.content_type,
    )

    # 6. Update release asset placeholder
    updated_release = _attach_cover_to_release(release, stored_record.artifact_id)

    return CoverAssetUploadResult(
        release=updated_release,
        artifact=stored_record,
        warnings=warnings,
    )


def _attach_cover_to_release(
    release: ReleasePack,
    artifact_id: UUID,
) -> ReleasePack:
    """Update the cover_art asset placeholder with the artifact reference."""
    updated_assets = []
    found = False
    for asset in release.assets:
        if asset.asset_type == "cover_art":
            updated_assets.append(
                asset.model_copy(
                    update={
                        "ready": True,
                        "artifact_id": artifact_id,
                    }
                )
            )
            found = True
        else:
            updated_assets.append(asset)

    if not found:
        # No placeholder existed — add one
        from app.schemas import ReleaseAssetPlaceholder

        updated_assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
                artifact_id=artifact_id,
            )
        )

    from datetime import datetime, timezone

    return release.model_copy(
        update={
            "assets": updated_assets,
            "updated_at": datetime.now(timezone.utc),
        }
    )
