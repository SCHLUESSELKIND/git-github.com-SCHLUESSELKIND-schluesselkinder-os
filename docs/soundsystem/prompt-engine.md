# Prompt Engine

## Goal

The prompt engine should turn modular creative control into repeatable engine-specific instructions without making the UI feel like a SaaS form.

## Prompt Object

```json
{
  "intent": "BUILD_RIDDIM",
  "modules": {
    "energy": "warehouse",
    "bass_pressure": "earthquake",
    "vocals": "ritual",
    "atmosphere": "dub_smoke",
    "structure": "stem_heavy",
    "tempo": "half_time_pressure",
    "druck": "soundsystem",
    "effect_devices": ["dub_delay", "spring_reverb", "tape_saturation"]
  },
  "character": "SHIBARI_KAWAII",
  "style_dna": ["cold-dub-industrial", "black-concrete-space"],
  "technical": {
    "bpm": 142,
    "key": "F minor",
    "duration_seconds": 180,
    "stems_required": true
  }
}
```

The prompt object compiles into the `SNUFFRAGA SOUNDGRAPH` model described in
[sound-model.md](./sound-model.md). The important product rule is that a prompt
does not only request a stereo song. It requests a stem-aware graph that can be
edited after generation.

## Prompting Modes

- Simple prompt: one natural-language instruction for fast creation.
- Modular prompt: selected modules for repeatable control.
- Stem prompt: generate or replace only one lane.
- Edit prompt: change a selected lane or region while preserving locked lanes.
- Repair prompt: fix mix or artifact problems without changing composition.

## Controlled Vocabulary

### Energy

- `hypnotic`: repetitive, locked, restraint, late-night loop pressure
- `destructive`: distorted transients, aggressive movement, unstable impact
- `euphoric`: lift without pop brightness, cold release, controlled emotion
- `warehouse`: concrete room, physical low-end, strobe-like momentum
- `demonic`: ritual threat, low-register tension, non-theatrical darkness

### Bass Pressure

- `warm`: rounded sub, tape-like saturation
- `deep`: sub-first, minimal upper harmonics
- `crushing`: compressed, heavy, body-pressure low-end
- `earthquake`: long sub waves, system-test movement
- `maximum`: dangerous, clipped edges, only for internal experiments

### Vocals

- `smoky`: close, low, breath-textured
- `haunting`: distant, spectral, unresolved
- `whisper`: intimate, almost spoken
- `ritual`: repeated mantra, call-like phrasing
- `melodic`: memorable but cold, not pop-polished

### Atmosphere

- `neon_green`: dark mint light, synthetic haze
- `dub_smoke`: delay trails, tape echoes, empty room
- `black_concrete`: dry brutalist space, minimal air
- `underground`: basement pressure, no festival gloss
- `post_human`: machine-cold, detached, synthetic presence

### Structure

- `no_intro`: immediate useful material
- `instant_drop`: first seconds establish the core
- `mantra_hook`: repeated hook fragment
- `long_breakdown`: extended tension without release
- `stem_heavy`: arrangement designed for later manual editing

### Tempo

- `straight`: grid-locked, direct, no swing
- `swung`: delayed off-grid movement
- `half_time_pressure`: slow-feeling body movement over faster BPM
- `double_time_hats`: fast hats/percussion over slower core groove
- `broken`: fractured groove with intentional gaps
- `stepping`: dub/techno forward movement

### Druck

- `open`: dynamic and not crushed
- `glued`: controlled pressure with usable headroom
- `club`: loud, clean, DJ-usable
- `soundsystem`: sub-forward physical pressure
- `crushed`: aggressive internal experiment
- `redline`: unsafe unless explicitly approved

### Effect Devices

- `eq`
- `compressor`
- `gate`
- `transient_shaper`
- `saturation`
- `distortion`
- `filter`
- `chorus`
- `phaser`
- `flanger`
- `dub_delay`
- `spring_reverb`
- `plate_reverb`
- `sidechain`
- `stutter`
- `reverse`
- `resampler`
- `tape_stop`

## LLM Roles

Use GPT-5.5 API for:

- prompt normalization
- negative prompt generation
- safety rewrite suggestions
- structured analysis
- JSON schema-constrained output

Use Claude API for:

- worldbuilding
- character text
- creative direction
- mood language
- narrative consistency

The prompt engine must save both raw user intent and compiled engine prompts. A later output must always be traceable to the original modules.

> No live LLM call is wired today. `compile_prompt` is fully deterministic
> and runs against in-process modules only. The LLM-role mapping above is
> the design target; the env flag and provider abstraction that gate real
> API calls land in a later slice.

## Related Compilers

The music-generation prompt compiler described here returns
`CompiledPrompt` (prompt text, negative prompt, stem plan, tempo, druck,
effect racks). It is distinct from the lyrics compiler.

The lyrics compiler `compile_lyrics_prompt` lives in `app/lyrics_engine.py`
and returns `CompiledLyricsPrompt` (instruction, negative prompt, safety
notes, Suno compatibility notes, SoundGraph compatibility notes,
risky-filler-pattern detection, resolved section structure). It owns the
section-level vocabulary (`verse`, `pre_chorus`, `chorus`, `bridge`,
`dub_breakdown`, `outro`, `instrumental_opening`) and the
`avoid_intro_singing` rule.

See [lyrics-engine.md](./lyrics-engine.md) for the full contract, endpoint
examples, and the future GPT-5.5 integration boundary.

## Anti-Patterns

- Do not prompt "in the style of [artist]".
- Do not request "make a song like [track]".
- Do not use reference audio without rights status.
- Do not let the LLM invent fake social metrics or release claims.
- Do not flatten character identity into generic genre tags.
