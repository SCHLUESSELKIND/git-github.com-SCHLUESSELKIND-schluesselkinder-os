from __future__ import annotations

from app.schemas import (
    CompiledPrompt,
    CompiledPromptRequest,
    DruckControls,
    EffectDevice,
    EffectDeviceType,
    EffectRack,
    StemLanePlan,
    StemLaneType,
    StemPlan,
    StemSourceType,
    TempoControls,
)


MODULE_LANGUAGE: dict[str, dict[str, str]] = {
    "energy": {
        "hypnotic": "locked repetitive movement with restrained late-night pressure",
        "destructive": "distorted transient impact with unstable industrial force",
        "euphoric": "cold lift and emotional release without pop gloss",
        "warehouse": "concrete-room momentum, physical low-end, strobe-like pressure",
        "demonic": "ritual threat in the low register, dark without theatrical horror",
    },
    "bass_pressure": {
        "warm": "rounded sub bass with controlled saturation",
        "deep": "sub-first low-end with minimal upper harmonics",
        "crushing": "compressed heavy bass pressure with body impact",
        "earthquake": "long sub waves and system-test movement",
        "maximum": "dangerous clipped low-end for internal experiments only",
    },
    "vocals": {
        "smoky": "close low vocal texture with breath and restraint",
        "haunting": "distant spectral vocal presence with unresolved tension",
        "whisper": "intimate near-spoken vocal fragments",
        "ritual": "repeated mantra phrasing and call-like delivery",
        "melodic": "memorable cold vocal line without radio-pop polish",
    },
    "atmosphere": {
        "neon_green": "dark mint synthetic light in a black room",
        "dub_smoke": "delay trails, tape echoes, and empty-room haze",
        "black_concrete": "dry brutalist space with hard surfaces",
        "underground": "basement pressure with no festival sheen",
        "post_human": "detached synthetic machine presence",
    },
    "structure": {
        "no_intro": "begin with useful material immediately",
        "instant_drop": "establish the core pressure in the first seconds",
        "mantra_hook": "repeat a short hook fragment as a ritual anchor",
        "long_breakdown": "hold extended tension without easy release",
        "stem_heavy": "arrange with clear separable parts for later editing",
    },
}


# Lane-by-lane device defaults. Conservative — enough to make the rack meaningful
# without claiming a real DSP chain. Real device parameters land with the audio
# implementation.
DEFAULT_LANE_DEVICES: dict[StemLaneType, list[EffectDeviceType]] = {
    StemLaneType.KICK: [
        EffectDeviceType.EQ,
        EffectDeviceType.TRANSIENT_SHAPER,
        EffectDeviceType.COMPRESSOR,
        EffectDeviceType.SATURATION,
    ],
    StemLaneType.DRUMS: [
        EffectDeviceType.EQ,
        EffectDeviceType.COMPRESSOR,
        EffectDeviceType.TRANSIENT_SHAPER,
    ],
    StemLaneType.PERCUSSION: [
        EffectDeviceType.EQ,
        EffectDeviceType.GATE,
        EffectDeviceType.SPRING_REVERB,
    ],
    StemLaneType.BASS: [
        EffectDeviceType.EQ,
        EffectDeviceType.COMPRESSOR,
        EffectDeviceType.SATURATION,
        EffectDeviceType.SIDECHAIN,
    ],
    StemLaneType.MUSIC: [
        EffectDeviceType.EQ,
        EffectDeviceType.FILTER,
        EffectDeviceType.PLATE_REVERB,
    ],
    StemLaneType.LEAD: [
        EffectDeviceType.EQ,
        EffectDeviceType.COMPRESSOR,
        EffectDeviceType.CHORUS,
        EffectDeviceType.DUB_DELAY,
    ],
    StemLaneType.VOCALS_MAIN: [
        EffectDeviceType.EQ,
        EffectDeviceType.COMPRESSOR,
        EffectDeviceType.SPRING_REVERB,
        EffectDeviceType.DUB_DELAY,
    ],
    StemLaneType.VOCALS_ADLIBS: [
        EffectDeviceType.EQ,
        EffectDeviceType.STUTTER,
        EffectDeviceType.DUB_DELAY,
    ],
    StemLaneType.FX: [
        EffectDeviceType.EQ,
        EffectDeviceType.REVERSE,
        EffectDeviceType.DUB_DELAY,
    ],
    StemLaneType.ATMOSPHERE: [
        EffectDeviceType.FILTER,
        EffectDeviceType.PLATE_REVERB,
    ],
    StemLaneType.RETURN_DELAY: [EffectDeviceType.DUB_DELAY],
    StemLaneType.RETURN_REVERB: [EffectDeviceType.SPRING_REVERB],
}


