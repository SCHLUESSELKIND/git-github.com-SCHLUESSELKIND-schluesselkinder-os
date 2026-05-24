"""Mock SoundCloud Publish Provider (S36).

Default provider — no external dependencies, deterministic results.
No real SoundCloud API calls. Safe for tests and local development.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.providers.soundcloud import (
    _build_metadata_from_release,
    _build_warnings,
)
from app.schemas import (
    ReleasePack,
    SoundCloudMetadata,
    SoundCloudPublishJob,
    SoundCloudPublishPreview,
    SoundCloudPublishStatus,
)


class MockSoundCloudPublishProvider:
    """Mock implementation — builds metadata previews and marks jobs as published_mock.

    No real SoundCloud API calls. Safe for tests and local development.
    """

    name: str = "mock"

    def build_metadata(self, release: ReleasePack) -> SoundCloudMetadata:
        """Extract SoundCloud metadata from a ReleasePack."""
        return _build_metadata_from_release(release)

    def create_publish_preview(self, release: ReleasePack) -> SoundCloudPublishPreview:
        """Build a preview of what would be published."""
        metadata = self.build_metadata(release)
        warnings = _build_warnings(release)

        # Can publish if audio is present (mock mode always allows)
        has_audio = metadata.audio_artifact_id is not None
        blocked_reason = None if has_audio else "No audio master uploaded."

        return SoundCloudPublishPreview(
            release_id=release.release_id,
            metadata=metadata,
            warnings=warnings,
            can_publish=has_audio,
            blocked_reason=blocked_reason,
        )

    def publish(self, job: SoundCloudPublishJob) -> SoundCloudPublishJob:
        """Mock publish: READY → PUBLISHED_MOCK."""
        if job.status == SoundCloudPublishStatus.BLOCKED:
            return job

        return job.model_copy(
            update={
                "status": SoundCloudPublishStatus.PUBLISHED_MOCK,
                "updated_at": datetime.now(timezone.utc),
            }
        )
