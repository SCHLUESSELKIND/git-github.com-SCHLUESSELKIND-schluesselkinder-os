/* eslint-disable */
// AUTO-GENERATED FROM services/soundsystem-inference/app/schemas.py.
// DO NOT EDIT BY HAND.
//
// Regenerate via:
//   cd services/soundsystem-inference
//   python scripts/generate_ts_types.py
//
// The pytest drift check `tests/test_generated_types.py`
// will fail if this file is stale.

// ---- Enums (string unions mirroring Python StrEnum) ----

export type ActivationStatus =
  | "conditional_live"
  | "live"
  | "mock"
  | "not_wired";

export type AnalyticsGranularity =
  | "daily"
  | "hourly"
  | "monthly"
  | "realtime"
  | "weekly";

export type AnalyticsMetric =
  | "campaign_heat"
  | "cart_adds"
  | "clicks"
  | "comments"
  | "conversions"
  | "engagement_rate"
  | "followers"
  | "likes"
  | "merch_interest"
  | "orders"
  | "plays"
  | "reposts"
  | "revenue"
  | "saves"
  | "shares"
  | "streams"
  | "views"
  | "vinyl_interest"
  | "watch_time";

export type AnalyticsRepositoryMode =
  | "in_memory"
  | "postgres";

export type AnalyticsSource =
  | "campaign"
  | "discord"
  | "ditto"
  | "instagram"
  | "manual"
  | "printful"
  | "shopify"
  | "soundcloud"
  | "spotify"
  | "tiktok"
  | "tiktok_shop"
  | "youtube";

export type ArtifactAccessMode =
  | "direct"
  | "signed";

export type ArtifactKind =
  | "audio_master"
  | "audio_mix"
  | "cover_art"
  | "export_pack"
  | "lyrics"
  | "manifest"
  | "music_job"
  | "other"
  | "provenance"
  | "release_pack"
  | "soundgraph"
  | "stem_pack";

export type ArtifactRegistryMode =
  | "in_memory"
  | "postgres";

export type ArtifactStatus =
  | "deleted"
  | "failed"
  | "missing"
  | "planned"
  | "stored";

export type ArtifactStorageMode =
  | "local"
  | "s3";

export type AsyncJobKind =
  | "dropbox_sync"
  | "generic"
  | "music_router"
  | "release_pack"
  | "soundgraph_handoff";

export type AsyncJobStatus =
  | "cancelled"
  | "failed"
  | "queued"
  | "retrying"
  | "running"
  | "succeeded";

export type Atmosphere =
  | "black_concrete"
  | "dub_smoke"
  | "neon_green"
  | "post_human"
  | "underground";

export type AutomationExecutionAuditMode =
  | "in_memory"
  | "postgres";

export type AutomationExecutionMode =
  | "disabled"
  | "mock";

export type AutomationExecutionRepositoryMode =
  | "in_memory"
  | "postgres";

export type AutomationExecutionStatus =
  | "blocked"
  | "completed_mock"
  | "failed"
  | "queued";

export type BassPressure =
  | "crushing"
  | "deep"
  | "earthquake"
  | "maximum"
  | "warm";

export type BlockedPromptCategory =
  | "named_artist_imitation"
  | "named_track_cloning"
  | "public_figure_voice"
  | "voice_likeness_without_consent";

export type CampaignAutomationAction =
  | "add_warning"
  | "create_task"
  | "mark_campaign_active"
  | "mark_campaign_ready"
  | "no_op"
  | "notify_operator";

export type CampaignAutomationDryRunStatus =
  | "blocked"
  | "no_match"
  | "would_run";

export type CampaignAutomationRuleStatus =
  | "active"
  | "archived"
  | "draft"
  | "paused";

export type CampaignAutomationTemplateCategory =
  | "intelligence_ops"
  | "merch_ops"
  | "operator_notification"
  | "release_ops"
  | "vinyl_ops";

export type CampaignAutomationTrigger =
  | "campaign_active"
  | "campaign_ready"
  | "distribution_ready"
  | "intelligence_heat_above_threshold"
  | "merch_capsule_locked"
  | "release_ready"
  | "snapshot_heat_delta_above_threshold"
  | "vinyl_ready";

export type CampaignChannel =
  | "discord"
  | "distribution"
  | "instagram"
  | "merch"
  | "soundcloud"
  | "tiktok";

export type CampaignRepositoryMode =
  | "in_memory"
  | "postgres";

export type CampaignStatus =
  | "active"
  | "archived"
  | "completed"
  | "planning"
  | "ready";

export type CampaignTaskStatus =
  | "blocked"
  | "completed"
  | "pending"
  | "ready";

export type CommandCenterReadinessStatus =
  | "blocked"
  | "missing"
  | "ready"
  | "warning";

export type CommerceSyncAuditAction =
  | "sync_both"
  | "sync_printful"
  | "sync_shopify";

export type CommerceSyncAuditMode =
  | "in_memory"
  | "postgres";

export type CommerceSyncProvider =
  | "printful"
  | "shopify";

export type CommerceSyncStatus =
  | "blocked"
  | "failed"
  | "not_synced"
  | "partial"
  | "synced_live"
  | "synced_mock";

export type CommercialStatus =
  | "approved_internal"
  | "approved_release"
  | "blocked"
  | "conditional"
  | "research_only"
  | "review_needed";

export type ConnectorCapability =
  | "analytics_pull"
  | "campaign_sync"
  | "commerce"
  | "distribution"
  | "merch"
  | "publishing"
  | "social"
  | "streaming"
  | "vinyl";

export type ConnectorImportAuditMode =
  | "in_memory"
  | "postgres";

export type ConnectorStatus =
  | "blocked"
  | "configured"
  | "disconnected"
  | "mock"
  | "ready";

export type ConnectorSyncMode =
  | "disabled"
  | "manual"
  | "mock";

export type ConnectorType =
  | "discord"
  | "ditto"
  | "instagram"
  | "manual"
  | "printful"
  | "shopify"
  | "soundcloud"
  | "spotify"
  | "tiktok"
  | "tiktok_shop"
  | "youtube";

export type ConsentSourceType =
  | "character_persona"
  | "licensed"
  | "test_voice"
  | "user_owned";

export type CorrelationSignal =
  | "campaign_to_streaming"
  | "discord_to_conversion"
  | "instagram_to_merch"
  | "merch_to_followers"
  | "release_to_shop"
  | "soundcloud_to_vinyl"
  | "tiktok_to_streaming";

export type CorrelationStrength =
  | "explosive"
  | "medium"
  | "strong"
  | "weak";

export type DistributionPackStatus =
  | "draft"
  | "live"
  | "ready"
  | "rejected"
  | "submitted"
  | "takedown";

export type DistributionProvider = "ditto";

export type DistributionRepositoryMode =
  | "in_memory"
  | "postgres";

export type DistributionStore =
  | "amazon_music"
  | "apple_music"
  | "deezer"
  | "instagram_facebook"
  | "spotify"
  | "tidal"
  | "tiktok"
  | "youtube_music";

export type DropboxSyncProviderMode =
  | "dropbox"
  | "mock";

export type DropboxSyncStatus =
  | "failed"
  | "planned"
  | "ready_for_sync"
  | "synced"
  | "syncing";

export type DruckPreset =
  | "club"
  | "crushed"
  | "glued"
  | "open"
  | "redline"
  | "soundsystem";

export type EffectDeviceType =
  | "chorus"
  | "compressor"
  | "distortion"
  | "dub_delay"
  | "eq"
  | "filter"
  | "flanger"
  | "gate"
  | "limiter"
  | "phaser"
  | "plate_reverb"
  | "resampler"
  | "reverse"
  | "saturation"
  | "sidechain"
  | "spring_reverb"
  | "stutter"
  | "tape_stop"
  | "transient_shaper";

export type Energy =
  | "demonic"
  | "destructive"
  | "euphoric"
  | "hypnotic"
  | "warehouse";

export type EnergyLevel =
  | "drop"
  | "high"
  | "low"
  | "medium"
  | "peak";

export type Engine =
  | "ACE_STEP"
  | "MOCK"
  | "STABLE_AUDIO_OPEN"
  | "YUE";

export type ExportPackStatus =
  | "complete"
  | "draft"
  | "failed";

export type ExportProfile =
  | "club_master_wav_24_48"
  | "hd_master_wav_24_96"
  | "premaster_wav_32_float"
  | "stem_pack_wav_24_48"
  | "streaming_ready_wav_24_441";

export type IntelligenceSnapshotRepositoryMode =
  | "in_memory"
  | "postgres";

export type IntelligenceSnapshotStatus =
  | "archived"
  | "created"
  | "superseded";

export type Intent =
  | "BUILD_RIDDIM"
  | "CHARACTER_VOICE"
  | "COVER_GENERATION"
  | "CREATE_TRACK"
  | "CREATE_VOCALS"
  | "DUB_FX_LAB"
  | "GENERATE_HOOK"
  | "PROMPT_LIBRARY"
  | "STEM_REMIX"
  | "STYLE_DNA_SYSTEM";

export type JobEventType =
  | "artifact.ready"
  | "dropbox.exported"
  | "engine.loaded"
  | "generation.progress"
  | "generation.started"
  | "job.cancelled"
  | "job.created"
  | "job.failed"
  | "job.queued"
  | "preflight.blocked"
  | "preflight.passed"
  | "prompt.compiled"
  | "safety.started"
  | "stems.started"
  | "worker.assigned";

export type JobQueueMode =
  | "in_memory"
  | "redis";

export type JobStatus =
  | "ANALYZING_SAFETY"
  | "CANCELLED"
  | "DRAFT"
  | "EXPORTED"
  | "EXPORT_READY"
  | "FAILED"
  | "PREFLIGHT_BLOCKED"
  | "QUEUED"
  | "RENDERING_STEMS"
  | "RUNNING";

