"""SoundCloud Publishing Provider Isolation Layer (S36).

Protocol + factory. Every SoundCloud publish provider must satisfy
`SoundCloudPublishProviderProtocol`. The factory function
`build_soundcloud_publish_provider()` reads `SOUNDSYSTEM_SOUNDCLOUD_PROVIDER`
and constructs the correct variant.

Supported values:
- "mock" (default) — deterministic metadata preview, no SoundCloud API call.
- "soundcloud" — real SoundCloud SDK boundary. Requires client ID/secret.
  Real publish is NOT implemented — always returns BLOCKED status.

Hard rules:
1. Mock remains default — tests never hit SoundCloud.
2. No silent fallback — if "soundcloud" selected without config, fail loudly.
3. No real SoundCloud API calls in this slice.
4. No OAuth implementation yet.
5. Credentials never exposed in logs, errors, or API responses.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    ReleasePack,
    SoundCloudMetadata,
    SoundCloudPublishJob,
    SoundCloudPublishPreview,
    SoundCloudPublishWarning,
)


class SoundCloudPublishProviderProtocol(Protocol):
    """Shared interface for all SoundCloud publish providers.

    Route handlers never see SoundCloud SDK types — only this Protocol.
    """

    name: str

    def build_metadata(self, release: ReleasePack) -> SoundCloudMetadata:
        """Extract SoundCloud metadata from a ReleasePack."""
        ...

    def create_publish_preview(self, release: ReleasePack) -> SoundCloudPublishPreview:
        """Build a preview of what would be published."""
        ...

    def publish(self, job: SoundCloudPublishJob) -> SoundCloudPublishJob:
        """Execute the publish action.

        Mock: marks job as published_mock.
        Real: returns BLOCKED (not implemented).
        """
        ...


def _build_metadata_from_release(release: ReleasePack) -> SoundCloudMetadata:
    """Shared metadata builder — used by both mock and real providers."""
    # Extract artifact IDs from asset placeholders
    cover_artifact_id = None
    audio_artifact_id = None
    for asset in release.assets:
        if asset.asset_type == "cover_art" and asset.ready and asset.artifact_id:
            cover_artifact_id = asset.artifact_id
        if asset.asset_type == "audio_master" and asset.ready and asset.artifact_id:
            audio_artifact_id = asset.artifact_id

    # Build tags from hashtags
    tags = [t.lstrip("#") for t in release.social_copy.hashtags if t]

    return SoundCloudMetadata(
        title=release.title,
        artist=release.artist,
        description=release.social_copy.soundcloud_description,
        tags=tags,
        genre=release.genre,
        is_private=True,
        downloadable=False,
        cover_artifact_id=cover_artifact_id,
        audio_artifact_id=audio_artifact_id,
        release_pack_id=release.release_id,
    )


def _build_warnings(release: ReleasePack) -> list[SoundCloudPublishWarning]:
    """Check release readiness and generate warnings."""
    warnings: list[SoundCloudPublishWarning] = []

    # Check audio master
    has_audio = any(
        a.asset_type == "audio_master" and a.ready and a.artifact_id for a in release.assets
    )
    if not has_audio:
        warnings.append(
            SoundCloudPublishWarning(
                code="audio_missing",
                message="No audio master uploaded. Cannot publish without audio.",
            )
        )

    # Check cover art
    has_cover = any(
        a.asset_type == "cover_art" and a.ready and a.artifact_id for a in release.assets
    )
    if not has_cover:
        warnings.append(
            SoundCloudPublishWarning(
                code="cover_missing",
                message="No cover art uploaded. SoundCloud track will use default artwork.",
            )
        )

    # Check compliance
    if not release.compliance_passed:
        warnings.append(
            SoundCloudPublishWarning(
                code="compliance_incomplete",
                message="Compliance checklist not fully passed.",
            )
        )

    # Check release status
    if release.status != "ready":
        warnings.append(
            SoundCloudPublishWarning(
                code="release_not_ready",
                message=f"Release status is '{release.status}', not 'ready'.",
            )
        )

    return warnings


def build_soundcloud_publish_provider() -> SoundCloudPublishProviderProtocol:
    """Factory: read config and return the correct provider instance.

    - MOCK (default): no external deps, deterministic.
    - SOUNDCLOUD: requires client_id + client_secret. Publish returns BLOCKED.
    """
    from app.config import (
        SoundCloudProviderConfigError,
        SoundCloudProviderMode,
        soundcloud_client_id,
        soundcloud_client_secret,
        soundcloud_provider_mode,
    )

    mode = soundcloud_provider_mode()

    if mode == SoundCloudProviderMode.SOUNDCLOUD:
        cid = soundcloud_client_id()
        csecret = soundcloud_client_secret()
        missing = []
        if not cid:
            missing.append("SOUNDCLOUD_CLIENT_ID")
        if not csecret:
            missing.append("SOUNDCLOUD_CLIENT_SECRET")
        if missing:
            raise SoundCloudProviderConfigError(
                f"SOUNDSYSTEM_SOUNDCLOUD_PROVIDER=soundcloud requires "
                f"{', '.join(missing)} to be set."
            )
        from app.providers.soundcloud.real import RealSoundCloudPublishProvider

        return RealSoundCloudPublishProvider()  # type: ignore[return-value]

    # Default: mock
    from app.providers.soundcloud.mock import MockSoundCloudPublishProvider

    return MockSoundCloudPublishProvider()  # type: ignore[return-value]
