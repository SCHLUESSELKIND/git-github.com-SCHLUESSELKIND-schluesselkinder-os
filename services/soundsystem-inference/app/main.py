from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as RawResponse

from app.auth import Operator, require_operator

from app.compliance_preflight import (
    evaluate_preflight,
    evaluate_release_eligibility,
)
from app.compliance_repository import (
    ComplianceRepository,
    build_default_compliance_repository,
)
from app.dropbox_sync import (
    DropboxSyncRepository,
    build_export_plan,
    create_sync_job,
    mark_ready_for_sync,
)
from app.providers.dropbox import build_dropbox_sync_provider
from app.providers.soundcloud import build_soundcloud_publish_provider
from app.soundcloud_repository import InMemorySoundCloudPublishRepository
from app.merch_capsule import (
    build_merch_capsule_from_release,
    build_mock_provider_export,
    enforce_merch_capsule_rules,
    update_merch_product,
)
from app.merch_provider_aggregation import build_provider_aggregation
from app.analytics_graph import (
    aggregate_campaign_performance,
    aggregate_track_performance,
    build_source_breakdown,
    generate_demo_analytics_events,
)
from app.analytics_repository import build_analytics_repository
from app.connector_import_audit import build_connector_import_audit_repository
from app.intelligence_snapshot_diff import compare_snapshots
from app.intelligence_snapshot_repository import build_intelligence_snapshot_repository
from app.intelligence_engine import (
    build_audience_heatmaps,
    build_intelligence_overview,
    build_revenue_correlations,
    build_timeline_correlations,
    detect_viral_moments,
)
from app.platform_connectors import (
    build_mock_platform_connector,
    has_mock_platform_connector,
)
from app.provider_connector_registry import build_connector_registry
from app.provider_sync_preview import build_connector_sync_preview
from app.automation_execution import (
    create_execution_job_from_dry_run,
    execute_mock_job,
)
from app.automation_execution_audit import (
    AutomationExecutionAuditRepository,
    build_automation_execution_audit_repository,
)
from app.automation_execution_repository import (
    AutomationExecutionRepository,
    build_automation_execution_repository,
)
from app.campaign_automation import evaluate_rule, evaluate_rules_for_campaign
from app.campaign_automation_repository import (
    CampaignAutomationRuleRepository,
    InMemoryCampaignAutomationRuleRepository,
)
from app.campaign_automation_templates import (
    build_default_automation_templates,
    get_template_by_slug,
    instantiate_template,
    summarize_templates,
)
from app.release_command_center import (
    bootstrap_release_campaign,
    build_release_command_center,
)
from app.config import (
    automation_execution_audit_mode as get_automation_execution_audit_mode,
    automation_execution_mode,
    automation_execution_repository_mode as get_automation_execution_repository_mode,
)
from app.campaign_builder import build_campaign_from_release
from app.campaign_repository import CampaignRepository, build_campaign_repository
from app.vinyl_release import (
    build_vinyl_export_payload,
    build_vinyl_release_from_release,
    update_vinyl_status,
)
from app.vinyl_repository import build_vinyl_repository
from app.merch_repository import (
    MerchRepository,
    build_merch_repository,
)
from app.distribution_pack import (
    build_distribution_pack_from_release,
    evaluate_readiness,
)
from app.distribution_repository import (
    DistributionRepository,
    build_distribution_repository,
)
from app.providers.shopify import (
    build_shopify_draft_provider,
    supports_live_sync as shopify_supports_live_sync,
)
from app.shopify_draft_repository import (
    InMemoryShopifyDraftRepository,
    ShopifyDraftRepository,
)
from app.providers.printful import (
    build_printful_sync_provider,
    supports_live_sync as printful_supports_live_sync,
)
from app.commerce_sync_dashboard import (
    build_commerce_capsule_sync_state,
    build_commerce_sync_summary,
    combine_sync_results,
)
from app.commerce_sync_audit import (
    CommerceSyncAuditRepository,
    build_commerce_sync_audit_repository,
)
from app.newsletter_subscribe import subscribe_to_newsletter
from app.config import (
    commerce_sync_audit_mode as get_commerce_sync_audit_mode,
    listmonk_is_configured as _listmonk_is_configured,
)
from app.printful_sync_repository import (
    InMemoryPrintfulSyncRepository,
    PrintfulSyncRepository,
)
from app.providers.tiktok_shop import build_tiktok_shop_provider
from app.tiktok_shop_repository import (
    InMemoryTikTokShopRepository,
    TikTokShopRepository,
)
from app.export_pack import (
    build_export_pack,
    build_library_entry,
)
from app.release_pack import (
    build_release_pack,
    mark_release_ready,
    update_checklist_item,
)
from app.release_repository import (
    ReleaseRepository,
    build_release_repository,
)
from app.job_queue import (
    JobQueue,
    build_job_queue,
)
from app.job_worker import (
    run_job_by_id,
)
from app.audio_upload import upload_audio_master_for_release
from app.cover_upload import upload_cover_for_release
from app.stem_upload import upload_stem_pack_for_release
from app.release_export import build_release_export_zip
from app.artifact_storage import (
    ArtifactStorage,
    LocalArtifactStorage,
    build_artifact_storage,
    decode_upload_content,
)
from app.artifact_bridge import (
    record_artifact_for_soundgraph,
    record_artifacts_for_export_pack,
    record_artifacts_for_music_job,
    record_artifacts_for_release_pack,
)
from app.artifact_url_policy import (
    generate_download_url,
    validate_token,
)
from app.config import (
    artifact_access_mode as get_artifact_access_mode,
    artifact_registry_mode as get_artifact_registry_mode,
)
from app.library_repository import (
    LibraryRepository,
    build_library_repository,
)
from app.music_router import (
    MusicRouterRepository,
    build_default_music_router_repository,
    run_music_job,
)
from app.voice_lab_repository import (
    VoiceLabRepository,
    build_default_voice_lab_repository,
)
from app.voice_provider import run_voice_job
from app.config import api_key as get_api_key, lyrics_repository_mode
from app.lyrics_engine import compile_lyrics_prompt
from app.providers.lyrics import build_lyrics_provider
from app.lyrics_repository import (
    LyricsRepository,
    build_lyrics_repository,
)
from app.master_bus import MockMasterBusProvider, reference_clearance_missing
from app.master_repository import InMemoryMasterBusRepository, MasterBusRepository
from app.prompt_engine import compile_prompt
from app.providers.registry import build_default_provider_registry
from app.soundgraph_handoff import (
    compile_handoff_prompt,
    estimate_duration_seconds,
    execute_handoff,
    extract_locked_lanes,
    extract_requested_lanes,
    resolve_intent_from_arrangement,
)
from app.soundgraph_writer import (
    SoundGraphRepository,
    compile_soundgraph,
)
from app.repository import GenerationJobRepository, InMemoryGenerationJobRepository
from app.schemas import (
    Atmosphere,
    AuditEvent,
    AuditEventCreateRequest,
    BassPressure,
    CapabilitiesResponse,
    CompiledLyricsPrompt,
    CompiledPrompt,
    CompiledPromptRequest,
    CompliancePreflightRequest,
    CompliancePreflightResult,
    ComplianceRegistrySummary,
    ConsentRecord,
    ConsentRecordCreateRequest,
    EffectDeviceType,
    Energy,
    Engine,
    ExportProfile,
    GenerationJob,
    GenerationRequest,
    HealthResponse,
    Intent,
    JobEventType,
    JobStatus,
    LicenseRegistryCreateRequest,
    LicenseRegistryEntry,
    LyricsApplySelectionRewriteRequest,
    LyricsEditRequest,
    LyricsExportManifest,
    LyricsGenerationRequest,
    LyricsLockToggleRequest,
    LyricsManualUpdateRequest,
    LyricsProject,
    LyricsRewriteResponse,
    LyricsRewriteSelectionRequest,
    LyricsSectionType,
    LyricsSource,
    LyricsVersion,
    MasterBusJob,
    MasterBusRequest,
    MasterJobStatus,
    MasteringMode,
    ModelRegistryEntry,
    OutputProvenance,
    OutputProvenanceCreateRequest,
    ProviderCapability,
    ReleaseEligibilityResult,
    StemLaneType,
    Structure,
    VocalPerformanceNote,
    Vocals,
    VoiceJob,
    VoiceJobCreateRequest,
    VoiceLabSummary,
    VoiceTag,
    VoiceTagCreateRequest,
    MusicArtifactManifest,
    MusicGenerationRequest,
    MusicIntentKind,
    MusicJob,
    MusicRouterSummary,
    SoundGraphArrangement,
    SoundGraphHandoffRequest,
    SoundGraphHandoffResult,
    SoundGraphWriteRequest,
    SoundGraphWriteResult,
    ExportPack,
    ExportPackCreateRequest,
    ProjectLibraryEntry,
    ProjectLibrarySummary,
    DropboxExportPlan,
    DropboxExportPlanCreateRequest,
    DropboxSyncJob,
    DropboxSyncSummary,
    ReleasePack,
    ReleasePackCreateRequest,
    ReleasePackSummary,
    CoverAssetUploadRequest,
    CoverAssetUploadResult,
    AudioMasterUploadRequest,
    AudioMasterUploadResult,
    StemPackUploadRequest,
    StemPackUploadResult,
    ReleaseExportResult,
    SoundCloudPublishJob,
    SoundCloudPublishPreview,
    SoundCloudPublishRequest,
    SoundCloudPublishStatus,
    SoundCloudPublishSummary,
    MerchCapsule,
    MerchCapsuleCreateRequest,
    MerchCapsuleStatus,
    MerchCapsuleSummary,
    MerchExportPayload,
    MerchProductUpdateRequest,
    MerchProductUpdateResult,
    DistributionPack,
    DistributionPackCreateRequest,
    DistributionPackStatusUpdateRequest,
    DistributionPackSummary,
    ShopifyDraftExport,
    ShopifyDraftSummary,
    ShopifyProductDraft,
    PrintfulProductSync,
    PrintfulSyncExport,
    PrintfulSyncSummary,
    TikTokShopListing,
    TikTokShopListingExport,
    TikTokShopSummary,
    MerchProviderAggregation,
    AutomationExecutionAuditRecord,
    AutomationExecutionAuditSummary,
    AutomationExecutionJob,
    AutomationExecutionResult,
    AutomationExecutionSummary,
    Campaign,
    CommerceCapsuleSyncResult,
    CommerceCapsuleSyncState,
    CommerceSyncAuditAction,
    CommerceSyncAuditRecord,
    CommerceSyncAuditSummary,
    CommerceSyncSummary,
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    CampaignAutomationDryRunResult,
    CampaignAutomationRule,
    CampaignAutomationRuleCreateRequest,
    CampaignAutomationRuleSummary,
    CampaignAutomationRuleTemplate,
    CampaignAutomationRuleUpdateRequest,
    CampaignAutomationTemplateInstantiationRequest,
    CampaignAutomationTemplateSummary,
    ReleaseCommandCenter,
    ReleaseCommandCenterBootstrapResult,
    CampaignCreateRequest,
    CampaignStatus,
    CampaignSummary,
    CampaignUpdateRequest,
    VinylExportPayload,
    VinylReleaseCreateRequest,
    VinylReleaseObject,
    VinylReleaseStatus,
    VinylReleaseStatusUpdateRequest,
    VinylReleaseSummary,
    AsyncJob,
    AsyncJobCreateRequest,
    AsyncJobKind,
    AsyncJobSummary,
    ArtifactCreateRequest,
    ArtifactKind,
    ArtifactRecord,
    ArtifactSignedUrl,
    ArtifactStorageSummary,
    ArtifactUploadRequest,
    AnalyticsEvent,
    AnalyticsEventCreateRequest,
    AnalyticsMetric,
    AnalyticsSource,
    AnalyticsSummary,
    CampaignPerformance,
    ChannelPerformance,
    TrackPerformance,
    AudienceHeatmap,
    IntelligenceOverview,
    RevenueCorrelation,
    TimelineCorrelation,
    ViralMoment,
    ConnectorHealth,
    ConnectorImportAuditRecord,
    ConnectorImportAuditSummary,
    ConnectorRegistrySummary,
    ConnectorSyncPreview,
    ConnectorType,
    IntelligenceSnapshot,
    IntelligenceSnapshotCreateRequest,
    IntelligenceSnapshotDiff,
    IntelligenceSnapshotStatus,
    IntelligenceSnapshotSummary,
    ProviderConnector,
)

app = FastAPI(
    title="SNUFFRAGA SOUNDSYSTEM AI ENGINE",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# CORS — opt-in via env. The public newsletter endpoint is called from the
# browser at schluesselkinder.de, which is cross-origin against
# api.schluesselkinder.de. Operator endpoints stay server-to-server and do
# not need a browser preflight.
#
# Env: SOUNDSYSTEM_CORS_ALLOWED_ORIGINS=comma,separated,origins
# If unset → no CORS middleware is installed (safe default for tests + dev).
# ---------------------------------------------------------------------------
_cors_origins_raw = os.environ.get("SOUNDSYSTEM_CORS_ALLOWED_ORIGINS", "").strip()
_cors_origins = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
        max_age=600,
    )