export type LibraryRepositoryMode =
  | "in_memory"
  | "postgres";

export type LicenseStatus =
  | "approved"
  | "needs_review"
  | "rejected"
  | "superseded";

export type LyricsProviderMode =
  | "gpt_5_5"
  | "mock";

export type LyricsRepositoryMode =
  | "in_memory"
  | "postgres";

export type LyricsSectionType =
  | "bridge"
  | "chorus"
  | "dub_breakdown"
  | "instrumental_opening"
  | "outro"
  | "pre_chorus"
  | "verse";

export type LyricsSource =
  | "gpt_5_5"
  | "mock"
  | "user";

export type MasterJobStatus =
  | "CANCELLED"
  | "DRAFT"
  | "EXPORT_READY"
  | "FAILED"
  | "QUEUED"
  | "REFERENCE_BLOCKED"
  | "RUNNING";

export type MasteringMode =
  | "bass_heavy"
  | "club_pressure"
  | "dark_warehouse"
  | "dub_warmth"
  | "reference_match"
  | "vocal_forward";

export type MerchAvailability =
  | "always_on"
  | "limited"
  | "unavailable";

export type MerchCapsuleStatus =
  | "archived"
  | "draft"
  | "exported_mock"
  | "locked";

export type MerchProductType =
  | "beanie"
  | "heavyweight_tee"
  | "longsleeve"
  | "oversized_hoodie"
  | "poster"
  | "sticker_pack"
  | "tote"
  | "vinyl_object";

export type MerchProviderGroup =
  | "apparel_provider"
  | "premium_drop_provider"
  | "vinyl_provider";

export type MerchRepositoryMode =
  | "in_memory"
  | "postgres";

export type MusicArtifactType =
  | "dub_fx"
  | "full_mix"
  | "loop"
  | "master"
  | "prompt_manifest"
  | "soundgraph_manifest"
  | "stem_pack";

export type MusicIntentKind =
  | "build_riddim"
  | "create_loop"
  | "create_song_sketch"
  | "create_stem_track"
  | "dub_fx_lab"
  | "master_track";

export type MusicJobStatus =
  | "completed"
  | "failed"
  | "preflight_blocked"
  | "processing"
  | "queued";

export type MusicProviderGroup =
  | "dub_fx_provider"
  | "full_song_experimental_provider"
  | "high_fidelity_clip_provider"
  | "mastering_provider"
  | "music_loop_provider"
  | "stem_generation_provider";

export type MusicRouterReadiness =
  | "blocked"
  | "mock_only"
  | "not_wired";

export type NewsletterSubscribeStatus =
  | "failed"
  | "offline"
  | "pending"
  | "subscribed";

export type PrintfulPrintTechnique =
  | "dtg"
  | "embroidery"
  | "not_applicable"
  | "sublimation";

export type PrintfulProviderMode =
  | "mock"
  | "printful";

export type PrintfulSyncStatus =
  | "blocked"
  | "draft"
  | "exported_mock"
  | "failed";

export type ProviderGroup =
  | "full_song_experimental_provider"
  | "high_fidelity_clip_provider"
  | "mastering_provider"
  | "music_loop_provider"
  | "offline_fallback_provider"
  | "singing_voice_provider"
  | "stem_separation_provider"
  | "voice_clone_provider"
  | "voice_tts_provider";

export type RegionRole =
  | "breakdown"
  | "bridge"
  | "chorus"
  | "drop"
  | "intro"
  | "outro"
  | "pre_chorus"
  | "verse";

export type ReleaseExportStatus =
  | "building"
  | "completed"
  | "failed";

export type ReleasePackStatus =
  | "draft"
  | "published"
  | "ready";

export type ReleaseRepositoryMode =
  | "in_memory"
  | "postgres";

export type RewriteStrategy =
  | "initial_generation"
  | "manual"
  | "prompt_edit"
  | "provider_regen"
  | "selection_rewrite";

export type RiskTier =
  | "amber"
  | "green"
  | "red";

export type SafetyReviewStatus =
  | "approved"
  | "needs_changes"
  | "pending"
  | "rejected";

export type ShopifyDraftStatus =
  | "blocked"
  | "draft"
  | "exported_mock"
  | "failed";

export type ShopifyProviderMode =
  | "mock"
  | "shopify";

export type SnapshotDiffDirection =
  | "declined"
  | "improved"
  | "mixed"
  | "unchanged";

export type SoundCloudProviderMode =
  | "mock"
  | "soundcloud";

export type SoundCloudPublishStatus =
  | "blocked"
  | "draft"
  | "failed"
  | "published_mock"
  | "ready";

export type StemLaneType =
  | "atmosphere"
  | "bass"
  | "drums"
  | "fx"
  | "kick"
  | "lead"
  | "music"
  | "percussion"
  | "return_delay"
  | "return_reverb"
  | "vocals_adlibs"
  | "vocals_main";

export type StemSourceType =
  | "generated_direct"
  | "imported"
  | "manual_edit"
  | "repainted"
  | "source_separated";

export type Structure =
  | "instant_drop"
  | "long_breakdown"
  | "mantra_hook"
  | "no_intro"
  | "stem_heavy";

export type TempoFeel =
  | "broken"
  | "double_time"
  | "double_time_hats"
  | "half_time"
  | "half_time_pressure"
  | "stepping"
  | "straight"
  | "swung";

export type TikTokShopContentAngle =
  | "collector_object"
  | "limited_capsule"
  | "political_drop"
  | "soundsystem_essential"
  | "warehouse_culture";

export type TikTokShopListingStatus =
  | "blocked"
  | "draft"
  | "exported_mock"
  | "failed";

export type TikTokShopProviderMode =
  | "mock"
  | "tiktok_shop";

export type TrendDirection =
  | "down"
  | "exploding"
  | "rising"
  | "stable";

export type VinylEditionType =
  | "collector_box"
  | "limited_numbered"
  | "vinyl_on_demand"
  | "white_label";

export type VinylFormat =
  | "dubplate"
  | "lathe_cut"
  | "seven_inch"
  | "ten_inch"
  | "twelve_inch";

export type VinylProviderGroup =
  | "disc_archive"
  | "elastic_stage"
  | "manual_collector"
  | "vinylograph";

export type VinylReleaseStatus =
  | "approved"
  | "archived"
  | "blocked"
  | "draft"
  | "live"
  | "ready"
  | "submitted"
  | "test_pressing";

export type VinylRepositoryMode =
  | "in_memory"
  | "postgres";

export type VocalEntry =
  | "adlibs"
  | "main"
  | "none"
  | "spoken"
  | "whisper";

export type Vocals =
  | "haunting"
  | "melodic"
  | "ritual"
  | "smoky"
  | "whisper";

export type VoiceJobKind =
  | "convert_approved_voice"
  | "create_spoken_vocal"
  | "create_voice_tag";

export type VoiceJobStatus =
  | "complete"
  | "draft"
  | "failed"
  | "preflight_blocked"
  | "processing";

// ---- Models (Pydantic BaseModel subclasses) ----

export type AnalyticsEvent = Readonly<{
  event_id: string;
  source: AnalyticsSource;
  metric: AnalyticsMetric;
  value: number;
  granularity: AnalyticsGranularity;
  campaign_id: string | null;
  release_id: string | null;
  track_id: string | null;
  merch_capsule_id: string | null;
  vinyl_id: string | null;
  timestamp: string;
  metadata: Readonly<Record<string, string>>;
}>;

export type AnalyticsEventCreateRequest = Readonly<{
  source: AnalyticsSource;
  metric: AnalyticsMetric;
  value: number;
  granularity?: AnalyticsGranularity;
  campaign_id?: string | null;
  release_id?: string | null;
  track_id?: string | null;
  merch_capsule_id?: string | null;
  vinyl_id?: string | null;
  metadata?: Readonly<Record<string, string>>;
}>;

export type AnalyticsSnapshot = Readonly<{
  snapshot_id: string;
  source: AnalyticsSource;
  metric: AnalyticsMetric;
  aggregate_value: number;
  period_start: string;
  period_end: string;
  dimensions: Readonly<Record<string, string>>;
  created_at: string;
}>;

export type AnalyticsSummary = Readonly<{
  total_events: number;
  total_campaigns: number;
  total_tracks: number;
  source_breakdown: Readonly<Record<string, number>>;
  metric_breakdown: Readonly<Record<string, number>>;
  latest_event_at: string | null;
}>;

export type ArrangementRegion = Readonly<{
  region_index: number;
  section_index: number;
  role: RegionRole;
  label: string;
  bar_start: number;
  bar_count: number;
  vocal_entry: VocalEntry;
  energy: EnergyLevel;
  lanes_active: ReadonlyArray<StemLaneType>;
  lanes_muted: ReadonlyArray<StemLaneType>;
  locked: boolean;
  notes: string | null;
}>;

export type ArtifactCreateRequest = Readonly<{
  kind: ArtifactKind;
  logical_path: string;
  content_type?: string;
  source_entity_type?: string | null;
  source_entity_id?: string | null;
  provenance_id?: string | null;
}>;

export type ArtifactDownloadLink = Readonly<{
  artifact_id: string;
  url: string;
  expires_at: string | null;
}>;

export type ArtifactManifest = Readonly<{
  full_mix_wav: string | null;
  stems: ReadonlyArray<string>;
  stem_lanes: ReadonlyArray<StemArtifact>;
  soundgraph_manifest_json: string | null;
  lyrics: string | null;
  prompt_json: string | null;
  metadata_json: string | null;
  cover_image: string | null;
  safety_report_json: string | null;
  generation_history_json: string | null;
}>;

