"""Campaign OS Builder Logic (S45, S47 vinyl integration).

Builds a Campaign object from a ReleasePack by inferring operational
tasks across all channels (SoundCloud, Distribution, Merch, Shopify,
Printful, TikTok Shop, Vinyl).

No real social API calls. No automation execution. No scheduling engine.
No real vinyl vendor calls. Orchestration read-model only.

Functions:
- build_campaign_from_release: scaffold a campaign from a ReleasePack
- infer_campaign_tasks: generate channel-specific tasks from release state
- infer_campaign_warnings: evaluate missing prerequisites
"""

from __future__ import annotations

from uuid import uuid4

from app.schemas import (
    Campaign,
    CampaignChannel,
    CampaignStatus,
    CampaignTask,
    CampaignTaskStatus,
    CampaignTimelineItem,
    CampaignWarning,
    ReleasePack,
    VinylReleaseObject,
    VinylReleaseStatus,
)


# ---------- Default channels ----------

_DEFAULT_CHANNELS: list[CampaignChannel] = [
    CampaignChannel.SOUNDCLOUD,
    CampaignChannel.DISTRIBUTION,
    CampaignChannel.MERCH,
    CampaignChannel.TIKTOK,
    CampaignChannel.INSTAGRAM,
]


# ---------- Task inference ----------


def infer_campaign_tasks(
    release: ReleasePack,
    vinyl_release: VinylReleaseObject | None = None,
) -> list[CampaignTask]:
    """Generate operational tasks from release state.

    Tasks are channel-grouped and status-aware. Missing prerequisites
    result in BLOCKED status. Vinyl tasks are included when a
    VinylReleaseObject is provided or when release assets suggest
    vinyl is relevant.
    """
    tasks: list[CampaignTask] = []

    # --- Release foundation tasks ---

    # Cover art upload
    cover_ready = _has_ready_asset(release, "cover_art")
    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.DISTRIBUTION,
            title="Upload cover art",
            description="Upload PNG cover artwork (min 1400x1400, square).",
            status=CampaignTaskStatus.COMPLETED if cover_ready else CampaignTaskStatus.PENDING,
        )
    )

    # Audio master upload
    audio_ready = _has_ready_asset(release, "audio_master")
    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.DISTRIBUTION,
            title="Upload audio master",
            description="Upload WAV audio master for distribution.",
            status=CampaignTaskStatus.COMPLETED if audio_ready else CampaignTaskStatus.PENDING,
        )
    )

    # Build release export ZIP
    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.DISTRIBUTION,
            title="Build release export ZIP",
            description="Bundle assets into downloadable release export.",
            status=CampaignTaskStatus.PENDING,
            depends_on=["Upload cover art", "Upload audio master"],
            warnings=[]
            if (cover_ready and audio_ready)
            else ["Missing assets — upload cover and audio first."],
        )
    )

    # --- SoundCloud ---

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.SOUNDCLOUD,
            title="Create SoundCloud preview",
            description="Generate SoundCloud publish metadata and eligibility check.",
            status=CampaignTaskStatus.PENDING,
            depends_on=["Upload audio master"],
            warnings=[] if audio_ready else ["Audio master required for SoundCloud preview."],
        )
    )

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.SOUNDCLOUD,
            title="Publish to SoundCloud (mock)",
            description="Execute mock SoundCloud publish job.",
            status=CampaignTaskStatus.BLOCKED if not audio_ready else CampaignTaskStatus.PENDING,
            depends_on=["Create SoundCloud preview"],
        )
    )

    # --- Ditto Distribution ---

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.DISTRIBUTION,
            title="Create Ditto distribution pack",
            description="Build distribution metadata and readiness checklist.",
            status=CampaignTaskStatus.PENDING,
        )
    )

    # --- Merch ---

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.MERCH,
            title="Build merch capsule",
            description="Scaffold merch products from release metadata.",
            status=CampaignTaskStatus.PENDING,
        )
    )

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.MERCH,
            title="Build Shopify drafts",
            description="Generate Shopify-compatible product draft payloads.",
            status=CampaignTaskStatus.PENDING,
            depends_on=["Build merch capsule"],
        )
    )

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.MERCH,
            title="Build Printful syncs",
            description="Generate Printful-compatible sync payloads.",
            status=CampaignTaskStatus.PENDING,
            depends_on=["Build merch capsule"],
        )
    )

    # --- TikTok ---

    tasks.append(
        CampaignTask(
            task_id=uuid4(),
            channel=CampaignChannel.TIKTOK,
            title="Build TikTok Shop listings",
            description="Generate TikTok Shop listing drafts from merch capsule.",
            status=CampaignTaskStatus.PENDING,
            depends_on=["Build merch capsule"],
        )
    )

    # --- Vinyl (S47) ---

    if vinyl_release is not None:
        # Vinyl release exists — reflect its state
        vinyl_ready = vinyl_release.status not in (
            VinylReleaseStatus.DRAFT,
            VinylReleaseStatus.BLOCKED,
        )
        readiness_passed = all(r.passed for r in vinyl_release.readiness_items)

        tasks.append(
            CampaignTask(
                task_id=uuid4(),
                channel=CampaignChannel.DISTRIBUTION,
                title="Build vinyl release object",
                description="Vinyl release object created from ReleasePack.",
                status=CampaignTaskStatus.COMPLETED,
                linked_object_id=vinyl_release.vinyl_id,
            )
        )

        tasks.append(
            CampaignTask(
                task_id=uuid4(),
                channel=CampaignChannel.DISTRIBUTION,
                title="Check vinyl readiness",
                description="Evaluate vinyl readiness checklist.",
                status=CampaignTaskStatus.COMPLETED
                if readiness_passed
                else CampaignTaskStatus.PENDING,
                depends_on=["Build vinyl release object"],
                linked_object_id=vinyl_release.vinyl_id,
                warnings=vinyl_release.warnings[:3] if not readiness_passed else [],
            )
        )

        tasks.append(
            CampaignTask(
                task_id=uuid4(),
                channel=CampaignChannel.DISTRIBUTION,
                title="Build vinyl export payload",
                description="Generate export payload for manual provider handoff.",
                status=CampaignTaskStatus.PENDING if vinyl_ready else CampaignTaskStatus.BLOCKED,
                depends_on=["Check vinyl readiness"],
                linked_object_id=vinyl_release.vinyl_id,
            )
        )

        tasks.append(
            CampaignTask(
                task_id=uuid4(),
                channel=CampaignChannel.DISTRIBUTION,
                title="Submit manual vinyl handoff",
                description="Manual handoff to vinyl provider. No manufacturing order placed.",
                status=CampaignTaskStatus.COMPLETED
                if vinyl_release.status
                in (
                    VinylReleaseStatus.SUBMITTED,
                    VinylReleaseStatus.TEST_PRESSING,
                    VinylReleaseStatus.APPROVED,
                    VinylReleaseStatus.LIVE,
                )
                else CampaignTaskStatus.BLOCKED,
                depends_on=["Build vinyl export payload"],
                linked_object_id=vinyl_release.vinyl_id,
            )
        )
    else:
        # No vinyl release yet — suggest building one
        tasks.append(
            CampaignTask(
                task_id=uuid4(),
                channel=CampaignChannel.DISTRIBUTION,
                title="Build vinyl release object",
                description="Create vinyl collector object from ReleasePack.",
                status=CampaignTaskStatus.PENDING
                if (cover_ready and audio_ready)
                else CampaignTaskStatus.BLOCKED,
                warnings=[]
                if (cover_ready and audio_ready)
                else ["Cover and audio master required for vinyl release."],
            )
        )

    return tasks


