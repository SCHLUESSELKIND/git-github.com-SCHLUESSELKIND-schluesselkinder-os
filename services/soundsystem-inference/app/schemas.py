from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import LyricsRepositoryMode


class Intent(StrEnum):
    CREATE_TRACK = "CREATE_TRACK"
    BUILD_RIDDIM = "BUILD_RIDDIM"
    GENERATE_HOOK = "GENERATE_HOOK"
    CREATE_VOCALS = "CREATE_VOCALS"
    STEM_REMIX = "STEM_REMIX"
    DUB_FX_LAB = "DUB_FX_LAB"
    CHARACTER_VOICE = "CHARACTER_VOICE"
    COVER_GENERATION = "COVER_GENERATION"
    PROMPT_LIBRARY = "PROMPT_LIBRARY"
    STYLE_DNA_SYSTEM = "STYLE_DNA_SYSTEM"


class Engine(StrEnum):
    ACE_STEP = "ACE_STEP"
    YUE = "YUE"
    STABLE_AUDIO_OPEN = "STABLE_AUDIO_OPEN"
    MOCK = "MOCK"


class JobStatus(StrEnum):
    DRAFT = "DRAFT"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RENDERING_STEMS = "RENDERING_STEMS"
    ANALYZING_SAFETY = "ANALYZING_SAFETY"
    EXPORT_READY = "EXPORT_READY"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobEventType(StrEnum):
    JOB_CREATED = "job.created"
    PROMPT_COMPILED = "prompt.compiled"
    JOB_QUEUED = "job.queued"
    PREFLIGHT_PASSED = "preflight.passed"
    PREFLIGHT_BLOCKED = "preflight.blocked"
    WORKER_ASSIGNED = "worker.assigned"
    ENGINE_LOADED = "engine.loaded"
    GENERATION_STARTED = "generation.started"
    GENERATION_PROGRESS = "generation.progress"
    STEMS_STARTED = "stems.started"
    SAFETY_STARTED = "safety.started"
    ARTIFACT_READY = "artifact.ready"
    DROPBOX_EXPORTED = "dropbox.exported"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"


class Energy(StrEnum):
    HYPNOTIC = "hypnotic"
    DESTRUCTIVE = "destructive"
    EUPHORIC = "euphoric"
    WAREHOUSE = "warehouse"
    DEMONIC = "demonic"


class BassPressure(StrEnum):
    WARM = "warm"
    DEEP = "deep"
    CRUSHING = "crushing"
    EARTHQUAKE = "earthquake"
    MAXIMUM = "maximum"


class Vocals(StrEnum):
    SMOKY = "smoky"
    HAUNTING = "haunting"
    WHISPER = "whisper"
    RITUAL = "ritual"
    MELODIC = "melodic"


class Atmosphere(StrEnum):
    NEON_GREEN = "neon_green"
    DUB_SMOKE = "dub_smoke"
    BLACK_CONCRETE = "black_concrete"
    UNDERGROUND = "underground"
    POST_HUMAN = "post_human"


class Structure(StrEnum):
    NO_INTRO = "no_intro"
    INSTANT_DROP = "instant_drop"
    MANTRA_HOOK = "mantra_hook"
    LONG_BREAKDOWN = "long_breakdown"
    STEM_HEAVY = "stem_heavy"


class StemLaneType(StrEnum):
    KICK = "kick"
    DRUMS = "drums"
    PERCUSSION = "percussion"
    BASS = "bass"
    MUSIC = "music"
    LEAD = "lead"
    VOCALS_MAIN = "vocals_main"
    VOCALS_ADLIBS = "vocals_adlibs"
    FX = "fx"
    ATMOSPHERE = "atmosphere"
    RETURN_DELAY = "return_delay"
    RETURN_REVERB = "return_reverb"


class StemSourceType(StrEnum):
    GENERATED_DIRECT = "generated_direct"
    SOURCE_SEPARATED = "source_separated"
    REPAINTED = "repainted"
    IMPORTED = "imported"
    MANUAL_EDIT = "manual_edit"


class EffectDeviceType(StrEnum):
    EQ = "eq"
    COMPRESSOR = "compressor"
    LIMITER = "limiter"
    GATE = "gate"
    TRANSIENT_SHAPER = "transient_shaper"
    SATURATION = "saturation"
    DISTORTION = "distortion"
    FILTER = "filter"
    CHORUS = "chorus"
    PHASER = "phaser"
    FLANGER = "flanger"
    DUB_DELAY = "dub_delay"
    SPRING_REVERB = "spring_reverb"
    PLATE_REVERB = "plate_reverb"
    SIDECHAIN = "sidechain"
    STUTTER = "stutter"
    REVERSE = "reverse"
    RESAMPLER = "resampler"
    TAPE_STOP = "tape_stop"


class TempoFeel(StrEnum):
    STRAIGHT = "straight"
    SWUNG = "swung"
    HALF_TIME = "half_time"
    HALF_TIME_PRESSURE = "half_time_pressure"
    DOUBLE_TIME = "double_time"
    DOUBLE_TIME_HATS = "double_time_hats"
    BROKEN = "broken"
    STEPPING = "stepping"


class DruckPreset(StrEnum):
    OPEN = "open"
    GLUED = "glued"
    CLUB = "club"
    SOUNDSYSTEM = "soundsystem"
    CRUSHED = "crushed"
    REDLINE = "redline"


class MasteringMode(StrEnum):
    CLUB_PRESSURE = "club_pressure"
    DUB_WARMTH = "dub_warmth"
    BASS_HEAVY = "bass_heavy"
    VOCAL_FORWARD = "vocal_forward"
    DARK_WAREHOUSE = "dark_warehouse"
    REFERENCE_MATCH = "reference_match"


class ExportProfile(StrEnum):
    STREAMING_READY_WAV_24_441 = "streaming_ready_wav_24_441"
    CLUB_MASTER_WAV_24_48 = "club_master_wav_24_48"
    HD_MASTER_WAV_24_96 = "hd_master_wav_24_96"
    PREMASTER_WAV_32_FLOAT = "premaster_wav_32_float"
    STEM_PACK_WAV_24_48 = "stem_pack_wav_24_48"


class MasterJobStatus(StrEnum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    REFERENCE_BLOCKED = "REFERENCE_BLOCKED"
    EXPORT_READY = "EXPORT_READY"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PromptModules(BaseModel):
    energy: Energy
    bass_pressure: BassPressure
    vocals: Vocals
    atmosphere: Atmosphere
    structure: Structure


class TechnicalControls(BaseModel):
    bpm: int | None = Field(default=None, ge=30, le=300)
    key: str | None = Field(default=None, max_length=40)
    duration_seconds: int = Field(default=180, ge=10, le=600)
    seed: int | None = Field(default=None, ge=0)
    stems_required: bool = True

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class TempoControls(BaseModel):
    bpm: int = Field(default=140, ge=30, le=300)
    time_signature: str = Field(default="4/4", max_length=8)
    feel: TempoFeel = TempoFeel.STRAIGHT
    swing: float = Field(default=0.0, ge=0.0, le=0.3)
    locked_grid: bool = False


class DruckControls(BaseModel):
    preset: DruckPreset = DruckPreset.GLUED
    sub_pressure: int = Field(default=3, ge=0, le=5)
    bass_body: int = Field(default=3, ge=0, le=5)
    transient_pressure: int = Field(default=3, ge=0, le=5)
    density: int = Field(default=3, ge=0, le=5)
    compression: int = Field(default=2, ge=0, le=5)
    distortion_pressure: int = Field(default=1, ge=0, le=5)
    air_control: int = Field(default=2, ge=0, le=5)
    headroom: int = Field(default=3, ge=0, le=5)


class EffectDevice(BaseModel):
    device: EffectDeviceType
    notes: str | None = Field(default=None, max_length=200)


class EffectRack(BaseModel):
    lane: StemLaneType
    devices: list[EffectDevice] = Field(default_factory=list)


class StemLanePlan(BaseModel):
    lane: StemLaneType
    source: StemSourceType = StemSourceType.GENERATED_DIRECT
    editable: bool = True
    locked: bool = False
    notes: str | None = Field(default=None, max_length=400)


class StemPlan(BaseModel):
    lanes: list[StemLanePlan]
    locked_lanes: list[StemLaneType] = Field(default_factory=list)
    target_lane: StemLaneType | None = None


class SafetyOptions(BaseModel):
    allow_reference_audio: bool = False
    allow_voice_likeness: bool = False
    release_candidate: bool = False


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=3, max_length=120)
    intent: Intent
    engine: Engine = Engine.MOCK
    prompt_modules: PromptModules
    character_code: str = Field(default="SHIBARI_KAWAII", min_length=2, max_length=80)
    lyrics: str | None = Field(default=None, max_length=12000)
    technical: TechnicalControls = Field(default_factory=TechnicalControls)
    safety: SafetyOptions = Field(default_factory=SafetyOptions)
    tempo: TempoControls | None = None
    druck: DruckControls | None = None
    requested_effects: list[EffectDeviceType] = Field(default_factory=list)
    target_lane: StemLaneType | None = None
    locked_lanes: list[StemLaneType] = Field(default_factory=list)


class CompiledPromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    prompt_modules: PromptModules
    character_code: str = Field(default="SHIBARI_KAWAII", min_length=2, max_length=80)
    lyrics: str | None = Field(default=None, max_length=12000)
    technical: TechnicalControls = Field(default_factory=TechnicalControls)
    tempo: TempoControls | None = None
    druck: DruckControls | None = None
    requested_effects: list[EffectDeviceType] = Field(default_factory=list)
    target_lane: StemLaneType | None = None
    locked_lanes: list[StemLaneType] = Field(default_factory=list)


class CompiledPrompt(BaseModel):
    prompt_text: str
    negative_prompt: str
    safety_notes: list[str]
    engine_hints: dict[str, str | int | bool | None]
    stem_plan: StemPlan
    tempo: TempoControls
    druck: DruckControls
    effect_racks: list[EffectRack]
    requested_effects: list[EffectDeviceType] = Field(default_factory=list)


class StemArtifact(BaseModel):
    lane: StemLaneType
    path: str
    source: StemSourceType = StemSourceType.GENERATED_DIRECT
    sample_rate: int = 48000
    bit_depth: int = 24


class SoundGraphManifest(BaseModel):
    soundgraph_id: UUID
    bpm: int
    key: str | None = None
    sample_rate: int = 48000
    lanes: list[StemArtifact]
    tempo: TempoControls
    druck: DruckControls


class ArtifactManifest(BaseModel):
    full_mix_wav: str | None = None
    stems: list[str] = Field(default_factory=list)
    stem_lanes: list[StemArtifact] = Field(default_factory=list)
    soundgraph_manifest_json: str | None = None
    lyrics: str | None = None
    prompt_json: str | None = None
    metadata_json: str | None = None
    cover_image: str | None = None
    safety_report_json: str | None = None
    generation_history_json: str | None = None