job_repository: GenerationJobRepository = InMemoryGenerationJobRepository()
provider_registry = build_default_provider_registry()
master_repository: MasterBusRepository = InMemoryMasterBusRepository()
master_provider = MockMasterBusProvider()
lyrics_repository: LyricsRepository = build_lyrics_repository()
lyrics_provider = build_lyrics_provider()
compliance_repository: ComplianceRepository = build_default_compliance_repository()
voice_lab_repository: VoiceLabRepository = build_default_voice_lab_repository()
music_router_repository: MusicRouterRepository = build_default_music_router_repository()
soundgraph_repository = SoundGraphRepository()
project_library: LibraryRepository = build_library_repository()
dropbox_sync_repository = DropboxSyncRepository()
dropbox_sync_provider = build_dropbox_sync_provider()
release_pack_repository: ReleaseRepository = build_release_repository()
job_queue: JobQueue = build_job_queue()
artifact_storage: ArtifactStorage = build_artifact_storage()
soundcloud_publish_provider = build_soundcloud_publish_provider()
soundcloud_publish_repository = InMemorySoundCloudPublishRepository()
merch_capsule_repository: MerchRepository = build_merch_repository()
distribution_repository: DistributionRepository = build_distribution_repository()
shopify_draft_provider = build_shopify_draft_provider()
shopify_draft_repository: ShopifyDraftRepository = InMemoryShopifyDraftRepository()
printful_sync_provider = build_printful_sync_provider()
printful_sync_repository: PrintfulSyncRepository = InMemoryPrintfulSyncRepository()
tiktok_shop_provider = build_tiktok_shop_provider()
tiktok_shop_repository: TikTokShopRepository = InMemoryTikTokShopRepository()
campaign_repository: CampaignRepository = build_campaign_repository()
campaign_automation_rule_repository: CampaignAutomationRuleRepository = (
    InMemoryCampaignAutomationRuleRepository()
)
automation_execution_repository: AutomationExecutionRepository = (
    build_automation_execution_repository()
)
automation_execution_audit_repository: AutomationExecutionAuditRepository = (
    build_automation_execution_audit_repository()
)
commerce_sync_audit_repository: CommerceSyncAuditRepository = build_commerce_sync_audit_repository()
vinyl_repository = build_vinyl_repository()
analytics_repository = build_analytics_repository()
connector_import_audit = build_connector_import_audit_repository()
intelligence_snapshot_repository = build_intelligence_snapshot_repository()
connector_registry = build_connector_registry()


@app.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="snuffraga-soundsystem-inference")


@app.get("/v1/capabilities")
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        service="snuffraga-soundsystem-inference",
        engines=[engine for engine in Engine],
        intents=[intent for intent in Intent],
        prompt_modules={
            "energy": [item.value for item in Energy],
            "bass_pressure": [item.value for item in BassPressure],
            "vocals": [item.value for item in Vocals],
            "atmosphere": [item.value for item in Atmosphere],
            "structure": [item.value for item in Structure],
        },
        providers=[
            ProviderCapability(
                name=provider.name,
                engine=provider.engine,
                available=provider.available,
                fallback=provider.fallback,
            )
            for provider in await provider_registry.health_check()
        ],
        stem_lanes=[lane for lane in StemLaneType],
        effect_devices=[device for device in EffectDeviceType],
        mastering_modes=[mode for mode in MasteringMode],
        export_profiles=[profile for profile in ExportProfile],
        lyrics_section_types=[section_type for section_type in LyricsSectionType],
        lyrics_sources=[source for source in LyricsSource],
        lyrics_repository_mode=lyrics_repository_mode(),
        compliance_repository_mode=compliance_repository.mode,
        compliance_registry_available=len(compliance_repository.list_models()) > 0,
        compliance_preflight_available=True,
        voice_lab_available=True,
        music_router_available=True,
        music_router_mode="mock",
        available_music_intents=[intent.value for intent in MusicIntentKind],
        soundgraph_writer_available=True,
        export_pack_available=True,
        library_repository_mode=project_library.mode,
        dropbox_sync_available=True,
        dropbox_sync_provider_mode=dropbox_sync_provider.name,
        release_pack_available=True,
        release_repository_mode=release_pack_repository.mode,
        auth_enabled=get_api_key() is not None,
        auth_mode="api_key" if get_api_key() is not None else "open",
        job_queue_available=True,
        job_queue_mode=job_queue.mode,
        async_jobs_available=True,
        artifact_storage_available=True,
        artifact_storage_mode=artifact_storage.mode,
        artifact_registry_mode=get_artifact_registry_mode(),
        artifact_access_mode=get_artifact_access_mode(),
        soundcloud_publish_available=True,
        soundcloud_provider_mode=soundcloud_publish_provider.name,
        merch_capsules_available=True,
        merch_provider_mode="mock",
        merch_repository_mode=merch_capsule_repository.mode,
        ditto_distribution_available=True,
        distribution_provider_mode="mock",
        distribution_repository_mode=distribution_repository.mode,
        shopify_drafts_available=True,
        shopify_provider_mode=shopify_draft_provider.name,
        shopify_live_draft_sync_available=shopify_supports_live_sync(shopify_draft_provider),
        printful_sync_available=True,
        printful_provider_mode=printful_sync_provider.name,
        printful_live_product_sync_available=printful_supports_live_sync(printful_sync_provider),
        commerce_sync_dashboard_available=True,
        commerce_sync_audit_available=True,
        commerce_sync_audit_mode=get_commerce_sync_audit_mode().value,
        newsletter_subscribe_available=True,
        newsletter_listmonk_configured=_listmonk_is_configured(),
        tiktok_shop_available=True,
        tiktok_shop_provider_mode=tiktok_shop_provider.name,
        campaign_os_available=True,
        campaign_repository_mode=campaign_repository.mode,
        campaign_automation_rules_available=True,
        campaign_automation_templates_available=True,
        release_command_center_available=True,
        automation_execution_boundary_available=True,
        automation_execution_mode=automation_execution_mode().value,
        automation_execution_repository_mode=(get_automation_execution_repository_mode().value),
        automation_execution_audit_available=True,
        automation_execution_audit_mode=get_automation_execution_audit_mode().value,
        vinyl_releases_available=True,
        vinyl_provider_mode="manual_handoff",
        vinyl_repository_mode=vinyl_repository.mode,
        analytics_graph_available=True,
        analytics_repository_mode=analytics_repository.mode,
        intelligence_engine_available=True,
        intelligence_snapshots_available=True,
        intelligence_snapshot_repository_mode=intelligence_snapshot_repository.mode,
        provider_connector_framework_available=True,
        mock_platform_connectors_available=True,
        connector_import_audit_available=True,
    )