# ---------- Warning inference ----------


def infer_campaign_warnings(release: ReleasePack) -> list[CampaignWarning]:
    """Evaluate missing prerequisites and generate campaign warnings."""
    warnings: list[CampaignWarning] = []

    if not _has_ready_asset(release, "cover_art"):
        warnings.append(
            CampaignWarning(
                code="missing_cover",
                message="Cover art not uploaded. Required for distribution and merch.",
            )
        )

    if not _has_ready_asset(release, "audio_master"):
        warnings.append(
            CampaignWarning(
                code="missing_audio",
                message="Audio master not uploaded. Required for SoundCloud and distribution.",
            )
        )

    if not release.compliance_passed:
        warnings.append(
            CampaignWarning(
                code="compliance_incomplete",
                message="Compliance checklist not fully passed. Complete before activating.",
            )
        )

    if release.status.value == "draft":
        warnings.append(
            CampaignWarning(
                code="release_not_ready",
                message="Release is still in draft. Mark as ready before activating campaign.",
            )
        )

    return warnings


# ---------- Campaign builder ----------


def build_campaign_from_release(
    release: ReleasePack,
    *,
    channels: list[CampaignChannel] | None = None,
    operator_id: str | None = None,
    notes: str = "",
    vinyl_release: VinylReleaseObject | None = None,
) -> Campaign:
    """Build a campaign scaffold from a ReleasePack.

    Infers tasks, evaluates warnings, sets initial status.
    No automation execution. Orchestration-only.
    """
    selected_channels = channels if channels else list(_DEFAULT_CHANNELS)
    tasks = infer_campaign_tasks(release, vinyl_release=vinyl_release)
    warnings = infer_campaign_warnings(release)

    # Filter tasks to selected channels
    tasks = [t for t in tasks if t.channel in selected_channels]

    # Determine initial status
    status = CampaignStatus.PLANNING

    timeline = [
        CampaignTimelineItem(
            event="Campaign created",
            object_type="release",
            object_id=release.release_id,
            notes=f"Scaffolded from release '{release.title}'.",
        )
    ]

    return Campaign(
        campaign_id=uuid4(),
        release_id=release.release_id,
        title=f"{release.title} — Campaign",
        status=status,
        channels=selected_channels,
        tasks=tasks,
        timeline=timeline,
        warnings=warnings,
        notes=notes,
        created_by=operator_id,
    )


# ---------- Helpers ----------


def _has_ready_asset(release: ReleasePack, asset_type: str) -> bool:
    """Check if a release has a ready asset of the given type."""
    return any(a.asset_type == asset_type and a.ready for a in release.assets)