class JobEvent(BaseModel):
    event_type: JobEventType
    detail: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerationJob(BaseModel):
    id: UUID
    project_id: str
    intent: Intent
    engine: Engine
    status: JobStatus
    progress: float = Field(default=0, ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    compiled_prompt: CompiledPrompt
    artifacts: ArtifactManifest = Field(default_factory=ArtifactManifest)
    events: list[JobEvent] = Field(default_factory=list)
    error: str | None = None


class MasterArtifact(BaseModel):
    profile: ExportProfile
    path: str
    sample_rate: int
    bit_depth: int
    is_float: bool = False


class MasterBusManifest(BaseModel):
    generation_id: UUID
    mode: MasteringMode
    masters: list[MasterArtifact]
    manifest_json: str
    pressure_report_json: str


class MasterBusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generation_id: UUID
    mode: MasteringMode = MasteringMode.CLUB_PRESSURE
    profiles: list[ExportProfile] = Field(
        default_factory=lambda: [
            ExportProfile.STREAMING_READY_WAV_24_441,
            ExportProfile.CLUB_MASTER_WAV_24_48,
        ]
    )
    reference_track_uri: str | None = Field(default=None, max_length=400)


class MasterBusJob(BaseModel):
    id: UUID
    generation_id: UUID
    mode: MasteringMode
    profiles: list[ExportProfile]
    status: MasterJobStatus
    progress: float = Field(default=0, ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    manifest: MasterBusManifest | None = None
    error: str | None = None


class ProviderCapability(BaseModel):
    name: str
    engine: Engine
    available: bool
    fallback: bool


class LyricsSectionType(StrEnum):
    INSTRUMENTAL_OPENING = "instrumental_opening"
    VERSE = "verse"
    PRE_CHORUS = "pre_chorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    DUB_BREAKDOWN = "dub_breakdown"
    OUTRO = "outro"


class LyricsSource(StrEnum):
    USER = "user"
    GPT_5_5 = "gpt_5_5"
    MOCK = "mock"


class VocalPerformanceNote(BaseModel):
    section_index: int = Field(ge=0)
    note: str = Field(max_length=300)


class LyricsLine(BaseModel):
    index: int = Field(ge=0)
    text: str = Field(max_length=400)
    syllables: int | None = Field(default=None, ge=0, le=200)
    rhyme_group: str | None = Field(default=None, max_length=8)
    vocal_note: str | None = Field(default=None, max_length=200)


class LyricsSection(BaseModel):
    index: int = Field(ge=0)
    section_type: LyricsSectionType
    label: str = Field(max_length=80)
    lines: list[LyricsLine] = Field(default_factory=list)
    locked: bool = False
    manually_edited: bool = False
    source: LyricsSource = LyricsSource.MOCK
    notes: str | None = Field(default=None, max_length=400)


class LyricsStructure(BaseModel):
    sections: list[LyricsSection]
    avoid_intro_singing: bool = False
    target_language: str = Field(default="en", max_length=8)


class LyricsVersion(BaseModel):
    id: UUID
    project_id: UUID
    version: int = Field(ge=1)
    structure: LyricsStructure
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parent_version_id: UUID | None = None
    edit_summary: str | None = Field(default=None, max_length=400)


class LyricsProject(BaseModel):
    id: UUID
    project_key: str = Field(min_length=3, max_length=120)
    title: str | None = Field(default=None, max_length=200)
    character_code: str = Field(default="SHIBARI_KAWAII", min_length=2, max_length=80)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LyricsGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_key: str = Field(min_length=3, max_length=120)
    prompt: str = Field(min_length=4, max_length=4000)
    character_code: str = Field(default="SHIBARI_KAWAII", min_length=2, max_length=80)
    structure: list[LyricsSectionType] | None = None
    target_language: str = Field(default="en", max_length=8)
    avoid_intro_singing: bool = False
    preserve_rhyme: bool = True
    preserve_syllable_length: bool = False
    title: str | None = Field(default=None, max_length=200)


class LyricsEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    edit_prompt: str = Field(min_length=2, max_length=4000)
    target_section: LyricsSectionType | None = None
    target_section_index: int | None = Field(default=None, ge=0)
    preserve_rhyme: bool = True
    preserve_syllable_length: bool = False


class LyricsRewriteSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    section_index: int = Field(ge=0)
    line_start_index: int = Field(ge=0)
    line_end_index: int = Field(ge=0)
    rewrite_prompt: str = Field(min_length=2, max_length=2000)
    variant_count: int = Field(default=3, ge=1, le=5)


class LyricsManualUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    section_index: int = Field(ge=0)
    lines: list[str] = Field(min_length=1, max_length=64)
    lock: bool = False
    notes: str | None = Field(default=None, max_length=400)


class LyricsLockToggleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locked: bool


class LyricsApplySelectionRewriteRequest(BaseModel):
    """Operator-confirmed rewrite application.

    Distinct from LyricsManualUpdateRequest because the provenance differs:
    manual updates set source=USER and manually_edited=True; an applied
    rewrite represents a provider-generated variant the operator accepted,
    so source stays MOCK (or the eventual real provider) and
    manually_edited stays False.
    """

    model_config = ConfigDict(extra="forbid")

    section_index: int = Field(ge=0)
    lines: list[str] = Field(min_length=1, max_length=64)
    lock: bool = False
    summary: str | None = Field(default=None, max_length=200)


class LyricsRewriteVariant(BaseModel):
    index: int = Field(ge=0)
    lines: list[LyricsLine]
    summary: str | None = Field(default=None, max_length=200)


class LyricsRewriteResponse(BaseModel):
    section_index: int
    line_start_index: int
    line_end_index: int
    variants: list[LyricsRewriteVariant]


class CompiledLyricsPrompt(BaseModel):
    instruction: str
    negative_prompt: str
    safety_notes: list[str]
    suno_compat_notes: list[str]
    soundgraph_compat_notes: list[str]
    structure: list[LyricsSectionType]
    risky_filler_patterns: list[str] = Field(default_factory=list)


class LyricsExportManifest(BaseModel):
    version_id: UUID
    project_id: UUID
    lyrics_txt_path: str
    lyrics_json_path: str
    vocal_notes: list[VocalPerformanceNote] = Field(default_factory=list)
    section_index_map: dict[str, int] = Field(default_factory=dict)
    safety_report_json_path: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str


class CapabilitiesResponse(BaseModel):
    service: Literal["snuffraga-soundsystem-inference"]
    engines: list[Engine]
    intents: list[Intent]
    prompt_modules: dict[str, list[str]]
    providers: list[ProviderCapability]
    stem_lanes: list[StemLaneType]
    effect_devices: list[EffectDeviceType]
    mastering_modes: list[MasteringMode]
    export_profiles: list[ExportProfile]
    lyrics_section_types: list[LyricsSectionType]
    lyrics_sources: list[LyricsSource]
    lyrics_repository_mode: LyricsRepositoryMode
    compliance_repository_mode: Literal["in_memory", "postgres"]
    compliance_registry_available: bool
    compliance_preflight_available: bool
    voice_lab_available: bool = False
    music_router_available: bool = False
    music_router_mode: Literal["mock"] = "mock"
    available_music_intents: list[str] = Field(default_factory=list)
    soundgraph_writer_available: bool = False
    export_pack_available: bool = False
    library_repository_mode: Literal["in_memory", "postgres"] = "in_memory"
    dropbox_sync_available: bool = False
    dropbox_sync_provider_mode: Literal["mock", "dropbox"] = "mock"
    release_pack_available: bool = False
    release_repository_mode: Literal["in_memory", "postgres"] = "in_memory"
    auth_enabled: bool = False
    auth_mode: Literal["open", "api_key"] = "open"
    job_queue_available: bool = False
    job_queue_mode: Literal["in_memory", "redis"] = "in_memory"
    async_jobs_available: bool = False
    artifact_storage_available: bool = False
    artifact_storage_mode: Literal["local", "s3"] = "local"
    artifact_registry_mode: Literal["in_memory", "postgres"] = "in_memory"
    artifact_access_mode: Literal["direct", "signed"] = "direct"
    soundcloud_publish_available: bool = False
    soundcloud_provider_mode: Literal["mock", "soundcloud"] = "mock"
    merch_capsules_available: bool = False
    merch_provider_mode: Literal["mock"] = "mock"
    merch_repository_mode: Literal["in_memory", "postgres"] = "in_memory"
    ditto_distribution_available: bool = False
    distribution_provider_mode: Literal["mock"] = "mock"
    distribution_repository_mode: Literal["in_memory", "postgres"] = "in_memory"
    shopify_drafts_available: bool = False
    shopify_provider_mode: Literal["mock", "shopify"] = "mock"
    shopify_live_draft_sync_available: bool = False
    printful_sync_available: bool = False
    printful_provider_mode: Literal["mock", "printful"] = "mock"
    printful_live_product_sync_available: bool = False
    commerce_sync_dashboard_available: bool = False
    commerce_sync_audit_available: bool = False
    commerce_sync_audit_mode: Literal["in_memory", "postgres"] = "in_memory"
    newsletter_subscribe_available: bool = False
    newsletter_listmonk_configured: bool = False
    tiktok_shop_available: bool = False
    tiktok_shop_provider_mode: Literal["mock", "tiktok_shop"] = "mock"
    campaign_os_available: bool = False
    campaign_repository_mode: str = "in_memory"
    campaign_automation_rules_available: bool = False
    campaign_automation_templates_available: bool = False
    release_command_center_available: bool = False
    automation_execution_boundary_available: bool = False
    automation_execution_mode: Literal["disabled", "mock"] = "disabled"
    automation_execution_repository_mode: Literal["in_memory", "postgres"] = "in_memory"
    automation_execution_audit_available: bool = False
    automation_execution_audit_mode: Literal["in_memory", "postgres"] = "in_memory"
    vinyl_releases_available: bool = False
    vinyl_provider_mode: Literal["manual_handoff", "elastic_stage", "disc_archive"] = (
        "manual_handoff"
    )
    vinyl_repository_mode: str = "in_memory"
    analytics_graph_available: bool = False
    analytics_repository_mode: str = "in_memory"
    intelligence_engine_available: bool = False
    provider_connector_framework_available: bool = False
    mock_platform_connectors_available: bool = False
    connector_import_audit_available: bool = False
    intelligence_snapshots_available: bool = False
    intelligence_snapshot_repository_mode: str = "in_memory"


# ---------- Compliance Foundation (S10) ----------


class CommercialStatus(StrEnum):
    RESEARCH_ONLY = "research_only"
    REVIEW_NEEDED = "review_needed"
    CONDITIONAL = "conditional"
    APPROVED_INTERNAL = "approved_internal"
    APPROVED_RELEASE = "approved_release"
    BLOCKED = "blocked"


class SafetyReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class ActivationStatus(StrEnum):
    NOT_WIRED = "not_wired"
    MOCK = "mock"
    CONDITIONAL_LIVE = "conditional_live"
    LIVE = "live"


class RiskTier(StrEnum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class ProviderGroup(StrEnum):
    MUSIC_LOOP_PROVIDER = "music_loop_provider"
    HIGH_FIDELITY_CLIP_PROVIDER = "high_fidelity_clip_provider"
    FULL_SONG_EXPERIMENTAL_PROVIDER = "full_song_experimental_provider"
    VOICE_TTS_PROVIDER = "voice_tts_provider"
    VOICE_CLONE_PROVIDER = "voice_clone_provider"
    SINGING_VOICE_PROVIDER = "singing_voice_provider"
    OFFLINE_FALLBACK_PROVIDER = "offline_fallback_provider"
    MASTERING_PROVIDER = "mastering_provider"
    STEM_SEPARATION_PROVIDER = "stem_separation_provider"


class LicenseStatus(StrEnum):
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ConsentSourceType(StrEnum):
    USER_OWNED = "user_owned"
    LICENSED = "licensed"
    TEST_VOICE = "test_voice"
    CHARACTER_PERSONA = "character_persona"


class RewriteStrategy(StrEnum):
    INITIAL_GENERATION = "initial_generation"
    MANUAL = "manual"
    PROMPT_EDIT = "prompt_edit"
    SELECTION_REWRITE = "selection_rewrite"
    PROVIDER_REGEN = "provider_regen"


class BlockedPromptCategory(StrEnum):
    NAMED_ARTIST_IMITATION = "named_artist_imitation"
    NAMED_TRACK_CLONING = "named_track_cloning"
    VOICE_LIKENESS_WITHOUT_CONSENT = "voice_likeness_without_consent"
    PUBLIC_FIGURE_VOICE = "public_figure_voice"


class LicenseRegistryEntry(BaseModel):
    license_id: UUID
    model_or_dataset_id: str = Field(max_length=200)
    license_name: str = Field(max_length=200)
    license_url: str | None = Field(default=None, max_length=400)
    permits_commercial: bool
    restrictions: list[str] = Field(default_factory=list)
    reviewed_by: str | None = Field(default=None, max_length=200)
    reviewed_at: datetime | None = None
    status: LicenseStatus = LicenseStatus.NEEDS_REVIEW
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LicenseRegistryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_or_dataset_id: str = Field(max_length=200)
    license_name: str = Field(max_length=200)
    license_url: str | None = Field(default=None, max_length=400)
    permits_commercial: bool
    restrictions: list[str] = Field(default_factory=list)
    reviewed_by: str | None = Field(default=None, max_length=200)
    status: LicenseStatus = LicenseStatus.NEEDS_REVIEW
    notes: str | None = Field(default=None, max_length=2000)


class ModelRegistryEntry(BaseModel):
    model_id: UUID
    provider_group: ProviderGroup
    adapter_key: str = Field(max_length=120)
    display_name_internal: str = Field(max_length=200)
    commercial_status: CommercialStatus
    activation_status: ActivationStatus
    risk_tier: RiskTier
    license_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConsentRecord(BaseModel):
    consent_id: UUID
    speaker_label: str = Field(max_length=200)
    source_type: ConsentSourceType
    permitted_uses: list[str] = Field(default_factory=list)
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConsentRecordCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker_label: str = Field(min_length=2, max_length=200)
    source_type: ConsentSourceType
    permitted_uses: list[str] = Field(default_factory=list, max_length=32)
    expires_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class OutputProvenance(BaseModel):
    provenance_id: UUID
    artifact_id: UUID
    artifact_kind: str = Field(max_length=120)
    parent_provenance_id: UUID | None = None
    provider: UUID | None = None
    model: str | None = Field(default=None, max_length=200)
    model_version: str | None = Field(default=None, max_length=200)
    prompt: str | None = Field(default=None, max_length=8000)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    safety_notes: list[str] = Field(default_factory=list)
    rewrite_strategy: RewriteStrategy
    locked_sections_respected: bool = True
    raw_provider_trace_id: str | None = Field(default=None, max_length=200)
    raw_operator_prompt: str | None = Field(default=None, max_length=8000)
    system_prompt_version: str | None = Field(default=None, max_length=80)
    safety_transformations: list[str] = Field(default_factory=list)
    license_bundle: list[UUID] = Field(default_factory=list)
    consent_records: list[UUID] = Field(default_factory=list)
    consent_required: bool = False
    commercial_status: CommercialStatus
    safety_review_status: SafetyReviewStatus = SafetyReviewStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutputProvenanceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: UUID
    artifact_kind: str = Field(min_length=2, max_length=120)
    parent_provenance_id: UUID | None = None
    provider: UUID | None = None
    model: str | None = Field(default=None, max_length=200)
    model_version: str | None = Field(default=None, max_length=200)
    prompt: str | None = Field(default=None, max_length=8000)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    safety_notes: list[str] = Field(default_factory=list)
    rewrite_strategy: RewriteStrategy
    locked_sections_respected: bool = True
    raw_provider_trace_id: str | None = Field(default=None, max_length=200)
    raw_operator_prompt: str | None = Field(default=None, max_length=8000)
    system_prompt_version: str | None = Field(default=None, max_length=80)
    safety_transformations: list[str] = Field(default_factory=list)
    license_bundle: list[UUID] = Field(default_factory=list)
    consent_records: list[UUID] = Field(default_factory=list)
    consent_required: bool = False
    commercial_status: CommercialStatus = CommercialStatus.RESEARCH_ONLY
    safety_review_status: SafetyReviewStatus = SafetyReviewStatus.PENDING


class AuditEvent(BaseModel):
    event_id: UUID
    operator_id: str | None = Field(default=None, max_length=200)
    action: str = Field(max_length=200)
    entity_type: str = Field(max_length=120)
    entity_id: UUID | None = None
    payload_summary: dict[str, str | int | bool | None] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditEventCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator_id: str | None = Field(default=None, max_length=200)
    action: str = Field(min_length=2, max_length=200)
    entity_type: str = Field(min_length=2, max_length=120)
    entity_id: UUID | None = None
    payload_summary: dict[str, str | int | bool | None] = Field(default_factory=dict)


class CompliancePreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_code: str = Field(min_length=2, max_length=120)
    provider_group: ProviderGroup | None = None
    prompt: str | None = Field(default=None, max_length=8000)
    consent_required: bool = False
    consent_record_ids: list[UUID] = Field(default_factory=list)
    requires_commercial: bool = False


class CompliancePreflightResult(BaseModel):
    ok: bool
    blocking_reasons: list[str]
    warning_reasons: list[str]
    preflight_codes: list[str]


class ReleaseEligibilityResult(BaseModel):
    artifact_id: UUID
    provenance_id: UUID | None
    eligible: bool
    blocking_reasons: list[str]
    warning_reasons: list[str]
    required_actions: list[str]


class ComplianceRegistrySummary(BaseModel):
    model_registry_count: int
    license_registry_count: int
    consent_records_count: int
    output_provenance_count: int
    audit_events_count: int
    repository_mode: Literal["in_memory", "postgres"]


# ---------- Voice Lab (S11) ----------


class VoiceJobStatus(StrEnum):
    DRAFT = "draft"
    PREFLIGHT_BLOCKED = "preflight_blocked"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class VoiceJobKind(StrEnum):
    CREATE_VOICE_TAG = "create_voice_tag"
    CREATE_SPOKEN_VOCAL = "create_spoken_vocal"
    CONVERT_APPROVED_VOICE = "convert_approved_voice"


class VoiceTag(BaseModel):
    """A reusable voice identity profile attached to a consent record."""

    tag_id: UUID
    label: str = Field(min_length=2, max_length=120)
    consent_id: UUID
    provider_group: ProviderGroup = ProviderGroup.VOICE_TTS_PROVIDER
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceTagCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=2, max_length=120)
    consent_id: UUID
    provider_group: ProviderGroup = ProviderGroup.VOICE_TTS_PROVIDER
    notes: str | None = Field(default=None, max_length=2000)


class VoiceJob(BaseModel):
    """A voice lab job — tag creation, spoken vocal, or voice convert."""

    job_id: UUID
    kind: VoiceJobKind
    status: VoiceJobStatus = VoiceJobStatus.DRAFT
    voice_tag_id: UUID | None = None
    consent_id: UUID | None = None
    prompt: str | None = Field(default=None, max_length=4000)
    output_artifact_path: str | None = Field(default=None, max_length=400)
    provenance_id: UUID | None = None
    error: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: VoiceJobKind
    voice_tag_id: UUID | None = None
    consent_id: UUID | None = None
    prompt: str | None = Field(default=None, max_length=4000)


class VoiceLabSummary(BaseModel):
    voice_tag_count: int
    voice_job_count: int
    jobs_complete: int
    jobs_blocked: int


# ---------- Music Provider Router (S12) ----------


class MusicIntentKind(StrEnum):
    CREATE_LOOP = "create_loop"
    CREATE_SONG_SKETCH = "create_song_sketch"
    CREATE_STEM_TRACK = "create_stem_track"
    BUILD_RIDDIM = "build_riddim"
    DUB_FX_LAB = "dub_fx_lab"
    MASTER_TRACK = "master_track"


class MusicJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PREFLIGHT_BLOCKED = "preflight_blocked"


class MusicProviderGroup(StrEnum):
    MUSIC_LOOP_PROVIDER = "music_loop_provider"
    HIGH_FIDELITY_CLIP_PROVIDER = "high_fidelity_clip_provider"
    FULL_SONG_EXPERIMENTAL_PROVIDER = "full_song_experimental_provider"
    STEM_GENERATION_PROVIDER = "stem_generation_provider"
    DUB_FX_PROVIDER = "dub_fx_provider"
    MASTERING_PROVIDER = "mastering_provider"


class MusicArtifactType(StrEnum):
    FULL_MIX = "full_mix"
    LOOP = "loop"
    STEM_PACK = "stem_pack"
    SOUNDGRAPH_MANIFEST = "soundgraph_manifest"
    DUB_FX = "dub_fx"
    MASTER = "master"
    PROMPT_MANIFEST = "prompt_manifest"


class MusicRouterReadiness(StrEnum):
    MOCK_ONLY = "mock_only"
    NOT_WIRED = "not_wired"
    BLOCKED = "blocked"


class MusicGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: MusicIntentKind
    title: str = Field(min_length=2, max_length=200)
    prompt: str = Field(min_length=2, max_length=8000)
    duration_seconds: float | None = Field(default=None, ge=1, le=600)
    bpm: int | None = Field(default=None, ge=30, le=300)
    key: str | None = Field(default=None, max_length=12)
    language: str | None = Field(default=None, max_length=20)
    lyrics_project_key: str | None = Field(default=None, max_length=120)
    lyrics_version_number: int | None = Field(default=None, ge=1)
    requested_lanes: list[StemLaneType] = Field(default_factory=list)
    locked_lanes: list[StemLaneType] = Field(default_factory=list)
    commercial_target: CommercialStatus = CommercialStatus.REVIEW_NEEDED
    operator_id: str | None = Field(default=None, max_length=200)


class MusicArtifactManifest(BaseModel):
    artifact_type: MusicArtifactType
    path: str = Field(max_length=400)
    duration_seconds: float | None = None
    format: str = Field(default="wav", max_length=20)


class MusicRouterDecision(BaseModel):
    intent: MusicIntentKind
    provider_group: MusicProviderGroup
    selected_adapter_key: str = Field(max_length=120)
    readiness_state: MusicRouterReadiness
    reason: str = Field(max_length=400)
    compliance_preflight_ok: bool = True
    compliance_preflight_codes: list[str] = Field(default_factory=list)
    provenance_id: UUID | None = None


class MusicJob(BaseModel):
    job_id: UUID
    intent: MusicIntentKind
    title: str
    prompt: str
    status: MusicJobStatus = MusicJobStatus.QUEUED
    router_decision: MusicRouterDecision | None = None
    artifacts: list[MusicArtifactManifest] = Field(default_factory=list)
    provenance_id: UUID | None = None
    error: str | None = Field(default=None, max_length=2000)
    commercial_target: CommercialStatus = CommercialStatus.REVIEW_NEEDED
    operator_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MusicRouterSummary(BaseModel):
    total_jobs: int
    jobs_completed: int
    jobs_blocked: int
    jobs_failed: int
    router_mode: Literal["mock"] = "mock"
    available_intents: list[MusicIntentKind]


# ---------- SoundGraph Manifest Writer (S14) ----------


class RegionRole(StrEnum):
    """Role of a region within the arrangement."""

    INTRO = "intro"
    VERSE = "verse"
    PRE_CHORUS = "pre_chorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    BREAKDOWN = "breakdown"
    DROP = "drop"
    OUTRO = "outro"


class VocalEntry(StrEnum):
    """Whether a region carries vocals."""

    NONE = "none"
    MAIN = "main"
    ADLIBS = "adlibs"
    WHISPER = "whisper"
    SPOKEN = "spoken"


class EnergyLevel(StrEnum):
    """Energy level for a region in the energy map."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PEAK = "peak"
    DROP = "drop"


class ArrangementRegion(BaseModel):
    """One region in the arrangement timeline.

    Maps directly from a LyricsSection but enriched with production data.
    """

    region_index: int = Field(ge=0)
    section_index: int = Field(ge=0, description="Index into the source LyricsStructure")
    role: RegionRole
    label: str = Field(max_length=80)
    bar_start: int = Field(ge=0, description="Start bar (0-indexed)")
    bar_count: int = Field(ge=1, le=64, description="Duration in bars")
    vocal_entry: VocalEntry = VocalEntry.NONE
    energy: EnergyLevel = EnergyLevel.MEDIUM
    lanes_active: list[StemLaneType] = Field(default_factory=list)
    lanes_muted: list[StemLaneType] = Field(default_factory=list)
    locked: bool = False
    notes: str | None = Field(default=None, max_length=400)


class EnergyMapPoint(BaseModel):
    """One point in the energy curve across regions."""

    region_index: int = Field(ge=0)
    bar: int = Field(ge=0)
    energy: EnergyLevel


class LaneAssignment(BaseModel):
    """Which lanes play in which regions."""

    lane: StemLaneType
    active_regions: list[int] = Field(
        default_factory=list, description="Region indices where this lane plays"
    )
    source: StemSourceType = StemSourceType.GENERATED_DIRECT
    notes: str | None = Field(default=None, max_length=200)


class SoundGraphArrangement(BaseModel):
    """The full arrangement derived from lyrics + production rules.

    This is the editable production structure — the bridge between lyrics
    text and audio generation.
    """

    arrangement_id: UUID
    lyrics_version_id: UUID
    project_key: str = Field(min_length=3, max_length=120)
    bpm: int = Field(ge=60, le=220)
    time_signature: str = Field(default="4/4", max_length=8)
    key_signature: str | None = Field(default=None, max_length=12)
    total_bars: int = Field(ge=1, le=512)
    regions: list[ArrangementRegion] = Field(default_factory=list)
    energy_map: list[EnergyMapPoint] = Field(default_factory=list)
    lane_assignments: list[LaneAssignment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SoundGraphWriteRequest(BaseModel):
    """Request to compile a LyricsVersion into a SoundGraphArrangement."""

    model_config = ConfigDict(extra="forbid")

    lyrics_version_id: UUID
    bpm: int = Field(default=140, ge=60, le=220)
    time_signature: str = Field(default="4/4", max_length=8)
    key_signature: str | None = Field(default=None, max_length=12)
    bars_per_section_override: dict[str, int] | None = Field(
        default=None,
        description="Optional override: section_type → bar_count",
    )
    energy_profile: str = Field(
        default="standard",
        max_length=40,
        description="Energy curve preset: standard, slow_build, peak_early, flat",
    )


class SoundGraphWriteResult(BaseModel):
    """Result of compiling lyrics into a SoundGraph arrangement."""

    arrangement: SoundGraphArrangement
    warnings: list[str] = Field(default_factory=list)
    section_count: int = Field(ge=0)
    total_bars: int = Field(ge=0)
    vocal_regions: int = Field(ge=0)
    instrumental_regions: int = Field(ge=0)


class SoundGraphHandoffRequest(BaseModel):
    """Request to hand off a SoundGraphArrangement to the Music Router."""

    model_config = ConfigDict(extra="forbid")

    arrangement_id: UUID
    title: str | None = Field(default=None, max_length=200)
    operator_id: str | None = Field(default=None, max_length=200)
    commercial_target: CommercialStatus = CommercialStatus.REVIEW_NEEDED
    intent_override: MusicIntentKind | None = None


class SoundGraphHandoffResult(BaseModel):
    """Result of the SoundGraph → Music Router handoff."""

    music_job: MusicJob
    resolved_intent: MusicIntentKind
    requested_lanes: list[StemLaneType]
    locked_lanes: list[StemLaneType]
    estimated_duration_seconds: float
    compiled_prompt: str


# ---------- Export Pack / Project Library (S17) ----------


class ExportPackStatus(StrEnum):
    """Status of an export pack."""

    DRAFT = "draft"
    COMPLETE = "complete"
    FAILED = "failed"


class ExportPackComponent(BaseModel):
    """One component bundled inside an export pack."""

    component_type: str = Field(max_length=60)
    component_id: UUID
    label: str = Field(max_length=200)
    path: str | None = Field(default=None, max_length=400)


class ExportPack(BaseModel):
    """A bundled project pack: MusicJob + Artifacts + Lyrics + SoundGraph + Provenance."""

    pack_id: UUID
    title: str = Field(min_length=2, max_length=200)
    status: ExportPackStatus = ExportPackStatus.DRAFT
    music_job_id: UUID
    lyrics_version_id: UUID | None = None
    arrangement_id: UUID | None = None
    provenance_id: UUID | None = None
    components: list[ExportPackComponent] = Field(default_factory=list)
    total_components: int = Field(default=0, ge=0)
    estimated_duration_seconds: float | None = None
    bpm: int | None = Field(default=None, ge=60, le=220)
    key_signature: str | None = Field(default=None, max_length=12)
    intent: MusicIntentKind | None = None
    operator_id: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportPackCreateRequest(BaseModel):
    """Request to create an export pack from a completed music job."""

    model_config = ConfigDict(extra="forbid")

    music_job_id: UUID
    title: str | None = Field(default=None, max_length=200)
    operator_id: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class ProjectLibraryEntry(BaseModel):
    """A library entry wrapping an export pack with catalogue metadata."""

    entry_id: UUID
    pack_id: UUID
    title: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=120)
    intent: MusicIntentKind | None = None
    status: ExportPackStatus = ExportPackStatus.COMPLETE
    bpm: int | None = Field(default=None, ge=60, le=220)
    key_signature: str | None = Field(default=None, max_length=12)
    estimated_duration_seconds: float | None = None
    component_count: int = Field(default=0, ge=0)
    artifact_count: int = Field(default=0, ge=0)
    has_lyrics: bool = False
    has_arrangement: bool = False
    has_provenance: bool = False
    operator_id: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectLibrarySummary(BaseModel):
    """Summary of the project library."""

    total_entries: int
    total_packs: int
    entries_with_lyrics: int
    entries_with_arrangements: int
    entries_with_provenance: int


# ---------- Dropbox Export Sync (S20) ----------


class DropboxSyncStatus(StrEnum):
    """Status of a Dropbox sync job."""

    PLANNED = "planned"
    READY_FOR_SYNC = "ready_for_sync"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


class DropboxFolderEntry(BaseModel):
    """One file/folder in the planned Dropbox export structure."""

    relative_path: str = Field(max_length=400)
    source_component_type: str = Field(max_length=60)
    source_label: str = Field(max_length=200)
    size_hint: str | None = Field(default=None, max_length=40)
    is_directory: bool = False


class DropboxExportPlan(BaseModel):
    """The planned Dropbox folder structure for an export pack."""

    plan_id: UUID
    pack_id: UUID
    pack_title: str = Field(min_length=2, max_length=200)
    target_root: str = Field(max_length=400)
    entries: list[DropboxFolderEntry] = Field(default_factory=list)
    total_files: int = Field(default=0, ge=0)
    total_directories: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DropboxSyncJob(BaseModel):
    """A Dropbox sync job — tracks the upload of an export pack."""

    sync_id: UUID
    pack_id: UUID
    plan_id: UUID
    status: DropboxSyncStatus = DropboxSyncStatus.PLANNED
    target_root: str = Field(max_length=400)
    files_planned: int = Field(default=0, ge=0)
    files_synced: int = Field(default=0, ge=0)
    error: str | None = Field(default=None, max_length=2000)
    operator_id: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DropboxExportPlanCreateRequest(BaseModel):
    """Request to create a Dropbox export plan from a pack."""

    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    target_root_override: str | None = Field(
        default=None,
        max_length=400,
        description="Override the default target folder path",
    )
    operator_id: str | None = Field(default=None, max_length=200)


class DropboxSyncSummary(BaseModel):
    """Summary of all Dropbox sync jobs."""

    total_plans: int
    total_sync_jobs: int
    jobs_planned: int
    jobs_ready: int
    jobs_synced: int
    jobs_failed: int


# ---------- Release Pack (S22) ----------


class ReleasePackStatus(StrEnum):
    """Lifecycle status of a release pack."""

    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"


class ComplianceChecklistItem(BaseModel):
    """Single item in the release compliance checklist."""

    code: str = Field(max_length=60)
    label: str = Field(max_length=200)
    passed: bool = False
    notes: str | None = Field(default=None, max_length=500)


class SocialCopy(BaseModel):
    """Platform-specific copy for distribution."""

    soundcloud_description: str = Field(default="", max_length=5000)
    tiktok_caption: str = Field(default="", max_length=300)
    instagram_caption: str = Field(default="", max_length=2200)
    hashtags: list[str] = Field(default_factory=list)


class ReleaseAssetPlaceholder(BaseModel):
    """Placeholder for a release asset (cover, audio, etc.)."""

    asset_type: str = Field(max_length=60)
    label: str = Field(max_length=200)
    expected_format: str = Field(max_length=20)
    ready: bool = False
    path: str | None = Field(default=None, max_length=400)
    artifact_id: UUID | None = None


class ReleasePack(BaseModel):
    """A release-ready package derived from an ExportPack."""

    release_id: UUID
    pack_id: UUID
    title: str = Field(min_length=2, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    status: ReleasePackStatus = ReleasePackStatus.DRAFT
    description: str = Field(default="", max_length=5000)
    social_copy: SocialCopy = Field(default_factory=SocialCopy)
    compliance_checklist: list[ComplianceChecklistItem] = Field(default_factory=list)
    compliance_passed: bool = False
    assets: list[ReleaseAssetPlaceholder] = Field(default_factory=list)
    dropbox_target: str | None = Field(default=None, max_length=500)
    genre: str | None = Field(default=None, max_length=60)
    bpm: int | None = Field(default=None, ge=60, le=220)
    key_signature: str | None = Field(default=None, max_length=12)
    duration_seconds: float | None = None
    operator_id: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReleasePackCreateRequest(BaseModel):
    """Request to create a release pack from a library pack."""

    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    title: str | None = Field(default=None, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    genre: str | None = Field(default=None, max_length=60)
    operator_id: str | None = Field(default=None, max_length=200)


class ReleasePackSummary(BaseModel):
    """Summary of all release packs."""

    total_releases: int
    drafts: int
    ready: int
    published: int
    compliance_passed: int


# ---------- Cover Asset Upload (S31) ----------


class CoverValidationWarning(BaseModel):
    """Non-fatal warning from cover validation (e.g. below recommended size)."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class CoverAssetUploadRequest(BaseModel):
    """Request to upload cover artwork for a release pack."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=200)
    content_type: str = Field(max_length=60)
    content_base64: str


class CoverAssetUploadResult(BaseModel):
    """Result of uploading cover artwork for a release pack."""

    release: ReleasePack
    artifact: ArtifactRecord
    warnings: list[CoverValidationWarning] = Field(default_factory=list)


# ---------- Audio Master Upload (S32) ----------


class AudioValidationWarning(BaseModel):
    """Non-fatal warning from audio master validation."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class AudioMasterUploadRequest(BaseModel):
    """Request to upload a WAV audio master for a release pack."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=200)
    content_type: str = Field(max_length=60)
    content_base64: str


class AudioMasterUploadResult(BaseModel):
    """Result of uploading an audio master for a release pack."""

    release: ReleasePack
    artifact: ArtifactRecord
    warnings: list[AudioValidationWarning] = Field(default_factory=list)
    channels: int | None = None
    sample_rate: int | None = None
    sample_width_bytes: int | None = None
    duration_seconds: float | None = None


# ---------- Stem Pack Upload (S33) ----------


class StemPackValidationWarning(BaseModel):
    """Non-fatal warning from stem pack validation."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class StemPackManifestEntry(BaseModel):
    """One file inside a stem pack ZIP."""

    filename: str = Field(max_length=400)
    size_bytes: int = Field(ge=0)
    extension: str = Field(max_length=20)
    is_audio: bool = False


class StemPackUploadRequest(BaseModel):
    """Request to upload a stem pack ZIP for a release pack."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=200)
    content_type: str = Field(max_length=60)
    content_base64: str


class StemPackUploadResult(BaseModel):
    """Result of uploading a stem pack ZIP for a release pack."""

    release: ReleasePack
    artifact: ArtifactRecord
    warnings: list[StemPackValidationWarning] = Field(default_factory=list)
    entries: list[StemPackManifestEntry] = Field(default_factory=list)
    total_files: int = 0
    total_uncompressed_bytes: int = 0


# ---------- Release Export ZIP Builder (S34) ----------


class ReleaseExportStatus(StrEnum):
    """Status of a release export build."""

    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"


class ReleaseExportEntry(BaseModel):
    """One file included in the release export ZIP."""

    path: str = Field(max_length=400)
    source_asset_type: str = Field(max_length=60)
    size_bytes: int = Field(ge=0)
    checksum_sha256: str = Field(max_length=64)
    content_type: str = Field(default="application/octet-stream", max_length=120)


class ReleaseExportWarning(BaseModel):
    """Non-fatal warning from release export build."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class ReleaseExportResult(BaseModel):
    """Result of building a release export ZIP."""

    export_id: UUID
    release_id: UUID
    artifact: ArtifactRecord
    status: ReleaseExportStatus = ReleaseExportStatus.COMPLETED
    entries: list[ReleaseExportEntry] = Field(default_factory=list)
    warnings: list[ReleaseExportWarning] = Field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Async Worker System (S26) ----------


class AsyncJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AsyncJobKind(StrEnum):
    MUSIC_ROUTER = "music_router"
    SOUNDGRAPH_HANDOFF = "soundgraph_handoff"
    DROPBOX_SYNC = "dropbox_sync"
    RELEASE_PACK = "release_pack"
    GENERIC = "generic"


class AsyncJobEvent(BaseModel):
    event_type: str = Field(max_length=80)
    detail: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AsyncJobProgress(BaseModel):
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str | None = Field(default=None, max_length=400)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AsyncJobResult(BaseModel):
    """Arbitrary JSON result payload for completed jobs."""

    data: dict | None = None
    error: str | None = Field(default=None, max_length=2000)


class AsyncJob(BaseModel):
    """A queued/running/completed async job."""

    job_id: UUID
    kind: AsyncJobKind
    status: AsyncJobStatus = AsyncJobStatus.QUEUED
    payload: dict = Field(default_factory=dict)
    result: AsyncJobResult | None = None
    progress: AsyncJobProgress = Field(default_factory=AsyncJobProgress)
    events: list[AsyncJobEvent] = Field(default_factory=list)
    retries: int = Field(default=0, ge=0)
    max_retries: int = Field(default=2, ge=0, le=10)
    operator_id: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AsyncJobCreateRequest(BaseModel):
    """Request to enqueue a new async job."""

    model_config = ConfigDict(extra="forbid")

    kind: AsyncJobKind
    payload: dict = Field(default_factory=dict)
    max_retries: int = Field(default=2, ge=0, le=10)


class AsyncJobSummary(BaseModel):
    """Summary of async jobs by status."""

    total: int
    queued: int
    running: int
    succeeded: int
    failed: int
    cancelled: int
    retrying: int


# ---------- Artifact Storage (S27) ----------


class ArtifactKind(StrEnum):
    LYRICS = "lyrics"
    SOUNDGRAPH = "soundgraph"
    MUSIC_JOB = "music_job"
    AUDIO_MIX = "audio_mix"
    AUDIO_MASTER = "audio_master"
    STEM_PACK = "stem_pack"
    COVER_ART = "cover_art"
    RELEASE_PACK = "release_pack"
    EXPORT_PACK = "export_pack"
    PROVENANCE = "provenance"
    MANIFEST = "manifest"
    OTHER = "other"


class ArtifactStatus(StrEnum):
    PLANNED = "planned"
    STORED = "stored"
    MISSING = "missing"
    DELETED = "deleted"
    FAILED = "failed"


class ArtifactRecord(BaseModel):
    """A registered artifact in the storage system."""

    artifact_id: UUID
    kind: ArtifactKind
    status: ArtifactStatus = ArtifactStatus.PLANNED
    storage_mode: Literal["local", "s3"] = "local"
    logical_path: str = Field(max_length=500)
    storage_key: str | None = Field(default=None, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    size_bytes: int | None = Field(default=None, ge=0)
    checksum_sha256: str | None = Field(default=None, max_length=64)
    operator_id: str | None = Field(default=None, max_length=200)
    source_entity_type: str | None = Field(default=None, max_length=80)
    source_entity_id: UUID | None = None
    provenance_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArtifactCreateRequest(BaseModel):
    """Request to register a new artifact (metadata only)."""

    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    logical_path: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    source_entity_type: str | None = Field(default=None, max_length=80)
    source_entity_id: UUID | None = None
    provenance_id: UUID | None = None


class ArtifactUploadRequest(BaseModel):
    """Request to upload bytes for a registered artifact.

    Accepts base64-encoded content for test simplicity.
    """

    model_config = ConfigDict(extra="forbid")

    content_base64: str = Field(min_length=1)
    content_type: str | None = Field(default=None, max_length=120)


class ArtifactDownloadLink(BaseModel):
    """A download link for an artifact."""

    artifact_id: UUID
    url: str
    expires_at: datetime | None = None


class ArtifactStorageSummary(BaseModel):
    """Summary of artifact storage state."""

    total: int
    planned: int
    stored: int
    missing: int
    deleted: int
    failed: int
    total_size_bytes: int
    storage_mode: str


# ---------- Artifact Signed URL / Access Policy (S29) ----------


class ArtifactSignedUrl(BaseModel):
    """A download URL for an artifact with access mode metadata."""

    artifact_id: UUID
    url: str
    expires_at: datetime | None = None
    access_mode: Literal["direct", "signed"] = "direct"
    method: Literal["GET"] = "GET"


# ---------- SoundCloud Publishing (S36) ----------


class SoundCloudPublishStatus(StrEnum):
    """Lifecycle status of a SoundCloud publish job."""

    DRAFT = "draft"
    READY = "ready"
    PUBLISHED_MOCK = "published_mock"
    FAILED = "failed"
    BLOCKED = "blocked"


class SoundCloudMetadata(BaseModel):
    """Metadata payload for SoundCloud track upload."""

    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list)
    genre: str | None = Field(default=None, max_length=60)
    release_date: str | None = Field(default=None, max_length=20)
    is_private: bool = True
    downloadable: bool = False
    cover_artifact_id: UUID | None = None
    audio_artifact_id: UUID | None = None
    release_pack_id: UUID
    export_artifact_id: UUID | None = None


class SoundCloudPublishWarning(BaseModel):
    """Warning generated during publish preview."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class SoundCloudPublishPreview(BaseModel):
    """Preview of what would be published to SoundCloud."""

    release_id: UUID
    metadata: SoundCloudMetadata
    warnings: list[SoundCloudPublishWarning] = Field(default_factory=list)
    can_publish: bool = False
    blocked_reason: str | None = Field(default=None, max_length=500)


class SoundCloudPublishRequest(BaseModel):
    """Request to create a SoundCloud publish job."""

    model_config = ConfigDict(extra="forbid")

    release_id: UUID


class SoundCloudPublishJob(BaseModel):
    """A SoundCloud publish job with lifecycle status."""

    job_id: UUID
    release_id: UUID
    status: SoundCloudPublishStatus = SoundCloudPublishStatus.DRAFT
    metadata: SoundCloudMetadata
    warnings: list[SoundCloudPublishWarning] = Field(default_factory=list)
    provider_mode: str = "mock"
    operator_id: str | None = Field(default=None, max_length=200)
    error: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SoundCloudPublishSummary(BaseModel):
    """Summary of SoundCloud publish jobs."""

    total_jobs: int = 0
    drafts: int = 0
    ready: int = 0
    published_mock: int = 0
    failed: int = 0
    blocked: int = 0


# ---------- Merch Capsule Contract (S37) ----------


class MerchCapsuleStatus(StrEnum):
    """Lifecycle status of a merch capsule."""

    DRAFT = "draft"
    LOCKED = "locked"
    EXPORTED_MOCK = "exported_mock"
    ARCHIVED = "archived"


class MerchProductType(StrEnum):
    """Supported merch product types."""

    HEAVYWEIGHT_TEE = "heavyweight_tee"
    OVERSIZED_HOODIE = "oversized_hoodie"
    LONGSLEEVE = "longsleeve"
    BEANIE = "beanie"
    TOTE = "tote"
    POSTER = "poster"
    STICKER_PACK = "sticker_pack"
    VINYL_OBJECT = "vinyl_object"


class MerchProviderGroup(StrEnum):
    """Provider groups for merch fulfillment routing."""

    APPAREL_PROVIDER = "apparel_provider"
    PREMIUM_DROP_PROVIDER = "premium_drop_provider"
    VINYL_PROVIDER = "vinyl_provider"


class MerchAvailability(StrEnum):
    """Availability tier for a merch product (70/20/10 rule)."""

    ALWAYS_ON = "always_on"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


class MerchVariant(BaseModel):
    """Size/color/format variant of a merch product."""

    variant_id: UUID
    label: str = Field(min_length=1, max_length=100)
    sku_suffix: str = Field(default="", max_length=40)
    stock_limit: int | None = Field(default=None, ge=0)


class MerchProduct(BaseModel):
    """A single merch product within a capsule."""

    product_id: UUID
    title: str = Field(min_length=1, max_length=200)
    product_type: MerchProductType
    availability: MerchAvailability = MerchAvailability.UNAVAILABLE
    provider_group: MerchProviderGroup
    price_positioning: str = Field(default="mid", max_length=40)
    artwork_artifact_id: UUID | None = None
    mockup_artifact_id: UUID | None = None
    variants: list[MerchVariant] = Field(default_factory=list)
    active: bool = False


class MerchCapsuleWarning(BaseModel):
    """Warning generated during capsule build or validation."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class MerchCapsule(BaseModel):
    """A merch capsule linked to a ReleasePack."""

    capsule_id: UUID
    release_id: UUID
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    status: MerchCapsuleStatus = MerchCapsuleStatus.DRAFT
    availability_strategy: str = Field(default="70_20_10", max_length=40)
    products: list[MerchProduct] = Field(default_factory=list)
    max_active_products: int = Field(default=5, ge=1, le=10)
    provider_groups: list[MerchProviderGroup] = Field(default_factory=list)
    drop_window_start: str | None = Field(default=None, max_length=30)
    drop_window_end: str | None = Field(default=None, max_length=30)
    notes: str = Field(default="", max_length=2000)
    warnings: list[MerchCapsuleWarning] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MerchCapsuleCreateRequest(BaseModel):
    """Request to create a merch capsule from a ReleasePack."""

    model_config = ConfigDict(extra="forbid")

    release_id: UUID
    notes: str = Field(default="", max_length=2000)


class MerchProductUpdateRequest(BaseModel):
    """Request to update a single product within a MerchCapsule.

    All fields are optional — only provided fields are applied.
    Locked/archived capsules reject updates (409).
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    active: bool | None = None
    availability: MerchAvailability | None = None
    price_positioning: str | None = Field(default=None, max_length=40)
    artwork_artifact_id: UUID | None = None
    mockup_artifact_id: UUID | None = None


class MerchProductUpdateResult(BaseModel):
    """Result of updating a product within a MerchCapsule."""

    capsule: MerchCapsule
    product: MerchProduct
    warnings: list[MerchCapsuleWarning] = Field(default_factory=list)


class MerchProviderExportNotes(BaseModel):
    """Mock export notes for a single provider group."""

    provider_group: MerchProviderGroup
    product_count: int = 0
    notes: str = Field(default="", max_length=1000)
    status: str = Field(default="mock_only", max_length=40)


class MerchExportPayload(BaseModel):
    """Mock export payload for future Printful/TikTok/Shopify integration."""

    capsule_id: UUID
    release_id: UUID
    title: str
    artist: str
    status: MerchCapsuleStatus
    products: list[MerchProduct]
    provider_exports: list[MerchProviderExportNotes] = Field(default_factory=list)
    warnings: list[MerchCapsuleWarning] = Field(default_factory=list)
    tiktok_shop_notes: str = Field(
        default="TikTok Shop integration deferred. Top-of-funnel only.",
        max_length=500,
    )
    printful_notes: str = Field(
        default="Printful adapter not connected. Mock export only.",
        max_length=500,
    )
    shopify_draft_notes: str = Field(
        default="Shopify draft product sync not implemented. No storefront changes.",
        max_length=500,
    )
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MerchCapsuleSummary(BaseModel):
    """Summary of all merch capsules."""

    total_capsules: int = 0
    drafts: int = 0
    locked: int = 0
    exported_mock: int = 0
    archived: int = 0
    total_products: int = 0
    total_active_products: int = 0


# ---------- Ditto Music Distribution Pack (S37) ----------


class DistributionProvider(StrEnum):
    DITTO = "ditto"


class DistributionPackStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    LIVE = "live"
    REJECTED = "rejected"
    TAKEDOWN = "takedown"


class DistributionStore(StrEnum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    YOUTUBE_MUSIC = "youtube_music"
    TIKTOK = "tiktok"
    INSTAGRAM_FACEBOOK = "instagram_facebook"
    DEEZER = "deezer"
    TIDAL = "tidal"
    AMAZON_MUSIC = "amazon_music"


class DistributionReadinessItem(BaseModel):
    """Single readiness check for distribution handoff."""

    code: str = Field(max_length=60)
    label: str = Field(max_length=200)
    passed: bool = False
    notes: str | None = Field(default=None, max_length=500)


class DittoDistributionMetadata(BaseModel):
    """Metadata block that maps to Ditto Music upload fields.

    Produced from a ReleasePack. No real Ditto API calls.
    """

    artist: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    genre: str | None = Field(default=None, max_length=60)
    language: str = Field(default="en", max_length=10)
    explicit: bool = False
    copyright_line: str = Field(default="", max_length=300)
    isrc: str | None = Field(default=None, max_length=15)
    upc: str | None = Field(default=None, max_length=13)
    release_date: str | None = Field(default=None, max_length=30)
    cover_artifact_id: UUID | None = None
    audio_master_artifact_id: UUID | None = None
    store_targets: list[DistributionStore] = Field(default_factory=list)


class DistributionPack(BaseModel):
    """Distribution handoff pack for Ditto Music.

    Created from a ReleasePack. Contains metadata, readiness checklist,
    store targets, and manual status tracking. No real distribution API
    calls — the operator manually uploads to Ditto.
    """

    distribution_id: UUID
    release_id: UUID
    provider: DistributionProvider = DistributionProvider.DITTO
    status: DistributionPackStatus = DistributionPackStatus.DRAFT
    metadata: DittoDistributionMetadata
    readiness_checklist: list[DistributionReadinessItem] = Field(default_factory=list)
    readiness_passed: bool = False
    store_targets: list[DistributionStore] = Field(default_factory=list)
    operator_notes: str = Field(default="", max_length=2000)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DistributionPackCreateRequest(BaseModel):
    """Request to create a distribution pack from a ReleasePack."""

    model_config = ConfigDict(extra="forbid")

    release_id: UUID
    store_targets: list[DistributionStore] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class DistributionPackStatusUpdateRequest(BaseModel):
    """Request to manually update distribution pack status."""

    model_config = ConfigDict(extra="forbid")

    status: DistributionPackStatus
    notes: str = Field(default="", max_length=2000)


class DistributionPackSummary(BaseModel):
    """Summary of all distribution packs."""

    total_packs: int = 0
    drafts: int = 0
    ready: int = 0
    submitted: int = 0
    live: int = 0
    rejected: int = 0
    takedown: int = 0


# ---------- Shopify Draft Provider Boundary (S40) ----------


class ShopifyDraftStatus(StrEnum):
    """Status of a Shopify product draft."""

    DRAFT = "draft"
    EXPORTED_MOCK = "exported_mock"
    BLOCKED = "blocked"
    FAILED = "failed"


class ShopifyVariantDraft(BaseModel):
    """A single variant within a Shopify product draft."""

    variant_id: UUID
    title: str = Field(min_length=1, max_length=200)
    sku_suffix: str = Field(default="", max_length=40)
    option1: str = Field(default="Default", max_length=100)
    price: str = Field(default="0.00", max_length=20)
    requires_shipping: bool = True
    inventory_management: str | None = None
    inventory_quantity: int | None = None


class ShopifyImageRef(BaseModel):
    """Reference to an image for a Shopify product draft."""

    artifact_id: UUID | None = None
    alt: str = Field(default="", max_length=200)
    position: int = 1


class ShopifyProductDraft(BaseModel):
    """A Shopify-compatible product draft built from a MerchProduct.

    No real Shopify API calls. No publishing. No inventory mutation.
    Draft payloads can be inspected and exported later.
    """

    draft_id: UUID
    capsule_id: UUID
    product_id: UUID
    title: str = Field(min_length=1, max_length=200)
    body_html: str = Field(default="", max_length=5000)
    vendor: str = Field(default="SCHLUESSELKINDER", max_length=200)
    product_type: str = Field(default="", max_length=100)
    tags: list[str] = Field(default_factory=list)
    status: ShopifyDraftStatus = ShopifyDraftStatus.DRAFT
    variants: list[ShopifyVariantDraft] = Field(default_factory=list)
    images: list[ShopifyImageRef] = Field(default_factory=list)
    provider_payload: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShopifyDraftCreateRequest(BaseModel):
    """Request to build Shopify drafts from a MerchCapsule."""

    model_config = ConfigDict(extra="forbid")

    capsule_id: UUID


class ShopifyDraftExport(BaseModel):
    """Result of building Shopify drafts from a capsule."""

    capsule_id: UUID
    drafts: list[ShopifyProductDraft] = Field(default_factory=list)
    provider_mode: str = "mock"
    total_products: int = 0
    total_warnings: int = 0
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShopifyDraftSummary(BaseModel):
    """Summary of all Shopify product drafts."""

    total_drafts: int = 0
    draft_status: int = 0
    exported_mock: int = 0
    blocked: int = 0
    failed: int = 0


# ---------- Printful Product Sync Boundary (S41) ----------


class PrintfulSyncStatus(StrEnum):
    """Status of a Printful product sync."""

    DRAFT = "draft"
    EXPORTED_MOCK = "exported_mock"
    BLOCKED = "blocked"
    FAILED = "failed"


class PrintfulPrintTechnique(StrEnum):
    """Print technique hint for Printful catalog mapping."""

    DTG = "dtg"
    EMBROIDERY = "embroidery"
    SUBLIMATION = "sublimation"
    NOT_APPLICABLE = "not_applicable"


class PrintfulVariantSync(BaseModel):
    """A single variant within a Printful product sync."""

    variant_id: UUID
    title: str = Field(min_length=1, max_length=200)
    sku_suffix: str = Field(default="", max_length=40)
    size: str = Field(default="", max_length=40)
    color: str = Field(default="", max_length=40)


class PrintfulProductSync(BaseModel):
    """A Printful-compatible product sync payload built from a MerchProduct.

    No real Printful API calls. No product creation. No fulfillment.
    No inventory sync. Sync payloads can be inspected and exported later.
    """

    sync_id: UUID
    capsule_id: UUID
    product_id: UUID
    title: str = Field(min_length=1, max_length=200)
    product_type: str = Field(default="", max_length=100)
    provider_catalog_hint: str = Field(default="", max_length=200)
    print_technique: PrintfulPrintTechnique = PrintfulPrintTechnique.DTG
    placement: str = Field(default="front", max_length=60)
    variants: list[PrintfulVariantSync] = Field(default_factory=list)
    artwork_artifact_id: UUID | None = None
    mockup_artifact_id: UUID | None = None
    provider_payload: dict = Field(default_factory=dict)
    status: PrintfulSyncStatus = PrintfulSyncStatus.DRAFT
    warnings: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrintfulSyncCreateRequest(BaseModel):
    """Request to build Printful syncs from a MerchCapsule."""

    model_config = ConfigDict(extra="forbid")

    capsule_id: UUID


class PrintfulSyncExport(BaseModel):
    """Result of building Printful syncs from a capsule."""

    capsule_id: UUID
    syncs: list[PrintfulProductSync] = Field(default_factory=list)
    provider_mode: str = "mock"
    total_products: int = 0
    total_warnings: int = 0
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrintfulSyncSummary(BaseModel):
    """Summary of all Printful product syncs."""

    total_syncs: int = 0
    draft_status: int = 0
    exported_mock: int = 0
    blocked: int = 0
    failed: int = 0


# ---------- TikTok Shop Draft Boundary (S42) ----------


class TikTokShopListingStatus(StrEnum):
    """Status of a TikTok Shop listing draft."""

    DRAFT = "draft"
    EXPORTED_MOCK = "exported_mock"
    BLOCKED = "blocked"
    FAILED = "failed"


class TikTokShopContentAngle(StrEnum):
    """Content positioning for TikTok Shop listings."""

    WAREHOUSE_CULTURE = "warehouse_culture"
    SOUNDSYSTEM_ESSENTIAL = "soundsystem_essential"
    LIMITED_CAPSULE = "limited_capsule"
    POLITICAL_DROP = "political_drop"
    COLLECTOR_OBJECT = "collector_object"


class TikTokShopVariantListing(BaseModel):
    """A single variant within a TikTok Shop listing."""

    variant_id: UUID
    title: str = Field(min_length=1, max_length=200)
    sku_suffix: str = Field(default="", max_length=40)
    option: str = Field(default="Default", max_length=100)


class TikTokShopListing(BaseModel):
    """A TikTok Shop-compatible listing draft built from a MerchProduct.

    No real TikTok Shop API calls. No product creation. No publishing.
    No inventory mutation. TikTok Shop is top-of-funnel only.
    """

    listing_id: UUID
    capsule_id: UUID
    product_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    category_hint: str = Field(default="", max_length=200)
    product_type: str = Field(default="", max_length=100)
    tags: list[str] = Field(default_factory=list)
    content_angle: TikTokShopContentAngle = TikTokShopContentAngle.SOUNDSYSTEM_ESSENTIAL
    variants: list[TikTokShopVariantListing] = Field(default_factory=list)
    images: list[UUID] = Field(default_factory=list)
    provider_payload: dict = Field(default_factory=dict)
    status: TikTokShopListingStatus = TikTokShopListingStatus.DRAFT
    warnings: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TikTokShopListingCreateRequest(BaseModel):
    """Request to build TikTok Shop listings from a MerchCapsule."""

    model_config = ConfigDict(extra="forbid")

    capsule_id: UUID


class TikTokShopListingExport(BaseModel):
    """Result of building TikTok Shop listings from a capsule."""

    capsule_id: UUID
    listings: list[TikTokShopListing] = Field(default_factory=list)
    provider_mode: str = "mock"
    total_products: int = 0
    total_warnings: int = 0
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TikTokShopSummary(BaseModel):
    """Summary of all TikTok Shop listing drafts."""

    total_listings: int = 0
    draft_status: int = 0
    exported_mock: int = 0
    blocked: int = 0
    failed: int = 0


# ---------------------------------------------------------------------------
# Merch Provider Aggregation (S43)
# ---------------------------------------------------------------------------


class MerchProviderProductStatus(BaseModel):
    """Per-product status across all commerce providers."""

    product_id: UUID
    title: str = ""
    product_type: str = ""
    availability: str = ""
    active: bool = True
    shopify_status: str = "not_created"
    printful_status: str = "not_created"
    tiktok_status: str = "not_created"
    shopify_warnings: list[str] = Field(default_factory=list)
    printful_warnings: list[str] = Field(default_factory=list)
    tiktok_warnings: list[str] = Field(default_factory=list)
    total_warnings: int = 0
    stale: bool = False


class MerchProviderStatus(BaseModel):
    """Status summary for a single provider."""

    provider: str = ""
    mode: str = "mock"
    total_products: int = 0
    exported_mock: int = 0
    blocked: int = 0
    draft: int = 0
    not_created: int = 0
    warnings: int = 0


class MerchProviderAggregationSummary(BaseModel):
    """Aggregate counts across all providers."""

    total_warnings: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    exported_mock_count: int = 0
    not_created_count: int = 0


class MerchProviderAggregation(BaseModel):
    """Unified provider aggregation view for a MerchCapsule.

    Read-only. No real commerce API calls. No inventory mutation.
    Operational preview only.
    """

    capsule_id: UUID
    capsule_title: str = ""
    capsule_status: str = ""
    product_count: int = 0
    active_product_count: int = 0
    providers: dict[str, MerchProviderStatus] = Field(default_factory=dict)
    products: list[MerchProviderProductStatus] = Field(default_factory=list)
    summary: MerchProviderAggregationSummary = Field(
        default_factory=MerchProviderAggregationSummary
    )
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Campaign OS Foundation (S45) ----------


class CampaignStatus(StrEnum):
    """Lifecycle status of a campaign."""

    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CampaignChannel(StrEnum):
    """Distribution/marketing channels a campaign can target."""

    SOUNDCLOUD = "soundcloud"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    DISCORD = "discord"
    MERCH = "merch"
    DISTRIBUTION = "distribution"


class CampaignTaskStatus(StrEnum):
    """Status of a single campaign task."""

    PENDING = "pending"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class CampaignTask(BaseModel):
    """A single operational task within a campaign."""

    task_id: UUID
    channel: CampaignChannel
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=500)
    status: CampaignTaskStatus = CampaignTaskStatus.PENDING
    depends_on: list[str] = Field(default_factory=list)
    linked_object_id: UUID | None = None
    warnings: list[str] = Field(default_factory=list)


class CampaignTimelineItem(BaseModel):
    """A timestamped event in the campaign timeline."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event: str = Field(max_length=200)
    object_type: str = Field(default="", max_length=60)
    object_id: UUID | None = None
    notes: str = Field(default="", max_length=500)


class CampaignWarning(BaseModel):
    """Warning generated during campaign build or evaluation."""

    code: str = Field(max_length=60)
    message: str = Field(max_length=500)


class Campaign(BaseModel):
    """Operational campaign object orchestrating a release across all channels.

    One ReleasePack → one Campaign. Read-model + orchestration first.
    No automation execution. No social API calls. No scheduling engine.
    """

    campaign_id: UUID
    release_id: UUID
    title: str = Field(min_length=1, max_length=200)
    status: CampaignStatus = CampaignStatus.PLANNING
    channels: list[CampaignChannel] = Field(default_factory=list)
    tasks: list[CampaignTask] = Field(default_factory=list)
    timeline: list[CampaignTimelineItem] = Field(default_factory=list)
    linked_merch_capsule_ids: list[UUID] = Field(default_factory=list)
    linked_distribution_pack_ids: list[UUID] = Field(default_factory=list)
    linked_soundcloud_job_ids: list[UUID] = Field(default_factory=list)
    warnings: list[CampaignWarning] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignCreateRequest(BaseModel):
    """Request to create a campaign from a ReleasePack."""

    model_config = ConfigDict(extra="forbid")

    release_id: UUID
    channels: list[CampaignChannel] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class CampaignUpdateRequest(BaseModel):
    """Request to update campaign fields."""

    model_config = ConfigDict(extra="forbid")

    status: CampaignStatus | None = None
    channels: list[CampaignChannel] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CampaignSummary(BaseModel):
    """Summary of all campaigns."""

    total_campaigns: int = 0
    planning: int = 0
    ready: int = 0
    active: int = 0
    completed: int = 0
    archived: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0


# ---------- Vinyl Release Object (S46) ----------


class VinylProviderGroup(StrEnum):
    """Vinyl provider groups."""

    ELASTIC_STAGE = "elastic_stage"
    DISC_ARCHIVE = "disc_archive"
    VINYLOGRAPH = "vinylograph"
    MANUAL_COLLECTOR = "manual_collector"


class VinylReleaseStatus(StrEnum):
    """Vinyl release lifecycle states."""

    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    TEST_PRESSING = "test_pressing"
    APPROVED = "approved"
    LIVE = "live"
    ARCHIVED = "archived"
    BLOCKED = "blocked"


class VinylFormat(StrEnum):
    """Physical vinyl format types."""

    SEVEN_INCH = "seven_inch"
    TEN_INCH = "ten_inch"
    TWELVE_INCH = "twelve_inch"
    DUBPLATE = "dubplate"
    LATHE_CUT = "lathe_cut"


class VinylEditionType(StrEnum):
    """Edition types for vinyl releases."""

    VINYL_ON_DEMAND = "vinyl_on_demand"
    LIMITED_NUMBERED = "limited_numbered"
    WHITE_LABEL = "white_label"
    COLLECTOR_BOX = "collector_box"


class VinylReadinessItem(BaseModel):
    """Single readiness check for a vinyl release."""

    code: str = Field(max_length=60)
    label: str = Field(max_length=200)
    passed: bool = False
    warning: str = Field(default="", max_length=500)


class VinylTrackListing(BaseModel):
    """A track entry for Side A or Side B."""

    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    duration_seconds: float | None = None
    artifact_id: UUID | None = None


class VinylReleaseObject(BaseModel):
    """Collector-vinyl release object.

    Vinyl is not normal merch. It is a collector artifact with its own
    lifecycle, readiness checks, and provider handoff contract.
    No real manufacturing or vendor API calls.
    """

    vinyl_id: UUID
    release_id: UUID
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    provider_group: VinylProviderGroup = VinylProviderGroup.ELASTIC_STAGE
    status: VinylReleaseStatus = VinylReleaseStatus.DRAFT
    format: VinylFormat = VinylFormat.TWELVE_INCH
    edition_type: VinylEditionType = VinylEditionType.VINYL_ON_DEMAND
    pressing_quantity: int | None = Field(default=None, ge=1)
    numbered: bool = False
    side_a_tracks: list[VinylTrackListing] = Field(default_factory=list)
    side_b_tracks: list[VinylTrackListing] = Field(default_factory=list)
    cover_artifact_id: UUID | None = None
    audio_master_artifact_id: UUID | None = None
    export_artifact_id: UUID | None = None
    soundcloud_job_id: UUID | None = None
    readiness_items: list[VinylReadinessItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VinylReleaseCreateRequest(BaseModel):
    """Request to create a vinyl release from a ReleasePack."""

    model_config = ConfigDict(extra="forbid")

    release_id: UUID
    format: VinylFormat = VinylFormat.TWELVE_INCH
    edition_type: VinylEditionType = VinylEditionType.VINYL_ON_DEMAND
    pressing_quantity: int | None = Field(default=None, ge=1)
    numbered: bool = False
    notes: str = Field(default="", max_length=2000)


class VinylReleaseStatusUpdateRequest(BaseModel):
    """Request to update vinyl release status."""

    model_config = ConfigDict(extra="forbid")

    status: VinylReleaseStatus


class VinylExportPayload(BaseModel):
    """Export payload for vinyl provider handoff.

    Contains all metadata needed for manual handoff to elasticStage,
    DISC_ARCHIVE, or other vinyl providers. No real API calls.
    """

    vinyl_id: UUID
    release_id: UUID
    title: str
    artist: str
    provider_group: VinylProviderGroup
    format: VinylFormat
    edition_type: VinylEditionType
    pressing_quantity: int | None = None
    numbered: bool = False
    side_a_tracks: list[VinylTrackListing] = Field(default_factory=list)
    side_b_tracks: list[VinylTrackListing] = Field(default_factory=list)
    cover_artifact_id: UUID | None = None
    audio_master_artifact_id: UUID | None = None
    readiness_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    handoff_notes: str = Field(default="Manual vinyl handoff. No manufacturing order placed.")
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VinylReleaseSummary(BaseModel):
    """Summary of all vinyl releases."""

    total_releases: int = 0
    draft: int = 0
    ready: int = 0
    submitted: int = 0
    test_pressing: int = 0
    approved: int = 0
    live: int = 0
    archived: int = 0
    blocked: int = 0


# ---------- Analytics Event Graph (S49) ----------


class AnalyticsSource(StrEnum):
    """Source platform for an analytics event."""

    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spotify"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    DISCORD = "discord"
    SHOPIFY = "shopify"
    PRINTFUL = "printful"
    TIKTOK_SHOP = "tiktok_shop"
    DITTO = "ditto"
    CAMPAIGN = "campaign"
    MANUAL = "manual"


class AnalyticsMetric(StrEnum):
    """Metric type for analytics events."""

    PLAYS = "plays"
    STREAMS = "streams"
    SAVES = "saves"
    LIKES = "likes"
    REPOSTS = "reposts"
    COMMENTS = "comments"
    SHARES = "shares"
    VIEWS = "views"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    ORDERS = "orders"
    REVENUE = "revenue"
    FOLLOWERS = "followers"
    ENGAGEMENT_RATE = "engagement_rate"
    WATCH_TIME = "watch_time"
    CART_ADDS = "cart_adds"
    VINYL_INTEREST = "vinyl_interest"
    MERCH_INTEREST = "merch_interest"
    CAMPAIGN_HEAT = "campaign_heat"


class AnalyticsGranularity(StrEnum):
    """Time granularity for analytics events."""

    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AnalyticsEvent(BaseModel):
    """A single normalized analytics event.

    All provider data normalizes into this unified schema.
    No real provider API calls. Internal graph only.
    """

    event_id: UUID
    source: AnalyticsSource
    metric: AnalyticsMetric
    value: float
    granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY
    campaign_id: UUID | None = None
    release_id: UUID | None = None
    track_id: UUID | None = None
    merch_capsule_id: UUID | None = None
    vinyl_id: UUID | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = Field(default_factory=dict)


class AnalyticsEventCreateRequest(BaseModel):
    """Request to create one or more analytics events."""

    model_config = ConfigDict(extra="forbid")

    source: AnalyticsSource
    metric: AnalyticsMetric
    value: float
    granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY
    campaign_id: UUID | None = None
    release_id: UUID | None = None
    track_id: UUID | None = None
    merch_capsule_id: UUID | None = None
    vinyl_id: UUID | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AnalyticsSnapshot(BaseModel):
    """Aggregated analytics snapshot over a time window."""

    snapshot_id: UUID
    source: AnalyticsSource
    metric: AnalyticsMetric
    aggregate_value: float
    period_start: datetime
    period_end: datetime
    dimensions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChannelPerformance(BaseModel):
    """Performance summary for a single analytics source/channel."""

    source: AnalyticsSource
    total_events: int = 0
    total_value: float = 0.0
    top_metric: AnalyticsMetric | None = None
    top_metric_value: float = 0.0


class CampaignPerformance(BaseModel):
    """Performance summary for a single campaign."""

    campaign_id: UUID
    total_reach: float = 0.0
    engagement: float = 0.0
    conversions: float = 0.0
    revenue_estimate: float = 0.0
    heat_score: float = 0.0
    top_channel: AnalyticsSource | None = None
    warnings: list[str] = Field(default_factory=list)


class TrackPerformance(BaseModel):
    """Performance summary for a single track."""

    track_id: UUID
    title: str = ""
    total_streams: float = 0.0
    saves: float = 0.0
    shares: float = 0.0
    viral_score: float = 0.0
    top_platform: AnalyticsSource | None = None


class AnalyticsSummary(BaseModel):
    """Global analytics summary."""

    total_events: int = 0
    total_campaigns: int = 0
    total_tracks: int = 0
    source_breakdown: dict[str, int] = Field(default_factory=dict)
    metric_breakdown: dict[str, int] = Field(default_factory=dict)
    latest_event_at: datetime | None = None


# ---------- Intelligence Engine (S50) ----------


class CorrelationStrength(StrEnum):
    """Strength of a detected correlation."""

    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    EXPLOSIVE = "explosive"


class TrendDirection(StrEnum):
    """Trend direction for a metric or platform."""

    DOWN = "down"
    STABLE = "stable"
    RISING = "rising"
    EXPLODING = "exploding"


class CorrelationSignal(StrEnum):
    """Known cross-platform correlation signals."""

    TIKTOK_TO_STREAMING = "tiktok_to_streaming"
    INSTAGRAM_TO_MERCH = "instagram_to_merch"
    DISCORD_TO_CONVERSION = "discord_to_conversion"
    SOUNDCLOUD_TO_VINYL = "soundcloud_to_vinyl"
    MERCH_TO_FOLLOWERS = "merch_to_followers"
    CAMPAIGN_TO_STREAMING = "campaign_to_streaming"
    RELEASE_TO_SHOP = "release_to_shop"


class ViralMoment(BaseModel):
    """A detected viral spike in the analytics graph."""

    moment_id: UUID
    title: str = Field(max_length=200)
    source: AnalyticsSource
    trigger_metric: AnalyticsMetric
    before_value: float = 0.0
    after_value: float = 0.0
    growth_percent: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    related_release_id: UUID | None = None
    related_campaign_id: UUID | None = None
    strength: CorrelationStrength = CorrelationStrength.WEAK


class AudienceHeatmap(BaseModel):
    """Platform audience heat summary."""

    platform: AnalyticsSource
    audience_size: float = 0.0
    engagement: float = 0.0
    conversion_rate: float = 0.0
    heat_score: float = 0.0
    trend: TrendDirection = TrendDirection.STABLE


class RevenueCorrelation(BaseModel):
    """Revenue attribution correlation to a source channel."""

    source: AnalyticsSource
    revenue: float = 0.0
    related_metric: AnalyticsMetric | None = None
    related_metric_value: float = 0.0
    conversion_strength: CorrelationStrength = CorrelationStrength.WEAK


class TimelineCorrelation(BaseModel):
    """Single point in the timeline fusion view."""

    timestamp: datetime
    event_count: int = 0
    dominant_source: AnalyticsSource | None = None
    dominant_metric: AnalyticsMetric | None = None
    heat: float = 0.0


class IntelligenceOverview(BaseModel):
    """Full intelligence overview for the dashboard.

    Deterministic. No ML. No AI inference. No external calls.
    Computed from internal analytics event graph only.
    """

    total_heat: float = 0.0
    hottest_platform: AnalyticsSource | None = None
    hottest_release_id: UUID | None = None
    hottest_campaign_id: UUID | None = None
    viral_moments: list[ViralMoment] = Field(default_factory=list)
    audience_heatmaps: list[AudienceHeatmap] = Field(default_factory=list)
    revenue_correlations: list[RevenueCorrelation] = Field(default_factory=list)
    timeline: list[TimelineCorrelation] = Field(default_factory=list)
    trend: TrendDirection = TrendDirection.STABLE
    warnings: list[str] = Field(default_factory=list)


# ---------- Provider Connector Framework (S51) ----------


class ConnectorType(StrEnum):
    """Provider connector type identifier."""

    SPOTIFY = "spotify"
    SOUNDCLOUD = "soundcloud"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    DISCORD = "discord"
    DITTO = "ditto"
    SHOPIFY = "shopify"
    PRINTFUL = "printful"
    TIKTOK_SHOP = "tiktok_shop"
    MANUAL = "manual"


class ConnectorStatus(StrEnum):
    """Connector operational status."""

    DISCONNECTED = "disconnected"
    CONFIGURED = "configured"
    READY = "ready"
    BLOCKED = "blocked"
    MOCK = "mock"


class ConnectorCapability(StrEnum):
    """Capability a connector can provide."""

    ANALYTICS_PULL = "analytics_pull"
    PUBLISHING = "publishing"
    COMMERCE = "commerce"
    DISTRIBUTION = "distribution"
    SOCIAL = "social"
    STREAMING = "streaming"
    MERCH = "merch"
    VINYL = "vinyl"
    CAMPAIGN_SYNC = "campaign_sync"


class ConnectorSyncMode(StrEnum):
    """How a connector synchronizes data."""

    MANUAL = "manual"
    MOCK = "mock"
    DISABLED = "disabled"


class ProviderConnector(BaseModel):
    """A registered provider connector in the framework."""

    connector_id: UUID
    connector_type: ConnectorType
    status: ConnectorStatus = ConnectorStatus.DISCONNECTED
    sync_mode: ConnectorSyncMode = ConnectorSyncMode.DISABLED
    capabilities: list[ConnectorCapability] = Field(default_factory=list)
    enabled: bool = False
    mock_mode: bool = True
    last_sync_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ConnectorHealth(BaseModel):
    """Health check result for a connector."""

    connector_type: ConnectorType
    status: ConnectorStatus
    healthy: bool = False
    warnings: list[str] = Field(default_factory=list)
    missing_configuration: list[str] = Field(default_factory=list)
    capabilities: list[ConnectorCapability] = Field(default_factory=list)


class ConnectorSyncPreview(BaseModel):
    """Preview of what a connector sync would produce."""

    connector_type: ConnectorType
    event_count: int = 0
    normalized_events: list[AnalyticsEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)


class ConnectorRegistrySummary(BaseModel):
    """Summary of all registered connectors."""

    total_connectors: int = 0
    enabled_connectors: int = 0
    ready_connectors: int = 0
    mock_connectors: int = 0
    blocked_connectors: int = 0
    capability_breakdown: dict[str, int] = Field(default_factory=dict)
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


# ---------- Connector Import Audit (S53) ----------


class ConnectorImportAuditRecord(BaseModel):
    """Audit record for a single connector import operation."""

    audit_id: UUID
    connector_type: ConnectorType
    operator_id: str
    event_count: int = 0
    event_ids: list[UUID] = Field(default_factory=list)
    status: Literal["completed", "failed", "partial"] = "completed"
    error_message: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectorImportAuditSummary(BaseModel):
    """Summary of all connector import audit records."""

    total_imports: int = 0
    total_events_imported: int = 0
    connector_breakdown: dict[str, int] = Field(default_factory=dict)
    operator_breakdown: dict[str, int] = Field(default_factory=dict)
    latest_import_at: datetime | None = None


# ---------- Intelligence Snapshot Persistence (S54) ----------


class IntelligenceSnapshotStatus(StrEnum):
    """Lifecycle status of an intelligence snapshot."""

    CREATED = "created"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class IntelligenceSnapshot(BaseModel):
    """A frozen point-in-time intelligence overview snapshot.

    Created only by explicit operator POST. No automation.
    No scheduler. No background workers.
    """

    snapshot_id: UUID
    status: IntelligenceSnapshotStatus = IntelligenceSnapshotStatus.CREATED
    overview: IntelligenceOverview
    event_count: int = 0
    source_event_latest_at: datetime | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntelligenceSnapshotCreateRequest(BaseModel):
    """Request body for creating an intelligence snapshot."""

    notes: str | None = None


class IntelligenceSnapshotSummary(BaseModel):
    """Summary of all intelligence snapshots."""

    total_snapshots: int = 0
    active_snapshots: int = 0
    archived_snapshots: int = 0
    latest_snapshot_at: datetime | None = None
    latest_total_heat: float = 0.0
    heat_delta_from_previous: float | None = None


# ---------- Intelligence Snapshot Diff (S55) ----------


class SnapshotDiffDirection(StrEnum):
    """Overall direction of change between two snapshots."""

    IMPROVED = "improved"
    DECLINED = "declined"
    UNCHANGED = "unchanged"
    MIXED = "mixed"


class SnapshotMetricDelta(BaseModel):
    """Delta for a single metric between two snapshots."""

    metric: str
    before_value: float = 0.0
    after_value: float = 0.0
    delta: float = 0.0
    delta_percent: float | None = None
    direction: SnapshotDiffDirection = SnapshotDiffDirection.UNCHANGED


class SnapshotPlatformDelta(BaseModel):
    """Delta for a single platform between two snapshots."""

    platform: AnalyticsSource
    before_heat: float = 0.0
    after_heat: float = 0.0
    heat_delta: float = 0.0
    direction: SnapshotDiffDirection = SnapshotDiffDirection.UNCHANGED
    engagement_delta: float = 0.0
    conversion_delta: float = 0.0


class SnapshotViralMomentDelta(BaseModel):
    """Delta for a single viral moment between two snapshots."""

    title: str
    before_strength: CorrelationStrength | None = None
    after_strength: CorrelationStrength | None = None
    appeared: bool = False
    disappeared: bool = False
    direction: SnapshotDiffDirection = SnapshotDiffDirection.UNCHANGED


class IntelligenceSnapshotDiff(BaseModel):
    """Deterministic comparison between two intelligence snapshots.

    Read-only. No persistence. No automation.
    Computed on demand from two existing snapshots.
    """

    before_snapshot_id: UUID
    after_snapshot_id: UUID
    before_created_at: datetime
    after_created_at: datetime
    overall_direction: SnapshotDiffDirection = SnapshotDiffDirection.UNCHANGED
    total_heat_delta: float = 0.0
    total_heat_delta_percent: float | None = None
    platform_deltas: list[SnapshotPlatformDelta] = Field(default_factory=list)
    viral_moment_deltas: list[SnapshotViralMomentDelta] = Field(default_factory=list)
    revenue_delta: SnapshotMetricDelta | None = None
    warning_changes: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Campaign Automation Rules (S57) ----------


class CampaignAutomationRuleStatus(StrEnum):
    """Lifecycle status of an automation rule definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CampaignAutomationTrigger(StrEnum):
    """Events that can trigger an automation rule (dry-run only)."""

    RELEASE_READY = "release_ready"
    CAMPAIGN_READY = "campaign_ready"
    CAMPAIGN_ACTIVE = "campaign_active"
    DISTRIBUTION_READY = "distribution_ready"
    MERCH_CAPSULE_LOCKED = "merch_capsule_locked"
    VINYL_READY = "vinyl_ready"
    INTELLIGENCE_HEAT_ABOVE_THRESHOLD = "intelligence_heat_above_threshold"
    SNAPSHOT_HEAT_DELTA_ABOVE_THRESHOLD = "snapshot_heat_delta_above_threshold"


class CampaignAutomationAction(StrEnum):
    """Actions that a rule would take (dry-run only — never executed)."""

    MARK_CAMPAIGN_READY = "mark_campaign_ready"
    MARK_CAMPAIGN_ACTIVE = "mark_campaign_active"
    CREATE_TASK = "create_task"
    ADD_WARNING = "add_warning"
    NOTIFY_OPERATOR = "notify_operator"
    NO_OP = "no_op"


class CampaignAutomationDryRunStatus(StrEnum):
    """Result status of a dry-run evaluation."""

    WOULD_RUN = "would_run"
    BLOCKED = "blocked"
    NO_MATCH = "no_match"


class CampaignAutomationRule(BaseModel):
    """Automation rule definition. Dry-run only — never executed.

    Rules define trigger conditions and proposed actions. The dry-run
    evaluator checks whether a rule's conditions match the current
    campaign state and reports what would happen. No mutations occur.
    """

    rule_id: UUID
    campaign_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    status: CampaignAutomationRuleStatus = CampaignAutomationRuleStatus.DRAFT
    trigger: CampaignAutomationTrigger
    action: CampaignAutomationAction
    conditions: dict[str, object] = Field(default_factory=dict)
    action_payload: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignAutomationRuleCreateRequest(BaseModel):
    """Request to create a new automation rule definition."""

    model_config = ConfigDict(extra="forbid")

    campaign_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    trigger: CampaignAutomationTrigger
    action: CampaignAutomationAction
    conditions: dict[str, object] = Field(default_factory=dict)
    action_payload: dict[str, object] = Field(default_factory=dict)


class CampaignAutomationRuleUpdateRequest(BaseModel):
    """Request to update an automation rule definition."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=200)
    status: CampaignAutomationRuleStatus | None = None
    trigger: CampaignAutomationTrigger | None = None
    action: CampaignAutomationAction | None = None
    conditions: dict[str, object] | None = None
    action_payload: dict[str, object] | None = None


class CampaignAutomationDryRunResult(BaseModel):
    """Result of evaluating an automation rule against a campaign.

    Read-only. No mutations. No side effects.
    Reports what *would* happen if the rule were executed.
    """

    rule_id: UUID
    campaign_id: UUID
    status: CampaignAutomationDryRunStatus
    matched: bool = False
    blocked_reasons: list[str] = Field(default_factory=list)
    proposed_changes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignAutomationRuleSummary(BaseModel):
    """Summary of all automation rule definitions."""

    total_rules: int = 0
    draft: int = 0
    active: int = 0
    paused: int = 0
    archived: int = 0


# ---------- Automation Execution Queue Boundary (S58) ----------


class AutomationExecutionMode(StrEnum):
    """Modes for the automation execution boundary.

    DISABLED (default) — execution requests are accepted but jobs are BLOCKED.
    MOCK — jobs may transition to COMPLETED_MOCK without side effects.

    No real execution. No scheduler. No background workers.
    No external API calls. No provider mutations.
    """

    DISABLED = "disabled"
    MOCK = "mock"


class AutomationExecutionStatus(StrEnum):
    """Lifecycle status of an automation execution job."""

    QUEUED = "queued"
    BLOCKED = "blocked"
    COMPLETED_MOCK = "completed_mock"
    FAILED = "failed"


class AutomationExecutionJob(BaseModel):
    """Execution job created from a dry-run result.

    A queued job has no side effects on the campaign or any provider.
    Even in MOCK mode, the job records intent only — no real automation runs.
    """

    execution_id: UUID
    rule_id: UUID
    campaign_id: UUID
    dry_run_status: CampaignAutomationDryRunStatus
    status: AutomationExecutionStatus
    proposed_changes: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class AutomationExecutionCreateRequest(BaseModel):
    """Request to queue an execution job from a rule.

    The server runs the dry-run evaluator first, then creates a job.
    The job's status depends on the configured execution mode.
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: UUID


class AutomationExecutionResult(BaseModel):
    """Result wrapper for queue-execution and execute-mock operations.

    Reports the job state plus a note that explains the operator UX.
    """

    job: AutomationExecutionJob
    note: str = ""


class AutomationExecutionSummary(BaseModel):
    """Summary of all execution jobs."""

    total: int = 0
    queued: int = 0
    blocked: int = 0
    completed_mock: int = 0
    failed: int = 0
    execution_mode: AutomationExecutionMode = AutomationExecutionMode.DISABLED


# ---------- Automation Execution Audit Log (S59) ----------


class AutomationExecutionAuditRecord(BaseModel):
    """Immutable audit record for an execution state transition.

    Append-only. Records the intent behind every state change on an
    AutomationExecutionJob. No side effects. No mutations of any other
    object. Operator identity is preserved when the transition was
    operator-triggered.
    """

    audit_id: UUID
    execution_id: UUID
    rule_id: UUID
    campaign_id: UUID
    from_status: AutomationExecutionStatus | None = None
    to_status: AutomationExecutionStatus
    operator_id: str | None = Field(default=None, max_length=200)
    reason: str | None = Field(default=None, max_length=200)
    details: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutomationExecutionAuditSummary(BaseModel):
    """Summary of all execution audit records."""

    total_records: int = 0
    by_to_status: dict[str, int] = Field(default_factory=dict)
    by_reason: dict[str, int] = Field(default_factory=dict)
    operator_breakdown: dict[str, int] = Field(default_factory=dict)
    latest_record_at: datetime | None = None


# ---------- Automation Rule Templates (S60) ----------


class CampaignAutomationTemplateCategory(StrEnum):
    """Operator-facing category for an automation rule template."""

    RELEASE_OPS = "release_ops"
    MERCH_OPS = "merch_ops"
    VINYL_OPS = "vinyl_ops"
    INTELLIGENCE_OPS = "intelligence_ops"
    OPERATOR_NOTIFICATION = "operator_notification"


class CampaignAutomationRuleTemplate(BaseModel):
    """Definition-only template that operators can instantiate onto a campaign.

    Templates create CampaignAutomationRule records when instantiated. No
    automation executes. No scheduler. No background workers. No webhooks.
    """

    template_id: UUID
    slug: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    category: CampaignAutomationTemplateCategory
    trigger: CampaignAutomationTrigger
    action: CampaignAutomationAction
    default_conditions: dict[str, object] = Field(default_factory=dict)
    default_action_payload: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    enabled: bool = True


class CampaignAutomationTemplateInstantiationRequest(BaseModel):
    """Request to instantiate a template onto a campaign.

    Stores a CampaignAutomationRule definition only. No execution, no jobs,
    no audit records, no provider calls.
    """

    model_config = ConfigDict(extra="forbid")

    campaign_id: UUID
    override_name: str | None = Field(default=None, max_length=200)
    condition_overrides: dict[str, object] = Field(default_factory=dict)
    action_payload_overrides: dict[str, object] = Field(default_factory=dict)


class CampaignAutomationTemplateSummary(BaseModel):
    """Summary of the curated template library."""

    total_templates: int = 0
    enabled_templates: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)


# ---------- Release-to-Campaign Command Center (S61) ----------


class CommandCenterReadinessStatus(StrEnum):
    """Operator-readability flag for a readiness item.

    READY    — green; all prerequisites met.
    WARNING  — yellow; non-blocking gap.
    BLOCKED  — orange; explicit blocker on this subsystem.
    MISSING  — neutral; the linked object does not exist yet.
    """

    READY = "ready"
    WARNING = "warning"
    BLOCKED = "blocked"
    MISSING = "missing"


class CommandCenterReadinessItem(BaseModel):
    """One row on the Command Center readiness board."""

    code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=200)
    status: CommandCenterReadinessStatus
    linked_object_id: UUID | None = None
    warnings: list[str] = Field(default_factory=list)


class CommandCenterRecommendedTemplate(BaseModel):
    """A template recommendation with attached-state inference."""

    template_slug: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    reason: str = Field(default="", max_length=300)
    already_attached: bool = False
    warnings: list[str] = Field(default_factory=list)


class ReleaseCommandCenter(BaseModel):
    """Read-model snapshot for a single release.

    Aggregates state across release, campaign, automation, merch,
    distribution, vinyl, and analytics. No execution side effects.
    """

    release_id: UUID
    release_title: str
    campaign_id: UUID | None = None
    campaign_status: CampaignStatus | None = None
    readiness_items: list[CommandCenterReadinessItem] = Field(default_factory=list)
    recommended_templates: list[CommandCenterRecommendedTemplate] = Field(default_factory=list)
    linked_merch_capsule_ids: list[UUID] = Field(default_factory=list)
    linked_distribution_pack_ids: list[UUID] = Field(default_factory=list)
    linked_vinyl_ids: list[UUID] = Field(default_factory=list)
    automation_rule_count: int = 0
    dry_run_summary: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ReleaseCommandCenterCreateRequest(BaseModel):
    """Reserved for future per-release overrides. Empty for now."""

    model_config = ConfigDict(extra="forbid")


class ReleaseCommandCenterBootstrapResult(BaseModel):
    """Result of the bootstrap action.

    Bootstrap may create a Campaign (if missing) and instantiate
    recommended templates as DRAFT rule definitions. It never queues
    or executes automation, never calls providers, never mutates the
    campaign beyond initial creation.
    """

    command_center: ReleaseCommandCenter
    created_campaign: bool = False
    instantiated_rule_ids: list[UUID] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------- Commerce Sync Dashboard (S64) ----------


class CommerceSyncProvider(StrEnum):
    """Provider key on the Commerce Sync dashboard."""

    SHOPIFY = "shopify"
    PRINTFUL = "printful"


class CommerceSyncStatus(StrEnum):
    """Aggregate sync status for one provider on one capsule.

    Determined deterministically from the underlying draft / sync rows.
    """

    NOT_SYNCED = "not_synced"
    SYNCED_MOCK = "synced_mock"
    SYNCED_LIVE = "synced_live"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class CommerceSyncProviderState(BaseModel):
    """Per-provider sync state for a single capsule.

    Read-model. No mutations. No tokens. No provider URLs that require
    auth.
    """

    provider: CommerceSyncProvider
    status: CommerceSyncStatus = CommerceSyncStatus.NOT_SYNCED
    provider_mode: str = "mock"
    item_count: int = 0
    synced_item_count: int = 0
    blocked_item_count: int = 0
    failed_item_count: int = 0
    provider_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    last_synced_at: datetime | None = None


class CommerceCapsuleSyncState(BaseModel):
    """Read-model snapshot for one capsule on the Commerce Sync dashboard."""

    capsule_id: UUID
    release_id: UUID
    title: str
    product_count: int = 0
    shopify: CommerceSyncProviderState
    printful: CommerceSyncProviderState
    overall_status: CommerceSyncStatus = CommerceSyncStatus.NOT_SYNCED
    warnings: list[str] = Field(default_factory=list)


class CommerceCapsuleSyncResult(BaseModel):
    """Result of the operator-triggered "sync both" action for one capsule.

    Carries the post-sync state plus the raw provider exports. Sync runs
    sequentially: Shopify first, then Printful. Neither call publishes,
    mutates inventory, orders, customers, or webhooks.
    """

    capsule_id: UUID
    shopify_result: ShopifyDraftExport | None = None
    printful_result: PrintfulSyncExport | None = None
    overall_status: CommerceSyncStatus = CommerceSyncStatus.NOT_SYNCED
    state: CommerceCapsuleSyncState
    warnings: list[str] = Field(default_factory=list)


class CommerceSyncSummary(BaseModel):
    """Summary of every capsule on the Commerce Sync dashboard."""

    total_capsules: int = 0
    not_synced: int = 0
    synced_mock: int = 0
    synced_live: int = 0
    partial: int = 0
    blocked: int = 0
    failed: int = 0
    shopify_provider_mode: Literal["mock", "shopify"] = "mock"
    printful_provider_mode: Literal["mock", "printful"] = "mock"


# ---------- Commerce Sync Audit Log (S65) ----------


class CommerceSyncAuditAction(StrEnum):
    """Action recorded on a Commerce Sync audit row."""

    SYNC_SHOPIFY = "sync_shopify"
    SYNC_PRINTFUL = "sync_printful"
    SYNC_BOTH = "sync_both"


class CommerceSyncAuditRecord(BaseModel):
    """Immutable audit row for one commerce-sync invocation.

    Append-only. Records operator intent and resulting per-provider
    summary state. NEVER carries provider tokens — ``details`` may
    contain Shopify product IDs / handles and Printful sync product IDs,
    nothing more.
    """

    audit_id: UUID
    capsule_id: UUID
    release_id: UUID | None = None
    operator_id: str | None = Field(default=None, max_length=200)
    action: CommerceSyncAuditAction
    overall_status: CommerceSyncStatus
    shopify_status: CommerceSyncStatus | None = None
    printful_status: CommerceSyncStatus | None = None
    shopify_item_count: int = 0
    printful_item_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommerceSyncAuditSummary(BaseModel):
    """Summary of every Commerce Sync audit row."""

    total_records: int = 0
    records_by_action: dict[str, int] = Field(default_factory=dict)
    records_by_status: dict[str, int] = Field(default_factory=dict)
    latest_record_at: datetime | None = None
    total_shopify_items: int = 0
    total_printful_items: int = 0


# ---------- Newsletter Subscribe (S66) ----------


class NewsletterSubscribeStatus(StrEnum):
    """Outcome of a public newsletter subscribe attempt.

    SUBSCRIBED — Listmonk accepted and confirmed the subscriber.
    PENDING    — Listmonk created the subscriber but is waiting for double
                 opt-in confirmation.
    OFFLINE    — Listmonk is not configured. The request was accepted by
                 the API surface, but no upstream call was made.
    FAILED     — Listmonk returned an error. We never reveal the upstream
                 error verbatim.
    """

    SUBSCRIBED = "subscribed"
    PENDING = "pending"
    OFFLINE = "offline"
    FAILED = "failed"


class NewsletterSubscribeRequest(BaseModel):
    """Public newsletter subscribe payload.

    Only `email` is required. `source` and `tags` are operator-readable
    routing hints — both are validated against an allowlist server-side.
    No tracking IDs. No IP. No referrer.
    """

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    source: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list)


class NewsletterSubscribeResponse(BaseModel):
    """Public newsletter subscribe response.

    The raw email address is NEVER echoed. We return a sha256 hash so the
    client can reconcile the submission with its own state without a
    server-side cookie.
    """

    ok: bool
    status: NewsletterSubscribeStatus
    message: str = Field(default="", max_length=200)
    email_hash: str = Field(min_length=64, max_length=64)
