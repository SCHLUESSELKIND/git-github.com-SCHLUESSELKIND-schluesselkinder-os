"""Real SoundCloud Publish Provider Boundary (S36).

Stub implementation — validates config exists but does NOT call the
SoundCloud API. Publish always returns BLOCKED status.

This provider exists as the architectural boundary for future OAuth
integration. No real API calls will be made until OAuth is implemented.

Hard rules:
- No SoundCloud API calls.
- No OAuth implementation.
- Publish returns BLOCKED with clear message.
- Credentials are never logged or returned in API responses.
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
    SoundCloudPublishWarning,
)


class RealSoundCloudPublishProvider:
    """Real SoundCloud provider boundary — no API calls yet.

    Config is validated at factory construction time. This class
    exists as the provider boundary for future OAuth integration.
    """

    name: str = "soundcloud"

    def build_metadata(self, release: ReleasePack) -> SoundCloudMetadata:
        """Extract SoundCloud metadata from a ReleasePack."""
        return _build_metadata_from_release(release)

    def create_publish_preview(self, release: ReleasePack) -> SoundCloudPublishPreview:
        """Build a preview — same as mock, but adds a provider warning."""
        metadata = self.build_metadata(release)
        warnings = _build_warnings(release)

        # Add real-provider-specific warning
        warnings.append(
            SoundCloudPublishWarning(
                code="real_provider_no_publish",
                message=(
                    "Real SoundCloud provider is selected but publishing is not "
                    "yet implemented. OAuth integration is required first."
                ),
            )
        )

        has_audio = metadata.audio_artifact_id is not None
        blocked_reason = (
            "Real SoundCloud publishing not yet implemented. OAuth integration required."
        )

        return SoundCloudPublishPreview(
            release_id=release.release_id,
            metadata=metadata,
            warnings=warnings,
            can_publish=False,
            blocked_reason=blocked_reason if has_audio else "No audio master uploaded.",
        )

    def publish(self, job: SoundCloudPublishJob) -> SoundCloudPublishJob:
        """Block publish — real API integration not available yet."""
        return job.model_copy(
            update={
                "status": SoundCloudPublishStatus.BLOCKED,
                "error": (
                    "Real SoundCloud publishing is not yet implemented. "
                    "OAuth integration is required. Use mock mode for testing."
                ),
                "updated_at": datetime.now(timezone.utc),
            }
        )