@app.post("/v1/prompts/compile")
async def compile_prompt_route(
    request: CompiledPromptRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CompiledPrompt:
    return compile_prompt(request)


@app.post("/v1/generations")
async def create_generation(
    request: GenerationRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> GenerationJob:
    compiled = compile_prompt(
        CompiledPromptRequest(
            intent=request.intent,
            prompt_modules=request.prompt_modules,
            character_code=request.character_code,
            lyrics=request.lyrics,
            technical=request.technical,
            tempo=request.tempo,
            druck=request.druck,
            requested_effects=request.requested_effects,
            target_lane=request.target_lane,
            locked_lanes=request.locked_lanes,
        )
    )

    job = job_repository.create(request, compiled)

    if request.safety.allow_voice_likeness:
        job_repository.set_error(job.id, "voice_likeness_requires_explicit_clearance")
        return job_repository.update_status(
            job.id,
            JobStatus.PREFLIGHT_BLOCKED,
            progress=0,
            event_type=JobEventType.PREFLIGHT_BLOCKED,
        )

    # MVP scaffold: run the selected provider inline. Real engines should move into workers.
    provider = provider_registry.select(request.engine)
    job_repository.append_event(
        job.id,
        JobEventType.WORKER_ASSIGNED,
        detail=f"provider:{provider.name}",
    )
    job_repository.update_status(job.id, JobStatus.RUNNING, 0.35, JobEventType.GENERATION_STARTED)

    start_result = await provider.start(request, compiled)
    provider_status = await provider.get_status(start_result.external_job_id)

    if provider_status.status == "failed":
        job_repository.set_error(
            job.id,
            provider_status.error or "provider_generation_failed",
        )
        return job_repository.update_status(
            job.id, JobStatus.FAILED, provider_status.progress, JobEventType.JOB_FAILED
        )

    if provider_status.artifacts is not None:
        job_repository.set_artifacts(job.id, provider_status.artifacts)

    job_repository.update_status(
        job.id, JobStatus.ANALYZING_SAFETY, 0.8, JobEventType.SAFETY_STARTED
    )
    return job_repository.update_status(
        job.id, JobStatus.EXPORT_READY, 1.0, JobEventType.ARTIFACT_READY
    )


@app.get("/v1/generations/{job_id}")
async def get_generation(job_id: UUID) -> GenerationJob:
    job = job_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="generation_not_found")
    return job


@app.post("/v1/masters")
async def create_master(
    request: MasterBusRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MasterBusJob:
    generation = job_repository.get(request.generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="generation_not_found")
    if generation.status is not JobStatus.EXPORT_READY:
        raise HTTPException(status_code=409, detail="generation_not_ready_for_mastering")

    job = master_repository.create(request)

    if reference_clearance_missing(request):
        master_repository.set_error(job.id, "reference_track_uri_required")
        return master_repository.update_status(
            job.id, MasterJobStatus.REFERENCE_BLOCKED, progress=0
        )

    master_repository.update_status(job.id, MasterJobStatus.RUNNING, 0.4)
    manifest = await master_provider.master(request, generation)
    master_repository.set_manifest(job.id, manifest)
    return master_repository.update_status(job.id, MasterJobStatus.EXPORT_READY, 1.0)


@app.get("/v1/masters/{job_id}")
async def get_master(job_id: UUID) -> MasterBusJob:
    job = master_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="master_not_found")
    return job


@app.post("/v1/lyrics/prompts/compile")
async def compile_lyrics_prompt_route(
    request: LyricsGenerationRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CompiledLyricsPrompt:
    return compile_lyrics_prompt(request)


@app.post("/v1/lyrics/generations")
async def create_lyrics(
    request: LyricsGenerationRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsVersion:
    project = lyrics_repository.create_project(
        project_key=request.project_key,
        title=request.title,
        character_code=request.character_code,
    )
    structure = await lyrics_provider.generate(request)
    return lyrics_repository.add_version(
        project_id=project.id,
        structure=structure,
        parent_version_id=None,
        edit_summary=None,
    )


@app.post("/v1/lyrics/edits")
async def edit_lyrics(
    request: LyricsEditRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsVersion:
    current = lyrics_repository.get_version(request.version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    edited = await lyrics_provider.edit(current.structure, request)
    return lyrics_repository.add_version(
        project_id=current.project_id,
        structure=edited,
        parent_version_id=current.id,
        edit_summary=request.edit_prompt,
    )


@app.post("/v1/lyrics/manual-updates")
async def manual_update_lyrics(
    request: LyricsManualUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsVersion:
    current = lyrics_repository.get_version(request.version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    if request.section_index >= len(current.structure.sections):
        raise HTTPException(status_code=400, detail="section_index_out_of_range")
    updated = lyrics_provider.apply_manual_update(
        current=current.structure,
        section_index=request.section_index,
        new_lines=request.lines,
        lock=request.lock,
        notes=request.notes,
    )
    return lyrics_repository.add_version(
        project_id=current.project_id,
        structure=updated,
        parent_version_id=current.id,
        edit_summary=f"manual update section {request.section_index}",
    )


@app.post("/v1/lyrics/selections")
async def rewrite_lyrics_selection(
    request: LyricsRewriteSelectionRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsRewriteResponse:
    current = lyrics_repository.get_version(request.version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    if request.section_index >= len(current.structure.sections):
        raise HTTPException(status_code=400, detail="section_index_out_of_range")
    section = current.structure.sections[request.section_index]
    if request.line_end_index < request.line_start_index:
        raise HTTPException(status_code=400, detail="line_range_invalid")
    if request.line_end_index >= len(section.lines):
        raise HTTPException(status_code=400, detail="line_range_out_of_range")
    variants = await lyrics_provider.rewrite_selection(current.structure, request)
    return LyricsRewriteResponse(
        section_index=request.section_index,
        line_start_index=request.line_start_index,
        line_end_index=request.line_end_index,
        variants=variants,
    )


@app.get("/v1/lyrics/versions/{version_id}")
async def get_lyrics_version(version_id: UUID) -> LyricsVersion:
    version = lyrics_repository.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    return version


@app.post("/v1/lyrics/versions/{version_id}/export")
async def export_lyrics_version(
    version_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsExportManifest:
    version = lyrics_repository.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    project = lyrics_repository.get_project(version.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="lyrics_project_not_found")

    base = f"/tmp/snuffraga/{project.project_key}/lyrics/v{version.version}"
    vocal_notes: list[VocalPerformanceNote] = []
    section_index_map: dict[str, int] = {}
    for section in version.structure.sections:
        section_index_map[section.label] = section.index
        if section.section_type is LyricsSectionType.INSTRUMENTAL_OPENING:
            vocal_notes.append(
                VocalPerformanceNote(
                    section_index=section.index,
                    note="vocal_entry=false (instrumental opening)",
                )
            )
        elif section.section_type is LyricsSectionType.DUB_BREAKDOWN:
            vocal_notes.append(
                VocalPerformanceNote(
                    section_index=section.index,
                    note="vocal_entry=false (dub breakdown · delay throws only)",
                )
            )
        else:
            vocal_notes.append(
                VocalPerformanceNote(
                    section_index=section.index,
                    note=f"vocal_entry=true · lane=vocals_main · source={section.source.value}",
                )
            )

    return LyricsExportManifest(
        version_id=version.id,
        project_id=project.id,
        lyrics_txt_path=f"{base}/lyrics.txt",
        lyrics_json_path=f"{base}/lyrics.json",
        vocal_notes=vocal_notes,
        section_index_map=section_index_map,
        safety_report_json_path=f"{base}/safety_report.json",
    )


@app.get("/v1/lyrics/projects")
async def list_lyrics_projects() -> list[LyricsProject]:
    return lyrics_repository.list_projects()


@app.get("/v1/lyrics/projects/{project_key}")
async def get_lyrics_project(project_key: str) -> LyricsProject:
    project = lyrics_repository.get_project_by_key(project_key)
    if project is None:
        raise HTTPException(status_code=404, detail="lyrics_project_not_found")
    return project


@app.get("/v1/lyrics/projects/{project_key}/versions")
async def list_lyrics_versions(project_key: str) -> list[LyricsVersion]:
    project = lyrics_repository.get_project_by_key(project_key)
    if project is None:
        raise HTTPException(status_code=404, detail="lyrics_project_not_found")
    return lyrics_repository.list_versions(project.id)


@app.get("/v1/lyrics/projects/{project_key}/versions/{version_number}")
async def get_lyrics_version_by_number(project_key: str, version_number: int) -> LyricsVersion:
    project = lyrics_repository.get_project_by_key(project_key)
    if project is None:
        raise HTTPException(status_code=404, detail="lyrics_project_not_found")
    for version in lyrics_repository.list_versions(project.id):
        if version.version == version_number:
            return version
    raise HTTPException(status_code=404, detail="lyrics_version_not_found")


@app.post("/v1/lyrics/versions/{version_id}/sections/{section_index}/lock")
async def toggle_lyrics_section_lock(
    version_id: UUID,
    section_index: int,
    request: LyricsLockToggleRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsVersion:
    current = lyrics_repository.get_version(version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    if section_index < 0 or section_index >= len(current.structure.sections):
        raise HTTPException(status_code=400, detail="section_index_out_of_range")
    updated_structure = lyrics_provider.apply_lock_toggle(
        current.structure, section_index, request.locked
    )
    summary = (
        f"lock section {section_index}" if request.locked else f"unlock section {section_index}"
    )
    return lyrics_repository.add_version(
        project_id=current.project_id,
        structure=updated_structure,
        parent_version_id=current.id,
        edit_summary=summary,
    )


@app.post("/v1/lyrics/versions/{version_id}/apply-selection-rewrite")
async def apply_selection_rewrite(
    version_id: UUID,
    request: LyricsApplySelectionRewriteRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LyricsVersion:
    current = lyrics_repository.get_version(version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")
    if request.section_index < 0 or request.section_index >= len(current.structure.sections):
        raise HTTPException(status_code=400, detail="section_index_out_of_range")
    section = current.structure.sections[request.section_index]
    if section.locked:
        raise HTTPException(status_code=409, detail="section_locked")

    updated_structure = lyrics_provider.apply_selection_rewrite(
        current.structure,
        section_index=request.section_index,
        new_lines=request.lines,
        lock=request.lock,
    )
    summary = (
        request.summary
        if request.summary is not None
        else f"apply selection rewrite section {request.section_index}"
    )
    return lyrics_repository.add_version(
        project_id=current.project_id,
        structure=updated_structure,
        parent_version_id=current.id,
        edit_summary=summary,
    )


# ---------- Compliance Foundation (S10) ----------


@app.get("/v1/compliance/summary")
async def compliance_summary() -> ComplianceRegistrySummary:
    return compliance_repository.summary()


@app.get("/v1/compliance/models")
async def list_compliance_models() -> list[ModelRegistryEntry]:
    return compliance_repository.list_models()


@app.get("/v1/compliance/licenses")
async def list_compliance_licenses() -> list[LicenseRegistryEntry]:
    return compliance_repository.list_licenses()


@app.post("/v1/compliance/licenses")
async def create_compliance_license(
    request: LicenseRegistryCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> LicenseRegistryEntry:
    return compliance_repository.create_license(request)


@app.get("/v1/compliance/consent-records")
async def list_compliance_consent_records() -> list[ConsentRecord]:
    return compliance_repository.list_consent_records()


@app.post("/v1/compliance/consent-records")
async def create_compliance_consent_record(
    request: ConsentRecordCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ConsentRecord:
    return compliance_repository.create_consent_record(request)


@app.get("/v1/compliance/provenance")
async def list_compliance_provenance(
    artifact_id: UUID | None = None,
) -> list[OutputProvenance]:
    if artifact_id is not None:
        return compliance_repository.list_provenance_for_artifact(artifact_id)
    return compliance_repository.list_provenance()


@app.post("/v1/compliance/provenance")
async def create_compliance_provenance(
    request: OutputProvenanceCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> OutputProvenance:
    return compliance_repository.create_provenance(request)


@app.get("/v1/compliance/audit-events")
async def list_compliance_audit_events() -> list[AuditEvent]:
    return compliance_repository.list_audit_events()


@app.post("/v1/compliance/audit-events")
async def create_compliance_audit_event(
    request: AuditEventCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AuditEvent:
    return compliance_repository.create_audit_event(request)


@app.post("/v1/compliance/preflight")
async def compliance_preflight(
    request: CompliancePreflightRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CompliancePreflightResult:
    return evaluate_preflight(
        request,
        compliance_repository.list_consent_records(),
    )


@app.get("/v1/compliance/release-eligibility/{artifact_id}")
async def compliance_release_eligibility(
    artifact_id: UUID,
) -> ReleaseEligibilityResult:
    candidates = compliance_repository.list_provenance_for_artifact(artifact_id)
    if not candidates:
        raise HTTPException(status_code=404, detail="provenance_not_found")
    provenance = candidates[0]
    return evaluate_release_eligibility(
        provenance,
        compliance_repository.list_licenses(),
        compliance_repository.list_consent_records(),
    )


# ---------- Voice Lab (S11) ----------


@app.get("/v1/voice-lab/summary")
async def voice_lab_summary() -> VoiceLabSummary:
    return voice_lab_repository.summary()


@app.get("/v1/voice-lab/tags")
async def list_voice_tags() -> list[VoiceTag]:
    return voice_lab_repository.list_tags()


@app.post("/v1/voice-lab/tags")
async def create_voice_tag(
    request: VoiceTagCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> VoiceTag:
    # Validate consent record exists
    consent = compliance_repository.get_consent_record(request.consent_id)
    if consent is None:
        raise HTTPException(status_code=404, detail="consent_record_not_found")
    if consent.revoked_at is not None:
        raise HTTPException(status_code=409, detail="consent_record_revoked")
    return voice_lab_repository.create_tag(request)


@app.get("/v1/voice-lab/jobs")
async def list_voice_jobs() -> list[VoiceJob]:
    return voice_lab_repository.list_jobs()


@app.get("/v1/voice-lab/jobs/{job_id}")
async def get_voice_job(job_id: UUID) -> VoiceJob:
    job = voice_lab_repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="voice_job_not_found")
    return job


@app.post("/v1/voice-lab/jobs")
async def create_voice_job_route(
    request: VoiceJobCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> VoiceJob:
    return run_voice_job(request, voice_lab_repository, compliance_repository)


@app.post("/v1/compliance/consent-records/{consent_id}/revoke")
async def revoke_consent_record(
    consent_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ConsentRecord:
    result = compliance_repository.revoke_consent_record(consent_id)
    if result is None:
        raise HTTPException(status_code=404, detail="consent_record_not_found")
    return result


# ---------- Music Provider Router (S12) ----------


@app.get("/v1/music-router/summary")
async def music_router_summary() -> MusicRouterSummary:
    return music_router_repository.summary()


@app.post("/v1/music-router/jobs")
async def create_music_job(
    request: MusicGenerationRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MusicJob:
    job = run_music_job(request, music_router_repository, compliance_repository)
    # S28: bridge completed jobs to artifact storage
    record_artifacts_for_music_job(job, artifact_storage, operator_id=operator.operator_id)
    return job


@app.get("/v1/music-router/jobs")
async def list_music_jobs() -> list[MusicJob]:
    return music_router_repository.list_jobs()


@app.get("/v1/music-router/jobs/{job_id}")
async def get_music_job(job_id: UUID) -> MusicJob:
    job = music_router_repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="music_job_not_found")
    return job


@app.get("/v1/music-router/jobs/{job_id}/artifacts")
async def get_music_job_artifacts(job_id: UUID) -> list[MusicArtifactManifest]:
    job = music_router_repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="music_job_not_found")
    return job.artifacts


# ---------- SoundGraph Manifest Writer (S14) ----------


@app.post("/v1/soundgraph/compile")
async def compile_soundgraph_route(
    request: SoundGraphWriteRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> SoundGraphWriteResult:
    """Compile a LyricsVersion into a SoundGraphArrangement.

    This is the bridge: lyrics text → editable production structure.
    """
    version = lyrics_repository.get_version(request.lyrics_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="lyrics_version_not_found")

    result = compile_soundgraph(version, request)
    soundgraph_repository.store(result.arrangement)
    # S28: bridge arrangement to artifact storage
    record_artifact_for_soundgraph(
        result.arrangement, artifact_storage, operator_id=operator.operator_id
    )
    return result


@app.get("/v1/soundgraph/arrangements/{arrangement_id}")
async def get_soundgraph_arrangement(
    arrangement_id: UUID,
) -> SoundGraphArrangement:
    arrangement = soundgraph_repository.get(arrangement_id)
    if arrangement is None:
        raise HTTPException(status_code=404, detail="arrangement_not_found")
    return arrangement


@app.get("/v1/soundgraph/by-lyrics-version/{lyrics_version_id}")
async def get_soundgraph_by_lyrics_version(
    lyrics_version_id: UUID,
) -> SoundGraphArrangement:
    arrangement = soundgraph_repository.get_by_lyrics_version(lyrics_version_id)
    if arrangement is None:
        raise HTTPException(status_code=404, detail="arrangement_not_found")
    return arrangement


@app.get("/v1/soundgraph/arrangements")
async def list_soundgraph_arrangements() -> list[SoundGraphArrangement]:
    return soundgraph_repository.list_all()


# ---------- SoundGraph → Music Router Handoff (S15) ----------


@app.post("/v1/soundgraph/handoff")
async def soundgraph_handoff_route(
    request: SoundGraphHandoffRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> SoundGraphHandoffResult:
    """Hand off a SoundGraphArrangement to the Music Router.

    Closes the loop: Lyrics → SoundGraph → Music Job → Artifacts.
    """
    arrangement = soundgraph_repository.get(request.arrangement_id)
    if arrangement is None:
        raise HTTPException(status_code=404, detail="arrangement_not_found")

    # Resolve intent and build prompt for transparency
    resolved_intent = request.intent_override or resolve_intent_from_arrangement(arrangement)
    requested_lanes = extract_requested_lanes(arrangement)
    locked_lanes = extract_locked_lanes(arrangement)
    duration = estimate_duration_seconds(arrangement)
    prompt = compile_handoff_prompt(arrangement)

    # Execute the handoff through the music router
    music_job = execute_handoff(
        arrangement,
        music_router_repository,
        compliance_repository,
        title=request.title,
        operator_id=operator.operator_id,
        commercial_target=request.commercial_target,
        intent_override=request.intent_override,
    )

    return SoundGraphHandoffResult(
        music_job=music_job,
        resolved_intent=resolved_intent,
        requested_lanes=requested_lanes,
        locked_lanes=locked_lanes,
        estimated_duration_seconds=duration,
        compiled_prompt=prompt,
    )


# ---------- Export Pack / Project Library (S17) ----------


@app.post("/v1/library/packs")
async def create_export_pack(
    request: ExportPackCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ExportPack:
    """Create an export pack from a completed music job.

    Bundles the job + artifacts + lyrics + soundgraph + provenance
    into a single exportable project pack.
    """
    music_job = music_router_repository.get_job(request.music_job_id)
    if music_job is None:
        raise HTTPException(status_code=404, detail="music_job_not_found")

    # Resolve linked lyrics version (if the job came from a lyrics project)
    lyrics_version: LyricsVersion | None = None
    if music_job.router_decision and music_job.router_decision.provenance_id:
        # Try to find lyrics via soundgraph → lyrics_version_id chain
        for arr in soundgraph_repository.list_all():
            if arr.arrangement_id == request.music_job_id:
                break
            # Check if any arrangement's handoff produced this job
        pass

    # Find arrangement that sourced this job (by scanning)
    arrangement: SoundGraphArrangement | None = None
    for arr in soundgraph_repository.list_all():
        # The handoff creates a job from an arrangement — we match by BPM
        # and key as a heuristic since we don't store the reverse link yet.
        # A better approach: check all arrangements and find one whose
        # lyrics_version_id matches the job's lyrics metadata.
        if music_job.router_decision:
            arrangement = arr
            # Pick the most recent arrangement (list is newest-first)
            break

    # If we found an arrangement, look up the lyrics version
    if arrangement is not None:
        lyrics_version = lyrics_repository.get_version(arrangement.lyrics_version_id)

    # Look up provenance
    provenance: OutputProvenance | None = None
    if music_job.provenance_id:
        candidates = compliance_repository.list_provenance()
        for p in candidates:
            if p.provenance_id == music_job.provenance_id:
                provenance = p
                break

    pack = build_export_pack(
        music_job,
        lyrics_version=lyrics_version,
        arrangement=arrangement,
        provenance=provenance,
        title=request.title,
        operator_id=operator.operator_id,
        notes=request.notes,
    )
    project_library.store_pack(pack)

    entry = build_library_entry(pack)
    project_library.store_entry(entry)

    # S28: bridge export pack components to artifact storage
    record_artifacts_for_export_pack(pack, artifact_storage, operator_id=operator.operator_id)

    return pack


@app.get("/v1/library/packs/{pack_id}")
async def get_export_pack(pack_id: UUID) -> ExportPack:
    pack = project_library.get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="export_pack_not_found")
    return pack


@app.get("/v1/library/entries")
async def list_library_entries() -> list[ProjectLibraryEntry]:
    return project_library.list_entries()


@app.get("/v1/library/entries/{entry_id}")
async def get_library_entry(entry_id: UUID) -> ProjectLibraryEntry:
    entry = project_library.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="library_entry_not_found")
    return entry


@app.get("/v1/library/summary")
async def library_summary() -> ProjectLibrarySummary:
    return project_library.summary()


# ---------- Dropbox Export Sync (S20) ----------


@app.post("/v1/dropbox/plans")
async def create_dropbox_export_plan(
    request: DropboxExportPlanCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DropboxExportPlan:
    """Create a Dropbox folder plan from a pack.

    Deterministic: same pack always produces the same structure.
    """
    pack = project_library.get_pack(request.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="export_pack_not_found")

    plan = build_export_plan(pack, target_root_override=request.target_root_override)
    dropbox_sync_repository.store_plan(plan)

    # Auto-create sync job in PLANNED status
    job = create_sync_job(plan, operator_id=operator.operator_id)
    dropbox_sync_repository.store_job(job)

    return plan


@app.get("/v1/dropbox/plans/{plan_id}")
async def get_dropbox_plan(plan_id: UUID) -> DropboxExportPlan:
    plan = dropbox_sync_repository.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="dropbox_plan_not_found")
    return plan


@app.get("/v1/dropbox/plans/by-pack/{pack_id}")
async def get_dropbox_plan_by_pack(pack_id: UUID) -> DropboxExportPlan:
    plan = dropbox_sync_repository.get_plan_by_pack(pack_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="dropbox_plan_not_found")
    return plan


@app.get("/v1/dropbox/jobs")
async def list_dropbox_jobs() -> list[DropboxSyncJob]:
    return dropbox_sync_repository.list_jobs()


@app.get("/v1/dropbox/jobs/{sync_id}")
async def get_dropbox_job(sync_id: UUID) -> DropboxSyncJob:
    job = dropbox_sync_repository.get_job(sync_id)
    if job is None:
        raise HTTPException(status_code=404, detail="dropbox_sync_job_not_found")
    return job


@app.post("/v1/dropbox/jobs/{sync_id}/ready")
async def mark_dropbox_job_ready(
    sync_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DropboxSyncJob:
    """Mark a sync job as READY_FOR_SYNC.

    In S21 this will validate Dropbox auth. For now, always succeeds.
    """
    job = dropbox_sync_repository.get_job(sync_id)
    if job is None:
        raise HTTPException(status_code=404, detail="dropbox_sync_job_not_found")
    updated = mark_ready_for_sync(job)
    dropbox_sync_repository.update_job(updated)
    return updated


@app.post("/v1/dropbox/jobs/{sync_id}/execute")
async def execute_dropbox_sync(
    sync_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DropboxSyncJob:
    """Execute the Dropbox sync via the configured provider.

    Job must be in READY_FOR_SYNC status. Provider is selected by
    SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER (mock | dropbox).
    """
    job = dropbox_sync_repository.get_job(sync_id)
    if job is None:
        raise HTTPException(status_code=404, detail="dropbox_sync_job_not_found")
    plan = dropbox_sync_repository.get_plan(job.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="dropbox_plan_not_found")
    updated = await dropbox_sync_provider.execute_sync(job, plan)
    dropbox_sync_repository.update_job(updated)
    return updated


@app.get("/v1/dropbox/summary")
async def dropbox_sync_summary() -> DropboxSyncSummary:
    return dropbox_sync_repository.summary()


# ---------- Release Pack (S22) ----------


@app.post("/v1/releases")
async def create_release_pack(
    request: ReleasePackCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ReleasePack:
    """Create a release pack from an existing library pack."""
    pack = project_library.get_pack(request.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="pack_not_found")
    release = build_release_pack(pack, request)
    release_pack_repository.store(release)
    # S28: bridge release pack to artifact storage
    record_artifacts_for_release_pack(release, artifact_storage, operator_id=operator.operator_id)
    return release


@app.get("/v1/releases")
async def list_releases() -> list[ReleasePack]:
    return release_pack_repository.list_all()


@app.get("/v1/releases/{release_id}")
async def get_release(release_id: UUID) -> ReleasePack:
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return release


@app.get("/v1/releases/by-pack/{pack_id}")
async def get_release_by_pack(pack_id: UUID) -> ReleasePack:
    release = release_pack_repository.get_by_pack(pack_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return release


@app.post("/v1/releases/{release_id}/checklist/{code}")
async def update_release_checklist(
    release_id: UUID,
    code: str,
    operator: Annotated[Operator, Depends(require_operator)],
    passed: bool = True,
    notes: str | None = None,
) -> ReleasePack:
    """Update a compliance checklist item on a release pack."""
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    try:
        updated = update_checklist_item(release, code, passed, notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    release_pack_repository.update(updated)
    return updated


@app.post("/v1/releases/{release_id}/ready")
async def mark_release_pack_ready(
    release_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ReleasePack:
    """Mark a release pack as READY (requires compliance_passed=True)."""
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    try:
        updated = mark_release_ready(release)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    release_pack_repository.update(updated)
    return updated


@app.get("/v1/releases/summary")
async def release_summary() -> ReleasePackSummary:
    return release_pack_repository.summary()


# ---------- Cover Asset Upload (S31) ----------


@app.post("/v1/releases/{release_id}/assets/cover")
async def upload_release_cover(
    release_id: UUID,
    request: CoverAssetUploadRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CoverAssetUploadResult:
    """Upload cover artwork for a release pack.

    Accepts PNG/JPG via base64. Validates content type, size (max 20 MB),
    dimensions (min 1400x1400 px, square required). Stores through
    ArtifactStorage and attaches to the release pack's cover_art
    asset placeholder.
    """
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    try:
        result = upload_cover_for_release(
            release=release,
            request=request,
            storage=artifact_storage,
            operator_id=operator.operator_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Persist the updated release
    release_pack_repository.update(result.release)

    return result


# ---------- Audio Master Upload (S32) ----------


@app.post("/v1/releases/{release_id}/assets/audio-master")
async def upload_release_audio_master(
    release_id: UUID,
    request: AudioMasterUploadRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AudioMasterUploadResult:
    """Upload a WAV audio master for a release pack.

    Accepts WAV via base64. Validates content type, size (max 120 MB),
    WAV header (channels, sample rate, bit depth, duration). Stores
    through ArtifactStorage and attaches to the release pack's
    audio_master asset placeholder.

    Note: This uses base64 JSON upload suitable for small/medium WAV files.
    Large masters will require a future chunked upload endpoint.
    """
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    try:
        result = upload_audio_master_for_release(
            release=release,
            request=request,
            storage=artifact_storage,
            operator_id=operator.operator_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Persist the updated release
    release_pack_repository.update(result.release)

    return result


# ---------- Stem Pack Upload (S33) ----------


@app.post("/v1/releases/{release_id}/assets/stems")
async def upload_release_stem_pack(
    release_id: UUID,
    request: StemPackUploadRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> StemPackUploadResult:
    """Upload a stem pack ZIP for a release pack.

    Accepts ZIP via base64. Validates content type, size (max 250 MB),
    ZIP structure (no path traversal, no encrypted entries, max 64 files,
    max 1 GB uncompressed, allowed extensions only). Stores through
    ArtifactStorage and attaches to the release pack's stems_archive
    asset placeholder.

    Note: This uses base64 JSON upload suitable for small/medium ZIP files.
    Large stem packs will require a future multipart/chunked upload endpoint.
    """
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    try:
        result = upload_stem_pack_for_release(
            release=release,
            request=request,
            storage=artifact_storage,
            operator_id=operator.operator_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Persist the updated release
    release_pack_repository.update(result.release)

    return result


# ---------- Release Export (S34) ----------


@app.post("/v1/releases/{release_id}/export")
async def build_release_export(
    release_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ReleaseExportResult:
    """Build a release export ZIP bundle from uploaded assets.

    Collects all available assets (cover art, audio master, stem pack),
    bundles them with release metadata, social copy, and a manifest
    into a downloadable ZIP stored through ArtifactStorage.

    Partial exports are allowed (warnings for missing assets).
    Fails if no assets are uploaded at all.

    Note: This does not publish or distribute — it only builds the bundle.
    """
    release = release_pack_repository.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    try:
        result = build_release_export_zip(
            release=release,
            storage=artifact_storage,
            operator_id=operator.operator_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return result


# ---------- Async Jobs (S26) ----------


@app.post("/v1/jobs")
async def create_async_job(
    request: AsyncJobCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AsyncJob:
    """Enqueue a new async job."""
    return job_queue.enqueue(request, operator_id=operator.operator_id)


@app.get("/v1/jobs")
async def list_async_jobs(
    kind: AsyncJobKind | None = None,
) -> list[AsyncJob]:
    """List all async jobs, optionally filtered by kind."""
    return job_queue.list_all(kind=kind)


@app.get("/v1/jobs/summary")
async def async_job_summary() -> AsyncJobSummary:
    """Return a summary of async job counts by status."""
    return job_queue.summary()


@app.get("/v1/jobs/{job_id}")
async def get_async_job(job_id: UUID) -> AsyncJob:
    """Get a single async job by ID."""
    job = job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="async_job_not_found")
    return job


@app.post("/v1/jobs/{job_id}/cancel")
async def cancel_async_job(
    job_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AsyncJob:
    """Cancel a queued or running async job."""
    result = job_queue.cancel(job_id)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="async_job_not_cancellable",
        )
    return result


@app.post("/v1/jobs/{job_id}/run-once")
async def run_async_job_once(
    job_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AsyncJob:
    """Execute a specific queued job synchronously (dev/test)."""
    result = run_job_by_id(job_queue, job_id)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="async_job_not_runnable",
        )
    return result


# ---------- Artifact Storage (S27) ----------


@app.post("/v1/artifacts")
async def create_artifact(
    request: ArtifactCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ArtifactRecord:
    """Register a new artifact (metadata only, no bytes yet)."""
    return artifact_storage.create_record(request, operator_id=operator.operator_id)


@app.get("/v1/artifacts")
async def list_artifacts(
    kind: ArtifactKind | None = None,
) -> list[ArtifactRecord]:
    """List all registered artifacts, optionally filtered by kind."""
    return artifact_storage.list_records(kind=kind)


@app.get("/v1/artifacts/summary")
async def artifact_summary() -> ArtifactStorageSummary:
    """Return a summary of artifact storage state."""
    return artifact_storage.summary()


@app.get("/v1/artifacts/{artifact_id}")
async def get_artifact(artifact_id: UUID) -> ArtifactRecord:
    """Get a single artifact record by ID."""
    record = artifact_storage.get_record(artifact_id)
    if record is None:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return record


@app.post("/v1/artifacts/{artifact_id}/bytes")
async def upload_artifact_bytes(
    artifact_id: UUID,
    request: ArtifactUploadRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ArtifactRecord:
    """Upload bytes for a registered artifact (base64-encoded)."""
    record = artifact_storage.get_record(artifact_id)
    if record is None:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    try:
        data = decode_upload_content(request.content_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        return artifact_storage.store_bytes(artifact_id, data, content_type=request.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/v1/artifacts/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    token: str | None = None,
    expires: str | None = None,
) -> RawResponse:
    """Download the stored bytes for an artifact.

    Returns the raw file content with appropriate content-type.
    For local storage, reads from the artifact root directory.

    In signed mode, a valid token is required (query params `token` + `expires`).
    In direct mode, no token is needed (backward compatible).
    """
    # S29: validate download token if in signed mode
    is_valid, error_msg = validate_token(artifact_id, token, expires)
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_msg)

    record = artifact_storage.get_record(artifact_id)
    if record is None:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    if record.status != "stored":
        raise HTTPException(
            status_code=409,
            detail=f"artifact_status_{record.status}",
        )

    # For local storage, read from disk
    if isinstance(artifact_storage, LocalArtifactStorage):
        file_path = artifact_storage.get_file_path(artifact_id)
        if file_path is None or not file_path.exists():
            raise HTTPException(status_code=404, detail="artifact_file_missing")
        content = file_path.read_bytes()
        return RawResponse(
            content=content,
            media_type=record.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_path.name}"',
            },
        )

    # For other storage modes (future S3), return link info
    link = artifact_storage.get_download_link(artifact_id)
    if link is None:
        raise HTTPException(status_code=404, detail="artifact_download_unavailable")
    raise HTTPException(
        status_code=307,
        headers={"Location": link.url},
    )


@app.get("/v1/artifacts/{artifact_id}/download-link")
async def get_artifact_download_link(artifact_id: UUID) -> ArtifactSignedUrl:
    """Get a download URL for an artifact.

    In direct mode: returns a plain route URL.
    In signed mode: returns a signed URL with HMAC token.
    """
    record = artifact_storage.get_record(artifact_id)
    if record is None:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    if record.status != "stored":
        raise HTTPException(
            status_code=409,
            detail=f"artifact_status_{record.status}",
        )
    return generate_download_url(artifact_id)


# ---------- SoundCloud Publishing (S36) ----------


@app.post("/v1/soundcloud/preview")
async def soundcloud_preview(
    request: SoundCloudPublishRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> SoundCloudPublishPreview:
    """Build a SoundCloud publish preview from a ReleasePack.

    Returns metadata, warnings, and publish eligibility.
    """
    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return soundcloud_publish_provider.create_publish_preview(release)


@app.post("/v1/soundcloud/jobs")
async def create_soundcloud_job(
    request: SoundCloudPublishRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> SoundCloudPublishJob:
    """Create a SoundCloud publish job from a ReleasePack.

    Builds metadata, checks eligibility, stores the job.
    """
    from uuid import uuid4 as _uuid4

    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    preview = soundcloud_publish_provider.create_publish_preview(release)

    status = (
        SoundCloudPublishStatus.READY if preview.can_publish else SoundCloudPublishStatus.BLOCKED
    )
    error = preview.blocked_reason if not preview.can_publish else None

    job = SoundCloudPublishJob(
        job_id=_uuid4(),
        release_id=request.release_id,
        status=status,
        metadata=preview.metadata,
        warnings=preview.warnings,
        provider_mode=soundcloud_publish_provider.name,
        operator_id=operator.operator_id,
        error=error,
    )
    soundcloud_publish_repository.store(job)
    return job


@app.get("/v1/soundcloud/jobs")
async def list_soundcloud_jobs() -> list[SoundCloudPublishJob]:
    return soundcloud_publish_repository.list_all()


@app.get("/v1/soundcloud/jobs/{job_id}")
async def get_soundcloud_job(job_id: UUID) -> SoundCloudPublishJob:
    job = soundcloud_publish_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="soundcloud_job_not_found")
    return job


@app.post("/v1/soundcloud/jobs/{job_id}/publish-mock")
async def publish_mock_soundcloud(
    job_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> SoundCloudPublishJob:
    """Execute mock publish on a SoundCloud job.

    Only works in mock provider mode. Real provider returns BLOCKED.
    """
    job = soundcloud_publish_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="soundcloud_job_not_found")
    if job.status == SoundCloudPublishStatus.BLOCKED:
        raise HTTPException(status_code=422, detail="job_blocked: " + (job.error or "blocked"))

    updated = soundcloud_publish_provider.publish(job)
    soundcloud_publish_repository.update(updated)
    return updated


@app.get("/v1/soundcloud/summary")
async def soundcloud_summary() -> SoundCloudPublishSummary:
    return soundcloud_publish_repository.summary()


# ---------------------------------------------------------------------------
# Merch Capsule Contract (S37)
# ---------------------------------------------------------------------------


@app.post("/v1/merch/capsules")
async def create_merch_capsule(
    request: MerchCapsuleCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MerchCapsule:
    """Create a merch capsule from a ReleasePack.

    Builds product suggestions, enforces rules, stores the capsule.
    No real commerce API calls.
    """
    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    capsule = build_merch_capsule_from_release(
        release,
        operator_id=operator.operator_id,
        notes=request.notes,
    )
    merch_capsule_repository.store(capsule)
    return capsule


@app.get("/v1/merch/capsules")
async def list_merch_capsules() -> list[MerchCapsule]:
    return merch_capsule_repository.list_all()


@app.get("/v1/merch/capsules/{capsule_id}")
async def get_merch_capsule(capsule_id: UUID) -> MerchCapsule:
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")
    return capsule


@app.post("/v1/merch/capsules/{capsule_id}/lock")
async def lock_merch_capsule(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MerchCapsule:
    """Lock a merch capsule — prevents further product edits.

    Re-validates rules before locking. Archived capsules cannot be locked.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    if capsule.status == MerchCapsuleStatus.ARCHIVED:
        raise HTTPException(
            status_code=422,
            detail="capsule_archived: archived capsules cannot be locked",
        )

    if capsule.status == MerchCapsuleStatus.LOCKED:
        return capsule  # idempotent

    # Re-validate and store warnings
    from datetime import datetime, timezone

    warnings = enforce_merch_capsule_rules(capsule)
    updated = capsule.model_copy(
        update={
            "status": MerchCapsuleStatus.LOCKED,
            "warnings": warnings,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    merch_capsule_repository.update(updated)
    return updated


@app.post("/v1/merch/capsules/{capsule_id}/export-mock")
async def export_mock_merch_capsule(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MerchExportPayload:
    """Build a mock export payload for a merch capsule.

    No real Printful/TikTok/Shopify API calls. Returns a structured
    payload showing what each provider adapter would receive.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    payload = build_mock_provider_export(capsule)

    # Update capsule status to exported_mock if still draft/locked
    if capsule.status in (MerchCapsuleStatus.DRAFT, MerchCapsuleStatus.LOCKED):
        from datetime import datetime, timezone

        updated = capsule.model_copy(
            update={
                "status": MerchCapsuleStatus.EXPORTED_MOCK,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        merch_capsule_repository.update(updated)

    return payload


@app.get("/v1/merch/summary")
async def merch_summary() -> MerchCapsuleSummary:
    return merch_capsule_repository.summary()


# ---------------------------------------------------------------------------
# Merch Product Editor (S44)
# ---------------------------------------------------------------------------


@app.patch("/v1/merch/capsules/{capsule_id}/products/{product_id}")
async def update_merch_capsule_product(
    capsule_id: UUID,
    product_id: UUID,
    request: MerchProductUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> MerchProductUpdateResult:
    """Update a single product within a merch capsule.

    Partial update — only provided fields are changed. Re-validates
    capsule rules after the update. Locked/archived capsules reject
    updates with 409. Unknown capsule/product returns 404.

    Does NOT auto-rebuild Shopify/Printful/TikTok payloads.
    Provider payloads may become stale after edits.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    if capsule.status in (MerchCapsuleStatus.LOCKED, MerchCapsuleStatus.ARCHIVED):
        raise HTTPException(
            status_code=409,
            detail=f"capsule_{capsule.status.value}: cannot edit products on a {capsule.status.value} capsule",
        )

    result = update_merch_product(capsule, product_id, request)
    if result is None:
        raise HTTPException(status_code=404, detail="merch_product_not_found")

    merch_capsule_repository.update(result.capsule)
    return result


# ---------------------------------------------------------------------------
# Merch Provider Aggregation (S43)
# ---------------------------------------------------------------------------


@app.get("/v1/merch/capsules/{capsule_id}/provider-status")
async def get_merch_provider_status(capsule_id: UUID) -> MerchProviderAggregation:
    """Unified read-only provider status for a merch capsule.

    Aggregates Shopify Draft, Printful Sync, and TikTok Shop Listing
    statuses into a single product-by-provider matrix.

    No real commerce API calls. No inventory mutation. No publishing.
    Operational preview only.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    shopify_drafts = shopify_draft_repository.list_by_capsule(capsule_id)
    printful_syncs = printful_sync_repository.list_by_capsule(capsule_id)
    tiktok_listings = tiktok_shop_repository.list_by_capsule(capsule_id)

    return build_provider_aggregation(
        capsule,
        shopify_drafts=shopify_drafts,
        printful_syncs=printful_syncs,
        tiktok_listings=tiktok_listings,
        shopify_mode=shopify_draft_provider.name,
        printful_mode=printful_sync_provider.name,
        tiktok_mode=tiktok_shop_provider.name,
    )


# ---------------------------------------------------------------------------
# Ditto Music Distribution (S37)
# ---------------------------------------------------------------------------


@app.post("/v1/distribution/packs")
async def create_distribution_pack(
    request: DistributionPackCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DistributionPack:
    """Create a distribution pack from an existing ReleasePack.

    Pre-populates metadata, readiness checklist, and store targets.
    No real Ditto API calls.
    """
    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    pack = build_distribution_pack_from_release(
        release,
        store_targets=request.store_targets or None,
        operator_id=operator.operator_id,
        notes=request.notes,
    )
    distribution_repository.store(pack)
    return pack


@app.get("/v1/distribution/packs")
async def list_distribution_packs() -> list[DistributionPack]:
    return distribution_repository.list_all()


@app.get("/v1/distribution/packs/{distribution_id}")
async def get_distribution_pack(distribution_id: UUID) -> DistributionPack:
    pack = distribution_repository.get(distribution_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="distribution_pack_not_found")
    return pack


@app.post("/v1/distribution/packs/{distribution_id}/status")
async def update_distribution_pack_status(
    distribution_id: UUID,
    request: DistributionPackStatusUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DistributionPack:
    """Manually update distribution pack status.

    Tracks the operator-driven lifecycle: draft → ready → submitted → live.
    Also supports rejected and takedown transitions.
    """
    from datetime import datetime, timezone

    pack = distribution_repository.get(distribution_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="distribution_pack_not_found")

    notes = pack.operator_notes
    if request.notes:
        notes = request.notes if not notes else f"{notes}\n{request.notes}"

    updated = pack.model_copy(
        update={
            "status": request.status,
            "operator_notes": notes,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    distribution_repository.update(updated)
    return updated


@app.post("/v1/distribution/packs/{distribution_id}/readiness/{code}")
async def update_distribution_readiness_item(
    distribution_id: UUID,
    code: str,
    operator: Annotated[Operator, Depends(require_operator)],
) -> DistributionPack:
    """Toggle a readiness checklist item by code.

    Re-evaluates readiness_passed after the toggle.
    """
    from datetime import datetime, timezone

    pack = distribution_repository.get(distribution_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="distribution_pack_not_found")

    found = False
    updated_items = []
    for item in pack.readiness_checklist:
        if item.code == code:
            found = True
            updated_items.append(item.model_copy(update={"passed": not item.passed}))
        else:
            updated_items.append(item)

    if not found:
        raise HTTPException(status_code=404, detail="readiness_item_not_found")

    updated = pack.model_copy(
        update={
            "readiness_checklist": updated_items,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    updated = evaluate_readiness(updated)
    distribution_repository.update(updated)
    return updated


@app.get("/v1/distribution/packs/by-release/{release_id}")
async def get_distribution_pack_by_release(release_id: UUID) -> DistributionPack:
    pack = distribution_repository.get_by_release(release_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="distribution_pack_not_found")
    return pack


@app.get("/v1/distribution/summary")
async def distribution_summary() -> DistributionPackSummary:
    return distribution_repository.summary()


# ---------------------------------------------------------------------------
# Shopify Draft Provider Boundary (S40)
# ---------------------------------------------------------------------------


@app.post("/v1/shopify/drafts/by-capsule/{capsule_id}")
async def build_shopify_drafts(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ShopifyDraftExport:
    """Build Shopify product drafts from a MerchCapsule.

    Maps capsule products to Shopify-compatible draft payloads.
    No real Shopify API calls. No product creation. No publishing.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    export = shopify_draft_provider.export_mock(capsule, operator_id=operator.operator_id)

    # Store drafts in repository
    shopify_draft_repository.store_many(export.drafts)

    return export


@app.post("/v1/shopify/drafts/by-capsule/{capsule_id}/sync-drafts")
async def sync_shopify_drafts(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ShopifyDraftExport:
    """S62 — Operator-triggered live Shopify draft sync.

    Creates Shopify products with status=DRAFT via the Admin GraphQL API
    when SOUNDSYSTEM_SHOPIFY_PROVIDER=shopify. In mock mode this is a
    deterministic alias for the mock export — no network call happens.

    NEVER publishes. NEVER mutates inventory, orders, customers, or
    webhooks. Token is never exposed in the response.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    if shopify_supports_live_sync(shopify_draft_provider):
        # Real provider — sync_drafts() does the GraphQL productCreate.
        export = shopify_draft_provider.sync_drafts(  # type: ignore[attr-defined]
            capsule, operator_id=operator.operator_id
        )
    else:
        # Mock provider — deterministic mock export. No network.
        export = shopify_draft_provider.export_mock(capsule, operator_id=operator.operator_id)

    shopify_draft_repository.store_many(export.drafts)

    # S65 — append-only audit record. No tokens.
    _audit_single_provider_sync(
        capsule=capsule,
        operator=operator,
        action=CommerceSyncAuditAction.SYNC_SHOPIFY,
    )

    return export


@app.get("/v1/shopify/drafts")
async def list_shopify_drafts() -> list[ShopifyProductDraft]:
    return shopify_draft_repository.list_all()


@app.get("/v1/shopify/drafts/{draft_id}")
async def get_shopify_draft(draft_id: UUID) -> ShopifyProductDraft:
    draft = shopify_draft_repository.get(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="shopify_draft_not_found")
    return draft


@app.get("/v1/shopify/drafts/by-capsule/{capsule_id}")
async def list_shopify_drafts_by_capsule(
    capsule_id: UUID,
) -> list[ShopifyProductDraft]:
    return shopify_draft_repository.list_by_capsule(capsule_id)


@app.get("/v1/shopify/summary")
async def shopify_draft_summary() -> ShopifyDraftSummary:
    return shopify_draft_repository.summary()


# ---------------------------------------------------------------------------
# Printful Product Sync Boundary (S41)
# ---------------------------------------------------------------------------


@app.post("/v1/printful/syncs/by-capsule/{capsule_id}")
async def build_printful_syncs(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> PrintfulSyncExport:
    """Build Printful product syncs from a MerchCapsule.

    Maps capsule products to Printful-compatible sync payloads.
    No real Printful API calls. No product creation. No fulfillment.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    export = printful_sync_provider.export_mock(capsule, operator_id=operator.operator_id)

    # Store syncs in repository
    printful_sync_repository.store_many(export.syncs)

    return export


@app.post("/v1/printful/syncs/by-capsule/{capsule_id}/sync-products")
async def sync_printful_products(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> PrintfulSyncExport:
    """S63 — Operator-triggered live Printful sync product creation.

    Calls Printful's Store API (``POST /store/products``) once per
    capsule product when SOUNDSYSTEM_PRINTFUL_PROVIDER=printful. In mock
    mode this is a deterministic alias for the mock export — no network
    call happens. Vinyl products are blocked at this boundary (not POD).

    NEVER publishes the Shopify storefront. NEVER mutates inventory,
    orders, customers, or webhooks. Token never appears in the response.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    if printful_supports_live_sync(printful_sync_provider):
        export = printful_sync_provider.sync_products(  # type: ignore[attr-defined]
            capsule, operator_id=operator.operator_id
        )
    else:
        export = printful_sync_provider.export_mock(capsule, operator_id=operator.operator_id)

    printful_sync_repository.store_many(export.syncs)

    # S65 — append-only audit record. No tokens.
    _audit_single_provider_sync(
        capsule=capsule,
        operator=operator,
        action=CommerceSyncAuditAction.SYNC_PRINTFUL,
    )

    return export


@app.get("/v1/printful/syncs")
async def list_printful_syncs() -> list[PrintfulProductSync]:
    return printful_sync_repository.list_all()


@app.get("/v1/printful/syncs/{sync_id}")
async def get_printful_sync(sync_id: UUID) -> PrintfulProductSync:
    sync = printful_sync_repository.get(sync_id)
    if sync is None:
        raise HTTPException(status_code=404, detail="printful_sync_not_found")
    return sync


@app.get("/v1/printful/syncs/by-capsule/{capsule_id}")
async def list_printful_syncs_by_capsule(
    capsule_id: UUID,
) -> list[PrintfulProductSync]:
    return printful_sync_repository.list_by_capsule(capsule_id)


@app.get("/v1/printful/summary")
async def printful_sync_summary() -> PrintfulSyncSummary:
    return printful_sync_repository.summary()


# ---------------------------------------------------------------------------
# TikTok Shop Listing Boundary (S42)
# ---------------------------------------------------------------------------


@app.post("/v1/tiktok-shop/listings/by-capsule/{capsule_id}")
async def build_tiktok_shop_listings(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> TikTokShopListingExport:
    """Build TikTok Shop listings from a MerchCapsule.

    Maps capsule products to TikTok Shop-compatible listing drafts.
    TikTok Shop is top-of-funnel. Vinyl routes elsewhere.
    No real TikTok Shop API calls. No product creation. No publishing.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    export = tiktok_shop_provider.export_mock(capsule, operator_id=operator.operator_id)

    # Store listings in repository
    tiktok_shop_repository.store_many(export.listings)

    return export


@app.get("/v1/tiktok-shop/listings")
async def list_tiktok_shop_listings() -> list[TikTokShopListing]:
    return tiktok_shop_repository.list_all()


@app.get("/v1/tiktok-shop/listings/{listing_id}")
async def get_tiktok_shop_listing(listing_id: UUID) -> TikTokShopListing:
    listing = tiktok_shop_repository.get(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="tiktok_shop_listing_not_found")
    return listing


@app.get("/v1/tiktok-shop/listings/by-capsule/{capsule_id}")
async def list_tiktok_shop_listings_by_capsule(
    capsule_id: UUID,
) -> list[TikTokShopListing]:
    return tiktok_shop_repository.list_by_capsule(capsule_id)


@app.get("/v1/tiktok-shop/summary")
async def tiktok_shop_summary() -> TikTokShopSummary:
    return tiktok_shop_repository.summary()


# ---------------------------------------------------------------------------
# Campaign OS (S45)
# ---------------------------------------------------------------------------


@app.post("/v1/campaigns")
async def create_campaign(
    request: CampaignCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Campaign:
    """Create a campaign from an existing ReleasePack.

    Infers operational tasks, evaluates warnings, sets initial status.
    No automation execution. No social API calls. Orchestration-only.
    """
    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    # One campaign per release
    existing = campaign_repository.get_by_release(request.release_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="campaign_already_exists_for_release",
        )

    # Look up existing vinyl release for campaign task inference
    vinyl_release = vinyl_repository.get_by_release(request.release_id)

    campaign = build_campaign_from_release(
        release,
        channels=request.channels or None,
        operator_id=operator.operator_id,
        notes=request.notes,
        vinyl_release=vinyl_release,
    )
    campaign_repository.store(campaign)
    return campaign


@app.get("/v1/campaigns")
async def list_campaigns() -> list[Campaign]:
    return campaign_repository.list_all()


@app.get("/v1/campaigns/summary")
async def get_campaign_summary() -> CampaignSummary:
    return campaign_repository.summary()


@app.get("/v1/campaigns/by-release/{release_id}")
async def get_campaign_by_release(release_id: UUID) -> Campaign:
    campaign = campaign_repository.get_by_release(release_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")
    return campaign


@app.get("/v1/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID) -> Campaign:
    campaign = campaign_repository.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")
    return campaign


@app.patch("/v1/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: UUID,
    request: CampaignUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Campaign:
    """Update campaign status, channels, or notes.

    No automation execution. No social API calls. Orchestration-only.
    """
    campaign = campaign_repository.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")

    if campaign.status == CampaignStatus.ARCHIVED:
        raise HTTPException(
            status_code=409,
            detail="campaign_archived: cannot update an archived campaign",
        )

    updates: dict[str, object] = {}
    if request.status is not None:
        updates["status"] = request.status
    if request.channels is not None:
        updates["channels"] = request.channels
    if request.notes is not None:
        updates["notes"] = request.notes

    if updates:
        from datetime import datetime, timezone

        updates["updated_at"] = datetime.now(timezone.utc)
        campaign = campaign.model_copy(update=updates)
        campaign_repository.update(campaign)

    return campaign


# ---------------------------------------------------------------------------
# Campaign Automation Rules (S57) — Dry-run only. No execution.
# ---------------------------------------------------------------------------


@app.post("/v1/campaign-automation/rules")
async def create_automation_rule(
    request: CampaignAutomationRuleCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CampaignAutomationRule:
    """Create an automation rule definition.

    Rules are definitions only. No automation is executed.
    No scheduler. No background jobs. No external calls.
    """
    rule = CampaignAutomationRule(
        rule_id=uuid4(),
        campaign_id=request.campaign_id,
        name=request.name,
        trigger=request.trigger,
        action=request.action,
        conditions=request.conditions,
        action_payload=request.action_payload,
        created_by=operator.operator_id,
    )
    campaign_automation_rule_repository.add_rule(rule)
    return rule


@app.get("/v1/campaign-automation/rules")
async def list_automation_rules() -> list[CampaignAutomationRule]:
    return campaign_automation_rule_repository.list_rules()


@app.get("/v1/campaign-automation/summary")
async def get_automation_rule_summary() -> CampaignAutomationRuleSummary:
    return campaign_automation_rule_repository.summary()


@app.get("/v1/campaign-automation/rules/by-campaign/{campaign_id}")
async def list_automation_rules_by_campaign(
    campaign_id: UUID,
) -> list[CampaignAutomationRule]:
    return campaign_automation_rule_repository.list_by_campaign(campaign_id)


@app.get("/v1/campaign-automation/rules/{rule_id}")
async def get_automation_rule(rule_id: UUID) -> CampaignAutomationRule:
    rule = campaign_automation_rule_repository.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="automation_rule_not_found")
    return rule


@app.patch("/v1/campaign-automation/rules/{rule_id}")
async def update_automation_rule(
    rule_id: UUID,
    request: CampaignAutomationRuleUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CampaignAutomationRule:
    """Update an automation rule definition.

    No automation is executed. No side effects. Definition-only.
    """
    rule = campaign_automation_rule_repository.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="automation_rule_not_found")

    updates: dict[str, object] = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.status is not None:
        updates["status"] = request.status
    if request.trigger is not None:
        updates["trigger"] = request.trigger
    if request.action is not None:
        updates["action"] = request.action
    if request.conditions is not None:
        updates["conditions"] = request.conditions
    if request.action_payload is not None:
        updates["action_payload"] = request.action_payload

    if updates:
        from datetime import datetime, timezone

        updates["updated_at"] = datetime.now(timezone.utc)
        rule = rule.model_copy(update=updates)
        campaign_automation_rule_repository.update_rule(rule)

    return rule


@app.post("/v1/campaign-automation/rules/{rule_id}/dry-run")
async def dry_run_automation_rule(
    rule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CampaignAutomationDryRunResult:
    """Dry-run a single rule against its linked campaign.

    Read-only evaluation. No mutations. No side effects.
    Reports what *would* happen if the rule were executed.
    """
    rule = campaign_automation_rule_repository.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="automation_rule_not_found")
    if rule.campaign_id is None:
        raise HTTPException(
            status_code=422,
            detail="rule_has_no_campaign: attach a campaign_id to dry-run",
        )
    campaign = campaign_repository.get(rule.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")
    return evaluate_rule(rule, campaign)


@app.post("/v1/campaigns/{campaign_id}/automation/dry-run")
async def dry_run_campaign_automation(
    campaign_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> list[CampaignAutomationDryRunResult]:
    """Dry-run all rules linked to a campaign.

    Read-only evaluation. No mutations. No side effects.
    Reports what *would* happen if automation ran.
    """
    campaign = campaign_repository.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")
    rules = campaign_automation_rule_repository.list_by_campaign(campaign_id)
    return evaluate_rules_for_campaign(rules, campaign)


# ---------------------------------------------------------------------------
# Automation Rule Templates (S60) — Definition-only catalogue. No execution.
# ---------------------------------------------------------------------------


@app.get("/v1/campaign-automation/templates")
async def list_automation_rule_templates() -> list[CampaignAutomationRuleTemplate]:
    """Return the curated catalogue of automation rule templates.

    Read-only. No mutations. No execution.
    """
    return build_default_automation_templates()


@app.get("/v1/campaign-automation/templates/summary")
async def get_automation_rule_template_summary() -> CampaignAutomationTemplateSummary:
    """Summary of the template catalogue."""
    return summarize_templates(build_default_automation_templates())


@app.get("/v1/campaign-automation/templates/{slug}")
async def get_automation_rule_template(slug: str) -> CampaignAutomationRuleTemplate:
    template = get_template_by_slug(slug)
    if template is None:
        raise HTTPException(status_code=404, detail="automation_template_not_found")
    return template


@app.post("/v1/campaign-automation/templates/{slug}/instantiate")
async def instantiate_automation_rule_template(
    slug: str,
    request: CampaignAutomationTemplateInstantiationRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CampaignAutomationRule:
    """Instantiate a template onto a campaign as a new draft rule.

    Stores a CampaignAutomationRule definition only. No execution.
    No execution-queue job is created. No audit record is created.
    No provider mutations. No external API calls.
    """
    template = get_template_by_slug(slug)
    if template is None:
        raise HTTPException(status_code=404, detail="automation_template_not_found")
    if not template.enabled:
        raise HTTPException(status_code=422, detail="automation_template_disabled")

    campaign = campaign_repository.get(request.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")

    rule = instantiate_template(template, request, operator_id=operator.operator_id)
    campaign_automation_rule_repository.add_rule(rule)
    return rule


# ---------------------------------------------------------------------------
# Automation Execution Queue Boundary (S58) — Disabled by default. No side effects.
# ---------------------------------------------------------------------------


@app.post("/v1/campaign-automation/rules/{rule_id}/queue-execution")
async def queue_automation_execution(
    rule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AutomationExecutionResult:
    """Queue an execution job for a rule by re-running the dry-run evaluator.

    Always disabled by default. In DISABLED mode jobs are BLOCKED.
    In MOCK mode, jobs with dry-run WOULD_RUN status are QUEUED.
    No campaign, rule, analytics, or provider state is changed.
    """
    rule = campaign_automation_rule_repository.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="automation_rule_not_found")
    if rule.campaign_id is None:
        raise HTTPException(
            status_code=422,
            detail="rule_has_no_campaign: attach a campaign_id to queue execution",
        )
    campaign = campaign_repository.get(rule.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")

    dry_run = evaluate_rule(rule, campaign)
    mode = automation_execution_mode()
    job = create_execution_job_from_dry_run(rule, campaign, dry_run, operator, mode)
    automation_execution_repository.add_job(job)

    # S59: append-only audit record for the initial state transition.
    # No side effects on the campaign, rule, or any provider.
    automation_execution_audit_repository.add_record(
        AutomationExecutionAuditRecord(
            audit_id=uuid4(),
            execution_id=job.execution_id,
            rule_id=job.rule_id,
            campaign_id=job.campaign_id,
            from_status=None,
            to_status=job.status,
            operator_id=operator.operator_id,
            reason="queue_execution",
            details={
                "execution_mode": mode.value,
                "dry_run_status": job.dry_run_status.value,
            },
        )
    )

    note = (
        "Automation execution is disabled. Job recorded as BLOCKED. No side effects."
        if mode.value == "disabled"
        else "Mock execution recorded intent. No campaign or provider state changed."
    )
    return AutomationExecutionResult(job=job, note=note)


@app.get("/v1/campaign-automation/executions")
async def list_automation_executions() -> list[AutomationExecutionJob]:
    return automation_execution_repository.list_jobs()


@app.get("/v1/campaign-automation/executions/summary")
async def get_automation_execution_summary() -> AutomationExecutionSummary:
    return automation_execution_repository.summary()


@app.get("/v1/campaign-automation/executions/by-campaign/{campaign_id}")
async def list_automation_executions_by_campaign(
    campaign_id: UUID,
) -> list[AutomationExecutionJob]:
    return automation_execution_repository.list_by_campaign(campaign_id)


@app.get("/v1/campaign-automation/executions/{execution_id}")
async def get_automation_execution(execution_id: UUID) -> AutomationExecutionJob:
    job = automation_execution_repository.get_job(execution_id)
    if job is None:
        raise HTTPException(status_code=404, detail="execution_job_not_found")
    return job


@app.post("/v1/campaign-automation/executions/{execution_id}/execute-mock")
async def execute_automation_execution_mock(
    execution_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AutomationExecutionResult:
    """Transition a QUEUED job to COMPLETED_MOCK. No side effects.

    Only valid when SOUNDSYSTEM_AUTOMATION_EXECUTION_MODE=mock and the job is
    in QUEUED state. No campaign, rule, or provider state is mutated — the
    job itself is the only object updated.

    The `operator` parameter is required for audit (route requires identity).
    """
    job = automation_execution_repository.get_job(execution_id)
    if job is None:
        raise HTTPException(status_code=404, detail="execution_job_not_found")

    mode = automation_execution_mode()
    previous_status = job.status
    new_job = execute_mock_job(job, mode)
    automation_execution_repository.update_job(new_job)

    # S59: append-only audit record for this transition.
    # No side effects on the campaign, rule, or any provider.
    automation_execution_audit_repository.add_record(
        AutomationExecutionAuditRecord(
            audit_id=uuid4(),
            execution_id=new_job.execution_id,
            rule_id=new_job.rule_id,
            campaign_id=new_job.campaign_id,
            from_status=previous_status,
            to_status=new_job.status,
            operator_id=operator.operator_id,
            reason="execute_mock",
            details={"execution_mode": mode.value},
        )
    )

    if new_job.status.value == "completed_mock":
        note = "Mock execution recorded intent only. No campaign or provider state is changed."
    elif new_job.status.value == "blocked":
        note = "Automation execution is disabled. Mock execution refused."
    else:
        note = "Mock execution failed — job was not in 'queued' state."
    return AutomationExecutionResult(job=new_job, note=note)


# ---------------------------------------------------------------------------
# Automation Execution Audit Log (S59) — Read-only. Append-only. Immutable.
# ---------------------------------------------------------------------------


@app.get("/v1/campaign-automation/execution-audit")
async def list_automation_execution_audit(
    limit: int = 100,
) -> list[AutomationExecutionAuditRecord]:
    """List audit records (most recent first). Read-only."""
    bounded = max(1, min(limit, 500))
    return automation_execution_audit_repository.list_records(limit=bounded)


@app.get("/v1/campaign-automation/execution-audit/summary")
async def get_automation_execution_audit_summary() -> AutomationExecutionAuditSummary:
    """Summary of the audit log. Read-only."""
    return automation_execution_audit_repository.summary()


@app.get("/v1/campaign-automation/executions/{execution_id}/audit")
async def list_automation_execution_audit_for_execution(
    execution_id: UUID,
) -> list[AutomationExecutionAuditRecord]:
    """List audit records for one execution (chronological). Read-only."""
    return automation_execution_audit_repository.list_by_execution(execution_id)


@app.get("/v1/campaigns/{campaign_id}/automation/audit")
async def list_automation_execution_audit_for_campaign(
    campaign_id: UUID,
) -> list[AutomationExecutionAuditRecord]:
    """List audit records for one campaign (most recent first). Read-only."""
    return automation_execution_audit_repository.list_by_campaign(campaign_id)


# ---------------------------------------------------------------------------
# Vinyl Release Object (S46)
# ---------------------------------------------------------------------------


@app.post("/v1/vinyl/releases")
async def create_vinyl_release(
    request: VinylReleaseCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> VinylReleaseObject:
    """Create a vinyl release from an existing ReleasePack.

    Infers provider group, evaluates readiness, builds default track listing.
    No real elasticStage/DISC_ARCHIVE API calls.
    No manufacturing. No order placement. Manual handoff only.
    """
    release = release_pack_repository.get(request.release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    # One vinyl release per release (for now)
    existing = vinyl_repository.get_by_release(request.release_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="vinyl_release_already_exists_for_release",
        )

    vinyl = build_vinyl_release_from_release(
        release,
        format=request.format,
        edition_type=request.edition_type,
        pressing_quantity=request.pressing_quantity,
        numbered=request.numbered,
        operator_id=operator.operator_id,
        notes=request.notes,
    )
    vinyl_repository.store(vinyl)
    return vinyl


@app.get("/v1/vinyl/releases")
async def list_vinyl_releases() -> list[VinylReleaseObject]:
    return vinyl_repository.list_all()


@app.get("/v1/vinyl/summary")
async def vinyl_release_summary() -> VinylReleaseSummary:
    return vinyl_repository.summary()


@app.get("/v1/vinyl/releases/by-release/{release_id}")
async def get_vinyl_release_by_release(release_id: UUID) -> VinylReleaseObject:
    vinyl = vinyl_repository.get_by_release(release_id)
    if vinyl is None:
        raise HTTPException(status_code=404, detail="vinyl_release_not_found")
    return vinyl


@app.get("/v1/vinyl/releases/{vinyl_id}")
async def get_vinyl_release(vinyl_id: UUID) -> VinylReleaseObject:
    vinyl = vinyl_repository.get(vinyl_id)
    if vinyl is None:
        raise HTTPException(status_code=404, detail="vinyl_release_not_found")
    return vinyl


@app.post("/v1/vinyl/releases/{vinyl_id}/status")
async def update_vinyl_release_status(
    vinyl_id: UUID,
    request: VinylReleaseStatusUpdateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> VinylReleaseObject:
    """Update vinyl release status.

    No real vendor notifications. Status is local only.
    """
    vinyl = vinyl_repository.get(vinyl_id)
    if vinyl is None:
        raise HTTPException(status_code=404, detail="vinyl_release_not_found")

    if vinyl.status == VinylReleaseStatus.ARCHIVED:
        raise HTTPException(
            status_code=409,
            detail="vinyl_archived: cannot update an archived vinyl release",
        )

    updated = update_vinyl_status(vinyl, request.status)
    vinyl_repository.update(updated)
    return updated


@app.get("/v1/vinyl/releases/{vinyl_id}/export")
async def get_vinyl_export(vinyl_id: UUID) -> VinylExportPayload:
    """Get export payload for manual provider handoff.

    No real API calls. No order placement.
    Manual vinyl handoff. No manufacturing order placed.
    """
    vinyl = vinyl_repository.get(vinyl_id)
    if vinyl is None:
        raise HTTPException(status_code=404, detail="vinyl_release_not_found")

    return build_vinyl_export_payload(vinyl)


# Analytics Event Graph (S49)
# ---------------------------------------------------------------------------


@app.post("/v1/analytics/events")
async def create_analytics_event(
    request: AnalyticsEventCreateRequest,
    operator: Annotated[Operator, Depends(require_operator)],
) -> AnalyticsEvent:
    """Record a normalized analytics event.

    No real provider API calls. Internal graph only.
    Future provider connectors will write into this endpoint.
    """
    from uuid import uuid4

    event = AnalyticsEvent(
        event_id=uuid4(),
        source=request.source,
        metric=request.metric,
        value=request.value,
        granularity=request.granularity,
        campaign_id=request.campaign_id,
        release_id=request.release_id,
        track_id=request.track_id,
        merch_capsule_id=request.merch_capsule_id,
        vinyl_id=request.vinyl_id,
        metadata=request.metadata,
    )
    analytics_repository.add_event(event)
    return event


@app.get("/v1/analytics/events")
async def list_analytics_events(
    source: AnalyticsSource | None = None,
    metric: AnalyticsMetric | None = None,
    campaign_id: UUID | None = None,
    release_id: UUID | None = None,
    track_id: UUID | None = None,
    limit: int = 100,
) -> list[AnalyticsEvent]:
    """List analytics events with optional filters."""
    return analytics_repository.list_events(
        source=source,
        metric=metric,
        campaign_id=campaign_id,
        release_id=release_id,
        track_id=track_id,
        limit=limit,
    )


@app.get("/v1/analytics/summary")
async def get_analytics_summary() -> AnalyticsSummary:
    """Get global analytics summary."""
    return analytics_repository.summary()


@app.get("/v1/analytics/channels")
async def get_analytics_channels() -> list[ChannelPerformance]:
    """Get per-channel performance breakdown."""
    events = analytics_repository.list_events(limit=10000)
    return build_source_breakdown(events)


@app.get("/v1/analytics/campaigns/{campaign_id}")
async def get_campaign_performance(campaign_id: UUID) -> CampaignPerformance:
    """Get campaign performance from analytics events.

    No real provider API calls. Computed from internal event graph.
    """
    events = analytics_repository.get_campaign_events(campaign_id)
    return aggregate_campaign_performance(campaign_id, events)


@app.get("/v1/analytics/tracks/{track_id}")
async def get_track_performance(track_id: UUID) -> TrackPerformance:
    """Get track performance from analytics events.

    No real provider API calls. Computed from internal event graph.
    """
    events = analytics_repository.get_track_events(track_id)
    return aggregate_track_performance(track_id, events)


@app.post("/v1/analytics/demo-seed")
async def seed_demo_analytics(
    operator: Annotated[Operator, Depends(require_operator)],
) -> list[AnalyticsEvent]:
    """Seed deterministic demo analytics events.

    Used for dashboard population and testing.
    No real data. Fixed values. Reproducible.
    """
    events = generate_demo_analytics_events()
    analytics_repository.add_events(events)
    return events


# Intelligence Engine (S50)
# ---------------------------------------------------------------------------


@app.get("/v1/intelligence/overview")
async def get_intelligence_overview() -> IntelligenceOverview:
    """Build full intelligence overview from all analytics events.

    Composes viral moments, audience heatmaps, revenue correlations,
    and timeline fusion. Deterministic. No ML. No AI. No external calls.
    """
    events = analytics_repository.list_events(limit=10000)
    return build_intelligence_overview(events)


@app.get("/v1/intelligence/viral-moments")
async def get_viral_moments() -> list[ViralMoment]:
    """Detect viral spikes across all analytics events.

    Groups events by (source, metric) and finds growth exceeding 50%.
    Deterministic. No ML.
    """
    events = analytics_repository.list_events(limit=10000)
    return detect_viral_moments(events)


@app.get("/v1/intelligence/heatmap")
async def get_audience_heatmap() -> list[AudienceHeatmap]:
    """Build per-platform audience heat summaries.

    Audience size, engagement, conversion rate, heat score, trend.
    Deterministic. No ML.
    """
    events = analytics_repository.list_events(limit=10000)
    return build_audience_heatmaps(events)


@app.get("/v1/intelligence/revenue")
async def get_revenue_correlations() -> list[RevenueCorrelation]:
    """Build per-source revenue attribution and correlations.

    Deterministic. No ML.
    """
    events = analytics_repository.list_events(limit=10000)
    return build_revenue_correlations(events)


@app.get("/v1/intelligence/timeline")
async def get_intelligence_timeline() -> list[TimelineCorrelation]:
    """Build daily timeline fusion from analytics events.

    Each point shows event density, dominant source/metric, and heat.
    Deterministic. No ML.
    """
    events = analytics_repository.list_events(limit=10000)
    return build_timeline_correlations(events)


# Intelligence Snapshot Persistence (S54)
# ---------------------------------------------------------------------------


@app.get("/v1/intelligence/snapshots/summary")
async def get_intelligence_snapshot_summary() -> IntelligenceSnapshotSummary:
    """Summary of all intelligence snapshots.

    Total, active, archived counts. Latest heat and delta from previous.
    """
    return intelligence_snapshot_repository.summary()


@app.get("/v1/intelligence/snapshots/diff/{before_id}/{after_id}")
async def get_intelligence_snapshot_diff(
    before_id: UUID,
    after_id: UUID,
) -> IntelligenceSnapshotDiff:
    """Compare two intelligence snapshots.

    Deterministic diff. Read-only. No persistence.
    404 if either snapshot not found.
    """
    before = intelligence_snapshot_repository.get_snapshot(before_id)
    if before is None:
        raise HTTPException(status_code=404, detail="before_snapshot_not_found")
    after = intelligence_snapshot_repository.get_snapshot(after_id)
    if after is None:
        raise HTTPException(status_code=404, detail="after_snapshot_not_found")
    return compare_snapshots(before, after)


@app.get("/v1/intelligence/snapshots/{snapshot_id}")
async def get_intelligence_snapshot(snapshot_id: UUID) -> IntelligenceSnapshot:
    """Get a single intelligence snapshot by ID."""
    snapshot = intelligence_snapshot_repository.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot_not_found")
    return snapshot


@app.get("/v1/intelligence/snapshots")
async def list_intelligence_snapshots(
    status: IntelligenceSnapshotStatus | None = None,
    limit: int = 50,
) -> list[IntelligenceSnapshot]:
    """List intelligence snapshots, most recent first.

    Optional status filter. No automation — snapshots created by operator POST only.
    """
    return intelligence_snapshot_repository.list_snapshots(status=status, limit=limit)


@app.post("/v1/intelligence/snapshots")
async def create_intelligence_snapshot(
    operator: Annotated[Operator, Depends(require_operator)],
    body: IntelligenceSnapshotCreateRequest | None = None,
) -> IntelligenceSnapshot:
    """Create a new intelligence snapshot from current analytics events.

    Reads all events, builds IntelligenceOverview, stores frozen snapshot.
    Requires operator identity. No automation. No scheduler.
    """
    events = analytics_repository.list_events(limit=10000)
    overview = build_intelligence_overview(events)

    latest_at = None
    if events:
        latest_at = max(e.timestamp for e in events)

    snapshot = IntelligenceSnapshot(
        snapshot_id=uuid4(),
        status=IntelligenceSnapshotStatus.CREATED,
        overview=overview,
        event_count=len(events),
        source_event_latest_at=latest_at,
        notes=body.notes if body else None,
        created_by=operator.operator_id,
    )

    intelligence_snapshot_repository.add_snapshot(snapshot)
    return snapshot


# Provider Connector Framework (S51)
# ---------------------------------------------------------------------------


@app.get("/v1/connectors")
async def list_connectors() -> list[ProviderConnector]:
    """List all registered provider connectors.

    No real provider API calls. Registry state only.
    """
    return connector_registry.list_connectors()


@app.get("/v1/connectors/summary")
async def get_connector_summary() -> ConnectorRegistrySummary:
    """Get provider connector registry summary.

    Aggregate counts by status, available capabilities,
    registered connector types.
    """
    return connector_registry.registry_summary()


# Connector Import Audit (S53)
# ---------------------------------------------------------------------------


@app.get("/v1/connectors/import-audit")
async def list_connector_import_audit(
    connector_type: ConnectorType | None = None,
    operator_id: str | None = None,
    limit: int = 100,
) -> list[ConnectorImportAuditRecord]:
    """List connector import audit records.

    Optional filters by connector_type and operator_id.
    Returns most recent first.
    """
    return connector_import_audit.list_records(
        connector_type=connector_type,
        operator_id=operator_id,
        limit=limit,
    )


@app.get("/v1/connectors/import-audit/summary")
async def connector_import_audit_summary() -> ConnectorImportAuditSummary:
    """Summary of all connector import audit records."""
    return connector_import_audit.summary()


@app.get("/v1/connectors/{connector_type}")
async def get_connector(connector_type: ConnectorType) -> ProviderConnector:
    """Get a single provider connector by type.

    No real provider API calls.
    """
    connector = connector_registry.get_connector(connector_type)
    if connector is None:
        raise HTTPException(status_code=404, detail="connector_not_found")
    return connector


@app.get("/v1/connectors/{connector_type}/health")
async def get_connector_health(
    connector_type: ConnectorType,
) -> ConnectorHealth:
    """Get connector health check.

    Reports healthy/unhealthy, warnings, missing configuration.
    No real provider API calls. Deterministic from registry state.
    """
    health = connector_registry.connector_health(connector_type)
    if health is None:
        raise HTTPException(status_code=404, detail="connector_not_found")
    return health


@app.get("/v1/connectors/{connector_type}/preview-sync")
async def preview_connector_sync(
    connector_type: ConnectorType,
) -> ConnectorSyncPreview:
    """Preview what a connector sync would produce.

    Returns mock normalized events. No real data pull.
    No real provider API calls. Deterministic mock preview.
    """
    connector = connector_registry.get_connector(connector_type)
    if connector is None:
        raise HTTPException(status_code=404, detail="connector_not_found")
    return build_connector_sync_preview(connector)


# Mock Platform Connectors (S52)
# ---------------------------------------------------------------------------


@app.post("/v1/connectors/{connector_type}/import-demo")
async def import_demo_events(
    connector_type: ConnectorType,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ConnectorSyncPreview:
    """Import deterministic mock events into the analytics repository.

    Uses the platform-specific mock adapter (S52) to generate events,
    then adds them to the analytics repository. Requires operator
    identity. Only supported for connector types with mock adapters.
    Creates an audit record for every import attempt (S53).

    No real provider API calls. Deterministic mock data only.
    """
    if not has_mock_platform_connector(connector_type):
        # Audit the failed attempt
        connector_import_audit.add_record(
            ConnectorImportAuditRecord(
                audit_id=uuid4(),
                connector_type=connector_type,
                operator_id=operator.operator_id,
                event_count=0,
                status="failed",
                error_message=f"No mock platform adapter for {connector_type.value}.",
            )
        )
        return ConnectorSyncPreview(
            connector_type=connector_type,
            event_count=0,
            normalized_events=[],
            warnings=[
                f"No mock platform adapter for {connector_type.value}. Import not available."
            ],
            blocked_reasons=[f"Connector type {connector_type.value!r} has no mock adapter."],
        )

    adapter = build_mock_platform_connector(connector_type)
    events = adapter.preview_events()

    # Add to analytics repository — this is the only mutation
    analytics_repository.add_events(events)

    # S53: Create audit record
    connector_import_audit.add_record(
        ConnectorImportAuditRecord(
            audit_id=uuid4(),
            connector_type=connector_type,
            operator_id=operator.operator_id,
            event_count=len(events),
            event_ids=[e.event_id for e in events],
            status="completed",
            metadata={"adapter": adapter.__class__.__name__},
        )
    )

    return ConnectorSyncPreview(
        connector_type=connector_type,
        event_count=len(events),
        normalized_events=events,
        warnings=[
            "Mock demo events imported. No real provider API called.",
            f"Added {len(events)} deterministic events to analytics repository.",
        ],
        blocked_reasons=[],
    )


# ---------------------------------------------------------------------------
# Release-to-Campaign Command Center (S61) — Orchestration surface.
# Read-only by default. POST bootstrap may create one Campaign + draft rules.
# ---------------------------------------------------------------------------


def _gather_command_center_inputs(release_id: UUID):
    """Fetch all subsystem state needed to build a Command Center snapshot.

    No mutations. No external calls.
    """
    release = release_pack_repository.get(release_id)
    if release is None:
        return None
    campaign = campaign_repository.get_by_release(release_id)
    existing_rules: list[CampaignAutomationRule] = []
    if campaign is not None:
        existing_rules = campaign_automation_rule_repository.list_by_campaign(campaign.campaign_id)
    merch_capsules = [c for c in merch_capsule_repository.list_all() if c.release_id == release_id]
    distribution_pack = distribution_repository.get_by_release(release_id)
    vinyl_release = vinyl_repository.get_by_release(release_id)
    return {
        "release": release,
        "campaign": campaign,
        "existing_rules": existing_rules,
        "merch_capsules": merch_capsules,
        "distribution_pack": distribution_pack,
        "vinyl_release": vinyl_release,
    }


@app.get("/v1/command-center/releases")
async def list_command_center_releases() -> list[ReleaseCommandCenter]:
    """List Command Center snapshots for every release. Read-only."""
    snapshots: list[ReleaseCommandCenter] = []
    for release in release_pack_repository.list_all():
        inputs = _gather_command_center_inputs(release.release_id)
        if inputs is None:
            continue
        snapshots.append(build_release_command_center(**inputs))
    return snapshots


@app.get("/v1/command-center/releases/{release_id}")
async def get_command_center_release(release_id: UUID) -> ReleaseCommandCenter:
    """Get the Command Center snapshot for one release. Read-only."""
    inputs = _gather_command_center_inputs(release_id)
    if inputs is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return build_release_command_center(**inputs)


@app.post("/v1/command-center/releases/{release_id}/bootstrap")
async def bootstrap_command_center_release(
    release_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> ReleaseCommandCenterBootstrapResult:
    """Create campaign (if missing) + instantiate recommended templates.

    Bootstrap NEVER queues execution jobs, NEVER writes audit records,
    NEVER calls providers, NEVER mutates merch/distribution/vinyl.
    """
    inputs = _gather_command_center_inputs(release_id)
    if inputs is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    return bootstrap_release_campaign(
        release=inputs["release"],
        campaign=inputs["campaign"],
        existing_rules=inputs["existing_rules"],
        merch_capsules=inputs["merch_capsules"],
        distribution_pack=inputs["distribution_pack"],
        vinyl_release=inputs["vinyl_release"],
        campaign_repo=campaign_repository,
        rule_repo=campaign_automation_rule_repository,
        operator=operator,
    )


# ---------------------------------------------------------------------------
# Commerce Sync Dashboard (S64) — Read-model + operator-triggered sync-both.
# ---------------------------------------------------------------------------


def _build_capsule_sync_state(capsule):
    return build_commerce_capsule_sync_state(
        capsule=capsule,
        shopify_drafts=shopify_draft_repository.list_by_capsule(capsule.capsule_id),
        printful_syncs=printful_sync_repository.list_by_capsule(capsule.capsule_id),
        shopify_provider_mode=shopify_draft_provider.name,
        printful_provider_mode=printful_sync_provider.name,
    )


@app.get("/v1/commerce/sync/capsules")
async def list_commerce_sync_capsules() -> list[CommerceCapsuleSyncState]:
    """List every capsule with its Shopify + Printful sync state. Read-only."""
    return [_build_capsule_sync_state(c) for c in merch_capsule_repository.list_all()]


@app.get("/v1/commerce/sync/summary")
async def get_commerce_sync_summary() -> CommerceSyncSummary:
    """Aggregate counts across every capsule. Read-only."""
    states = [_build_capsule_sync_state(c) for c in merch_capsule_repository.list_all()]
    return build_commerce_sync_summary(
        states,
        shopify_provider_mode=shopify_draft_provider.name,
        printful_provider_mode=printful_sync_provider.name,
    )


@app.get("/v1/commerce/sync/capsules/{capsule_id}")
async def get_commerce_sync_capsule(capsule_id: UUID) -> CommerceCapsuleSyncState:
    """Get a single capsule's sync state. Read-only."""
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")
    return _build_capsule_sync_state(capsule)


@app.post("/v1/commerce/sync/capsules/{capsule_id}/sync-both")
async def sync_commerce_capsule_both(
    capsule_id: UUID,
    operator: Annotated[Operator, Depends(require_operator)],
) -> CommerceCapsuleSyncResult:
    """Operator-triggered sequential Shopify + Printful sync for one capsule.

    Calls the Shopify sync boundary first, then the Printful sync boundary.
    Neither call publishes the Shopify storefront, mutates inventory,
    orders, customers, or webhooks. No background work. No scheduler.
    Tokens are never exposed in the response.

    Returns the combined provider exports plus the post-sync read-model
    state for the capsule.
    """
    capsule = merch_capsule_repository.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=404, detail="merch_capsule_not_found")

    # 1) Shopify
    if shopify_supports_live_sync(shopify_draft_provider):
        shopify_export = shopify_draft_provider.sync_drafts(  # type: ignore[attr-defined]
            capsule, operator_id=operator.operator_id
        )
    else:
        shopify_export = shopify_draft_provider.export_mock(
            capsule, operator_id=operator.operator_id
        )
    shopify_draft_repository.store_many(shopify_export.drafts)

    # 2) Printful
    if printful_supports_live_sync(printful_sync_provider):
        printful_export = printful_sync_provider.sync_products(  # type: ignore[attr-defined]
            capsule, operator_id=operator.operator_id
        )
    else:
        printful_export = printful_sync_provider.export_mock(
            capsule, operator_id=operator.operator_id
        )
    printful_sync_repository.store_many(printful_export.syncs)

    result = combine_sync_results(
        capsule=capsule,
        shopify_export=shopify_export,
        printful_export=printful_export,
        shopify_drafts=shopify_draft_repository.list_by_capsule(capsule.capsule_id),
        printful_syncs=printful_sync_repository.list_by_capsule(capsule.capsule_id),
        shopify_provider_mode=shopify_draft_provider.name,
        printful_provider_mode=printful_sync_provider.name,
    )

    # S65 — append-only audit record. No tokens. Details carry provider IDs only.
    commerce_sync_audit_repository.add_record(
        CommerceSyncAuditRecord(
            audit_id=uuid4(),
            capsule_id=capsule.capsule_id,
            release_id=capsule.release_id,
            operator_id=operator.operator_id,
            action=CommerceSyncAuditAction.SYNC_BOTH,
            overall_status=result.overall_status,
            shopify_status=result.state.shopify.status,
            printful_status=result.state.printful.status,
            shopify_item_count=result.state.shopify.item_count,
            printful_item_count=result.state.printful.item_count,
            warnings=list(result.warnings),
            details={
                "shopify_provider_mode": result.state.shopify.provider_mode,
                "printful_provider_mode": result.state.printful.provider_mode,
                "shopify_provider_ids": list(result.state.shopify.provider_ids),
                "printful_provider_ids": list(result.state.printful.provider_ids),
                "shopify_synced": result.state.shopify.synced_item_count,
                "printful_synced": result.state.printful.synced_item_count,
                "shopify_blocked": result.state.shopify.blocked_item_count,
                "printful_blocked": result.state.printful.blocked_item_count,
                "shopify_failed": result.state.shopify.failed_item_count,
                "printful_failed": result.state.printful.failed_item_count,
            },
        )
    )

    return result


# ---------------------------------------------------------------------------
# Commerce Sync Audit Log (S65) — Append-only. Read-only routes are open.
# ---------------------------------------------------------------------------


def _audit_single_provider_sync(
    *,
    capsule,
    operator: Operator,
    action: CommerceSyncAuditAction,
) -> None:
    """Append an audit record for a single-provider sync.

    Reads the current sync state from the repositories and writes one
    audit row. No tokens. No external calls.
    """
    state = build_commerce_capsule_sync_state(
        capsule=capsule,
        shopify_drafts=shopify_draft_repository.list_by_capsule(capsule.capsule_id),
        printful_syncs=printful_sync_repository.list_by_capsule(capsule.capsule_id),
        shopify_provider_mode=shopify_draft_provider.name,
        printful_provider_mode=printful_sync_provider.name,
    )
    commerce_sync_audit_repository.add_record(
        CommerceSyncAuditRecord(
            audit_id=uuid4(),
            capsule_id=capsule.capsule_id,
            release_id=capsule.release_id,
            operator_id=operator.operator_id,
            action=action,
            overall_status=state.overall_status,
            shopify_status=state.shopify.status,
            printful_status=state.printful.status,
            shopify_item_count=state.shopify.item_count,
            printful_item_count=state.printful.item_count,
            warnings=list(state.warnings),
            details={
                "shopify_provider_mode": state.shopify.provider_mode,
                "printful_provider_mode": state.printful.provider_mode,
                "shopify_provider_ids": list(state.shopify.provider_ids),
                "printful_provider_ids": list(state.printful.provider_ids),
            },
        )
    )


@app.get("/v1/commerce/sync/audit")
async def list_commerce_sync_audit(
    limit: int = 100,
) -> list[CommerceSyncAuditRecord]:
    """List commerce-sync audit records (most recent first). Read-only."""
    bounded = max(1, min(limit, 500))
    return commerce_sync_audit_repository.list_records(limit=bounded)


@app.get("/v1/commerce/sync/audit/summary")
async def get_commerce_sync_audit_summary() -> CommerceSyncAuditSummary:
    """Summary of the commerce-sync audit log. Read-only."""
    return commerce_sync_audit_repository.summary()


@app.get("/v1/commerce/sync/capsules/{capsule_id}/audit")
async def list_commerce_sync_audit_by_capsule(
    capsule_id: UUID,
) -> list[CommerceSyncAuditRecord]:
    """Audit rows for one capsule (chronological). Read-only."""
    return commerce_sync_audit_repository.list_by_capsule(capsule_id)


@app.get("/v1/commerce/sync/releases/{release_id}/audit")
async def list_commerce_sync_audit_by_release(
    release_id: UUID,
) -> list[CommerceSyncAuditRecord]:
    """Audit rows for one release (most recent first). Read-only."""
    return commerce_sync_audit_repository.list_by_release(release_id)


# ---------------------------------------------------------------------------
# Public newsletter subscribe (S66) — Operator-friendly, Listmonk-backed.
# No tracking. No cookies. Email hashed in response. Offline-honest.
# ---------------------------------------------------------------------------


@app.post("/v1/public/newsletter/subscribe")
async def public_newsletter_subscribe(
    request: NewsletterSubscribeRequest,
) -> NewsletterSubscribeResponse:
    """Accept a public newsletter signup. Open route — no operator auth.

    Forwards the email to the configured Listmonk instance if every
    Listmonk env var is set. Otherwise returns ``status=offline`` —
    we never fake success.

    The raw email is never returned. We respond with the SHA-256 hash of
    the normalized email so the client can reconcile state without a
    server-side cookie. No IP, no referrer, no user-agent is captured
    or stored by this route.
    """
    return subscribe_to_newsletter(request)