def _resolve_tempo(request: CompiledPromptRequest) -> TempoControls:
    if request.tempo is not None:
        return request.tempo
    bpm = request.technical.bpm if request.technical.bpm is not None else 140
    return TempoControls(bpm=bpm)


def _resolve_druck(request: CompiledPromptRequest) -> DruckControls:
    if request.druck is not None:
        return request.druck
    return DruckControls()


def _build_stem_plan(request: CompiledPromptRequest) -> StemPlan:
    locked = list(request.locked_lanes)
    lanes = [
        StemLanePlan(
            lane=lane,
            source=StemSourceType.GENERATED_DIRECT,
            editable=True,
            locked=lane in locked,
        )
        for lane in StemLaneType
    ]
    return StemPlan(lanes=lanes, locked_lanes=locked, target_lane=request.target_lane)


def _build_effect_racks(request: CompiledPromptRequest) -> list[EffectRack]:
    racks: list[EffectRack] = []
    for lane in StemLaneType:
        devices = list(DEFAULT_LANE_DEVICES.get(lane, []))
        for effect in request.requested_effects:
            if effect not in devices:
                devices.append(effect)
        racks.append(
            EffectRack(
                lane=lane,
                devices=[EffectDevice(device=device) for device in devices],
            )
        )
    return racks


def compile_prompt(request: CompiledPromptRequest) -> CompiledPrompt:
    modules = request.prompt_modules
    technical = request.technical
    tempo = _resolve_tempo(request)
    druck = _resolve_druck(request)

    selected = {
        "energy": modules.energy.value,
        "bass_pressure": modules.bass_pressure.value,
        "vocals": modules.vocals.value,
        "atmosphere": modules.atmosphere.value,
        "structure": modules.structure.value,
    }

    module_lines = [MODULE_LANGUAGE[group][value] for group, value in selected.items()]

    lyrics_hint = ""
    if request.lyrics:
        lyrics_hint = " Use the supplied lyrics as source material; do not add third-party lines."

    tempo_hint = f" Target BPM {tempo.bpm} · feel {tempo.feel.value} · swing {tempo.swing}."
    if tempo.locked_grid:
        tempo_hint += " Grid is locked; do not stretch."
    if technical.key:
        tempo_hint += f" Target key {technical.key}."

    druck_hint = (
        f" Druck preset {druck.preset.value} ·"
        f" sub {druck.sub_pressure}/5 ·"
        f" transient {druck.transient_pressure}/5 ·"
        f" density {druck.density}/5."
    )

    effect_hint = ""
    if request.requested_effects:
        effect_names = ", ".join(effect.value for effect in request.requested_effects)
        effect_hint = f" Effects requested: {effect_names}."

    target_hint = ""
    if request.target_lane is not None:
        target_hint = f" Target lane: {request.target_lane.value}."

    locked_hint = ""
    if request.locked_lanes:
        locked_names = ", ".join(lane.value for lane in request.locked_lanes)
        locked_hint = f" Locked lanes: {locked_names}."

    prompt_text = (
        f"{request.intent.value} for {request.character_code}. "
        "Dark industrial dub, premium underground record-label tone. "
        + "; ".join(module_lines)
        + ". "
        f"Target duration {technical.duration_seconds}s."
        f"{tempo_hint}"
        f"{druck_hint}"
        f"{effect_hint}"
        f"{target_hint}"
        f"{locked_hint}"
        f"{lyrics_hint}"
    )

    negative_prompt = (
        "No named artist imitation, no commercial song cloning, no unauthorized vocal likeness, "
        "no festival EDM gloss, no cheerful SaaS-pop energy, no copied lyrics."
    )

    safety_notes = [
        "Prompt avoids named artist or track imitation.",
        "Reference audio requires explicit rights before use.",
        "Release candidates require separate human review.",
    ]

    if modules.bass_pressure.value == "maximum":
        safety_notes.append("Maximum bass pressure is marked internal experiment only.")
    if druck.preset.value in ("crushed", "redline"):
        safety_notes.append(
            f"Druck preset '{druck.preset.value}' is internal experiment only and must not ship as release."
        )

    return CompiledPrompt(
        prompt_text=prompt_text,
        negative_prompt=negative_prompt,
        safety_notes=safety_notes,
        engine_hints={
            "duration_seconds": technical.duration_seconds,
            "bpm": tempo.bpm,
            "key": technical.key,
            "stems_required": technical.stems_required,
            "seed": technical.seed,
            "tempo_feel": tempo.feel.value,
            "druck_preset": druck.preset.value,
        },
        stem_plan=_build_stem_plan(request),
        tempo=tempo,
        druck=druck,
        effect_racks=_build_effect_racks(request),
        requested_effects=list(request.requested_effects),
    )