export type ArtifactRecord = Readonly<{
  artifact_id: string;
  kind: ArtifactKind;
  status: ArtifactStatus;
  storage_mode: "local" | "s3";
  logical_path: string;
  storage_key: string | null;
  content_type: string;
  size_bytes: number | null;
  checksum_sha256: string | null;
  operator_id: string | null;
  source_entity_type: string | null;
  source_entity_id: string | null;
  provenance_id: string | null;
  created_at: string;
  updated_at: string;
}>;

export type ArtifactSignedUrl = Readonly<{
  artifact_id: string;
  url: string;
  expires_at: string | null;
  access_mode: "direct" | "signed";
  method: "GET";
}>;

export type ArtifactStorageSummary = Readonly<{
  total: number;
  planned: number;
  stored: number;
  missing: number;
  deleted: number;
  failed: number;
  total_size_bytes: number;
  storage_mode: string;
}>;

export type ArtifactUploadRequest = Readonly<{
  content_base64: string;
  content_type?: string | null;
}>;

export type AsyncJob = Readonly<{
  job_id: string;
  kind: AsyncJobKind;
  status: AsyncJobStatus;
  payload: unknown;
  result: AsyncJobResult | null;
  progress: AsyncJobProgress;
  events: ReadonlyArray<AsyncJobEvent>;
  retries: number;
  max_retries: number;
  operator_id: string | null;
  created_at: string;
  updated_at: string;
}>;

export type AsyncJobCreateRequest = Readonly<{
  kind: AsyncJobKind;
  payload?: unknown;
  max_retries?: number;
}>;

export type AsyncJobEvent = Readonly<{
  event_type: string;
  detail: string | null;
  created_at: string;
}>;

export type AsyncJobProgress = Readonly<{
  progress: number;
  message: string | null;
  updated_at: string;
}>;

export type AsyncJobResult = Readonly<{
  data: unknown | null;
  error: string | null;
}>;

export type AsyncJobSummary = Readonly<{
  total: number;
  queued: number;
  running: number;
  succeeded: number;
  failed: number;
  cancelled: number;
  retrying: number;
}>;

export type AudienceHeatmap = Readonly<{
  platform: AnalyticsSource;
  audience_size: number;
  engagement: number;
  conversion_rate: number;
  heat_score: number;
  trend: TrendDirection;
}>;

export type AudioMasterUploadRequest = Readonly<{
  filename: string;
  content_type: string;
  content_base64: string;
}>;

export type AudioMasterUploadResult = Readonly<{
  release: ReleasePack;
  artifact: ArtifactRecord;
  warnings: ReadonlyArray<AudioValidationWarning>;
  channels: number | null;
  sample_rate: number | null;
  sample_width_bytes: number | null;
  duration_seconds: number | null;
}>;

export type AudioValidationWarning = Readonly<{
  code: string;
  message: string;
}>;

export type AuditEvent = Readonly<{
  event_id: string;
  operator_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  payload_summary: Readonly<Record<string, string | number | boolean | null>>;
  created_at: string;
}>;

export type AuditEventCreateRequest = Readonly<{
  operator_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  payload_summary?: Readonly<Record<string, string | number | boolean | null>>;
}>;

export type AutomationExecutionAuditRecord = Readonly<{
  audit_id: string;
  execution_id: string;
  rule_id: string;
  campaign_id: string;
  from_status: AutomationExecutionStatus | null;
  to_status: AutomationExecutionStatus;
  operator_id: string | null;
  reason: string | null;
  details: Readonly<Record<string, unknown>>;
  created_at: string;
}>;

export type AutomationExecutionAuditSummary = Readonly<{
  total_records: number;
  by_to_status: Readonly<Record<string, number>>;
  by_reason: Readonly<Record<string, number>>;
  operator_breakdown: Readonly<Record<string, number>>;
  latest_record_at: string | null;
}>;

export type AutomationExecutionCreateRequest = Readonly<{
  rule_id: string;
}>;

export type AutomationExecutionJob = Readonly<{
  execution_id: string;
  rule_id: string;
  campaign_id: string;
  dry_run_status: CampaignAutomationDryRunStatus;
  status: AutomationExecutionStatus;
  proposed_changes: ReadonlyArray<string>;
  blocked_reasons: ReadonlyArray<string>;
  warnings: ReadonlyArray<string>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}>;

export type AutomationExecutionResult = Readonly<{
  job: AutomationExecutionJob;
  note: string;
}>;

export type AutomationExecutionSummary = Readonly<{
  total: number;
  queued: number;
  blocked: number;
  completed_mock: number;
  failed: number;
  execution_mode: AutomationExecutionMode;
}>;

