from __future__ import annotations

from app.schemas import CompiledPrompt, CompiledPromptRequest


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


def compile_prompt(request: CompiledPromptRequest) -> CompiledPrompt:
    modules = request.prompt_modules
    technical = request.technical

    selected = {
        "energy": modules.energy.value,
        "bass_pressure": modules.bass_pressure.value,
        "vocals": modules.vocals.value,
        "atmosphere": modules.atmosphere.value,
        "structure": modules.structure.value,
    }

    module_lines = [
        MODULE_LANGUAGE[group][value]
        for group, value in selected.items()
    ]

    lyrics_hint = ""
    if request.lyrics:
        lyrics_hint = " Use the supplied lyrics as source material; do not add third-party lines."

    prompt_text = (
        f"{request.intent.value} for {request.character_code}. "
        "Dark industrial dub, premium underground record-label tone. "
        + "; ".join(module_lines)
        + ". "
        f"Target duration {technical.duration_seconds}s."
        f"{' Target BPM ' + str(technical.bpm) + '.' if technical.bpm else ''}"
        f"{' Target key ' + technical.key + '.' if technical.key else ''}"
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

    return CompiledPrompt(
        prompt_text=prompt_text,
        negative_prompt=negative_prompt,
        safety_notes=safety_notes,
        engine_hints={
            "duration_seconds": technical.duration_seconds,
            "bpm": technical.bpm,
            "key": technical.key,
            "stems_required": technical.stems_required,
            "seed": technical.seed,
        },
    )
