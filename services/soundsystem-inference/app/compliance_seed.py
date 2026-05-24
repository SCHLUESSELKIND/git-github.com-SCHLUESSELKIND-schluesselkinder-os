"""Default model registry seed for the compliance foundation.

Every entry is a documented research/review-only candidate. No entry is
auto-promoted to a release-ready state. The seed is consumed once by the
in-memory repository on first read and is idempotent via stable UUIDs so
the Postgres repository (S10b) can re-apply it without producing duplicates.

The seed sources its candidate list from
docs/soundsystem/model-provider-strategy.md. Provider/model names appear here
because this is admin/compliance/debug context — these names never reach the
primary operator-console create flows (see
docs/soundsystem/operator-interface-principles.md).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas import (
    ActivationStatus,
    CommercialStatus,
    LicenseRegistryEntry,
    LicenseStatus,
    ModelRegistryEntry,
    ProviderGroup,
    RiskTier,
)


# Stable namespace for deterministic UUID generation. Lets the seed produce
# identical IDs across in-memory and Postgres repositories so cross-system
# references survive.
_SEED_NAMESPACE = uuid.UUID("3a8e8b1e-4f9a-4c6d-9d8e-7a6b5c4d3e2f")


def stable_uuid(label: str, *parts: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NAMESPACE, "|".join((label, *parts)))


_FIXED_TS = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)


def _license(
    adapter_key: str,
    license_name: str,
    permits_commercial: bool,
    *,
    restrictions: tuple[str, ...] = (),
    license_url: str | None = None,
    status: LicenseStatus = LicenseStatus.NEEDS_REVIEW,
    notes: str | None = None,
) -> LicenseRegistryEntry:
    return LicenseRegistryEntry(
        license_id=stable_uuid("license", adapter_key, license_name),
        model_or_dataset_id=adapter_key,
        license_name=license_name,
        license_url=license_url,
        permits_commercial=permits_commercial,
        restrictions=list(restrictions),
        reviewed_by=None,
        reviewed_at=None,
        status=status,
        notes=notes,
        created_at=_FIXED_TS,
    )


def _model(
    adapter_key: str,
    provider_group: ProviderGroup,
    display_name_internal: str,
    *,
    commercial_status: CommercialStatus,
    activation_status: ActivationStatus,
    risk_tier: RiskTier,
    license_id: uuid.UUID | None,
    notes: str | None = None,
) -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id=stable_uuid("model", provider_group.value, adapter_key),
        provider_group=provider_group,
        adapter_key=adapter_key,
        display_name_internal=display_name_internal,
        commercial_status=commercial_status,
        activation_status=activation_status,
        risk_tier=risk_tier,
        license_id=license_id,
        notes=notes,
        created_at=_FIXED_TS,
        updated_at=_FIXED_TS,
    )


def default_license_seed() -> list[LicenseRegistryEntry]:
    return [
        _license(
            "mock-internal",
            "internal-mock",
            permits_commercial=False,
            status=LicenseStatus.APPROVED,
            notes="Internal deterministic mock adapter. Not a real model.",
        ),
        _license(
            "musicgen",
            "MIT-code / CC-BY-NC-weights",
            permits_commercial=False,
            restrictions=("weights non-commercial",),
            license_url="https://github.com/facebookresearch/audiocraft",
        ),
        _license(
            "stable-audio-open",
            "Stability AI Community License",
            permits_commercial=False,
            restrictions=("commercial requires Stability terms review",),
            license_url="https://stability.ai/license",
        ),
        _license(
            "ace-step",
            "research-license",
            permits_commercial=False,
            restrictions=("custom research license; commercial unclear",),
            license_url="https://ace-step.github.io/",
        ),
        _license(
            "tencent-songgeneration",
            "vendor-provided",
            permits_commercial=False,
            restrictions=("API-only / provider TOS"),
            license_url="https://github.com/tencent-ailab/SongGeneration",
        ),
        _license(
            "yue",
            "Apache-2.0-code / varies-weights",
            permits_commercial=False,
            restrictions=("weights license varies per checkpoint",),
            license_url="https://github.com/multimodal-art-projection/YuE",
        ),
        _license(
            "kokoro",
            "Apache-2.0",
            permits_commercial=True,
            license_url="https://huggingface.co/hexgrad/Kokoro-82M",
        ),
        _license(
            "qwen3-tts",
            "Apache-2.0",
            permits_commercial=True,
            restrictions=("weight terms vary per checkpoint — verify",),
            license_url="https://github.com/QwenLM/Qwen3-TTS",
        ),
        _license(
            "piper",
            "MIT",
            permits_commercial=True,
            license_url="https://github.com/rhasspy/piper",
        ),
        _license(
            "seed-tts",
            "no-public-weights",
            permits_commercial=False,
            restrictions=("reference/benchmark only — no code or weights released",),
            status=LicenseStatus.REJECTED,
        ),
        _license(
            "xtts-v2",
            "Coqui-Public-Model-License",
            permits_commercial=False,
            status=LicenseStatus.REJECTED,
        ),
        _license(
            "f5-tts",
            "MIT-code / CC-BY-NC-pretrained",
            permits_commercial=False,
            status=LicenseStatus.REJECTED,
        ),
        _license(
            "openvoice-v2",
            "MIT",
            permits_commercial=True,
            restrictions=("speaker consent required for any cloning use",),
            license_url="https://github.com/myshell-ai/OpenVoice",
        ),
        _license(
            "fish-speech",
            "Apache-2.0-code / varies-weights",
            permits_commercial=False,
            restrictions=("commercial use of pretrained weights conditional",),
            license_url="https://github.com/fishaudio/fish-speech",
        ),
        _license(
            "voxcpm2",
            "vendor-provided",
            permits_commercial=False,
            restrictions=("review per release",),
            license_url="https://github.com/OpenBMB/VoxCPM",
        ),
        _license(
            "rvc-webui",
            "varies-public-models",
            permits_commercial=False,
            restrictions=(
                "public RVC voice models commonly built without subject consent — blocked",
            ),
            status=LicenseStatus.REJECTED,
        ),
        _license(
            "diffsinger",
            "permissive-code / voicebank-varies",
            permits_commercial=False,
            restrictions=("voicebank license per voicebank",),
        ),
        _license(
            "openutau",
            "MIT-tooling / voicebank-varies",
            permits_commercial=False,
            restrictions=("voicebank license per voicebank",),
        ),
        _license(
            "demucs",
            "MIT",
            permits_commercial=True,
            license_url="https://github.com/facebookresearch/demucs",
        ),
        _license(
            "sonicmaster",
            "Apache-2.0",
            permits_commercial=True,
            license_url="https://github.com/",
        ),
        _license(
            "matchering",
            "GPL-3.0",
            permits_commercial=False,
            restrictions=("GPL-3.0 copyleft constraints on derivative works",),
            license_url="https://github.com/sergree/matchering",
        ),
    ]


def default_model_seed(
    licenses: list[LicenseRegistryEntry],
) -> list[ModelRegistryEntry]:
    by_key: dict[str, uuid.UUID] = {
        entry.model_or_dataset_id: entry.license_id for entry in licenses
    }

    def lic(key: str) -> uuid.UUID | None:
        return by_key.get(key)

    entries: list[ModelRegistryEntry] = []

    # music_loop_provider ---------------------------------------------------
    entries.append(
        _model(
            "mock-music-loop",
            ProviderGroup.MUSIC_LOOP_PROVIDER,
            "Mock Music Loop Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
            notes="Always-available deterministic stub for the SoundGraph loop path.",
        )
    )
    entries.append(
        _model(
            "musicgen-medium",
            ProviderGroup.MUSIC_LOOP_PROVIDER,
            "MusicGen / AudioCraft",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("musicgen"),
            notes="Code MIT, weights research/CC-BY-NC. Review per checkpoint before commercial use.",
        )
    )
    entries.append(
        _model(
            "stable-audio-open",
            ProviderGroup.MUSIC_LOOP_PROVIDER,
            "Stable Audio Open",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("stable-audio-open"),
            notes="Stability AI Community License — legal review before commercial use.",
        )
    )

    # high_fidelity_clip_provider -------------------------------------------
    entries.append(
        _model(
            "mock-hifi-clip",
            ProviderGroup.HIGH_FIDELITY_CLIP_PROVIDER,
            "Mock High-Fidelity Clip Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
            notes="Always-available deterministic stub for short clips/atmospheres.",
        )
    )
    entries.append(
        _model(
            "stable-audio-open-hifi",
            ProviderGroup.HIGH_FIDELITY_CLIP_PROVIDER,
            "Stable Audio Open (clip mode)",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("stable-audio-open"),
        )
    )

    # full_song_experimental_provider --------------------------------------
    entries.append(
        _model(
            "mock-full-song",
            ProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER,
            "Mock Full-Song Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
        )
    )
    entries.append(
        _model(
            "ace-step",
            ProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER,
            "ACE-Step",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("ace-step"),
            notes="Custom research license; commercial unclear. Output requires Master Bus pass before any release claim.",
        )
    )
    entries.append(
        _model(
            "tencent-songgeneration",
            ProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER,
            "Tencent SongGeneration",
            commercial_status=CommercialStatus.BLOCKED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.RED,
            license_id=lic("tencent-songgeneration"),
            notes="Provider TOS / API-only. Not a build candidate without legal review.",
        )
    )
    entries.append(
        _model(
            "yue-instrumental",
            ProviderGroup.FULL_SONG_EXPERIMENTAL_PROVIDER,
            "YuE (instrumental)",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("yue"),
        )
    )

    # voice_tts_provider ----------------------------------------------------
    entries.append(
        _model(
            "mock-voice-tts",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "Mock Voice TTS Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
        )
    )
    entries.append(
        _model(
            "kokoro",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "Kokoro",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.GREEN,
            license_id=lic("kokoro"),
            notes="Apache-2.0; strongest cleanly-licensed candidate for narration today.",
        )
    )
    entries.append(
        _model(
            "qwen3-tts",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "Qwen3-TTS",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("qwen3-tts"),
        )
    )
    entries.append(
        _model(
            "seed-tts",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "Seed-TTS (reference)",
            commercial_status=CommercialStatus.BLOCKED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.RED,
            license_id=lic("seed-tts"),
            notes="Benchmark only — no code/weights released. Not a build candidate.",
        )
    )
    entries.append(
        _model(
            "xtts-v2",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "XTTS-v2",
            commercial_status=CommercialStatus.BLOCKED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.RED,
            license_id=lic("xtts-v2"),
            notes="Coqui Public Model License restricts commercial use.",
        )
    )
    entries.append(
        _model(
            "f5-tts",
            ProviderGroup.VOICE_TTS_PROVIDER,
            "F5-TTS (pretrained)",
            commercial_status=CommercialStatus.BLOCKED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.RED,
            license_id=lic("f5-tts"),
            notes="Pretrained CC-BY-NC — not a commercial candidate.",
        )
    )

    # voice_clone_provider --------------------------------------------------
    entries.append(
        _model(
            "mock-voice-clone",
            ProviderGroup.VOICE_CLONE_PROVIDER,
            "Mock Voice Clone Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
            notes="Consent-gated even in mock mode.",
        )
    )
    entries.append(
        _model(
            "openvoice-v2",
            ProviderGroup.VOICE_CLONE_PROVIDER,
            "OpenVoice V2",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("openvoice-v2"),
        )
    )
    entries.append(
        _model(
            "fish-speech",
            ProviderGroup.VOICE_CLONE_PROVIDER,
            "Fish Speech",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("fish-speech"),
        )
    )
    entries.append(
        _model(
            "voxcpm2",
            ProviderGroup.VOICE_CLONE_PROVIDER,
            "VoxCPM2",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("voxcpm2"),
        )
    )
    entries.append(
        _model(
            "rvc-webui",
            ProviderGroup.VOICE_CLONE_PROVIDER,
            "RVC WebUI",
            commercial_status=CommercialStatus.BLOCKED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.RED,
            license_id=lic("rvc-webui"),
            notes="Public RVC models without subject consent are blocked. Internal/consent-only use is a separate adapter and not auto-activated.",
        )
    )

    # singing_voice_provider ------------------------------------------------
    entries.append(
        _model(
            "mock-singing-voice",
            ProviderGroup.SINGING_VOICE_PROVIDER,
            "Mock Singing Voice Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
        )
    )
    entries.append(
        _model(
            "yue-vocal",
            ProviderGroup.SINGING_VOICE_PROVIDER,
            "YuE (vocal)",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("yue"),
        )
    )
    entries.append(
        _model(
            "diffsinger",
            ProviderGroup.SINGING_VOICE_PROVIDER,
            "DiffSinger",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("diffsinger"),
            notes="Voicebank license must be cleared per voicebank.",
        )
    )
    entries.append(
        _model(
            "openutau",
            ProviderGroup.SINGING_VOICE_PROVIDER,
            "OpenUtau (tooling)",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("openutau"),
            notes="Tooling under MIT; voicebanks under separate licenses.",
        )
    )

    # offline_fallback_provider --------------------------------------------
    entries.append(
        _model(
            "mock-offline-fallback",
            ProviderGroup.OFFLINE_FALLBACK_PROVIDER,
            "Mock Offline Fallback Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
        )
    )
    entries.append(
        _model(
            "piper",
            ProviderGroup.OFFLINE_FALLBACK_PROVIDER,
            "Piper TTS",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.GREEN,
            license_id=lic("piper"),
            notes="MIT; offline, low-resource — natural fallback.",
        )
    )

    # mastering_provider ----------------------------------------------------
    entries.append(
        _model(
            "mock-mastering",
            ProviderGroup.MASTERING_PROVIDER,
            "Mock Master Bus Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
            notes="Currently live mock adapter behind Master Bus contract.",
        )
    )
    entries.append(
        _model(
            "sonicmaster",
            ProviderGroup.MASTERING_PROVIDER,
            "SonicMaster",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.GREEN,
            license_id=lic("sonicmaster"),
            notes="Apache-2.0; primary candidate behind the Master Bus modes.",
        )
    )
    entries.append(
        _model(
            "matchering",
            ProviderGroup.MASTERING_PROVIDER,
            "Matchering (reference-match)",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.AMBER,
            license_id=lic("matchering"),
            notes="GPL-3.0 — copyleft constraints. Use only via subprocess/CLI boundary if at all.",
        )
    )

    # stem_separation_provider ---------------------------------------------
    entries.append(
        _model(
            "mock-stem-separation",
            ProviderGroup.STEM_SEPARATION_PROVIDER,
            "Mock Stem Separation Provider",
            commercial_status=CommercialStatus.RESEARCH_ONLY,
            activation_status=ActivationStatus.MOCK,
            risk_tier=RiskTier.GREEN,
            license_id=lic("mock-internal"),
        )
    )
    entries.append(
        _model(
            "demucs",
            ProviderGroup.STEM_SEPARATION_PROVIDER,
            "Demucs",
            commercial_status=CommercialStatus.REVIEW_NEEDED,
            activation_status=ActivationStatus.NOT_WIRED,
            risk_tier=RiskTier.GREEN,
            license_id=lic("demucs"),
            notes="MIT; standard stem separator behind the STEM TRACK intent.",
        )
    )

    return entries
