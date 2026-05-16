from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class CompiledPromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    prompt_modules: PromptModules
    character_code: str = Field(default="SHIBARI_KAWAII", min_length=2, max_length=80)
    lyrics: str | None = Field(default=None, max_length=12000)
    technical: TechnicalControls = Field(default_factory=TechnicalControls)


class CompiledPrompt(BaseModel):
    prompt_text: str
    negative_prompt: str
    safety_notes: list[str]
    engine_hints: dict[str, str | int | bool | None]


class ArtifactManifest(BaseModel):
    full_mix_wav: str | None = None
    stems: list[str] = Field(default_factory=list)
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


class ProviderCapability(BaseModel):
    name: str
    engine: Engine
    available: bool
    fallback: bool


class CapabilitiesResponse(BaseModel):
    service: Literal["snuffraga-soundsystem-inference"]
    engines: list[Engine]
    intents: list[Intent]
    prompt_modules: dict[str, list[str]]
    providers: list[ProviderCapability]