export type Campaign = Readonly<{
  campaign_id: string;
  release_id: string;
  title: string;
  status: CampaignStatus;
  channels: ReadonlyArray<CampaignChannel>;
  tasks: ReadonlyArray<CampaignTask>;
  timeline: ReadonlyArray<CampaignTimelineItem>;
  linked_merch_capsule_ids: ReadonlyArray<string>;
  linked_distribution_pack_ids: ReadonlyArray<string>;
  linked_soundcloud_job_ids: ReadonlyArray<string>;
  warnings: ReadonlyArray<CampaignWarning>;
  notes: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type CampaignAutomationDryRunResult = Readonly<{
  rule_id: string;
  campaign_id: string;
  status: CampaignAutomationDryRunStatus;
  matched: boolean;
  blocked_reasons: ReadonlyArray<string>;
  proposed_changes: ReadonlyArray<string>;
  warnings: ReadonlyArray<string>;
  evaluated_at: string;
}>;

export type CampaignAutomationRule = Readonly<{
  rule_id: string;
  campaign_id: string | null;
  name: string;
  status: CampaignAutomationRuleStatus;
  trigger: CampaignAutomationTrigger;
  action: CampaignAutomationAction;
  conditions: Readonly<Record<string, unknown>>;
  action_payload: Readonly<Record<string, unknown>>;
  warnings: ReadonlyArray<string>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type CampaignAutomationRuleCreateRequest = Readonly<{
  campaign_id?: string | null;
  name: string;
  trigger: CampaignAutomationTrigger;
  action: CampaignAutomationAction;
  conditions?: Readonly<Record<string, unknown>>;
  action_payload?: Readonly<Record<string, unknown>>;
}>;

export type CampaignAutomationRuleSummary = Readonly<{
  total_rules: number;
  draft: number;
  active: number;
  paused: number;
  archived: number;
}>;

export type CampaignAutomationRuleTemplate = Readonly<{
  template_id: string;
  slug: string;
  name: string;
  description: string;
  category: CampaignAutomationTemplateCategory;
  trigger: CampaignAutomationTrigger;
  action: CampaignAutomationAction;
  default_conditions: Readonly<Record<string, unknown>>;
  default_action_payload: Readonly<Record<string, unknown>>;
  warnings: ReadonlyArray<string>;
  enabled: boolean;
}>;

export type CampaignAutomationRuleUpdateRequest = Readonly<{
  name?: string | null;
  status?: CampaignAutomationRuleStatus | null;
  trigger?: CampaignAutomationTrigger | null;
  action?: CampaignAutomationAction | null;
  conditions?: Readonly<Record<string, unknown>> | null;
  action_payload?: Readonly<Record<string, unknown>> | null;
}>;

export type CampaignAutomationTemplateInstantiationRequest = Readonly<{
  campaign_id: string;
  override_name?: string | null;
  condition_overrides?: Readonly<Record<string, unknown>>;
  action_payload_overrides?: Readonly<Record<string, unknown>>;
}>;

export type CampaignAutomationTemplateSummary = Readonly<{
  total_templates: number;
  enabled_templates: number;
  by_category: Readonly<Record<string, number>>;
}>;

export type CampaignCreateRequest = Readonly<{
  release_id: string;
  channels?: ReadonlyArray<CampaignChannel>;
  notes?: string;
}>;

export type CampaignPerformance = Readonly<{
  campaign_id: string;
  total_reach: number;
  engagement: number;
  conversions: number;
  revenue_estimate: number;
  heat_score: number;
  top_channel: AnalyticsSource | null;
  warnings: ReadonlyArray<string>;
}>;

export type CampaignSummary = Readonly<{
  total_campaigns: number;
  planning: number;
  ready: number;
  active: number;
  completed: number;
  archived: number;
  total_tasks: number;
  completed_tasks: number;
  blocked_tasks: number;
}>;

export type CampaignTask = Readonly<{
  task_id: string;
  channel: CampaignChannel;
  title: string;
  description: string;
  status: CampaignTaskStatus;
  depends_on: ReadonlyArray<string>;
  linked_object_id: string | null;
  warnings: ReadonlyArray<string>;
}>;

export type CampaignTimelineItem = Readonly<{
  timestamp: string;
  event: string;
  object_type: string;
  object_id: string | null;
  notes: string;
}>;

export type CampaignUpdateRequest = Readonly<{
  status?: CampaignStatus | null;
  channels?: ReadonlyArray<CampaignChannel> | null;
  notes?: string | null;
}>;

export type CampaignWarning = Readonly<{
  code: string;
  message: string;
}>;

export type CapabilitiesResponse = Readonly<{
  service: "snuffraga-soundsystem-inference";
  engines: ReadonlyArray<Engine>;
  intents: ReadonlyArray<Intent>;
  prompt_modules: Readonly<Record<string, ReadonlyArray<string>>>;
  providers: ReadonlyArray<ProviderCapability>;
  stem_lanes: ReadonlyArray<StemLaneType>;
  effect_devices: ReadonlyArray<EffectDeviceType>;
  mastering_modes: ReadonlyArray<MasteringMode>;
  export_profiles: ReadonlyArray<ExportProfile>;
  lyrics_section_types: ReadonlyArray<LyricsSectionType>;
  lyrics_sources: ReadonlyArray<LyricsSource>;
  lyrics_repository_mode: LyricsRepositoryMode;
  compliance_repository_mode: "in_memory" | "postgres";
  compliance_registry_available: boolean;
  compliance_preflight_available: boolean;
  voice_lab_available: boolean;
  music_router_available: boolean;
  music_router_mode: "mock";
  available_music_intents: ReadonlyArray<string>;
  soundgraph_writer_available: boolean;
  export_pack_available: boolean;
  library_repository_mode: "in_memory" | "postgres";
  dropbox_sync_available: boolean;
  dropbox_sync_provider_mode: "mock" | "dropbox";
  release_pack_available: boolean;
  release_repository_mode: "in_memory" | "postgres";
  auth_enabled: boolean;
  auth_mode: "open" | "api_key";
  job_queue_available: boolean;
  job_queue_mode: "in_memory" | "redis";
  async_jobs_available: boolean;
  artifact_storage_available: boolean;
  artifact_storage_mode: "local" | "s3";
  artifact_registry_mode: "in_memory" | "postgres";
  artifact_access_mode: "direct" | "signed";
  soundcloud_publish_available: boolean;
  soundcloud_provider_mode: "mock" | "soundcloud";
  merch_capsules_available: boolean;
  merch_provider_mode: "mock";
  merch_repository_mode: "in_memory" | "postgres";
  ditto_distribution_available: boolean;
  distribution_provider_mode: "mock";
  distribution_repository_mode: "in_memory" | "postgres";
  shopify_drafts_available: boolean;
  shopify_provider_mode: "mock" | "shopify";
  shopify_live_draft_sync_available: boolean;
  printful_sync_available: boolean;
  printful_provider_mode: "mock" | "printful";
  printful_live_product_sync_available: boolean;
  commerce_sync_dashboard_available: boolean;
  commerce_sync_audit_available: boolean;
  commerce_sync_audit_mode: "in_memory" | "postgres";
  newsletter_subscribe_available: boolean;
  newsletter_listmonk_configured: boolean;
  tiktok_shop_available: boolean;
  tiktok_shop_provider_mode: "mock" | "tiktok_shop";
  campaign_os_available: boolean;
  campaign_repository_mode: string;
  campaign_automation_rules_available: boolean;
  campaign_automation_templates_available: boolean;
  release_command_center_available: boolean;
  automation_execution_boundary_available: boolean;
  automation_execution_mode: "disabled" | "mock";
  automation_execution_repository_mode: "in_memory" | "postgres";
  automation_execution_audit_available: boolean;
  automation_execution_audit_mode: "in_memory" | "postgres";
  vinyl_releases_available: boolean;
  vinyl_provider_mode: "manual_handoff" | "elastic_stage" | "disc_archive";
  vinyl_repository_mode: string;
  analytics_graph_available: boolean;
  analytics_repository_mode: string;
  intelligence_engine_available: boolean;
  provider_connector_framework_available: boolean;
  mock_platform_connectors_available: boolean;
  connector_import_audit_available: boolean;
  intelligence_snapshots_available: boolean;
  intelligence_snapshot_repository_mode: string;
}>;

export type ChannelPerformance = Readonly<{
  source: AnalyticsSource;
  total_events: number;
  total_value: number;
  top_metric: AnalyticsMetric | null;
  top_metric_value: number;
}>;

export type CommandCenterReadinessItem = Readonly<{
  code: string;
  label: string;
  status: CommandCenterReadinessStatus;
  linked_object_id: string | null;
  warnings: ReadonlyArray<string>;
}>;

export type CommandCenterRecommendedTemplate = Readonly<{
  template_slug: string;
  name: string;
  reason: string;
  already_attached: boolean;
  warnings: ReadonlyArray<string>;
}>;

export type CommerceCapsuleSyncResult = Readonly<{
  capsule_id: string;
  shopify_result: ShopifyDraftExport | null;
  printful_result: PrintfulSyncExport | null;
  overall_status: CommerceSyncStatus;
  state: CommerceCapsuleSyncState;
  warnings: ReadonlyArray<string>;
}>;

export type CommerceCapsuleSyncState = Readonly<{
  capsule_id: string;
  release_id: string;
  title: string;
  product_count: number;
  shopify: CommerceSyncProviderState;
  printful: CommerceSyncProviderState;
  overall_status: CommerceSyncStatus;
  warnings: ReadonlyArray<string>;
}>;

export type CommerceSyncAuditRecord = Readonly<{
  audit_id: string;
  capsule_id: string;
  release_id: string | null;
  operator_id: string | null;
  action: CommerceSyncAuditAction;
  overall_status: CommerceSyncStatus;
  shopify_status: CommerceSyncStatus | null;
  printful_status: CommerceSyncStatus | null;
  shopify_item_count: number;
  printful_item_count: number;
  warnings: ReadonlyArray<string>;
  details: Readonly<Record<string, unknown>>;
  created_at: string;
}>;

export type CommerceSyncAuditSummary = Readonly<{
  total_records: number;
  records_by_action: Readonly<Record<string, number>>;
  records_by_status: Readonly<Record<string, number>>;
  latest_record_at: string | null;
  total_shopify_items: number;
  total_printful_items: number;
}>;

export type CommerceSyncProviderState = Readonly<{
  provider: CommerceSyncProvider;
  status: CommerceSyncStatus;
  provider_mode: string;
  item_count: number;
  synced_item_count: number;
  blocked_item_count: number;
  failed_item_count: number;
  provider_ids: ReadonlyArray<string>;
  warnings: ReadonlyArray<string>;
  last_synced_at: string | null;
}>;

export type CommerceSyncSummary = Readonly<{
  total_capsules: number;
  not_synced: number;
  synced_mock: number;
  synced_live: number;
  partial: number;
  blocked: number;
  failed: number;
  shopify_provider_mode: "mock" | "shopify";
  printful_provider_mode: "mock" | "printful";
}>;

export type CompiledLyricsPrompt = Readonly<{
  instruction: string;
  negative_prompt: string;
  safety_notes: ReadonlyArray<string>;
  suno_compat_notes: ReadonlyArray<string>;
  soundgraph_compat_notes: ReadonlyArray<string>;
  structure: ReadonlyArray<LyricsSectionType>;
  risky_filler_patterns: ReadonlyArray<string>;
}>;

export type CompiledPrompt = Readonly<{
  prompt_text: string;
  negative_prompt: string;
  safety_notes: ReadonlyArray<string>;
  engine_hints: Readonly<Record<string, string | number | boolean | null>>;
  stem_plan: StemPlan;
  tempo: TempoControls;
  druck: DruckControls;
  effect_racks: ReadonlyArray<EffectRack>;
  requested_effects: ReadonlyArray<EffectDeviceType>;
}>;

export type CompiledPromptRequest = Readonly<{
  intent: Intent;
  prompt_modules: PromptModules;
  character_code?: string;
  lyrics?: string | null;
  technical?: TechnicalControls;
  tempo?: TempoControls | null;
  druck?: DruckControls | null;
  requested_effects?: ReadonlyArray<EffectDeviceType>;
  target_lane?: StemLaneType | null;
  locked_lanes?: ReadonlyArray<StemLaneType>;
}>;

export type ComplianceChecklistItem = Readonly<{
  code: string;
  label: string;
  passed: boolean;
  notes: string | null;
}>;

export type CompliancePreflightRequest = Readonly<{
  intent_code: string;
  provider_group?: ProviderGroup | null;
  prompt?: string | null;
  consent_required?: boolean;
  consent_record_ids?: ReadonlyArray<string>;
  requires_commercial?: boolean;
}>;

export type CompliancePreflightResult = Readonly<{
  ok: boolean;
  blocking_reasons: ReadonlyArray<string>;
  warning_reasons: ReadonlyArray<string>;
  preflight_codes: ReadonlyArray<string>;
}>;

export type ComplianceRegistrySummary = Readonly<{
  model_registry_count: number;
  license_registry_count: number;
  consent_records_count: number;
  output_provenance_count: number;
  audit_events_count: number;
  repository_mode: "in_memory" | "postgres";
}>;

export type ConnectorHealth = Readonly<{
  connector_type: ConnectorType;
  status: ConnectorStatus;
  healthy: boolean;
  warnings: ReadonlyArray<string>;
  missing_configuration: ReadonlyArray<string>;
  capabilities: ReadonlyArray<ConnectorCapability>;
}>;

export type ConnectorImportAuditRecord = Readonly<{
  audit_id: string;
  connector_type: ConnectorType;
  operator_id: string;
  event_count: number;
  event_ids: ReadonlyArray<string>;
  status: "completed" | "failed" | "partial";
  error_message: string | null;
  metadata: Readonly<Record<string, string>>;
  created_at: string;
}>;

export type ConnectorImportAuditSummary = Readonly<{
  total_imports: number;
  total_events_imported: number;
  connector_breakdown: Readonly<Record<string, number>>;
  operator_breakdown: Readonly<Record<string, number>>;
  latest_import_at: string | null;
}>;

export type ConnectorRegistrySummary = Readonly<{
  total_connectors: number;
  enabled_connectors: number;
  ready_connectors: number;
  mock_connectors: number;
  blocked_connectors: number;
  capability_breakdown: Readonly<Record<string, number>>;
  status_breakdown: Readonly<Record<string, number>>;
  warnings: ReadonlyArray<string>;
}>;

export type ConnectorSyncPreview = Readonly<{
  connector_type: ConnectorType;
  event_count: number;
  normalized_events: ReadonlyArray<AnalyticsEvent>;
  warnings: ReadonlyArray<string>;
  blocked_reasons: ReadonlyArray<string>;
}>;

export type ConsentRecord = Readonly<{
  consent_id: string;
  speaker_label: string;
  source_type: ConsentSourceType;
  permitted_uses: ReadonlyArray<string>;
  revoked_at: string | null;
  expires_at: string | null;
  notes: string | null;
  created_at: string;
}>;

export type ConsentRecordCreateRequest = Readonly<{
  speaker_label: string;
  source_type: ConsentSourceType;
  permitted_uses?: ReadonlyArray<string>;
  expires_at?: string | null;
  notes?: string | null;
}>;

export type CoverAssetUploadRequest = Readonly<{
  filename: string;
  content_type: string;
  content_base64: string;
}>;

export type CoverAssetUploadResult = Readonly<{
  release: ReleasePack;
  artifact: ArtifactRecord;
  warnings: ReadonlyArray<CoverValidationWarning>;
}>;

export type CoverValidationWarning = Readonly<{
  code: string;
  message: string;
}>;

export type DistributionPack = Readonly<{
  distribution_id: string;
  release_id: string;
  provider: DistributionProvider;
  status: DistributionPackStatus;
  metadata: DittoDistributionMetadata;
  readiness_checklist: ReadonlyArray<DistributionReadinessItem>;
  readiness_passed: boolean;
  store_targets: ReadonlyArray<DistributionStore>;
  operator_notes: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type DistributionPackCreateRequest = Readonly<{
  release_id: string;
  store_targets?: ReadonlyArray<DistributionStore>;
  notes?: string;
}>;

export type DistributionPackStatusUpdateRequest = Readonly<{
  status: DistributionPackStatus;
  notes?: string;
}>;

export type DistributionPackSummary = Readonly<{
  total_packs: number;
  drafts: number;
  ready: number;
  submitted: number;
  live: number;
  rejected: number;
  takedown: number;
}>;

export type DistributionReadinessItem = Readonly<{
  code: string;
  label: string;
  passed: boolean;
  notes: string | null;
}>;

export type DittoDistributionMetadata = Readonly<{
  artist: string;
  title: string;
  genre: string | null;
  language: string;
  explicit: boolean;
  copyright_line: string;
  isrc: string | null;
  upc: string | null;
  release_date: string | null;
  cover_artifact_id: string | null;
  audio_master_artifact_id: string | null;
  store_targets: ReadonlyArray<DistributionStore>;
}>;

export type DropboxExportPlan = Readonly<{
  plan_id: string;
  pack_id: string;
  pack_title: string;
  target_root: string;
  entries: ReadonlyArray<DropboxFolderEntry>;
  total_files: number;
  total_directories: number;
  created_at: string;
}>;

export type DropboxExportPlanCreateRequest = Readonly<{
  pack_id: string;
  target_root_override?: string | null;
  operator_id?: string | null;
}>;

export type DropboxFolderEntry = Readonly<{
  relative_path: string;
  source_component_type: string;
  source_label: string;
  size_hint: string | null;
  is_directory: boolean;
}>;

export type DropboxSyncJob = Readonly<{
  sync_id: string;
  pack_id: string;
  plan_id: string;
  status: DropboxSyncStatus;
  target_root: string;
  files_planned: number;
  files_synced: number;
  error: string | null;
  operator_id: string | null;
  created_at: string;
  updated_at: string;
}>;

export type DropboxSyncSummary = Readonly<{
  total_plans: number;
  total_sync_jobs: number;
  jobs_planned: number;
  jobs_ready: number;
  jobs_synced: number;
  jobs_failed: number;
}>;

export type DruckControls = Readonly<{
  preset: DruckPreset;
  sub_pressure: number;
  bass_body: number;
  transient_pressure: number;
  density: number;
  compression: number;
  distortion_pressure: number;
  air_control: number;
  headroom: number;
}>;

export type EffectDevice = Readonly<{
  device: EffectDeviceType;
  notes: string | null;
}>;

export type EffectRack = Readonly<{
  lane: StemLaneType;
  devices: ReadonlyArray<EffectDevice>;
}>;

export type EnergyMapPoint = Readonly<{
  region_index: number;
  bar: number;
  energy: EnergyLevel;
}>;

export type ExportPack = Readonly<{
  pack_id: string;
  title: string;
  status: ExportPackStatus;
  music_job_id: string;
  lyrics_version_id: string | null;
  arrangement_id: string | null;
  provenance_id: string | null;
  components: ReadonlyArray<ExportPackComponent>;
  total_components: number;
  estimated_duration_seconds: number | null;
  bpm: number | null;
  key_signature: string | null;
  intent: MusicIntentKind | null;
  operator_id: string | null;
  notes: string | null;
  created_at: string;
}>;

export type ExportPackComponent = Readonly<{
  component_type: string;
  component_id: string;
  label: string;
  path: string | null;
}>;

export type ExportPackCreateRequest = Readonly<{
  music_job_id: string;
  title?: string | null;
  operator_id?: string | null;
  notes?: string | null;
}>;

export type GenerationJob = Readonly<{
  id: string;
  project_id: string;
  intent: Intent;
  engine: Engine;
  status: JobStatus;
  progress: number;
  created_at: string;
  updated_at: string;
  compiled_prompt: CompiledPrompt;
  artifacts: ArtifactManifest;
  events: ReadonlyArray<JobEvent>;
  error: string | null;
}>;

export type GenerationRequest = Readonly<{
  project_id: string;
  intent: Intent;
  engine?: Engine;
  prompt_modules: PromptModules;
  character_code?: string;
  lyrics?: string | null;
  technical?: TechnicalControls;
  safety?: SafetyOptions;
  tempo?: TempoControls | null;
  druck?: DruckControls | null;
  requested_effects?: ReadonlyArray<EffectDeviceType>;
  target_lane?: StemLaneType | null;
  locked_lanes?: ReadonlyArray<StemLaneType>;
}>;

export type HealthResponse = Readonly<{
  status: string;
  service: string;
}>;

export type IntelligenceOverview = Readonly<{
  total_heat: number;
  hottest_platform: AnalyticsSource | null;
  hottest_release_id: string | null;
  hottest_campaign_id: string | null;
  viral_moments: ReadonlyArray<ViralMoment>;
  audience_heatmaps: ReadonlyArray<AudienceHeatmap>;
  revenue_correlations: ReadonlyArray<RevenueCorrelation>;
  timeline: ReadonlyArray<TimelineCorrelation>;
  trend: TrendDirection;
  warnings: ReadonlyArray<string>;
}>;

export type IntelligenceSnapshot = Readonly<{
  snapshot_id: string;
  status: IntelligenceSnapshotStatus;
  overview: IntelligenceOverview;
  event_count: number;
  source_event_latest_at: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type IntelligenceSnapshotCreateRequest = Readonly<{
  notes?: string | null;
}>;

export type IntelligenceSnapshotDiff = Readonly<{
  before_snapshot_id: string;
  after_snapshot_id: string;
  before_created_at: string;
  after_created_at: string;
  overall_direction: SnapshotDiffDirection;
  total_heat_delta: number;
  total_heat_delta_percent: number | null;
  platform_deltas: ReadonlyArray<SnapshotPlatformDelta>;
  viral_moment_deltas: ReadonlyArray<SnapshotViralMomentDelta>;
  revenue_delta: SnapshotMetricDelta | null;
  warning_changes: ReadonlyArray<string>;
  generated_at: string;
}>;

export type IntelligenceSnapshotSummary = Readonly<{
  total_snapshots: number;
  active_snapshots: number;
  archived_snapshots: number;
  latest_snapshot_at: string | null;
  latest_total_heat: number;
  heat_delta_from_previous: number | null;
}>;

export type JobEvent = Readonly<{
  event_type: JobEventType;
  detail: string | null;
  created_at: string;
}>;

export type LaneAssignment = Readonly<{
  lane: StemLaneType;
  active_regions: ReadonlyArray<number>;
  source: StemSourceType;
  notes: string | null;
}>;

export type LicenseRegistryCreateRequest = Readonly<{
  model_or_dataset_id: string;
  license_name: string;
  license_url?: string | null;
  permits_commercial: boolean;
  restrictions?: ReadonlyArray<string>;
  reviewed_by?: string | null;
  status?: LicenseStatus;
  notes?: string | null;
}>;

export type LicenseRegistryEntry = Readonly<{
  license_id: string;
  model_or_dataset_id: string;
  license_name: string;
  license_url: string | null;
  permits_commercial: boolean;
  restrictions: ReadonlyArray<string>;
  reviewed_by: string | null;
  reviewed_at: string | null;
  status: LicenseStatus;
  notes: string | null;
  created_at: string;
}>;

export type LyricsApplySelectionRewriteRequest = Readonly<{
  section_index: number;
  lines: ReadonlyArray<string>;
  lock?: boolean;
  summary?: string | null;
}>;

export type LyricsEditRequest = Readonly<{
  version_id: string;
  edit_prompt: string;
  target_section?: LyricsSectionType | null;
  target_section_index?: number | null;
  preserve_rhyme?: boolean;
  preserve_syllable_length?: boolean;
}>;

export type LyricsExportManifest = Readonly<{
  version_id: string;
  project_id: string;
  lyrics_txt_path: string;
  lyrics_json_path: string;
  vocal_notes: ReadonlyArray<VocalPerformanceNote>;
  section_index_map: Readonly<Record<string, number>>;
  safety_report_json_path: string | null;
}>;

export type LyricsGenerationRequest = Readonly<{
  project_key: string;
  prompt: string;
  character_code?: string;
  structure?: ReadonlyArray<LyricsSectionType> | null;
  target_language?: string;
  avoid_intro_singing?: boolean;
  preserve_rhyme?: boolean;
  preserve_syllable_length?: boolean;
  title?: string | null;
}>;

export type LyricsLine = Readonly<{
  index: number;
  text: string;
  syllables: number | null;
  rhyme_group: string | null;
  vocal_note: string | null;
}>;

export type LyricsLockToggleRequest = Readonly<{
  locked: boolean;
}>;

export type LyricsManualUpdateRequest = Readonly<{
  version_id: string;
  section_index: number;
  lines: ReadonlyArray<string>;
  lock?: boolean;
  notes?: string | null;
}>;

export type LyricsProject = Readonly<{
  id: string;
  project_key: string;
  title: string | null;
  character_code: string;
  created_at: string;
}>;

export type LyricsRewriteResponse = Readonly<{
  section_index: number;
  line_start_index: number;
  line_end_index: number;
  variants: ReadonlyArray<LyricsRewriteVariant>;
}>;

export type LyricsRewriteSelectionRequest = Readonly<{
  version_id: string;
  section_index: number;
  line_start_index: number;
  line_end_index: number;
  rewrite_prompt: string;
  variant_count?: number;
}>;

export type LyricsRewriteVariant = Readonly<{
  index: number;
  lines: ReadonlyArray<LyricsLine>;
  summary: string | null;
}>;

export type LyricsSection = Readonly<{
  index: number;
  section_type: LyricsSectionType;
  label: string;
  lines: ReadonlyArray<LyricsLine>;
  locked: boolean;
  manually_edited: boolean;
  source: LyricsSource;
  notes: string | null;
}>;

export type LyricsStructure = Readonly<{
  sections: ReadonlyArray<LyricsSection>;
  avoid_intro_singing: boolean;
  target_language: string;
}>;

export type LyricsVersion = Readonly<{
  id: string;
  project_id: string;
  version: number;
  structure: LyricsStructure;
  created_at: string;
  parent_version_id: string | null;
  edit_summary: string | null;
}>;

export type MasterArtifact = Readonly<{
  profile: ExportProfile;
  path: string;
  sample_rate: number;
  bit_depth: number;
  is_float: boolean;
}>;

export type MasterBusJob = Readonly<{
  id: string;
  generation_id: string;
  mode: MasteringMode;
  profiles: ReadonlyArray<ExportProfile>;
  status: MasterJobStatus;
  progress: number;
  created_at: string;
  updated_at: string;
  manifest: MasterBusManifest | null;
  error: string | null;
}>;

export type MasterBusManifest = Readonly<{
  generation_id: string;
  mode: MasteringMode;
  masters: ReadonlyArray<MasterArtifact>;
  manifest_json: string;
  pressure_report_json: string;
}>;

export type MasterBusRequest = Readonly<{
  generation_id: string;
  mode?: MasteringMode;
  profiles?: ReadonlyArray<ExportProfile>;
  reference_track_uri?: string | null;
}>;

export type MerchCapsule = Readonly<{
  capsule_id: string;
  release_id: string;
  title: string;
  artist: string;
  status: MerchCapsuleStatus;
  availability_strategy: string;
  products: ReadonlyArray<MerchProduct>;
  max_active_products: number;
  provider_groups: ReadonlyArray<MerchProviderGroup>;
  drop_window_start: string | null;
  drop_window_end: string | null;
  notes: string;
  warnings: ReadonlyArray<MerchCapsuleWarning>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type MerchCapsuleCreateRequest = Readonly<{
  release_id: string;
  notes?: string;
}>;

export type MerchCapsuleSummary = Readonly<{
  total_capsules: number;
  drafts: number;
  locked: number;
  exported_mock: number;
  archived: number;
  total_products: number;
  total_active_products: number;
}>;

export type MerchCapsuleWarning = Readonly<{
  code: string;
  message: string;
}>;

export type MerchExportPayload = Readonly<{
  capsule_id: string;
  release_id: string;
  title: string;
  artist: string;
  status: MerchCapsuleStatus;
  products: ReadonlyArray<MerchProduct>;
  provider_exports: ReadonlyArray<MerchProviderExportNotes>;
  warnings: ReadonlyArray<MerchCapsuleWarning>;
  tiktok_shop_notes: string;
  printful_notes: string;
  shopify_draft_notes: string;
  exported_at: string;
}>;

export type MerchProduct = Readonly<{
  product_id: string;
  title: string;
  product_type: MerchProductType;
  availability: MerchAvailability;
  provider_group: MerchProviderGroup;
  price_positioning: string;
  artwork_artifact_id: string | null;
  mockup_artifact_id: string | null;
  variants: ReadonlyArray<MerchVariant>;
  active: boolean;
}>;

export type MerchProductUpdateRequest = Readonly<{
  title?: string | null;
  active?: boolean | null;
  availability?: MerchAvailability | null;
  price_positioning?: string | null;
  artwork_artifact_id?: string | null;
  mockup_artifact_id?: string | null;
}>;

export type MerchProductUpdateResult = Readonly<{
  capsule: MerchCapsule;
  product: MerchProduct;
  warnings: ReadonlyArray<MerchCapsuleWarning>;
}>;

export type MerchProviderAggregation = Readonly<{
  capsule_id: string;
  capsule_title: string;
  capsule_status: string;
  product_count: number;
  active_product_count: number;
  providers: Readonly<Record<string, MerchProviderStatus>>;
  products: ReadonlyArray<MerchProviderProductStatus>;
  summary: MerchProviderAggregationSummary;
  aggregated_at: string;
}>;

export type MerchProviderAggregationSummary = Readonly<{
  total_warnings: number;
  ready_count: number;
  blocked_count: number;
  exported_mock_count: number;
  not_created_count: number;
}>;

export type MerchProviderExportNotes = Readonly<{
  provider_group: MerchProviderGroup;
  product_count: number;
  notes: string;
  status: string;
}>;

export type MerchProviderProductStatus = Readonly<{
  product_id: string;
  title: string;
  product_type: string;
  availability: string;
  active: boolean;
  shopify_status: string;
  printful_status: string;
  tiktok_status: string;
  shopify_warnings: ReadonlyArray<string>;
  printful_warnings: ReadonlyArray<string>;
  tiktok_warnings: ReadonlyArray<string>;
  total_warnings: number;
  stale: boolean;
}>;

export type MerchProviderStatus = Readonly<{
  provider: string;
  mode: string;
  total_products: number;
  exported_mock: number;
  blocked: number;
  draft: number;
  not_created: number;
  warnings: number;
}>;

export type MerchVariant = Readonly<{
  variant_id: string;
  label: string;
  sku_suffix: string;
  stock_limit: number | null;
}>;

export type ModelRegistryEntry = Readonly<{
  model_id: string;
  provider_group: ProviderGroup;
  adapter_key: string;
  display_name_internal: string;
  commercial_status: CommercialStatus;
  activation_status: ActivationStatus;
  risk_tier: RiskTier;
  license_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}>;

export type MusicArtifactManifest = Readonly<{
  artifact_type: MusicArtifactType;
  path: string;
  duration_seconds: number | null;
  format: string;
}>;

export type MusicGenerationRequest = Readonly<{
  intent: MusicIntentKind;
  title: string;
  prompt: string;
  duration_seconds?: number | null;
  bpm?: number | null;
  key?: string | null;
  language?: string | null;
  lyrics_project_key?: string | null;
  lyrics_version_number?: number | null;
  requested_lanes?: ReadonlyArray<StemLaneType>;
  locked_lanes?: ReadonlyArray<StemLaneType>;
  commercial_target?: CommercialStatus;
  operator_id?: string | null;
}>;

export type MusicJob = Readonly<{
  job_id: string;
  intent: MusicIntentKind;
  title: string;
  prompt: string;
  status: MusicJobStatus;
  router_decision: MusicRouterDecision | null;
  artifacts: ReadonlyArray<MusicArtifactManifest>;
  provenance_id: string | null;
  error: string | null;
  commercial_target: CommercialStatus;
  operator_id: string | null;
  created_at: string;
  updated_at: string;
}>;

export type MusicRouterDecision = Readonly<{
  intent: MusicIntentKind;
  provider_group: MusicProviderGroup;
  selected_adapter_key: string;
  readiness_state: MusicRouterReadiness;
  reason: string;
  compliance_preflight_ok: boolean;
  compliance_preflight_codes: ReadonlyArray<string>;
  provenance_id: string | null;
}>;

export type MusicRouterSummary = Readonly<{
  total_jobs: number;
  jobs_completed: number;
  jobs_blocked: number;
  jobs_failed: number;
  router_mode: "mock";
  available_intents: ReadonlyArray<MusicIntentKind>;
}>;

export type NewsletterSubscribeRequest = Readonly<{
  email: string;
  source?: string | null;
  tags?: ReadonlyArray<string>;
}>;

export type NewsletterSubscribeResponse = Readonly<{
  ok: boolean;
  status: NewsletterSubscribeStatus;
  message: string;
  email_hash: string;
}>;

export type OutputProvenance = Readonly<{
  provenance_id: string;
  artifact_id: string;
  artifact_kind: string;
  parent_provenance_id: string | null;
  provider: string | null;
  model: string | null;
  model_version: string | null;
  prompt: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  estimated_cost_usd: number | null;
  latency_ms: number | null;
  safety_notes: ReadonlyArray<string>;
  rewrite_strategy: RewriteStrategy;
  locked_sections_respected: boolean;
  raw_provider_trace_id: string | null;
  raw_operator_prompt: string | null;
  system_prompt_version: string | null;
  safety_transformations: ReadonlyArray<string>;
  license_bundle: ReadonlyArray<string>;
  consent_records: ReadonlyArray<string>;
  consent_required: boolean;
  commercial_status: CommercialStatus;
  safety_review_status: SafetyReviewStatus;
  created_at: string;
}>;

export type OutputProvenanceCreateRequest = Readonly<{
  artifact_id: string;
  artifact_kind: string;
  parent_provenance_id?: string | null;
  provider?: string | null;
  model?: string | null;
  model_version?: string | null;
  prompt?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  estimated_cost_usd?: number | null;
  latency_ms?: number | null;
  safety_notes?: ReadonlyArray<string>;
  rewrite_strategy: RewriteStrategy;
  locked_sections_respected?: boolean;
  raw_provider_trace_id?: string | null;
  raw_operator_prompt?: string | null;
  system_prompt_version?: string | null;
  safety_transformations?: ReadonlyArray<string>;
  license_bundle?: ReadonlyArray<string>;
  consent_records?: ReadonlyArray<string>;
  consent_required?: boolean;
  commercial_status?: CommercialStatus;
  safety_review_status?: SafetyReviewStatus;
}>;

export type PrintfulProductSync = Readonly<{
  sync_id: string;
  capsule_id: string;
  product_id: string;
  title: string;
  product_type: string;
  provider_catalog_hint: string;
  print_technique: PrintfulPrintTechnique;
  placement: string;
  variants: ReadonlyArray<PrintfulVariantSync>;
  artwork_artifact_id: string | null;
  mockup_artifact_id: string | null;
  provider_payload: unknown;
  status: PrintfulSyncStatus;
  warnings: ReadonlyArray<string>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type PrintfulSyncCreateRequest = Readonly<{
  capsule_id: string;
}>;

export type PrintfulSyncExport = Readonly<{
  capsule_id: string;
  syncs: ReadonlyArray<PrintfulProductSync>;
  provider_mode: string;
  total_products: number;
  total_warnings: number;
  exported_at: string;
}>;

export type PrintfulSyncSummary = Readonly<{
  total_syncs: number;
  draft_status: number;
  exported_mock: number;
  blocked: number;
  failed: number;
}>;

export type PrintfulVariantSync = Readonly<{
  variant_id: string;
  title: string;
  sku_suffix: string;
  size: string;
  color: string;
}>;

export type ProjectLibraryEntry = Readonly<{
  entry_id: string;
  pack_id: string;
  title: string;
  slug: string;
  intent: MusicIntentKind | null;
  status: ExportPackStatus;
  bpm: number | null;
  key_signature: string | null;
  estimated_duration_seconds: number | null;
  component_count: number;
  artifact_count: number;
  has_lyrics: boolean;
  has_arrangement: boolean;
  has_provenance: boolean;
  operator_id: string | null;
  created_at: string;
}>;

export type ProjectLibrarySummary = Readonly<{
  total_entries: number;
  total_packs: number;
  entries_with_lyrics: number;
  entries_with_arrangements: number;
  entries_with_provenance: number;
}>;

export type PromptModules = Readonly<{
  energy: Energy;
  bass_pressure: BassPressure;
  vocals: Vocals;
  atmosphere: Atmosphere;
  structure: Structure;
}>;

export type ProviderCapability = Readonly<{
  name: string;
  engine: Engine;
  available: boolean;
  fallback: boolean;
}>;

export type ProviderConnector = Readonly<{
  connector_id: string;
  connector_type: ConnectorType;
  status: ConnectorStatus;
  sync_mode: ConnectorSyncMode;
  capabilities: ReadonlyArray<ConnectorCapability>;
  enabled: boolean;
  mock_mode: boolean;
  last_sync_at: string | null;
  warnings: ReadonlyArray<string>;
  metadata: Readonly<Record<string, string>>;
}>;

export type ReleaseAssetPlaceholder = Readonly<{
  asset_type: string;
  label: string;
  expected_format: string;
  ready: boolean;
  path: string | null;
  artifact_id: string | null;
}>;

export type ReleaseCommandCenter = Readonly<{
  release_id: string;
  release_title: string;
  campaign_id: string | null;
  campaign_status: CampaignStatus | null;
  readiness_items: ReadonlyArray<CommandCenterReadinessItem>;
  recommended_templates: ReadonlyArray<CommandCenterRecommendedTemplate>;
  linked_merch_capsule_ids: ReadonlyArray<string>;
  linked_distribution_pack_ids: ReadonlyArray<string>;
  linked_vinyl_ids: ReadonlyArray<string>;
  automation_rule_count: number;
  dry_run_summary: Readonly<Record<string, number>>;
  warnings: ReadonlyArray<string>;
}>;

export type ReleaseCommandCenterBootstrapResult = Readonly<{
  command_center: ReleaseCommandCenter;
  created_campaign: boolean;
  instantiated_rule_ids: ReadonlyArray<string>;
  warnings: ReadonlyArray<string>;
}>;

export type ReleaseCommandCenterCreateRequest = Readonly<{
}>;

export type ReleaseEligibilityResult = Readonly<{
  artifact_id: string;
  provenance_id: string | null;
  eligible: boolean;
  blocking_reasons: ReadonlyArray<string>;
  warning_reasons: ReadonlyArray<string>;
  required_actions: ReadonlyArray<string>;
}>;

export type ReleaseExportEntry = Readonly<{
  path: string;
  source_asset_type: string;
  size_bytes: number;
  checksum_sha256: string;
  content_type: string;
}>;

export type ReleaseExportResult = Readonly<{
  export_id: string;
  release_id: string;
  artifact: ArtifactRecord;
  status: ReleaseExportStatus;
  entries: ReadonlyArray<ReleaseExportEntry>;
  warnings: ReadonlyArray<ReleaseExportWarning>;
  total_files: number;
  total_size_bytes: number;
  created_at: string;
}>;

export type ReleaseExportWarning = Readonly<{
  code: string;
  message: string;
}>;

export type ReleasePack = Readonly<{
  release_id: string;
  pack_id: string;
  title: string;
  artist: string;
  status: ReleasePackStatus;
  description: string;
  social_copy: SocialCopy;
  compliance_checklist: ReadonlyArray<ComplianceChecklistItem>;
  compliance_passed: boolean;
  assets: ReadonlyArray<ReleaseAssetPlaceholder>;
  dropbox_target: string | null;
  genre: string | null;
  bpm: number | null;
  key_signature: string | null;
  duration_seconds: number | null;
  operator_id: string | null;
  created_at: string;
  updated_at: string;
}>;

export type ReleasePackCreateRequest = Readonly<{
  pack_id: string;
  title?: string | null;
  artist: string;
  description?: string | null;
  genre?: string | null;
  operator_id?: string | null;
}>;

export type ReleasePackSummary = Readonly<{
  total_releases: number;
  drafts: number;
  ready: number;
  published: number;
  compliance_passed: number;
}>;

export type RevenueCorrelation = Readonly<{
  source: AnalyticsSource;
  revenue: number;
  related_metric: AnalyticsMetric | null;
  related_metric_value: number;
  conversion_strength: CorrelationStrength;
}>;

export type SafetyOptions = Readonly<{
  allow_reference_audio: boolean;
  allow_voice_likeness: boolean;
  release_candidate: boolean;
}>;

export type ShopifyDraftCreateRequest = Readonly<{
  capsule_id: string;
}>;

export type ShopifyDraftExport = Readonly<{
  capsule_id: string;
  drafts: ReadonlyArray<ShopifyProductDraft>;
  provider_mode: string;
  total_products: number;
  total_warnings: number;
  exported_at: string;
}>;

export type ShopifyDraftSummary = Readonly<{
  total_drafts: number;
  draft_status: number;
  exported_mock: number;
  blocked: number;
  failed: number;
}>;

export type ShopifyImageRef = Readonly<{
  artifact_id: string | null;
  alt: string;
  position: number;
}>;

export type ShopifyProductDraft = Readonly<{
  draft_id: string;
  capsule_id: string;
  product_id: string;
  title: string;
  body_html: string;
  vendor: string;
  product_type: string;
  tags: ReadonlyArray<string>;
  status: ShopifyDraftStatus;
  variants: ReadonlyArray<ShopifyVariantDraft>;
  images: ReadonlyArray<ShopifyImageRef>;
  provider_payload: unknown;
  warnings: ReadonlyArray<string>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type ShopifyVariantDraft = Readonly<{
  variant_id: string;
  title: string;
  sku_suffix: string;
  option1: string;
  price: string;
  requires_shipping: boolean;
  inventory_management: string | null;
  inventory_quantity: number | null;
}>;

export type SnapshotMetricDelta = Readonly<{
  metric: string;
  before_value: number;
  after_value: number;
  delta: number;
  delta_percent: number | null;
  direction: SnapshotDiffDirection;
}>;

export type SnapshotPlatformDelta = Readonly<{
  platform: AnalyticsSource;
  before_heat: number;
  after_heat: number;
  heat_delta: number;
  direction: SnapshotDiffDirection;
  engagement_delta: number;
  conversion_delta: number;
}>;

export type SnapshotViralMomentDelta = Readonly<{
  title: string;
  before_strength: CorrelationStrength | null;
  after_strength: CorrelationStrength | null;
  appeared: boolean;
  disappeared: boolean;
  direction: SnapshotDiffDirection;
}>;

export type SocialCopy = Readonly<{
  soundcloud_description: string;
  tiktok_caption: string;
  instagram_caption: string;
  hashtags: ReadonlyArray<string>;
}>;

export type SoundCloudMetadata = Readonly<{
  title: string;
  artist: string;
  description: string;
  tags: ReadonlyArray<string>;
  genre: string | null;
  release_date: string | null;
  is_private: boolean;
  downloadable: boolean;
  cover_artifact_id: string | null;
  audio_artifact_id: string | null;
  release_pack_id: string;
  export_artifact_id: string | null;
}>;

export type SoundCloudPublishJob = Readonly<{
  job_id: string;
  release_id: string;
  status: SoundCloudPublishStatus;
  metadata: SoundCloudMetadata;
  warnings: ReadonlyArray<SoundCloudPublishWarning>;
  provider_mode: string;
  operator_id: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}>;

export type SoundCloudPublishPreview = Readonly<{
  release_id: string;
  metadata: SoundCloudMetadata;
  warnings: ReadonlyArray<SoundCloudPublishWarning>;
  can_publish: boolean;
  blocked_reason: string | null;
}>;

export type SoundCloudPublishRequest = Readonly<{
  release_id: string;
}>;

export type SoundCloudPublishSummary = Readonly<{
  total_jobs: number;
  drafts: number;
  ready: number;
  published_mock: number;
  failed: number;
  blocked: number;
}>;

export type SoundCloudPublishWarning = Readonly<{
  code: string;
  message: string;
}>;

export type SoundGraphArrangement = Readonly<{
  arrangement_id: string;
  lyrics_version_id: string;
  project_key: string;
  bpm: number;
  time_signature: string;
  key_signature: string | null;
  total_bars: number;
  regions: ReadonlyArray<ArrangementRegion>;
  energy_map: ReadonlyArray<EnergyMapPoint>;
  lane_assignments: ReadonlyArray<LaneAssignment>;
  created_at: string;
}>;

export type SoundGraphHandoffRequest = Readonly<{
  arrangement_id: string;
  title?: string | null;
  operator_id?: string | null;
  commercial_target?: CommercialStatus;
  intent_override?: MusicIntentKind | null;
}>;

export type SoundGraphHandoffResult = Readonly<{
  music_job: MusicJob;
  resolved_intent: MusicIntentKind;
  requested_lanes: ReadonlyArray<StemLaneType>;
  locked_lanes: ReadonlyArray<StemLaneType>;
  estimated_duration_seconds: number;
  compiled_prompt: string;
}>;

export type SoundGraphManifest = Readonly<{
  soundgraph_id: string;
  bpm: number;
  key: string | null;
  sample_rate: number;
  lanes: ReadonlyArray<StemArtifact>;
  tempo: TempoControls;
  druck: DruckControls;
}>;

export type SoundGraphWriteRequest = Readonly<{
  lyrics_version_id: string;
  bpm?: number;
  time_signature?: string;
  key_signature?: string | null;
  bars_per_section_override?: Readonly<Record<string, number>> | null;
  energy_profile?: string;
}>;

export type SoundGraphWriteResult = Readonly<{
  arrangement: SoundGraphArrangement;
  warnings: ReadonlyArray<string>;
  section_count: number;
  total_bars: number;
  vocal_regions: number;
  instrumental_regions: number;
}>;

export type StemArtifact = Readonly<{
  lane: StemLaneType;
  path: string;
  source: StemSourceType;
  sample_rate: number;
  bit_depth: number;
}>;

export type StemLanePlan = Readonly<{
  lane: StemLaneType;
  source: StemSourceType;
  editable: boolean;
  locked: boolean;
  notes: string | null;
}>;

export type StemPackManifestEntry = Readonly<{
  filename: string;
  size_bytes: number;
  extension: string;
  is_audio: boolean;
}>;

export type StemPackUploadRequest = Readonly<{
  filename: string;
  content_type: string;
  content_base64: string;
}>;

export type StemPackUploadResult = Readonly<{
  release: ReleasePack;
  artifact: ArtifactRecord;
  warnings: ReadonlyArray<StemPackValidationWarning>;
  entries: ReadonlyArray<StemPackManifestEntry>;
  total_files: number;
  total_uncompressed_bytes: number;
}>;

export type StemPackValidationWarning = Readonly<{
  code: string;
  message: string;
}>;

export type StemPlan = Readonly<{
  lanes: ReadonlyArray<StemLanePlan>;
  locked_lanes: ReadonlyArray<StemLaneType>;
  target_lane: StemLaneType | null;
}>;

export type TechnicalControls = Readonly<{
  bpm: number | null;
  key: string | null;
  duration_seconds: number;
  seed: number | null;
  stems_required: boolean;
}>;

export type TempoControls = Readonly<{
  bpm: number;
  time_signature: string;
  feel: TempoFeel;
  swing: number;
  locked_grid: boolean;
}>;

export type TikTokShopListing = Readonly<{
  listing_id: string;
  capsule_id: string;
  product_id: string;
  title: string;
  description: string;
  category_hint: string;
  product_type: string;
  tags: ReadonlyArray<string>;
  content_angle: TikTokShopContentAngle;
  variants: ReadonlyArray<TikTokShopVariantListing>;
  images: ReadonlyArray<string>;
  provider_payload: unknown;
  status: TikTokShopListingStatus;
  warnings: ReadonlyArray<string>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type TikTokShopListingCreateRequest = Readonly<{
  capsule_id: string;
}>;

export type TikTokShopListingExport = Readonly<{
  capsule_id: string;
  listings: ReadonlyArray<TikTokShopListing>;
  provider_mode: string;
  total_products: number;
  total_warnings: number;
  exported_at: string;
}>;

export type TikTokShopSummary = Readonly<{
  total_listings: number;
  draft_status: number;
  exported_mock: number;
  blocked: number;
  failed: number;
}>;

export type TikTokShopVariantListing = Readonly<{
  variant_id: string;
  title: string;
  sku_suffix: string;
  option: string;
}>;

export type TimelineCorrelation = Readonly<{
  timestamp: string;
  event_count: number;
  dominant_source: AnalyticsSource | null;
  dominant_metric: AnalyticsMetric | null;
  heat: number;
}>;

export type TrackPerformance = Readonly<{
  track_id: string;
  title: string;
  total_streams: number;
  saves: number;
  shares: number;
  viral_score: number;
  top_platform: AnalyticsSource | null;
}>;

export type VinylExportPayload = Readonly<{
  vinyl_id: string;
  release_id: string;
  title: string;
  artist: string;
  provider_group: VinylProviderGroup;
  format: VinylFormat;
  edition_type: VinylEditionType;
  pressing_quantity: number | null;
  numbered: boolean;
  side_a_tracks: ReadonlyArray<VinylTrackListing>;
  side_b_tracks: ReadonlyArray<VinylTrackListing>;
  cover_artifact_id: string | null;
  audio_master_artifact_id: string | null;
  readiness_summary: string;
  warnings: ReadonlyArray<string>;
  handoff_notes: string;
  exported_at: string;
}>;

export type VinylReadinessItem = Readonly<{
  code: string;
  label: string;
  passed: boolean;
  warning: string;
}>;

export type VinylReleaseCreateRequest = Readonly<{
  release_id: string;
  format?: VinylFormat;
  edition_type?: VinylEditionType;
  pressing_quantity?: number | null;
  numbered?: boolean;
  notes?: string;
}>;

export type VinylReleaseObject = Readonly<{
  vinyl_id: string;
  release_id: string;
  title: string;
  artist: string;
  provider_group: VinylProviderGroup;
  status: VinylReleaseStatus;
  format: VinylFormat;
  edition_type: VinylEditionType;
  pressing_quantity: number | null;
  numbered: boolean;
  side_a_tracks: ReadonlyArray<VinylTrackListing>;
  side_b_tracks: ReadonlyArray<VinylTrackListing>;
  cover_artifact_id: string | null;
  audio_master_artifact_id: string | null;
  export_artifact_id: string | null;
  soundcloud_job_id: string | null;
  readiness_items: ReadonlyArray<VinylReadinessItem>;
  warnings: ReadonlyArray<string>;
  notes: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}>;

export type VinylReleaseStatusUpdateRequest = Readonly<{
  status: VinylReleaseStatus;
}>;

export type VinylReleaseSummary = Readonly<{
  total_releases: number;
  draft: number;
  ready: number;
  submitted: number;
  test_pressing: number;
  approved: number;
  live: number;
  archived: number;
  blocked: number;
}>;

export type VinylTrackListing = Readonly<{
  position: number;
  title: string;
  duration_seconds: number | null;
  artifact_id: string | null;
}>;

export type ViralMoment = Readonly<{
  moment_id: string;
  title: string;
  source: AnalyticsSource;
  trigger_metric: AnalyticsMetric;
  before_value: number;
  after_value: number;
  growth_percent: number;
  timestamp: string;
  related_release_id: string | null;
  related_campaign_id: string | null;
  strength: CorrelationStrength;
}>;

export type VocalPerformanceNote = Readonly<{
  section_index: number;
  note: string;
}>;

export type VoiceJob = Readonly<{
  job_id: string;
  kind: VoiceJobKind;
  status: VoiceJobStatus;
  voice_tag_id: string | null;
  consent_id: string | null;
  prompt: string | null;
  output_artifact_path: string | null;
  provenance_id: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}>;

export type VoiceJobCreateRequest = Readonly<{
  kind: VoiceJobKind;
  voice_tag_id?: string | null;
  consent_id?: string | null;
  prompt?: string | null;
}>;

export type VoiceLabSummary = Readonly<{
  voice_tag_count: number;
  voice_job_count: number;
  jobs_complete: number;
  jobs_blocked: number;
}>;

export type VoiceTag = Readonly<{
  tag_id: string;
  label: string;
  consent_id: string;
  provider_group: ProviderGroup;
  notes: string | null;
  created_at: string;
}>;

export type VoiceTagCreateRequest = Readonly<{
  label: string;
  consent_id: string;
  provider_group?: ProviderGroup;
  notes?: string | null;
}>;

